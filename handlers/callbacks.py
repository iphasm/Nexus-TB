"""
NEXUS TRADING BOT - Callback Query Handlers
Handles all inline keyboard button presses
EXACT REPLICA of main.py interface
"""

from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.exceptions import TelegramBadRequest
import os

router = Router(name="callbacks")


async def safe_answer(callback: CallbackQuery, text: str = None, show_alert: bool = False):
    """Safely answer a callback query, handling expired/stale queries gracefully."""
    try:
        await callback.answer(text, show_alert=show_alert)
    except TelegramBadRequest as e:
        if "query is too old" in str(e) or "query ID is invalid" in str(e):
            # Query expired (>30s) - ignore silently
            pass
        else:
            raise


@router.callback_query(F.data.startswith("MENU|"))
async def handle_menu_callback(callback: CallbackQuery, **kwargs):
    """Handle v4 Menu Navigation"""
    menu = callback.data.split("|")[1]
    
    if menu == "INTEL":
        # Intel Menu (Previously in callbacks.py but now moved/unified)
        msg = (
            "📡 **INTEL CENTER**\n"
            "━━━━━━━━━━━━━━\n"
            "Acceso a datos de mercado y análisis cuántico.\n"
            "Seleccione un módulo:"
        )
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="💎 Precios Spot", callback_data="CMD|price"),
                InlineKeyboardButton(text="📰 Noticias AI", callback_data="CMD|news")
            ],
            [InlineKeyboardButton(text="🧠 Sentimiento", callback_data="CMD|sentiment")],
            [InlineKeyboardButton(text="🔙 Volver al Hub", callback_data="CMD|start")]
        ])
        await callback.message.edit_text(msg, reply_markup=keyboard, parse_mode="Markdown")
        
    elif menu == "MODES":
        # Handled in commands.py? No, cleaner here to avoid import circles.
        # But we defined it in commands.py earlier. Let's redirect to commands if possible, 
        # OR re-implement here (safe since it's just a keyboard).
        # We'll use the one defined in commands.py if registered, else here.
        pass # It is registered in commands.py, so it will be caught there if router order allows.
             # Wait, different routers? Same dispatcher. Commands router usually first.
             # We should ensure commands router catches MENU|MODES.
             # Actually, better to centralize menu logic here.
             
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🤖 PILOT (Auto)", callback_data="CMD|pilot")],
            [InlineKeyboardButton(text="👨‍✈️ COPILOT (Semi)", callback_data="CMD|copilot")],
            [InlineKeyboardButton(text="👁️ WATCHER (Alertas)", callback_data="CMD|watcher")],
            [InlineKeyboardButton(text="🔙 Volver al Hub", callback_data="CMD|start")]
        ])
        await callback.message.edit_text(
            "🎮 *SELECTOR DE MODO*\n"
            "Selecciona perfil operativo:",
            reply_markup=keyboard, 
            parse_mode="Markdown"
        )


