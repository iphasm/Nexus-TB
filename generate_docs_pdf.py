from fpdf import FPDF
import os

class PDF(FPDF):
    def header(self):
        # Logo placeholder (text only for now)
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, 'Antigravity Bot Documentation', 0, 1, 'C')
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, 'Page ' + str(self.page_no()) + '/{nb}', 0, 0, 'C')

    def chapter_title(self, num, label):
        self.set_font('Arial', 'B', 16)
        self.set_fill_color(200, 220, 255)
        self.cell(0, 6, f'{num} : {label}', 0, 1, 'L', 1)
        self.ln(4)

    def chapter_body(self, body):
        self.set_font('Arial', '', 12)
        self.multi_cell(0, 6, body.encode('latin-1', 'replace').decode('latin-1')) # basic encoding handling
        self.ln()

    def add_chapter(self, num, title, body):
        self.add_page()
        self.chapter_title(num, title)
        self.chapter_body(body)

def get_manual_usuario_text():
    return """
🚀 INICIO RÁPIDO

Para comenzar a operar con Antigravity Bot, sigue estos 3 pasos básicos:
1. Inicia el bot con /start
2. Configura tus llaves con /set_keys (o usa variables de entorno)
3. Selecciona un modo de operación (Default: Watcher)

🕹️ COMANDOS PRINCIPALES

/start - Inicia el bot y muestra el panel de control.
/status - Muestra estado actual, PnL y exposición.
/mode [PERFIL] - Cambia el modo (RONIN, GUARDIAN, QUANTUM).
/wallet - Muestra balance detallado.
/price [TICKER] - Consulta precio en tiempo real.
/sniper [TICKER] - Análisis técnico rápido.

🛡️ PERFILES ESTRATÉGICOS

[⚔️ RONIN]
Estilo: Agresivo / Scalping
- Apalancamiento: 20x
- Stop Loss: Ajustado (1.5 ATR)
- Filtro IA: Permisivo (-0.8)

[🌌 QUANTUM]
Estilo: Balanceado (Recomendado)
- Apalancamiento: 5x
- Stop Loss: Estándar (2.0 ATR)
- Filtro IA: Moderado (-0.6)

[🛡️ GUARDIAN]
Estilo: Conservador / Swing
- Apalancamiento: 3x
- Stop Loss: Amplio (3.0 ATR)
- Filtro IA: Estricto (-0.3)

MODOS DE OPERACIÓN

1. Watcher Mode: Vigilancia y alertas. No opera solo.
2. Copilot Mode: Propone operaciones, tú confirmas.
3. Pilot Mode: 100% Autónomo.
"""

def get_manual_tecnico_text():
    return """
🏗️ ARQUITECTURA DEL SISTEMA

Antigravity Bot utiliza una arquitectura asíncrona basada en eventos (QuantumBridge).

Flujo Simplificado:
[Market Data] -> [Strategy Engine] -> [Signal Generation] -> [Quantum Decision] -> [Execution]

Componentes Clave:
- main.py: Event Loop y Telegram Handlers.
- utils/trading_manager.py: Ejecución, risk management, sesiones.
- strategies/engine.py: Cálculo de indicadores y señales.
- utils/ai_analyst.py: Análisis de sentimiento con OpenAI.

⚙️ REQUISITOS

- Python 3.9+
- Binance API Key + Secret (Futures enabled)
- OpenAI API Key
- Telegram Bot Token

🔧 CONFIGURACIÓN AVANZADA (TradingSession)

- max_capital_pct: % máximo por trade (Default 10%)
- leverage: Apalancamiento base
- sentiment_threshold: Filtro de IA (-1 a 1)

🐛 SOLUCIÓN DE PROBLEMAS common

- Error "Binance API Exception": Verificar permisos de IP y Futuros.
- Bot no responde: Revisa si hay otra instancia corriendo.
"""

def get_pilot_logic_text():
    return """
DIAGRAMA LÓGICO: PILOT MODE

El modo Pilot sigue un estricto árbol de decisión:

1. ¿Hay Señal Técnica? (RSI, Bollinger, Momentum)
   - NO: Esperar.
   - SI: Pasar a paso 2.

2. ¿Sentimiento de Mercado favorable? (AI Analyst)
   - SI Score > Threshold: Continuar.
   - NO: Bloquear Trade (Filtro de Sentimiento).

3. ¿Capital Disponible?
   - SI: Calcular tamaño de posición (Kelly/Risk %).
   - NO: Rechazar señal.

4. Ejecución
   - Enviar orden a Binance/Alpaca.
   - Colocar OCO (Order Cancel Order) para TP/SL.

5. Monitorización
   - Trailing Stop activo.
   - Cierre por señal opuesta o TP/SL alcanzado.
"""

pdf = PDF()
pdf.alias_nb_pages()
pdf.set_title('Antigravity Bot Docs')

# Page 1: Intro
pdf.add_page()
pdf.set_font('Arial', 'B', 24)
pdf.cell(0, 40, 'Antigravity Bot', 0, 1, 'C')
pdf.set_font('Arial', '', 14)
pdf.cell(0, 10, 'Documentación Unificada v3.1', 0, 1, 'C')
pdf.ln(20)
pdf.set_font('Arial', '', 12)
pdf.multi_cell(0, 10, "Este documento contiene el Manual de Usuario, la Documentación Técnica y la Lógica del Modo Pilot unificadas.")

# Chapters
pdf.add_chapter(1, 'Manual de Usuario', get_manual_usuario_text())
pdf.add_chapter(2, 'Documentación Técnica', get_manual_tecnico_text())
pdf.add_chapter(3, 'Lógica Pilot Mode', get_pilot_logic_text())

# Output
output_path = os.path.join("DOCUMENTACIÓN", "Antigravity_Documentation.pdf")
pdf.output(output_path, 'F')
print(f"PDF Generated successfully at: {output_path}")
