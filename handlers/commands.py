"""
Antigravity Bot - Command Handlers
Basic commands: /start, /help, /status, /wallet, /price, /pnl
"""

from aiogram import Router, F
from aiogram.filters import Command, CommandStart
from aiogram.types import Message
import os
import requests

router = Router(name="commands")

# --- ASSET CONFIGURATION (Imported from main config) ---
ASSET_GROUPS = {
    'CRYPTO': [
        'BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'SOLUSDT', 'ADAUSDT', 'XRPUSDT', 
        'AVAXUSDT', 'LTCUSDT', 'DOTUSDT', 'MATICUSDT', 'LINKUSDT', 
        'NEARUSDT', 'ATOMUSDT', 'ICPUSDT', 'BCHUSDT',
        'WIFUSDT', '1000PEPEUSDT', 'DOGEUSDT', 'SHIBUSDT', 'SUIUSDT', 
        'RENDERUSDT', 'FETUSDT', 'INJUSDT', 'FTMUSDT', 'SEIUSDT',
        'BONKUSDT', 'FLOKIUSDT', 'TRBUSDT', 'ZECUSDT', 'EOSUSDT',
        'UNIUSDT', 'AAVEUSDT', 'XLMUSDT', 'CRVUSDT'
    ],
    'STOCKS': ['TSLA', 'NVDA', 'MSFT', 'AAPL', 'AMD'],
    'COMMODITY': ['GLD', 'USO', 'SLV', 'CPER', 'UNG']
}

GROUP_CONFIG = {
    'CRYPTO': True,
    'STOCKS': True,
    'COMMODITY': True
}

TICKER_MAP = {
    'BTCUSDT': 'Bitcoin', 'ETHUSDT': 'Ethereum', 'SOLUSDT': 'Solana',
    'BNBUSDT': 'Binance Coin', 'XRPUSDT': 'Ripple', 'ADAUSDT': 'Cardano',
    'TSLA': 'Tesla', 'NVDA': 'NVIDIA', 'MSFT': 'Microsoft',
    'GLD': 'ORO', 'USO': 'PETROLEO', 'SLV': 'PLATA'
}


async def get_fear_and_greed_index() -> str:
    """Fetch Fear and Greed Index from alternative.me (async-safe via requests)"""
    try:
        url = "https://api.alternative.me/fng/"
        resp = requests.get(url, timeout=5)
        data = resp.json()
        if 'data' in data and len(data['data']) > 0:
            item = data['data'][0]
            val = int(item['value'])
            classification = item['value_classification']
            
            icon = "😐"
            if val >= 75: icon = "🤑"
            elif val >= 55: icon = "😏"
            elif val <= 25: icon = "😱"
            elif val <= 45: icon = "😨"
            
            return f"{icon} *{classification}* ({val}/100)"
    except Exception as e:
        print(f"F&G Error: {e}")
    
    return "N/A"


@router.message(CommandStart())
async def cmd_start(message: Message):
    """Professional welcome message with loading effect"""
    # Send initial loading message
    loading = await message.answer("⏳ *Iniciando Antigravity...*", parse_mode="Markdown")
    
    # Build welcome message
    welcome = (
        "🚀 *ANTIGRAVITY BOT*\n"
        "━━━━━━━━━━━━━━━━━━━\n\n"
        "Sistema de trading algorítmico profesional.\n\n"
        
        "📡 *Escáneres Activos:*\n"
        "• Criptomonedas (Binance Futures)\n"
        "• Acciones (Alpaca)\n"
        "• Materias Primas (ETFs)\n\n"
        
        "🎮 *Modos de Operación:*\n"
        "• `WATCHER` - Solo alertas\n"
        "• `COPILOT` - Propuestas con confirmación\n"
        "• `PILOT` - Trading automático\n\n"
        
        "💡 Usa /help para ver comandos disponibles."
    )
    
    await loading.edit_text(welcome, parse_mode="Markdown")


@router.message(Command("help"))
async def cmd_help(message: Message):
    """Command reference"""
    help_text = (
        "📚 *COMANDOS DISPONIBLES*\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        
        "*📊 Información*\n"
        "`/status` - Estado del sistema\n"
        "`/price` - Radar de mercado\n"
        "`/wallet` - Balance de cartera\n"
        "`/pnl` - Historial de PnL\n\n"
        
        "*🎮 Control*\n"
        "`/watcher` - Modo observador\n"
        "`/copilot` - Modo asistido\n"
        "`/pilot` - Modo automático\n\n"
        
        "*💹 Trading Manual*\n"
        "`/long <SYMBOL>` - Abrir Long\n"
        "`/short <SYMBOL>` - Abrir Short\n"
        "`/close <SYMBOL>` - Cerrar posición\n"
        "`/closeall` - Cerrar todo\n\n"
        
        "*⚙️ Configuración*\n"
        "`/config` - Panel de control\n"
        "`/set_keys` - Configurar API\n"
        "`/strategies` - Toggle estrategias\n"
    )
    
    await message.answer(help_text, parse_mode="Markdown")


