# AITS Print Server - PyInstaller Spec File for Windows
# -*- mode: python ; coding: utf-8 -*-
import os

block_cipher = None

a = Analysis(
    ['../tray_app.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('../server.py', '.'),
        ('../server_simple.py', '.'),
        ('../printer_manager.py', '.'),
        ('../job_queue.py', '.'),
        ('../auth.py', '.'),
        ('../odoo_client.py', '.'),
        ('../generate_ssl_cert.py', '.'),
        ('../static', 'static'),
        ('../config.yaml.example', '.'),
    ],
    hiddenimports=[
        'flask',
        'flask_cors',
        'yaml',
        'pystray',
        'PIL',
        'PIL.Image',
        'PIL.ImageDraw',
        'win32print',
        'win32api',
        'waitress',
        'logging.handlers',
        'sqlite3',
        'uuid',
        'threading',
        'queue',
        'requests',
        'cryptography',
        'certifi',
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
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='AITS_Print_Server',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # Enable console for debugging - can disable later
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='../static/icon.ico' if os.path.exists('../static/icon.ico') else None,
)
