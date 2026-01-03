#!/usr/bin/env python3
"""
NEXUS ML TRAINER GUI
====================

Interfaz gráfica simple para entrenar el modelo ML de Nexus.
Compatible con Windows, macOS y Linux.
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import subprocess
import threading
import os
import sys
import json
from datetime import datetime
import signal

class MLTrainerGUI:
    """Interfaz gráfica para el entrenador ML de Nexus."""

    def __init__(self, root):
        self.root = root
        self.root.title("🚀 Nexus ML Trainer v2.0")
        self.root.geometry("900x700")
        self.root.resizable(True, True)

        # Variables de control
        self.training_process = None
        self.training_thread = None
        self.is_training = False

        # Configuración por defecto
        self.default_config = {
            "candles": 5000,
            "symbols": None,  # None = todos los habilitados
            "interactive": False,
            "verbose": True
        }

        self.setup_ui()
        self.load_last_config()

    def setup_ui(self):
        """Configura la interfaz de usuario."""
        # Frame principal
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Configurar grid
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(4, weight=1)

        # Título
        title_label = ttk.Label(main_frame, text="🤖 Nexus ML Model Trainer",
                               font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))

        # Frame de configuración
        config_frame = ttk.LabelFrame(main_frame, text="⚙️ Configuración de Entrenamiento", padding="10")
        config_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        config_frame.columnconfigure(1, weight=1)

        # Parámetros de entrada
        ttk.Label(config_frame, text="📊 Velas de entrenamiento:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.candles_var = tk.StringVar(value=str(self.default_config["candles"]))
        candles_entry = ttk.Entry(config_frame, textvariable=self.candles_var, width=10)
        candles_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(10, 0), pady=2)

        ttk.Label(config_frame, text="🎯 Límite de símbolos (opcional):").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.symbols_var = tk.StringVar(value="")
        symbols_entry = ttk.Entry(config_frame, textvariable=self.symbols_var, width=10)
        symbols_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=(10, 0), pady=2)

        # Opciones
        options_frame = ttk.Frame(config_frame)
        options_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0))

        self.verbose_var = tk.BooleanVar(value=self.default_config["verbose"])
        ttk.Checkbutton(options_frame, text="📝 Verbose (logs detallados)",
                       variable=self.verbose_var).grid(row=0, column=0, sticky=tk.W, padx=(0, 20))

        self.backup_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_frame, text="💾 Backup automático del modelo anterior",
                       variable=self.backup_var).grid(row=0, column=1, sticky=tk.W)

        # Información del sistema
        info_frame = ttk.LabelFrame(main_frame, text="ℹ️ Información del Sistema", padding="10")
        info_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))

        self.system_info_text = tk.Text(info_frame, height=4, wrap=tk.WORD, state=tk.DISABLED)
        self.system_info_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        info_frame.columnconfigure(0, weight=1)
        info_frame.rowconfigure(0, weight=1)

        self.update_system_info()

        # Área de logs
        logs_frame = ttk.LabelFrame(main_frame, text="📋 Logs de Entrenamiento", padding="10")
        logs_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        logs_frame.columnconfigure(0, weight=1)
        logs_frame.rowconfigure(0, weight=1)

        self.logs_text = scrolledtext.ScrolledText(logs_frame, wrap=tk.WORD, height=15)
        self.logs_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Frame de botones
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.grid(row=4, column=0, columnspan=3, pady=(10, 0))

        self.start_button = ttk.Button(buttons_frame, text="🚀 Iniciar Entrenamiento",
                                     command=self.start_training, style="Accent.TButton")
        self.start_button.grid(row=0, column=0, padx=(0, 10))

        self.stop_button = ttk.Button(buttons_frame, text="⏹️ Detener", command=self.stop_training, state=tk.DISABLED)
        self.stop_button.grid(row=0, column=1, padx=(0, 10))

        self.clear_button = ttk.Button(buttons_frame, text="🧹 Limpiar Logs", command=self.clear_logs)
        self.clear_button.grid(row=0, column=2, padx=(0, 10))

        self.save_logs_button = ttk.Button(buttons_frame, text="💾 Guardar Logs", command=self.save_logs)
        self.save_logs_button.grid(row=0, column=3)

        # Barra de progreso
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(main_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.grid(row=5, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(10, 0))

        self.status_label = ttk.Label(main_frame, text="✅ Listo para entrenar")
        self.status_label.grid(row=6, column=0, columnspan=3, pady=(5, 0))

        # Configurar estilos
        style = ttk.Style()
        style.configure("Accent.TButton", font=("Arial", 10, "bold"))

        # Atajos de teclado
        self.root.bind('<Control-s>', lambda e: self.save_logs())
        self.root.bind('<Control-l>', lambda e: self.clear_logs())
        self.root.bind('<F5>', lambda e: self.start_training())
        self.root.bind('<Escape>', lambda e: self.stop_training())

    def update_system_info(self):
        """Actualiza la información del sistema."""
        try:
            from system_directive import ASSET_GROUPS, GROUP_CONFIG

            enabled_assets = []
            for group_name, assets in ASSET_GROUPS.items():
                if GROUP_CONFIG.get(group_name, True):
                    enabled_assets.extend(assets)
            enabled_assets = list(set(enabled_assets))

            info_text = f"""📊 Activos habilitados: {len(enabled_assets)}
