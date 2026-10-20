# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.hooks import collect_all


customtkinter_datas, customtkinter_binaries, customtkinter_hidden = collect_all(
    "customtkinter"
)
pytchat_datas, pytchat_binaries, pytchat_hidden = collect_all("pytchat")

a = Analysis(
    ["gui_app.py"],
    pathex=[],
    binaries=customtkinter_binaries + pytchat_binaries,
    datas=customtkinter_datas + pytchat_datas,
    hiddenimports=customtkinter_hidden + pytchat_hidden,
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
    [],
    exclude_binaries=True,
    name="YT直播留言監控",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="YT直播留言監控",
)
