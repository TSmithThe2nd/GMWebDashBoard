"""
routes/data.py — Generic JSON data store API

GET    /data/<store>  → returns stored JSON
POST   /data/<store>  → saves JSON body
DELETE /data/<store>  → deletes store
"""

import json
from flask import Blueprint, request, jsonify
from pathlib import Path

data_bp = Blueprint('data', __name__)

# Populated by create_app()
STORES: dict = {}


@data_bp.route('/data/<store>', methods=['GET'])
def get_data(store):
    if store not in STORES:
        return jsonify({'error': 'Unknown store'}), 404
    path = STORES[store]
    if not path.exists():
        return jsonify(None)
    with open(path) as f:
        return jsonify(json.load(f))


@data_bp.route('/data/<store>', methods=['POST'])
def set_data(store):
    if store not in STORES:
        return jsonify({'error': 'Unknown store'}), 404
    data = request.get_json(force=True)
    with open(STORES[store], 'w') as f:
        json.dump(data, f, indent=2)
    return jsonify({'ok': True})


@data_bp.route('/data/<store>', methods=['DELETE'])
def delete_data(store):
    if store not in STORES:
        return jsonify({'error': 'Unknown store'}), 404
    path = STORES[store]
    if path.exists():
        path.unlink()
    return jsonify({'ok': True})
