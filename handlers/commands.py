"""
NEXUS TRADING BOT - Command Handlers
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
from servos.auth import admin_only, is_authorized_admin, owner_only
from servos.db import get_user_name

router = Router(name="commands")

# --- ASSET CONFIGURATION (Centralized) ---
from system_directive import ASSET_GROUPS, GROUP_CONFIG, TICKER_MAP, get_display_name


def get_fear_and_greed_index() -> str:
    """Fetch Fear and Greed Index from alternative.me with retry and extended timeout"""
    url = "https://api.alternative.me/fng/"
    for attempt in range(2):
        try:
            resp = requests.get(url, timeout=15)
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
            if attempt == 1:
                print(f"F&G Error (Final): {e}")
            else:
                print(f"F&G Error (Retrying...): {e}")
    
    return "N/A"


@router.message(CommandStart())
async def cmd_start(message: Message, **kwargs):
    """
    Centro de Comando Principal (Hub v5)

    Interfaz unificada y organizada que proporciona acceso rápido a todas las
    funcionalidades del bot de forma lógica y estructurada.
    """
    try:
        edit_message = kwargs.get('edit_message', False)
        session_manager = kwargs.get('session_manager')

        # 1. Estado de carga (solo si es mensaje nuevo)
        if not edit_message:
            msg_load = await message.answer("🔄 _Iniciando Hub..._", parse_mode="Markdown")
            await asyncio.sleep(0.1)  # Reducido para mejor UX
        else:
            msg_load = message

        # 2. Obtener datos de sesión
        chat_id = str(message.chat.id)
        session = session_manager.get_session(chat_id) if session_manager else None
        user_name = get_user_name(chat_id)

        # 3. Valores por defecto
        mode = "WATCHER"
        p_name = "Estándar"
        risk_label = "Personalizado"
        p_key = "STANDARD_ES"
        ai_enabled = True

        # 4. Obtener configuración de sesión
        if session:
            mode = session.config.get('mode', 'WATCHER')
            p_key = session.config.get('personality', 'STANDARD_ES')
            ai_enabled = session.config.get('sentiment_filter', True)

            # Obtener nombre de personalidad
            from servos.personalities import PersonalityManager
            pm = PersonalityManager()
            profile = pm.get_profile(p_key)
            p_name = profile.get('NAME', p_key)

            # Determinar etiqueta de riesgo desde el perfil seleccionado
            risk_profile = session.config.get('risk_profile', None)
            lev = session.config.get('leverage', 5)

            # Debug: print risk profile detection
            print(f"🔍 Risk profile detection: risk_profile='{risk_profile}', leverage={lev}")

            if risk_profile == "RONIN":
                risk_label = "⚔️ Ronin"
            elif risk_profile == "CONSERVADOR":
                risk_label = "🛡️ Conservador"
            elif risk_profile == "NEXUS":
                risk_label = "🌌 Nexus"
            else:
                # Fallback: determinar por leverage actual
                if lev >= 15:
                    risk_label = "⚔️ Ronin"
                elif lev <= 4:
                    risk_label = "🛡️ Conservador"
                else:
                    risk_label = "🌌 Nexus"

        # 5. Iconos y estado
        mode_icons = {
            'PILOT': '🤖',
            'COPILOT': '👨‍✈️',
            'WATCHER': '👀'
        }
        mode_icon = mode_icons.get(mode, '❓')
        ai_suffix = " ✨" if ai_enabled else ""

        # 6. Obtener saludo personalizado
        from servos.personalities import PersonalityManager
        pm = PersonalityManager()
        profile = pm.get_profile(p_key)

        raw_greeting = profile.get('GREETING', ["Ready."])
        quote = random.choice(raw_greeting) if isinstance(raw_greeting, list) else raw_greeting

        try:
            quote = quote.format(user_name=user_name)
        except:
            pass

        # Limpiar puntuación final para evitar duplicados
        quote = quote.rstrip('.!?,;:')
        formatted_quote = f"      \"{quote}, **{user_name}**.\""

        # 7. Verificar balances y generar mensaje dinámico (solo si hay problemas)
        balance_warning = ""
        show_balance_section = False

        # Fast balance check - only use cached data, no network calls
        if session and hasattr(session, 'shadow_wallet') and session.shadow_wallet:
            try:
                # Use only cached balance data - no network operations
                connected_exchanges = ['BINANCE', 'BYBIT']  # Assume connected if session exists
                low_balance_exchanges = []

                for exchange in connected_exchanges:
                    balance = session.shadow_wallet.balances.get(exchange, {}).get('available', 0)
                    threshold = 6.0  # Same threshold as check_liquidity

                    if balance < threshold and balance > 0:  # Only show if we have data and it's low
                        low_balance_exchanges.append(f"⚠️ **{exchange}:** ${balance:.2f} (Mín: ${threshold:.2f})")
                        show_balance_section = True

                if show_balance_section and low_balance_exchanges:
                    balance_warning = f"💰 **Estado de Balances:**\n" + "\n".join(low_balance_exchanges) + "\n━━━━━━━━━━━━━━━━━━━━━━━━\n"

            except Exception as e:
                # Silent fail - don't block /start for balance check errors
                print(f"⚠️ Fast balance check failed in /start: {e}")
                balance_warning = ""

        # 8. Construir mensaje de bienvenida
        welcome = (
            f"🌌 **NEXUS TRADING BOT** | {mode_icon} **{mode}{ai_suffix}**\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🧠 **Personalidad:** {p_name}\n"
            f"{formatted_quote}\n"
            f"⚖️ **Riesgo:** {risk_label}\n"
            f"{balance_warning}"
            "**Selecciona un módulo:**"
        )

        # 8. Teclado interactivo organizado por categorías
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            # Operaciones principales
            [
                InlineKeyboardButton(text="📊 Dashboard", callback_data="CMD|dashboard"),
                InlineKeyboardButton(text="🔄 Sync All", callback_data="SYNC_ORDERS")
            ],
            # Módulos de selección
            [
                InlineKeyboardButton(text="🌍 GLOBAL MARKET", callback_data="MENU|INTEL"),
                InlineKeyboardButton(text=f"🎮 Modos ({mode})", callback_data="MENU|MODES")
            ],
            # Configuración y ayuda
            [
                InlineKeyboardButton(text="⚙️ Configuración", callback_data="CMD|config"),
                InlineKeyboardButton(text="❓ Ayuda", callback_data="CMD|help")
            ]
        ])

        # 9. Enviar/editar mensaje
        await msg_load.edit_text(welcome, reply_markup=keyboard, parse_mode="Markdown")

    except Exception as e:
        # Fallback message if /start fails
        error_msg = (
            "🌌 **NEXUS TRADING BOT**\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "⚠️ *Error al cargar el Hub principal*\n\n"
            "Intenta usar `/dashboard` para ver el estado del sistema.\n\n"
            f"Error: {str(e)[:100]}..."
        )
        try:
            if not edit_message:
                await msg_load.edit_text(error_msg, parse_mode="Markdown")
            else:
                await message.edit_text(error_msg, parse_mode="Markdown")
        except:
            # Last resort - send new message
            await message.reply("⚠️ Error al cargar el Hub. Usa /dashboard", parse_mode="Markdown")
        print(f"❌ Error in /start command: {e}")


# --- NEW MENU HANDLERS ---

@router.callback_query(F.data == "MENU|MODES")
async def menu_modes(callback: CallbackQuery, **kwargs):
    """Sub-menu for Mode Selection"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🤖 PILOT (Auto)", callback_data="CMD|pilot")],
        [InlineKeyboardButton(text="👨‍✈️ COPILOT (Asist.)", callback_data="CMD|copilot")],
        [InlineKeyboardButton(text="👀 WATCHER (Alertas)", callback_data="CMD|watcher")],
        [InlineKeyboardButton(text="⬅️ Volver al Menú Principal", callback_data="CMD|start")]
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
        
        "🤖 **¿Qué es NEXUS TRADING BOT?**\n"
        "Trading automatizado en Binance, Bybit y Alpaca.\n\n"
        
        "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "🔧 **CONFIGURACIÓN**\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        
        "**PASO 1: Gestión de Exchanges**\n"
        "`/exchanges` - Configura Binance, Bybit y Alpaca desde un solo panel.\n\n"
        
        "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "🎮 **MODOS**\n"
        "• 👀 Watcher - Solo alertas\n"
        "• 👨‍✈️ Copilot - Confirmación manual\n"
        "• 🤖 Pilot - 100% automático\n\n"
        
        "¿Listo? Usa `/exchanges` 🚀"
    )
    
    try:
        await message.answer(startup_text, parse_mode="Markdown", disable_web_page_preview=True)
    except:
        await message.answer(startup_text.replace('*', '').replace('`', ''))


