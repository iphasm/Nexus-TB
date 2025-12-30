"""
Compatibilidad Backward - Imports para código existente
Este archivo permite que el código antiguo siga funcionando
mientras se migra gradualmente a la nueva estructura.
"""

# ML Imports (re-export from new structure)
try:
    from src.ml.train_cortex import fetch_data, add_indicators
    from src.ml.add_new_features import add_all_new_features
    from src.ml.analyze_features import analyze_model_features
    from src.ml.walk_forward_validation import walk_forward_validation
    from src.ml.performance_evaluation import evaluate_model_robustness
    from src.ml.train_expanded_model import quick_train
except ImportError as e:
    print(f"⚠️  Warning: Could not import from new structure: {e}")
    print("   Falling back to legacy imports...")

    # Fallback to old imports if new structure fails
    try:
        from train_cortex import fetch_data, add_indicators
        from add_new_features import add_all_new_features
        from analyze_features import analyze_model_features
        from walk_forward_validation import walk_forward_validation
        from performance_evaluation import evaluate_model_robustness
        from train_expanded_model import quick_train
    except ImportError as e2:
        print(f"❌ Error: Could not import legacy modules either: {e2}")
        raise ImportError("Neither new nor legacy ML modules could be imported")

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

# Auto-import for backward compatibility
# This ensures old imports work automatically
import sys
from pathlib import Path

# Add src to path for Railway compatibility
src_path = Path(__file__).parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

print("✅ Compatibility imports loaded successfully")
print(f"✅ Added {src_path} to Python path")

# Try to import from new structure
try:
    from src.ml.train_cortex import fetch_data, add_indicators
    from src.ml.add_new_features import add_all_new_features
    from src.ml.analyze_features import analyze_model_features
    from src.ml.walk_forward_validation import walk_forward_validation
    from src.ml.performance_evaluation import evaluate_model_robustness
    from src.ml.train_expanded_model import quick_train

    # Make them available as if they were in the old locations
    import sys
    current_module = sys.modules[__name__]

    # Inject into sys.modules to simulate old imports
    sys.modules['train_cortex'] = type(sys)('train_cortex')
    sys.modules['train_cortex'].fetch_data = fetch_data
    sys.modules['train_cortex'].add_indicators = add_indicators

    sys.modules['add_new_features'] = type(sys)('add_new_features')
    sys.modules['add_new_features'].add_all_new_features = add_all_new_features

    sys.modules['analyze_features'] = type(sys)('analyze_features')
    sys.modules['analyze_features'].analyze_model_features = analyze_model_features

    sys.modules['walk_forward_validation'] = type(sys)('walk_forward_validation')
    sys.modules['walk_forward_validation'].walk_forward_validation = walk_forward_validation

    sys.modules['performance_evaluation'] = type(sys)('performance_evaluation')
    sys.modules['performance_evaluation'].evaluate_model_robustness = evaluate_model_robustness

    sys.modules['train_expanded_model'] = type(sys)('train_expanded_model')
    sys.modules['train_expanded_model'].quick_train = quick_train

    print("✅ All backward compatibility imports successful")

except ImportError as e:
    print(f"⚠️  Failed to import from new structure: {e}")
    print("   This may cause some features to not work properly")
    raise
