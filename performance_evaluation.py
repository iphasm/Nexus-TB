#!/usr/bin/env python3
"""
Evaluación completa del rendimiento del modelo ML optimizado
Análisis de robustez, estabilidad y capacidad predictiva
"""
import os
import time
import joblib
import pandas as pd
import numpy as np
from sklearn.metrics import (
    classification_report, confusion_matrix,
    accuracy_score, precision_recall_fscore_support
)
import warnings
warnings.filterwarnings('ignore')

def log_progress(message, level="INFO"):
    """Logging con timestamps"""
    timestamp = time.strftime("%H:%M:%S", time.localtime())
    print(f"[{timestamp}] {level}: {message}", flush=True)

def load_model_and_data():
    """Carga modelo y prepara datos de evaluación"""
    try:
        # Cargar modelo (expandido si existe, sino normal)
        model_paths = [
            "nexus_system/memory_archives/ml_model_expanded.pkl",
            "nexus_system/memory_archives/ml_model.pkl"
        ]

        model_data = None
        for path in model_paths:
            if os.path.exists(path):
                log_progress(f"Cargando modelo desde {path}")
                model_data = joblib.load(path)
                break

        if not model_data:
            log_progress("ERROR: No se encontró modelo entrenado", "ERROR")
            return None, None, None

        # Preparar datos de evaluación
        from system_directive import get_all_assets
        from train_cortex import fetch_data, add_indicators
        from add_new_features import add_all_new_features

        symbols = get_all_assets()[:4]  # Más símbolos para evaluación robusta
        log_progress(f"Preparando datos de evaluación con {len(symbols)} símbolos")

        evaluation_data = []
        for symbol in symbols:
            log_progress(f"Procesando {symbol} para evaluación...")
            df = fetch_data(symbol, max_candles=1000, verbose=False)

            if df is not None and len(df) > 100:
                df = add_indicators(df)
                df = add_all_new_features(df)
                df['symbol'] = symbol
                evaluation_data.append(df)

        if not evaluation_data:
            log_progress("ERROR: No se obtuvieron datos de evaluación", "ERROR")
            return None, None, None

        # Combinar datos
        eval_df = pd.concat(evaluation_data, ignore_index=True)
        eval_df = eval_df.sort_values('timestamp').reset_index(drop=True)

        log_progress(f"Dataset de evaluación: {len(eval_df):,} filas, {len(eval_df.columns)} columnas")

        return model_data, eval_df, symbols

    except Exception as e:
        log_progress(f"ERROR en carga de datos: {e}", "ERROR")
        return None, None, None

