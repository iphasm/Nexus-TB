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
import argparse
from datetime import datetime

def retrain_ml_model(candles=5000, assets=None, features=None, symbols_limit=None):
    """Reentrena el modelo ML con activos y features seleccionados."""

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

    print("\n🔧 Parámetros de entrenamiento:")
    print(f"   Candles: {candles}")
    print(f"   Assets: {len(assets) if assets else 'Todos'} seleccionados")
    print(f"   Features: {len(features) if features else 'Todos'} activas")
    print(f"   Symbols: {'Todos habilitados' if symbols_limit is None else symbols_limit}")

    # Crear archivo de configuración temporal para features y assets
    config_file = None
    if features or assets:
        config_file = "temp_ml_config.json"
        config_data = {
            "enabled_features": features or [],
            "selected_assets": assets or []
        }
        import json
        with open(config_file, 'w') as f:
            json.dump(config_data, f)
        print(f"   Config: {config_file}")

    # Ejecutar entrenamiento
    print("\n🏃 Ejecutando entrenamiento...")
    print("=" * 60)

    # Configurar entorno para ejecución correcta
    env = os.environ.copy()
    current_dir = os.getcwd()
    env["PYTHONPATH"] = current_dir

    cmd = [
        sys.executable,
        train_script,
        "--candles", str(candles)
    ]

    if config_file:
        cmd.extend(["--config", config_file])

    if symbols_limit:
        cmd.extend(["--symbols", str(symbols_limit)])

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=1800,  # 30 min timeout
                              env=env, cwd=current_dir)

        print("STDOUT:")
        print(result.stdout)

        if result.stderr:
            print("STDERR:")
            print(result.stderr)

        if result.returncode == 0:
            print("\n✅ ENTRENAMIENTO COMPLETADO EXITOSAMENTE")
            print("🎯 Modelo reentrenado con activos actuales")

            # Verificar que los archivos se crearon
            model_path = os.path.join("nexus_system", "memory_archives", "ml_model.pkl")
            scaler_path = os.path.join("nexus_system", "memory_archives", "scaler.pkl")

            if os.path.exists(model_path):
                model_size = os.path.getsize(model_path) / 1024 / 1024  # MB
                print(f"   📊 Modelo creado: {model_size:.2f} MB")
            else:
                print("⚠️  Modelo no encontrado después del entrenamiento")

            if os.path.exists(scaler_path):
                scaler_size = os.path.getsize(scaler_path) / 1024 / 1024  # MB
                print(f"   📊 Scaler creado: {scaler_size:.2f} MB")
            else:
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

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Reentrenar modelo ML de Nexus')
    parser.add_argument('--candles', type=int, default=5000,
                       help='Número de velas para entrenamiento')
    parser.add_argument('--symbols', type=int, default=None,
                       help='Límite de símbolos para entrenar')
    parser.add_argument('--assets', nargs='*', default=None,
                       help='Lista específica de activos para entrenar')
    parser.add_argument('--rsi', action='store_true', default=True,
                       help='Incluir indicador RSI')
    parser.add_argument('--macd', action='store_true', default=True,
                       help='Incluir indicador MACD')
    parser.add_argument('--bbands', action='store_true', default=True,
                       help='Incluir Bollinger Bands')
    parser.add_argument('--stoch', action='store_true', default=True,
                       help='Incluir Stochastic Oscillator')
    parser.add_argument('--adx', action='store_true', default=True,
                       help='Incluir ADX')
    parser.add_argument('--mfi', action='store_true', default=True,
                       help='Incluir MFI')
    parser.add_argument('--cci', action='store_true', default=True,
                       help='Incluir CCI')
    parser.add_argument('--willr', action='store_true', default=True,
                       help='Incluir Williams %R')
    parser.add_argument('--obv', action='store_true', default=True,
                       help='Incluir OBV')
    parser.add_argument('--ema', action='store_true', default=True,
                       help='Incluir EMA')
    parser.add_argument('--sma', action='store_true', default=True,
                       help='Incluir SMA')

    return parser.parse_args()

if __name__ == "__main__":
    print("🤖 Nexus ML Model Retraining")
    print("=" * 80)

    # Parsear argumentos
    args = parse_arguments()

    # Recopilar features activas
    features = []
    if args.rsi: features.append('rsi')
    if args.macd: features.append('macd')
    if args.bbands: features.append('bbands')
    if args.stoch: features.append('stoch')
    if args.adx: features.append('adx')
    if args.mfi: features.append('mfi')
    if args.cci: features.append('cci')
    if args.willr: features.append('willr')
    if args.obv: features.append('obv')
    if args.ema: features.append('ema')
    if args.sma: features.append('sma')

    # Crear backup del modelo actual
    print("📦 Creando backup del modelo actual...")
    backup_existing_model()

    print()

    # Ejecutar reentrenamiento con parámetros
    success = retrain_ml_model(
        candles=args.candles,
        assets=args.assets,
        features=features,
        symbols_limit=args.symbols
    )

    # Limpiar archivo de configuración temporal
    if os.path.exists("temp_ml_config.json"):
        os.remove("temp_ml_config.json")

    # Resultado final
    print("\n" + "=" * 80)
    if success:
        print("🎉 REENTRENAMIENTO COMPLETADO - Modelo actualizado con configuración personalizada")
        print("\n📋 RECOMENDACIONES:")
        print("✅ Reinicia el bot para cargar el nuevo modelo")
        print("✅ Monitorea el rendimiento del clasificador ML")
        print("✅ Verifica que las predicciones sean consistentes")
        sys.exit(0)
    else:
        print("❌ REENTRENAMIENTO FALLÓ - Revisa los logs de error arriba")
        print("\n🔄 El modelo anterior permanece intacto")
        sys.exit(1)
