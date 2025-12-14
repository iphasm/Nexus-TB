"""
Antigravity Bot - Command Handlers
Basic commands: /start, /help, /status, /wallet, /price, /pnl
EXACT REPLICA of main.py interface
"""

import asyncio
from aiogram import Router, F
from aiogram.filters import Command, CommandStart
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
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


def get_fear_and_greed_index() -> str:
    """Fetch Fear and Greed Index from alternative.me"""
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
async def cmd_start(message: Message, **kwargs):
    """Bienvenida Profesional con Efecto de Carga - EXACT REPLICA"""
    # 1. Mensaje de carga inicial
    msg_load = await message.answer("🔄 _Despertando funciones cognitivas..._", parse_mode="Markdown")
    
    # Simular micro-check
    await asyncio.sleep(0.5)
    
    # 2. Verificar estado
    bot = message.bot
    me = await bot.get_me()
    status_icon = "🟢" if me else "🔴"
    status_text = "SISTEMA ONLINE" if me else "ERROR DE CONEXIÓN"
    
    chat_id = str(message.chat.id)
    session_manager = kwargs.get('session_manager')
    session = session_manager.get_session(chat_id) if session_manager else None
    
    # 3. Datos de Sesión
    mode = "WATCHER"
    auth = "🔒 Sin Credenciales"
    
    if session:
        cfg = session.get_configuration()
        mode = cfg.get('mode', 'WATCHER')
        
        # Build Auth String
        auth_list = []
        if session.client:
            auth_list.append("Binance")
        if session.alpaca_client:
            auth_list.append("🦙 Alpaca")
            
        if auth_list:
            auth = "🔑 " + " + ".join(auth_list)
    
    # Get Personality
    p_key = session.config.get('personality', 'NEXUS') if session else 'NEXUS'

    # 4. Mensaje Final (Styled like original)
    welcome = (
        f"{status_icon} *{status_text}*\n\n"
        "🤖 *ANTIGRAVITY BOT v3.5 (Async)*\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        f"🎮 Modo: `{mode}`\n"
        f"{auth}\n\n"
        "_Usa los botones o escribe /help_"
    )
    
    # Interactive Menu (Buttons) - EXACT REPLICA
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        # Row 1: Status | Wallet
        [
            InlineKeyboardButton(text="📊 Estado", callback_data="CMD|status"),
            InlineKeyboardButton(text="💰 Cartera", callback_data="CMD|wallet")
        ],
        # Row 2: Watcher | Copilot
        [
            InlineKeyboardButton(text="🔎 Watcher", callback_data="CMD|watcher"),
            InlineKeyboardButton(text="🦾 Copilot", callback_data="CMD|copilot")
        ],
        # Row 3: Pilot (Big)
        [
            InlineKeyboardButton(text="🤖 Pilot Mode", callback_data="CMD|pilot")
        ],
        # Row 4: AI Commands
        [
            InlineKeyboardButton(text="📰 News", callback_data="CMD|news"),
            InlineKeyboardButton(text="🧠 Sentiment", callback_data="CMD|sentiment"),
            InlineKeyboardButton(text="🎯 Sniper", callback_data="CMD|sniper")
        ],
        # Row 5: Presets
        [
            InlineKeyboardButton(text="⚔️ Ronin", callback_data="CMD|mode_RONIN"),
            InlineKeyboardButton(text="🛡️ Guardian", callback_data="CMD|mode_GUARDIAN"),
            InlineKeyboardButton(text="🌌 Quantum", callback_data="CMD|mode_QUANTUM")
        ],
        # Row 6: Config / Personality / Help
        [
            InlineKeyboardButton(text="🧠 Persona", callback_data="CMD|personality"),
            InlineKeyboardButton(text="⚙️ Config", callback_data="CMD|config"),
            InlineKeyboardButton(text="❓ Ayuda", callback_data="CMD|help")
        ]
    ])
    
    await msg_load.edit_text(welcome, parse_mode="Markdown", reply_markup=keyboard)


