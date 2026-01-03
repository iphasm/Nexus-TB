#!/usr/bin/env python3
"""
AUDITORÍA COMPLETA: ML Classifier y Entrenamiento
================================================

Audita el estado actual del ML Classifier y compara con la configuración de activos.
Verifica consistencia entre modelo entrenado y activos configurados.
"""

import os
import sys
import joblib
import pandas as pd
import numpy as np
from datetime import datetime
from system_directive import get_all_assets, ASSET_GROUPS, GROUP_CONFIG

def audit_ml_classifier():
    """Audita completamente el ML Classifier."""

    print("🔬 AUDITORÍA ML CLASSIFIER")
    print("=" * 60)

    # 1. Verificar archivos del modelo
    print("\n1️⃣ VERIFICACIÓN DE ARCHIVOS DEL MODELO")
    print("-" * 40)

    model_path = "nexus_system/memory_archives/ml_model.pkl"
    scaler_path = "nexus_system/memory_archives/scaler.pkl"

    model_exists = os.path.exists(model_path)
    scaler_exists = os.path.exists(scaler_path)

    print(f"📁 Modelo: {'✅' if model_exists else '❌'} {model_path}")
    print(f"📁 Scaler: {'✅' if scaler_exists else '❌'} {scaler_path}")

    if not model_exists:
        print("❌ CRÍTICO: Modelo no encontrado - usando solo clasificación rule-based")
        return False

    # 2. Cargar y analizar modelo
    print("\n2️⃣ ANÁLISIS DEL MODELO")
    print("-" * 40)

    try:
        model_data = joblib.load(model_path)
        if isinstance(model_data, dict):
            model = model_data.get('model')
            label_encoder = model_data.get('label_encoder')
            feature_names = model_data.get('feature_names')
            print("✅ Modelo cargado (formato bundle)")
        else:
            model = model_data
            label_encoder = None
            feature_names = None
            print("⚠️  Modelo cargado (formato legacy)")

        print(f"🔧 Tipo de modelo: {type(model).__name__}")

        if hasattr(model, 'n_features_in_'):
            print(f"📊 Features esperadas: {model.n_features_in_}")

        if label_encoder:
            classes = label_encoder.classes_
            print(f"🎯 Clases objetivo: {list(classes)}")

        if feature_names:
            print(f"📈 Features del modelo: {len(feature_names)}")
            print(f"   Primeras 5: {feature_names[:5]}")
            print(f"   Últimas 5: {feature_names[-5:]}")

    except Exception as e:
        print(f"❌ Error cargando modelo: {e}")
        return False

    # 3. Verificar scaler
    print("\n3️⃣ VERIFICACIÓN DEL SCALER")
    print("-" * 40)

    if scaler_exists:
        try:
            scaler = joblib.load(scaler_path)
            print(f"✅ Scaler cargado: {type(scaler).__name__}")
            if hasattr(scaler, 'feature_names_in_'):
                print(f"📊 Features en scaler: {len(scaler.feature_names_in_)}")
        except Exception as e:
            print(f"❌ Error cargando scaler: {e}")
    else:
        print("⚠️  Scaler no encontrado - usando features sin escalar")

    # 4. Análisis de activos configurados vs modelo
    print("\n4️⃣ ANÁLISIS DE ACTIVOS")
    print("-" * 40)

    current_assets = get_all_assets()
    print(f"📊 Total de activos configurados: {len(current_assets)}")

    # Desglose por grupos
    print("\n📂 DESGLOSE POR GRUPOS:")
    for group_name, assets in ASSET_GROUPS.items():
        enabled = GROUP_CONFIG.get(group_name, True)
        status = "✅" if enabled else "❌"
        print(f"   {status} {group_name}: {len(assets)} activos")

    # Activos habilitados actualmente
    enabled_assets = []
    for group_name, assets in ASSET_GROUPS.items():
        if GROUP_CONFIG.get(group_name, True):
            enabled_assets.extend(assets)

    enabled_assets = list(set(enabled_assets))  # Remover duplicados
    print(f"\n🎯 Activos HABILITADOS actualmente: {len(enabled_assets)}")

    # Verificar si el modelo conoce estos activos
    if feature_names:
        model_known_assets = []
        for asset in enabled_assets:
            # Verificar si el asset aparece en los nombres de features
            asset_in_model = any(asset.upper() in str(name).upper()
                               for name in feature_names[:20])  # Solo primeros 20 para eficiencia
            if asset_in_model:
                model_known_assets.append(asset)

        coverage = len(model_known_assets) / len(enabled_assets) * 100
        print(f"📊 Cobertura del modelo: {coverage:.1f}%")
        print(f"📈 Cobertura del modelo: {len(model_known_assets)}/{len(enabled_assets)} activos")

        if coverage < 80:
            print("⚠️  ADVERTENCIA: Cobertura baja - modelo necesita reentrenamiento")
        else:
            print("✅ Cobertura buena - modelo actualizado")

    # 5. Verificar características del modelo
    print("\n5️⃣ CARACTERÍSTICAS DEL MODELO")
    print("-" * 40)

    try:
        # Verificar importancia de features si está disponible
        if hasattr(model, 'feature_importances_'):
            importances = model.feature_importances_
            top_features = np.argsort(importances)[-5:][::-1]  # Top 5
            print("🏆 Top 5 features más importantes:")
            for i, idx in enumerate(top_features):
                if feature_names and idx < len(feature_names):
                    feature_name = feature_names[idx]
                else:
                    feature_name = f"feature_{idx}"
                importance = importances[idx]
                print(f"   {i+1}. {feature_name}: {importance:.4f}")

        # Verificar parámetros del modelo
        if hasattr(model, 'get_params'):
            params = model.get_params()
            print("\n🔧 Parámetros clave:")
            print(f"   learning_rate: {params.get('learning_rate', 'N/A')}")
            print(f"   max_depth: {params.get('max_depth', 'N/A')}")
            print(f"   n_estimators: {params.get('n_estimators', 'N/A')}")

    except Exception as e:
        print(f"❌ Error analizando características: {e}")

    # 6. Recomendaciones
    print("\n6️⃣ RECOMENDACIONES")
    print("-" * 40)

    issues = []

    if not model_exists:
        issues.append("❌ Modelo faltante - reentrenar urgentemente")

    if not scaler_exists:
        issues.append("⚠️  Scaler faltante - features sin normalizar")

    if feature_names and len(feature_names) < 50:
        issues.append("⚠️  Pocos features - modelo sub-optimizado")

    if hasattr(model, 'feature_importances_'):
        importances = model.feature_importances_
        if np.max(importances) > 0.5:
            issues.append("⚠️  Feature dominance - posible overfitting")

    if issues:
        print("🚨 PROBLEMAS IDENTIFICADOS:")
        for issue in issues:
            print(f"   {issue}")
    else:
        print("✅ No se encontraron problemas críticos")

    # 7. Estado final
    print("\n" + "=" * 60)
    print("🎯 RESULTADO DE LA AUDITORÍA")

    if issues and any("❌" in issue for issue in issues):
        print("❌ AUDITORÍA FALLIDA - Requiere reentrenamiento inmediato")
        return False
    elif issues:
        print("⚠️  AUDITORÍA CON ADVERTENCIAS - Reentrenamiento recomendado")
        return True
    else:
        print("✅ AUDITORÍA EXITOSA - Modelo en buen estado")
        return True

