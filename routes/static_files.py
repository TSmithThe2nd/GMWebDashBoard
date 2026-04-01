"""
routes/static_files.py — Serve HTML modules and static assets
"""

from flask import Blueprint, send_from_directory

static_bp = Blueprint('static_files', __name__)


@static_bp.route('/')
def index():
    return send_from_directory('static', 'thekodia-initiative-tracker.html')


@static_bp.route('/<path:filename>')
def static_files(filename):
    return send_from_directory('static', filename)
