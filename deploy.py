#!/usr/bin/env python3
"""
Nexus Trading Bot - Auto Deploy Script (Python)
Automatiza: git add, commit, push a GitHub
Railway detecta automáticamente el push y despliega
"""

import subprocess
import sys
import os
from datetime import datetime

# Colores ANSI
class Colors:
    CYAN = '\033[36m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    RED = '\033[31m'
    RESET = '\033[0m'

def print_color(color, message):
    """Print colored message"""
    print(f"{color}{message}{Colors.RESET}")

def run_command(cmd, check=True, capture_output=False):
    """Run shell command"""
    try:
        if capture_output:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=check)
            return result.stdout.strip()
        else:
            subprocess.run(cmd, shell=True, check=check)
            return None
    except subprocess.CalledProcessError as e:
        if check:
            print_color(Colors.RED, f"❌ Error ejecutando: {cmd}")
            print_color(Colors.RED, f"   {e.stderr if hasattr(e, 'stderr') else str(e)}")
            sys.exit(1)
        return None

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Auto Deploy Nexus Trading Bot to GitHub')
    parser.add_argument('-m', '--message', type=str, help='Mensaje de commit')
    parser.add_argument('-a', '--all', action='store_true', help='Agregar todos los cambios (incluyendo eliminados)')
    parser.add_argument('-s', '--status', action='store_true', help='Solo mostrar estado del repositorio')
    parser.add_argument('--no-push', action='store_true', help='No hacer push, solo commit local')
    parser.add_argument('--skip-tests', action='store_true', help='Omitir ejecución de tests')
    parser.add_argument('--skip-lint', action='store_true', help='Omitir verificación de linter')
    parser.add_argument('--notify', action='store_true', help='Enviar notificación a Telegram')
    
    args = parser.parse_args()
    
    print_color(Colors.CYAN, "🌌 NEXUS TRADING BOT - Auto Deploy")
    print_color(Colors.CYAN, "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    
    # Check if git is available
    try:
        git_version = run_command("git --version", capture_output=True)
        print_color(Colors.GREEN, f"✅ Git encontrado: {git_version}")
    except:
        print_color(Colors.RED, "❌ Git no está instalado o no está en PATH")
        sys.exit(1)
    
    # Check if we're in a git repository
    if not os.path.exists('.git'):
        print_color(Colors.RED, "❌ No estás en un repositorio Git")
        sys.exit(1)
    
    # Show status if requested
    if args.status:
        print_color(Colors.YELLOW, "\n📊 Estado del repositorio:")
        run_command("git status --short", check=False)
        return
    
    # Get current branch
    current_branch = run_command("git rev-parse --abbrev-ref HEAD", capture_output=True)
    print_color(Colors.CYAN, f"\n🌿 Rama actual: {current_branch}")
    
    # Check for changes
    changes = run_command("git status --porcelain", capture_output=True)
    if not changes:
        print_color(Colors.YELLOW, "⚠️ No hay cambios para commitear")
        return
    
    # Show changes
    print_color(Colors.YELLOW, "\n📝 Cambios detectados:")
    run_command("git status --short", check=False)
    
    # Pre-deploy validations
    print_color(Colors.CYAN, "\n🔍 Ejecutando validaciones pre-deploy...")
    
    # 0. Backup Critical Files
    print_color(Colors.YELLOW, "  0️⃣ Creando backup de archivos críticos...")
    backup_dir = "backups"
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = os.path.join(backup_dir, f"backup_{timestamp}")
    
    if not os.path.exists(backup_dir):
        os.makedirs(backup_path)
    
    # Files to backup
    critical_files = [
        "system_directive.py",
        "nexus_loader.py",
        ".env.example",
        "railway.json",
        "requirements.txt"
    ]
    
    # Directories to backup
    critical_dirs = [
        "nexus_system/core",
        "nexus_system/cortex",
        "servos"
    ]
    
    backed_up = 0
    import shutil
    
    for file in critical_files:
        if os.path.exists(file):
            dest = os.path.join(backup_path, file)
            dest_dir = os.path.dirname(dest)
            if not os.path.exists(dest_dir):
                os.makedirs(dest_dir)
            shutil.copy2(file, dest)
            backed_up += 1
    
    for dir_path in critical_dirs:
        if os.path.exists(dir_path):
            dest = os.path.join(backup_path, dir_path)
            shutil.copytree(dir_path, dest, dirs_exist_ok=True)
            backed_up += 1
    
    if backed_up > 0:
        print_color(Colors.GREEN, f"    ✅ Backup creado: {backup_path} ({backed_up} items)")
        # Keep only last 5 backups
        if os.path.exists(backup_dir):
            backups = sorted([d for d in os.listdir(backup_dir) if os.path.isdir(os.path.join(backup_dir, d))], 
                           key=lambda x: os.path.getmtime(os.path.join(backup_dir, x)), reverse=True)
            for old_backup in backups[5:]:
                shutil.rmtree(os.path.join(backup_dir, old_backup))
            print_color(Colors.YELLOW, "    🧹 Limpieza: Manteniendo últimos 5 backups")
    else:
        print_color(Colors.YELLOW, "    ⚠️ No se encontraron archivos para backup")
    
    # 1. Dependency Check
    print_color(Colors.YELLOW, "  1️⃣ Verificando dependencias...")
    if os.path.exists("requirements.txt"):
        missing_deps = []
        with open("requirements.txt", "r") as f:
            required_deps = [line.split(">=")[0].split("==")[0].strip().lower() 
                           for line in f if line.strip() and not line.strip().startswith("#")]
        
        for dep in required_deps:
            if dep:
                result = run_command(f"python -m pip show {dep}", check=False, capture_output=True)
                if result is None:  # Error occurred
                    missing_deps.append(dep)
        
        if missing_deps:
            print_color(Colors.RED, "    ❌ Dependencias faltantes:")
            for dep in missing_deps:
                print_color(Colors.RED, f"       - {dep}")
            print_color(Colors.YELLOW, "    💡 Ejecuta: pip install -r requirements.txt")
            response = input("¿Continuar de todas formas? (s/N): ").strip().lower()
            if response != 's':
                sys.exit(1)
        else:
            print_color(Colors.GREEN, "    ✅ Todas las dependencias instaladas")
    else:
        print_color(Colors.YELLOW, "    ⏭️ requirements.txt no encontrado")
    
    # 2. Python Syntax Check
    print_color(Colors.YELLOW, "  1️⃣ Verificando sintaxis Python...")
    python_files = run_command("git diff --cached --name-only --diff-filter=ACM", capture_output=True)
    python_files = [f for f in python_files.split('\n') if f and f.endswith('.py')] if python_files else []
    
    if python_files:
        syntax_errors = []
        for file in python_files:
            result = run_command(f"python -m py_compile {file}", check=False, capture_output=True)
            if result is None:  # Error occurred
                syntax_errors.append(file)
                print_color(Colors.RED, f"     ❌ Error de sintaxis en: {file}")
        
        if syntax_errors:
            print_color(Colors.RED, "\n❌ Errores de sintaxis detectados. Corrige antes de deployar.")
            sys.exit(1)
        print_color(Colors.GREEN, "    ✅ Sintaxis Python OK")
    else:
        print_color(Colors.YELLOW, "    ⏭️ No hay archivos Python modificados")
    
    # 3. Linter Check (optional)
    if not args.skip_lint:
        print_color(Colors.YELLOW, "  2️⃣ Verificando linter (opcional)...")
        has_linter = False
        try:
            run_command("pylint --version", capture_output=True, check=False)
            has_linter = True
            linter_cmd = "pylint"
        except:
            try:
                run_command("flake8 --version", capture_output=True, check=False)
                has_linter = True
                linter_cmd = "flake8"
            except:
                print_color(Colors.YELLOW, "    ⏭️ Linter no disponible (pylint/flake8)")
        
        if has_linter and python_files:
            lint_errors = 0
            for file in python_files:
                result = run_command(f"{linter_cmd} --errors-only {file}", check=False, capture_output=True)
                if result is None:
                    lint_errors += 1
            if lint_errors > 0:
                print_color(Colors.YELLOW, "    ⚠️ Advertencias de linter encontradas (continuando...)")
            else:
                print_color(Colors.GREEN, "    ✅ Linter OK")
    
    # 4. Run Tests (optional)
    if not args.skip_tests:
        print_color(Colors.YELLOW, "  3️⃣ Ejecutando tests...")
        if os.path.exists("tests"):
            try:
                result = run_command("pytest tests -v --tb=short", check=False, capture_output=True)
                if result is None:  # Tests failed
                    print_color(Colors.RED, "\n❌ Tests fallaron. Revisa los errores arriba.")
                    print_color(Colors.YELLOW, "💡 Usa --skip-tests para omitir tests")
                    response = input("¿Continuar de todas formas? (s/N): ").strip().lower()
                    if response != 's':
                        sys.exit(1)
                else:
                    print_color(Colors.GREEN, "    ✅ Tests pasaron")
            except:
                print_color(Colors.YELLOW, "    ⚠️ pytest no disponible o tests fallaron (continuando...)")
        else:
            print_color(Colors.YELLOW, "    ⏭️ Carpeta tests no encontrada")
    
    print_color(Colors.GREEN, "\n✅ Validaciones completadas")
    
    # Get commit message
    message = args.message
    if not message:
        print_color(Colors.CYAN, "\n💬 Ingresa el mensaje de commit (o presiona Enter para auto-generar):")
        message = input().strip()
    
    if not message:
        # Auto-generate message based on changes
        changed_files = run_command("git diff --name-only HEAD", capture_output=True)
        file_list = changed_files.split('\n') if changed_files else []
        file_count = len([f for f in file_list if f])
        
        message = f"🔧 Update: {file_count} archivo(s) modificado(s)"
        
        # Try to detect what was changed
        if any('nexus_bridge' in f or 'adapter' in f for f in file_list):
            message += " [Bridge/Adapters]"
        if any('trading_manager' in f for f in file_list):
            message += " [Trading]"
        if any('cortex' in f or 'strategy' in f for f in file_list):
            message += " [Strategies]"
        if any('handler' in f or 'command' in f for f in file_list):
            message += " [Handlers]"
        
        print_color(Colors.YELLOW, f"📝 Mensaje auto-generado: {message}")
    
    # Stage changes
    print_color(Colors.CYAN, "\n📦 Agregando cambios...")
    if args.all:
        run_command("git add -A")
        print_color(Colors.GREEN, "✅ Todos los cambios agregados (incluyendo eliminados)")
    else:
        run_command("git add .")
        print_color(Colors.GREEN, "✅ Cambios agregados")
    
    # Commit
    print_color(Colors.CYAN, "\n💾 Creando commit...")
    try:
        run_command(f'git commit -m "{message}"')
        print_color(Colors.GREEN, "✅ Commit creado exitosamente")
    except:
        print_color(Colors.RED, "❌ Error al crear commit")
        sys.exit(1)
    
    # Push
    if not args.no_push:
        print_color(Colors.CYAN, "\n🚀 Enviando a GitHub...")
        try:
            run_command(f"git push origin {current_branch}")
            print_color(Colors.GREEN, "\n✅ Push exitoso a GitHub!")
            print_color(Colors.CYAN, "🔄 Railway detectará el push y desplegará automáticamente")
            print_color(Colors.YELLOW, "\n💡 Monitorea el despliegue en: https://railway.app")
            
            # Send notification if requested
            if args.notify:
                print_color(Colors.CYAN, "\n📧 Enviando notificación...")
                try:
                    import requests
                    
                    telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
                    telegram_chat_id = os.getenv('TELEGRAM_ADMIN_ID')
                    
                    if telegram_token and telegram_chat_id:
                        notification_text = (
                            f"🚀 *Deploy Exitoso*\n\n"
                            f"📝 Commit: {message}\n"
                            f"🌿 Branch: {current_branch}\n"
                            f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                            f"🔄 Railway desplegando automáticamente..."
                        )
                        
                        url = f"https://api.telegram.org/bot{telegram_token}/sendMessage"
                        payload = {
                            'chat_id': telegram_chat_id,
                            'text': notification_text,
                            'parse_mode': 'Markdown'
                        }
                        
                        requests.post(url, json=payload, timeout=5)
                        print_color(Colors.GREEN, "✅ Notificación enviada a Telegram")
                    else:
                        print_color(Colors.YELLOW, "⚠️ Variables TELEGRAM_BOT_TOKEN o TELEGRAM_ADMIN_ID no configuradas")
                except Exception as e:
                    print_color(Colors.YELLOW, f"⚠️ Error enviando notificación: {e}")
        except:
            print_color(Colors.RED, "\n❌ Error al hacer push")
            print_color(Colors.YELLOW, f"💡 Intenta manualmente: git push origin {current_branch}")
            sys.exit(1)
    else:
        print_color(Colors.YELLOW, "\n⏭️ Push omitido (--no-push)")
    
    print_color(Colors.GREEN, "\n✨ Proceso completado exitosamente!")

if __name__ == "__main__":
    main()