def audit_training_module():
    """Audita el módulo de entrenamiento."""

    print("\n\n🔧 AUDITORÍA MÓDULO DE ENTRENAMIENTO")
    print("=" * 60)

    # Verificar que el script existe
    training_script = "src/ml/train_cortex.py"
    if not os.path.exists(training_script):
        print(f"❌ Script de entrenamiento no encontrado: {training_script}")
        return False

    print(f"✅ Script encontrado: {training_script}")

    # Verificar dependencias
    try:
        import xgboost
        import sklearn
        import pandas_ta
        print("✅ Dependencias ML disponibles")
    except ImportError as e:
        print(f"❌ Dependencia faltante: {e}")
        return False

    # Verificar configuración de activos
    try:
        from system_directive import get_all_assets
        assets = get_all_assets()
        enabled_assets = []

        for group_name, group_assets in ASSET_GROUPS.items():
            if GROUP_CONFIG.get(group_name, True):
                enabled_assets.extend(group_assets)

        enabled_assets = list(set(enabled_assets))

        print(f"📊 Activos configurados: {len(assets)}")
        print(f"🎯 Activos habilitados: {len(enabled_assets)}")

        # Verificar que no haya activos duplicados
        duplicates = [x for x in assets if assets.count(x) > 1]
        if duplicates:
            print(f"⚠️  Activos duplicados encontrados: {set(duplicates)}")
        else:
            print("✅ No hay activos duplicados")

    except Exception as e:
        print(f"❌ Error verificando configuración: {e}")
        return False

    return True

if __name__ == "__main__":
    print(f"🤖 Nexus ML Classifier Audit - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)

    # Auditar clasificador
    classifier_ok = audit_ml_classifier()

    # Auditar módulo de entrenamiento
    training_ok = audit_training_module()

    # Resultado final
    print("\n" + "=" * 80)
    print("🎯 RESULTADO FINAL DE AUDITORÍA")

    if classifier_ok and training_ok:
        print("✅ SISTEMA ML OPERATIVO - Todo en orden")
        sys.exit(0)
    elif classifier_ok:
        print("⚠️  CLASIFICADOR OK - Módulo de entrenamiento necesita revisión")
        sys.exit(1)
    else:
        print("❌ REENTRENAMIENTO REQUERIDO - Sistema ML necesita atención")
        sys.exit(1)