@router.callback_query(F.data.startswith("CMD|"))
async def handle_cmd_callback(callback: CallbackQuery, **kwargs):
    """Handle command shortcuts from buttons - dispatches to actual handlers"""
    cmd = callback.data.split("|")[1]
    session_manager = kwargs.get('session_manager')
    
    await safe_answer(callback)
    
    # Dashboard (Unified Status + Wallet)
    if cmd == "dashboard":
        from handlers.commands import cmd_dashboard
        await cmd_dashboard(callback.message, session_manager=session_manager, edit_message=True)
    
    # Status (Now aliases to Dashboard)
    elif cmd == "status":
        from handlers.commands import cmd_dashboard
        await cmd_dashboard(callback.message, session_manager=session_manager, edit_message=True)
    
    # Wallet (Now aliases to Dashboard)
    elif cmd == "wallet":
        from handlers.commands import cmd_dashboard
        await cmd_dashboard(callback.message, session_manager=session_manager, edit_message=True)
    
    # Mode switches
    elif cmd == "watcher":
        session = session_manager.get_session(str(callback.message.chat.id)) if session_manager else None
        if session:
            session.set_mode('WATCHER')
            await session_manager.save_sessions()
            
            from servos.db import get_user_name
            from servos.personalities import PersonalityManager
            user_name = get_user_name(callback.message.chat.id)
            p_key = session.config.get('personality', 'STANDARD_ES')
            msg = PersonalityManager().get_message(p_key, 'WATCHER_ON', user_name=user_name)
            
            await callback.message.answer(msg, parse_mode="Markdown")
        else:
            await callback.message.answer("⚠️ Sin sesión activa.")
    
    elif cmd == "copilot":
        session = session_manager.get_session(str(callback.message.chat.id)) if session_manager else None
        if session:
            session.set_mode('COPILOT')
            await session_manager.save_sessions()
            
            from servos.db import get_user_name
            from servos.personalities import PersonalityManager
            user_name = get_user_name(callback.message.chat.id)
            p_key = session.config.get('personality', 'STANDARD_ES')
            msg = PersonalityManager().get_message(p_key, 'COPILOT_ON', user_name=user_name)
            
            await callback.message.answer(msg, parse_mode="Markdown")
        else:
            await callback.message.answer("⚠️ Sin sesión activa.")
    
    elif cmd == "pilot":
        session = session_manager.get_session(str(callback.message.chat.id)) if session_manager else None
        if session:
            session.set_mode('PILOT')
            await session_manager.save_sessions()
            
            from servos.db import get_user_name
            from servos.personalities import PersonalityManager
            user_name = get_user_name(callback.message.chat.id)
            p_key = session.config.get('personality', 'STANDARD_ES')
            msg = PersonalityManager().get_message(p_key, 'PILOT_ON', user_name=user_name)
            
            await callback.message.answer(msg, parse_mode="Markdown")
        else:
            await callback.message.answer("⚠️ Sin sesión activa.")
    
    # Help
    elif cmd == "help":
        from handlers.commands import cmd_help
        await cmd_help(callback.message)
    
    # Config
    elif cmd == "config":
        from handlers.config import cmd_config
        await cmd_config(callback.message, session_manager=session_manager, edit_message=True)
    
    # Assets
    elif cmd == "assets":
        from handlers.config import cmd_assets
        await cmd_assets(callback.message, session_manager=session_manager, edit_message=True)

    # Strategies
    elif cmd == "strategies":
        from handlers.config import cmd_strategies
        await cmd_strategies(callback.message, session_manager=session_manager, edit_message=True)

    # Personality
    elif cmd == "personality":
        from handlers.config import cmd_personality
        await cmd_personality(callback.message, session_manager=session_manager, edit_message=True)

    # Mode presets (Ronin/Guardian/Nexus)
    elif cmd.startswith("mode_"):
        preset = cmd.split("_")[1]
        session = session_manager.get_session(str(callback.message.chat.id)) if session_manager else None
        
        if not session:
            await callback.message.answer("⚠️ Sin sesión activa.")
            return
        
        # Apply preset configurations (LEGACY - Use new risk profiles instead)
        # These presets are maintained for backward compatibility but apply risk profiles
        if preset == "RONIN":
            # Apply RONIN risk profile instead of direct config
            await apply_risk_profile_to_session(session, "RONIN")
            msg = "⚔️ *Modo RONIN Activado (Legacy)*\n\nAhora usa el perfil RONIN actualizado:\n• Leverage máx: 20x\n• Capital máx: 20%\n• ATR multiplier: 2.5x\n\n_Se recomienda usar los nuevos perfiles de riesgo._"
        elif preset == "GUARDIAN":
            # Apply CONSERVADOR risk profile (GUARDIAN = CONSERVADOR)
            await apply_risk_profile_to_session(session, "CONSERVADOR")
            msg = "🛡️ *Modo GUARDIAN Activado (Legacy)*\n\nAhora usa el perfil CONSERVADOR:\n• Leverage máx: 3x\n• Capital máx: 30%\n• ATR multiplier: 1.5x\n\n_Se recomienda usar los nuevos perfiles de riesgo._"
        elif preset == "NEXUS" or preset == "QUANTUM":  # Support both for backward compatibility
            # Apply NEXUS risk profile
            await apply_risk_profile_to_session(session, "NEXUS")
            msg = "🌌 *Modo NEXUS Activado (Legacy)*\n\nAhora usa el perfil NEXUS:\n• Leverage máx: 10x\n• Capital máx: 50%\n• ATR multiplier: 2.0x\n\n_Se recomienda usar los nuevos perfiles de riesgo._"
        else:
            msg = f"❓ Preset desconocido: {preset}"
        
        await session_manager.save_sessions()
        await callback.message.answer(msg, parse_mode="Markdown")
    
    # AI Commands - Execute actual handlers
    elif cmd == "news":
        from handlers.commands import cmd_news
        await cmd_news(callback.message, session_manager=session_manager)
    
    elif cmd == "sentiment":
        from handlers.commands import cmd_sentiment
        await cmd_sentiment(callback.message, session_manager=session_manager)
    
        
    # Scanner
    elif cmd == "scanner":
        from handlers.commands import cmd_scanner
        await cmd_scanner(callback.message, session_manager=session_manager, edit_message=True)
        
    elif cmd == "price":
        from handlers.commands import cmd_price
        await cmd_price(callback.message, session_manager=session_manager)
        
    elif cmd == "fomc":
        from handlers.commands import cmd_fomc
        await cmd_fomc(callback.message, session_manager=session_manager)
        
    elif cmd == "start":
        from handlers.commands import cmd_start
        await cmd_start(callback.message, session_manager=session_manager, edit_message=True)
    
    elif cmd == "exchanges":
        from handlers.config import cmd_exchanges
        await cmd_exchanges(callback.message, session_manager=session_manager, edit_message=True)
    
    elif cmd == "delete_keys":
        # Show danger zone confirmation
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🗑️ CONFIRMAR BORRADO", callback_data="CONFIRM_DELETE_KEYS")],
            [InlineKeyboardButton(text="⬅️ Cancelar", callback_data="CMD|exchanges")]
        ])
        await callback.message.edit_text(
            "⚠️ *ZONA DE PELIGRO*\n\n"
            "Esto borrará TODAS tus API Keys y configuración.\n"
            "¿Estás seguro?",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
    
    else:
        await callback.message.answer(f"⚠️ Comando no reconocido: {cmd}")


@router.callback_query(F.data.startswith("WIZARD|"))
async def handle_wizard_callback(callback: CallbackQuery, **kwargs):
    """Handle API Key Setup Wizard"""
    exchange = callback.data.split("|")[1]
    
    await safe_answer(callback)
    
    # Map exchange to command
    cmd_map = {
        'BINANCE': '/set_binance',
        'BYBIT': '/set_bybit',
        'ALPACA': '/set_alpaca'
    }
    
    cmd = cmd_map.get(exchange, '/set_binance')
    
    await callback.message.edit_text(
        f"🔑 *Configurar {exchange}*\n\n"
        f"Envía tus claves API en el siguiente formato:\n\n"
        f"`{cmd} TU_API_KEY TU_API_SECRET`\n\n"
        f"_Las claves se guardan de forma segura._",
        parse_mode="Markdown"
    )


@router.callback_query(F.data.startswith("EXCHANGE|PRIMARY|"))
async def handle_primary_exchange(callback: CallbackQuery, **kwargs):
    """Handle Primary Exchange Selection"""
    session_manager = kwargs.get('session_manager')
    exchange = callback.data.split("|")[2]
    
    await safe_answer(callback)
    
    if not session_manager:
        await callback.message.answer("⚠️ Error interno.")
        return
    
    session = session_manager.get_session(str(callback.message.chat.id))
    if not session:
        await callback.message.answer("⚠️ Sin sesión activa.")
        return
    
    # Update primary exchange
    await session.update_config('primary_exchange', exchange)
    await session_manager.save_sessions()
    
    # Refresh the exchanges panel
    from handlers.config import cmd_exchanges
    await cmd_exchanges(callback.message, session_manager=session_manager, edit_message=True)


@router.callback_query(F.data == "CONFIRM_DELETE_KEYS")
async def handle_confirm_delete(callback: CallbackQuery, **kwargs):
    """Handle key deletion confirmation"""
    session_manager = kwargs.get('session_manager')
    
    await safe_answer(callback)
    
    if session_manager:
        chat_id = str(callback.message.chat.id)
        session_manager.remove_session(chat_id)
        await session_manager.save_sessions()
        await callback.message.edit_text("🗑️ *Sesión eliminada.*\n\nUsa /start para comenzar de nuevo.", parse_mode="Markdown")
    else:
        await callback.message.answer("⚠️ Error interno.")


@router.callback_query(F.data.startswith("CFG|"))
async def handle_config_callback(callback: CallbackQuery, **kwargs):
    """Handle configuration changes"""
    session_manager = kwargs.get('session_manager')
    
    parts = callback.data.split("|")
    action = parts[1]
    
    await safe_answer(callback)
    
    if action == "LEV_MENU":
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
            ],
            [InlineKeyboardButton(text="🔙 Volver", callback_data="CMD|config")]
        ])
        await callback.message.edit_text(
            "⚖️ *CONFIGURAR APALANCAMIENTO*\n\nSelecciona el nivel:",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
        
    elif action == "MARGIN_MENU":
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
            ],
            [InlineKeyboardButton(text="🔙 Volver", callback_data="CMD|config")]
        ])
        await callback.message.edit_text(
            "💰 *CONFIGURAR MARGEN*\n\nPorcentaje del balance por operación:",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
        
    elif action == "LEV" and len(parts) >= 3:
        value = int(parts[2])
        
        if session_manager:
            session = session_manager.get_session(str(callback.message.chat.id))
            if session:
                await session.update_config('leverage', value)
                await session_manager.save_sessions()
                await callback.message.edit_text(f"✅ Apalancamiento configurado a *{value}x*", parse_mode="Markdown")
            else:
                await callback.message.edit_text("⚠️ No tienes sesión activa.")
        else:
            await callback.message.edit_text(f"✅ Apalancamiento: *{value}x*", parse_mode="Markdown")
            
    elif action == "MARGIN" and len(parts) >= 3:
        value = int(parts[2])
        
        if session_manager:
            session = session_manager.get_session(str(callback.message.chat.id))
            if session:
                await session.update_config('max_capital_pct', value / 100)
                await session_manager.save_sessions()
                await callback.message.edit_text(f"✅ Margen configurado a *{value}%*", parse_mode="Markdown")
            else:
                await callback.message.edit_text("⚠️ No tienes sesión activa.")
        else:
            await callback.message.edit_text(f"✅ Margen: *{value}%*", parse_mode="Markdown")


@router.callback_query(F.data.startswith("TOGGLE|"))
async def handle_strategy_toggle(callback: CallbackQuery, **kwargs):
    """Toggle strategy on/off and persist to Session + sync with Global Config."""
    strategy = callback.data.split("|")[1]
    session_manager = kwargs.get('session_manager')
    
    if not session_manager:
        await safe_answer(callback, "⚠️ Error: No session manager", show_alert=True)
        return
        
    session = session_manager.get_session(str(callback.message.chat.id))
    if not session:
        await safe_answer(callback, "⚠️ No hay sesión activa.", show_alert=True)
        return
    
    # Special case: AI_FILTER toggle (mapped to sentiment_filter)
    if strategy == "AI_FILTER":
        current = session.config.get('sentiment_filter', True)
        new_state = not current
        await session.update_config('sentiment_filter', new_state)
        await session_manager.save_sessions()
        
        # SYNC with global config
        import system_directive as aq_config
        aq_config.AI_FILTER_ENABLED = new_state
        
        status = "🟢 ACTIVADO" if new_state else "🔴 DESACTIVADO"
        await safe_answer(callback, f"🧠 AI Filter {status}")
        
        # Refresh Config Menu
        from handlers.config import cmd_config
        await cmd_config(callback.message, session_manager=session_manager, edit_message=True)
        return

    # Special case: ML_MODE toggle
    if strategy == "ML_MODE":
        import system_directive as aq_config
        current = aq_config.ML_CLASSIFIER_ENABLED
        new_state = not current
        aq_config.ML_CLASSIFIER_ENABLED = new_state
        
        # Persist to DB
        from servos.db import save_bot_state
        from system_directive import GROUP_CONFIG
        gc_copy = dict(GROUP_CONFIG)
        gc_copy['_ML_CLASSIFIER'] = new_state  # Store ML flag
        save_bot_state(aq_config.ENABLED_STRATEGIES, gc_copy, list(aq_config.DISABLED_ASSETS), aq_config.AI_FILTER_ENABLED)
        
        status = "🟢 ACTIVADO" if new_state else "🔴 DESACTIVADO"
        
        # Check model existence warning
        import os
        model_path = os.path.join("nexus_system", "memory_archives", "ml_model.pkl")
        if new_state and not os.path.exists(model_path):
             status += " (⚠️ Sin Modelo)"
             
        await safe_answer(callback, f"🤖 ML Mode {status}")
        
        # Refresh Config Menu
        from handlers.config import cmd_config
        await cmd_config(callback.message, session_manager=session_manager, edit_message=True)
        return

    # Special case: PREMIUM SIGNALS toggle
    if strategy == "PREMIUM":
        import system_directive as aq_config
        current = aq_config.PREMIUM_SIGNALS_ENABLED
        new_state = not current
        aq_config.PREMIUM_SIGNALS_ENABLED = new_state
        
        # Persist to DB
        from servos.db import save_bot_state
        from system_directive import GROUP_CONFIG
        save_bot_state(aq_config.ENABLED_STRATEGIES, GROUP_CONFIG, list(aq_config.DISABLED_ASSETS), aq_config.AI_FILTER_ENABLED, new_state)
        
        status = "💎 ACTIVADO (MTF + Volume)" if new_state else "❌ DESACTIVADO"
        await safe_answer(callback, f"Premium Signals: {status}")
        
        # Refresh Strategy Menu
        from handlers.config import cmd_strategies
        await cmd_strategies(callback.message, session_manager=session_manager, edit_message=True)
        return

    # Special case: CIRCUIT BREAKER toggle
    if strategy == "CIRCUIT_BREAKER":
        current = session.config.get('circuit_breaker_enabled', True)
        new_state = not current
        await session.update_config('circuit_breaker_enabled', new_state)
        await session_manager.save_sessions()
        
        status = "ACTIVO" if new_state else "DESACTIVADO"
        await safe_answer(callback, f"🔌 Circuit Breaker: {status}")
        
        # Refresh Config Menu (NOT Strategy Menu)
        from handlers.config import cmd_config
        await cmd_config(callback.message, session_manager=session_manager, edit_message=True)
        return

    # Special case: KELLY CRITERION toggle
    if strategy == "KELLY":
        current = session.config.get('use_kelly_criterion', False)
        new_state = not current
        await session.update_config('use_kelly_criterion', new_state)
        await session_manager.save_sessions()
        
        status = "🟢 ACTIVADO" if new_state else "🔴 DESACTIVADO"
        await safe_answer(callback, f"💰 Kelly Criterion {status}")
        
        # Refresh Config Menu
        from handlers.config import cmd_config
        await cmd_config(callback.message, session_manager=session_manager, edit_message=True)
        return
        
    # Special case: SHIELD toggle
    if strategy == "SHIELD":
        current = session.config.get('correlation_guard_enabled', True)
        new_state = not current
        await session.update_config('correlation_guard_enabled', new_state)
        await session_manager.save_sessions()
        
        status = "🟢 ACTIVADO" if new_state else "🔴 DESACTIVADO"
        await safe_answer(callback, f"🛡️ Portfolio Shield {status}")
        
        # Refresh Config Menu
        from handlers.config import cmd_config
        await cmd_config(callback.message, session_manager=session_manager, edit_message=True)
        return

    # Special case: SENTINEL toggle (unified Black Swan + Shark)
    if strategy == "SENTINEL":
        # Toggle both BLACK_SWAN and SHARK together
        current_bs = session.config.get('strategies', {}).get('BLACK_SWAN', True)
        new_state = not current_bs
        
        session.config.setdefault('strategies', {})
        session.config['strategies']['BLACK_SWAN'] = new_state
        session.config['strategies']['SHARK'] = new_state
        session.config['strategies']['SENTINEL'] = new_state
        await session_manager.save_sessions()
        
        # Sync with global
        import system_directive as aq_config
        aq_config.ENABLED_STRATEGIES['BLACK_SWAN'] = new_state
        aq_config.ENABLED_STRATEGIES['SHARK'] = new_state
        
        status = "🛡️ ACTIVO (Defense + Shark)" if new_state else "❌ DESACTIVADO"
        await safe_answer(callback, f"Sentinel: {status}")
        
        # Refresh Strategy Menu
        from handlers.config import cmd_strategies
        await cmd_strategies(callback.message, session_manager=session_manager, edit_message=True)
        return
    
    # Normal strategy toggle
    try:
        new_val = session.toggle_strategy(strategy)
        await session_manager.save_sessions()
        
        # === CRITICAL: Sync with Global ENABLED_STRATEGIES ===
        # This ensures StrategyFactory respects user preferences
        import system_directive as aq_config
        aq_config.ENABLED_STRATEGIES[strategy] = new_val
        print(f"🔄 Strategy Sync: {strategy} = {new_val}")
        
        new_state = "✅ ACTIVADO" if new_val else "❌ DESACTIVADO"
        await safe_answer(callback, f"{strategy}: {new_state}")
        
        # Rebuild keyboard (use unified Sentinel)
        strategies = session.config.get('strategies', {})
        t_state = "✅" if strategies.get('TREND', True) else "❌"
        s_state = "✅" if strategies.get('SCALPING', True) else "❌"
        g_state = "✅" if strategies.get('GRID', True) else "❌"
        m_state = "✅" if strategies.get('MEAN_REVERSION', True) else "❌"
        sent_state = "✅" if strategies.get('SENTINEL', True) or strategies.get('BLACK_SWAN', True) else "❌"
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=f"📈 Trend (BTC): {t_state}", callback_data="TOGGLE|TREND")],
            [InlineKeyboardButton(text=f"🛡️ Sentinel (Defense/Shark): {sent_state}", callback_data="TOGGLE|SENTINEL")],
            [
                InlineKeyboardButton(text=f"⚡ Scalp: {s_state}", callback_data="TOGGLE|SCALPING"),
                InlineKeyboardButton(text=f"🕸️ Grid: {g_state}", callback_data="TOGGLE|GRID")
            ],
            [InlineKeyboardButton(text=f"📉 Mean Rev: {m_state}", callback_data="TOGGLE|MEAN_REVERSION")],
            [InlineKeyboardButton(text="⬅️ Volver", callback_data="CMD|config")]
        ])
        
        await callback.message.edit_reply_markup(reply_markup=keyboard)
        
    except Exception as e:
        await safe_answer(callback, f"Error: {e}", show_alert=True)



