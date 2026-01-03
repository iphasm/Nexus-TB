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
import requests
from typing import List, Dict, Set

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
            "selected_assets": [],  # Lista de activos seleccionados
            "features": {
                "rsi": True,
                "macd": True,
                "bbands": True,
                "stoch": True,
                "adx": True,
                "mfi": True,
                "cci": True,
                "willr": True,
                "obv": True,
                "ema": True,
                "sma": True
            },
            "interactive": False,
            "verbose": True
        }

        # Variables para selección de activos
        self.all_futures_assets = []
        self.selected_assets = set()
        self.asset_checkboxes = {}

        # Variables para features
        self.feature_vars = {}

        self.setup_ui()
        self.load_futures_assets()
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

        # Selección de activos
        self.create_asset_selection_ui(main_frame)

        # Configuración de features
        self.create_features_selection_ui(main_frame)

        # Información del sistema
        info_frame = ttk.LabelFrame(main_frame, text="ℹ️ Información del Sistema", padding="10")
        info_frame.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))

        self.system_info_text = tk.Text(info_frame, height=4, wrap=tk.WORD, state=tk.DISABLED)
        self.system_info_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        info_frame.columnconfigure(0, weight=1)
        info_frame.rowconfigure(0, weight=1)

        self.update_system_info()

        # Área de logs
        logs_frame = ttk.LabelFrame(main_frame, text="📋 Logs de Entrenamiento", padding="10")
        logs_frame.grid(row=5, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        logs_frame.columnconfigure(0, weight=1)
        logs_frame.rowconfigure(0, weight=1)

        self.logs_text = scrolledtext.ScrolledText(logs_frame, wrap=tk.WORD, height=15)
        self.logs_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Frame de botones
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.grid(row=6, column=0, columnspan=3, pady=(10, 0))

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
        progress_frame = ttk.Frame(main_frame)
        progress_frame.grid(row=7, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))

        ttk.Label(progress_frame, text="📈 Progreso:").grid(row=0, column=0, sticky=tk.W)
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(10, 0))

        self.status_label = ttk.Label(progress_frame, text="⏳ Listo para entrenar")
        self.status_label.grid(row=0, column=2, sticky=tk.W, padx=(10, 0))
        progress_frame.columnconfigure(1, weight=1)

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

        # Recopilar configuración de activos y features
        selected_assets_list = list(self.selected_assets) if self.selected_assets else None
        selected_features = {k: v.get() for k, v in self.feature_vars.items()}

        # Confirmar inicio
        config_summary = f"""
📊 Velas: {candles}
🎯 Símbolos: {'Todos habilitados' if symbols_limit is None else symbols_limit}
🎯 Activos seleccionados: {len(selected_assets_list) if selected_assets_list else 'Todos'}
🧠 Features activas: {sum(selected_features.values())}
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

            # Agregar configuración de activos
            if selected_assets_list:
                cmd.extend(["--assets"] + selected_assets_list)

            # Agregar configuración de features
            for feature, enabled in selected_features.items():
                if enabled:
                    cmd.extend([f"--{feature}"])

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

    def get_binance_futures_assets(self) -> List[str]:
        """Obtiene lista de activos de futuros de Binance."""
        try:
            url = "https://fapi.binance.com/fapi/v1/exchangeInfo"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()

            assets = []
            for symbol_info in data.get('symbols', []):
                symbol = symbol_info.get('symbol', '')
                if symbol.endswith('USDT') and symbol_info.get('status') == 'TRADING':
                    assets.append(symbol)

            return sorted(assets)
        except Exception as e:
            self.log_message(f"⚠️ Error obteniendo activos Binance: {e}", "WARNING")
            return []

    def get_bybit_futures_assets(self) -> List[str]:
        """Obtiene lista de activos de futuros de Bybit."""
        try:
            url = "https://api.bybit.com/v5/market/instruments-info?category=linear"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()

            assets = []
            for symbol_info in data.get('result', {}).get('list', []):
                symbol = symbol_info.get('symbol', '')
                if symbol.endswith('USDT') and symbol_info.get('status') == 'Trading':
                    assets.append(symbol)

            return sorted(assets)
        except Exception as e:
            self.log_message(f"⚠️ Error obteniendo activos Bybit: {e}", "WARNING")
            return []

    def load_futures_assets(self):
        """Carga lista de activos de futuros de ambos exchanges."""
        try:
            self.log_message("🔄 Cargando lista de activos de futuros...", "INFO")

            binance_assets = self.get_binance_futures_assets()
            bybit_assets = self.get_bybit_futures_assets()

            # Combinar y eliminar duplicados
            all_assets = list(set(binance_assets + bybit_assets))
            self.all_futures_assets = sorted(all_assets)

            self.log_message(f"✅ Cargados {len(self.all_futures_assets)} activos de futuros", "SUCCESS")

        except Exception as e:
            self.log_message(f"❌ Error cargando activos: {e}", "ERROR")
            self.all_futures_assets = []

    def create_asset_selection_ui(self, parent_frame):
        """Crea la interfaz para selección de activos."""
        # Frame para selección de activos
        assets_frame = ttk.LabelFrame(parent_frame, text="🎯 Selección de Activos", padding="10")
        assets_frame.pack(fill=tk.X, pady=(0, 10))

        # Botones de control
        control_frame = ttk.Frame(assets_frame)
        control_frame.pack(fill=tk.X, pady=(0, 5))

        ttk.Button(control_frame, text="📋 Todos Binance",
                  command=self.select_binance_assets).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(control_frame, text="📋 Todos Bybit",
                  command=self.select_bybit_assets).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(control_frame, text="✅ Seleccionar Todos",
                  command=self.select_all_assets).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(control_frame, text="❌ Deseleccionar Todos",
                  command=self.deselect_all_assets).pack(side=tk.LEFT, padx=(0, 5))

        # Lista de activos con scroll
        list_frame = ttk.Frame(assets_frame)
        list_frame.pack(fill=tk.BOTH, expand=True)

        # Canvas y scrollbar para la lista
        canvas = tk.Canvas(list_frame, height=150)
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Crear checkboxes para cada activo
        self.asset_checkboxes = {}
        for i, asset in enumerate(self.all_futures_assets):
            var = tk.BooleanVar(value=False)
            cb = ttk.Checkbutton(scrollable_frame, text=asset, variable=var,
                               command=lambda a=asset, v=var: self.toggle_asset(a, v))
            cb.grid(row=i//4, column=i%4, sticky=tk.W, padx=5, pady=2)
            self.asset_checkboxes[asset] = var

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Contador de seleccionados
        self.asset_count_label = ttk.Label(assets_frame, text="Seleccionados: 0")
        self.asset_count_label.pack(anchor=tk.W)

    def create_features_selection_ui(self, parent_frame):
        """Crea la interfaz para selección de features."""
        features_frame = ttk.LabelFrame(parent_frame, text="🧠 Configuración de Features", padding="10")
        features_frame.pack(fill=tk.X, pady=(0, 10))

        # Features disponibles
        available_features = {
            "rsi": "RSI (Relative Strength Index)",
            "macd": "MACD (Moving Average Convergence Divergence)",
            "bbands": "Bollinger Bands",
            "stoch": "Stochastic Oscillator",
            "adx": "ADX (Average Directional Index)",
            "mfi": "MFI (Money Flow Index)",
            "cci": "CCI (Commodity Channel Index)",
            "willr": "Williams %R",
            "obv": "OBV (On Balance Volume)",
            "ema": "EMA (Exponential Moving Average)",
            "sma": "SMA (Simple Moving Average)"
        }

        self.feature_vars = {}
        for i, (key, description) in enumerate(available_features.items()):
            var = tk.BooleanVar(value=self.default_config["features"].get(key, True))
            cb = ttk.Checkbutton(features_frame, text=f"{description}",
                               variable=var)
            cb.grid(row=i//2, column=i%2, sticky=tk.W, padx=10, pady=2)
            self.feature_vars[key] = var

        # Botones de control para features
        control_frame = ttk.Frame(features_frame)
        control_frame.grid(row=len(available_features)//2 + 1, column=0, columnspan=2,
                          sticky=(tk.W, tk.E), pady=(10, 0))

        ttk.Button(control_frame, text="✅ Todos",
                  command=self.select_all_features).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(control_frame, text="❌ Ninguno",
                  command=self.deselect_all_features).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(control_frame, text="🔄 Restaurar",
                  command=self.reset_features).pack(side=tk.LEFT)

    def toggle_asset(self, asset: str, var: tk.BooleanVar):
        """Alterna selección de un activo."""
        if var.get():
            self.selected_assets.add(asset)
        else:
            self.selected_assets.discard(asset)
        self.update_asset_count()

    def select_binance_assets(self):
        """Selecciona todos los activos de Binance."""
        binance_assets = self.get_binance_futures_assets()
        for asset in binance_assets:
            if asset in self.asset_checkboxes:
                self.asset_checkboxes[asset].set(True)
                self.selected_assets.add(asset)
        self.update_asset_count()

    def select_bybit_assets(self):
        """Selecciona todos los activos de Bybit."""
        bybit_assets = self.get_bybit_futures_assets()
        for asset in bybit_assets:
            if asset in self.asset_checkboxes:
                self.asset_checkboxes[asset].set(True)
                self.selected_assets.add(asset)
        self.update_asset_count()

    def select_all_assets(self):
        """Selecciona todos los activos."""
        for asset, var in self.asset_checkboxes.items():
            var.set(True)
            self.selected_assets.add(asset)
        self.update_asset_count()

    def deselect_all_assets(self):
        """Deselecciona todos los activos."""
        for asset, var in self.asset_checkboxes.items():
            var.set(False)
            self.selected_assets.discard(asset)
        self.update_asset_count()

    def update_asset_count(self):
        """Actualiza contador de activos seleccionados."""
        if hasattr(self, 'asset_count_label'):
            self.asset_count_label.config(text=f"Seleccionados: {len(self.selected_assets)}")

    def select_all_features(self):
        """Selecciona todos los features."""
        for var in self.feature_vars.values():
            var.set(True)

    def deselect_all_features(self):
        """Deselecciona todos los features."""
        for var in self.feature_vars.values():
            var.set(False)

    def reset_features(self):
        """Restaura configuración por defecto de features."""
        for key, var in self.feature_vars.items():
            var.set(self.default_config["features"].get(key, True))

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
