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


@router.message(Command("exchanges"))
async def cmd_exchanges(message: Message, **kwargs):
    """Exchange status and configuration panel"""
    session_manager = kwargs.get('session_manager')
    session = None

    if session_manager:
        session = session_manager.get_session(str(message.chat.id))

    if not session:
        await message.answer("❌ No tienes una sesión activa. Usa /start primero.")
        return

    # Get exchange configuration and connectivity status
    configured_exchanges = session.get_configured_exchanges()
    exchange_prefs = session.get_exchange_preferences()

    # Check bridge connectivity
    bridge_status = {}
    if hasattr(session, 'bridge') and session.bridge:
        for exchange in ['BINANCE', 'BYBIT', 'ALPACA']:
            bridge_status[exchange] = exchange in session.bridge.adapters
    else:
        bridge_status = {'BINANCE': False, 'BYBIT': False, 'ALPACA': False}

    # Get group status
    from system_directive import GROUP_CONFIG
    crypto_enabled = session.is_group_enabled('CRYPTO')
    bybit_enabled = session.is_group_enabled('BYBIT')
    stocks_enabled = session.is_group_enabled('STOCKS')
    etfs_enabled = session.is_group_enabled('ETFS')

    # Build comprehensive status message
    status_msg = (
        "🔗 <b>ESTADO DE EXCHANGES</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "<b>🔑 Configuración de API Keys:</b>\n"
        f"{'✅' if configured_exchanges.get('BINANCE', False) else '❌'} <b>Binance:</b> {'Configurado' if configured_exchanges.get('BINANCE', False) else 'No configurado'}\n"
        f"{'✅' if configured_exchanges.get('BYBIT', False) else '❌'} <b>Bybit:</b> {'Configurado' if configured_exchanges.get('BYBIT', False) else 'No configurado'}\n"
        f"{'✅' if configured_exchanges.get('ALPACA', False) else '❌'} <b>Alpaca:</b> {'Configurado' if configured_exchanges.get('ALPACA', False) else 'No configurado'}\n\n"
        "<b>🌐 Conectividad Bridge:</b>\n"
        f"{'✅' if bridge_status['BINANCE'] else '❌'} <b>Binance:</b> {'Conectado' if bridge_status['BINANCE'] else 'Desconectado'}\n"
        f"{'✅' if bridge_status['BYBIT'] else '❌'} <b>Bybit:</b> {'Conectado' if bridge_status['BYBIT'] else 'Desconectado'}\n"
        f"{'✅' if bridge_status['ALPACA'] else '❌'} <b>Alpaca:</b> {'Conectado' if bridge_status['ALPACA'] else 'Desconectado'}\n\n"
        "<b>🎯 Grupos Habilitados:</b>\n"
        f"{'✅' if crypto_enabled else '❌'} <b>💰 Crypto:</b> {'Habilitado' if crypto_enabled else 'Deshabilitado'}\n"
        f"{'✅' if stocks_enabled else '❌'} <b>📈 Stocks:</b> {'Habilitado' if stocks_enabled else 'Deshabilitado'}\n"
        f"{'✅' if etfs_enabled else '❌'} <b>📊 ETFs:</b> {'Habilitado' if etfs_enabled else 'Deshabilitado'}\n\n"
        "<b>🚀 Exchanges dentro de Crypto:</b>\n"
        f"{'✅' if exchange_prefs.get('BINANCE', False) else '❌'} <b>Binance:</b> {'Habilitado' if exchange_prefs.get('BINANCE', False) else 'Deshabilitado'}\n"
        f"{'✅' if exchange_prefs.get('BYBIT', False) else '❌'} <b>Bybit:</b> {'Habilitado' if exchange_prefs.get('BYBIT', False) else 'Deshabilitado'}\n\n"
        "<b>🚀 Otros Exchanges:</b>\n"
        f"{'✅' if exchange_prefs.get('ALPACA', False) else '❌'} <b>Alpaca:</b> {'Listo para operar' if exchange_prefs.get('ALPACA', False) else 'No operativo'}\n\n"
    )

    # Add specific guidance based on configuration status
    any_configured = any(configured_exchanges.values())

    if not any_configured:
        status_msg += (
            "<b>🚨 Estado:</b> No tienes exchanges configurados\n\n"
            "<b>💡 Para comenzar:</b>\n"
            "1. Usa /set_keys para configurar tus primeras API keys\n"
            "2. Elige Binance para crypto o Alpaca para stocks\n"
            "3. Una vez configurado, aparecerán balances y podrás operar\n\n"
        )
    else:
        operational_exchanges = [ex for ex, ready in exchange_prefs.items() if ready]
        if operational_exchanges:
            status_msg += (
                f"<b>✅ Estado:</b> {len(operational_exchanges)} exchange(s) operativo(s)\n\n"
                "<b>💡 Consejos:</b>\n"
                "• Usa /dashboard para ver balances y posiciones\n"
                "• Configura más exchanges para diversificar\n"
                "• Revisa /assets para gestionar grupos de activos\n\n"
            )
        else:
            status_msg += (
                "<b>⚠️ Estado:</b> Exchanges configurados pero no operativos\n\n"
                "<b>💡 Posibles soluciones:</b>\n"
                "• Verifica que las API keys sean correctas\n"
                "• Asegúrate de que los grupos estén habilitados\n"
                "• Revisa la conectividad del bridge\n\n"
            )

    # Add debug information if user has exchanges configured but none operational
    if any_configured and not any(exchange_prefs.values()):
        status_msg += (
            "\n<b>🐛 DEBUG INFO:</b>\n"
            f"• Exchanges configurados: {list(configured_exchanges.keys())}\n"
            f"• Grupos habilitados: {[g for g in ['CRYPTO', 'BYBIT', 'STOCKS', 'ETFS'] if session.is_group_enabled(g)]}\n"
            f"• Bridge conectado: {bool(hasattr(session, 'bridge') and session.bridge)}\n"
            f"• Adapters activos: {list(bridge_status.keys()) if hasattr(session, 'bridge') and session.bridge else 'None'}\n\n"
        )

    status_msg += "━━━━━━━━━━━━━━━━━━━━━━━━━"

    # Create keyboard for exchange management
    keyboard_buttons = [
        [InlineKeyboardButton(text="🔄 Recargar Estado", callback_data="EXCHANGES|REFRESH")],
    ]

    # Add toggle buttons for configured exchanges
    if any_configured:
        toggle_buttons = []
        for exchange in ['BINANCE', 'BYBIT', 'ALPACA']:
            if configured_exchanges.get(exchange, False):
                # Check if currently enabled via preferences
                is_enabled = exchange_prefs.get(exchange, False)
                status_emoji = "🟢" if is_enabled else "🔴"
                action = "DISABLE" if is_enabled else "ENABLE"
                toggle_buttons.append(
                    InlineKeyboardButton(
                        text=f"{status_emoji} {exchange}",
                        callback_data=f"EXCHANGES|{action}_{exchange}"
                    )
                )

        if toggle_buttons:
            # Split into rows of 2 buttons max
            for i in range(0, len(toggle_buttons), 2):
                keyboard_buttons.append(toggle_buttons[i:i+2])

    # Add management buttons
    keyboard_buttons.extend([
        [InlineKeyboardButton(text="⚙️ Configurar Grupos", callback_data="CMD|assets")],
        [InlineKeyboardButton(text="🔑 Gestionar Credenciales", callback_data="CMD|set_keys")],
        [InlineKeyboardButton(text="⬅️ Volver a Config", callback_data="CMD|config")]
    ])

    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)

    await message.answer(status_msg, reply_markup=keyboard, parse_mode="HTML")


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

    # Determine current risk profile based on max allowed leverage
    max_allowed_lev = session.config.get('max_leverage_allowed', 5) if session else 5

    # AUTO-APPLY SAVED RISK PROFILE: If current leverage exceeds profile limits, reapply the profile
    if session and lev > max_allowed_lev:
        print(f"⚠️ Leverage {lev}x exceeds profile limit {max_allowed_lev}x - Reapplying risk profile")
        # Get saved risk profile and reapply it
        saved_profile = session.config.get('risk_profile')
        if saved_profile:
            try:
                from handlers.callbacks import apply_risk_profile_to_session
                await apply_risk_profile_to_session(session, saved_profile)
                await session_manager.save_sessions()
                # Update values after reapplying profile
                lev = session.config.get('leverage', 5)
                margin = (session.config.get('max_capital_pct', 0.1) * 100)
                max_allowed_lev = session.config.get('max_leverage_allowed', 5)
                print(f"✅ Risk profile '{saved_profile}' reapplied - Leverage: {lev}x, Max: {max_allowed_lev}x")
            except Exception as e:
                print(f"❌ Error reapplying risk profile: {e}")

    if max_allowed_lev <= 3:
        current_profile = "CONSERVADOR"
        profile_icon = "🛡️"
    elif max_allowed_lev <= 10:
        current_profile = "NEXUS"
        profile_icon = "🌌"
    else:  # 20x
        current_profile = "RONIN"
        profile_icon = "⚔️"

    # Dynamic calculations info
    atr_based = session.config.get('use_atr_for_sl_tp', True) if session else True
    dynamic_indicator = "🎯" if atr_based else "📊"
    
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
    
    # Build keyboard (Propuesta 1: Dashboard Modular con Perfiles de Riesgo)
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        # Estado activo del perfil
        [
            InlineKeyboardButton(text=f"🎯 PERFIL: {current_profile} {profile_icon}",
                                callback_data="INFO|PROFILE")
        ],
        # Perfiles de riesgo (botones principales)
        [
            InlineKeyboardButton(text="🛡️ CONSERVADOR", callback_data="RISK|CONSERVADOR"),
            InlineKeyboardButton(text=f"🌌 NEXUS {'⭐' if current_profile == 'NEXUS' else ''}",
                                callback_data="RISK|NEXUS"),
            InlineKeyboardButton(text="⚔️ RONIN", callback_data="RISK|RONIN")
        ],
        # Información ATR
        [
            InlineKeyboardButton(text=f"{dynamic_indicator} ATR SL/TP: ACTIVE",
                                callback_data="INFO|ATR")
        ],
        # Módulos de configuración
        [
            InlineKeyboardButton(text="🎛️ Ajustes Detallados", callback_data="MODULE|DETAILED"),
            InlineKeyboardButton(text="🧠 IA & Automation", callback_data="MODULE|AI")
        ],
        [
            InlineKeyboardButton(text="🛡️ Protecciones", callback_data="MODULE|PROTECTIONS"),
            InlineKeyboardButton(text="📊 Estrategias", callback_data="MODULE|STRATEGIES")
        ],
        [
            InlineKeyboardButton(text="🔗 Exchanges", callback_data="CMD|exchanges"),
            InlineKeyboardButton(text="📈 Dashboard", callback_data="CMD|dashboard")
        ],
        [
            InlineKeyboardButton(text="⬅️ Volver al Hub", callback_data="CMD|start")
        ]
    ])
    
    msg_text = (
        "⚙️ *CENTRO DE CONTROL NEXUS*\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🎯 **PERFIL ACTIVO: {current_profile} {profile_icon}**\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🎮 Modo: PILOT 🟢\n"
        f"🧠 Personalidad: Nexus Lord\n"
        f"⚖️ Leverage: {lev}x (Máx perfil: {max_allowed_lev}x)\n"
        f"💰 Capital: {margin:.0f}%\n"
        f"{dynamic_indicator} SL/TP: ATR Dinámico\n\n"
        "🛡️ **PERFILES DE RIESGO (Topes Máximos)**\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "💡 **CÁLCULOS DINÁMICOS ATR**\n"
        "• SL/TP siempre calculados por ATR\n"
        "• Leverage/capital se ajustan dinámicamente\n"
        "• Nunca superan los topes del perfil\n\n"
        "**Selecciona un módulo:**"
    )

    if edit_message:
        try:
            await message.edit_text(msg_text, reply_markup=keyboard, parse_mode="Markdown")
        except Exception as e:
            # Handle case where message content/markup is identical (TelegramBadRequest)
            if "message is not modified" in str(e):
                # Message is already up to date, no need to edit
                pass
            else:
                # Re-raise other exceptions
                raise e
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
    
    # Get exchange signal toggles
    binance_signals = session.config.get('signals_binance', True)
    bybit_signals = session.config.get('signals_bybit', True)
    alpaca_signals = session.config.get('signals_alpaca', True)

    msg_text = (
        "🔗 *GESTIÓN DE EXCHANGES*\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🟡 *Binance:* {binance_status}\n"
        f"🟣 *Bybit:* {bybit_status}\n"
        f"🟢 *Alpaca:* {alpaca_status}\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "📡 *SEÑALES POR EXCHANGE:*\n"
        f"{'✅' if binance_signals else '❌'} Binance\n"
        f"{'✅' if bybit_signals else '❌'} Bybit\n"
        f"{'✅' if alpaca_signals else '❌'} Alpaca\n\n"
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
            InlineKeyboardButton(text=f"📡 Binance: {'✅' if binance_signals else '❌'}", callback_data="TOGGLE_SIGNALS|BINANCE"),
            InlineKeyboardButton(text=f"📡 Bybit: {'✅' if bybit_signals else '❌'}", callback_data="TOGGLE_SIGNALS|BYBIT")
        ],
        [
            InlineKeyboardButton(text=f"📡 Alpaca: {'✅' if alpaca_signals else '❌'}", callback_data="TOGGLE_SIGNALS|ALPACA")
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
        try:
            await message.edit_text(msg_text, reply_markup=keyboard, parse_mode="Markdown")
        except Exception as e:
            # Handle case where message content/markup is identical (TelegramBadRequest)
            if "message is not modified" in str(e):
                # Message is already up to date, no need to edit
                pass
            else:
                # Re-raise other exceptions
                raise e
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
    # Sentinel combines Black Swan + Shark
    sent_state = "✅" if session_strategies.get('SENTINEL', True) or session_strategies.get('BLACK_SWAN', True) else "❌"
    
    # Premium Signal State
    try:
        from system_directive import PREMIUM_SIGNALS_ENABLED
        ps_state = "✅" if PREMIUM_SIGNALS_ENABLED else "❌"
    except ImportError:
        ps_state = "❌"

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"💎 Premium Signals: {ps_state}", callback_data="TOGGLE|PREMIUM")],
        [InlineKeyboardButton(text=f"📈 Trend (BTC): {t_state}", callback_data="TOGGLE|TREND")],
        [InlineKeyboardButton(text=f"🛡️ Sentinel (Defense/Shark): {sent_state}", callback_data="TOGGLE|SENTINEL")],
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
        "🛡️ *Sentinel:* Unifica Black Swan (Defensa) y Shark Mode (Ataque)."
    )
    
    if edit_message:
        try:
            await message.edit_text(msg_text, reply_markup=keyboard, parse_mode="Markdown")
        except Exception as e:
            # Handle case where message content/markup is identical (TelegramBadRequest)
            if "message is not modified" in str(e):
                # Message is already up to date, no need to edit
                pass
            else:
                # Re-raise other exceptions
                raise e
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
            
    # Map friendly display names to internal group names
    # Binance controls CRYPTO, Bybit controls BYBIT
    group_mapping = {
        'Binance': 'CRYPTO',
        'Bybit': 'BYBIT',
        'Stocks': 'STOCKS',
        'ETFs': 'ETFS'
    }
    
    group_buttons = []
    for display_name, internal_group in group_mapping.items():
        enabled = session_groups.get(internal_group, False)
        icon = "✅" if enabled else "❌"
        # Use display name in button, but store internal group in callback
        group_buttons.append(InlineKeyboardButton(
            text=f"{icon} {display_name}", 
            callback_data=f"TOGGLEGRP|{internal_group}|{display_name}"
        ))
    
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
        "**Grupos:** Activa/desactiva exchanges completos.\n"
        "Al desactivar un exchange, no recibirás señales de ese exchange.\n\n"
        "**Listas:** Configura activos individuales."
    )
    
    if edit_message:
        try:
            await message.edit_text(msg_text, reply_markup=keyboard, parse_mode="Markdown")
        except Exception as e:
            # Handle case where message content/markup is identical (TelegramBadRequest)
            if "message is not modified" in str(e):
                # Message is already up to date, no need to edit
                pass
            else:
                # Re-raise other exceptions
                raise e
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
        # Save to config (use consistent names with trading_manager)
        session.update_config('bybit_api_key', key)
        session.update_config('bybit_api_secret', secret)
        
        # Initialize the adapter immediately
        loading_msg = await message.answer("⏳ Conectando a Bybit...")
        
        connected = await session.bridge.connect_exchange(
            'BYBIT',
            api_key=key,
            api_secret=secret
        )
        
        await session_manager.save_sessions()
        
        if connected:
            # Test connection by getting balance
            bybit_adapter = session.bridge.adapters.get('BYBIT')
            if bybit_adapter:
                balance = await bybit_adapter.get_account_balance()
                await loading_msg.edit_text(
                    "✅ *Bybit Conectado Exitosamente*\n\n"
                    f"💰 Balance: `${balance.get('total', 0):,.2f} USDT`\n"
                    f"💵 Disponible: `${balance.get('available', 0):,.2f} USDT`\n\n"
                    "🔗 El bot ahora puede operar en Bybit.\n"
                    "Los activos del grupo **BYBIT** serán ruteados automáticamente.",
                    parse_mode="Markdown"
                )
            else:
                await loading_msg.edit_text(
                    "✅ *Bybit Keys Configuradas*\n\n"
                    "⚠️ Adapter registrado pero no verificado.\n"
                    "Reinicia el bot o usa `/debug` para verificar.",
                    parse_mode="Markdown"
                )
        else:
            await loading_msg.edit_text(
                "⚠️ *Keys Guardadas pero Conexión Fallida*\n\n"
                "Verifica que las API keys tengan permisos de:\n"
                "• Lectura de cuenta\n"
                "• Trading de derivados\n\n"
                "Usa `/debug` para más detalles.",
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


@router.message(Command("debug_exchanges"))
async def cmd_debug_exchanges(message: Message, **kwargs):
    """Debug command to show detailed exchange configuration"""
    session_manager = kwargs.get('session_manager')
    session = None

    if session_manager:
        session = session_manager.get_session(str(message.chat.id))

    if not session:
        await message.answer("❌ No tienes una sesión activa. Usa /start primero.")
        return

    # Get all configuration details
    configured_exchanges = session.get_configured_exchanges()
    exchange_prefs = session.get_exchange_preferences()

    debug_msg = (
        "🐛 <b>DEBUG: CONFIGURACIÓN DE EXCHANGES</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "<b>📋 Configuración de API Keys:</b>\n"
    )

    # Show raw config values (masked for security)
    config_items = [
        ('api_key', 'BINANCE API Key'),
        ('api_secret', 'BINANCE API Secret'),
        ('binance_api_key', 'BINANCE API Key (alt)'),
        ('binance_api_secret', 'BINANCE API Secret (alt)'),
        ('bybit_api_key', 'BYBIT API Key'),
        ('bybit_api_secret', 'BYBIT API Secret'),
        ('alpaca_key', 'ALPACA API Key'),
        ('alpaca_secret', 'ALPACA API Secret'),
    ]

    for config_key, display_name in config_items:
        value = session.config.get(config_key, 'NOT SET')
        if value and value != 'NOT SET' and len(str(value)) > 8:
            masked_value = f"{str(value)[:8]}..."
        else:
            masked_value = str(value) if value else 'NOT SET'
        debug_msg += f"• {display_name}: `{masked_value}`\n"

    debug_msg += (
        f"\n<b>🔍 Detección Automática:</b>\n"
        f"• BINANCE configurado: {configured_exchanges.get('BINANCE', False)}\n"
        f"• BYBIT configurado: {configured_exchanges.get('BYBIT', False)}\n"
        f"• ALPACA configurado: {configured_exchanges.get('ALPACA', False)}\n\n"
        f"<b>⚙️ Grupos Habilitados:</b>\n"
        f"• 💰 CRYPTO: {session.is_group_enabled('CRYPTO')}\n"
        f"• 📈 STOCKS: {session.is_group_enabled('STOCKS')}\n"
        f"• 📊 ETFS: {session.is_group_enabled('ETFS')}\n\n"
        f"<b>🔄 Exchanges dentro de CRYPTO:</b>\n"
        f"<b>🔌 Bridge Status:</b>\n"
    )

    if hasattr(session, 'bridge') and session.bridge:
        adapters = list(session.bridge.adapters.keys()) if session.bridge.adapters else []
        debug_msg += f"• Bridge conectado: ✅\n"
        debug_msg += f"• Adapters activos: {adapters}\n"
    else:
        debug_msg += "• Bridge conectado: ❌\n"

    debug_msg += (
        f"\n<b>🚀 Estado Final:</b>\n"
        f"• BINANCE operativo: {exchange_prefs.get('BINANCE', False)}\n"
        f"• BYBIT operativo: {exchange_prefs.get('BYBIT', False)}\n"
        f"• ALPACA operativo: {exchange_prefs.get('ALPACA', False)}\n\n"
        f"<b>💡 Diagnóstico:</b>\n"
    )

    exchange_prefs = session.get_exchange_preferences()
    debug_msg += (
        f"• BINANCE: {exchange_prefs.get('BINANCE', False)}\n"
        f"• BYBIT: {exchange_prefs.get('BYBIT', False)}\n\n"
    )

    # Diagnostic logic
    issues = []

    if not configured_exchanges.get('BINANCE', False) and not configured_exchanges.get('BYBIT', False) and not configured_exchanges.get('ALPACA', False):
        issues.append("• No hay API keys configuradas")
    else:
        if configured_exchanges.get('BINANCE', False) and not exchange_prefs.get('BINANCE', False):
            issues.append("• BINANCE: Configurado pero no operativo (revisa bridge/grupos)")
        if configured_exchanges.get('BYBIT', False) and not exchange_prefs.get('BYBIT', False):
            issues.append("• BYBIT: Configurado pero no operativo (revisa bridge/grupos)")
        if configured_exchanges.get('ALPACA', False) and not exchange_prefs.get('ALPACA', False):
            issues.append("• ALPACA: Configurado pero no operativo (revisa bridge/grupos)")

    if issues:
        debug_msg += "\n".join(issues)
    else:
        debug_msg += "• No se detectaron problemas evidentes"

    # Add hierarchy explanation
    debug_msg += "\n\n" + "="*50 + "\n"
    debug_msg += session.explain_group_hierarchy()

    await message.answer(debug_msg, parse_mode="HTML")
