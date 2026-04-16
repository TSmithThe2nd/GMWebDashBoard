"""
routes/static_files.py — Serve HTML modules and static assets
"""

from flask import Blueprint, send_from_directory

static_bp = Blueprint('static_files', __name__)

# Overridden by app.py to an absolute path when running as a PyInstaller bundle.
STATIC_DIR = 'static'


@static_bp.route('/')
def index():
    return send_from_directory(STATIC_DIR, 'thekodia-initiative-tracker.html')


@static_bp.route('/<path:filename>')
def static_files(filename):
    return send_from_directory(STATIC_DIR, filename)
