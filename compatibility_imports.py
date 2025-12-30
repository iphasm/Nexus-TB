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

print("✅ Compatibility imports loaded successfully")
