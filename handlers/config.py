"""
NEXUS TRADING BOT - Configuration Handlers
Config commands: /config, /strategies, /assets, /toggle, /set_keys, /set_alpaca
"""

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

import os
import re

router = Router(name="config")

def get_proxy_ip_safe() -> str:
    """Extract IP from PROXY_URL safely."""
    proxy = os.getenv('PROXY_URL', '')
    if not proxy: return None
    
    # Regex to extract IP
    match = re.search(r'@([\d\.]+):', proxy)
    if match:
        return match.group(1)
    
    # Try simple split if regex fails (e.g. http://1.2.3.4:80)
    try:
        if '@' in proxy:
            return proxy.split('@')[1].split(':')[0]
        else:
            return proxy.split('//')[1].split(':')[0]
    except:
        return None


@router.message(Command("config"))
async def cmd_config(message: Message, **kwargs):
    """Interactive configuration panel"""
    session_manager = kwargs.get('session_manager')
    edit_message = kwargs.get('edit_message', False)
    session = None
    
    if session_manager:
        session = session_manager.get_session(str(message.chat.id))
    
    # Get current values
    lev = session.config.get('leverage', 5) if session else 5
    margin = (session.config.get('max_capital_pct', 0.1) * 100) if session else 10
    
    # Circuit Breaker Status
    cb_enabled = session.config.get('circuit_breaker_enabled', True) if session else True
    cb_status = "🟢 ON" if cb_enabled else "🔴 OFF"
    
    # ML Classifier Status (Global)
    try:
        from system_directive import ML_CLASSIFIER_ENABLED
        ml_status = "🟢 ON" if ML_CLASSIFIER_ENABLED else "🔴 OFF"
    except ImportError:
        ml_status = "❓ N/A"

    # AI Filter Status (Session)
    ai_enabled = session.config.get('sentiment_filter', True) if session else True
    ai_status = "🟢 ON" if ai_enabled else "🔴 OFF"

    # Kelly & Shield Status
    kelly_enabled = session.config.get('use_kelly_criterion', False) if session else False
    kelly_status = "🟢 ON" if kelly_enabled else "🔴 OFF"
    
    shield_enabled = session.config.get('correlation_guard_enabled', True) if session else True
    shield_status = "🟢 ON" if shield_enabled else "🔴 OFF"
    
    # Build keyboard (v4 Clean)
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🎛️ Estrategias (Motor)", callback_data="CMD|strategies"),
            InlineKeyboardButton(text="📡 Grupos y Activos", callback_data="CMD|assets")
        ],
        [
            InlineKeyboardButton(text=f"⚖️ Lev: {lev}x", callback_data="CFG|LEV_MENU"),
            InlineKeyboardButton(text=f"💰 Margin: {margin:.0f}%", callback_data="CFG|MARGIN_MENU")
        ],
        [
            InlineKeyboardButton(text=f"✨ AI Filter [{ai_status}]", callback_data="TOGGLE|AI_FILTER"),
            InlineKeyboardButton(text=f"🧠 ML Mode [{ml_status}]", callback_data="TOGGLE|ML_MODE")
        ],
        [
            InlineKeyboardButton(text=f"🔌 Circuit Breaker [{cb_status}]", callback_data="TOGGLE|CIRCUIT_BREAKER"),
            InlineKeyboardButton(text="🧩 Personalidad", callback_data="CMD|personality")
        ],
        [
            InlineKeyboardButton(text=f"💰 Kelly Criterion [{kelly_status}]", callback_data="TOGGLE|KELLY"),
            InlineKeyboardButton(text=f"🛡️ Portf. Shield [{shield_status}]", callback_data="TOGGLE|SHIELD")
        ],
        [
            InlineKeyboardButton(text="⬅️ Volver al Hub", callback_data="CMD|start")
        ]
    ])
    
    msg_text = (
        "⚙️ *PANEL DE CONTROL*\n"
        "Selecciona qué deseas ajustar:"
    )
    
    if edit_message:
        await message.edit_text(msg_text, reply_markup=keyboard, parse_mode="Markdown")
    else:
        await message.answer(msg_text, reply_markup=keyboard, parse_mode="Markdown")


