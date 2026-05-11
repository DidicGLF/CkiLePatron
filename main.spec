# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['main.py'],
    binaries=[],
    datas=[
        ('templates', 'templates'),
        ('static',    'static'),
        ('extension', 'extension'),
    ],
    hiddenimports=['flask', 'jinja2', 'werkzeug', 'click'],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    name='CkiLePatron',
    console=False,
    upx=True,
)
