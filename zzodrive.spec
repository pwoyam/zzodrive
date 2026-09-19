# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for zzoDrive."""

block_cipher = None

a = Analysis(
    ['run.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('zzodrive/web/templates', 'zzodrive/web/templates'),
        ('zzodrive/web/static', 'zzodrive/web/static'),
    ],
    hiddenimports=[
        'telethon',
        'telethon.tl',
        'telethon.tl.functions',
        'telethon.tl.functions.upload',
        'telethon.network',
        'telethon.network.connection',
        'cryptography',
        'cryptography.hazmat',
        'cryptography.hazmat.primitives',
        'cryptography.hazmat.primitives.ciphers',
        'cryptography.hazmat.primitives.kdf',
        'cryptography.hazmat.bindings._rust',
        'flask',
        'jinja2',
        'werkzeug',
        'waitress',
        'aiofasttelethonhelper',
        'python_socks',
        'cryptg',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter', 'matplotlib', 'numpy', 'scipy', 'pandas',
        'PyQt5', 'PyQt6', 'PySide2', 'PySide6',
        'IPython', 'jupyter', 'notebook',
    ],
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
    name='zzodrive',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,               # show a console window so the user can close it
    disable_windowed_traceback=False,
    argv_emulation=False,
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
    upx=False,
    upx_exclude=[],
    name='zzodrive',
)
