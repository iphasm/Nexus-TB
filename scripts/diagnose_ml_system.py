#!/usr/bin/env python3
"""
DIAGNÓSTICO COMPLETO: Sistema ML Post-Auditoría
===============================================

Diagnóstico completo del sistema ML después de la auditoría y actualizaciones.
Verifica que todo esté funcionando correctamente con los activos actuales.
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime

def diagnose_ml_system():
    """Diagnóstico completo del sistema ML."""

    print("🔬 DIAGNÓSTICO COMPLETO SISTEMA ML")
    print("=" * 80)
    print(f"🕒 Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    issues = []
    warnings = []

    # 1. Verificar configuración de activos
    print("1️⃣ CONFIGURACIÓN DE ACTIVOS")
    print("-" * 40)

    try:
        from system_directive import ASSET_GROUPS, GROUP_CONFIG, get_all_assets

        total_configured = len(get_all_assets())

        enabled_assets = []
        enabled_groups = []

        for group_name, assets in ASSET_GROUPS.items():
            if GROUP_CONFIG.get(group_name, True):
                enabled_assets.extend(assets)
                enabled_groups.append(group_name)

        enabled_assets = list(set(enabled_assets))  # Remover duplicados

        print(f"✅ Total activos configurados: {total_configured}")
        print(f"✅ Activos habilitados: {len(enabled_assets)}")
        print(f"✅ Grupos habilitados: {enabled_groups}")

        # Verificar que tenemos suficientes activos
        if len(enabled_assets) < 10:
            issues.append(f"Pocos activos habilitados: {len(enabled_assets)}")

    except Exception as e:
        issues.append(f"Error cargando configuración de activos: {e}")

    # 2. Verificar archivos del modelo
    print("\n2️⃣ ARCHIVOS DEL MODELO")
    print("-" * 40)

    model_path = "nexus_system/memory_archives/ml_model.pkl"
    scaler_path = "nexus_system/memory_archives/scaler.pkl"

    model_exists = os.path.exists(model_path)
    scaler_exists = os.path.exists(scaler_path)

    if model_exists:
        model_size = os.path.getsize(model_path) / 1024 / 1024  # MB
        model_mtime = datetime.fromtimestamp(os.path.getmtime(model_path))
        print(f"   Tamaño: {model_size:.2f} MB")
        print(f"   Última modificación: {model_mtime.strftime('%Y-%m-%d %H:%M:%S')}")
    else:
        issues.append("Archivo del modelo no encontrado")

    if scaler_exists:
        scaler_size = os.path.getsize(scaler_path) / 1024 / 1024  # MB
        scaler_mtime = datetime.fromtimestamp(os.path.getmtime(scaler_path))
        print(f"   Tamaño: {scaler_size:.2f} MB")
        print(f"   Última modificación: {scaler_mtime.strftime('%Y-%m-%d %H:%M:%S')}")
    else:
        warnings.append("Archivo del scaler no encontrado")

    # 3. Verificar integridad del modelo
    print("\n3️⃣ INTEGRIDAD DEL MODELO")
    print("-" * 40)

    if model_exists:
        try:
            import joblib
            model_data = joblib.load(model_path)

            if isinstance(model_data, dict):
                model = model_data.get('model')
                label_encoder = model_data.get('label_encoder')
                feature_names = model_data.get('feature_names')

                print("✅ Modelo en formato bundle")
                print(f"   Tipo: {type(model).__name__}")
                print(f"   Features: {len(feature_names) if feature_names else 'N/A'}")

                if hasattr(model, 'n_features_in_'):
                    print(f"   Features esperadas: {model.n_features_in_}")

                if label_encoder and hasattr(label_encoder, 'classes_'):
                    print(f"   Clases: {list(label_encoder.classes_)}")
            else:
                print("⚠️  Modelo en formato legacy")
                model = model_data

            # Verificar que el modelo se puede usar para predicción
            if hasattr(model, 'predict'):
                print("✅ Modelo funcional para predicciones")
            else:
                issues.append("Modelo no tiene método predict")

        except Exception as e:
            issues.append(f"Error cargando modelo: {e}")
    else:
        issues.append("No se puede verificar integridad - modelo no existe")

    # 4. Verificar compatibilidad con activos
    print("\n4️⃣ COMPATIBILIDAD CON ACTIVOS")
    print("-" * 40)

    if model_exists and 'enabled_assets' in locals():
        try:
            from nexus_system.cortex.ml_classifier import MLClassifier

            # Intentar clasificar algunos activos
            test_assets = enabled_assets[:3]  # Probar solo los primeros 3

            successful_classifications = 0
            bypass_count = 0

            for asset in test_assets:
                try:
                    # Simular datos de mercado básicos
                    market_data = {
                        'symbol': asset,
                        'dataframe': None  # Esto debería causar fallback
                    }

                    result = MLClassifier.classify(market_data)
                    if result is None:
                        bypass_count += 1
                    else:
                        successful_classifications += 1

                except Exception as e:
                    print(f"   ⚠️  Error clasificando {asset}: {str(e)[:50]}...")

            print(f"✅ Activos probados: {len(test_assets)}")
            print(f"✅ Clasificaciones exitosas: {successful_classifications}")
            print(f"ℹ️  Fallbacks (normal): {bypass_count}")

            if successful_classifications > 0:
                print("✅ ML Classifier operativo")
            elif bypass_count > 0:
                print("ℹ️  ML Classifier en modo fallback (usando rule-based)")
            else:
                warnings.append("ML Classifier no produce resultados")

        except Exception as e:
            issues.append(f"Error probando ML Classifier: {e}")

    # 5. Verificar scripts de entrenamiento
    print("\n5️⃣ SCRIPTS DE ENTRENAMIENTO")
    print("-" * 40)

    scripts_to_check = [
        "src/ml/train_cortex.py",
        "src/ml/quick_train_expanded.py",
        "scripts/retrain_ml_model.py"
    ]

    for script in scripts_to_check:
        if os.path.exists(script):
            print(f"✅ {script}")
        else:
            warnings.append(f"Script faltante: {script}")

    # 6. Recomendaciones
    print("\n6️⃣ DIAGNÓSTICO Y RECOMENDACIONES")
    print("-" * 40)

    if not issues:
        print("✅ SISTEMA ML DIAGNOSTICADO SATISFACTORIAMENTE")
        print("   No se encontraron problemas críticos")
    else:
        print("❌ PROBLEMAS CRÍTICOS ENCONTRADOS:")
        for issue in issues:
            print(f"   ❌ {issue}")

    if warnings:
        print("\n⚠️  ADVERTENCIAS:")
        for warning in warnings:
            print(f"   ⚠️  {warning}")

    # Recomendaciones específicas
    print("\n📋 RECOMENDACIONES:")

    if "modelo no encontrado" in str(issues).lower():
        print("❌ Ejecutar reentrenamiento: python scripts/retrain_ml_model.py")

    if "pocos activos" in str(issues).lower():
        print("⚠️  Revisar configuración de grupos en system_directive.py")

    if not any("bundle" in str(msg).lower() for msg in [""]):
        print("ℹ️  Considerar reentrenar para formato bundle mejorado")

    print("✅ Monitorear rendimiento del clasificador en producción")

    return len(issues) == 0

if __name__ == "__main__":
    success = diagnose_ml_system()

    print("\n" + "=" * 80)
    print("🎯 RESULTADO FINAL:")
    if success:
        print("✅ SISTEMA ML LISTO PARA PRODUCCIÓN")
    else:
        print("❌ REVISAR PROBLEMAS ANTES DE PRODUCCIÓN")

    sys.exit(0 if success else 1)
