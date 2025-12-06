# AITS Print Server - PyInstaller Spec File for macOS
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['../tray_app.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('../server_simple.py', '.'),
        ('../static', 'static'),
        ('../config.yaml.example', '.'),
    ],
    hiddenimports=[
        'flask',
        'flask_cors',
        'yaml',
        'pystray',
        'PIL',
        'cups',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='AITS_Print_Server',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=True,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='AITS_Print_Server',
)

app = BUNDLE(
    coll,
    name='AITS Print Server.app',
    icon='../static/icon.icns' if os.path.exists('../static/icon.icns') else None,
    bundle_identifier='com.aits.printserver',
    info_plist={
        'NSPrincipalClass': 'NSApplication',
        'NSAppleScriptEnabled': False,
        'CFBundleShortVersionString': '1.0.0',
        'CFBundleVersion': '1.0.0',
        'NSHumanReadableCopyright': 'Copyright © 2025 AITS',
        'LSBackgroundOnly': False,
    },
)