@router.message(Command("exchanges"))
async def cmd_exchanges(message: Message, **kwargs):
    """Unified Exchange Dashboard"""
    session_manager = kwargs.get('session_manager')
    edit_message = kwargs.get('edit_message', False)
    
    if not session_manager:
        await message.answer("⚠️ Error interno.")
        return
    
    session = session_manager.get_session(str(message.chat.id))
    if not session:
        await message.answer("⚠️ Sin sesión. Usa /start primero.")
        return
    
    # Determine connection status for each exchange
    # FIX: Use Bridge Adapters instead of deprecated clients
    binance_status = "✅ Conectado" if session.bridge.adapters.get('BINANCE') else "❌ No Configurado"
    bybit_status = "✅ Conectado" if session.bridge.adapters.get('BYBIT') else "❌ No Configurado"
    alpaca_status = "✅ Conectado" if session.bridge.adapters.get('ALPACA') else "❌ No Configurado"
    
    # Primary exchange
    primary = session.config.get('primary_exchange', 'BINANCE')
    
    msg_text = (
        "🔗 *GESTIÓN DE EXCHANGES*\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🟡 *Binance:* {binance_status}\n"
        f"🟣 *Bybit:* {bybit_status}\n"
        f"🟢 *Alpaca:* {alpaca_status}\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"⭐ *Exchange Principal (Crypto):* `{primary}`\n"
        "_Usado para comandos genéricos como /long BTCUSDT_"
    )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🔑 Config Binance", callback_data="WIZARD|BINANCE"),
            InlineKeyboardButton(text="🔑 Config Bybit", callback_data="WIZARD|BYBIT")
        ],
        [
            InlineKeyboardButton(text="🔑 Config Alpaca", callback_data="WIZARD|ALPACA")
        ],
        [
            InlineKeyboardButton(text=f"⭐ Set Primary: BINANCE", callback_data="EXCHANGE|PRIMARY|BINANCE"),
            InlineKeyboardButton(text=f"⭐ Set Primary: BYBIT", callback_data="EXCHANGE|PRIMARY|BYBIT")
        ],
        [
            InlineKeyboardButton(text="🗑️ Reset Keys", callback_data="CMD|delete_keys")
        ],
        [
            InlineKeyboardButton(text="⬅️ Volver", callback_data="CMD|config")
        ]
    ])
    
    if edit_message:
        await message.edit_text(msg_text, reply_markup=keyboard, parse_mode="Markdown")
    else:
        await message.answer(msg_text, reply_markup=keyboard, parse_mode="Markdown")


@router.message(Command("strategies"))
async def cmd_strategies(message: Message, **kwargs):
    """Interactive strategy selector - ALL 6 STRATEGIES"""
    edit_message = kwargs.get('edit_message', False)
    
    # Get session configuration
    session_strategies = {}
    if kwargs.get('session_manager'):
        session = kwargs['session_manager'].get_session(str(message.chat.id))
        if session:
            session_strategies = session.config.get('strategies', {})
            
    # Default fallback if no session (should not happen usually)
    if not session_strategies:
        try:
             from system_directive import ENABLED_STRATEGIES
             session_strategies = ENABLED_STRATEGIES.copy()
        except ImportError:
             session_strategies = {'TREND': True, 'SCALPING': True, 'GRID': True, 'MEAN_REVERSION': True, 'BLACK_SWAN': True, 'SHARK': False}

    # Build state strings
    t_state = "✅" if session_strategies.get('TREND', True) else "❌"
    s_state = "✅" if session_strategies.get('SCALPING', True) else "❌"
    g_state = "✅" if session_strategies.get('GRID', True) else "❌"
    m_state = "✅" if session_strategies.get('MEAN_REVERSION', True) else "❌"
    bs_state = "✅" if session_strategies.get('BLACK_SWAN', True) else "❌"
    sh_state = "✅" if session_strategies.get('SHARK', False) else "❌"
    
    # Premium Signal State
    try:
        from system_directive import PREMIUM_SIGNALS_ENABLED
        ps_state = "✅" if PREMIUM_SIGNALS_ENABLED else "❌"
    except ImportError:
        ps_state = "❌"

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"💎 Premium Signals: {ps_state}", callback_data="TOGGLE|PREMIUM")],
        [InlineKeyboardButton(text=f"📈 Trend (BTC): {t_state}", callback_data="TOGGLE|TREND")],
        [InlineKeyboardButton(text=f"🦢 Black Swan: {bs_state}", callback_data="TOGGLE|BLACK_SWAN")],
        [InlineKeyboardButton(text=f"🦈 Shark Mode: {sh_state}", callback_data="TOGGLE|SHARK")],
        [
            InlineKeyboardButton(text=f"⚡ Scalping: {s_state}", callback_data="TOGGLE|SCALPING"),
            InlineKeyboardButton(text=f"🕸️ Grid: {g_state}", callback_data="TOGGLE|GRID")
        ],
        [InlineKeyboardButton(text=f"📉 Mean Rev: {m_state}", callback_data="TOGGLE|MEAN_REVERSION")],
        [InlineKeyboardButton(text="⬅️ Volver", callback_data="CMD|config")]
    ])
    
    msg_text = (
        "🎛️ *MOTOR DINÁMICO DE ESTRATEGIAS*\n"
        "El sistema selecciona automáticamente la mejor estrategia:\n\n"
        "• 📈 *Trend* - Tendencias fuertes (RSI > 50 + ADX)\n"
        "• ⚡ *Scalping* - Alta volatilidad intradía\n"
        "• 🕸️ *Grid* - Mercados laterales\n"
        "• 📉 *Mean Rev* - Reversión a la media\n\n"
        "_Los módulos Black Swan y Shark siguen siendo configurables:_ "
    )
    
    if edit_message:
        await message.edit_text(msg_text, reply_markup=keyboard, parse_mode="Markdown")
    else:
        await message.answer(msg_text, reply_markup=keyboard, parse_mode="Markdown")


