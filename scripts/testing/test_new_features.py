#!/usr/bin/env python3
"""
Test para verificar que las nuevas features se agregan correctamente
"""
from src.ml.train_cortex import fetch_data, add_indicators
from src.ml.add_new_features import add_all_new_features

def test_new_features():
    print("=" * 60)
    print("🧪 TEST - NUEVAS FEATURES")
    print("=" * 60)

    # Paso 1: Obtener datos básicos
    print("\n📊 PASO 1: Fetch de datos...")
    df = fetch_data("BTCUSDT", max_candles=200, verbose=True)

    if df is None or df.empty:
        print("❌ No se pudieron obtener datos")
        return False

    print(f"✅ Datos obtenidos: {len(df)} filas")

    # Paso 2: Agregar indicadores
    print("\n📊 PASO 2: Indicadores básicos...")
    df = add_indicators(df)
    basic_features = len(df.columns)
    print(f"✅ Features después de indicadores: {basic_features}")

    # Verificar features básicas
    expected_basic = ['close', 'rsi', 'adx', 'atr_pct', 'ema_20']
    basic_present = [f for f in expected_basic if f in df.columns]
    print(f"   📋 Features básicas presentes: {len(basic_present)}/5")

    # Paso 3: Agregar nuevas features
    print("\n📊 PASO 3: Nuevas features...")
    df = add_all_new_features(df)
    total_features = len(df.columns)
    new_features = total_features - basic_features

    print(f"✅ Features totales: {total_features} (+{new_features} nuevas)")

    # Verificar categorías de nuevas features
    momentum_features = [f for f in df.columns if f.startswith(('roc_', 'williams_', 'cci_', 'ultimate_'))]
    volume_features = [f for f in df.columns if f.startswith(('volume_', 'chaikin_', 'force_', 'ease_'))]
    structure_features = [f for f in df.columns if f.startswith(('dist_sma', 'dist_sma', 'pivot_', 'fib_'))]
    correlation_features = [f for f in df.columns if f.startswith(('morning_', 'afternoon_', 'gap_', 'range_'))]
    sentiment_features = [f for f in df.columns if f.startswith(('bull_', 'bear_', 'momentum_div', 'vpt', 'intraday_'))]

    print("\n🔍 VERIFICACIÓN DE CATEGORÍAS:")
    print(f"   📈 Momentum: {len(momentum_features)} features")
    print(f"   📊 Volumen: {len(volume_features)} features")
    print(f"   🏗️  Estructura: {len(structure_features)} features")
    print(f"   🔗 Correlación: {len(correlation_features)} features")
    print(f"   😊 Sentimiento: {len(sentiment_features)} features")

    # Verificar algunas features específicas
    key_features = [
        'roc_21', 'williams_r', 'cci', 'volume_roc_5',
        'chaikin_mf', 'dist_sma20', 'pivot_dist', 'gap_up',
        'bull_power', 'intraday_momentum'
    ]

    present_key = [f for f in key_features if f in df.columns]
    print(f"\n🔑 Features clave presentes: {len(present_key)}/10")
    if len(present_key) < 10:
        missing = [f for f in key_features if f not in df.columns]
        print(f"   ❌ Faltan: {missing}")

    # Resultado final
    print("\n" + "=" * 60)
    if new_features >= 25:  # Deberíamos tener al menos 25 nuevas features
        print("🎉 ¡ÉXITO! Las nuevas features se agregaron correctamente")
        print(f"   📊 Total features: {total_features} (+{new_features} nuevas)")
        print("   ✅ Listo para entrenamiento con features expandidas")
        return True
    else:
        print(f"❌ ERROR: Solo se agregaron {new_features} features nuevas")
        print("   💡 Deberían ser al menos 25 nuevas features")
        print("   🔧 Revisar add_new_features.py")
        return False

if __name__ == "__main__":
    success = test_new_features()
    exit(0 if success else 1)
