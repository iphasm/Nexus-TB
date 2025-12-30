#!/usr/bin/env python3
"""
Verificar qué features se están usando realmente en el modelo
"""
import joblib
from pathlib import Path

def verify_model_features():
    """Verifica las features del modelo guardado"""
    model_path = Path("nexus_system/memory_archives/ml_model.pkl")

    if not model_path.exists():
        print("❌ No se encontró el modelo entrenado")
        return

    try:
        model_data = joblib.load(model_path)
        feature_names = model_data['feature_names']

        print("=" * 60)
        print("🔍 VERIFICACIÓN DE FEATURES DEL MODELO")
        print("=" * 60)
        print(f"📊 Total de features en el modelo: {len(feature_names)}")
        print()

        print("📋 LISTA COMPLETA DE FEATURES:")
        print("-" * 40)
        for i, feature in enumerate(feature_names, 1):
            print("2d")

        print()
        print("🔍 ANÁLISIS DE FEATURES:")

        # Categorizar features
        atr_features = [f for f in feature_names if 'atr' in f.lower()]
        momentum_features = [f for f in feature_names if any(x in f.lower() for x in ['roc', 'rsi', 'mfi', 'williams', 'cci', 'ultimate'])]
        volume_features = [f for f in feature_names if any(x in f.lower() for x in ['volume', 'chaikin', 'force', 'ease'])]
        structure_features = [f for f in feature_names if any(x in f.lower() for x in ['pivot', 'fib', 'dist_sma', 'dist_ema'])]
        correlation_features = [f for f in feature_names if any(x in f.lower() for x in ['morning', 'afternoon', 'gap', 'range'])]
        sentiment_features = [f for f in feature_names if any(x in f.lower() for x in ['bull', 'bear', 'momentum_div', 'vpt', 'intraday'])]

        print(f"   • Features ATR: {len(atr_features)} {atr_features}")
        print(f"   • Features Momentum: {len(momentum_features)}")
        print(f"   • Features Volumen: {len(volume_features)}")
        print(f"   • Features Estructura: {len(structure_features)}")
        print(f"   • Features Correlación: {len(correlation_features)}")
        print(f"   • Features Sentimiento: {len(sentiment_features)}")

        total_new_features = len(momentum_features) + len(volume_features) + len(structure_features) + len(correlation_features) + len(sentiment_features)
        total_old_features = len(feature_names) - total_new_features

        print()
        print("📊 RESUMEN:")
        print(f"   • Features antiguas (v3.1): {total_old_features}")
        print(f"   • Features nuevas (v3.2): {total_new_features}")
        print(".1f")
        if total_new_features == 0:
            print("   ❌ ¡NINGUNA FEATURE NUEVA SE AGREGÓ!")
            print("   💡 Revisa el código de add_new_features.py")
        elif total_new_features < 10:
            print("   ⚠️  POCAS FEATURES NUEVAS")
            print("   💡 Verifica que add_all_new_features() se esté llamando")

        print()
        print("=" * 60)

    except Exception as e:
        print(f"❌ Error cargando modelo: {e}")

if __name__ == "__main__":
    verify_model_features()
