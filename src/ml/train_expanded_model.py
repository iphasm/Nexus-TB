#!/usr/bin/env python3
"""
Entrenamiento del modelo con features expandidas (79 features)
Objetivo: Reducir dependencia de ATR por debajo del 25%
"""
import os
import sys
import time
import signal
import logging
import joblib
import pandas as pd
import numpy as np
from tqdm import tqdm
from xgboost import XGBClassifier
from sklearn.preprocessing import RobustScaler, LabelEncoder
from sklearn.model_selection import TimeSeriesSplit
from sklearn.utils.class_weight import compute_sample_weight
from sklearn.metrics import classification_report

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Global interrupt flag
interrupted = False

def signal_handler(signum, frame):
    global interrupted
    interrupted = True
    print("\n⚠️  Entrenamiento interrumpido por el usuario (Ctrl+C)", flush=True)

# Setup signal handling
signal.signal(signal.SIGINT, signal_handler)

def log_progress(message, phase=""):
    """Enhanced logging with timestamps"""
    timestamp = time.strftime("%H:%M:%S", time.localtime())
    if phase:
        print(f"[{timestamp}] {phase} {message}", flush=True)
    else:
        print(f"[{timestamp}] {message}", flush=True)

def load_system_config():
    """Load system configuration"""
    try:
        from system_directive import get_all_assets, is_crypto
        symbols = get_all_assets()
        return symbols
    except Exception as e:
        logger.error(f"Error loading system config: {e}")
        return []

def fetch_training_data(symbols, max_candles=2000, max_symbols=5):
    """Fetch training data with expanded features"""
    from train_cortex import fetch_data, add_indicators
    from add_new_features import add_all_new_features

    log_progress("📊 Iniciando descarga de datos de entrenamiento", "📥")

    # Limit symbols for faster training
    symbols = symbols[:max_symbols]
    log_progress(f"🎯 Usando {len(symbols)} símbolos: {', '.join(symbols[:3])}...")

    all_data = []

    for symbol in symbols:
        if interrupted:
            log_progress("⚠️  Descarga interrumpida por el usuario", "📥")
            break

        log_progress(f"Descargando {symbol}...", "📊")
        df = fetch_data(symbol, max_candles=max_candles, verbose=False)

        if df is not None and not df.empty:
            log_progress(f"✅ {symbol}: {len(df)} filas crudas", "📊")

            # Add indicators
            df = add_indicators(df)

            # Add expanded features
            df = add_all_new_features(df)

            if len(df) > 50:  # Ensure we have enough data
                all_data.append(df)
                log_progress(f"✅ {symbol}: {len(df.columns)} features finales", "📊")
            else:
                log_progress(f"⚠️  {symbol}: Datos insuficientes después del procesamiento", "📊")
        else:
            log_progress(f"❌ {symbol}: Error en descarga", "📊")

    if not all_data:
        log_progress("❌ No se pudo obtener datos de ningún símbolo", "📥")
        return None

    # Combine all data
    log_progress("🔗 Combinando datasets...", "📊")
    full_df = pd.concat(all_data, ignore_index=True)

    log_progress("✅ Dataset combinado listo", "📊")
    log_progress(f"📊 Total filas: {len(full_df):,}", "📊")
    log_progress(f"📈 Total columnas: {len(full_df.columns)}", "📊")

    return full_df

