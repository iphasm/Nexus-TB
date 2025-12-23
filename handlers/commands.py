"""
Antigravity Bot - Command Handlers
Basic commands: /start, /help, /status, /wallet, /price, /pnl
EXACT REPLICA of main.py interface
"""

import asyncio
import logging
import random
import os
import requests
from aiogram import Router, F
from aiogram.filters import Command, CommandStart
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from utils.auth import admin_only, is_authorized_admin, owner_only
from utils.db import get_user_name

router = Router(name="commands")

# --- ASSET CONFIGURATION (Centralized) ---
from config import ASSET_GROUPS, GROUP_CONFIG, TICKER_MAP, get_display_name


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
    """
    v4 CENTRAL HUB
    Single message navigation center.
    """
    edit_message = kwargs.get('edit_message', False)
    session_manager = kwargs.get('session_manager')
    
    # 1. Loading State (only if new message)
    if not edit_message:
        msg_load = await message.answer("🔄 _Iniciando v4 Hub..._", parse_mode="Markdown")
        await asyncio.sleep(0.3)
    else:
        msg_load = message

    # 2. Session Data
    chat_id = str(message.chat.id)
    session = session_manager.get_session(chat_id) if session_manager else None
    user_name = get_user_name(chat_id)
    
    # Defaults
    mode = "WATCHER"
    p_name = "Estándar"
    risk_label = "Personalizado"
    p_key = "STANDARD_ES"
    
    if session:
        # Mode
        mode = session.config.get('mode', 'WATCHER')
        
        # Personality
        p_key = session.config.get('personality', 'STANDARD_ES')
        from utils.personalities import PersonalityManager
        p_name = PersonalityManager().get_profile(p_key).get('NAME', p_key)
        
        # Risk
        lev = session.config.get('leverage', 5)
        sl = session.config.get('stop_loss_pct', 0.02)
        if lev == 20: risk_label = "⚔️ Ronin"
        elif lev == 3: risk_label = "🛡️ Guardian"
        elif lev == 5: risk_label = "🌌 Quantum"

    # 3. Status Icons
    mode_icon = {
        'PILOT': '🤖',
        'COPILOT': '👨‍✈️',
        'WATCHER': '👁️'
    }.get(mode, '❓')
    
    # 4. Message Content (Personalized)
    from utils.personalities import PersonalityManager
    pm = PersonalityManager()
    
    # AI Filter Status (Moved up for header construction)
    ai_enabled = True
    if session:
        ai_enabled = session.config.get('sentiment_filter', True)
    ai_status = "🟢 ON" if ai_enabled else "🔴 OFF"
    ai_header_suffix = " + 🧠" if ai_enabled else ""

    # 4. Message Content (Custom Layout)
    from utils.personalities import PersonalityManager
    pm = PersonalityManager()
    profile = pm.get_profile(p_key)
    p_name = profile.get('NAME', p_name)
    
    # Get a greeting quote and format it with user_name
    raw_greeting = profile.get('GREETING', ["Ready."])
    if isinstance(raw_greeting, list):
        quote = random.choice(raw_greeting)
    else:
        quote = raw_greeting
        
    try:
        quote = quote.format(user_name=user_name)
    except:
        pass
        
    # Indent the quote for the UI
    formatted_quote = f"      \"{quote}\""

    welcome = (
        f"🌌 **ANTIGRAVITY BOT v4.0** | {mode_icon} **{mode}{ai_header_suffix}**\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🎭 **Personalidad:** {p_name}\n"
        f"{formatted_quote}\n"
        f"⚖️ **Riesgo:** {risk_label}\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "Selecciona un módulo operativo:"
    )
    
    # 5. v4 Interactive Keyboard
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        # Main Operations
        [
            InlineKeyboardButton(text="📈 Dashboard", callback_data="CMD|dashboard"),
            InlineKeyboardButton(text="📡 Intel", callback_data="MENU|INTEL")
        ],
        # Quick Actions
        [
            InlineKeyboardButton(text=f"🎮 Modos ({mode})", callback_data="MENU|MODES"),
            InlineKeyboardButton(text="⚙️ Config", callback_data="CMD|config")
        ],
        # Tools
        [
            InlineKeyboardButton(text="🔄 Sync", callback_data="SYNC_ORDERS"),
            InlineKeyboardButton(text=f"🧠 AI Filter [{ai_status}]", callback_data="TOGGLE|AI_FILTER") 
        ],
        # Info
        [
            InlineKeyboardButton(text="❓ Ayuda / Docs", callback_data="CMD|help")
        ]
    ])
    
    if edit_message:
        await msg_load.edit_text(welcome, reply_markup=keyboard, parse_mode="Markdown")
    else:
        await msg_load.edit_text(welcome, reply_markup=keyboard, parse_mode="Markdown")


# --- NEW MENU HANDLERS ---

