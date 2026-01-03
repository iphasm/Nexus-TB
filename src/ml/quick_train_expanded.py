#!/usr/bin/env python3
"""
Entrenamiento rápido del modelo con features expandidas
"""
import os
import time
import joblib
import pandas as pd
from xgboost import XGBClassifier
from sklearn.preprocessing import RobustScaler, LabelEncoder
from sklearn.utils.class_weight import compute_sample_weight

def quick_train():
    """Entrenamiento rápido con features expandidas"""
    print("=" * 60)
    print("🚀 ENTRENAMIENTO RÁPIDO - FEATURES EXPANDIDAS")
    print("=" * 60)

    start_time = time.time()

    try:
        # Cargar datos existentes - usar activos HABILITADOS
        print("📂 Cargando datos existentes...")
        from system_directive import ASSET_GROUPS, GROUP_CONFIG
        from train_cortex import fetch_data, add_indicators
        from add_new_features import add_all_new_features

        # Solo usar activos de grupos habilitados
        enabled_symbols = []
        for group_name, assets in ASSET_GROUPS.items():
            if GROUP_CONFIG.get(group_name, True):
                enabled_symbols.extend(assets)
        enabled_symbols = list(set(enabled_symbols))  # Remover duplicados

        symbols = enabled_symbols[:5]  # Solo 5 símbolos para rapidez (de los habilitados)
        all_data = []

        for symbol in symbols:
            print(f"  📊 Procesando {symbol}...")
            df = fetch_data(symbol, max_candles=500, verbose=False)
            if df is not None and not df.empty:
                df = add_indicators(df)
                df = add_all_new_features(df)
                if len(df) > 20:
                    all_data.append(df)
                    print(f"    ✅ {len(df.columns)} features, {len(df)} filas")

        if not all_data:
            print("❌ No se obtuvieron datos")
            return

        # Combinar datos
        df = pd.concat(all_data, ignore_index=True)
        print(f"📊 Dataset total: {len(df):,} filas, {len(df.columns)} columnas")

        # Preparar features
        X_cols = [col for col in df.columns if col != 'target' and not col.startswith(('timestamp', 'open', 'high', 'low', 'close', 'volume'))]
        X = df[X_cols].dropna()
        y = df.loc[X.index, 'target']

        print(f"🎯 Features finales: {len(X_cols)}")
        print(f"📈 Muestras de entrenamiento: {len(X):,}")

        # Entrenar modelo
        print("🤖 Entrenando modelo XGBoost...")

        label_encoder = LabelEncoder()
        y_encoded = label_encoder.fit_transform(y)

        scaler = RobustScaler()
        X_scaled = scaler.fit_transform(X)

        sample_weights = compute_sample_weight('balanced', y_encoded)

        model = XGBClassifier(
            objective='multi:softprob',
            num_class=len(label_encoder.classes_),
            max_depth=4,
            n_estimators=100,
            learning_rate=0.1,
            random_state=42,
            n_jobs=-1
        )

        model.fit(X_scaled, y_encoded, sample_weight=sample_weights)

        # Análisis de importancia
        importance_df = pd.DataFrame({
            'feature': X_cols,
            'importance': model.feature_importances_
        }).sort_values('importance', ascending=False)

        # ATR analysis
        atr_features = [f for f in X_cols if 'atr' in f.lower()]
        if atr_features:
            atr_importance = importance_df[importance_df['feature'].isin(atr_features)]['importance'].sum()
            total_importance = importance_df['importance'].sum()
            atr_percentage = (atr_importance / total_importance) * 100
        else:
            atr_percentage = 0

        print("\n🔑 TOP 10 FEATURES:")
        for i, (_, row) in enumerate(importance_df.head(10).iterrows(), 1):
            feature = row['feature']
            importance = row['importance']
            print(".3f")

        print("\n📊 DEPENDENCIA ATR:")
        print(".2f")

        if atr_percentage < 25:
            print("🎉 ¡OBJETIVO ALCANZADO! Dependencia ATR < 25%")
        elif atr_percentage < 40:
            print("✅ Dependencia ATR reducida moderadamente")
        else:
            print("⚠️  Dependencia ATR aún alta")

        # Guardar modelo expandido
        print("💾 Guardando modelo expandido...")
        model_data = {
            'model': model,
            'scaler': scaler,
            'label_encoder': label_encoder,
            'feature_names': X_cols,
            'atr_percentage': atr_percentage,
            'total_features': len(X_cols),
            'training_date': time.strftime("%Y-%m-%d %H:%M:%S")
        }

        os.makedirs("nexus_system/memory_archives", exist_ok=True)
        joblib.dump(model_data, "nexus_system/memory_archives/ml_model_expanded.pkl")

        training_time = time.time() - start_time
        print(".1f")
        print("✅ Modelo expandido guardado exitosamente!")

        return atr_percentage

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    atr_final = quick_train()
    if atr_final is not None:
        print(f"\n🎯 RESULTADO FINAL: Dependencia ATR = {atr_final:.1f}%")
        if atr_final < 25:
            print("🏆 ¡ÉXITO! Modelo optimizado con dependencia ATR reducida!")
        else:
            print("📈 Modelo entrenado pero ATR aún alto - considerar más features")