@router.message(Command("togglegroup"))
async def cmd_togglegroup(message: Message, **kwargs):
    """Interactive group selector - redirects to assets"""
    # Redirect to unified assets menu
    await cmd_assets(message, **kwargs)


@router.message(Command("assets"))
async def cmd_assets(message: Message, **kwargs):
    """v4 Combined Assets + Groups Menu"""
    edit_message = kwargs.get('edit_message', False)
    
    # 1. Groups Section
    from system_directive import GROUP_CONFIG
    session_groups = dict(GROUP_CONFIG)
    if kwargs.get('session_manager'):
        session = kwargs['session_manager'].get_session(str(message.chat.id))
        if session:
            stored = session.config.get('groups', {})
            session_groups.update(stored)
            # Standardize naming if legacy state exists
            if 'COMMODITY' in session_groups:
                session_groups['ETFS'] = session_groups.pop('COMMODITY')
            
    group_buttons = []
    for grp, enabled in session_groups.items():
        if grp.startswith('_'): continue # Skip internal keys
        icon = "✅" if enabled else "❌"
        group_buttons.append(InlineKeyboardButton(text=f"{icon} {grp}", callback_data=f"TOGGLEGRP|{grp}"))
    
    # 2. Specific Asset Lists
    list_buttons = [
        InlineKeyboardButton(text="🦈 Shark Targets", callback_data="ASSETS|SHARK"),
        InlineKeyboardButton(text="📡 Scanner Global", callback_data="ASSETS|GLOBAL")
    ]
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        group_buttons, # Row 1: Groups
        list_buttons,  # Row 2: Asset Lists
        [InlineKeyboardButton(text="⬅️ Volver", callback_data="CMD|config")]
    ])
    
    msg_text = (
        "📦 *GESTIÓN DE ACTIVOS*\n\n"
        "1. **Grupos:** Activa sectores completos.\n"
        "2. **Listas:** Configura activos individuales."
    )
    
    if edit_message:
        await message.edit_text(msg_text, reply_markup=keyboard, parse_mode="Markdown")
    else:
        await message.answer(msg_text, reply_markup=keyboard, parse_mode="Markdown")