@router.message(Command("help"))
async def cmd_help(message: Message):
    """
    Guía de Comandos - Referencia Completa
    
    Proporciona una referencia organizada de todos los comandos disponibles,
    agrupados por categorías lógicas para facilitar la navegación.
    """
    is_admin = is_authorized_admin(str(message.chat.id))
    
    # Parte 1: Comandos Principales
    help_part1 = (
        "🤖 **NEXUS TRADING BOT v7**\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"

        "📊 **DASHBOARD & MERCADO**\n"
        "/start - Centro de comando principal\n"
        "/dashboard - Balance, posiciones, PnL\n"
        "/scanner - Diagnóstico de mercado\n"
        "/price SYMBOL - Cotización rápida\n"
        "/pnl - Historial de ganancias\n"
        "/sync - Sincronizar SL/TP\n"
        "/net - Red y latencia\n\n"

        "🎯 **TRADING MANUAL**\n"
        "/long SYMBOL - Abrir posición LONG (auto-routing)\n"
        "/short SYMBOL - Abrir posición SHORT (auto-routing)\n"
        "/long_binance SYMBOL - LONG en Binance\n"
        "/short_binance SYMBOL - SHORT en Binance\n"
        "/long_bybit SYMBOL - LONG en Bybit\n"
        "/short_bybit SYMBOL - SHORT en Bybit\n"
        "/buy SYMBOL - Compra SPOT\n"
        "/close SYMBOL - Cerrar posición\n"
        "/closeall - Cierre de emergencia\n\n"

        "🕹️ **MODOS OPERATIVOS**\n"
        "/pilot - Trading 100% autónomo\n"
        "/copilot - Confirmación manual\n"
        "/watcher - Solo alertas\n"
        "/mode PRESET - Ronin/Guardian/Nexus\n"
        "/resetpilot - Reset Circuit Breaker\n"
    )
    
    # Parte 2: IA y Configuración
    help_part2 = (
        "✨ **INTELIGENCIA ARTIFICIAL**\n"
        "/analyze SYMBOL - Análisis IA profundo\n"
        "/news - Boletín de mercado\n"
        "/sentiment - Sentimiento crypto/macro\n"
        "/fomc - Análisis de la FED\n\n"

        "⚙️ **CONFIGURACIÓN**\n"
        "/config - Panel interactivo ⭐\n"
        "/strategies - Motores de señales\n"
        "/assets - Gestión de activos\n"
        "/icons - Gestión de logos\n"
        "/togglegroup - Filtrar grupos\n"
        "/personality - Cambiar voz del bot\n"
        "/set_leverage - Apalancamiento\n"
        "/set_margin - Margen por trade\n\n"

        "🔐 **SEGURIDAD & EXCHANGES**\n"
        "/exchanges - Panel de conexiones ⭐\n"
        "/set_binance - (Legacy) API Keys\n"
        "/delete_keys - Borrar sesión\n\n"

        "📅 **UTILIDADES**\n"
        "/schedule - Programar alertas\n"
        "/tasks - Ver tareas activas\n"
        "/cancel ID - Cancelar tarea\n"
        "/timezone - Zona horaria\n"
        "/cooldowns - Ver cooldowns\n"
    )
    
    # Parte 3: Admin e Información
    help_part3 = ""
    
    if is_admin:
        help_part3 += (
            "\n👑 **ADMINISTRACIÓN**\n"
            "/subs - Listar usuarios\n"
            "/addsub - Agregar suscriptor\n"
            "/addadmin - Agregar admin\n"
            "/remsub - Eliminar usuario\n"
            "/wsstatus - Estado WebSocket\n"
            "/ml_mode - Toggle ML Classifier\n"
            "/retrain - Reentrenar modelo\n"
            "/reset_assets - Limpiar assets\n"
            "/debug - Diagnóstico sistema\n"
        )

    help_part3 += (
        "\n📖 **INFORMACIÓN**\n"
        "/about - Sobre Nexus\n"
        "/strategy - Lógica de señales\n"
        "/startup - Guía de inicio\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "💡 _Tip: Usa /start para navegación rápida_"
    )
    
    try:
        await message.answer(help_part1, parse_mode="Markdown")
        await message.answer(help_part2 + help_part3, parse_mode="Markdown")
    except Exception as e:
        # Fallback sin markdown
        clean = (help_part1 + help_part2 + help_part3).replace('*', '').replace('`', '').replace('\\_', '_')
        try:
            await message.answer(clean)
        except:
            await message.answer("❌ Error mostrando ayuda. Usa /start para navegar.")
        


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
        
        # Macro Data
        macro = data.get('macro', {})
        btc_dom = macro.get('btc_dominance', 0)
        global_state = macro.get('global_state', 'NORMAL')
        state_icon = "🦈" if 'SHARK' in global_state else "🦢" if 'BLACK' in global_state else "✅"
        
        # Build Message
        msg = (
            "📊 **TRADING DASHBOARD**\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            
            f"💰 **Net Worth:** `${net_worth:,.2f}`\n"
            f"📈 **PnL Binance:** {'🟢' if pos.get('binance', {}).get('pnl', 0) >= 0 else '🔴'} `${pos.get('binance', {}).get('pnl', 0):,.2f}`\n"
            f"📈 **PnL Bybit:** {'🟢' if pos.get('bybit', {}).get('pnl', 0) >= 0 else '🔴'} `${pos.get('bybit', {}).get('pnl', 0):,.2f}`\n"
            f"📈 **PnL Alpaca:** {'🟢' if pos.get('alpaca', {}).get('pnl', 0) >= 0 else '🔴'} `${pos.get('alpaca', {}).get('pnl', 0):,.2f}`\n\n"
            
            "**💰 Balances**\n"
            f"• Binance Spot: `${wallet.get('spot_usdt', 0) + wallet.get('earn_usdt', 0):,.0f}`\n"
            f"• Binance Futures: `${wallet.get('futures_balance', 0):,.0f}`\n"
            f"• Bybit Futures: `${wallet.get('bybit_balance', 0):,.0f}`\n"
            f"• Alpaca Equity: `${wallet.get('alpaca_equity', 0):,.0f}`\n\n"
            
            "**⚙️ Estado**\n"
            f"• Modo: {mode_display}\n"
            f"• Posiciones Binance: `{pos.get('binance', {}).get('count', 0)}` ({pos.get('binance', {}).get('longs', 0)}L / {pos.get('binance', {}).get('shorts', 0)}S)\n"
            f"• Posiciones Bybit: `{pos.get('bybit', {}).get('count', 0)}` ({pos.get('bybit', {}).get('longs', 0)}L / {pos.get('bybit', {}).get('shorts', 0)}S)\n"
            f"• Posiciones Alpaca: `{pos.get('alpaca', {}).get('count', 0)}` ({pos.get('alpaca', {}).get('longs', 0)}L / {pos.get('alpaca', {}).get('shorts', 0)}S)\n\n"
            
            "**🌡️ Mercado Global**\n"
            f"{fg_text}\n"
            f"• BTC Dominance: `{btc_dom:.1f}%`\n"
            f"• Sentinel State: {state_icon} `{global_state}`"
        )
        
        # Keyboard
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="🔄 Actualizar", callback_data="CMD|dashboard"),
                InlineKeyboardButton(text="⚙️ Config", callback_data="CMD|config")
            ],
            [
                InlineKeyboardButton(text="⬅️ Volver al Menú Principal", callback_data="CMD|start")
            ]
        ])
        
        await target_msg.edit_text(msg, parse_mode="Markdown", reply_markup=kb)

    except Exception as e:
        await target_msg.edit_text(f"❌ Error: {e}")


