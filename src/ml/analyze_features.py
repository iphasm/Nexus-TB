#!/usr/bin/env python3
"""
Análisis detallado de features del modelo ML entrenado
"""
import os
import joblib
import pandas as pd
import numpy as np
from pathlib import Path

def load_model():
    """Carga el modelo entrenado"""
    model_path = Path("nexus_system/memory_archives/ml_model.pkl")
    scaler_path = Path("nexus_system/memory_archives/scaler.pkl")

    if not model_path.exists():
        print("❌ No se encontró el modelo entrenado")
        return None, None

    try:
        model_data = joblib.load(model_path)
        scaler = joblib.load(scaler_path)

        model = model_data['model']
        label_encoder = model_data['label_encoder']
        feature_names = model_data['feature_names']

        print("✅ Modelo cargado exitosamente")
        print(f"   • Features: {len(feature_names)}")
        print(f"   • Estrategias: {len(label_encoder.classes_)}")

        return model, feature_names, label_encoder.classes_, scaler

    except Exception as e:
        print(f"❌ Error cargando modelo: {e}")
        return None, None, None, None

def analyze_feature_importance(model, feature_names):
    """Analiza la importancia de las features"""
    if not hasattr(model, 'feature_importances_'):
        print("❌ El modelo no tiene información de importancia de features")
        return None

    # Crear DataFrame con importancia de features
    importance_df = pd.DataFrame({
        'feature': feature_names,
        'importance': model.feature_importances_
    }).sort_values('importance', ascending=False)

    return importance_df

def categorize_features(feature_names):
    """Categoriza las features por tipo"""
    categories = {
        'Precio/Volumen': [],
        'Tendencia': [],
        'Momentum': [],
        'Volatilidad': [],
        'Tiempo': [],
        'Otros': []
    }

    for feature in feature_names:
        if any(keyword in feature.lower() for keyword in ['close', 'open', 'high', 'low', 'volume', 'price']):
            categories['Precio/Volumen'].append(feature)
        elif any(keyword in feature.lower() for keyword in ['trend', 'ema', 'sma', 'adx']):
            categories['Tendencia'].append(feature)
        elif any(keyword in feature.lower() for keyword in ['rsi', 'mfi', 'macd', 'stoch']):
            categories['Momentum'].append(feature)
        elif any(keyword in feature.lower() for keyword in ['atr', 'bb_', 'std', 'volatility']):
            categories['Volatilidad'].append(feature)
        elif any(keyword in feature.lower() for keyword in ['hour', 'day', 'time']):
            categories['Tiempo'].append(feature)
        else:
            categories['Otros'].append(feature)

    return categories

def analyze_atr_dependence(importance_df):
    """Analiza específicamente la dependencia de ATR"""
    atr_features = [f for f in importance_df['feature'] if 'atr' in f.lower()]

    if not atr_features:
        print("⚠️  No se encontraron features relacionadas con ATR")
        return 0

    atr_importance = importance_df[importance_df['feature'].isin(atr_features)]['importance'].sum()
    total_importance = importance_df['importance'].sum()

    atr_percentage = (atr_importance / total_importance) * 100

    print("\n📊 DEPENDENCIA ATR:")
    print(f"   • Importancia total ATR: {atr_percentage:.2f}%")
    print(f"   • Features ATR encontradas: {len(atr_features)}")
    if atr_percentage > 25:
        print("   ⚠️  DEPENDENCIA ALTA - Se recomienda agregar más features")
    else:
        print("   ✅ DEPENDENCIA ACEPTABLE")

    return atr_percentage