@router.message(Command("set_binance", "setbinance"))
async def cmd_set_keys(message: Message, **kwargs):
    """Configure Binance API Keys"""
    session_manager = kwargs.get('session_manager')
    if not session_manager:
        await message.answer("⚠️ Error interno.")
        return
    
    chat_id = str(message.chat.id)
    args = message.text.split()
    
    if len(args) != 3:
        await message.answer(
            "⚠️ Uso: `/set_binance <API_KEY> <API_SECRET>`\n"
            "_(Te recomendamos borrar el mensaje después)_",
            parse_mode="Markdown"
        )
        return
    
    key = args[1].strip().strip('<>').strip()
    secret = args[2].strip().strip('<>').strip()
    
    try:
        # Create or update session
        session = await session_manager.create_or_update_session(chat_id, key, secret)
        
        status = "✅ *API Keys Configuradas Correctamente.*\n"
        # FIX: Check Bridge for connection status
        if session.bridge.adapters.get('BINANCE'):
            status += "🔌 Conexión con Binance: *ESTABLE*"
        else:
            status += "⚠️ Keys guardadas pero *falló la conexión* (Revisa si son correctas)."
            
        # PROXY INSTRUCTION
        proxy_ip = get_proxy_ip_safe()
        if proxy_ip:
            status += (
                f"\n\n🚨 **ACCIÓN REQUERIDA** 🚨\n"
                f"Para evitar bloqueos, añade esta IP a la **Lista Blanca (Whitelist)** de tu API en Binance:\n"
                f"`{proxy_ip}`"
            )
        
        await message.answer(status, parse_mode="Markdown")
        
    except Exception as e:
        await message.answer(f"❌ Error: {e}")


@router.message(Command("set_alpaca", "setalpaca"))
async def cmd_set_alpaca(message: Message, **kwargs):
    """Configure Alpaca API Keys"""
    session_manager = kwargs.get('session_manager')
    if not session_manager:
        await message.answer("⚠️ Error interno.")
        return
    
    chat_id = str(message.chat.id)
    session = session_manager.get_session(chat_id)
    
    if not session:
        await message.answer("⚠️ Primero configura tu sesión con `/set_keys`.", parse_mode="Markdown")
        return
    
    args = message.text.split()
    if len(args) != 3:
        await message.answer(
            "⚠️ Uso: `/set_alpaca <API_KEY> <SECRET>`\n"
            "_(Te recomendamos borrar el mensaje después)_",
            parse_mode="Markdown"
        )
        return
    
    key = args[1].strip().strip('<>').strip()
    secret = args[2].strip().strip('<>').strip()
    
    try:
        # Update config
        await session.update_config('alpaca_key', key)
        await session.update_config('alpaca_secret', secret)
        await session.initialize_alpaca()
        
        await session_manager.save_sessions()
        
        status = "✅ *Alpaca Keys Configuradas*\n"
        # FIX: Check Bridge for connection status
        if session.bridge.adapters.get('ALPACA'):
            status += "🦙 Conexión con Alpaca: *ESTABLE*"
        else:
            status += "⚠️ Keys guardadas pero *falló la conexión*."
            
        # PROXY INSTRUCTION
        proxy_ip = get_proxy_ip_safe()
        if proxy_ip:
            status += (
                f"\n\n🚨 **ACCIÓN REQUERIDA** 🚨\n"
                f"Asegúrate de permitir el acceso desde esta IP en Alpaca:\n"
                f"`{proxy_ip}`"
            )
        
        await message.answer(status, parse_mode="Markdown")
        
    except Exception as e:
        await message.answer(f"❌ Error: {e}")


@router.message(Command("set_bybit", "setbybit"))
async def cmd_set_bybit(message: Message, **kwargs):
    """Configure Bybit API Keys for enhanced order management."""
    session_manager = kwargs.get('session_manager')
    if not session_manager:
        await message.answer("⚠️ Error interno.")
        return
    
    chat_id = str(message.chat.id)
    session = session_manager.get_session(chat_id)
    
    if not session:
        await message.answer(
            "⚠️ Primero configura tu sesión con `/set_binance`.\n"
            "Bybit se puede usar como exchange alternativo para crypto.",
            parse_mode="Markdown"
        )
        return
    
    args = message.text.split()
    if len(args) != 3:
        await message.answer(
            "⚠️ *Configurar Bybit*\n\n"
            "**Uso:** `/set_bybit <API_KEY> <SECRET>`\n\n"
            "**Ventajas de Bybit:**\n"
            "• Cancelación de órdenes en un solo request\n"
            "• TP/SL vinculados a posición\n"
            "• Edición de órdenes en caliente\n"
            "• Trailing stops nativos\n\n"
            "_(Borra este mensaje después)_",
            parse_mode="Markdown"
        )
        return
    
    key = args[1].strip().strip('<>').strip()
    secret = args[2].strip().strip('<>').strip()
    
    try:
        await session.update_config('bybit_key', key)
        await session.update_config('bybit_secret', secret)
        await session_manager.save_sessions()
        
        await message.answer(
            "✅ *Bybit Keys Configuradas*\n\n"
            "🔐 Credenciales guardadas.\n\n"
            "**Para usar Bybit para crypto:**\n"
            "Contacta al admin para cambiar `crypto_exchange` a `BYBIT`.",
            parse_mode="Markdown"
        )
        
    except Exception as e:
        await message.answer(f"❌ Error: {e}")