def prepare_features_and_target(df):
    """Prepare features and target for training"""
    log_progress("🔧 Preparando features y target", "🔄")

    # Define feature columns (expanded set)
    X_cols = [
        # Core (original)
        'rsi', 'adx', 'atr_pct', 'trend_str', 'vol_change',
        # v3.0 features
        'macd_hist_norm', 'bb_pct', 'bb_width',
        'roc_5', 'roc_10', 'obv_change',
        'price_position', 'body_pct',
        'above_ema200', 'ema_cross',
        # NEW v3.1 features (reduce ATR dependence)
        'ema20_slope', 'mfi', 'dist_50_high', 'dist_50_low',
        'hour_of_day', 'day_of_week',
        # NEW v3.2 features (further reduce ATR dependence)
        # Momentum features
        'roc_21', 'roc_50', 'williams_r', 'cci', 'ultimate_osc',
        # Volume features
        'volume_roc_5', 'volume_roc_21', 'chaikin_mf', 'force_index', 'ease_movement',
        # Structure features
        'dist_sma20', 'dist_sma50', 'pivot_dist', 'fib_dist',
        # Correlation features
        'morning_volatility', 'afternoon_volatility', 'gap_up', 'gap_down', 'range_change',
        # Sentiment features
        'bull_power', 'bear_power', 'momentum_div', 'vpt', 'intraday_momentum'
    ]

    # Filter to available columns
    available_cols = [col for col in X_cols if col in df.columns]
    missing_cols = [col for col in X_cols if col not in df.columns]

    if missing_cols:
        log_progress(f"⚠️  Features faltantes: {len(missing_cols)}", "🔄")
        log_progress(f"   Faltan: {missing_cols[:5]}...", "🔄")

    log_progress(f"✅ Usando {len(available_cols)} features disponibles", "🔄")

    X = df[available_cols]
    y = df['target']

    # Remove rows with NaN
    initial_rows = len(X)
    valid_rows = X.dropna().index
    X = X.loc[valid_rows]
    y = y.loc[valid_rows]

    final_rows = len(X)
    removed_rows = initial_rows - final_rows

    log_progress(f"🧹 Limpieza de NaN: {initial_rows:,} → {final_rows:,} filas ({removed_rows} removidas)", "🔄")

    return X, y, available_cols

def train_expanded_model(X, y, feature_names):
    """Train model with expanded features"""
    log_progress("🚀 Iniciando entrenamiento del modelo expandido", "🚀")

    # Encode labels
    label_encoder = LabelEncoder()
    y_encoded = label_encoder.fit_transform(y)
    class_names = label_encoder.classes_

    log_progress(f"🏷️  Estrategias detectadas: {', '.join(class_names)}", "🚀")

    # Apply RobustScaler
    log_progress("🔧 Aplicando RobustScaler...", "🚀")
    scaler = RobustScaler()
    X_scaled = scaler.fit_transform(X)

    # Calculate sample weights
    log_progress("⚖️  Calculando pesos de muestra...", "🚀")
    sample_weights = compute_sample_weight('balanced', y_encoded)

    # XGBoost with expanded features
    log_progress("🤖 Configurando XGBoost para features expandidas...", "🚀")
    model = XGBClassifier(
        objective='multi:softprob',
        num_class=len(class_names),
        max_depth=6,  # Slightly deeper for more features
        n_estimators=200,  # Fewer estimators for faster training
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        reg_alpha=0.1,
        reg_lambda=1.0,
        random_state=42,
        n_jobs=-1,
        use_label_encoder=False,
        eval_metric='mlogloss'
    )

    # TimeSeriesSplit Cross-Validation
    log_progress("🔄 Ejecutando validación cruzada chronológica...", "🚀")
    tscv = TimeSeriesSplit(n_splits=3)  # Fewer folds for speed

    cv_scores = []
    for fold, (train_idx, val_idx) in enumerate(tscv.split(X_scaled)):
        if interrupted:
            log_progress("⚠️  CV interrumpida por el usuario", "🚀")
            break

        X_cv_train, X_cv_val = X_scaled[train_idx], X_scaled[val_idx]
        y_cv_train, y_cv_val = y_encoded[train_idx], y_encoded[val_idx]
        weights_cv = sample_weights[train_idx]

        model.fit(X_cv_train, y_cv_train, sample_weight=weights_cv)
        score = model.score(X_cv_val, y_cv_val)
        cv_scores.append(score)
        log_progress(f"   ✅ Fold {fold+1}: {score:.3f}", "🚀")

    if cv_scores:
        cv_mean = np.mean(cv_scores)
        cv_std = np.std(cv_scores)
        log_progress(".3f")
        log_progress(".3f")
    # Final training
    log_progress("🏋️  Entrenamiento final en dataset completo...", "🚀")
    model.fit(X_scaled, y_encoded, sample_weight=sample_weights)

    # Feature importance analysis
    log_progress("🔍 Analizando importancia de features...", "🚀")

    feature_importance = pd.DataFrame({
        'feature': feature_names,
        'importance': model.feature_importances_
    }).sort_values('importance', ascending=False)

    # ATR dependence analysis
    atr_features = [f for f in feature_names if 'atr' in f.lower()]
    if atr_features:
        atr_importance = feature_importance[feature_importance['feature'].isin(atr_features)]['importance'].sum()
        total_importance = feature_importance['importance'].sum()
        atr_percentage = (atr_importance / total_importance) * 100

        log_progress(".2f")
        if atr_percentage < 25:
            log_progress("🎉 ¡DEPENDENCIA ATR REDUCIDA EXITOSAMENTE!", "🚀")
        elif atr_percentage < 40:
            log_progress("✅ Dependencia ATR moderadamente reducida", "🚀")
        else:
            log_progress("⚠️  Dependencia ATR aún alta - considerar más features", "🚀")

    # Save model
    log_progress("💾 Guardando modelo expandido...", "🚀")

    model_dir = "nexus_system/memory_archives"
    os.makedirs(model_dir, exist_ok=True)

    model_data = {
        'model': model,
        'label_encoder': label_encoder,
        'feature_names': feature_names,
        'scaler': scaler,
        'atr_percentage': atr_percentage if 'atr_percentage' in locals() else 0,
        'total_features': len(feature_names),
        'training_date': time.strftime("%Y-%m-%d %H:%M:%S")
    }

    model_path = os.path.join(model_dir, 'ml_model_expanded.pkl')
    joblib.dump(model_data, model_path)

    log_progress(f"✅ Modelo guardado en: {model_path}", "🚀")

    return model, feature_names, cv_scores, atr_percentage

