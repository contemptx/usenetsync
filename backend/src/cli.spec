# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec file for UsenetSync CLI

import sys
import os
from PyInstaller.utils.hooks import collect_all, collect_submodules

block_cipher = None

# Collect all data files and hidden imports
datas = []
hiddenimports = [
    'nntp',
    'pynntp',
    'click',
    'psycopg2',
    'cryptography',
    'bcrypt',
    'asyncio',
    'asyncpg',
    'sqlalchemy',
    'aiohttp',
    'aiofiles',
    'upload.enhanced_upload',
    'upload.enhanced_upload_system',
    'upload.segment_packing_system',
    'upload.publishing_system',
    'upload.upload_queue_manager',
    'download.enhanced_download',
    'download.enhanced_download_system',
    'database.postgresql_manager',
    'networking.production_nntp_client',
    'security.enhanced_security_system',
    'indexing.share_id_generator',
    'core.integrated_backend',
    'publishing.publishing_system',
    'monitoring.system_monitor',
    'queue.queue_manager',
    'optimization.performance_optimizer',
    'licensing.license_manager',
    'config.config_manager',
    'utils.file_utils',
]

# Add all submodules
for module in ['upload', 'download', 'database', 'networking', 'security', 
               'indexing', 'core', 'publishing', 'monitoring', 'queue',
               'optimization', 'licensing', 'config', 'utils']:
    try:
        hiddenimports.extend(collect_submodules(module))
    except:
        pass

a = Analysis(
    ['cli.py'],
    pathex=[os.path.dirname(os.path.abspath('cli.py'))],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
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
    name='usenetsync-cli',
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
    icon=None
)