@router.callback_query(F.data == "MENU|MODES")
async def menu_modes(callback: CallbackQuery, **kwargs):
    """Sub-menu for Mode Selection"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🤖 PILOT (Auto)", callback_data="CMD|pilot")],
        [InlineKeyboardButton(text="👨‍✈️ COPILOT (Semi)", callback_data="CMD|copilot")],
        [InlineKeyboardButton(text="👁️ WATCHER (Alertas)", callback_data="CMD|watcher")],
        [InlineKeyboardButton(text="🔙 Volver al Hub", callback_data="CMD|start")]
    ])
    
    await callback.message.edit_text(
        "🎮 *SELECTOR DE MODO*\n\n"
        "• **PILOT**: El bot opera 100% solo.\n"
        "• **COPILOT**: Te pregunta antes de entrar.\n"
        "• **WATCHER**: Solo envía señales.\n\n"
        "Selecciona modo activo:",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )



@router.message(Command("startup"))
async def cmd_startup(message: Message):
    """Onboarding guide - explains how to set up the bot"""
    
    startup_text = (
        "🚀 **GUÍA DE INICIO RÁPIDO**\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        
        "🤖 **¿Qué es Antigravity Bot?**\n"
        "Un sistema de trading automatizado que opera en Binance (Crypto) y Alpaca (Stocks/ETFs) "
        "usando algoritmos avanzados de análisis técnico y sentimiento de mercado.\n\n"
        
        "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "🔧 **CONFIGURACIÓN INICIAL**\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        
        "**PASO 1: Configurar Binance (Crypto)**\n"
        "1. Ve a [Binance API Management](https://www.binance.com/en/my/settings/api-management)\n"
        "2. Crea una nueva API Key con permisos:\n"
        "   • ✅ Enable Reading\n"
        "   • ✅ Enable Futures\n"
        "   • ✅ Enable Spot & Margin (opcional)\n"
        "   • ⛔ NO habilites Withdrawals\n"
        "   • 🛡️ **IP Whitelist**: Debes agregar la IP confiable `96.62.194.97`\n"
        "     *(Sin esto, la API rechazará las conexiones de Railway)*\n"
        "3. Copia tu API Key y Secret\n"
        "4. Usa el comando:\n"
        "   `/set_binance <API_KEY> <API_SECRET>`\n"
        "   ⚠️ _Borra el mensaje después de enviarlo_\n\n"
        
        "**PASO 2: Configurar Alpaca (Stocks)** *(opcional)*\n"
        "1. Crea cuenta en [Alpaca Markets](https://alpaca.markets/)\n"
        "2. Ve a Paper Trading > API Keys\n"
        "3. Genera nuevas credenciales\n"
        "4. Usa el comando:\n"
        "   `/set_alpaca <API_KEY> <API_SECRET>`\n\n"
        
        "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "🎮 **MODOS DE OPERACIÓN**\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        
        "• 🔍 **Watcher**: Solo alertas (sin operaciones)\n"
        "• 👨‍✈️ **Copilot**: Propuestas con botones Aceptar/Rechazar\n"
        "• 🤖 **Pilot**: Trading 100% automático\n\n"
        
        "Cambia con: `/watcher`, `/copilot`, `/pilot`\n\n"
        
        "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "⚙️ **COMANDOS ESENCIALES**\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        
        "• `/start` - Menú principal\n"
        "• `/status` - Estado de tu sesión\n"
        "• `/wallet` - Ver tu cartera\n"
        "• `/config` - Panel de configuración\n"
        "• `/strategies` - Activar/Desactivar estrategias\n"
        "• `/help` - Lista completa de comandos\n\n"
        
        "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "🛡️ **SEGURIDAD**\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        
        "• Nunca compartas tus API Keys\n"
        "• Usa `/delete_keys` para borrar tu sesión\n"
        "• Las claves se almacenan encriptadas\n"
        "• El bot NO puede hacer retiros\n\n"
        
        "¿Listo? Usa `/set_binance` para empezar 🚀"
    )
    
    try:
        await message.answer(startup_text, parse_mode="Markdown", disable_web_page_preview=True)
    except:
        # Fallback without markdown
        await message.answer(startup_text.replace('*', '').replace('`', '').replace('_', '_'))


@router.message(Command("help"))
async def cmd_help(message: Message):
    """Command reference - DYNAMIC based on ROLE"""
    
    is_admin = is_authorized_admin(str(message.chat.id))
    
    # Base Help (For everyone)
    help_text = (
        "🤖 *ANTIGRAVITY BOT v4.0*\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        
        "📊 *INFO & MERCADO*\n"
        "• /start - Menú principal\n"
        "• /status - Estado personal\n"
        "• /wallet - Ver cartera\n"
        "• /analyze SYMBOL - Análisis IA\n"
        "• /cooldown - Ver/Setear cooldown\n\n"
        
        "💹 *TRADING MANUAL*\n"
        "• /long SYMBOL - Abrir LONG\n"
        "• /short SYMBOL - Abrir SHORT\n"
        "• /buy SYMBOL - Compra SPOT\n"
        "• /close SYMBOL - Cerrar posición\n"
        "• /closeall - Cerrar TODO\n"
        "• /sync - Sincronizar SL/TP\n"
        "• /cleanup - Limpiar órdenes\n\n"
        
        "🎮 *MODOS OPERATIVOS*\n"
        "• /pilot - Automático\n"
        "• /copilot - Asistido\n"
        "• /watcher - Solo alertas\n"
        "• /mode PRESET - Ronin/Guardian/Quantum\n\n"
        
        "⚙️ *CONFIGURACIÓN*\n"
        "• /config - Panel de ajustes\n"
        "• /strategies - Motor Dinámico\n"
        "• /set\\_leverage - Apalancamiento\n"
        "• /set\\_margin - Margen máximo\n"
        "• /set\\_binance - API Keys Binance\n"
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
        
        "📅 *PROGRAMACIÓN*\n"
        "• /schedule TEXTO - Programar tarea\n"
        "• /tasks - Ver tareas\n"
        "• /cancel ID - Cancelar tarea\n"
        "• /timezone ZONA - Zona horaria\n\n"
        
        "🛡️ *SEGURIDAD*\n"
        "• /risk - Gestión de riesgo\n"
        "• /resetpilot - Reset breaker\n"
    )
    
    # Admin Section (Only if admin)
    if is_admin:
        help_text += (
            "\n👑 *ADMINISTRACIÓN*\n"
            "• /subs - Listar usuarios\n"
            "• /addsub - Agregar suscriptor\n"
            "• /remsub - Eliminar usuario\n"
            "• /reset\\_assets - Limpiar assets\n"
            "• /debug - Diagnóstico Sistema\n"
        )

    help_text += (
        "\n📖 *DOCS*\n"
        "• /about - Sobre el bot\n"
        "• /strategy - Lógica Dinámica\n"
        "• /startup - Guía de inicio rápido\n"
        "• /cooldowns - Ver cooldowns activos"
    )
    
    try:
        # Split if too long (Telegram limit ~4096 chars, be safe at 3500)
        if len(help_text) > 3500:
            # Split at a natural point (after INFO section)
            split_point = help_text.find("💹 *TRADING")
            if split_point > 0:
                part1 = help_text[:split_point]
                part2 = help_text[split_point:]
                await message.answer(part1, parse_mode="Markdown")
                await message.answer(part2, parse_mode="Markdown")
            else:
                await message.answer(help_text, parse_mode="Markdown")
        else:
            await message.answer(help_text, parse_mode="Markdown")
    except Exception as e:
        print(f"⚠️ Help Command Error: {e}")
        # Fallback: Remove markdown and try again
        clean_text = help_text.replace('*', '').replace('`', '')
        try:
            await message.answer(clean_text)
        except Exception as e2:
            print(f"⚠️ Help Fallback Error: {e2}")
            await message.answer("❌ Error mostrando ayuda. Intenta /startup en su lugar.")
        


@router.message(Command("dashboard"))
async def cmd_dashboard(message: Message, edit_message: bool = False, **kwargs):
    """
    📊 TRADING DASHBOARD
    Unified view of Status + Wallet
    """
    session_manager = kwargs.get('session_manager')
    if not session_manager: 
        return
    
    session = session_manager.get_session(str(message.chat.id))
    if not session:
        text = "⚠️ Sin sesión activa. Usa /set_keys."
        if edit_message:
            try:
                await message.edit_text(text)
            except:
                await message.answer(text)
        else:
            await message.answer(text)
        return

    # Show loading indicator
    loading_text = "⏳ Cargando Dashboard..."
    try:
        if edit_message:
            await message.edit_text(loading_text)
            target_msg = message
        else:
            target_msg = await message.answer(loading_text)
    except Exception:
        target_msg = await message.answer(loading_text)
    
    try:
        # Fetch Data
        data = await session.get_dashboard_summary()
        wallet = data['wallet']
        pos = data['positions']
        cfg = data['config']
        
        # Mode Info
        mode = cfg.get('mode', 'WATCHER')
        mode_map = {'WATCHER': '👁️ Watcher', 'COPILOT': '🦾 Copilot', 'PILOT': '🤖 Pilot'}
        mode_display = mode_map.get(mode, mode)
        
        # Net Worth
        net_worth = wallet.get('total', 0.0)
        
        # PnL
        pnl = pos['total_pnl']
        pnl_icon = "🟢" if pnl >= 0 else "🔴"
        
        # Fear & Greed
        fg_text = get_fear_and_greed_index()
        
        # Build Message
        msg = (
            "📊 **TRADING DASHBOARD**\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            
            f"� **Net Worth:** `${net_worth:,.2f}`\n"
            f"📈 **PnL Abierto:** {pnl_icon} `${pnl:,.2f}`\n\n"
            
            "**💰 Balances**\n"
            f"• Binance Spot: `${wallet.get('spot_usdt', 0) + wallet.get('earn_usdt', 0):,.0f}`\n"
            f"• Binance Futures: `${wallet.get('futures_balance', 0):,.0f}`\n"
            f"• Alpaca: `${wallet.get('alpaca_equity', 0):,.0f}`\n\n"
            
            "**⚙️ Estado**\n"
            f"• Modo: {mode_display}\n"
            f"• Posiciones: `{pos['count']}` ({pos['longs']}L / {pos['shorts']}S)\n\n"
            
            "**🌡️ Mercado**\n"
            f"{fg_text}"
        )
        
        # Keyboard
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="🔄 Actualizar", callback_data="CMD|dashboard"),
                InlineKeyboardButton(text="⚙️ Config", callback_data="CMD|config")
            ],
            [
                InlineKeyboardButton(text="🔙 Menú Principal", callback_data="CMD|start")
            ]
        ])
        
        await target_msg.edit_text(msg, parse_mode="Markdown", reply_markup=kb)

    except Exception as e:
        await target_msg.edit_text(f"❌ Error: {e}")


# ALIASES
@router.message(Command("status"))
async def cmd_status(message: Message, **kwargs):
    await cmd_dashboard(message, **kwargs)

@router.message(Command("wallet"))
async def cmd_wallet(message: Message, **kwargs):
    await cmd_dashboard(message, **kwargs)



@router.message(Command("watcher"))
async def cmd_watcher(message: Message, **kwargs):
    """Switch to Watcher mode"""
    session_manager = kwargs.get('session_manager')
    if not session_manager:
        await message.answer("⚠️ Error interno.")
        return
        
    session = session_manager.get_session(str(message.chat.id))
    if not session:
        await message.answer("⚠️ Sin sesión activa. Usa /set_keys primero.")
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
        await message.answer("⚠️ Sin sesión activa. Usa /set_keys primero.")
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
        await message.answer("⚠️ Sin sesión activa. Usa /set_keys primero.")
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
        await message.answer("⚠️ Sin sesión activa. Usa /set_keys.")
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
@admin_only
async def cmd_debug(message: Message, **kwargs):
    """System diagnostics - Full Network Report (User-Specific)"""
    # Import locally to avoid circular deps if any
    from utils.diagnostics import run_diagnostics
    from functools import partial
    
    msg = await message.answer("⏳ Ejecutando diagnóstico de red y sistema...")
    
    try:
        # Get user's session credentials (if available)
        session_manager = kwargs.get('session_manager')
        session = session_manager.get_session(str(message.chat.id)) if session_manager else None
        
        user_api_key = session.api_key if session else None
        user_api_secret = session.api_secret if session else None
        
        # Run blocking diagnostics in thread pool with user's credentials
        loop = asyncio.get_running_loop()
        diag_func = partial(run_diagnostics, api_key=user_api_key, api_secret=user_api_secret)
        report = await loop.run_in_executor(None, diag_func)
        
        # Split report if too long (Telegram limit 4096)
        if len(report) > 4000:
            for i in range(0, len(report), 4000):
                await message.answer(report[i:i+4000], parse_mode="Markdown")
        else:
            await msg.edit_text(report, parse_mode="Markdown")
            
    except Exception as e:
        await msg.edit_text(f"❌ Error en diagnóstico: {e}")


@router.message(Command("migrate_security"))
@admin_only
async def cmd_migrate_security(message: Message, **kwargs):
    """Forces encryption of all database entries."""
    from utils.force_encrypt import force_encrypt_all
    
    msg = await message.answer("🔐 **Iniciando Migración de Seguridad...**\nLeyendo DB y re-encriptando todo...")
    
    try:
        # Run in executor to avoid blocking
        loop = asyncio.get_running_loop()
        success = await loop.run_in_executor(None, force_encrypt_all)
        
        if success:
            await msg.edit_text("✅ **Migración Completa**\nTodas las claves en la base de datos han sido encriptadas exitosamente con AES-256.")
        else:
            await msg.edit_text("❌ **Error en Migración**\nRevisa los logs del servidor.")
            
    except Exception as e:
        await msg.edit_text(f"❌ Error crítico: {e}")


# ============================================
# --- RESTORED COMMANDS FROM SYNC VERSION ---
# ============================================

@router.message(Command("mode"))
async def cmd_mode(message: Message, **kwargs):
    """Risk presets: /mode RONIN|GUARDIAN|QUANTUM"""
    session_manager = kwargs.get('session_manager')
    if not session_manager:
        await message.answer("⚠️ Session manager not available.")
        return
    
    chat_id = str(message.chat.id)
    session = session_manager.get_session(chat_id)
    
    if not session:
        await message.answer("⚠️ Sin sesión activa. Usa /set_binance.")
        return
    
    args = message.text.upper().split()
    if len(args) < 2:
        await message.answer("⚠️ Uso: `/mode <RONIN | GUARDIAN | QUANTUM>`", parse_mode='Markdown')
        return
    
    profile = args[1]
    
    if profile == 'RONIN':
        # Aggressive
        session.update_config('leverage', 20)
        session.update_config('stop_loss_pct', 0.015)
        session.update_config('atr_multiplier', 1.5)
        session.update_config('sentiment_threshold', -0.8)
        session_manager.save_sessions()
        await message.answer(
            "⚔️ **MODO RONIN ACTIVADO**\n"
            "- Apalancamiento: 20x\n"
            "- Stop Loss: Apretado (1.5 ATR)\n"
            "- Filtro IA: Laxo (-0.8)\n"
            "_Ojo: Alto Riesgo._",
            parse_mode='Markdown'
        )
    elif profile == 'GUARDIAN':
        # Conservative
        session.update_config('leverage', 3)
        session.update_config('stop_loss_pct', 0.03)
        session.update_config('atr_multiplier', 3.0)
        session.update_config('sentiment_threshold', -0.3)
        session_manager.save_sessions()
        await message.answer(
            "🛡️ **MODO GUARDIAN ACTIVADO**\n"
            "- Apalancamiento: 3x\n"
            "- Stop Loss: Amplio (3.0 ATR)\n"
            "- Filtro IA: Estricto (-0.3)\n"
            "_Prioridad: Protección de Capital._",
            parse_mode='Markdown'
        )
    elif profile == 'QUANTUM':
        # Balanced
        session.update_config('leverage', 5)
        session.update_config('stop_loss_pct', 0.02)
        session.update_config('atr_multiplier', 2.0)
        session.update_config('sentiment_threshold', -0.6)
        session_manager.save_sessions()
        await message.answer(
            "🌌 **MODO QUANTUM ACTIVADO**\n"
            "- Apalancamiento: 5x\n"
            "- Stop Loss: Estándar (2.0 ATR)\n"
            "- Filtro IA: Balanceado (-0.6)\n"
            "_Equilibrio Matemático._",
            parse_mode='Markdown'
        )
    else:
        await message.answer("⚠️ Perfil desconocido. Usa: RONIN, GUARDIAN, QUANTUM.")


@router.message(Command("resetpilot"))
async def cmd_resetpilot(message: Message, **kwargs):
    """Reset circuit breaker"""
    session_manager = kwargs.get('session_manager')
    if not session_manager:
        await message.answer("⚠️ Session manager not available.")
        return
    
    chat_id = str(message.chat.id)
    session = session_manager.get_session(chat_id)
    
    if not session:
        await message.answer("⚠️ Sin sesión activa.")
        return
    
    session.reset_circuit_breaker()
    await message.answer(
        "🔄 **Circuit Breaker Reseteado**\n"
        "El contador de pérdidas consecutivas se ha reiniciado.\n"
        "Ahora puedes volver a activar modo PILOT con `/pilot`.",
        parse_mode='Markdown'
    )


@router.message(Command("risk"))
async def cmd_risk(message: Message, **kwargs):
    """Display current risk management settings"""
    session_manager = kwargs.get('session_manager')
    if not session_manager:
        await message.answer("⚠️ Session manager not available.")
        return
    
    chat_id = str(message.chat.id)
    session = session_manager.get_session(chat_id)
    
    if not session:
        await message.answer("⚠️ Sin sesión activa. Configura primero con `/set_binance`.", parse_mode="Markdown")
        return
    
    # Extract risk parameters from session config
    leverage = session.config.get('leverage', 5)
    margin_pct = session.config.get('max_capital_pct', 0.10) * 100
    sl_pct = session.config.get('stop_loss_pct', 0.02) * 100
    atr_mult = session.config.get('atr_multiplier', 2.0)
    
    # Calculate losses and breaker status
    losses = getattr(session, 'consecutive_losses', 0)
    max_losses = getattr(session, 'max_consecutive_losses', 3)
    breaker_status = "🔴 ACTIVADO" if losses >= max_losses else f"🟢 OK ({losses}/{max_losses})"
    
    await message.answer(
        "🛡️ **GESTIÓN DE RIESGO**\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        f"⚖️ Apalancamiento: `{leverage}x`\n"
        f"💰 Margen por Op: `{margin_pct:.0f}%` (Max Cap)\n"
        f"📉 Stop Loss Base: `{sl_pct:.1f}%`\n"
        f"📏 Multiplicador ATR: `{atr_mult}x`\n"
        f"🧠 **Risk Model**: Dynamic 1% / trade\n\n"
        f"🔌 Circuit Breaker: {breaker_status}\n\n"
        "_Usa /config para modificar estos valores._",
        parse_mode='Markdown'
    )


@router.message(Command("sniper"))
async def cmd_sniper(message: Message, **kwargs):
    """Scan for instant trading opportunities"""
    from utils.ai_analyst import QuantumAnalyst
    from data.fetcher import get_market_data
    from strategies.engine import StrategyEngine
    
    session_manager = kwargs.get('session_manager')
    if not session_manager:
        await message.answer("⚠️ Session manager not available.")
        return
    
    chat_id = str(message.chat.id)
    session = session_manager.get_session(chat_id)
    
    msg = await message.answer("🎯 **SNIPER MODE ACTIVADO**\n👁️ Escaneando 5 activos principales...")
    
    targets = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'BNBUSDT', 'DOGEUSDT']
    best_candidate = None
    best_score = -999
    
    try:
        analyst = QuantumAnalyst()
        
        for asset in targets:
            # 1. Tech Analysis
            df = get_market_data(asset, timeframe='15m', limit=100)
            if df.empty:
                continue
            
            engine = StrategyEngine(df)
            res = engine.analyze()
            
            # Score Technicals
            tech_score = 0
            sig = res.get('signal_futures', 'NEUTRAL')
            if sig == 'BUY':
                tech_score = 1
            elif sig == 'SHORT':
                tech_score = -1
            else:
                continue
            
            # 2. AI Confirmation
            if analyst.client:
                sentiment = analyst.check_market_sentiment(asset)
                sent_score = sentiment.get('score', 0)
                
                # Congruence Check
                total_score = 0
                if sig == 'BUY' and sent_score > 0.2:
                    total_score = 1 + sent_score
                elif sig == 'SHORT' and sent_score < -0.2:
                    total_score = 1 + abs(sent_score)
                
                if total_score > best_score:
                    best_score = total_score
                    best_candidate = {
                        'asset': asset,
                        'signal': sig,
                        'price': res.get('metrics', {}).get('close', 0),
                        'reason_tech': res.get('reason_futures', 'N/A'),
                        'reason_ai': sentiment.get('reason', 'N/A'),
                        'vol_risk': sentiment.get('volatility_risk', 'LOW')
                    }
        
        if best_candidate and best_score > 0:
            c = best_candidate
            icon = "🚀" if c['signal'] == 'BUY' else "🩸"
            
            result = (
                f"🎯 **BLANCO ENCONTRADO: {c['asset']}**\n"
                f"{icon} Señal: **{c['signal']}** @ ${c['price']:,.2f}\n\n"
                f"📊 **Técnico:** {c['reason_tech']}\n"
                f"🧠 **AI:** {c['reason_ai']}\n"
                f"⚠️ Riesgo: {c['vol_risk']}\n\n"
                f"👇 Ejecutar con: `/{c['signal'].lower()} {c['asset']}`"
            )
            await msg.edit_text(result, parse_mode='Markdown')
        else:
            await msg.edit_text("🤷‍♂️ **Sin blancos claros.**\nEl mercado está mixto. Recomiendo esperar.")
    
    except Exception as e:
        await msg.edit_text(f"❌ Error Sniper: {e}")


@router.message(Command("news"))
async def cmd_news(message: Message, **kwargs):
    """AI market briefing"""
    from utils.ai_analyst import QuantumAnalyst
    
    msg = await message.answer("🗞️ *Leyendo las noticias...* (Consultando via AI)", parse_mode='Markdown')
    
    try:
        analyst = QuantumAnalyst()
        if not analyst.client:
            await msg.edit_text("⚠️ IA no disponible. Configura OPENAI_API_KEY.")
            return
        
        report = analyst.generate_market_briefing()
        await msg.edit_text(f"📰 **BOLETÍN DE MERCADO**\n\n{report}", parse_mode='Markdown')
    except Exception as e:
        await msg.edit_text(f"❌ Error: {e}")


@router.message(Command("sentiment"))
async def cmd_sentiment(message: Message, **kwargs):
    """Global sentiment analysis"""
    from utils.ai_analyst import QuantumAnalyst
    
    msg = await message.answer("🧠 *Escaneando Redes y Noticias...*", parse_mode='Markdown')
    
    try:
        analyst = QuantumAnalyst()
        if not analyst.client:
            await msg.edit_text("⚠️ IA no disponible. Configura OPENAI_API_KEY.")
            return
        
        res_btc = analyst.check_market_sentiment('BTCUSDT')
        res_macro = analyst.check_market_sentiment('^GSPC')  # S&P 500
        
        score_btc = res_btc.get('score', 0)
        score_macro = res_macro.get('score', 0)
        
        def interpret(s):
            if s > 0.3: return "🟢 BULLISH"
            if s < -0.3: return "🔴 BEARISH"
            return "⚪ NEUTRAL"
        
        result = (
            "🧠 **SENTIMIENTO GLOBAL DEL MERCADO**\n"
            "-----------------------------------\n"
            f"💎 **Cripto (BTC):** {score_btc:.2f} | {interpret(score_btc)}\n"
            f"_{res_btc.get('reason', 'N/A')}_\n\n"
            f"🌍 **Macro (S&P500):** {score_macro:.2f} | {interpret(score_macro)}\n"
            f"_{res_macro.get('reason', 'N/A')}_\n\n"
            f"⚠️ **Riesgo Volatilidad:** `{res_macro.get('volatility_risk', 'LOW')}`"
        )
        await msg.edit_text(result, parse_mode='Markdown')
    
    except Exception as e:
        await msg.edit_text(f"❌ Error: {e}")


@router.message(Command("fomc"))
async def cmd_fomc(message: Message, **kwargs):
    """Federal Reserve (FED) analysis"""
    from utils.ai_analyst import QuantumAnalyst
    
    session_manager = kwargs.get('session_manager')
    chat_id = str(message.chat.id)
    session = session_manager.get_session(chat_id) if session_manager else None
    
    p_key = session.config.get('personality', 'Standard') if session else 'Standard'
    
    msg = await message.answer("🏦 *Analizando situación de la FED...* (Tasas, Bonos, Powell)", parse_mode='Markdown')
    
    try:
        analyst = QuantumAnalyst()
        if not analyst.client:
            await msg.edit_text("⚠️ IA no disponible. Configura OPENAI_API_KEY.")
            return
        
        report = analyst.analyze_fomc(personality=p_key)
        await msg.edit_text(f"🏦 **ANÁLISIS FOMC (FED)**\n\n{report}", parse_mode='Markdown')
    except Exception as e:
        await msg.edit_text(f"❌ Error: {e}")


@router.message(Command("analyze"))
async def cmd_analyze(message: Message, **kwargs):
    """Per-asset AI analysis: /analyze BTC - Uses active personality"""
    from utils.ai_analyst import QuantumAnalyst
    from data.fetcher import get_market_data
    from utils.personalities import PersonalityManager
    
    # Get user's active personality from session
    session_manager = kwargs.get('session_manager')
    chat_id = str(message.chat.id)
    session = session_manager.get_session(chat_id) if session_manager else None
    
    # Get personality key and name
    p_key = session.config.get('personality', 'STANDARD_ES') if session else 'STANDARD_ES'
    pm = PersonalityManager()
    p_name = pm.get_profile(p_key).get('NAME', 'Estándar')
    
    args = message.text.split()
    if len(args) < 2:
        await message.answer("⚠️ Uso: `/analyze <SYMBOL>`\nEjemplo: `/analyze BTC`", parse_mode='Markdown')
        return
    
    symbol = args[1].upper()
    if 'USDT' not in symbol:
        symbol = f"{symbol}USDT"
    
    msg = await message.answer(f"🔍 Analizando {symbol} con personalidad *{p_name}*...", parse_mode='Markdown')
    
    try:
        # Get data with more indicators
        df = get_market_data(symbol, timeframe='1h', limit=50)
        if df.empty:
            await msg.edit_text(f"❌ No data for {symbol}")
            return
        
        current_price = float(df['close'].iloc[-1])
        
        # Calculate RSI from close prices using the utility function
        from utils.indicators import calculate_rsi
        closes = df['close'].tolist()
        rsi = calculate_rsi(closes, period=14)
        
        # Calculate Bollinger Bands (20 period, 2 std dev)
        close_series = df['close'].astype(float)
        bb_middle = close_series.rolling(window=20).mean()
        bb_std = close_series.rolling(window=20).std()
        bb_upper = float(bb_middle.iloc[-1] + 2 * bb_std.iloc[-1]) if len(df) >= 20 else current_price * 1.02
        bb_lower = float(bb_middle.iloc[-1] - 2 * bb_std.iloc[-1]) if len(df) >= 20 else current_price * 0.98
        
        # Volume metrics
        volume = float(df['volume'].iloc[-1]) if 'volume' in df.columns else 0
        avg_vol = float(df['volume'].mean()) if 'volume' in df.columns else 1
        
        analyst = QuantumAnalyst()
        if not analyst.client:
            await msg.edit_text("⚠️ IA no disponible.")
            return
        
        indicators = {
            'price': current_price,
            'rsi': rsi,
            'bb_upper': bb_upper,
            'bb_lower': bb_lower,
            'bb_width': bb_upper - bb_lower,
            'volume_ratio': volume / avg_vol if avg_vol > 0 else 1
        }
        
        # Pass personality key for character-based analysis
        analysis = analyst.analyze_signal(symbol, '1h', indicators, personality=p_key)
        
        await msg.edit_text(
            f"🔬 **ANÁLISIS: {symbol}**\n\n"
            f"💵 Precio: ${current_price:,.2f}\n"
            f"📊 RSI: {rsi:.1f}\n"
            f"🎭 Personalidad: *{p_name}*\n\n"
            f"{analysis}",
            parse_mode='Markdown'
        )
    except Exception as e:
        await msg.edit_text(f"❌ Error: {e}")


# =================================================================
# /cooldown - Configure Signal Alert Cooldown
# =================================================================
@router.message(Command("cooldown"))
async def cmd_cooldown(message: Message, **kwargs):
    """Configure or view signal alert cooldown using DynamicCooldownManager."""
    from bot_async import cooldown_manager
    
    args = message.text.split()
    
    if len(args) < 2:
        # Show current default cooldown
        current = cooldown_manager.default_cooldown // 60
        await message.reply(
            f"⏱️ **COOLDOWN ACTUAL**\n\n"
            f"Intervalo anti-spam: `{current}` minutos\n\n"
            f"Uso: `/cooldown <minutos>`\n"
            f"Ejemplo: `/cooldown 10`",
            parse_mode="Markdown"
        )
        return
    
    try:
        minutes = int(args[1])
        if minutes < 1 or minutes > 60:
            await message.reply("❌ El valor debe estar entre 1 y 60 minutos.")
            return
        
        # Update DynamicCooldownManager
        cooldown_manager.default_cooldown = minutes * 60
        
        # Clear existing cooldowns to apply immediately
        cooldown_manager.cooldowns.clear()
        cooldown_manager.frequency_tracker.clear()
        
        await message.reply(
            f"✅ **COOLDOWN ACTUALIZADO**\n\n"
            f"Nuevo intervalo base: `{minutes}` minutos\n\n"
            f"_Nota: El sistema ajusta dinámicamente según frecuencia y volatilidad._",
            parse_mode="Markdown"
        )
    except ValueError:
        await message.reply("❌ Valor inválido. Usa: `/cooldown 10`", parse_mode="Markdown")


@router.message(Command("cooldowns"))
async def cmd_cooldowns(message: Message, **kwargs):
    """Show all active symbol cooldowns."""
    from bot_async import cooldown_manager
    
    # Get all symbols with active cooldowns
    active = []
    for symbol, last_time in cooldown_manager._last_alert.items():
        status = cooldown_manager.get_status(symbol)
        if status['remaining_seconds'] > 0:
            active.append(status)
    
    if not active:
        await message.reply(
            "⏱️ **COOLDOWNS ACTIVOS**\n\n"
            "No hay cooldowns activos actualmente.\n"
            f"Intervalo base: `{cooldown_manager.default_cooldown // 60}` minutos.",
            parse_mode="Markdown"
        )
        return
    
    # Build report
    lines = ["⏱️ **COOLDOWNS ACTIVOS**\n"]
    for s in active[:15]:  # Limit to 15
        remaining_m = int(s['remaining_seconds'] // 60)
        remaining_s = int(s['remaining_seconds'] % 60)
        lines.append(
            f"• `{s['symbol']}`: {remaining_m}m {remaining_s}s restante "
            f"(freq: {s['signals_per_hour']:.1f}/hr)"
        )
    
    lines.append(f"\n_Base: {cooldown_manager.default_cooldown // 60} min_")
    await message.reply("\n".join(lines), parse_mode="Markdown")


@router.message(Command("reset_assets"))
async def cmd_reset_assets(message: Message, **kwargs):
    """Clear all disabled assets (Admin only)."""
    from antigravity_quantum.config import DISABLED_ASSETS, ENABLED_STRATEGIES
    from config import GROUP_CONFIG
    from utils.db import save_bot_state
    import antigravity_quantum.config as aq_config
    
    count = len(DISABLED_ASSETS)
    DISABLED_ASSETS.clear()
    
    # Persist to database
    save_bot_state(ENABLED_STRATEGIES, GROUP_CONFIG, [], aq_config.AI_FILTER_ENABLED)
    
    await message.reply(
        f"✅ **Assets Reset**\n"
        f"Se habilitaron {count} activos previamente deshabilitados.\n"
        f"Total disabled ahora: 0",
        parse_mode="Markdown"
    )


# =================================================================
# MANUAL TRADING COMMANDS
# =================================================================

@router.message(Command("long"))
async def cmd_long(message: Message, **kwargs):
    """Manually trigger a LONG position (Futures) with Dynamic ATR."""
    session_manager = kwargs.get('session_manager')
    if not session_manager: return
    
    session = session_manager.get_session(str(message.chat.id))
    if not session:
        await message.reply("⚠️ Sin sesión activa.")
        return

    args = message.text.split()
    if len(args) < 2:
        await message.reply("⚠️ Uso: `/long <SYMBOL>` (ej: `/long BTC`)", parse_mode="Markdown")
        return
    
    # Smart Symbol Resolution
    from config import resolve_symbol
    raw_symbol = args[1]
    symbol = resolve_symbol(raw_symbol)
    
    # Calculate ATR
    msg_wait = await message.reply(f"⏳ Analizando volatilidad (ATR) para `{symbol}`...", parse_mode="Markdown")
    
    try:
        from data.fetcher import get_market_data, calculate_atr
        
        # Fetch 1h candles
        df = get_market_data(symbol, timeframe='1h', limit=50)
        atr_value = calculate_atr(df, period=14)
        
        atr_msg = f" (ATR: {atr_value:.4f})" if atr_value > 0 else " (ATR: N/A, usando default)"
        
        await msg_wait.edit_text(f"🚀 Iniciando **LONG FUTURES** en `{symbol}`{atr_msg}...", parse_mode="Markdown")
        
        # Execute with ATR
        success, res_msg = await session.execute_long_position(symbol, atr=atr_value)
        await message.reply(res_msg, parse_mode="Markdown")
        
    except Exception as e:
        await msg_wait.edit_text(f"❌ Error iniciando operación: {e}")


@router.message(Command("buy"))
async def cmd_buy_spot(message: Message, **kwargs):
    """Manually trigger a SPOT BUY."""
    session_manager = kwargs.get('session_manager')
    if not session_manager: return
    
    session = session_manager.get_session(str(message.chat.id))
    if not session:
        await message.reply("⚠️ Sin sesión activa.")
        return

    args = message.text.split()
    if len(args) < 2:
        await message.reply("⚠️ Uso: `/buy <SYMBOL>` (ej: `/buy XRP`)", parse_mode="Markdown")
        return
    
    # Smart Symbol Resolution
    from config import resolve_symbol
    raw_symbol = args[1]
    symbol = resolve_symbol(raw_symbol)
    
    msg_wait = await message.reply(f"⏳ Ejecutando Compra SPOT en `{symbol}`...", parse_mode="Markdown")
    
    try:
        # Verify execute_spot_buy exists
        if not hasattr(session, 'execute_spot_buy'):
             await msg_wait.edit_text("❌ Error: Función Spot no implementada en Session.")
             return

        success, res_msg = await session.execute_spot_buy(symbol)
        
        if success:
             await msg_wait.edit_text(f"✅ *COMPRA SPOT EXITOSA*\n{res_msg}", parse_mode="Markdown")
        else:
             await msg_wait.edit_text(f"❌ Falló Compra: {res_msg}")
             
    except Exception as e:
        await msg_wait.edit_text(f"❌ Error crítico: {e}")


@router.message(Command("short", "sell"))
async def cmd_short(message: Message, **kwargs):
    """Manually trigger a SHORT position with Dynamic ATR."""
    session_manager = kwargs.get('session_manager')
    if not session_manager: return
    
    session = session_manager.get_session(str(message.chat.id))
    if not session:
        await message.reply("⚠️ Sin sesión activa.")
        return

    args = message.text.split()
    if len(args) < 2:
        await message.reply("⚠️ Uso: `/short <SYMBOL>` (ej: `/short ETH`)", parse_mode="Markdown")
        return
    
    # Smart Symbol Resolution
    from config import resolve_symbol
    raw_symbol = args[1]
    symbol = resolve_symbol(raw_symbol)
    
    # Calculate ATR
    msg_wait = await message.reply(f"⏳ Analizando volatilidad (ATR) para `{symbol}`...", parse_mode="Markdown")
    
    try:
        from data.fetcher import get_market_data, calculate_atr
        
        # Fetch 1h candles
        df = get_market_data(symbol, timeframe='1h', limit=50)
        atr_value = calculate_atr(df, period=14)
        
        atr_msg = f" (ATR: {atr_value:.4f})" if atr_value > 0 else " (ATR: N/A, usando default)"
        
        await msg_wait.edit_text(f"🐻 Iniciando **SHORT** en `{symbol}`{atr_msg}...", parse_mode="Markdown")
        
        # Execute with ATR
        success, res_msg = await session.execute_short_position(symbol, atr=atr_value)
        await message.reply(res_msg, parse_mode="Markdown")
        
    except Exception as e:
        await msg_wait.edit_text(f"❌ Error iniciando operación: {e}")


@router.message(Command("sync"))
@router.message(Command("syncorders"))  # Alias for backwards compatibility
async def cmd_sync(message: Message, **kwargs):
    """
    Smart Sync - Unified order management:
    1. Applies breakeven SL to positions with ROI >= 10%
    2. Applies standard SL/TP to remaining positions
    """
    session_manager = kwargs.get('session_manager')
    if not session_manager:
        await message.answer("⚠️ Session manager not available.")
        return
        
    session = session_manager.get_session(str(message.chat.id))
    if not session:
        await message.answer("⚠️ Sin sesión activa.")
        return
        
    msg = await message.answer(
        "🔄 **Sincronización Inteligente...**\n"
        "• Aplicando breakeven a posiciones rentables (ROI ≥ 10%)\n"
        "• Sincronizando SL/TP en posiciones restantes",
        parse_mode="Markdown"
    )
    
    # Step 1: Apply breakeven to profitable positions
    breakeven_report = await session.smart_breakeven_check(breakeven_roi_threshold=0.10)
    
    # Step 2: Apply standard SL/TP sync to all positions
    sync_report = await session.execute_refresh_all_orders()
    
    # Combine reports
    final_report = (
        "📊 **SINCRONIZACIÓN COMPLETADA**\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "🛡️ **Breakeven (ROI ≥ 10%):**\n"
        f"{breakeven_report}\n\n"
        "🔄 **SL/TP Estándar:**\n"
        f"{sync_report}"
    )
    
    await msg.edit_text(final_report, parse_mode="Markdown")

@router.message(Command("about"))
async def cmd_about(message: Message, **kwargs):
    """Show bot information with personality-aware message."""
    session_manager = kwargs.get('session_manager')
    chat_id = str(message.chat.id)
    session = session_manager.get_session(chat_id) if session_manager else None
    
    p_key = session.config.get('personality', 'STANDARD_ES') if session else 'STANDARD_ES'
    
    # Import personality manager from bot_async
    from bot_async import personality_manager
    msg = personality_manager.get_message(p_key, 'ABOUT_MSG')
    
    await message.answer(msg, parse_mode="Markdown")


@router.message(Command("strategy"))
async def cmd_strategy(message: Message, **kwargs):
    """Educational documentation about all trading strategies."""
    
    strategy_docs = (
        "📚 *ESTRATEGIAS DE TRADING*\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        
        "📈 *BTC TREND FOLLOWING*\n"
        "Sigue la tendencia macro de Bitcoin usando EMA200.\n"
        "• Señal LONG: Precio cruza EMA200 hacia arriba\n"
        "• Señal SHORT: Precio cruza EMA200 hacia abajo\n"
        "• Timeframe: 4H / Daily\n\n"
        
        "🦢 *BLACK SWAN (Defensa)*\n"
        "Protección contra crashs súbitos del mercado.\n"
        "• Detecta caídas >5% en ventanas cortas\n"
        "• Cierra posiciones LONG automáticamente\n"
        "• Actúa como circuit breaker\n\n"
        
        "🦈 *SHARK MODE (Ataque)*\n"
        "Estrategia ofensiva durante crashs.\n"
        "• Se activa cuando Black Swan detecta crash\n"
        "• Abre posiciones SHORT para capitalizar caídas\n"
        "• Alto riesgo / Alta recompensa\n\n"
        
        "⚡ *SCALPING*\n"
        "Operaciones rápidas en timeframes cortos.\n"
        "• RSI + Bollinger Bands\n"
        "• Entradas en sobreventa/sobrecompra\n"
        "• Timeframe: 1m-15m\n\n"
        
        "🕸️ *GRID TRADING*\n"
        "Trading en mercados laterales.\n"
        "• Define rangos de precio\n"
        "• Compra bajo, vende alto repetidamente\n"
        "• Ideal para consolidación\n\n"
        
        "📉 *MEAN REVERSION*\n"
        "Reversión a la media estadística.\n"
        "• Detecta desviaciones extremas\n"
        "• Apuesta por retorno al promedio\n"
        "• Usa Z-score y bandas de Bollinger\n\n"
        
        "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "💡 Usa `/strategies` para activar o desactivar."
    )
    
    await message.answer(strategy_docs, parse_mode="Markdown")



@router.message(Command("price"))
async def cmd_price(message: Message, **kwargs):
    """Market Scan (Price + 24h% + RSI + Sentiment)"""
    try:
        loading = await message.answer("🔍 _Analizando mercado..._", parse_mode="Markdown")
        
        # 1. Fear & Greed
        fng = get_fear_and_greed_index()
        
        # 2. Build dynamic target lists
        from config import ASSET_GROUPS, GROUP_CONFIG, TICKER_MAP
        from antigravity_quantum.config import DISABLED_ASSETS
        from utils.indicators import calculate_rsi
        import numpy as np
        
        crypto_targets = []
        stock_targets = []
        commodity_targets = []
        
        # Filter Logic (Same as before)
        if GROUP_CONFIG.get('CRYPTO', False):
            for asset in ASSET_GROUPS.get('CRYPTO', []):
                if asset.endswith('USDT') and asset not in DISABLED_ASSETS:
                    clean_asset = ''.join(c for c in asset if c.isalnum())
                    if clean_asset: crypto_targets.append(clean_asset)
        
        if GROUP_CONFIG.get('STOCKS', False):
            for asset in ASSET_GROUPS.get('STOCKS', []):
                if asset not in DISABLED_ASSETS: stock_targets.append(asset)
        
        if GROUP_CONFIG.get('COMMODITY', False):
            for asset in ASSET_GROUPS.get('COMMODITY', []):
                if asset not in DISABLED_ASSETS: commodity_targets.append(asset)
        
        # --- 3. FETCH & PROCESS CRYPTO (Binance) ---
        crypto_str = ""
        for symbol in crypto_targets[:6]:  # Limit 6
            try:
                # A. Get Price & 24h Change
                ticker_url = f"https://fapi.binance.com/fapi/v1/ticker/24hr?symbol={symbol}"
                # B. Get Klines for RSI (4h interval, 20 candles)
                klines_url = f"https://fapi.binance.com/fapi/v1/klines?symbol={symbol}&interval=4h&limit=20"
                
                # Fetch
                t_resp = requests.get(ticker_url, timeout=2).json()
                k_resp = requests.get(klines_url, timeout=2).json()
                
                if 'lastPrice' in t_resp:
                    # Data Extraction
                    price = float(t_resp['lastPrice'])
                    pct_change = float(t_resp['priceChangePercent'])
                    
                    # RSI Calc
                    closes = [float(k[4]) for k in k_resp] # Index 4 is Close
                    rsi = calculate_rsi(closes)
                    
                    # Indicators
                    sym = symbol.replace('USDT', '').replace('1000', '')
                    
                    # Logic: Bull/Bear/Nuetral
                    trend_icon = "🐂" if pct_change > 0 else "🐻"
                    pct_str = f"{'+' if pct_change > 0 else ''}{pct_change:.1f}%"
                    
                    # RSI Status
                    rsi_status = ""
                    if rsi > 70: rsi_status = "🔥 (OB)" # Overbought
                    elif rsi < 30: rsi_status = "🧊 (OS)" # Oversold
                    
                    crypto_str += f"• *{sym}:* `${price:,.2f}` {trend_icon} `{pct_str}` | `RSI {int(rsi)}` {rsi_status}\n"
            except Exception as e:
                print(f"Error fetching {symbol}: {e}")
                continue

        # --- 4. FETCH & PROCESS STOCKS/COMMODITIES (Yahoo) ---
        stocks_str = ""
        commodities_str = ""
        yf_symbols = stock_targets[:4] + commodity_targets[:3]
        
        if yf_symbols:
            headers = {'User-Agent': 'Mozilla/5.0'}
            for sym in yf_symbols:
                try:
                    # Fetch History (1 month daily to calc RSI)
                    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{sym}?interval=1d&range=1mo"
                    resp = requests.get(url, headers=headers, timeout=3)
                    data = resp.json()
                    
                    result = data.get('chart', {}).get('result', [{}])[0]
                    meta = result.get('meta', {})
                    indicators = result.get('indicators', {}).get('quote', [{}])[0]
                    
                    price = meta.get('regularMarketPrice')
                    prev_close = meta.get('chartPreviousClose')
                    
                    if price and prev_close:
                        # Calcs
                        pct_change = ((price - prev_close) / prev_close) * 100
                        closes = indicators.get('close', [])
                        # Filter None values
                        clean_closes = [c for c in closes if c is not None]
                        rsi = calculate_rsi(clean_closes)
                        
                        name = TICKER_MAP.get(sym, sym)
                        
                        # Formatting
                        trend_icon = "🐂" if pct_change > 0 else "🐻"
                        pct_str = f"{'+' if pct_change > 0 else ''}{pct_change:.1f}%"
                        
                        rsi_status = ""
                        if rsi > 70: rsi_status = "🔥"
                        elif rsi < 30: rsi_status = "🧊"
                        
                        line = f"• *{name}:* `${price:,.2f}` {trend_icon} `{pct_str}` | `RSI {int(rsi)}` {rsi_status}\n"
                        
                        if sym in stock_targets: stocks_str += line
                        elif sym in commodity_targets: commodities_str += line
                except:
                    continue

        # --- BUILD MESSAGE ---
        msg = (
            "📡 **MARKET INTEL (Advanced)**\n"
            "━━━━━━━━━━━━━━━━\n"
            f"🧠 **Sentimiento:** {fng}\n\n"
        )
        
        if crypto_str: msg += f"💎 **Crypto (4h RSI):**\n{crypto_str}\n"
        if stocks_str: msg += f"📈 **Stocks (Daily):**\n{stocks_str}\n"
        if commodities_str: msg += f"🏆 **Commodities:**\n{commodities_str}\n"
        
        if not (crypto_str or stocks_str or commodities_str):
            msg += "📭 Sin datos disponibles.\n"
            
        msg += (
            "━━━━━━━━━━━━━━━━\n"
            "🐂 Bull | 🐻 Bear | 🔥 Overbought | 🧊 Oversold"
        )
        
        await loading.edit_text(msg, parse_mode="Markdown")
        
    except Exception as e:
        await message.answer(f"❌ Error en Price: {e}")


# =================================================================
# SCHEDULER COMMANDS - Time & Task Management
# =================================================================

@router.message(Command("timezone"))
async def cmd_timezone(message: Message, **kwargs):
    """View or set user timezone: /timezone [ZONE]"""
    from utils.timezone_manager import (
        get_user_timezone, set_user_timezone, resolve_timezone,
        get_current_time_str, TIMEZONE_ALIASES
    )
    
    user_id = message.from_user.id
    args = message.text.split(maxsplit=1)
    
    if len(args) < 2:
        # Display current timezone
        current_tz = get_user_timezone(user_id)
        current_time = get_current_time_str(user_id, "%Y-%m-%d %H:%M:%S %Z")
        
        aliases = ", ".join(TIMEZONE_ALIASES.keys())
        
        await message.answer(
            f"🌍 **Tu Zona Horaria**\n"
            f"━━━━━━━━━━━━━━━━━━\n\n"
            f"📍 Zona: `{current_tz}`\n"
            f"🕐 Hora actual: `{current_time}`\n\n"
            f"**Cambiar:** `/timezone <ZONA>`\n"
            f"**Alias válidos:** `{aliases}`\n"
            f"**Ejemplos:** `America/New_York`, `Europe/Madrid`, `Asia/Tokyo`",
            parse_mode="Markdown"
        )
        return
    
    # Set new timezone
    tz_input = args[1].strip()
    resolved = resolve_timezone(tz_input)
    success, msg_text = set_user_timezone(user_id, resolved)
    
    if success:
        current_time = get_current_time_str(user_id, "%Y-%m-%d %H:%M:%S %Z")
        await message.answer(
            f"{msg_text}\n🕐 Hora actual: `{current_time}`",
            parse_mode="Markdown"
        )
    else:
        await message.answer(msg_text, parse_mode="Markdown")


@router.message(Command("schedule"))
async def cmd_schedule(message: Message, **kwargs):
    """
    Create a scheduled task using natural language.
    Example: /schedule analyze BTC every day at 9am
    """
    from utils.task_scheduler import get_scheduler
    from utils.timezone_manager import get_user_timezone, get_current_time_str
    
    user_id = message.from_user.id
    args = message.text.split(maxsplit=1)
    
    if len(args) < 2:
        await message.answer(
            "📅 **Programar Tarea**\n"
            "━━━━━━━━━━━━━━━━━━\n\n"
            "**Uso:** `/schedule <descripción en lenguaje natural>`\n\n"
            "**Ejemplos:**\n"
            "• `/schedule analyze BTC every day at 9am`\n"
            "• `/schedule news every Monday at 8:00`\n"
            "• `/schedule sniper in 30 minutes`\n"
            "• `/schedule dashboard every 4 hours`\n\n"
            "**Acciones disponibles:**\n"
            "`analyze`, `sniper`, `news`, `sentiment`, `fomc`, `dashboard`",
            parse_mode="Markdown"
        )
        return
    
    task_description = args[1]
    msg = await message.answer("⏳ Procesando solicitud con IA...")
    
    try:
        scheduler = get_scheduler()
        user_tz = get_user_timezone(user_id)
        
        # Parse with LLM
        parsed = await scheduler.parse_task_with_llm(task_description, user_id, user_tz)
        
        if parsed.get("error"):
            await msg.edit_text(f"❌ {parsed['error']}", parse_mode="Markdown")
            return
        
        # Schedule the task
        success, result_msg, task_id = await scheduler.schedule_task(
            user_id=user_id,
            action=parsed["action"],
            params=parsed.get("params", {}),
            schedule=parsed["schedule"],
            description=parsed.get("description", task_description)
        )
        
        await msg.edit_text(result_msg, parse_mode="Markdown")
        
    except Exception as e:
        await msg.edit_text(f"❌ Error: {e}", parse_mode="Markdown")


@router.message(Command("tasks"))
async def cmd_tasks(message: Message, **kwargs):
    """List all scheduled tasks for the user."""
    from utils.task_scheduler import get_scheduler
    from utils.timezone_manager import convert_from_utc, get_user_timezone
    from datetime import datetime
    
    user_id = message.from_user.id
    scheduler = get_scheduler()
    tasks = scheduler.list_tasks(user_id)
    
    if not tasks:
        await message.answer(
            "📋 **Tareas Programadas**\n"
            "━━━━━━━━━━━━━━━━━━\n\n"
            "No tienes tareas programadas.\n\n"
            "Usa `/schedule <descripción>` para crear una.",
            parse_mode="Markdown"
        )
        return
    
    user_tz = get_user_timezone(user_id)
    
    msg = "📋 **Tareas Programadas**\n━━━━━━━━━━━━━━━━━━\n\n"
    
    for task in tasks:
        task_id = task.get('id')
        action = task.get('action', 'N/A')
        description = task.get('description', 'Sin descripción')
        schedule_type = task.get('schedule_type', '')
        schedule_value = task.get('schedule_value', '')
        next_run = task.get('next_run')
        
        # Format next run time
        next_run_str = "N/A"
        if next_run:
            try:
                if isinstance(next_run, str):
                    next_run = datetime.fromisoformat(next_run.replace('Z', '+00:00'))
                next_run_str = next_run.strftime("%m/%d %H:%M UTC")
            except:
                next_run_str = str(next_run)[:16]
        
        schedule_icon = {
            "cron": "🔄",
            "interval": "⏱️",
            "date": "📆"
        }.get(schedule_type, "📌")
        
        msg += (
            f"**#{task_id}** `{action}` {schedule_icon}\n"
            f"   📝 {description}\n"
            f"   ⏰ Próximo: `{next_run_str}`\n\n"
        )
    
    msg += f"━━━━━━━━━━━━━━━━━━\n📌 Total: {len(tasks)} tareas\n`/cancel <ID>` para cancelar"
    
    await message.answer(msg, parse_mode="Markdown")


@router.message(Command("cancel"))
async def cmd_cancel(message: Message, **kwargs):
    """Cancel a scheduled task: /cancel <TASK_ID>"""
    from utils.task_scheduler import get_scheduler
    
    user_id = message.from_user.id
    args = message.text.split()
    
    if len(args) < 2:
        await message.answer(
            "❌ **Uso:** `/cancel <TASK_ID>`\n\n"
            "Usa `/tasks` para ver tus tareas y sus IDs.",
            parse_mode="Markdown"
        )
        return
    
    task_id = args[1]
    scheduler = get_scheduler()
    success, result_msg = scheduler.cancel_task(user_id, task_id)
    
    await message.answer(result_msg, parse_mode="Markdown")