# ALIASES
@router.message(Command("status", "wallet", "dashboard"))
async def cmd_dashboard_alias(message: Message, **kwargs):
    """Unified access to Dashboard"""
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
    from servos.diagnostics import run_diagnostics
    
    msg = await message.answer("⏳ Ejecutando diagnóstico de red y sistema...")
    
    try:
        # Get user's session credentials (if available)
        session_manager = kwargs.get('session_manager')
        session = session_manager.get_session(str(message.chat.id)) if session_manager else None
        
        user_api_key = session.config_api_key if session else None
        user_api_secret = session.config_api_secret if session else None
        user_proxy = session.config.get('http_proxy') or getattr(session, '_proxy', None)
        
        # Run async diagnostics directly (no executor needed)
        report = await run_diagnostics(
            api_key=user_api_key, 
            api_secret=user_api_secret, 
            proxy_url=user_proxy
        )
        
        # Split report if too long (Telegram limit 4096)
        if len(report) > 4000:
            for i in range(0, len(report), 4000):
                await message.answer(report[i:i+4000], parse_mode="Markdown")
        else:
            await msg.edit_text(report, parse_mode="Markdown")
            
    except Exception as e:
        # Disable parse_mode for error reporting to avoid "Can't parse entities"
        await msg.edit_text(f"❌ Error en diagnóstico: {e}", parse_mode=None)


@router.message(Command("diag"))
async def cmd_diag(message: Message, **kwargs):
    """Per-symbol diagnostic: /diag SYMBOL"""
    args = message.text.split()
    if len(args) < 2:
        await message.answer("Uso: /diag SYMBOL (ej: /diag BTC o /diag TSLA)")
        return
    
    symbol = args[1].upper()
    
    # Determine if this is an Alpaca symbol or crypto
    from system_directive import ASSET_GROUPS
    is_alpaca = symbol in ASSET_GROUPS.get('STOCKS', []) or symbol in ASSET_GROUPS.get('ETFS', [])
    
    # Only append USDT for crypto symbols
    if not is_alpaca and not symbol.endswith('USDT'):
        symbol = f"{symbol}USDT"
    
    msg = await message.answer(f"Diagnosticando {symbol}...")
    
    try:
        report = f"DIAGNOSTICO: {symbol}\n==================\n\n"
        
        if is_alpaca:
            # ALPACA PATH
            from nexus_system.uplink.price_cache import get_alpaca_price_cache
            from nexus_system.uplink.alpaca_ws_manager import is_us_market_open
            
            cache = get_alpaca_price_cache()
            cached_df = cache.get_dataframe(symbol)
            last_update = cache.get_last_update(symbol)
            is_stale = cache.is_stale(symbol, max_age_seconds=120)
            
            market_status = "ABIERTO" if is_us_market_open() else "CERRADO"
            report += f"Mercado US: {market_status}\n\n"
            
            if not cached_df.empty:
                last_price = cached_df['close'].iloc[-1] if 'close' in cached_df.columns else 0
                candle_count = len(cached_df)
                report += f"WebSocket Cache\n"
                report += f"  Candles: {candle_count}\n"
                report += f"  Ultimo precio: ${last_price:,.2f}\n"
                report += f"  Ultima actualizacion: {last_update.strftime('%H:%M:%S') if last_update else 'N/A'}\n"
                report += f"  Estado: {'Fresco' if not is_stale else 'Stale'}\n\n"
            else:
                report += f"WebSocket Cache: Sin datos\n\n"
            
            # Try Alpaca REST
            try:
                from nexus_system.uplink.alpaca_stream import AlpacaStream
                import os
                key = os.getenv('APCA_API_KEY_ID', '')
                secret = os.getenv('APCA_API_SECRET_KEY', '')
                if key and secret:
                    alpaca = AlpacaStream(api_key=key, api_secret=secret)
                    await alpaca.initialize()
                    result = await alpaca.get_candles(symbol, limit=10)
                    if not result['dataframe'].empty:
                        rest_price = result['dataframe']['close'].iloc[-1]
                        report += f"REST API\n"
                        report += f"  Precio: ${rest_price:,.2f}\n\n"
                    else:
                        report += f"REST API: Sin datos\n\n"
            except Exception as e:
                report += f"REST API: {str(e)[:50]}\n\n"
        else:
            # BINANCE PATH (original logic)
            from nexus_system.uplink.price_cache import get_price_cache
            
            cache = get_price_cache()
            cached_df = cache.get_dataframe(symbol)
            last_update = cache.get_last_update(symbol)
            is_stale = cache.is_stale(symbol, max_age_seconds=120)
            
            if not cached_df.empty:
                last_price = cached_df['close'].iloc[-1] if 'close' in cached_df.columns else 0
                candle_count = len(cached_df)
                report += f"WebSocket Cache\n"
                report += f"  Candles: {candle_count}\n"
                report += f"  Ultimo precio: ${last_price:,.2f}\n"
                report += f"  Ultima actualizacion: {last_update.strftime('%H:%M:%S') if last_update else 'N/A'}\n"
                report += f"  Estado: {'Fresco' if not is_stale else 'Stale'}\n\n"
            else:
                report += f"WebSocket Cache: Sin datos\n\n"
            
            # Try Binance REST
            session_manager = kwargs.get('session_manager')
            if session_manager:
                session = session_manager.get_session(str(message.chat.id))
                if session and session.bridge:
                    try:
                        rest_price = await session.bridge.get_last_price(symbol)
                        if rest_price > 0:
                            report += f"REST API\n"
                            report += f"  Precio: ${rest_price:,.2f}\n\n"
                        else:
                            report += f"REST API: Sin datos\n\n"
                    except Exception as e:
                        report += f"REST API: {str(e)[:50]}\n\n"
        
        # Common: Strategy info
        report += f"Configuracion\n"
        from system_directive import DISABLED_ASSETS
        is_disabled = symbol in DISABLED_ASSETS
        report += f"  Estado: {'Deshabilitado' if is_disabled else 'Activo'}\n"
        report += f"  Broker: {'ALPACA' if is_alpaca else 'BINANCE'}\n"
        
        await msg.edit_text(report)
        
    except Exception as e:
        await msg.edit_text(f"Error: {e}")


