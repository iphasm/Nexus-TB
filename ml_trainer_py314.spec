# -*- mode: python ; coding: utf-8 -*-

import os
import sys

project_root = r"C:\Users\iphas\OneDrive\Documents\GitHub\Nexus-TB"

a = Analysis(
    ['scripts/ml_trainer_gui.py'],
    pathex=[r"C:\Users\iphas\OneDrive\Documents\GitHub\Nexus-TB"],
    binaries=[],
    datas=[
        (r"C:\Users\iphas\OneDrive\Documents\GitHub\Nexus-TB\system_directive.py", '.'),
        (r"C:\Users\iphas\OneDrive\Documents\GitHub\Nexus-TB\nexus_system", 'nexus_system'),
        (r"C:\Users\iphas\OneDrive\Documents\GitHub\Nexus-TB\src", 'src'),
        (r"C:\Users\iphas\OneDrive\Documents\GitHub\Nexus-TB\servos", 'servos'),
    ],
    hiddenimports=[
        'tkinter', 'tkinter.ttk', 'tkinter.scrolledtext',
        'tkinter.messagebox', 'tkinter.filedialog',
        'system_directive', 'servos.voight_kampff',
        'nexus_system.cortex.ml_classifier',
        'pandas.plotting._matplotlib', 'pandas.plotting._core',
        'sklearn.utils._weight_vector', 'sklearn.utils._cython_blas',
        'xgboost.core', 'xgboost.sklearn',
        'joblib.numpy_pickle_utils', 'joblib.compression',
        'yfinance.utils', 'yfinance.ticker',
        # pandas-ta-openbb compatible con Python 3.14 (instalado desde PyPI)
        'pandas_ta', 'pandas_ta.momentum', 'pandas_ta.trend', 'pandas_ta.volatility',
        'pandas_ta.overlap', 'pandas_ta.volume', 'pandas_ta.statistics',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter.test', 'test', 'unittest', 'pdb', 'pydoc',
        'doctest', 'sqlite3', 'dbm', 'gdbm', 'readline', 'rlcompleter',
        # Excluir dependencias problemáticas (pandas-ta-openbb ya incluido)
        'numba', 'llvmlite',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='Nexus_ML_Trainer_PY314',
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
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Nexus_ML_Trainer_PY314'
)