@router.callback_query(F.data.startswith("TOGGLEGRP|"))
async def handle_group_toggle(callback: CallbackQuery, **kwargs):
    """Toggle asset group on/off - Supports display name mapping"""
    parts = callback.data.split("|")
    group = parts[1]  # Internal group name (CRYPTO, BYBIT, STOCKS, ETFS)
    display_name = parts[2] if len(parts) > 2 else group  # Friendly name (Binance, Bybit, etc.)
    
    session_manager = kwargs.get('session_manager')
    
    if not session_manager:
        await safe_answer(callback, "⚠️ Error interno", show_alert=True)
        return
        
    session = session_manager.get_session(str(callback.message.chat.id))
    if not session:
        await safe_answer(callback, "⚠️ Sin sesión", show_alert=True)
        return
    
    try:
        new_val = session.toggle_group(group)
        await session_manager.save_sessions()
        
        new_state = "✅ ACTIVADO" if new_val else "❌ DESACTIVADO"
        # Use display name in confirmation message
        await safe_answer(callback, f"{display_name}: {new_state}")
        
        # Rebuild buttons + Volver
        # Use simple reload of cmd_assets to update view properly
        from handlers.config import cmd_assets
        await cmd_assets(callback.message, session_manager=session_manager, edit_message=True)
        
    except Exception as e:
        await safe_answer(callback, f"Error: {e}", show_alert=True)