@router.message(Command("delete_keys", "deletekeys"))
async def cmd_delete_keys(message: Message, **kwargs):
    """Delete user's API Keys"""
    session_manager = kwargs.get('session_manager')
    if not session_manager:
        await message.answer("⚠️ Error interno.")
        return
    
    chat_id = str(message.chat.id)
    session = session_manager.get_session(chat_id)
    
    if not session:
        await message.answer("⚠️ No tienes ninguna sesión activa para eliminar.")
        return
    
    try:
        success = await session_manager.delete_session(chat_id)
        if success:
            await message.answer(
                "🗑️ *Sesión Eliminada*\n\n"
                "Tus API Keys han sido borradas de nuestra base de datos.\n"
                "Para volver a operar, usa `/set_keys <API_KEY> <SECRET>`",
                parse_mode="Markdown"
            )
        else:
            await message.answer("❌ Error eliminando la sesión.")
    except Exception as e:
        await message.answer(f"❌ Error: {e}")


@router.message(Command("personality"))
async def cmd_personality(message: Message, **kwargs):
    """Personality selector menu - DYNAMICALLY loaded from PersonalityManager"""
    from servos.personalities import PersonalityManager
    
    pm = PersonalityManager()
    
    # Build list from PROFILES: [(display_name, code), ...]
    personalities = []
    for code, profile in pm.PROFILES.items():
        name = profile.get('NAME', code)
        personalities.append((name, code))
    
    # Sort by name for consistency
    personalities.sort(key=lambda x: x[0])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=name, callback_data=f"PERSONALITY|{code}")]
        for name, code in personalities
    ])
    
    await message.answer(
        "🧠 *SELECCIÓN DE PERSONALIDAD*\n\n"
        "Elige el estilo de comunicación del bot:",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )


@router.message(Command("set_leverage", "setleverage"))
async def cmd_set_leverage(message: Message, **kwargs):
    """Leverage selection menu"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="3x", callback_data="CFG|LEV|3"),
            InlineKeyboardButton(text="5x", callback_data="CFG|LEV|5"),
            InlineKeyboardButton(text="10x", callback_data="CFG|LEV|10")
        ],
        [
            InlineKeyboardButton(text="15x", callback_data="CFG|LEV|15"),
            InlineKeyboardButton(text="20x", callback_data="CFG|LEV|20"),
            InlineKeyboardButton(text="25x", callback_data="CFG|LEV|25")
        ]
    ])
    
    await message.answer(
        "⚖️ *CONFIGURAR APALANCAMIENTO*\n\n"
        "Selecciona el nivel de leverage:",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )


@router.message(Command("set_margin", "setmargin"))
async def cmd_set_margin(message: Message, **kwargs):
    """Margin percentage selection menu"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="5%", callback_data="CFG|MARGIN|5"),
            InlineKeyboardButton(text="10%", callback_data="CFG|MARGIN|10"),
            InlineKeyboardButton(text="15%", callback_data="CFG|MARGIN|15")
        ],
        [
            InlineKeyboardButton(text="20%", callback_data="CFG|MARGIN|20"),
            InlineKeyboardButton(text="25%", callback_data="CFG|MARGIN|25"),
            InlineKeyboardButton(text="50%", callback_data="CFG|MARGIN|50")
        ]
    ])
    
    await message.answer(
        "💰 *CONFIGURAR MARGEN*\n\n"
        "Porcentaje del balance a usar por operación:",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
