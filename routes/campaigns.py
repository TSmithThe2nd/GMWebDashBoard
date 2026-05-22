"""
routes/campaigns.py — Campaign management API

GET    /campaigns            → list all campaigns + active name
POST   /campaigns            → create new campaign { name }
POST   /campaigns/switch     → switch active campaign { name }, reload required
DELETE /campaigns/<name>     → delete campaign (not active)
PATCH  /campaigns/<name>     → rename campaign { name: newName }
"""

import json
import shutil
from flask import Blueprint, request, jsonify
from pathlib import Path

campaigns_bp = Blueprint('campaigns', __name__)

# Populated by create_app()
CAMPAIGNS_DIR: Path = None
CONFIG_PATH: Path = None
STORES: dict = {}

STORE_KEYS = [
    'encounters', 'library', 'players', 'clock', 'clock_history',
    'display_state', 'weather', 'event', 'ref_notes', 'dice_presets',
    'dice_history', 'live_add', 'groups', 'settings',
]


def _valid_name(name: str) -> bool:
    return bool(name) and '/' not in name and '\\' not in name and '..' not in name and name == name.strip()


def _get_active() -> str:
    if not CONFIG_PATH or not CONFIG_PATH.exists():
        return 'Default'
    try:
        return json.loads(CONFIG_PATH.read_text()).get('active_campaign', 'Default')
    except Exception:
        return 'Default'


def remap_stores(campaign_name: str) -> None:
    d = CAMPAIGNS_DIR / campaign_name
    d.mkdir(parents=True, exist_ok=True)
    STORES.clear()
    STORES.update({k: d / f'{k}.json' for k in STORE_KEYS})


@campaigns_bp.route('/campaigns', methods=['GET'])
def list_campaigns():
    if not CAMPAIGNS_DIR or not CAMPAIGNS_DIR.exists():
        return jsonify({'campaigns': [], 'active': 'Default'})
    campaigns = sorted(d.name for d in CAMPAIGNS_DIR.iterdir() if d.is_dir())
    return jsonify({'campaigns': campaigns, 'active': _get_active()})


@campaigns_bp.route('/campaigns', methods=['POST'])
def create_campaign():
    data = request.get_json(force=True) or {}
    name = (data.get('name') or '').strip()
    if not _valid_name(name):
        return jsonify({'error': 'Invalid campaign name'}), 400
    new_dir = CAMPAIGNS_DIR / name
    if new_dir.exists():
        return jsonify({'error': 'Campaign already exists'}), 409
    new_dir.mkdir(parents=True)
    return jsonify({'ok': True})


@campaigns_bp.route('/campaigns/switch', methods=['POST'])
def switch_campaign():
    data = request.get_json(force=True) or {}
    name = (data.get('name') or '').strip()
    if not CAMPAIGNS_DIR or not (CAMPAIGNS_DIR / name).is_dir():
        return jsonify({'error': 'Campaign not found'}), 404
    CONFIG_PATH.write_text(json.dumps({'active_campaign': name}, indent=2))
    remap_stores(name)
    return jsonify({'ok': True})


@campaigns_bp.route('/campaigns/<name>', methods=['DELETE'])
def delete_campaign(name):
    if name == _get_active():
        return jsonify({'error': 'Cannot delete the active campaign'}), 400
    if not CAMPAIGNS_DIR:
        return jsonify({'error': 'Campaign not found'}), 404
    target = CAMPAIGNS_DIR / name
    if not target.is_dir():
        return jsonify({'error': 'Campaign not found'}), 404
    shutil.rmtree(str(target))
    return jsonify({'ok': True})


@campaigns_bp.route('/campaigns/<name>', methods=['PATCH'])
def rename_campaign(name):
    data = request.get_json(force=True) or {}
    new_name = (data.get('name') or '').strip()
    if not _valid_name(new_name):
        return jsonify({'error': 'Invalid name'}), 400
    if not CAMPAIGNS_DIR:
        return jsonify({'error': 'Campaign not found'}), 404
    old_dir = CAMPAIGNS_DIR / name
    new_dir = CAMPAIGNS_DIR / new_name
    if not old_dir.is_dir():
        return jsonify({'error': 'Campaign not found'}), 404
    if new_dir.exists():
        return jsonify({'error': 'Name already taken'}), 409
    old_dir.rename(new_dir)
    if CONFIG_PATH and CONFIG_PATH.exists():
        try:
            cfg = json.loads(CONFIG_PATH.read_text())
            if cfg.get('active_campaign') == name:
                cfg['active_campaign'] = new_name
                CONFIG_PATH.write_text(json.dumps(cfg, indent=2))
                remap_stores(new_name)
        except Exception:
            pass
    return jsonify({'ok': True})