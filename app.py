"""
Thekodia DM Dashboard — Flask Server
Run: python app.py  →  http://localhost:5000
"""

import webbrowser
import threading
from pathlib import Path
from flask import Flask

from routes.data import data_bp
from routes.pdf import pdf_bp
from routes.static_files import static_bp
import routes.data as _data_mod
import routes.pdf as _pdf_mod

# ── Paths ─────────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / 'data'
DATA_DIR.mkdir(exist_ok=True)

STORES = {
    'encounters':    DATA_DIR / 'encounters.json',
    'library':       DATA_DIR / 'library.json',
    'players':       DATA_DIR / 'players.json',
    'clock':         DATA_DIR / 'clock.json',
    'clock_history': DATA_DIR / 'clock_history.json',
    'display_state': DATA_DIR / 'display_state.json',
    'weather':       DATA_DIR / 'weather.json',
    'event':         DATA_DIR / 'event.json',
    'ref_notes':     DATA_DIR / 'ref_notes.json',
    'dice_presets':  DATA_DIR / 'dice_presets.json',
    'dice_history':  DATA_DIR / 'dice_history.json',
    'live_add':      DATA_DIR / 'live_add.json',
}


def create_app() -> Flask:
    app = Flask(__name__, static_folder='static')

    # Inject shared state into route modules
    _data_mod.STORES = STORES
    _pdf_mod.DATA_DIR = DATA_DIR

    @app.after_request
    def add_cors(response):
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, DELETE, OPTIONS'
        return response

    @app.route('/', methods=['OPTIONS'])
    def options():
        return '', 200

    app.register_blueprint(data_bp)
    app.register_blueprint(pdf_bp)
    app.register_blueprint(static_bp)

    @app.route('/health')
    def health():
        from parsers.ddb import PDF_SUPPORT, PYPDF_SUPPORT
        return {'status': 'ok', 'pdf_support': PDF_SUPPORT and PYPDF_SUPPORT,
                'stores': list(STORES.keys())}

    return app


if __name__ == '__main__':
    app = create_app()
    print('\n' + '=' * 50)
    print('  Thekodia DM Dashboard')
    print('  http://localhost:5000')
    print('=' * 50 + '\n')
    threading.Timer(1.0, lambda: webbrowser.open('http://localhost:5000')).start()
    app.run(host='localhost', port=5000, debug=False)