def analyze_model_features():
    """Función principal que combina todo el análisis del modelo"""
    print("=" * 60)
    print("🔍 ANÁLISIS COMPLETO DEL MODELO ML ENTRENADO")
    print("=" * 60)

    # Cargar modelo
    model, feature_names, strategies, scaler = load_model()
    if not model:
        return None

    # Analizar importancia de features
    importance_df = analyze_feature_importance(model, feature_names)
    if importance_df is None:
        return None

    # Categorizar features
    categories = categorize_features(feature_names)

    # Analizar dependencia ATR
    atr_analysis = analyze_atr_dependence(importance_df)

    print("\n🎯 RESULTADOS DEL ANÁLISIS:")
    print(f"   • Modelo: XGBoost con {len(feature_names)} features")
    print(f"   • Estrategias: {', '.join(strategies)}")

    print("\n🔑 TOP 10 FEATURES MÁS IMPORTANTES:")
    for i, (_, row) in enumerate(importance_df.head(10).iterrows(), 1):
        feature = row['feature']
        importance = row['importance']
        print(".3f")

    print("\n📂 DISTRIBUCIÓN POR CATEGORÍAS:")
    for category, features in categories.items():
        count = len(features)
        percentage = (count / len(feature_names)) * 100
        print(".1f")

    print("\n🎯 DEPENDENCIA ATR:")
    if atr_analysis:
        atr_percentage = atr_analysis['atr_percentage']
        atr_features = atr_analysis['atr_features']
        print(".2f")
        print(f"   • Features ATR encontradas: {atr_features}")

        if atr_percentage < 25:
            print("   ✅ DEPENDENCIA BAJA - Modelo bien diversificado")
        elif atr_percentage < 40:
            print("   ⚠️  DEPENDENCIA MODERADA - Requiere atención")
        else:
            print("   ❌ DEPENDENCIA ALTA - Necesita más features")

    print("=" * 60)
    return {
        'importance_df': importance_df,
        'categories': categories,
        'atr_analysis': atr_analysis,
        'strategies': strategies
    }

def main():
    print("=" * 70)
    print("🔍 ANÁLISIS DE FEATURES - MODELO ML ENTRENADO")
    print("=" * 70)

    # Cargar modelo
    model, feature_names, strategies, scaler = load_model()
    if not model:
        return

    print(f"\n🎯 ESTRATEGIAS DISPONIBLES: {', '.join(strategies)}")
    print()

    # Análisis de importancia de features
    importance_df = analyze_feature_importance(model, feature_names)
    if importance_df is None:
        return

    print("🔑 TOP 15 FEATURES MÁS IMPORTANTES:")
    print("-" * 50)
    for i, (_, row) in enumerate(importance_df.head(15).iterrows(), 1):
        feature = row['feature']
        importance = row['importance']
        bar = "█" * int(importance * 50)

        rank_emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i:2d}"
        print(f"   {rank_emoji} {feature:18} {importance:.3f} {bar}")
    # Categorización de features
    categories = categorize_features(feature_names)

    print("\n📂 DISTRIBUCIÓN DE FEATURES POR CATEGORÍA:")
    print("-" * 50)
    for category, features in categories.items():
        if features:
            count = len(features)
            percentage = (count / len(feature_names)) * 100
            print(f"   • {category:15} {count:2d} features ({percentage:5.1f}%)")
    # Análisis específico de ATR
    atr_percentage = analyze_atr_dependence(importance_df)

    print("\n💡 RECOMENDACIONES DE OPTIMIZACIÓN:")
    print("-" * 50)

    # Analizar balance de categorías
    total_features = len(feature_names)
    volatility_count = len(categories['Volatilidad'])
    trend_count = len(categories['Tendencia'])
    momentum_count = len(categories['Momentum'])

    if volatility_count > trend_count + momentum_count:
        print("⚠️  SOBREDEPENDENCIA DE VOLATILIDAD")
        print("   💡 Agregar más features de momentum y tendencia")

    if 'hour_of_day' in feature_names and 'day_of_week' in feature_names:
        print("✅ FEATURES TEMPORALES INCLUIDOS")
    else:
        print("💡 CONSIDERAR agregar features temporales")

    if atr_percentage > 25:
        print("🔧 OPTIMIZACIONES RECOMENDADAS:")
        print("   • Agregar features de correlación inter-mercado")
        print("   • Incluir datos de order book (spread bid/ask)")
        print("   • Features de sentimiento y volumen avanzado")
        print("   • Reducir importancia de ATR por debajo del 25%")

    print("\n📁 ARCHIVOS ANALIZADOS:")
    print("   • Modelo: nexus_system/memory_archives/ml_model.pkl")
    print("   • Scaler: nexus_system/memory_archives/scaler.pkl")

    print("\n" + "=" * 70)

if __name__ == "__main__":
    main()