@router.message(Command("migrate_security"))
@admin_only
async def cmd_migrate_security(message: Message, **kwargs):
    """Forces encryption of all database entries."""
    from servos.force_encrypt import force_encrypt_all
    
    msg = await message.answer("🔐 Iniciando Migración de Seguridad...\nLeyendo DB y re-encriptando todo...")
    
    try:
        # Run in executor to avoid blocking
        loop = asyncio.get_running_loop()
        success = await loop.run_in_executor(None, force_encrypt_all)
        
        if success:
            await msg.edit_text("✅ Migración Completa\nTodas las claves en la base de datos han sido encriptadas exitosamente con AES-256.")
        else:
            await msg.edit_text("❌ Error en Migración\nRevisa los logs del servidor.")
            
    except Exception as e:
        await msg.edit_text(f"❌ Error crítico: {e}")


# ============================================
# --- RESTORED COMMANDS FROM SYNC VERSION ---
# ============================================

@router.message(Command("mode"))
async def cmd_mode(message: Message, **kwargs):
    """Risk presets: /mode RONIN|GUARDIAN|NEXUS"""
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
        await message.answer("⚠️ Uso: `/mode <RONIN | GUARDIAN | NEXUS>`", parse_mode='Markdown')
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
    elif profile == 'NEXUS' or profile == 'QUANTUM':  # Support both for backward compatibility
        # Balanced
        session.update_config('leverage', 5)
        session.update_config('stop_loss_pct', 0.02)
        session.update_config('atr_multiplier', 2.0)
        session.update_config('sentiment_threshold', -0.6)
        session_manager.save_sessions()
        await message.answer(
            "🌌 **MODO NEXUS ACTIVADO**\n"
            "- Apalancamiento: 5x\n"
            "- Stop Loss: Estándar (2.0 ATR)\n"
            "- Filtro IA: Balanceado (-0.6)\n"
            "_Equilibrio Matemático._",
            parse_mode='Markdown'
        )
    else:
        await message.answer("⚠️ Perfil desconocido. Usa: RONIN, GUARDIAN, NEXUS.")


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




@router.message(Command("news"))
async def cmd_news(message: Message, **kwargs):
    """AI market briefing"""
    from servos.ai_analyst import NexusAnalyst
    
    msg = await message.answer("🗞️ *Leyendo las noticias...* (Consultando via AI)", parse_mode='Markdown')
    
    try:
        analyst = NexusAnalyst()
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
    from servos.ai_analyst import NexusAnalyst
    
    msg = await message.answer("✨ *Escaneando Redes y Noticias...*", parse_mode='Markdown')
    
    try:
        analyst = NexusAnalyst()
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
            "✨ **SENTIMIENTO GLOBAL DEL MERCADO**\n"
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
    from servos.ai_analyst import NexusAnalyst
    
    session_manager = kwargs.get('session_manager')
    chat_id = str(message.chat.id)
    session = session_manager.get_session(chat_id) if session_manager else None
    
    p_key = session.config.get('personality', 'Standard') if session else 'Standard'
    
    msg = await message.answer("🏦 *Analizando situación de la FED...* (Tasas, Bonos, Powell)", parse_mode='Markdown')
    
    try:
        analyst = NexusAnalyst()
        if not analyst.client:
            await msg.edit_text("⚠️ IA no disponible. Configura OPENAI_API_KEY.")
            return
        
        report = analyst.analyze_fomc(personality=p_key)
        await msg.edit_text(f"🏦 **ANÁLISIS FOMC (FED)**\n\n{report}", parse_mode='Markdown')
    except Exception as e:
        await msg.edit_text(f"❌ Error: {e}")