def main():
    """Main training function"""
    print("=" * 70)
    print("🚀 ENTRENAMIENTO MODELO ML - FEATURES EXPANDIDAS")
    print("=" * 70)

    start_time = time.time()

    try:
        # Load configuration
        symbols = load_system_config()
        if not symbols:
            log_progress("❌ Error cargando configuración del sistema", "❌")
            return

        # Fetch and prepare data
        df = fetch_training_data(symbols, max_candles=2000, max_symbols=5)
        if df is None:
            log_progress("❌ Error obteniendo datos de entrenamiento", "❌")
            return

        # Prepare features
        X, y, feature_names = prepare_features_and_target(df)

        if len(X) < 100:
            log_progress("❌ Datos insuficientes para entrenamiento", "❌")
            return

        # Train model
        model, feature_names, cv_scores, atr_percentage = train_expanded_model(X, y, feature_names)

        # Final summary
        total_time = time.time() - start_time
        print("\n" + "=" * 70)
        print("🎉 ENTRENAMIENTO COMPLETADO EXITOSAMENTE")
        print("=" * 70)
        print(".1f")
        print(f"📊 Features utilizadas: {len(feature_names)}")
        print(".3f")
        print(".2f")
        print(f"📁 Modelo guardado: nexus_system/memory_archives/ml_model_expanded.pkl")

        if atr_percentage < 25:
            print("🎯 OBJETIVO ALCANZADO: Dependencia ATR < 25%")
        else:
            print(f"🎯 OBJETIVO PENDIENTE: Dependencia ATR = {atr_percentage:.1f}% (meta: <25%)")

        print("=" * 70)

    except KeyboardInterrupt:
        log_progress("👋 Entrenamiento cancelado por el usuario", "👋")
    except Exception as e:
        log_progress(f"❌ Error durante el entrenamiento: {e}", "❌")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
