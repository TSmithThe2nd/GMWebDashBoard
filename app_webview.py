"""
Thekodia DM Dashboard — PyWebView desktop launcher
Runs Flask in a background thread and opens the app as a native window.
Use app.py directly if you want the browser-based experience instead.
"""

import os
import sys
import threading
import time
import urllib.request
from pathlib import Path

import webview

from app import create_app

STORAGE_PATH = str(Path(os.environ.get('APPDATA', Path.home())) / 'Thekodia' / 'webdata')
Path(STORAGE_PATH).mkdir(parents=True, exist_ok=True)

URL = 'http://localhost:5000'


class Api:
    def close_self(self):
        """Close whichever popup window called this — never closes the main DM window."""
        w = webview.active_window()
        if w and w.title != 'Thekodia DM':
            w.destroy()

    def open_player_display(self):
        """Open the full player-facing display as a second always-on-top window."""
        for w in webview.windows:
            if w.title == 'Thekodia — Player View':
                return
        webview.create_window(
            'Thekodia — Player View',
            f'{URL}/thekodia-player-display.html',
            width=1280,
            height=720,
            resizable=True,
            on_top=True,
        )

    def open_player_panel(self):
        """Open the compact player-panel popout (combat/ambient) as an always-on-top transparent window.
        Multiple panels can be opened simultaneously for players at different seats."""
        existing = sum(1 for w in webview.windows if w.title.startswith('Thekodia — Player Panel'))
        title = f'Thekodia — Player Panel {existing + 1}' if existing else 'Thekodia — Player Panel'
        webview.create_window(
            title,
            f'{URL}/thekodia-popout-player-panel.html',
            width=580,
            height=220,
            resizable=True,
            on_top=True,
            transparent=True,
            frameless=True,
            js_api=self,
        )

    def open_initiative(self):
        """Open the interactive initiative tracker popout as an always-on-top transparent window."""
        for w in webview.windows:
            if w.title == 'Thekodia — Initiative':
                return
        webview.create_window(
            'Thekodia — Initiative',
            f'{URL}/thekodia-popout-initiative.html',
            width=360,
            height=620,
            resizable=True,
            on_top=True,
            transparent=True,
            frameless=True,
            js_api=self,
        )

    def open_dice(self):
        """Open the dice roller popout as an always-on-top window."""
        for w in webview.windows:
            if w.title == 'Thekodia — Dice':
                return
        webview.create_window(
            'Thekodia — Dice',
            f'{URL}/thekodia-popout-dice.html',
            width=400,
            height=580,
            resizable=True,
            on_top=True,
            js_api=self,
        )


def _wait_for_server(timeout: float = 10.0) -> bool:
    """Poll /health until Flask is accepting connections."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            urllib.request.urlopen(f'{URL}/health', timeout=0.5)
            return True
        except Exception:
            time.sleep(0.1)
    return False


def _run_flask() -> None:
    app = create_app()
    # use_reloader=False is required when Flask runs in a thread
    app.run(host='localhost', port=5000, debug=False, use_reloader=False)


if __name__ == '__main__':
    flask_thread = threading.Thread(target=_run_flask, daemon=True)
    flask_thread.start()

    if not _wait_for_server():
        print('ERROR: Flask did not start within 10 seconds. Check for port conflicts.')
        sys.exit(1)

    api = Api()
    webview.create_window(
        'Thekodia DM',
        URL,
        js_api=api,
        width=1400,
        height=900,
        min_size=(900, 600),
        resizable=True,
    )

    webview.start(storage_path=STORAGE_PATH)