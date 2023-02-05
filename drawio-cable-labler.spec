# -*- mode: python ; coding: utf-8 -*-


block_cipher = None

added_files = [
    ('main.py', '.'),
    ('scripts/*', 'scripts/'),
    ('tests/drawings/example.drawio', 'tests/drawings/')
]

a = Analysis(
    ['window.py'],
    pathex=[],
    binaries=[],
    datas=added_files,
    hiddenimports=['lxml.etree'],
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
    name='drawio-cable-labler',
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
    icon=['icon/icon.iconset/icon.icns'],
)
app = BUNDLE(
    exe,
    name='drawio-cable-labler.app',
    icon='./icon/icon.iconset/icon.icns',
    bundle_identifier='com.vlrlab.macOS.drawio-cable-labler',
)
