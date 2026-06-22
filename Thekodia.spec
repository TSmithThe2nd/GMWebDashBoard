# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all

webview_datas, webview_bins, webview_hidden = collect_all('webview')

a = Analysis(
    ['app.py'],
    pathex=[],
    binaries=webview_bins,
    datas=[('static', 'static'), ('parsers', 'parsers')] + webview_datas,
    hiddenimports=webview_hidden,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='Thekodia',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='static/thekodia-logo.ico',
)