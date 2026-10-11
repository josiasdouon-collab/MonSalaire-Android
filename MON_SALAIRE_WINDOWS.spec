# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all

kivy_datas, kivy_binaries, kivy_hiddenimports = collect_all('kivy')

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=kivy_binaries,
    datas=kivy_datas + [('icon.png', '.'), ('assets', 'assets')],
    hiddenimports=kivy_hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='MON SALAIRE',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    icon='icon.ico',
)