@router.callback_query(F.data.startswith("PERSONALITY|"))
async def handle_personality_select(callback: CallbackQuery, **kwargs):
    """Set bot personality"""
    personality = callback.data.split("|")[1]
    session_manager = kwargs.get('session_manager')
    
    if session_manager:
        session = session_manager.get_session(str(callback.message.chat.id))
        if session:
            await session.update_config('personality', personality)
            await session_manager.save_sessions()
            await safe_answer(callback, f"Personalidad: {personality}")
            await callback.message.edit_text(f"🧠 Personalidad cambiada a *{personality}*", parse_mode="Markdown")
            return
    
    await safe_answer(callback, "⚠️ Sin sesión activa", show_alert=True)


@router.callback_query(F.data.startswith("TRADE|"))
async def handle_trade_proposal(callback: CallbackQuery, **kwargs):
    """Handle Copilot trade proposals (Accept/Reject) - Auto-delete proposal"""
    session_manager = kwargs.get('session_manager')
    
    parts = callback.data.split("|")
    
    if len(parts) < 4:
        await safe_answer(callback, "❌ Datos inválidos", show_alert=True)
        return
    
    action = parts[1]
    symbol = parts[2]
    side = parts[3]
    strategy = parts[4] if len(parts) > 4 else "Manual"
    
    await safe_answer(callback)
    
    # Delete the proposal message
    try:
        await callback.message.delete()
    except:
        pass  # Ignore if already deleted
    
    if action == "REJECT":
        await callback.message.answer(
            f"❌ *Propuesta Rechazada* ({strategy})\n"
            f"Operación {side} en {symbol} cancelada.",
            parse_mode="Markdown"
        )
        return
    
    # ACCEPT
    if not session_manager:
        await callback.message.answer("⚠️ Error: SessionManager no disponible.")
        return
    
    session = session_manager.get_session(str(callback.message.chat.id))
    if not session:
        await callback.message.answer("⚠️ No tienes sesión activa.")
        return
    
    status_msg = await callback.message.answer(f"⏳ Ejecutando {side} en {symbol}...")
    
    try:
        if side == "LONG":
            success, msg = await session.execute_long_position(symbol, strategy=strategy)
        else:
            success, msg = await session.execute_short_position(symbol, strategy=strategy)
        
        if success:
            img_path = None
            if "[IMAGE]:" in msg:
                parts = msg.split("[IMAGE]:")
                msg = parts[0].strip()
                img_path = parts[1].strip()

            await status_msg.edit_text(
                f"✅ *{side} EJECUTADO*\n{msg}",
                parse_mode="Markdown"
            )
            
            if img_path and os.path.exists(img_path):
                from aiogram.types import FSInputFile
                try:
                    photo = FSInputFile(img_path)
                    await callback.message.answer_photo(photo, caption=f"📸 Análisis Visual: {symbol}")
                except Exception as e:
                    print(f"Failed to send photo: {e}")
        else:
            await status_msg.edit_text(f"❌ Error: {msg}")
            
    except Exception as e:
        await status_msg.edit_text(f"❌ Error crítico: {e}")


