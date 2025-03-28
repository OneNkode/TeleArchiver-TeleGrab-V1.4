# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['tele_archiver.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('config.json', '.'),
        ('lang.json', '.'),
        ('icon.ico', '.')
    ],
    hiddenimports=[
        'telethon',
        'requests',
        'dateutil',
        'PIL',
        'json',
        'asyncio',
        'tkinter',
        'threading',
        'cryptography',
        'aiohttp',
        'python_socks',
        'pytz'
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
    name='tele_archiver',
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
    version='1.3.0',
    icon='icon.ico'
)
