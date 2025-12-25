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
    
    # Personality
    elif cmd == "personality":
        from handlers.config import cmd_personality
        await cmd_personality(callback.message, session_manager=session_manager)
    
    # Strategies
    elif cmd == "strategies":
        from handlers.config import cmd_strategies
        await cmd_strategies(callback.message, session_manager=session_manager, edit_message=True)
    
    # Toggle Group
    elif cmd == "togglegroup":
        from handlers.config import cmd_togglegroup
        await cmd_togglegroup(callback.message, session_manager=session_manager, edit_message=True)
    
    # Assets
    elif cmd == "assets":
        from handlers.config import cmd_assets
        await cmd_assets(callback.message, session_manager=session_manager, edit_message=True)

    # Mode presets (Ronin/Guardian/Quantum)
    elif cmd.startswith("mode_"):
        preset = cmd.split("_")[1]
        session = session_manager.get_session(str(callback.message.chat.id)) if session_manager else None
        
        if not session:
            await callback.message.answer("⚠️ Sin sesión activa.")
            return
        
        # Apply preset configurations
        if preset == "RONIN":
            await session.update_config('leverage', 10)
            await session.update_config('max_capital_pct', 0.15)
            await session.update_config('atr_multiplier', 1.5)
            msg = "⚔️ *Modo RONIN Activado*\n\n• Leverage: 10x\n• Margen: 15%\n• SL Ajustado: 1.5x ATR\n\n_Perfil agresivo para traders experimentados._"
        elif preset == "GUARDIAN":
            await session.update_config('leverage', 3)
            await session.update_config('max_capital_pct', 0.05)
            await session.update_config('atr_multiplier', 3.0)
            msg = "🛡️ *Modo GUARDIAN Activado*\n\n• Leverage: 3x\n• Margen: 5%\n• SL Amplio: 3x ATR\n\n_Perfil conservador para proteger capital._"
        elif preset == "QUANTUM":
            await session.update_config('leverage', 5)
            await session.update_config('max_capital_pct', 0.10)
            await session.update_config('atr_multiplier', 2.0)
            msg = "🌌 *Modo QUANTUM Activado*\n\n• Leverage: 5x\n• Margen: 10%\n• SL Balanceado: 2x ATR\n\n_Perfil equilibrado recomendado._"
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
    
        
    elif cmd == "dashboard":
        from handlers.commands import cmd_dashboard
        await cmd_dashboard(callback.message, session_manager=session_manager)
        
    elif cmd == "price":
        from handlers.commands import cmd_price
        await cmd_price(callback.message, session_manager=session_manager)
        
    elif cmd == "fomc":
        from handlers.commands import cmd_fomc
        await cmd_fomc(callback.message, session_manager=session_manager)
        
    elif cmd == "start":
        from handlers.commands import cmd_start
        await cmd_start(callback.message, session_manager=session_manager, edit_message=True)
    
    else:
        await callback.message.answer(f"⚠️ Comando no reconocido: {cmd}")


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
        
        # Rebuild keyboard
        strategies = session.config.get('strategies', {})
        t_state = "✅" if strategies.get('TREND', True) else "❌"
        s_state = "✅" if strategies.get('SCALPING', True) else "❌"
        g_state = "✅" if strategies.get('GRID', True) else "❌"
        m_state = "✅" if strategies.get('MEAN_REVERSION', True) else "❌"
        bs_state = "✅" if strategies.get('BLACK_SWAN', True) else "❌"
        sh_state = "✅" if strategies.get('SHARK', False) else "❌"
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=f"📈 Trend (BTC): {t_state}", callback_data="TOGGLE|TREND")],
            [InlineKeyboardButton(text=f"🦢 Black Swan: {bs_state}", callback_data="TOGGLE|BLACK_SWAN")],
            [InlineKeyboardButton(text=f"🦈 Shark Mode: {sh_state}", callback_data="TOGGLE|SHARK")],
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
    """Toggle asset group on/off"""
    group = callback.data.split("|")[1]
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
        await safe_answer(callback, f"{group}: {new_state}")
        
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
    """Handle asset module selection"""
    module = callback.data.split("|")[1]
    session_manager = kwargs.get('session_manager')
    
    await safe_answer(callback)
    
    # Build asset list for selected module
    try:
        from system_directive import SHARK_TARGETS, DISABLED_ASSETS
        
        if module == "SHARK":
            assets = SHARK_TARGETS
            title = "🦈 SHARK TARGETS"
        else:
            # Global scanner - Import from root config to ensure all groups are present
            from system_directive import ASSET_GROUPS
            assets = []
            for group in ASSET_GROUPS.values():
                assets.extend(group)
            title = "📡 SCANNER GLOBAL"
        
        # Build keyboard with toggle buttons
        buttons = []
        if not session_manager:
             await callback.message.edit_text("⚠️ Error interno")
             return
             
        session = session_manager.get_session(str(callback.message.chat.id))
        is_disabled = False
        
        for asset in assets[:80]:
            if session:
                is_disabled = session.is_asset_disabled(asset)
            else:
                 is_disabled = asset in DISABLED_ASSETS
                 
            icon = "❌" if is_disabled else "✅"
            buttons.append([InlineKeyboardButton(
                text=f"{icon} {asset}",
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
        
        # ALSO update GLOBAL DISABLED_ASSETS (used by QuantumEngine)
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

