#!/usr/bin/env python3
"""
Validación Walk-Forward Chronológica para evaluación robusta del modelo ML
Simula condiciones reales de trading sin data leakage
"""
import os
import time
import joblib
import pandas as pd
import numpy as np
from sklearn.metrics import classification_report, accuracy_score
from sklearn.preprocessing import RobustScaler, LabelEncoder
from xgboost import XGBClassifier
from sklearn.utils.class_weight import compute_sample_weight
import warnings
warnings.filterwarnings('ignore')

def log_progress(message, level="INFO"):
    """Logging con timestamps"""
    timestamp = time.strftime("%H:%M:%S", time.localtime())
    print(f"[{timestamp}] {level}: {message}", flush=True)

def load_model_data():
    """Carga el modelo entrenado y datos"""
    try:
        # Intentar cargar modelo expandido primero, luego el normal
        model_paths = [
            "nexus_system/memory_archives/ml_model_expanded.pkl",
            "nexus_system/memory_archives/ml_model.pkl"
        ]

        for model_path in model_paths:
            if os.path.exists(model_path):
                log_progress(f"Cargando modelo desde {model_path}")
                model_data = joblib.load(model_path)

                model = model_data['model']
                scaler = model_data.get('scaler')
                label_encoder = model_data['label_encoder']
                feature_names = model_data['feature_names']

                log_progress(f"Modelo cargado: {len(feature_names)} features, {len(label_encoder.classes_)} estrategias")
                return model, scaler, label_encoder, feature_names

        log_progress("ERROR: No se encontró ningún modelo entrenado", "ERROR")
        return None, None, None, None

    except Exception as e:
        log_progress(f"ERROR cargando modelo: {e}", "ERROR")
        return None, None, None, None

def prepare_walk_forward_data(symbols=None, max_candles=3000):
    """Prepara datos para validación walk-forward"""
    from system_directive import get_all_assets
    from train_cortex import fetch_data, add_indicators
    from add_new_features import add_all_new_features

    if symbols is None:
        symbols = get_all_assets()[:5]  # Limitar para validación rápida

    log_progress(f"Preparando datos WF con {len(symbols)} símbolos")

    all_data = []
    for symbol in symbols:
        log_progress(f"Procesando {symbol}...")
        df = fetch_data(symbol, max_candles=max_candles, verbose=False)

        if df is not None and not df.empty:
            df = add_indicators(df)
            df = add_all_new_features(df)

            if len(df) > 100:
                # Agregar columna de símbolo para tracking
                df['symbol'] = symbol
                all_data.append(df)
                log_progress(f"  ✅ {symbol}: {len(df)} filas, {len(df.columns)} features")

    if not all_data:
        log_progress("ERROR: No se obtuvieron datos", "ERROR")
        return None

    # Combinar y ordenar chronológicamente
    df = pd.concat(all_data, ignore_index=True)
    df = df.sort_values('timestamp').reset_index(drop=True)

    log_progress(f"Dataset WF preparado: {len(df):,} filas totales")
    return df

