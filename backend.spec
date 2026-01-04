# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller Spec File for Data20 Backend
Phase 7.1: Desktop Embedded Backend

This spec file creates a standalone executable of the FastAPI backend
that can be embedded into the Electron desktop application.

Usage:
    pyinstaller backend.spec

Output:
    dist/data20-backend[.exe]  - Standalone executable
"""

import sys
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# Collect all backend modules
backend_modules = [
    'backend.server',
    'backend.tool_registry',
    'backend.tool_runner',
    'backend.auth',
    'backend.database',
    'backend.database_v2',
    'backend.models',
    'backend.config',
    'backend.logger',
    'backend.metrics',
]

# Collect all tool modules
tool_modules = collect_submodules('tools')

# Hidden imports required by FastAPI and dependencies
hidden_imports = [
    # FastAPI
    'fastapi',
    'fastapi.routing',
    'fastapi.responses',
    'fastapi.middleware',
    'fastapi.middleware.cors',

    # Uvicorn
    'uvicorn',
    'uvicorn.logging',
    'uvicorn.loops',
    'uvicorn.loops.auto',
    'uvicorn.protocols',
    'uvicorn.protocols.http',
    'uvicorn.protocols.http.auto',
    'uvicorn.protocols.http.h11_impl',
    'uvicorn.protocols.websockets',
    'uvicorn.protocols.websockets.auto',
    'uvicorn.lifespan',
    'uvicorn.lifespan.on',

    # Starlette
    'starlette',
    'starlette.routing',
    'starlette.middleware',
    'starlette.middleware.cors',

    # SQLAlchemy
    'sqlalchemy',
    'sqlalchemy.ext',
    'sqlalchemy.ext.declarative',
    'sqlalchemy.orm',
    'sqlalchemy.dialects',
    'sqlalchemy.dialects.sqlite',
    'sqlalchemy.sql',
    'sqlalchemy.sql.default_comparator',

    # Pydantic
    'pydantic',
    'pydantic.fields',
    'pydantic.main',
    'pydantic.types',
    'pydantic_settings',

    # Authentication
    'jose',
    'jose.jwt',
    'passlib',
    'passlib.context',
    'passlib.handlers',
    'passlib.handlers.bcrypt',

    # Logging and Metrics
    'structlog',
    'structlog.processors',
    'structlog.dev',
    'prometheus_client',
    'prometheus_client.core',
    'prometheus_client.registry',

    # Utilities
    'psutil',
    'watchdog',
    'watchdog.observers',
    'multipart',

    # Standard library (sometimes needed)
    'email.mime.multipart',
    'email.mime.text',
    'email.mime.base',
    'asyncio',
]

# Data files to include
datas = [
    # Backend Python files (as data for inspection)
    ('backend/tool_registry.py', 'backend'),
    ('backend/tool_runner.py', 'backend'),
    ('backend/auth.py', 'backend'),
    ('backend/database.py', 'backend'),
    ('backend/database_v2.py', 'backend'),
    ('backend/models.py', 'backend'),
    ('backend/config.py', 'backend'),
    ('backend/logger.py', 'backend'),
    ('backend/metrics.py', 'backend'),

    # Tools directory
    ('tools/', 'tools/'),
]

# Analysis
a = Analysis(
    ['backend/server.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=backend_modules + tool_modules + hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Exclude heavy dependencies not needed in standalone mode
        'celery',
        'kombu',
        'amqp',
        'billiard',
        'redis',
        'psycopg2',
        'psycopg2-binary',

        # Exclude GUI libraries
        'tkinter',
        'matplotlib',
        'PyQt5',
        'PyQt6',

        # Exclude test libraries
        'pytest',
        'unittest',
        'nose',

        # Exclude documentation
        'sphinx',
        'docutils',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# Filter out unnecessary files
def filter_binaries(binaries):
    """Remove unnecessary binary files to reduce size"""
    excluded = [
        'tcl',
        'tk',
        '_tkinter',
    ]
    return [(name, path, type_) for name, path, type_ in binaries
            if not any(ex in name.lower() for ex in excluded)]

a.binaries = filter_binaries(a.binaries)

# PYZ Archive
pyz = PYZ(
    a.pure,
    a.zipped_data,
    cipher=block_cipher
)

# Executable
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='data20-backend',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,  # Compress with UPX
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # Keep console for logging
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='desktop-app/resources/icons/icon.ico' if sys.platform == 'win32' else None,
)

# Post-build information
print("\n" + "="*60)
print("PyInstaller Build Complete!")
print("="*60)
print(f"Executable: dist/data20-backend{'.exe' if sys.platform == 'win32' else ''}")
print("\nNext steps:")
print("1. Test the executable: ./dist/data20-backend --help")
print("2. Copy to Electron app: cp dist/data20-backend* desktop-app/resources/backend/")
print("3. Build Electron app: cd desktop-app && npm run build")
print("="*60 + "\n")