@router.callback_query(F.data.startswith("ASSETS|"))
async def handle_assets_menu(callback: CallbackQuery, **kwargs):
    """Handle asset module selection - Show category selector for GLOBAL"""
    module = callback.data.split("|")[1]
    session_manager = kwargs.get('session_manager')
    
    await safe_answer(callback)
    
    try:
        from system_directive import SHARK_TARGETS, DISABLED_ASSETS, ASSET_GROUPS, TICKER_MAP
        
        if module == "SHARK":
            assets = SHARK_TARGETS
            title = "🦈 SHARK TARGETS"
            
            # Build simple flat list for Shark
            buttons = []
            if not session_manager:
                await callback.message.edit_text("⚠️ Error interno")
                return
                 
            session = session_manager.get_session(str(callback.message.chat.id))
            
            for asset in assets[:80]:
                is_disabled = session.is_asset_disabled(asset) if session else asset in DISABLED_ASSETS
                icon = "❌" if is_disabled else "✅"
                display = TICKER_MAP.get(asset, asset)
                buttons.append([InlineKeyboardButton(
                    text=f"{icon} {display}",
                    callback_data=f"ASSET_TOGGLE|{module}|{asset}"
                )])
            
            buttons.append([InlineKeyboardButton(text="⬅️ Volver", callback_data="CMD|config")])
            keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
            
            await callback.message.edit_text(
                f"📦 *{title}*\n\n"
                f"Activos: {len(assets)}\n"
                "Toca para activar/desactivar:",
                reply_markup=keyboard,
                parse_mode="Markdown"
            )
            return
        
        # === GLOBAL SCANNER: Show Category Selector ===
        # Show: CRYPTO | STOCKS | ETFs
        # When CRYPTO is pressed, show Binance and Bybit options
        crypto_count = len(ASSET_GROUPS.get('CRYPTO', []))
        bybit_count = len(ASSET_GROUPS.get('BYBIT', []))
        stocks_count = len(ASSET_GROUPS.get('STOCKS', []))
        etfs_count = len(ASSET_GROUPS.get('ETFS', []))
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=f"🟡 CRYPTO ({crypto_count + bybit_count})", callback_data="ASSETS_CAT|CRYPTO")],
            [InlineKeyboardButton(text=f"📈 STOCKS ({stocks_count})", callback_data="ASSETS_CAT|STOCKS")],
            [InlineKeyboardButton(text=f"📦 ETFs ({etfs_count})", callback_data="ASSETS_CAT|ETFS")],
            [InlineKeyboardButton(text="⬅️ Volver", callback_data="CMD|config")]
        ])
        
        await callback.message.edit_text(
            "📡 *SCANNER GLOBAL*\n\n"
            f"Total: {crypto_count + bybit_count + stocks_count + etfs_count} activos\n\n"
            "Selecciona una categoría:",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
        
    except Exception as e:
        await callback.message.edit_text(f"❌ Error: {e}")


@router.callback_query(F.data.startswith("ASSETS_CAT|"))
async def handle_assets_category(callback: CallbackQuery, **kwargs):
    """Handle category-specific asset list - Special handling for CRYPTO"""
    category = callback.data.split("|")[1]
    session_manager = kwargs.get('session_manager')
    
    await safe_answer(callback)
    
    try:
        from system_directive import DISABLED_ASSETS, ASSET_GROUPS, TICKER_MAP
        
        # Special case: If CRYPTO is selected, show Binance and Bybit options
        if category == 'CRYPTO':
            crypto_count = len(ASSET_GROUPS.get('CRYPTO', []))
            bybit_count = len(ASSET_GROUPS.get('BYBIT', []))
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text=f"🟡 Binance ({crypto_count})", callback_data="ASSETS_CAT|BINANCE")],
                [InlineKeyboardButton(text=f"⬛ Bybit ({bybit_count})", callback_data="ASSETS_CAT|BYBIT")],
                [InlineKeyboardButton(text="⬅️ Volver", callback_data="ASSETS|GLOBAL")]
            ])
            
            await callback.message.edit_text(
                "🟡 *CRYPTO*\n\n"
                "Selecciona un exchange:",
                reply_markup=keyboard,
                parse_mode="Markdown"
            )
            return
        
        # Map BINANCE to CRYPTO group for asset retrieval
        if category == 'BINANCE':
            category = 'CRYPTO'
        
        assets = ASSET_GROUPS.get(category, [])
        
        titles = {
            'CRYPTO': '🟡 BINANCE',
            'BINANCE': '🟡 BINANCE',
            'BYBIT': '⬛ BYBIT',
            'STOCKS': '📈 STOCKS (Alpaca)',
            'ETFS': '📦 ETFs (Alpaca)'
        }
        title = titles.get(category, category)
        
        if not session_manager:
            await callback.message.edit_text("⚠️ Error interno")
            return
             
        session = session_manager.get_session(str(callback.message.chat.id))
        
        buttons = []
        
        # Helper to format display name for stocks/ETFs
        def get_display(asset: str) -> str:
            name = TICKER_MAP.get(asset, asset)
            if category in ['STOCKS', 'ETFS']:
                # Strip emoji and show "Full Name (TICKER)"
                clean_name = ''.join(c for c in name if c.isalnum() or c.isspace() or c == '&').strip()
                return f"{clean_name} ({asset})"
            return name
        
        for asset in assets:
            is_disabled = session.is_asset_disabled(asset) if session else asset in DISABLED_ASSETS
            icon = "❌" if is_disabled else "✅"
            display = get_display(asset)
            buttons.append([InlineKeyboardButton(
                text=f"{icon} {display}",
                callback_data=f"ASSET_TOGGLE|{category}|{asset}"
            )])
        
        buttons.append([InlineKeyboardButton(text="⬅️ Volver", callback_data="ASSETS|GLOBAL")])
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
        
        await callback.message.edit_text(
            f"📦 *{title}*\n\n"
            f"Activos: {len(assets)}\n"
            "Toca para activar/desactivar:",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
        
    except Exception as e:
        await callback.message.edit_text(f"❌ Error: {e}")





@router.callback_query(F.data.startswith("ASSET_TOGGLE|"))
async def handle_asset_toggle(callback: CallbackQuery, **kwargs):
    """Toggle individual asset"""
    parts = callback.data.split("|")
    module = parts[1]
    asset = parts[2]
    
    session_manager = kwargs.get('session_manager')
    if not session_manager:
        await safe_answer(callback, "⚠️ Error interno", show_alert=True)
        return
        
    session = session_manager.get_session(str(callback.message.chat.id))
    if not session:
        await safe_answer(callback, "⚠️ Sin sesión", show_alert=True)
        return
    
    try:
        # Toggle using session method (for per-user filtering)
        is_now_disabled = session.toggle_asset_blacklist(asset)
        await session_manager.save_sessions()
        
        # ALSO update GLOBAL DISABLED_ASSETS (used by NexusCore)
        from system_directive import DISABLED_ASSETS
        from system_directive import ASSET_GROUPS, GROUP_CONFIG
        from servos.db import save_bot_state
        import system_directive as aq_config
        
        if is_now_disabled:
            DISABLED_ASSETS.add(asset)
        else:
            DISABLED_ASSETS.discard(asset)
        
        # Persist to database so it survives restarts
        from system_directive import ENABLED_STRATEGIES
        save_bot_state(ENABLED_STRATEGIES, GROUP_CONFIG, list(DISABLED_ASSETS), aq_config.AI_FILTER_ENABLED)
        
        if is_now_disabled:
            await safe_answer(callback, f"❌ {asset} desactivado (Global + Session)")
        else:
            await safe_answer(callback, f"✅ {asset} activado (Global + Session)")
        
        # Refresh menu
        await handle_assets_menu(callback, **kwargs)
        
    except Exception as e:
        await safe_answer(callback, f"Error: {e}", show_alert=True)


@router.callback_query(F.data == "MENU|INTEL")
async def handle_intel_menu(callback: CallbackQuery, **kwargs):
    """Intel / Data Menu"""
    
    msg = (
        "📡 **INTEL CENTER**\n"
        "━━━━━━━━━━━━━━\n"
        "Acceso a datos de mercado y análisis cuántico.\n"
        "Seleccione un módulo:"
    )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="💎 Precios Spot", callback_data="CMD|price"),
            InlineKeyboardButton(text="📰 Noticias AI", callback_data="CMD|news")
        ],
        [
            InlineKeyboardButton(text="🧠 Sentimiento", callback_data="CMD|sentiment"),
            InlineKeyboardButton(text="🔙 Menú Principal", callback_data="CMD|start")
        ]
    ])
    
    await callback.message.edit_text(msg, reply_markup=keyboard, parse_mode="Markdown")


