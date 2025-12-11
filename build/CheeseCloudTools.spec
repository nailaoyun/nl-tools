# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['D:\\workers\\project\\ai\\nly-tool\\main.py'],
    pathex=[],
    binaries=[],
    datas=[('D:\\workers\\project\\ai\\nly-tool\\resources', 'resources'), ('D:\\workers\\project\\ai\\nly-tool\\image', 'image')],
    hiddenimports=['PySide6.QtSvg', 'PySide6.QtSvgWidgets', 'PIL', 'PIL.Image', 'fitz', 'pandas', 'openpyxl', 'matplotlib', 'matplotlib.backends.backend_qtagg'],
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
    name='CheeseCloudTools',
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
    version='D:\\workers\\project\\ai\\nly-tool\\version_info.txt',
    icon=['D:\\workers\\project\\ai\\nly-tool\\build_icons\\app.ico'],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='CheeseCloudTools',
)