@router.message(Command("analyze"))
async def cmd_analyze(message: Message, **kwargs):
    """
    Análisis AI por activo: /analyze BTC - Usa la personalidad activa del usuario.
    Migrado a versión async usando MarketStream.
    """
    from servos.ai_analyst import NexusAnalyst
    from nexus_system.utils.market_data import get_market_data_async
    from servos.personalities import PersonalityManager
    
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
        # Obtener datos de forma async (usa MarketStream)
        df = await get_market_data_async(symbol, timeframe='1h', limit=50)
        if df.empty:
            await msg.edit_text(f"❌ No data for {symbol}")
            return
        
        current_price = float(df['close'].iloc[-1])
        
        # Calculate RSI from close prices using the utility function
        from servos.indicators import calculate_rsi
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
        
        analyst = NexusAnalyst()
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
            f"🧠 Personalidad: *{p_name}*\n\n"
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
    from nexus_loader import cooldown_manager
    
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
    from nexus_loader import cooldown_manager
    
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
async def _execute_manual_position(message: Message, side: str, force_exchange: str, **kwargs):
    """Helper function to execute manual positions with forced exchange."""
    session_manager = kwargs.get('session_manager')
    if not session_manager: return

    session = session_manager.get_session(str(message.chat.id))
    if not session:
        await message.reply("⚠️ Sin sesión activa.")
        return

    args = message.text.split()
    if len(args) < 2:
        await message.reply(f"⚠️ Uso: /{message.text.split()[0].replace('/', '')} <SYMBOL> (ej: /{message.text.split()[0].replace('/', '')} BTC)")
        return

    # Smart Symbol Resolution
    from system_directive import resolve_symbol
    raw_symbol = args[1]
    symbol = resolve_symbol(raw_symbol)

    # Calculate ATR
    msg_wait = await message.reply(f"⏳ Analizando volatilidad (ATR) para {symbol}...")

    try:
        from nexus_system.utils.market_data import get_market_data_async, calculate_atr_async

        # Obtener velas 1h de forma async
        df = await get_market_data_async(symbol, timeframe='1h', limit=50)
        atr_value = await calculate_atr_async(df, period=14)

        atr_msg = f" (ATR: {atr_value:.4f})" if atr_value > 0 else " (ATR: N/A)"

        direction_emoji = "🚀" if side == "LONG" else "🐻"
        await msg_wait.edit_text(f"{direction_emoji} Iniciando {side} en {symbol} via {force_exchange}{atr_msg}...")

        # Execute with forced exchange
        if side == "LONG":
            success, res_msg = await session.execute_long_position(symbol, atr=atr_value, force_exchange=force_exchange)
        else:
            success, res_msg = await session.execute_short_position(symbol, atr=atr_value, force_exchange=force_exchange)

        # Only send success messages to chat - silence low balance errors
        if success:
            await message.reply(res_msg, parse_mode=None)
        else:
            # Log the error for debugging but don't show to user
            print(f"🔕 Silenced error for {message.text.split()[0]} {symbol}: {res_msg}")
            # Optionally send a generic message
            await message.reply("⚠️ Operación no ejecutada (fondos insuficientes o verificación fallida)", parse_mode=None)

    except Exception as e:
        await msg_wait.edit_text(f"❌ Error iniciando operación: {str(e)}", parse_mode=None)


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
        await message.reply("⚠️ Uso: /long <SYMBOL> (ej: /long BTC)")
        return
    
    # Smart Symbol Resolution
    from system_directive import resolve_symbol
    raw_symbol = args[1]
    symbol = resolve_symbol(raw_symbol)
    
    # Calculate ATR
    msg_wait = await message.reply(f"⏳ Analizando volatilidad (ATR) para {symbol}...")
    
    try:
        from nexus_system.utils.market_data import get_market_data_async, calculate_atr_async
        
        # Obtener velas 1h de forma async
        df = await get_market_data_async(symbol, timeframe='1h', limit=50)
        atr_value = await calculate_atr_async(df, period=14)
        
        atr_msg = f" (ATR: {atr_value:.4f})" if atr_value > 0 else " (ATR: N/A)"
        
        await msg_wait.edit_text(f"🚀 Iniciando LONG FUTURES en {symbol}{atr_msg}...")
        
        # Execute with ATR
        success, res_msg = await session.execute_long_position(symbol, atr=atr_value)

        # Only send success messages to chat - silence low balance errors
        if success:
            await message.reply(res_msg, parse_mode=None)
        else:
            # Log the error for debugging but don't show to user
            print(f"🔕 Silenced error for /long {symbol}: {res_msg}")
            # Optionally send a generic message
            await message.reply("⚠️ Operación no ejecutada (fondos insuficientes o verificación fallida)", parse_mode=None)
        
    except Exception as e:
        await msg_wait.edit_text(f"❌ Error iniciando operación: {str(e)}", parse_mode=None)


@router.message(Command("long_binance"))
async def cmd_long_binance(message: Message, **kwargs):
    """Manually trigger a LONG position on BINANCE specifically."""
    await _execute_manual_position(message, "LONG", "BINANCE", **kwargs)

@router.message(Command("long_bybit"))
async def cmd_long_bybit(message: Message, **kwargs):
    """Manually trigger a LONG position on BYBIT specifically."""
    await _execute_manual_position(message, "LONG", "BYBIT", **kwargs)

@router.message(Command("short_binance"))
async def cmd_short_binance(message: Message, **kwargs):
    """Manually trigger a SHORT position on BINANCE specifically."""
    await _execute_manual_position(message, "SHORT", "BINANCE", **kwargs)