🎯 Grupos activos: {sum(1 for g in GROUP_CONFIG.values() if g)}
💾 Modelo existente: {'Sí' if os.path.exists('nexus_system/memory_archives/ml_model.pkl') else 'No'}
⚙️ Python: {sys.version.split()[0]}"""

            self.system_info_text.config(state=tk.NORMAL)
            self.system_info_text.delete(1.0, tk.END)
            self.system_info_text.insert(tk.END, info_text)
            self.system_info_text.config(state=tk.DISABLED)

        except Exception as e:
            self.log_message(f"⚠️ Error cargando info del sistema: {e}", "WARNING")

    def load_last_config(self):
        """Carga la última configuración usada."""
        try:
            if os.path.exists("ml_trainer_config.json"):
                with open("ml_trainer_config.json", "r") as f:
                    config = json.load(f)
                    self.candles_var.set(str(config.get("candles", self.default_config["candles"])))
                    self.symbols_var.set(str(config.get("symbols", "")))
                    self.verbose_var.set(config.get("verbose", self.default_config["verbose"]))
                    self.backup_var.set(config.get("backup", True))
        except Exception:
            pass  # Usar valores por defecto

    def save_config(self):
        """Guarda la configuración actual."""
        try:
            config = {
                "candles": int(self.candles_var.get() or self.default_config["candles"]),
                "symbols": int(self.symbols_var.get()) if self.symbols_var.get() else None,
                "verbose": self.verbose_var.get(),
                "backup": self.backup_var.get()
            }

            with open("ml_trainer_config.json", "w") as f:
                json.dump(config, f, indent=2)

        except Exception as e:
            self.log_message(f"⚠️ Error guardando configuración: {e}", "WARNING")

    def log_message(self, message, level="INFO"):
        """Agrega un mensaje a los logs."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        level_emojis = {
            "INFO": "ℹ️",
            "SUCCESS": "✅",
            "WARNING": "⚠️",
            "ERROR": "❌",
            "CRITICAL": "🚨"
        }

        emoji = level_emojis.get(level, "📝")
        formatted_message = f"[{timestamp}] {emoji} {message}\n"

        self.logs_text.insert(tk.END, formatted_message)
        self.logs_text.see(tk.END)

        # Actualizar status
        if level == "ERROR":
            self.status_label.config(text=f"❌ Error: {message[:50]}...")
        elif level == "SUCCESS":
            self.status_label.config(text=f"✅ {message[:50]}...")
        elif "progreso" in message.lower() or "completado" in message.lower():
            self.status_label.config(text=f"📊 {message[:50]}...")

    def start_training(self):
        """Inicia el proceso de entrenamiento."""
        if self.is_training:
            messagebox.showwarning("Entrenamiento en curso", "Ya hay un entrenamiento ejecutándose.")
            return

        # Validar parámetros
        try:
            candles = int(self.candles_var.get())
            if candles < 1000:
                raise ValueError("Mínimo 1000 velas")
            if candles > 50000:
                raise ValueError("Máximo 50000 velas")
        except ValueError as e:
            messagebox.showerror("Parámetros inválidos", f"Velas: {e}")
            return

        symbols_limit = None
        if self.symbols_var.get():
            try:
                symbols_limit = int(self.symbols_var.get())
                if symbols_limit < 1:
                    raise ValueError("Mínimo 1 símbolo")
            except ValueError as e:
                messagebox.showerror("Parámetros inválidos", f"Símbolos: {e}")
                return

        # Confirmar inicio
        config_summary = f"""
📊 Velas: {candles}
🎯 Símbolos: {'Todos habilitados' if symbols_limit is None else symbols_limit}
📝 Verbose: {'Sí' if self.verbose_var.get() else 'No'}
💾 Backup: {'Sí' if self.backup_var.get() else 'No'}
        """.strip()

        if not messagebox.askyesno("Confirmar Entrenamiento",
                                  f"¿Iniciar entrenamiento?\n\n{config_summary}"):
            return

        # Guardar configuración
        self.save_config()

        # Iniciar entrenamiento
        self.is_training = True
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.progress_var.set(0)

        self.log_message("🚀 Iniciando entrenamiento ML...", "INFO")

        # Ejecutar en thread separado
        self.training_thread = threading.Thread(target=self.run_training,
                                              args=(candles, symbols_limit),
                                              daemon=True)
        self.training_thread.start()

    def run_training(self, candles, symbols_limit):
        """Ejecuta el entrenamiento en un thread separado."""
        try:
            # Preparar comando
            cmd = [sys.executable, "scripts/retrain_ml_model.py", "--candles", str(candles)]
            if symbols_limit:
                cmd.extend(["--symbols", str(symbols_limit)])

            env = os.environ.copy()
            current_dir = os.getcwd()
            script_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(script_dir)

            # Configurar PYTHONPATH para incluir el directorio del proyecto
            env["PYTHONPATH"] = project_root
            if current_dir != project_root:
                env["PYTHONPATH"] += os.pathsep + current_dir

            # Ejecutar proceso
            self.training_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True,
                env=env,
                cwd=project_root
            )

            # Leer output en tiempo real
            while True:
                output = self.training_process.stdout.readline()
                if output == '' and self.training_process.poll() is not None:
                    break
                if output:
                    self.root.after(0, lambda: self.log_message(output.strip()))

                    # Actualizar progreso basado en output
                    self.update_progress_from_output(output.strip())

            # Esperar finalización
            return_code = self.training_process.poll()

            if return_code == 0:
                self.root.after(0, lambda: self.log_message("✅ Entrenamiento completado exitosamente!", "SUCCESS"))
                self.root.after(0, lambda: self.progress_var.set(100))
            else:
                self.root.after(0, lambda: self.log_message(f"❌ Entrenamiento falló (código: {return_code})", "ERROR"))

        except Exception as e:
            self.root.after(0, lambda: self.log_message(f"❌ Error durante entrenamiento: {e}", "ERROR"))

        finally:
            # Limpiar estado
            self.training_process = None
            self.root.after(0, self.training_finished)

    def update_progress_from_output(self, output):
        """Actualiza la barra de progreso basado en el output."""
        output_lower = output.lower()

        # Estimar progreso basado en mensajes conocidos
        if "fase 1" in output_lower and "descarga" in output_lower:
            self.root.after(0, lambda: self.progress_var.set(10))
        elif "fase 1 completada" in output_lower:
            self.root.after(0, lambda: self.progress_var.set(30))
        elif "fase 2" in output_lower and "preparación" in output_lower:
            self.root.after(0, lambda: self.progress_var.set(40))
        elif "fase 3" in output_lower and "entrenamiento" in output_lower:
            self.root.after(0, lambda: self.progress_var.set(60))
        elif "fase 6" in output_lower and "guardando" in output_lower:
            self.root.after(0, lambda: self.progress_var.set(90))

    def stop_training(self):
        """Detiene el entrenamiento en curso."""
        if not self.is_training:
            return

        if messagebox.askyesno("Confirmar", "¿Detener el entrenamiento en curso?"):
            self.log_message("⏹️ Deteniendo entrenamiento...", "WARNING")

            if self.training_process:
                try:
                    # Enviar señal de terminación
                    if os.name == 'nt':  # Windows
                        self.training_process.terminate()
                    else:  # Unix/Linux
                        os.kill(self.training_process.pid, signal.SIGTERM)

                    # Esperar un poco
                    self.training_process.wait(timeout=5)

                except subprocess.TimeoutExpired:
                    # Forzar terminación si no responde
                    self.training_process.kill()
                    self.log_message("💀 Proceso forzosamente terminado", "WARNING")
                except Exception as e:
                    self.log_message(f"⚠️ Error deteniendo proceso: {e}", "WARNING")

            self.training_finished()

    def training_finished(self):
        """Llamado cuando el entrenamiento termina."""
        self.is_training = False
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.status_label.config(text="✅ Entrenamiento completado")

    def clear_logs(self):
        """Limpia el área de logs."""
        self.logs_text.delete(1.0, tk.END)
        self.log_message("🧹 Logs limpiados", "INFO")

    def save_logs(self):
        """Guarda los logs en un archivo."""
        try:
            filename = f"ml_training_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            file_path = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("Archivos de texto", "*.txt"), ("Todos los archivos", "*.*")],
                initialfile=filename
            )

            if file_path:
                with open(file_path, 'w', encoding='utf-8') as f:
                    logs_content = self.logs_text.get(1.0, tk.END)
                    f.write(f"Nexus ML Training Logs - {datetime.now()}\n")
                    f.write("=" * 50 + "\n\n")
                    f.write(logs_content)

                self.log_message(f"💾 Logs guardados en: {file_path}", "SUCCESS")

        except Exception as e:
            messagebox.showerror("Error", f"Error guardando logs: {e}")

def main():
    """Función principal."""
    try:
        root = tk.Tk()
        app = MLTrainerGUI(root)

        # Configurar icono si existe
        try:
            # Intentar cargar icono (opcional)
            icon_path = "assets/nexus_icon.ico"
            if os.path.exists(icon_path):
                root.iconbitmap(icon_path)
        except:
            pass  # Ignorar si no hay icono

        root.mainloop()

    except Exception as e:
        # Fallback a CLI si GUI falla
        print(f"❌ Error iniciando GUI: {e}")
        print("💡 Ejecutar: python scripts/retrain_ml_model.py")
        sys.exit(1)

if __name__ == "__main__":
    main()