def walk_forward_validation(df, feature_names, label_encoder, n_splits=5):
    """
    Implementa validación walk-forward chronológica

    Divide los datos en ventanas temporales:
    - Entrena en datos pasados
    - Predice en datos futuros
    - Simula condiciones reales de trading
    """
    log_progress("🚀 Iniciando Validación Walk-Forward Chronológica")
    log_progress(f"📊 Configuración: {n_splits} splits temporales")

    # Asegurar que tenemos las features necesarias
    available_features = [f for f in feature_names if f in df.columns]
    if len(available_features) < len(feature_names):
        missing = [f for f in feature_names if f not in df.columns]
        log_progress(f"WARNING: {len(missing)} features faltantes: {missing[:3]}...", "WARN")

    # Preparar datos
    X = df[available_features].dropna()
    y = df.loc[X.index, 'target']

    if len(X) < 500:
        log_progress("ERROR: Datos insuficientes para WF validation", "ERROR")
        return None

    log_progress(f"📈 Datos finales: {len(X):,} muestras, {len(available_features)} features")

    # Calcular tamaños de ventanas
    total_samples = len(X)
    window_size = total_samples // (n_splits + 1)  # Una ventana extra para test final

    results = []
    predictions_all = []
    actuals_all = []

    log_progress("🔄 Ejecutando validación walk-forward...")

    for split in range(n_splits):
        # Definir ventanas temporales
        train_end = (split + 1) * window_size
        test_end = (split + 2) * window_size

        if test_end > total_samples:
            test_end = total_samples

        # Datos de entrenamiento (pasado)
        X_train = X.iloc[:train_end]
        y_train = y.iloc[:train_end]

        # Datos de test (futuro)
        X_test = X.iloc[train_end:test_end]
        y_test = y.iloc[train_end:test_end]

        if len(X_test) < 50:
            log_progress(f"WARNING: Split {split+1} tiene pocos datos de test ({len(X_test)})", "WARN")
            continue

        log_progress(f"  📊 Split {split+1}: Train={len(X_train)}, Test={len(X_test)}")

        # Entrenar modelo en ventana histórica
        model = XGBClassifier(
            objective='multi:softprob',
            num_class=len(label_encoder.classes_),
            max_depth=5,
            n_estimators=100,
            learning_rate=0.05,
            random_state=42 + split,  # Diferente seed por split
            n_jobs=-1
        )

        # Preparar datos
        scaler = RobustScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)

        y_train_encoded = label_encoder.transform(y_train)
        y_test_encoded = label_encoder.transform(y_test)

        sample_weights = compute_sample_weight('balanced', y_train_encoded)

        # Entrenar
        model.fit(X_train_scaled, y_train_encoded, sample_weight=sample_weights)

        # Predecir
        predictions = model.predict(X_test_scaled)
        probabilities = model.predict_proba(X_test_scaled)

        # Métricas
        accuracy = accuracy_score(y_test_encoded, predictions)

        # Análisis de importancia por split
        feature_importance = pd.DataFrame({
            'feature': available_features,
            'importance': model.feature_importances_
        }).sort_values('importance', ascending=False)

        # ATR analysis por split
        atr_features = [f for f in available_features if 'atr' in f.lower()]
        atr_importance = 0
        if atr_features:
            atr_sum = feature_importance[feature_importance['feature'].isin(atr_features)]['importance'].sum()
            atr_importance = (atr_sum / feature_importance['importance'].sum()) * 100

        # Guardar resultados del split
        split_result = {
            'split': split + 1,
            'train_samples': len(X_train),
            'test_samples': len(X_test),
            'accuracy': accuracy,
            'atr_importance': atr_importance,
            'predictions': predictions,
            'actuals': y_test_encoded,
            'probabilities': probabilities,
            'feature_importance': feature_importance
        }

        results.append(split_result)
        predictions_all.extend(predictions)
        actuals_all.extend(y_test_encoded)

        log_progress(f"    ✅ Accuracy: {accuracy:.3f}, ATR: {atr_importance:.1f}%")

    # Resultados globales
    if results:
        accuracies = [r['accuracy'] for r in results]
        atr_importances = [r['atr_importance'] for r in results]

        wf_accuracy = np.mean(accuracies)
        wf_accuracy_std = np.std(accuracies)
        wf_atr_avg = np.mean(atr_importances)

        log_progress("\n🎯 RESULTADOS WALK-FORWARD:")
        log_progress(".3f")
        log_progress(".3f")
        log_progress(".1f")
        # Análisis de estabilidad
        if wf_accuracy_std < 0.05:
            stability = "🔒 MUY ESTABLE"
        elif wf_accuracy_std < 0.10:
            stability = "✅ ESTABLE"
        else:
            stability = "⚠️  INESTABLE"

        log_progress(f"   📊 Estabilidad temporal: {stability}")

        # Evaluación general
        if wf_accuracy > 0.55 and wf_atr_avg < 25:
            overall_rating = "🏆 EXCELENTE - Modelo robusto y optimizado"
        elif wf_accuracy > 0.50 and wf_atr_avg < 35:
            overall_rating = "✅ BUENO - Modelo funcional con optimizaciones"
        elif wf_accuracy > 0.45:
            overall_rating = "⚠️  ACEPTABLE - Requiere mejoras"
        else:
            overall_rating = "❌ DEFICIENTE - Necesita revisión completa"

        log_progress(f"   🎖️  Evaluación general: {overall_rating}")

        return {
            'results': results,
            'overall_accuracy': wf_accuracy,
            'accuracy_std': wf_accuracy_std,
            'atr_importance_avg': wf_atr_avg,
            'predictions': np.array(predictions_all),
            'actuals': np.array(actuals_all),
            'stability': wf_accuracy_std
        }

    return None