@router.message(Command("short_bybit"))
async def cmd_short_bybit(message: Message, **kwargs):
    """Manually trigger a SHORT position on BYBIT specifically."""
    await _execute_manual_position(message, "SHORT", "BYBIT", **kwargs)

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
    from system_directive import resolve_symbol
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
             await msg_wait.edit_text(f"❌ Falló Compra: {res_msg}", parse_mode=None)
             
    except Exception as e:
        await msg_wait.edit_text(f"❌ Error crítico: {str(e)}", parse_mode=None)


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
        await message.reply("⚠️ Uso: /short <SYMBOL> (ej: /short ETH)")
        return
    
    # Smart Symbol Resolution
    from system_directive import resolve_symbol
    raw_symbol = args[1]
    symbol = resolve_symbol(raw_symbol)
    
    # Calculate ATR
    msg_wait = await message.reply(f"⏳ Analizando volatilidad (ATR) para {symbol}...")
    
    try:
        from nexus_system.utils.market_data import get_market_data_async, calculate_atr_async
        
        # Obtener velas 1h de forma async
        df = await get_market_data_async(symbol, timeframe='1h', limit=50)
        atr_value = await calculate_atr_async(df, period=14)
        
        atr_msg = f" (ATR: {atr_value:.4f})" if atr_value > 0 else " (ATR: N/A)"
        
        await msg_wait.edit_text(f"🐻 Iniciando SHORT en {symbol}{atr_msg}...")
        
        # Execute with ATR
        success, res_msg = await session.execute_short_position(symbol, atr=atr_value)

        # Only send success messages to chat - silence low balance errors
        if success:
            await message.reply(res_msg, parse_mode=None)
        else:
            # Log the error for debugging but don't show to user
            print(f"🔕 Silenced error for /short {symbol}: {res_msg}")
            # Optionally send a generic message
            await message.reply("⚠️ Operación no ejecutada (fondos insuficientes o verificación fallida)", parse_mode=None)
        
    except Exception as e:
        await msg_wait.edit_text(f"❌ Error iniciando operación: {str(e)}", parse_mode=None)


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
    
    # Paso 1: Aplicar breakeven a posiciones rentables (ROI >= 10%)
    breakeven_report = await session.smart_breakeven_check(breakeven_roi_threshold=0.10)
    
    # Paso 2: Aplicar sincronización estándar de SL/TP a todas las posiciones
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
    from nexus_loader import personality_manager
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
        from system_directive import ASSET_GROUPS, GROUP_CONFIG, TICKER_MAP
        from system_directive import DISABLED_ASSETS
        from servos.indicators import calculate_rsi
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
        
        if GROUP_CONFIG.get('ETFS', False):
            for asset in ASSET_GROUPS.get('ETFS', []):
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
                    rsi_series = calculate_rsi(closes)
                    rsi = float(rsi_series.iloc[-1]) if hasattr(rsi_series, 'iloc') else float(rsi_series)
                    
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
                        clean_closes = [c for c in closes if c is not None]
                        rsi_series = calculate_rsi(clean_closes)
                        rsi = float(rsi_series.iloc[-1]) if hasattr(rsi_series, 'iloc') else float(rsi_series)
                        
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

        # --- GET CMC DATA ---
        cmc_data = {}
        try:
            from nexus_system.uplink.cmc_client import CMCClient
            cmc_client = CMCClient()
            cmc_data = await cmc_client.get_global_metrics()
        except Exception as e:
            print(f"⚠️ CMC Data unavailable: {e}")
            cmc_data = {}

        # --- BUILD MESSAGE (PROPUESTA 2) ---
        msg = (
            "🌍 GLOBAL MARKET PULSE\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "📊 **MARKET INTELLIGENCE**\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        )

        # Fear & Greed with thermometer emoji
        thermometer_emoji = "🌡️"  # Changed from 😱
        msg += f"{thermometer_emoji} Sentiment: {fng}\n"

        # CMC Data
        btc_dom = cmc_data.get('btc_dominance', 0)
        eth_dom = cmc_data.get('eth_dominance', 0)
        total_cap = cmc_data.get('total_market_cap', 0)
        total_vol = cmc_data.get('total_volume_24h', 0)

        if btc_dom > 0:
            msg += f"💎 BTC Dominance: {btc_dom:.1f}%\n"
        if eth_dom > 0:
            msg += f"💎 ETH Dominance: {eth_dom:.1f}%\n"
        if total_cap > 0:
            msg += f"💰 Market Cap: ${total_cap/1e9:.1f}T\n"
        if total_vol > 0:
            msg += f"📈 24h Volume: ${total_vol/1e9:.1f}B\n"

        msg += "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"

        # Crypto section with coin emoji instead of diamond
        if crypto_str:
            msg += "🪙 **TOP CRYPTO** (4h Analysis)\n━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            # Add dominance to crypto items (simplified for top 2)
            crypto_lines = crypto_str.split('\n')
            for i, line in enumerate(crypto_lines[:2]):  # Only first 2 cryptos
                if line.strip() and ('BTC' in line or 'ETH' in line):
                    if 'BTC' in line and btc_dom > 0:
                        line += f" • DOM {btc_dom:.1f}%"
                    elif 'ETH' in line and eth_dom > 0:
                        line += f" • DOM {eth_dom:.1f}%"
                    crypto_lines[i] = line
            msg += '\n'.join(crypto_lines) + "\n\n"

        # Stocks section
        if stocks_str:
            msg += "📈 **KEY STOCKS** (Daily)\n━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            msg += stocks_str + "\n"

        # Commodities/Indices section
        if commodities_str:
            msg += "🏆 **MARKET INDICATORS**\n━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            msg += commodities_str + "\n"

        if not (crypto_str or stocks_str or commodities_str):
            msg += "📭 Sin datos disponibles.\n\n"

        msg += "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n📈 Bullish | 📉 Bearish | 🎯 Neutral | 💎 CMC Data"
        
        await loading.edit_text(msg, parse_mode="Markdown")
        
    except Exception as e:
        await message.answer(f"❌ Error en Price: {e}")


# =================================================================
# SCHEDULER COMMANDS - Time & Task Management
# =================================================================

@router.message(Command("timezone"))
async def cmd_timezone(message: Message, **kwargs):
    """View or set user timezone: /timezone [ZONE]"""
    from servos.timezone_manager import (
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
    from servos.task_scheduler import get_scheduler
    from servos.timezone_manager import get_user_timezone, get_current_time_str
    
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
    from servos.task_scheduler import get_scheduler
    from servos.timezone_manager import convert_from_utc, get_user_timezone
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
    from servos.task_scheduler import get_scheduler
    
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


# =================================================================
# OWNER-ONLY OPEN CHAT (LLM with Personality)
# =================================================================

@router.message(F.text & ~F.text.startswith('/'))
async def owner_chat_handler(message: Message, **kwargs):
    """
    Open chat with OpenAI LLM - OWNER ONLY.
    Responses are conditioned by the user's selected personality.
    """
    # Owner-only check
    admin_ids = os.getenv('TELEGRAM_ADMIN_ID', '').replace(' ', '').split(',')
    if str(message.from_user.id) not in admin_ids:
        # Silently ignore non-owner messages (let other handlers pick up)
        return
    
    session_manager = kwargs.get('session_manager')
    if not session_manager:
        return
    
    session = session_manager.get_session(str(message.chat.id))
    if not session:
        return
    
    # Get personality
    personality = session.config.get('personality', 'STANDARD_ES')
    
    # Get OpenAI client
    from servos.ai_analyst import NexusAnalyst
    analyst = NexusAnalyst()
    
    if not analyst.client:
        await message.reply("⚠️ OpenAI no configurado. Verifica `OPENAI_API_KEY`.")
        return
    
    # Get personality prompt
    char_desc = analyst.PERSONALITY_PROMPTS.get(
        personality, 
        analyst.PERSONALITY_PROMPTS.get('STANDARD_ES')
    )
    
    # System prompt for chat
    system_prompt = f"""Eres un asistente de trading con la siguiente personalidad:
{char_desc}

REGLAS:
1. SIEMPRE responde EN ESPAÑOL a menos que el usuario escriba en otro idioma.
2. Mantén el tono y estilo del personaje en TODO momento.
3. Si el usuario pregunta sobre trading, crypto, acciones o mercados, incorpora perspectiva de trading.
4. Sé conciso pero útil (máximo 2-3 párrafos).
5. Puedes usar emojis apropiados al personaje."""

    try:
        # Send typing action
        await message.chat.do('typing')
        
        response = analyst.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": message.text}
            ],
            max_tokens=500,
            temperature=0.8
        )
        
        reply = response.choices[0].message.content
        await message.reply(reply)
        
    except Exception as e:
        await message.reply(f"❌ Error LLM: {e}")


# ========================================================
# ASSET GROUP MANAGEMENT (/assets)
# ========================================================

from servos.db import get_user_enabled_groups, set_user_enabled_groups