@router.message(Command("help"))
async def cmd_help(message: Message):
    """Command reference - EXACT REPLICA"""
    help_text = (
        "🤖 *ANTIGRAVITY BOT v3.5*\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        
        "📊 *INFO & MERCADO*\n"
        "• /start - Menú principal\n"
        "• /price - Precios y señales\n"
        "• /status - Estado del sistema\n"
        "• /wallet - Ver cartera\n"
        "• /analyze `<SYM>` - Análisis IA\n\n"
        
        "💹 *TRADING MANUAL*\n"
        "• /long `<SYM>` - Abrir LONG\n"
        "• /short `<SYM>` - Abrir SHORT\n"
        "• /buy `<SYM>` - Compra SPOT\n"
        "• /sell `<SYM>` - Cerrar/Flip\n"
        "• /close `<SYM>` - Cerrar posición\n"
        "• /closeall - Cerrar TODO\n\n"
        
        "🎮 *MODOS OPERATIVOS*\n"
        "• /pilot - Automático\n"
        "• /copilot - Asistido\n"
        "• /watcher - Solo alertas\n"
        "• /mode `<PRESET>` - Ronin/Guardian/Quantum\n\n"
        
        "⚙️ *CONFIGURACIÓN*\n"
        "• /config - Panel de ajustes\n"
        "• /strategies - Motores activos\n"
        "• /set\\_leverage - Apalancamiento\n"
        "• /set\\_margin - Margen máximo\n"
        "• /set\\_keys - API Keys Binance\n"
        "• /set\\_alpaca - API Keys Alpaca\n"
        "• /delete\\_keys - Borrar sesión\n"
        "• /togglegroup - Filtrar grupos\n"
        "• /assets - Config activos\n"
        "• /personality - Cambiar voz\n\n"
        
        "🧠 *AI & SENTIMIENTO*\n"
        "• /news - Boletín IA\n"
        "• /sentiment - Radar global\n"
        "• /sniper - Oportunidades\n"
        "• /fomc - Análisis FED\n\n"
        
        "🛡️ *SEGURIDAD*\n"
        "• /risk - Gestión de riesgo\n"
        "• /resetpilot - Reset breaker\n"
        "• /debug - Diagnóstico\n\n"
        
        "📖 *DOCS*\n"
        "• /about - Sobre el bot\n"
        "• /strategy - Lógica de trading"
    )
    
    try:
        await message.answer(help_text, parse_mode="Markdown")
    except:
        # Fallback sin markdown
        await message.answer(help_text.replace('*', '').replace('`', '').replace('\\_', '_'))


@router.message(Command("status"))
async def cmd_status(message: Message, **kwargs):
    """Muestra estado del sistema (Diseño: Clean Glass) - EXACT REPLICA"""
    session_manager = kwargs.get('session_manager')
    session = None
    
    if session_manager:
        session = session_manager.get_session(str(message.chat.id))
    
    mode = "WATCHER"
    has_keys = False
    
    if session:
        cfg = session.get_configuration()
        mode = cfg.get('mode', 'WATCHER')
        has_keys = cfg.get('has_keys', False)
    
    # Fear & Greed
    fg_text = get_fear_and_greed_index()
    
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
        "🤖 **Estado de Antigravity**\n\n"
        
        "**Modo de Operación**\n"
        f"🕹️ `{mode_display}`\n\n"
        
        "**Entorno de Mercado**\n"
        f"🌡️ Sentimiento: {fg_text}\n"
        f"💻 Conexión: **{'Estable' if has_keys else 'Desconectado'}**\n\n"
        
        "**Escáneres Activos**\n"
        f"{active_radars}\n"
        "_Sistema ejecutándose correctamente._"
    )
    
    await message.answer(status, parse_mode="Markdown")


@router.message(Command("wallet"))
async def cmd_wallet(message: Message, **kwargs):
    """Muestra detalles completos de la cartera - EXACT REPLICA"""
    session_manager = kwargs.get('session_manager')
    if not session_manager:
        await message.answer("⚠️ Error interno.")
        return
    
    session = session_manager.get_session(str(message.chat.id))
    if not session:
        await message.answer("⚠️ Sin sesión activa. Usa /set\\_keys.")
        return
    
    loading = await message.answer("⏳ Consultando Blockchain y Binance...")
    
    try:
        details = await session.get_wallet_details()
        if not details or 'error' in details:
            await loading.edit_text(f"❌ Error: {details.get('error', 'Unknown')}")
            return
        
        # Unpack
        spot_bal = details.get('spot_usdt', 0.0)
        earn_bal = details.get('earn_usdt', 0.0)
        spot_total = spot_bal + earn_bal
        
        fut_bal = details.get('futures_balance', 0.0)
        fut_pnl = details.get('futures_pnl', 0.0)
        fut_total = details.get('total', fut_bal)
        alpaca_native = details.get('alpaca_equity', 0.0)
        
        net_worth = spot_total + fut_total + alpaca_native
        
        pnl_icon = "🟢" if fut_pnl >= 0 else "🔴"
        
        msg = (
            "💼 *CARTERA ANTIGRAVITY*\n"
            "〰️〰️〰️〰️〰️〰️\n"
            f"🏦 *SPOT (USDT):* `${spot_bal:,.2f}`\n"
            f"🐷 *EARN (Ahorros):* `${earn_bal:,.2f}`\n"
            "〰️〰️〰️〰️〰️〰️\n"
            f"🚀 *FUTUROS Balance:* `${fut_bal:,.2f}`\n"
            f"📊 *FUTUROS PnL:* {pnl_icon} `${fut_pnl:,.2f}`\n"
            f"💰 *FUTUROS Total:* `${fut_total:,.2f}`\n"
            "〰️〰️〰️〰️〰️〰️\n"
            f"🦙 *ALPACA (Stocks):* `${alpaca_native:,.2f}`\n"
            "〰️〰️〰️〰️〰️〰️\n"
            f"🏆 *NET WORTH TOTAL:* `${net_worth:,.2f}`"
        )
        
        await loading.edit_text(msg, parse_mode="Markdown")
        
    except Exception as e:
        await loading.edit_text(f"❌ Error: {e}")