def analyze_walk_forward_results(results):
    """Análisis detallado de resultados de WF validation"""
    if not results:
        return

    log_progress("\n🔍 ANÁLISIS DETALLADO WALK-FORWARD")

    # Análisis por split
    log_progress("📊 Rendimiento por ventana temporal:")
    for i, split_result in enumerate(results['results'], 1):
        acc = split_result['accuracy']
        atr = split_result['atr_importance']
        train_size = split_result['train_samples']
        test_size = split_result['test_samples']

        trend = "📈" if acc > results['overall_accuracy'] else "📉"
        log_progress(f"  {trend} Ventana {i}: {acc:.3f} acc, {atr:.1f}% ATR ({train_size}→{test_size})")

    # Análisis de estabilidad
    stability = results['stability']
    if stability < 0.03:
        stability_msg = "🔒 Excelente estabilidad - Modelo consistente en el tiempo"
    elif stability < 0.07:
        stability_msg = "✅ Buena estabilidad - Modelo confiable"
    elif stability < 0.12:
        stability_msg = "⚠️  Estabilidad moderada - Revisar con más datos"
    else:
        stability_msg = "❌ Baja estabilidad - Posible overfitting"

    log_progress(f"\n🎯 Estabilidad temporal: {stability_msg}")

    # Análisis de dependencia ATR
    atr_avg = results['atr_importance_avg']
    if atr_avg < 20:
        atr_msg = "🎉 Dependencia ATR muy baja - Excelente diversificación"
    elif atr_avg < 30:
        atr_msg = "✅ Dependencia ATR aceptable - Buen balance"
    elif atr_avg < 40:
        atr_msg = "⚠️  Dependencia ATR moderada - Requiere atención"
    else:
        atr_msg = "❌ Dependencia ATR alta - Necesita más features"

    log_progress(f"🎯 Dependencia ATR: {atr_msg}")

    # Reporte de clasificación detallado
    log_progress("\n📋 REPORTE DE CLASIFICACIÓN DETALLADO:")
    from sklearn.metrics import classification_report
    report = classification_report(
        results['actuals'],
        results['predictions'],
        target_names=['grid', 'mean_rev', 'scalp', 'trend'],  # Ajustar según el label encoder
        zero_division=0
    )
    print(report)

def save_walk_forward_results(results, filename="wf_validation_results.pkl"):
    """Guarda resultados de validación walk-forward"""
    if results:
        os.makedirs("results", exist_ok=True)
        filepath = os.path.join("results", filename)

        # Convertir arrays numpy a listas para serialización
        results_copy = results.copy()
        results_copy['predictions'] = results_copy['predictions'].tolist()
        results_copy['actuals'] = results_copy['actuals'].tolist()

        joblib.dump(results_copy, filepath)
        log_progress(f"💾 Resultados guardados en {filepath}")

        return filepath

    return None

def main():
    """Función principal"""
    print("=" * 70)
    print("🔬 VALIDACIÓN WALK-FORWARD CHRONOLÓGICA")
    print("Simula condiciones reales de trading sin data leakage")
    print("=" * 70)

    start_time = time.time()

    try:
        # Cargar modelo
        model, scaler, label_encoder, feature_names = load_model_data()
        if not model:
            return

        # Preparar datos
        df = prepare_walk_forward_data(max_candles=2000)
        if df is None:
            return

        # Ejecutar validación walk-forward
        results = walk_forward_validation(df, feature_names, label_encoder, n_splits=4)

        if results:
            # Análisis detallado
            analyze_walk_forward_results(results)

            # Guardar resultados
            saved_file = save_walk_forward_results(results)

            # Resumen final
            total_time = time.time() - start_time
            print("\n" + "=" * 70)
            print("✅ VALIDACIÓN WALK-FORWARD COMPLETADA")
            print("=" * 70)
            print(".1f")
            print(".3f")
            print(".1f")
            print(f"📁 Resultados guardados: {saved_file}")

            if results['overall_accuracy'] > 0.55 and results['atr_importance_avg'] < 25:
                print("🏆 RESULTADO: Modelo EXCELENTE para producción")
            elif results['overall_accuracy'] > 0.50:
                print("✅ RESULTADO: Modelo BUENO para producción")
            else:
                print("⚠️  RESULTADO: Modelo requiere mejoras adicionales")

        else:
            log_progress("❌ Validación walk-forward fallida", "ERROR")

    except Exception as e:
        log_progress(f"❌ Error en validación WF: {e}", "ERROR")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