def _build_assets_keyboard(chat_id: str) -> InlineKeyboardMarkup:
    """Build inline keyboard showing current asset group toggles."""
    groups = get_user_enabled_groups(chat_id)
    
    def icon(enabled: bool) -> str:
        return "✅" if enabled else "❌"
    
    keyboard = [
        [InlineKeyboardButton(
            text=f"{icon(groups.get('CRYPTO', True))} Crypto (Binance)",
            callback_data="toggle_group:CRYPTO"
        )],
        [InlineKeyboardButton(
            text=f"{icon(groups.get('STOCKS', True))} Stocks (Alpaca)",
            callback_data="toggle_group:STOCKS"
        )],
        [InlineKeyboardButton(
            text=f"{icon(groups.get('ETFS', True))} ETFs (Alpaca)",
            callback_data="toggle_group:ETFS"
        )],
        [InlineKeyboardButton(text="🔙 Volver", callback_data="back_to_start")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


@router.message(Command("assets"))
async def cmd_assets(message: Message, **kwargs):
    """
    Show asset group configuration menu.
    Allows users to enable/disable scanning for Crypto, Stocks, or ETFs.
    """
    chat_id = str(message.chat.id)
    keyboard = _build_assets_keyboard(chat_id)
    
    await message.answer(
        "⚙️ **Configuración de Activos**\n\n"
        "Selecciona los grupos de activos que deseas escanear.\n"
        "Las señales solo se generarán para los grupos habilitados.\n",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )


@router.callback_query(F.data.startswith("toggle_group:"))
async def callback_toggle_group(callback: CallbackQuery, **kwargs):
    """Handle toggle of asset groups."""
    chat_id = str(callback.message.chat.id)
    group_name = callback.data.split(":")[1]
    
    # Get current settings
    groups = get_user_enabled_groups(chat_id)
    
    # Toggle
    groups[group_name] = not groups.get(group_name, True)
    
    # Save
    set_user_enabled_groups(chat_id, groups)
    
    # Update keyboard
    keyboard = _build_assets_keyboard(chat_id)
    
    status = "✅ Habilitado" if groups[group_name] else "❌ Deshabilitado"
    await callback.answer(f"{group_name}: {status}")
    
    await callback.message.edit_reply_markup(reply_markup=keyboard)


# =================================================================
# /scanner - Exchange-Based Asset Scanner Menu
# =================================================================
@router.message(Command("scanner"))
async def cmd_scanner(message: Message, **kwargs):
    """
    Scanner menu - Select exchange to analyze.
    """
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🟡 Binance", callback_data="SCANNER|BINANCE"),
            InlineKeyboardButton(text="🟣 Bybit", callback_data="SCANNER|BYBIT"),
        ],
        [
            InlineKeyboardButton(text="🟢 Alpaca", callback_data="SCANNER|ALPACA"),
        ],
        [
            InlineKeyboardButton(text="🌐 Escaneo Global", callback_data="SCANNER|ALL"),
        ],
        [
            InlineKeyboardButton(text="⬅️ Volver", callback_data="CMD|start"),
        ]
    ])
    
    msg_text = (
        "🔍 <b>NEXUS SCANNER</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "<b>Selecciona un exchange para analizar:</b>\n\n"
        "🟡 <b>Binance</b> → Crypto Perpetuos (USDT)\n"
        "🟣 <b>Bybit</b> → Crypto Perpetuos (V5)\n"
        "🟢 <b>Alpaca</b> → Stocks &amp; ETFs\n\n"
        "🌐 <b>Global</b> → Todos los activos"
    )
    
    edit_message = kwargs.get('edit_message', False)
    if edit_message:
        await message.edit_text(msg_text, reply_markup=keyboard, parse_mode="HTML")
    else:
        await message.answer(msg_text, reply_markup=keyboard, parse_mode="HTML")


async def execute_scanner(message, exchange_filter: str = 'ALL'):
    """
    Execute deep scan for specified exchange(s).
    
    Args:
        message: Telegram message to edit
        exchange_filter: 'BINANCE', 'BYBIT', 'ALPACA', or 'ALL'
    """
    from system_directive import ASSET_GROUPS, get_display_name
    from system_directive import DISABLED_ASSETS, ML_CLASSIFIER_ENABLED
    from nexus_system.cortex.classifier import MarketClassifier
    from nexus_system.cortex.factory import StrategyFactory
    from nexus_system.utils.market_data import get_market_data_async
    from servos.indicators import calculate_rsi, calculate_adx, calculate_atr, calculate_ema, calculate_bollinger_bands
    import pandas as pd
    import html
    import asyncio
    
    # Map exchange to asset groups
    exchange_groups = {
        'BINANCE': ['CRYPTO'],
        'BYBIT': ['BYBIT'],  # Uses dedicated BYBIT asset list
        'ALPACA': ['STOCKS', 'ETFS'],
        'ALL': ['CRYPTO', 'BYBIT', 'STOCKS', 'ETFS']
    }
    
    exchange_icons = {
        'BINANCE': '🟡',
        'BYBIT': '🟣', 
        'ALPACA': '🟢',
        'ALL': '🌐'
    }
    
    groups_to_scan = exchange_groups.get(exchange_filter, ['CRYPTO'])
    icon = exchange_icons.get(exchange_filter, '📡')
    
    report_lines = [
        f"{icon} <b>NEXUS SCANNER - {exchange_filter}</b>",
        "━━━━━━━━━━━━━━━━━━━━━━━━━"
    ]
    
    total_assets = 0
    signals_would_fire = 0
    
    for group_name in groups_to_scan:
        assets = ASSET_GROUPS.get(group_name, [])
        if not assets:
            continue
        
        group_icon = '🟡' if group_name == 'CRYPTO' else '⬛' if group_name == 'BYBIT' else '📈' if group_name == 'STOCKS' else '📦'
        report_lines.append(f"\n{group_icon} <b>{group_name}</b> ({len(assets)} activos)")
        report_lines.append("─" * 30)
        
        for asset in assets:
            total_assets += 1
            tag = "⛔ " if asset in DISABLED_ASSETS else ""
            
            try:
                # Obtener datos de forma async
                df = await get_market_data_async(asset, timeframe='15m', limit=250)
                
                if df is None or df.empty or len(df) < 50:
                    display = html.escape(get_display_name(asset))
                    report_lines.append(f"• <code>{display}</code>: ❌ No data")
                    continue
                
                # Calculate indicators
                df['rsi'] = calculate_rsi(df['close'], 14)
                df['ema_20'] = calculate_ema(df['close'], 20)
                df['ema_50'] = calculate_ema(df['close'], 50)
                df['ema_200'] = calculate_ema(df['close'], 200)
                df['atr'] = calculate_atr(df, 14)
                adx_data = calculate_adx(df, 14)
                df['adx'] = adx_data['adx']
                bb = calculate_bollinger_bands(df['close'], 20, 2.0)
                df['bb_upper'] = bb['upper']
                df['bb_lower'] = bb['lower']
                
                last = df.iloc[-1]
                close = float(last['close'])
                rsi = float(last.get('rsi', 50))
                adx = float(last.get('adx', 0))
                atr = float(last.get('atr', 0))
                atr_pct = (atr / close) * 100 if close > 0 else 0
                
                ema_20 = float(last.get('ema_20', close))
                ema_50 = float(last.get('ema_50', close))
                ema_200 = float(last.get('ema_200', close))
                
                bb_width = ((float(last['bb_upper']) - float(last['bb_lower'])) / close) * 100 if close > 0 else 0
                
                # Trend
                if close > ema_200:
                    trend = "🐂 BULL" if ema_20 > ema_50 else "📈 UP-Weak"
                else:
                    trend = "🐻 BEAR" if ema_20 < ema_50 else "📉 DN-Weak"
                
                # Regime & Signal
                market_data = {'dataframe': df, 'symbol': asset}
                regime = MarketClassifier.classify(market_data)
                strategy = StrategyFactory.get_strategy(asset, market_data)
                
                try:
                    signal = await strategy.analyze(market_data)
                except:
                    signal = None
                
                if signal and signal.action not in ['HOLD', 'WAIT', None]:
                    action_safe = html.escape(str(signal.action))
                    signal_str = f"🚨 <b>{action_safe}</b> ({signal.confidence:.0%})"
                    signals_would_fire += 1
                else:
                    signal_str = "💤 HOLD"
                
                display = html.escape(get_display_name(asset))
                strat_safe = html.escape(strategy.name)
                
                report_lines.append(f"📌 <b>{tag}{display}</b> | <code>${close:,.2f}</code> | {trend}")
                report_lines.append(f"   RSI: <code>{rsi:.1f}</code> | ADX: <code>{adx:.1f}</code> | ATR: <code>{atr_pct:.2f}%</code>")
                report_lines.append(f"   EMA200: <code>${ema_200:,.2f}</code> | BB-W: <code>{bb_width:.1f}%</code>")
                report_lines.append(f"   ⚙️ {regime} | {strat_safe} → {signal_str}")
                report_lines.append("")
                
            except Exception as e:
                display = html.escape(get_display_name(asset))
                err_safe = html.escape(str(e)[:20])
                report_lines.append(f"• <code>{display}</code>: ⚠️ Error: {err_safe}")
    
    # Summary
    report_lines.append("━" * 20)
    report_lines.append(f"🏁 <b>Total Escaneado:</b> {total_assets} Activos")
    report_lines.append(f"🔥 <b>Señales Potenciales:</b> {signals_would_fire}")
    
    # Chunk and send
    chunks = []
    current_chunk = ""
    for line in report_lines:
        if len(current_chunk) + len(line) + 1 > 2500:
            chunks.append(current_chunk)
            current_chunk = line + "\n"
        else:
            current_chunk += line + "\n"
    if current_chunk:
        chunks.append(current_chunk)
    
    await message.edit_text(chunks[0], parse_mode="HTML")
    for chunk in chunks[1:]:
        await message.answer(chunk, parse_mode="HTML")
        await asyncio.sleep(0.3)




