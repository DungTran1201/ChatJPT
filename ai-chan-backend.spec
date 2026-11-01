# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['C:/Users/PC/Project/ai-chan/packaging/windows/backend_entry.py'],
    pathex=['C:/Users/PC/Project/ai-chan/ai-backend'],
    binaries=[],
    datas=[('C:/Users/PC/Project/ai-chan/ai-backend/database', 'database'), ('C:/Users/PC/Project/ai-chan/ai-backend/data/cache', 'data/cache'), ('C:/Users/PC/Project/ai-chan/ai-backend/data/storage/skills', 'data/storage/skills')],
    hiddenimports=['uvicorn.logging', 'uvicorn.loops', 'uvicorn.loops.auto', 'uvicorn.protocols', 'uvicorn.protocols.http', 'uvicorn.protocols.http.auto', 'uvicorn.protocols.websockets', 'uvicorn.protocols.websockets.auto', 'uvicorn.lifespan', 'uvicorn.lifespan.on', 'uvicorn.lifespan.off', 'sqlite3'],
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
    name='ai-chan-backend',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='ai-chan-backend',
)