@router.message(Command("status"))
async def cmd_status(message: Message, **kwargs):
    """System status with clean glass design"""
    # Get session from middleware/context
    session_manager = kwargs.get('session_manager')
    session = None
    
    if session_manager:
        session = session_manager.get_session(str(message.chat.id))
    
    mode = "WATCHER"
    has_keys = False
    
    if session:
        mode = session.config.get('mode', 'WATCHER')
        has_keys = bool(session.client)
    
    # Fear & Greed
    fg_text = await get_fear_and_greed_index()
    
    # Mode display
    mode_map = {
        'WATCHER': 'WATCHER (Observador)',
        'COPILOT': 'COPILOT (Asistido)',
        'PILOT': 'PILOT (Automático)'
    }
    mode_display = mode_map.get(mode, mode)
    
    # Build asset list
    active_radars = ""
    for group, enabled in GROUP_CONFIG.items():
        icon = "🟢" if enabled else "⚪"
        name_map = {
            'CRYPTO': 'Criptomonedas',
            'STOCKS': 'Acciones',
            'COMMODITY': 'Materias Primas'
        }
        name = name_map.get(group, group)
        count = len(ASSET_GROUPS.get(group, [])) if enabled else 0
        count_str = f"({count})" if enabled else ""
        active_radars += f"{icon} {name} {count_str}\n"
    
    status = (
        "🤖 *Estado de Antigravity*\n\n"
        
        "*Modo de Operación*\n"
        f"🕹️ `{mode_display}`\n\n"
        
        "*Entorno de Mercado*\n"
        f"🌡️ Sentimiento: {fg_text}\n"
        f"💻 Conexión: *{'Estable' if has_keys else 'Desconectado'}*\n\n"
        
        "*Escáneres Activos*\n"
        f"{active_radars}\n"
        "_Sistema ejecutándose correctamente._"
    )
    
    await message.answer(status, parse_mode="Markdown")


@router.message(Command("watcher"))
async def cmd_watcher(message: Message, **kwargs):
    """Switch to Watcher mode"""
    session_manager = kwargs.get('session_manager')
    if not session_manager:
        await message.answer("⚠️ Error interno: SessionManager no disponible.")
        return
        
    session = session_manager.get_session(str(message.chat.id))
    if not session:
        await message.answer("⚠️ No tienes sesión activa. Usa /set\\_keys primero.")
        return
    
    session.set_mode('WATCHER')
    await session_manager.save_sessions()
    
    await message.answer(
        "👁️ *Modo WATCHER Activado*\n\n"
        "Solo recibirás alertas de señales.\n"
        "No se ejecutarán operaciones automáticas.",
        parse_mode="Markdown"
    )


@router.message(Command("copilot"))
async def cmd_copilot(message: Message, **kwargs):
    """Switch to Copilot mode"""
    session_manager = kwargs.get('session_manager')
    if not session_manager:
        await message.answer("⚠️ Error interno.")
        return
        
    session = session_manager.get_session(str(message.chat.id))
    if not session:
        await message.answer("⚠️ No tienes sesión activa. Usa /set\\_keys primero.")
        return
    
    session.set_mode('COPILOT')
    await session_manager.save_sessions()
    
    await message.answer(
        "🤝 *Modo COPILOT Activado*\n\n"
        "Recibirás propuestas de trading con botones.\n"
        "Tú decides si ejecutar o rechazar cada operación.",
        parse_mode="Markdown"
    )


@router.message(Command("pilot"))
async def cmd_pilot(message: Message, **kwargs):
    """Switch to Pilot mode"""
    session_manager = kwargs.get('session_manager')
    if not session_manager:
        await message.answer("⚠️ Error interno.")
        return
        
    session = session_manager.get_session(str(message.chat.id))
    if not session:
        await message.answer("⚠️ No tienes sesión activa. Usa /set\\_keys primero.")
        return
    
    session.set_mode('PILOT')
    await session_manager.save_sessions()
    
    await message.answer(
        "🚀 *Modo PILOT Activado*\n\n"
        "El bot ejecutará operaciones automáticamente.\n"
        "⚠️ _Asegúrate de tener configurado tu riesgo correctamente._",
        parse_mode="Markdown"
    )