@router.callback_query(F.data == "SYNC_ORDERS")
async def handle_sync_orders(callback: CallbackQuery, **kwargs):
    """Handle Sync Orders button"""
    session_manager = kwargs.get('session_manager')
    if not session_manager:
        await safe_answer(callback, "⚠️ Error interno.")
        return
        
    session = session_manager.get_session(str(callback.message.chat.id))
    if not session:
        await safe_answer(callback, "⚠️ Sin sesión.")
        return
    
    await safe_answer(callback, "⏳ Sincronizando órdenes...")
    
    try:
        report = await session.execute_refresh_all_orders()
        await callback.message.answer(report, parse_mode="Markdown")
        
    except Exception as e:
        await callback.message.answer(f"❌ Error: {e}")


@router.callback_query(F.data.startswith("SCANNER|"))
async def handle_scanner_callback(callback: CallbackQuery, **kwargs):
    """Handle scanner exchange selection - Execute scan for selected exchange."""
    exchange = callback.data.split("|")[1]
    session_manager = kwargs.get('session_manager')
    
    await safe_answer(callback, f"🔍 Escaneando {exchange}...")
    
    try:
        # Update message to show scanning
        msg = await callback.message.edit_text(
            f"🔍 <b>Escaneando {exchange}...</b>\n\n"
            "Esto puede tomar unos momentos.",
            parse_mode="HTML"
        )
        
        # Import and execute scanner
        from handlers.commands import execute_scanner
        await execute_scanner(msg, exchange_filter=exchange)
        
    except Exception as e:
        err_clean = str(e).replace('<', '').replace('>', '')
        await callback.message.edit_text(f"❌ Scanner Error: {err_clean}", parse_mode=None)


# =================================================================
# PROPUESTA 1: DASHBOARD MODULAR CON PERFILES DE RIESGO
# =================================================================

