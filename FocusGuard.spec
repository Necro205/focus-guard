# FocusGuard.spec
# PyInstaller spec file — generates a single Windows .exe
#
# Usage:
#   py -3.11 -m PyInstaller FocusGuard.spec --clean
#
# Output: dist/FocusGuard.exe  (≈ 400-600 MB, includes all ML models)

# -*- mode: python ; coding: utf-8 -*-

import sys
from pathlib import Path
from PyInstaller.utils.hooks import collect_all, collect_data_files, collect_submodules

block_cipher = None
project_root = Path('.').absolute()

# ---- Collect everything for known-tricky packages ----
mediapipe_datas, mediapipe_binaries, mediapipe_hiddenimports = collect_all('mediapipe')
ultralytics_datas, ultralytics_binaries, ultralytics_hiddenimports = collect_all('ultralytics')
cv2_datas, cv2_binaries, cv2_hiddenimports = collect_all('cv2')

# Additional hidden imports that PyInstaller often misses
extra_hidden = [
    'PIL._tkinter_finder',
    'scipy.special.cython_special',
    'scipy._lib.messagestream',
    'sklearn.utils._typedefs',
    'sklearn.neighbors._partition_nodes',
    'pandas._libs.tslibs.base',
    'plyer.platforms.win.notification',
]

a = Analysis(
    ['main.py'],
    pathex=[str(project_root)],
    binaries=mediapipe_binaries + ultralytics_binaries + cv2_binaries,
    datas=mediapipe_datas + ultralytics_datas + cv2_datas + [
        # Include YOLO weights if already downloaded
        ('yolov8n.pt', '.') if Path('yolov8n.pt').exists() else ('requirements.txt', '.'),
    ],
    hiddenimports=(
        mediapipe_hiddenimports + ultralytics_hiddenimports +
        cv2_hiddenimports + extra_hidden
    ),
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Exclude stuff we don't need (reduces size)
        'tensorflow', 'torch.distributions', 'torchvision.datasets',
        'IPython', 'jupyter', 'notebook', 'pytest',
    ],
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
    name='FocusGuard',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,              # <-- Konsol gözükmesin
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/icon.ico' if Path('assets/icon.ico').exists() else None,
)