def evaluate_model_robustness(model_data, eval_df):
    """Evaluación completa de robustez del modelo"""
    log_progress("🔬 Iniciando evaluación de robustez del modelo")

    model = model_data['model']
    scaler = model_data.get('scaler')
    label_encoder = model_data['label_encoder']
    feature_names = model_data['feature_names']

    # Preparar datos
    available_features = [f for f in feature_names if f in eval_df.columns]
    X = eval_df[available_features].dropna()
    y = eval_df.loc[X.index, 'target']

    if len(X) < 200:
        log_progress("ERROR: Datos insuficientes para evaluación", "ERROR")
        return None

    log_progress(f"Evaluando con {len(X):,} muestras y {len(available_features)} features")

    # Preparar datos
    if scaler:
        X_scaled = scaler.transform(X)
    else:
        from sklearn.preprocessing import RobustScaler
        scaler = RobustScaler()
        X_scaled = scaler.fit_transform(X)

    y_encoded = label_encoder.transform(y)

    # Predicciones
    predictions = model.predict(X_scaled)
    probabilities = model.predict_proba(X_scaled)

    # Evaluación básica
    accuracy = accuracy_score(y_encoded, predictions)
    log_progress(".3f"
    # Reporte detallado
    report = classification_report(
        y_encoded, predictions,
        target_names=label_encoder.classes_,
        zero_division=0,
        output_dict=True
    )

    # Análisis por estrategia
    strategy_analysis = {}
    for i, strategy in enumerate(label_encoder.classes_):
        strategy_mask = (y_encoded == i)
        if strategy_mask.sum() > 0:
            strategy_acc = accuracy_score(y_encoded[strategy_mask], predictions[strategy_mask])
            strategy_precision = report[strategy]['precision']
            strategy_recall = report[strategy]['recall']
            strategy_f1 = report[strategy]['f1-score']
            strategy_support = report[strategy]['support']

            strategy_analysis[strategy] = {
                'accuracy': strategy_acc,
                'precision': strategy_precision,
                'recall': strategy_recall,
                'f1_score': strategy_f1,
                'support': strategy_support
            }

    return {
        'overall_accuracy': accuracy,
        'strategy_analysis': strategy_analysis,
        'predictions': predictions,
        'probabilities': probabilities,
        'actuals': y_encoded,
        'report': report
    }

def analyze_market_conditions(eval_df, results):
    """Análisis de rendimiento por condiciones de mercado"""
    log_progress("📊 Analizando rendimiento por condiciones de mercado")

    # Definir condiciones de mercado basadas en indicadores
    market_conditions = []

    for idx, row in eval_df.iterrows():
        # Condiciones simplificadas
        volatility = "HIGH" if row.get('atr_pct', 0) > 2.0 else "NORMAL" if row.get('atr_pct', 0) > 1.0 else "LOW"
        trend = "UPTREND" if row.get('adx', 0) > 25 and row.get('close', 0) > row.get('ema_20', 0) else \
                "DOWNTREND" if row.get('adx', 0) > 25 and row.get('close', 0) < row.get('ema_20', 0) else "SIDEWAYS"

        market_conditions.append(f"{volatility}_{trend}")

    # Análisis por condición
    conditions_analysis = {}
    predictions = results['predictions']
    actuals = results['actuals']

    for condition in set(market_conditions):
        condition_mask = [c == condition for c in market_conditions]
        if sum(condition_mask) > 20:  # Suficientes muestras
            condition_acc = accuracy_score(
                actuals[condition_mask],
                predictions[condition_mask]
            )
            conditions_analysis[condition] = {
                'accuracy': condition_acc,
                'samples': sum(condition_mask)
            }

    return conditions_analysis

def evaluate_prediction_confidence(results):
    """Evaluación de confianza en predicciones"""
    log_progress("🎯 Evaluando confianza en predicciones")

    probabilities = results['probabilities']
    predictions = results['predictions']
    actuals = results['actuals']

    # Confianza por predicción (máxima probabilidad)
    confidence_levels = np.max(probabilities, axis=1)

    # Análisis por niveles de confianza
    confidence_bins = [0.4, 0.5, 0.6, 0.7, 0.8, 0.9]
    confidence_analysis = {}

    for threshold in confidence_bins:
        high_conf_mask = confidence_levels >= threshold
        if high_conf_mask.sum() > 50:  # Suficientes muestras
            high_conf_accuracy = accuracy_score(
                actuals[high_conf_mask],
                predictions[high_conf_mask]
            )

            confidence_analysis[f">={threshold:.1f}"] = {
                'accuracy': high_conf_accuracy,
                'samples': high_conf_mask.sum(),
                'percentage': high_conf_mask.sum() / len(confidence_levels) * 100
            }

    return confidence_analysis

def generate_performance_report(results, market_analysis, confidence_analysis):
    """Genera reporte completo de rendimiento"""
    log_progress("📋 Generando reporte completo de rendimiento")

    print("\n" + "=" * 80)
    print("🎯 REPORTE DE RENDIMIENTO DEL MODELO ML OPTIMIZADO")
    print("=" * 80)

    # Rendimiento general
    print("
📊 RENDIMIENTO GENERAL:"    print(".3f"    print(f"   • Estrategias analizadas: {len(results['strategy_analysis'])}")

    # Análisis por estrategia
    print("
🎯 RENDIMIENTO POR ESTRATEGIA:"    print("   Estrategia    | Accuracy | Precision | Recall | F1-Score | Muestras")
    print("   --------------|----------|-----------|--------|----------|----------")

    for strategy, metrics in results['strategy_analysis'].items():
        print("10")

    # Análisis por condiciones de mercado
    if market_analysis:
        print("
🌍 RENDIMIENTO POR CONDICIONES DE MERCADO:"        print("   Condición          | Accuracy | Muestras")
        print("   -------------------|----------|----------")

        for condition, data in market_analysis.items():
            print("19")

    # Análisis de confianza
    if confidence_analysis:
        print("
🎖️  RENDIMIENTO POR NIVEL DE CONFIANZA:"        print("   Confianza | Accuracy | Muestras | Porcentaje")
        print("   ----------|----------|----------|------------")

        for conf_level, data in confidence_analysis.items():
            print("8")

    # Evaluación final
    overall_acc = results['overall_accuracy']
    best_strategy_acc = max([m['accuracy'] for m in results['strategy_analysis'].values()])

    if overall_acc > 0.60 and best_strategy_acc > 0.65:
        final_rating = "🏆 EXCELENTE - Modelo listo para producción"
        confidence_level = "🔒 Alta confianza"
    elif overall_acc > 0.55 and best_strategy_acc > 0.60:
        final_rating = "✅ MUY BUENO - Modelo recomendado para producción"
        confidence_level = "✅ Confianza buena"
    elif overall_acc > 0.50 and best_strategy_acc > 0.55:
        final_rating = "⚠️  ACEPTABLE - Modelo funcional con supervision"
        confidence_level = "⚠️  Confianza moderada"
    else:
        final_rating = "❌ MEJORABLE - Requiere optimizaciones adicionales"
        confidence_level = "❌ Confianza baja"

    print("
🎖️  EVALUACIÓN FINAL:"    print(f"   📊 Rendimiento general: {final_rating}")
    print(f"   🎯 Nivel de confianza: {confidence_level}")
    print(f"   📈 Accuracy promedio: {overall_acc:.1f}%")
    print(f"   🏆 Mejor estrategia: {best_strategy_acc:.1f}%")

    # Recomendaciones
    print("
💡 RECOMENDACIONES:"    if overall_acc < 0.55:
        print("   • Considerar agregar más features técnicas")
        print("   • Revisar balance de clases en el dataset")
        print("   • Experimentar con diferentes hiperparámetros")

    if best_strategy_acc - overall_acc > 0.1:
        print("   • Modelo funciona mejor en estrategias específicas")
        print("   • Considerar modelos especializados por estrategia")

    if market_analysis and len(market_analysis) > 1:
        acc_range = max([d['accuracy'] for d in market_analysis.values()]) - min([d['accuracy'] for d in market_analysis.values()])
        if acc_range > 0.15:
            print("   • Rendimiento variable por condiciones de mercado")
            print("   • Considerar modelos adaptativos por régimen de mercado")

    print("
✅ EVALUACIÓN COMPLETADA"    print("=" * 80)

def save_performance_results(results, market_analysis, confidence_analysis, filename="performance_results.pkl"):
    """Guarda resultados de evaluación de rendimiento"""
    try:
        os.makedirs("results", exist_ok=True)
        filepath = os.path.join("results", filename)

        performance_data = {
            'results': results,
            'market_analysis': market_analysis,
            'confidence_analysis': confidence_analysis,
            'timestamp': time.strftime("%Y-%m-%d %H:%M:%S")
        }

        joblib.dump(performance_data, filepath)
        log_progress(f"💾 Resultados guardados en {filepath}")

    except Exception as e:
        log_progress(f"ERROR guardando resultados: {e}", "ERROR")

def main():
    """Función principal"""
    start_time = time.time()

    try:
        # Cargar modelo y datos
        model_data, eval_df, symbols = load_model_and_data()
        if not model_data or eval_df is None:
            return

        # Evaluación de robustez
        results = evaluate_model_robustness(model_data, eval_df)
        if not results:
            return

        # Análisis por condiciones de mercado
        market_analysis = analyze_market_conditions(eval_df, results)

        # Análisis de confianza
        confidence_analysis = evaluate_prediction_confidence(results)

        # Generar reporte completo
        generate_performance_report(results, market_analysis, confidence_analysis)

        # Guardar resultados
        save_performance_results(results, market_analysis, confidence_analysis)

        # Tiempo total
        total_time = time.time() - start_time
        log_progress(".1f"
    except Exception as e:
        log_progress(f"❌ Error en evaluación de rendimiento: {e}", "ERROR")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