async def apply_risk_profile_to_session(session, profile_name: str):
    """Helper function to apply risk profiles consistently across the system."""
    profiles_data = {
        "CONSERVADOR": {
            "max_leverage": 3,
            "default_leverage": 3,
            "max_capital_pct": 0.30,
            "atr_multiplier": 1.5,
            "rr_ratio": 1.2,
            "description": "Conservador: ≤3x máx, ATR 1.5x"
        },
        "NEXUS": {
            "max_leverage": 10,
            "default_leverage": 5,
            "max_capital_pct": 0.50,
            "atr_multiplier": 2.0,
            "rr_ratio": 1.5,
            "description": "Nexus: ≤10x dinámico, ATR 2.0x"
        },
        "RONIN": {
            "max_leverage": 20,
            "default_leverage": 20,
            "max_capital_pct": 0.20,
            "atr_multiplier": 2.5,
            "rr_ratio": 2.0,
            "description": "Ronin: ≤20x máx, ATR 2.5x"
        }
    }

    if profile_name not in profiles_data:
        return False

    profile_config = profiles_data[profile_name]

    # Apply profile settings consistently
    await session.update_config('max_leverage_allowed', profile_config['max_leverage'])
    await session.update_config('leverage', min(session.config.get('leverage', profile_config['default_leverage']),
                                               profile_config['max_leverage']))
    await session.update_config('max_capital_pct_allowed', profile_config['max_capital_pct'])
    await session.update_config('max_capital_pct', min(session.config.get('max_capital_pct', 0.25),
                                                     profile_config['max_capital_pct']))
    await session.update_config('atr_multiplier', profile_config['atr_multiplier'])
    await session.update_config('risk_reward_ratio', profile_config['rr_ratio'])
    await session.update_config('risk_profile', profile_name)

    # Always enable ATR for SL/TP
    await session.update_config('use_atr_for_sl_tp', True)

    return True


@router.callback_query(F.data.startswith("RISK|"))
async def handle_risk_profile_callback(callback: CallbackQuery, **kwargs):
    """Handle risk profile selection and application"""
    profile = callback.data.split("|")[1]
    session_manager = kwargs.get('session_manager')

    if not session_manager:
        await safe_answer(callback, "⚠️ Error interno")
        return

    session = session_manager.get_session(str(callback.message.chat.id))
    if not session:
        await safe_answer(callback, "⚠️ Sesión no encontrada")
        return

    # Apply risk profile
    try:
        # Define profile parameters
        profiles_data = {
            "CONSERVADOR": {
                "max_leverage": 3,
                "default_leverage": 3,
                "max_capital_pct": 0.30,
                "atr_multiplier": 1.5,
                "rr_ratio": 1.2,
                "description": "Conservador: ≤3x máx, ATR 1.5x"
            },
            "NEXUS": {
                "max_leverage": 10,
                "default_leverage": 5,
                "max_capital_pct": 0.50,
                "atr_multiplier": 2.0,
                "rr_ratio": 1.5,
                "description": "Nexus: ≤10x dinámico, ATR 2.0x"
            },
            "RONIN": {
                "max_leverage": 20,
                "default_leverage": 20,
                "max_capital_pct": 0.20,
                "atr_multiplier": 2.5,
                "rr_ratio": 2.0,
                "description": "Ronin: ≤20x máx, ATR 2.5x"
            }
        }

        if profile not in profiles_data:
            await safe_answer(callback, "⚠️ Perfil no válido")
            return

        profile_config = profiles_data[profile]

        # Apply profile settings using consistent helper
        success = await apply_risk_profile_to_session(session, profile)
        if not success:
            await safe_answer(callback, "⚠️ Error aplicando perfil")
            return

        # Get profile description
        descriptions = {
            "CONSERVADOR": "🛡️ CONSERVADOR: ≤3x máx, ATR 1.5x",
            "NEXUS": "🌌 NEXUS: ≤10x dinámico, ATR 2.0x",
            "RONIN": "⚔️ RONIN: ≤20x máx, ATR 2.5x"
        }

        await safe_answer(callback, f"✅ {descriptions.get(profile, 'Perfil aplicado')}")

        # Always enable ATR for SL/TP
        session.config['use_atr_for_sl_tp'] = True

        # Save session
        session_manager.save_sessions()

        await safe_answer(callback, f"✅ {profile_config['description']}")

        # Refresh config panel
        from handlers.config import cmd_config
        await cmd_config(callback.message, session_manager=session_manager, edit_message=True)

    except Exception as e:
        await safe_answer(callback, f"❌ Error aplicando perfil: {str(e)[:50]}")


