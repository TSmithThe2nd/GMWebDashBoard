"""
Thekodia DM Dashboard — PyWebView desktop launcher
Runs Flask in a background thread and opens the app as a native window.
Use app.py directly if you want the browser-based experience instead.
"""

import sys
import threading
import time
import urllib.request

import webview

from app import create_app

URL = 'http://localhost:5000'


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

    webview.create_window(
        'Thekodia DM',
        URL,
        width=1400,
        height=900,
        min_size=(900, 600),
        resizable=True,
    )

    webview.start()