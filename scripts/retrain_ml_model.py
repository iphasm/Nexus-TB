#!/usr/bin/env python3
"""
REENTRENAMIENTO COMPLETO: ML Model con Activos Actuales
=======================================================

Reentrena el modelo ML con todos los activos habilitados actualmente.
Usa la configuración actual de system_directive.py para determinar qué activos incluir.
"""

import os
import sys
import subprocess
from datetime import datetime

def retrain_ml_model():
    """Reentrena el modelo ML con activos actuales."""

    print("🚀 REENTRENAMIENTO ML MODEL")
    print("=" * 60)
    print(f"🕒 Inicio: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Verificar que estamos en el directorio correcto
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)

    os.chdir(project_root)

    # Verificar archivos necesarios
    train_script = "src/ml/train_cortex.py"
    if not os.path.exists(train_script):
        print(f"❌ Script de entrenamiento no encontrado: {train_script}")
        return False

    print("✅ Archivos verificados")
    print(f"   Script: {train_script}")

    # Configurar parámetros de entrenamiento
    # Usar menos datos para entrenamiento más rápido pero representativo
    candles = 5000  # Reducido para entrenamiento más rápido
    symbols_limit = None  # Usar todos los habilitados

    print("\n🔧 Parámetros de entrenamiento:")    print(f"   Candles: {candles}")
    print(f"   Symbols: {'Todos habilitados' if symbols_limit is None else symbols_limit}")

    # Ejecutar entrenamiento
    print("\n🏃 Ejecutando entrenamiento...")    print("=" * 60)

    cmd = [
        sys.executable,
        train_script,
        "--candles", str(candles)
    ]

    if symbols_limit:
        cmd.extend(["--symbols", str(symbols_limit)])

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=1800)  # 30 min timeout

        print("STDOUT:")
        print(result.stdout)

        if result.stderr:
            print("STDERR:")
            print(result.stderr)

        if result.returncode == 0:
            print("\n✅ ENTRENAMIENTO COMPLETADO EXITOSAMENTE")            print("🎯 Modelo reentrenado con activos actuales")

            # Verificar que los archivos se crearon
            model_path = os.path.join("nexus_system", "memory_archives", "ml_model.pkl")
            scaler_path = os.path.join("nexus_system", "memory_archives", "scaler.pkl")

            if os.path.exists(model_path):
                model_size = os.path.getsize(model_path) / 1024 / 1024  # MB
                print(f"   📊 Modelo creado: {model_size:.2f} MB")            else:
                print("⚠️  Modelo no encontrado después del entrenamiento")

            if os.path.exists(scaler_path):
                scaler_size = os.path.getsize(scaler_path) / 1024 / 1024  # MB
                print(f"   📊 Scaler creado: {scaler_size:.2f} MB")            else:
                print("⚠️  Scaler no encontrado después del entrenamiento")

            return True
        else:
            print(f"\n❌ ENTRENAMIENTO FALLÓ (Código: {result.returncode})")
            return False

    except subprocess.TimeoutExpired:
        print("\n❌ ENTRENAMIENTO CANCELADO - Timeout (30 minutos)")
        return False
    except Exception as e:
        print(f"\n❌ ERROR ejecutando entrenamiento: {e}")
        return False

def backup_existing_model():
    """Crea backup del modelo existente antes de reentrenar."""

    import shutil
    from datetime import datetime

    model_path = os.path.join("nexus_system", "memory_archives", "ml_model.pkl")
    scaler_path = os.path.join("nexus_system", "memory_archives", "scaler.pkl")

    if os.path.exists(model_path):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = os.path.join("nexus_system", "memory_archives")
        backup_model = os.path.join(backup_dir, f"ml_model_backup_{timestamp}.pkl")
        shutil.copy2(model_path, backup_model)
        print(f"📦 Backup modelo: {backup_model}")

    if os.path.exists(scaler_path):
        backup_scaler = os.path.join(backup_dir, f"scaler_backup_{timestamp}.pkl")
        shutil.copy2(scaler_path, backup_scaler)
        print(f"📦 Backup scaler: {backup_scaler}")

if __name__ == "__main__":
    print("🤖 Nexus ML Model Retraining")
    print("=" * 80)

    # Crear backup del modelo actual
    print("📦 Creando backup del modelo actual...")
    backup_existing_model()

    print()

    # Ejecutar reentrenamiento
    success = retrain_ml_model()

    # Resultado final
    print("\n" + "=" * 80)
    if success:
        print("🎉 REENTRENAMIENTO COMPLETADO - Modelo actualizado con activos actuales")
        print("\n📋 RECOMENDACIONES:")
        print("✅ Reinicia el bot para cargar el nuevo modelo")
        print("✅ Monitorea el rendimiento del clasificador ML")
        print("✅ Verifica que las predicciones sean consistentes")
        sys.exit(0)
    else:
        print("❌ REENTRENAMIENTO FALLÓ - Revisa los logs de error arriba")
        print("\n🔄 El modelo anterior permanece intacto")
        sys.exit(1)
