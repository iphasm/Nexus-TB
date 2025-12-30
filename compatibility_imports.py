"""
Compatibilidad Backward - Imports para código existente
Este archivo permite que el código antiguo siga funcionando
mientras se migra gradualmente a la nueva estructura.
"""

import sys
from pathlib import Path

# Add src to path for imports
project_root = Path(__file__).parent
src_path = project_root / "src"
ml_path = src_path / "ml"

# Ensure paths are in sys.path
for path in [str(project_root), str(src_path), str(ml_path)]:
    if path not in sys.path:
        sys.path.insert(0, path)

# Track what we successfully import
_imported = []
_failed = []

# Try to import from new structure (src.ml)
try:
    from src.ml.train_cortex import fetch_data, add_indicators
    _imported.append('train_cortex')
except ImportError as e:
    _failed.append(f'train_cortex: {e}')
    fetch_data = None
    add_indicators = None

try:
    from src.ml.add_new_features import add_all_new_features
    _imported.append('add_new_features')
except ImportError as e:
    _failed.append(f'add_new_features: {e}')
    add_all_new_features = None

try:
    from src.ml.analyze_features import analyze_model_features
    _imported.append('analyze_features')
except ImportError as e:
    _failed.append(f'analyze_features: {e}')
    analyze_model_features = None

try:
    from src.ml.walk_forward_validation import walk_forward_validation
    _imported.append('walk_forward_validation')
except ImportError as e:
    _failed.append(f'walk_forward_validation: {e}')
    walk_forward_validation = None

try:
    from src.ml.performance_evaluation import evaluate_model_robustness
    _imported.append('performance_evaluation')
except ImportError as e:
    _failed.append(f'performance_evaluation: {e}')
    evaluate_model_robustness = None

try:
    from src.ml.quick_train_expanded import quick_train
    _imported.append('quick_train_expanded')
except ImportError as e:
    _failed.append(f'quick_train_expanded: {e}')
    quick_train = None

# Create mock modules for backward compatibility
def _create_mock_module(name, attributes):
    """Create a mock module with specified attributes"""
    mock = type(sys)('mock_' + name)
    for attr_name, attr_value in attributes.items():
        setattr(mock, attr_name, attr_value)
    return mock

# Inject mock modules into sys.modules for backward compatibility
if fetch_data is not None or add_indicators is not None:
    sys.modules['train_cortex'] = _create_mock_module('train_cortex', {
        'fetch_data': fetch_data,
        'add_indicators': add_indicators
    })

if add_all_new_features is not None:
    sys.modules['add_new_features'] = _create_mock_module('add_new_features', {
        'add_all_new_features': add_all_new_features
    })

if analyze_model_features is not None:
    sys.modules['analyze_features'] = _create_mock_module('analyze_features', {
        'analyze_model_features': analyze_model_features
    })

if walk_forward_validation is not None:
    sys.modules['walk_forward_validation'] = _create_mock_module('walk_forward_validation', {
        'walk_forward_validation': walk_forward_validation
    })

if evaluate_model_robustness is not None:
    sys.modules['performance_evaluation'] = _create_mock_module('performance_evaluation', {
        'evaluate_model_robustness': evaluate_model_robustness
    })

if quick_train is not None:
    sys.modules['train_expanded_model'] = _create_mock_module('train_expanded_model', {
        'quick_train': quick_train
    })

# Re-export for backward compatibility
__all__ = [
    'fetch_data',
    'add_indicators',
    'add_all_new_features',
    'analyze_model_features',
    'walk_forward_validation',
    'evaluate_model_robustness',
    'quick_train'
]

# Print status
if _imported:
    print(f"✅ Compatibility imports loaded: {', '.join(_imported)}")
if _failed:
    print(f"⚠️  Some imports failed (non-critical): {len(_failed)} modules")
    for f in _failed:
        print(f"   - {f}")