# =================================================================
# /icons - Branding: Check Missing Logos
# =================================================================
@router.message(Command("icons"))
async def cmd_icons(message: Message, **kwargs):
    """
    Utility to check which enabled assets lack a custom icon.
    """
    from servos.media_manager import MediaManager
    from system_directive import get_all_assets
    
    symbols = get_all_assets()
    missing = MediaManager.list_missing_icons(symbols)
    
    if not missing:
        return await message.answer("✅ **Perfecto!** Todos los activos habilitados tienen su respectivo icono.")
    
    report = [
        "🖼️ **Branding Status: Asset Icons**",
        f"Se encontraron `{len(missing)}` activos sin icono personalizado.",
        "\n**Faltantes:**",
        f"`{', '.join(missing[:50])}`"
    ]
    
    if len(missing) > 50:
        report.append(f"... y {len(missing) - 50} más.")
        
    report.append("\n**Instrucciones:**")
    report.append("1. Sube los archivos PNG a la carpeta `assets/icons/`.")
    report.append("2. Nombra los archivos en minúsculas (ej: `btc.png`, `sol.png`).")
    report.append("3. Asegúrate de que sean fondos transparentes para mejor visualización.")
    
    await message.answer("\n".join(report), parse_mode="Markdown")


# =================================================================
# /net - Network & Connectivity Diagnostics
# =================================================================
@router.message(Command("net", "ping"))
async def cmd_network_diag(message: Message, **kwargs):
    """
    Diagnostic command to check connectivity and latency to exchanges.
    """
    session_manager = kwargs.get('session_manager')
    chat_id = str(message.chat.id)
    session = session_manager.get_session(chat_id) if session_manager else None
    
    if not session or not session.bridge:
        return await message.answer("❌ No hay una sesión activa para diagnosticar.")
        
    msg_wait = await message.answer("📡 **Escaneando conectividad...**\n_Nexus está probando los túneles de red..._")
    
    report = [
        "🌐 **Diagnóstico de Red Nexus**",
        f"📍 Chat ID: `{chat_id}`",
        f"📅 Hora: `{datetime.now().strftime('%H:%M:%S')}`",
        "━" * 15
    ]
    
    import time
    
    for name, adapter in session.bridge.adapters.items():
        try:
            start_time = time.time()
            # Fast ping: get balance or fetch candles (1m/1 limit)
            if name == 'ALPACA':
                # Alpaca is REST, just get balance
                await adapter.get_account_balance()
            else:
                # Crypto: fetch 1 candle
                await adapter.fetch_candles('BTCUSDT', limit=1)
                
            latency = int((time.time() - start_time) * 1000)
            
            status_icon = "🟢 OK" if latency < 500 else "🟡 LAG"
            if latency > 1500: status_icon = "🟠 SLOW"
            
            report.append(f"🔌 **{name}**: {status_icon}")
            report.append(f"   ⏱️ Latencia: `{latency}ms`")
            
        except Exception as e:
            report.append(f"🔌 **{name}**: 🔴 ERROR")
            report.append(f"   ⚠️ Detalle: `{str(e)[:40]}`")
            
    # WebSocket Status (Binance specific currently)
    try:
        if hasattr(session, 'ws_manager') and session.ws_manager:
            ws_status = session.ws_manager.get_status()
            icon = "🟢 ACTIVO" if ws_status['connected'] else "🔴 OFFLINE"
            report.append(f"\n📡 **Stream (WS)**: {icon}")
            if not ws_status['connected']:
                report.append(f"   🔄 Reintentos: `{ws_status.get('reconnect_attempts', 0)}/25`")
    except:
        pass
        
    report.append("\n💡 *Tip:* Si ves reintentos altos o errores persistentes, verifica tu configuración de PROXY.")
    
    await msg_wait.edit_text("\n".join(report), parse_mode="Markdown")
