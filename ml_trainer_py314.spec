# -*- mode: python ; coding: utf-8 -*-

import os
import sys

# Calcular project_root de manera confiable
import inspect
current_frame = inspect.currentframe()
if current_frame and '__file__' in current_frame.f_globals:
    # Si estamos ejecutando como script
    project_root = os.path.dirname(os.path.abspath(current_frame.f_globals['__file__']))
else:
    # Si estamos ejecutando como spec, usar SPEC
    project_root = os.path.dirname(os.path.abspath(SPEC))

a = Analysis(
    ['scripts/ml_trainer_gui.py'],
    pathex=[project_root],
    binaries=[],
    datas=[
        (os.path.join(project_root, 'system_directive.py'), '.'),
        (os.path.join(project_root, 'nexus_system'), 'nexus_system'),
        (os.path.join(project_root, 'src'), 'src'),
        (os.path.join(project_root, 'servos'), 'servos'),
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
