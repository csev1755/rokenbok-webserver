# -*- mode: python ; coding: utf-8 -*-

import os, re
ref = os.getenv('REF_NAME', '')

github_env = os.getenv('GITHUB_ENV')
if re.match(r'^v\d+\.\d+\.\d+', ref):
    path = 'rokenbok_webserver.py'
    content = open(path).read().replace('version_string = "rokenbok-webserver (dev)"', f'version_string = "rokenbok-webserver {ref}"')
    open(path, 'w').write(content)
else:
    ref = "dev"
if github_env:
    with open(github_env, 'a') as f:
        f.write(f'BUILD_STRING={ref}\n')

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
