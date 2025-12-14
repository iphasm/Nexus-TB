"""
Antigravity Bot - Configuration Handlers
Config commands: /config, /strategies, /assets, /toggle, /set_keys, /set_alpaca
"""

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

router = Router(name="config")


@router.message(Command("config"))
async def cmd_config(message: Message, **kwargs):
    """Interactive configuration panel"""
    session_manager = kwargs.get('session_manager')
    session = None
    
    if session_manager:
        session = session_manager.get_session(str(message.chat.id))
    
    # Get current values
    lev = session.config.get('leverage', 5) if session else 5
    margin = (session.config.get('max_capital_pct', 0.1) * 100) if session else 10
    
    # Build keyboard
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🎛️ Estrategias", callback_data="CMD|strategies"),
            InlineKeyboardButton(text="📡 Grupos", callback_data="CMD|togglegroup")
        ],
        [
            InlineKeyboardButton(text="🪙 Activos (Blacklist)", callback_data="CMD|assets")
        ],
        [
            InlineKeyboardButton(text=f"⚖️ Lev: {lev}x", callback_data="CFG|LEV_MENU"),
            InlineKeyboardButton(text=f"💰 Margin: {margin:.0f}%", callback_data="CFG|MARGIN_MENU")
        ],
        [
            InlineKeyboardButton(text="🧠 Personalidad", callback_data="CMD|personality")
        ]
    ])
    
    await message.answer(
        "⚙️ *PANEL DE CONTROL*\n"
        "Selecciona qué deseas ajustar:",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )


@router.message(Command("strategies"))
async def cmd_strategies(message: Message, **kwargs):
    """Interactive strategy selector"""
    # Import strategy config
    try:
        from antigravity_quantum.config import ENABLED_STRATEGIES
    except ImportError:
        ENABLED_STRATEGIES = {'SCALPING': True, 'GRID': True, 'MEAN_REVERSION': True, 'SHARK': True}
    
    # Build state strings
    s_state = "✅ ACTIVADO" if ENABLED_STRATEGIES.get('SCALPING', True) else "❌ DESACTIVADO"
    g_state = "✅ ACTIVADO" if ENABLED_STRATEGIES.get('GRID', True) else "❌ DESACTIVADO"
    m_state = "✅ ACTIVADO" if ENABLED_STRATEGIES.get('MEAN_REVERSION', True) else "❌ DESACTIVADO"
    sh_state = "✅ ACTIVADO" if ENABLED_STRATEGIES.get('SHARK', True) else "❌ DESACTIVADO"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"⚡ Scalping: {s_state}", callback_data="TOGGLE|SCALPING")],
        [InlineKeyboardButton(text=f"🕸️ Grid: {g_state}", callback_data="TOGGLE|GRID")],
        [InlineKeyboardButton(text=f"📉 Mean Rev: {m_state}", callback_data="TOGGLE|MEAN_REVERSION")],
        [InlineKeyboardButton(text=f"🦈 Shark Mode: {sh_state}", callback_data="TOGGLE|SHARK")]
    ])
    
    await message.answer(
        "🎛️ *CONFIGURACIÓN DE ESTRATEGIAS*\n"
        "Activa/Desactiva módulos de trading:\n\n"
        "_Nota: Shark Mode corre en segundo plano para protección._",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )


@router.message(Command("togglegroup"))
async def cmd_togglegroup(message: Message, **kwargs):
    """Interactive group selector"""
    # Import group config
    GROUP_CONFIG = {
        'CRYPTO': True,
        'STOCKS': True,
        'COMMODITY': True
    }
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=f"{'✅' if enabled else '❌'} {group}",
            callback_data=f"TOGGLEGRP|{group}"
        )] for group, enabled in GROUP_CONFIG.items()
    ])
    
    await message.answer(
        "📡 *CONFIGURACIÓN DE RADARES*\n"
        "Activa/Desactiva grupos de mercado:",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )


@router.message(Command("assets"))
async def cmd_assets(message: Message, **kwargs):
    """Hierarchical asset selection menu"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🦈 Shark Targets", callback_data="ASSETS|SHARK"),
            InlineKeyboardButton(text="⚡ Scalping", callback_data="ASSETS|SCALPING")
        ],
        [
            InlineKeyboardButton(text="🕸️ Grid Trading", callback_data="ASSETS|GRID"),
            InlineKeyboardButton(text="📉 Mean Reversion", callback_data="ASSETS|MEANREV")
        ],
        [
            InlineKeyboardButton(text="📡 Scanner Global", callback_data="ASSETS|GLOBAL")
        ]
    ])
    
    await message.answer(
        "📦 *CONFIGURACIÓN DE ACTIVOS*\n\n"
        "Selecciona el módulo a configurar:",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )


@router.message(Command("set_keys", "setkeys"))
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
            "⚠️ Uso: `/set_keys <API_KEY> <API_SECRET>`\n"
            "_(Te recomendamos borrar el mensaje después)_",
            parse_mode="Markdown"
        )
        return
    
    key = args[1].strip()
    secret = args[2].strip()
    
    try:
        # Create or update session
        session = await session_manager.create_or_update_session(chat_id, key, secret)
        
        status = "✅ *API Keys Configuradas Correctamente.*\n"
        if session.client:
            status += "🔌 Conexión con Binance: *ESTABLE*"
        else:
            status += "⚠️ Keys guardadas pero *falló la conexión* (Revisa si son correctas)."
        
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
    
    key = args[1].strip()
    secret = args[2].strip()
    
    try:
        # Update config
        await session.update_config('alpaca_key', key)
        await session.update_config('alpaca_secret', secret)
        await session.initialize_alpaca()
        
        await session_manager.save_sessions()
        
        status = "✅ *Alpaca Keys Configuradas*\n"
        if session.alpaca_client:
            status += "🦙 Conexión con Alpaca: *ESTABLE*"
        else:
            status += "⚠️ Keys guardadas pero *falló la conexión*."
        
        await message.answer(status, parse_mode="Markdown")
        
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
    from utils.personalities import PersonalityManager
    
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
