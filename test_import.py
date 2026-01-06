#!/usr/bin/env python3
"""
Test import and basic functionality
"""

try:
    from nexus_system.cortex.ml_classifier import MLClassifier
    print('✅ Import successful')

    # Test basic functionality
    MLClassifier.load_model()
    print('✅ Model loaded')

    if MLClassifier._model_loaded:
        print('✅ Model is loaded')
        if hasattr(MLClassifier, '_model') and MLClassifier._model:
            if isinstance(MLClassifier._model, dict):
                metadata = MLClassifier._model.get('metadata', {})
                symbols = metadata.get('symbols', [])
                print(f'📊 Symbols in model: {symbols}')
                has_sol = 'SOLUSDT' in symbols
                print(f'SOLUSDT included: {"✅ Yes" if has_sol else "❌ No"}')
            else:
                print('⚠️ Model is not dict format')
        else:
            print('❌ Model not loaded')
    else:
        print('❌ Model not loaded')

except Exception as e:
    print(f'❌ Error: {e}')
    import traceback
    traceback.print_exc()
