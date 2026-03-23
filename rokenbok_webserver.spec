# -*- mode: python ; coding: utf-8 -*-

import os, re
ref = os.getenv('REF_NAME', '')
if re.match(r'^v\d+\.\d+\.\d+', ref):
    path = 'rokenbok_webserver.py'
    content = open(path).read().replace('print(\"rokenbok-webserver (dev)\")', f'print(\"rokenbok-webserver {ref}\")')
    open(path, 'w').write(content)
    github_env = os.getenv('GITHUB_ENV')
    with open(github_env, 'a') as f:
        f.write(f'BUILD_STRING={ref}\n')
else:
    ref = "dev"

print(f"rokenbok-webserver version: {ref}")

a = Analysis(
    ['rokenbok_webserver.py'],
    pathex=[],
    binaries=[('bin', 'bin')],
    datas=[('web', 'web')],
    hiddenimports=['engineio.async_drivers.threading'],
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
    name='rokenbok_webserver',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