@router.callback_query(F.data.startswith("MODULE|"))
async def handle_module_callback(callback: CallbackQuery, **kwargs):
    """Handle module navigation for Propuesta 1"""
    module = callback.data.split("|")[1]
    session_manager = kwargs.get('session_manager')

    if module == "DETAILED":
        # Ajustes detallados
        msg = (
            "⚖️ *CONFIGURACIÓN DETALLADA*\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "📊 **PERFIL ACTIVO**\n"
            "• Leverage máximo según perfil\n"
            "• Capital máximo según perfil\n"
            "• SL/TP: SIEMPRE por ATR dinámico\n\n"
            "🎚️ **AJUSTES FINOS**\n"
            "• Valores calculados dinámicamente\n"
            "• Nunca superan topes del perfil\n"
            "• ATR determina SL/TP óptimos"
        )

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⚖️ Configurar Leverage", callback_data="CFG|LEV_MENU")],
            [InlineKeyboardButton(text="💰 Configurar Capital", callback_data="CFG|MARGIN_MENU")],
            [InlineKeyboardButton(text="🎯 Ver Cálculos ATR", callback_data="INFO|ATR_CALC")],
            [InlineKeyboardButton(text="⬅️ Volver a Config", callback_data="CMD|config")]
        ])

    elif module == "AI":
        # IA & Automation
        msg = (
            "🧠 *CENTRO DE INTELIGENCIA*\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "🤖 **SISTEMAS DE IA ACTIVA**\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "• AI Filter: Filtra señales por sentimiento\n"
            "• ML Classifier: Predice dirección usando ML\n"
            "• Sentiment Analysis: Análisis Fear & Greed\n"
            "• ATR Integration: Cálculos dinámicos siempre\n\n"
            "🎛️ **CONTROLES RÁPIDOS**"
        )

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✨ Toggle AI Filter", callback_data="TOGGLE|AI_FILTER")],
            [InlineKeyboardButton(text="🧠 Toggle ML Mode", callback_data="TOGGLE|ML_MODE")],
            [InlineKeyboardButton(text="🎭 Toggle Sentiment", callback_data="TOGGLE|SENTIMENT")],
            [InlineKeyboardButton(text="🎯 Estado IA", callback_data="INFO|AI_STATUS")],
            [InlineKeyboardButton(text="⬅️ Volver a Config", callback_data="CMD|config")]
        ])

    elif module == "PROTECTIONS":
        # Protecciones
        msg = (
            "🛡️ *SISTEMA DE PROTECCIONES*\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "🔌 **PROTECCIONES ACTIVAS**\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "• Circuit Breaker: Detiene operaciones en crash\n"
            "• Portfolio Shield: Protege correlaciones\n"
            "• Emergency Stop: Parada manual de emergencia\n\n"
            "🎛️ **CONFIGURACIÓN**"
        )

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔌 Circuit Breaker", callback_data="TOGGLE|CIRCUIT_BREAKER")],
            [InlineKeyboardButton(text="🛡️ Portfolio Shield", callback_data="TOGGLE|SHIELD")],
            [InlineKeyboardButton(text="🚨 Emergency Stop", callback_data="TOGGLE|EMERGENCY")],
            [InlineKeyboardButton(text="⬅️ Volver a Config", callback_data="CMD|config")]
        ])

    elif module == "STRATEGIES":
        # Estrategias
        msg = (
            "📊 *ESTRATEGIAS & ACTivos*\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "🎛️ **CONFIGURACIÓN DE ESTRATEGIAS**\n"
            "• Motores de señales activas\n"
            "• Grupos de activos habilitados\n"
            "• Parámetros de cada estrategia\n\n"
            "📡 **GRUPOS DE ACTIVOS**\n"
            "• Exchanges disponibles\n"
            "• Símbolos por grupo\n"
            "• Configuración por grupo"
        )

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🎛️ Estrategias (Motor)", callback_data="CMD|strategies")],
            [InlineKeyboardButton(text="📡 Grupos y Activos", callback_data="CMD|assets")],
            [InlineKeyboardButton(text="⬅️ Volver a Config", callback_data="CMD|config")]
        ])

    else:
        await safe_answer(callback, "⚠️ Módulo no encontrado")
        return

    try:
        await callback.message.edit_text(msg, reply_markup=keyboard, parse_mode="Markdown")
    except Exception as e:
        await safe_answer(callback, f"Error: {str(e)[:50]}")


@router.callback_query(F.data.startswith("INFO|"))
async def handle_info_callback(callback: CallbackQuery, **kwargs):
    """Handle informational callbacks"""
    info_type = callback.data.split("|")[1]

    if info_type == "PROFILE":
        msg = (
            "🎯 *INFORMACIÓN DE PERFILES*\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "🛡️ **CONSERVADOR** (≤3x máx)\n"
            "• Leverage máximo: 3x\n"
            "• Capital máximo: 30%\n"
            "• ATR multiplier: 1.5x (SL conservador)\n"
            "• Risk/Reward: 1:1.2\n\n"
            "🌌 **NEXUS** (≤10x dinámico)\n"
            "• Leverage: 5-10x según condiciones\n"
            "• Capital máximo: 50%\n"
            "• ATR multiplier: 2.0x (SL equilibrado)\n"
            "• Risk/Reward: 1:1.5\n\n"
            "⚔️ **RONIN** (≤20x máx)\n"
            "• Leverage máximo: 20x\n"
            "• Capital máximo: 20%\n"
            "• ATR multiplier: 2.5x (SL amplio)\n"
            "• Risk/Reward: 1:2.0"
        )

    elif info_type == "ATR":
        msg = (
            "🎯 *SISTEMA ATR DINÁMICO*\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "📊 **CÓMO FUNCIONA**\n"
            "• ATR mide volatilidad real del mercado\n"
            "• SL = ATR × multiplier (según perfil)\n"
            "• TP = SL × risk/reward ratio\n"
            "• Se recalcula en cada operación\n\n"
            "🎛️ **MULTIPLIERS POR PERFIL**\n"
            "• 🛡️ Conservador: 1.5x (más cerca)\n"
            "• 🌌 Nexus: 2.0x (equilibrado)\n"
            "• ⚔️ Ronin: 2.5x (más amplio)\n\n"
            "✅ **VENTAJAS**\n"
            "• Stop loss adaptativo a volatilidad\n"
            "• Take profit basado en riesgo asumido\n"
            "• Funciona en cualquier condición de mercado"
        )

    elif info_type == "ATR_CALC":
        msg = (
            "🎯 *CÁLCULOS ATR DETALLADOS*\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "📈 **FÓRMULAS ACTIVAS**\n"
            "```\n"
            "ATR = Average True Range (14 periodos)\n"
            "SL = Precio_Entrada × (1 - ATR × Multiplier)\n"
            "TP = Precio_Entrada × (1 + ATR × Multiplier × RR_Ratio)\n"
            "```\n\n"
            "🎚️ **PARÁMETROS ACTUALES**\n"
            "• Periodo ATR: 14 velas\n"
            "• Timeframe: 4 horas\n"
            "• Multiplier: Según perfil de riesgo\n"
            "• RR Ratio: Según perfil de riesgo"
        )

    elif info_type == "AI_STATUS":
        msg = (
            "🧠 *ESTADO DE SISTEMAS IA*\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "✨ **AI FILTER**\n"
            "• Estado: ACTIVE\n"
            "• Función: Filtra señales por sentimiento\n"
            "• Datos: Fear & Greed Index\n\n"
            "🧠 **ML CLASSIFIER**\n"
            "• Estado: ACTIVE\n"
            "• Función: Predice dirección de mercado\n"
            "• Modelo: XGBoost con features técnicas\n\n"
            "🎭 **SENTIMENT ANALYSIS**\n"
            "• Estado: ACTIVE\n"
            "• Función: Análisis de sentimiento macro\n"
            "• Fuentes: Múltiples indicadores"
        )

    else:
        await safe_answer(callback, "⚠️ Información no encontrada")
        return

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Volver a Config", callback_data="CMD|config")]
    ])

    try:
        await callback.message.edit_text(msg, reply_markup=keyboard, parse_mode="Markdown")
    except Exception as e:
        await safe_answer(callback, f"Error mostrando info: {str(e)[:50]}")
