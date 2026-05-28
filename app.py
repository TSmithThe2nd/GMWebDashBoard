"""
Thekodia DM Dashboard — Flask Server
Run: python app.py  →  http://localhost:5000
"""

import sys
import os
import json
import shutil
import webbrowser
import threading
from pathlib import Path
from flask import Flask

from routes.data import data_bp
from routes.pdf import pdf_bp
from routes.static_files import static_bp
from routes.campaigns import campaigns_bp
import routes.data as _data_mod
import routes.pdf as _pdf_mod
import routes.static_files as _static_mod
import routes.campaigns as _campaigns_mod

# ── Paths ─────────────────────────────────────────────────────────────────────
# When frozen by PyInstaller, bundled read-only files live in sys._MEIPASS.
# Runtime data (data/*.json) is kept next to the executable so it persists.
if getattr(sys, 'frozen', False):
    BASE_DIR = Path(sys._MEIPASS)          # bundled assets (static, routes, parsers)
    EXE_DIR  = Path(sys.executable).parent # writable folder next to the .exe
else:
    BASE_DIR = Path(__file__).parent
    EXE_DIR  = BASE_DIR

DATA_DIR = EXE_DIR / 'data'
DATA_DIR.mkdir(exist_ok=True)

CAMPAIGNS_DIR = DATA_DIR / 'campaigns'
CONFIG_PATH   = DATA_DIR / 'config.json'

STORE_KEYS = [
    'encounters', 'library', 'players', 'clock', 'clock_history',
    'display_state', 'weather', 'event', 'ref_notes', 'dice_presets',
    'dice_history', 'groups', 'settings',
]


def _migrate_existing() -> None:
    """On first run of new version, move data/*.json → data/campaigns/Default/"""
    if CONFIG_PATH.exists():
        return
    default_dir = CAMPAIGNS_DIR / 'Default'
    default_dir.mkdir(parents=True, exist_ok=True)
    for f in DATA_DIR.glob('*.json'):
        shutil.move(str(f), str(default_dir / f.name))
    CONFIG_PATH.write_text(json.dumps({'active_campaign': 'Default'}, indent=2))


def _get_active_campaign() -> str:
    try:
        return json.loads(CONFIG_PATH.read_text()).get('active_campaign', 'Default')
    except Exception:
        return 'Default'


def _build_stores(campaign_name: str) -> dict:
    d = CAMPAIGNS_DIR / campaign_name
    d.mkdir(parents=True, exist_ok=True)
    return {k: d / f'{k}.json' for k in STORE_KEYS}


# Run migration before building stores
_migrate_existing()

# Mutable dict — campaigns module updates it in-place on switch
STORES = _build_stores(_get_active_campaign())


def create_app() -> Flask:
    app = Flask(__name__, static_folder='static')

    # Inject shared state into route modules
    _data_mod.STORES = STORES
    _pdf_mod.DATA_DIR = DATA_DIR
    _static_mod.STATIC_DIR = str(BASE_DIR / 'static')
    _campaigns_mod.CAMPAIGNS_DIR = CAMPAIGNS_DIR
    _campaigns_mod.CONFIG_PATH = CONFIG_PATH
    _campaigns_mod.STORES = STORES  # same dict object — in-place updates propagate to data_mod

    @app.after_request
    def add_cors(response):
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, DELETE, PATCH, OPTIONS'
        return response

    @app.route('/', methods=['OPTIONS'])
    def options():
        return '', 200

    app.register_blueprint(data_bp)
    app.register_blueprint(pdf_bp)
    app.register_blueprint(static_bp)
    app.register_blueprint(campaigns_bp)

    @app.route('/health')
    def health():
        from parsers.ddb import PDF_SUPPORT, PYPDF_SUPPORT
        active = _campaigns_mod._get_active()
        return {'status': 'ok', 'pdf_support': PDF_SUPPORT and PYPDF_SUPPORT,
                'stores': list(STORES.keys()), 'campaign': active}

    @app.route('/shutdown', methods=['POST'])
    def shutdown():
        threading.Timer(0.3, lambda: os._exit(0)).start()
        return 'ok'

    return app


if __name__ == '__main__':
    app = create_app()
    print('\n' + '=' * 50)
    print('  Thekodia DM Dashboard')
    print('  http://localhost:5000')
    print('=' * 50 + '\n')
    threading.Timer(1.0, lambda: webbrowser.open('http://localhost:5000')).start()
    app.run(host='localhost', port=5000, debug=False)
