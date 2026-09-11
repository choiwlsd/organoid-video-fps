# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.hooks import collect_all

cv2_datas, cv2_binaries, cv2_hiddenimports = collect_all("cv2")

a = Analysis(
    ["app.py"],
    pathex=[],
    binaries=cv2_binaries,
    datas=[
        ("templates", "templates"),
        ("static", "static"),
        *cv2_datas,
    ],
    hiddenimports=cv2_hiddenimports,
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
    name="VideoMetadataChecker",
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
)