@router.message(Command("watcher"))
async def cmd_watcher(message: Message, **kwargs):
    """Switch to Watcher mode"""
    session_manager = kwargs.get('session_manager')
    if not session_manager:
        await message.answer("⚠️ Error interno.")
        return
        
    session = session_manager.get_session(str(message.chat.id))
    if not session:
        await message.answer("⚠️ Sin sesión activa. Usa /set\\_keys primero.")
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
        await message.answer("⚠️ Sin sesión activa. Usa /set\\_keys primero.")
        return
    
    session.set_mode('COPILOT')
    await session_manager.save_sessions()
    
    await message.answer(
        "🦾 *Modo COPILOT Activado*\n\n"
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
        await message.answer("⚠️ Sin sesión activa. Usa /set\\_keys primero.")
        return
    
    session.set_mode('PILOT')
    await session_manager.save_sessions()
    
    await message.answer(
        "🤖 *Modo PILOT Activado*\n\n"
        "El bot ejecutará operaciones automáticamente.\n"
        "⚠️ _Asegúrate de tener configurado tu riesgo correctamente._",
        parse_mode="Markdown"
    )


@router.message(Command("pnl"))
async def cmd_pnl(message: Message, **kwargs):
    """Show PnL history"""
    session_manager = kwargs.get('session_manager')
    if not session_manager:
        await message.answer("⚠️ Error interno.")
        return
    
    session = session_manager.get_session(str(message.chat.id))
    if not session:
        await message.answer("⚠️ Sin sesión activa. Usa /set\\_keys.")
        return
    
    loading = await message.answer("⏳ Consultando historial de PnL...")
    
    try:
        # Get PnL from session
        if hasattr(session, 'get_pnl_history'):
            pnl_data = await session.get_pnl_history(days=7)
        else:
            pnl_data = []
        
        if not pnl_data:
            await loading.edit_text("📊 No hay historial de PnL disponible.")
            return
        
        # Format output
        msg = "📊 *HISTORIAL DE PnL (7 días)*\n━━━━━━━━━━━━━━━━━━\n\n"
        total = 0.0
        
        for entry in pnl_data[-10:]:  # Last 10 entries
            symbol = entry.get('symbol', 'N/A')
            pnl = float(entry.get('realizedPnl', 0))
            total += pnl
            icon = "🟢" if pnl >= 0 else "🔴"
            msg += f"{icon} {symbol}: `${pnl:,.2f}`\n"
        
        total_icon = "🟢" if total >= 0 else "🔴"
        msg += f"\n━━━━━━━━━━━━━━━━━━\n{total_icon} *TOTAL:* `${total:,.2f}`"
        
        await loading.edit_text(msg, parse_mode="Markdown")
        
    except Exception as e:
        await loading.edit_text(f"❌ Error: {e}")


@router.message(Command("debug"))
async def cmd_debug(message: Message, **kwargs):
    """System diagnostics"""
    import platform
    
    session_manager = kwargs.get('session_manager')
    session = session_manager.get_session(str(message.chat.id)) if session_manager else None
    
    py_ver = platform.python_version()
    os_plat = platform.system()
    
    has_bin = "✅" if session and session.client else "❌"
    has_alp = "✅" if session and session.alpaca_client else "❌"
    
    debug_msg = (
        "🔧 *DIAGNÓSTICO DEL SISTEMA*\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        f"🐍 Python: `{py_ver}`\n"
        f"💻 OS: `{os_plat}`\n"
        f"🏗️ Arch: `Async (aiogram 3.x)`\n\n"
        f"🔌 Binance: {has_bin}\n"
        f"🦙 Alpaca: {has_alp}\n\n"
        f"📡 Sessions: `{len(session_manager.sessions) if session_manager else 0}`\n"
    )
    
    await message.answer(debug_msg, parse_mode="Markdown")
