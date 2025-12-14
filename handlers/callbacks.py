"""
Antigravity Bot - Callback Query Handlers
Handles all inline keyboard button presses
EXACT REPLICA of main.py interface
"""

from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

router = Router(name="callbacks")


@router.callback_query(F.data.startswith("CMD|"))
async def handle_cmd_callback(callback: CallbackQuery, **kwargs):
    """Handle command shortcuts from buttons - dispatches to actual handlers"""
    cmd = callback.data.split("|")[1]
    session_manager = kwargs.get('session_manager')
    
    await callback.answer()
    
    # Status
    if cmd == "status":
        from handlers.commands import cmd_status
        # Create a fake message-like call
        await cmd_status(callback.message, session_manager=session_manager)
    
    # Wallet
    elif cmd == "wallet":
        from handlers.commands import cmd_wallet
        await cmd_wallet(callback.message, session_manager=session_manager)
    
    # Mode switches
    elif cmd == "watcher":
        session = session_manager.get_session(str(callback.message.chat.id)) if session_manager else None
        if session:
            session.set_mode('WATCHER')
            await session_manager.save_sessions()
            await callback.message.answer("👁️ *Modo WATCHER Activado*", parse_mode="Markdown")
        else:
            await callback.message.answer("⚠️ Sin sesión activa.")
    
    elif cmd == "copilot":
        session = session_manager.get_session(str(callback.message.chat.id)) if session_manager else None
        if session:
            session.set_mode('COPILOT')
            await session_manager.save_sessions()
            await callback.message.answer("🦾 *Modo COPILOT Activado*", parse_mode="Markdown")
        else:
            await callback.message.answer("⚠️ Sin sesión activa.")
    
    elif cmd == "pilot":
        session = session_manager.get_session(str(callback.message.chat.id)) if session_manager else None
        if session:
            session.set_mode('PILOT')
            await session_manager.save_sessions()
            await callback.message.answer("🤖 *Modo PILOT Activado*\n⚠️ _Trading automático habilitado._", parse_mode="Markdown")
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
    
    elif cmd == "sniper":
        from handlers.commands import cmd_sniper
        await cmd_sniper(callback.message, session_manager=session_manager)
        
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
    
    await callback.answer()
    
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
            ]
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
            ]
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
    """Toggle strategy on/off and persist to DB"""
    strategy = callback.data.split("|")[1]
    
    try:
        from antigravity_quantum.config import ENABLED_STRATEGIES, DISABLED_ASSETS, GROUP_CONFIG
        from utils.db import save_bot_state
        
        current = ENABLED_STRATEGIES.get(strategy, True)
        ENABLED_STRATEGIES[strategy] = not current
        
        # PERSIST TO DB
        save_bot_state(ENABLED_STRATEGIES, GROUP_CONFIG, list(DISABLED_ASSETS))
        
        new_state = "✅ ACTIVADO" if ENABLED_STRATEGIES[strategy] else "❌ DESACTIVADO"
        await callback.answer(f"{strategy}: {new_state}")
        
        # Rebuild keyboard
        t_state = "✅" if ENABLED_STRATEGIES.get('TREND', True) else "❌"
        s_state = "✅" if ENABLED_STRATEGIES.get('SCALPING', True) else "❌"
        g_state = "✅" if ENABLED_STRATEGIES.get('GRID', True) else "❌"
        m_state = "✅" if ENABLED_STRATEGIES.get('MEAN_REVERSION', True) else "❌"
        bs_state = "✅" if ENABLED_STRATEGIES.get('BLACK_SWAN', True) else "❌"
        sh_state = "✅" if ENABLED_STRATEGIES.get('SHARK', True) else "❌"
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=f"📈 Trend (BTC): {t_state}", callback_data="TOGGLE|TREND")],
            [InlineKeyboardButton(text=f"🦢 Black Swan: {bs_state}", callback_data="TOGGLE|BLACK_SWAN")],
            [InlineKeyboardButton(text=f"🦈 Shark Mode: {sh_state}", callback_data="TOGGLE|SHARK")],
            [
                InlineKeyboardButton(text=f"⚡ Scalp: {s_state}", callback_data="TOGGLE|SCALPING"),
                InlineKeyboardButton(text=f"🕸️ Grid: {g_state}", callback_data="TOGGLE|GRID")
            ],
            [InlineKeyboardButton(text=f"📉 Mean Rev: {m_state}", callback_data="TOGGLE|MEAN_REVERSION")]
        ])
        
        await callback.message.edit_reply_markup(reply_markup=keyboard)
        
    except Exception as e:
        await callback.answer(f"Error: {e}", show_alert=True)


@router.callback_query(F.data.startswith("TOGGLEGRP|"))
async def handle_group_toggle(callback: CallbackQuery, **kwargs):
    """Toggle asset group on/off"""
    group = callback.data.split("|")[1]
    
    try:
        from antigravity_quantum.config import GROUP_CONFIG, ENABLED_STRATEGIES, DISABLED_ASSETS
        from utils.db import save_bot_state
        
        current = GROUP_CONFIG.get(group, True)
        GROUP_CONFIG[group] = not current
        
        # Save to DB
        save_bot_state(ENABLED_STRATEGIES, GROUP_CONFIG, list(DISABLED_ASSETS))
        
        new_state = "✅ ACTIVADO" if GROUP_CONFIG[group] else "❌ DESACTIVADO"
        await callback.answer(f"{group}: {new_state}")
        
        # Rebuild buttons + Volver
        buttons = [
            [InlineKeyboardButton(
                text=f"{'✅' if enabled else '❌'} {grp}",
                callback_data=f"TOGGLEGRP|{grp}"
            )] for grp, enabled in GROUP_CONFIG.items()
        ]
        buttons.append([InlineKeyboardButton(text="⬅️ Volver", callback_data="CMD|config")])
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
        
        await callback.message.edit_reply_markup(reply_markup=keyboard)
        
    except Exception as e:
        await callback.answer(f"Error: {e}", show_alert=True)


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
            await callback.answer(f"Personalidad: {personality}")
            await callback.message.edit_text(f"🧠 Personalidad cambiada a *{personality}*", parse_mode="Markdown")
            return
    
    await callback.answer("⚠️ Sin sesión activa", show_alert=True)


@router.callback_query(F.data.startswith("TRADE|"))
async def handle_trade_proposal(callback: CallbackQuery, **kwargs):
    """Handle Copilot trade proposals (Accept/Reject) - Auto-delete proposal"""
    session_manager = kwargs.get('session_manager')
    
    parts = callback.data.split("|")
    
    if len(parts) < 4:
        await callback.answer("❌ Datos inválidos", show_alert=True)
        return
    
    action = parts[1]
    symbol = parts[2]
    side = parts[3]
    
    await callback.answer()
    
    # Delete the proposal message
    try:
        await callback.message.delete()
    except:
        pass  # Ignore if already deleted
    
    if action == "REJECT":
        await callback.message.answer(
            f"❌ *Propuesta Rechazada*\n"
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
            success, msg = await session.execute_long_position(symbol)
        else:
            success, msg = await session.execute_short_position(symbol)
        
        if success:
            await status_msg.edit_text(
                f"✅ *{side} EJECUTADO*\n{msg}",
                parse_mode="Markdown"
            )
        else:
            await status_msg.edit_text(f"❌ Error: {msg}")
            
    except Exception as e:
        await status_msg.edit_text(f"❌ Error crítico: {e}")


@router.callback_query(F.data.startswith("ASSETS|"))
async def handle_assets_menu(callback: CallbackQuery, **kwargs):
    """Handle asset module selection"""
    module = callback.data.split("|")[1]
    
    await callback.answer()
    
    # Build asset list for selected module
    try:
        from antigravity_quantum.config import SHARK_TARGETS, SCALPING_ASSETS, GRID_ASSETS, MEAN_REV_ASSETS, DISABLED_ASSETS
        
        if module == "SHARK":
            assets = SHARK_TARGETS
            title = "🦈 SHARK TARGETS"
        elif module == "SCALPING":
            assets = SCALPING_ASSETS
            title = "⚡ SCALPING ASSETS"
        elif module == "GRID":
            assets = GRID_ASSETS
            title = "🕸️ GRID ASSETS"
        elif module == "MEANREV":
            assets = MEAN_REV_ASSETS
            title = "📉 MEAN REVERSION"
        else:
            # Global scanner - Import from root config to ensure all groups are present
            from config import ASSET_GROUPS
            assets = []
            for group in ASSET_GROUPS.values():
                assets.extend(group)
            title = "📡 SCANNER GLOBAL"
        
        # Build keyboard with toggle buttons
        buttons = []
        for asset in assets[:80]:  # Limit increased to 80 (covers Crypto + Stocks + Commodities)
            is_disabled = asset in DISABLED_ASSETS
            icon = "❌" if is_disabled else "✅"
            buttons.append([InlineKeyboardButton(
                text=f"{icon} {asset}",
                callback_data=f"ASSET_TOGGLE|{module}|{asset}"
            )])
        
        buttons.append([InlineKeyboardButton(text="⬅️ Volver", callback_data="CMD|assets")])
        
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
    
    try:
        from antigravity_quantum.config import DISABLED_ASSETS, ENABLED_STRATEGIES, GROUP_CONFIG
        from utils.db import save_bot_state
        
        if asset in DISABLED_ASSETS:
            DISABLED_ASSETS.remove(asset)
            await callback.answer(f"✅ {asset} activado")
        else:
            DISABLED_ASSETS.add(asset)
            await callback.answer(f"❌ {asset} desactivado")
        
        # Save state to DB
        save_bot_state(ENABLED_STRATEGIES, GROUP_CONFIG, list(DISABLED_ASSETS))
        
        # Refresh menu
        await handle_assets_menu(callback, **kwargs)
        
    except Exception as e:
        await callback.answer(f"Error: {e}", show_alert=True)


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
            InlineKeyboardButton(text="🏦 FOMC / FED", callback_data="CMD|fomc")
        ],
        [InlineKeyboardButton(text="🎯 Sniper Scan", callback_data="CMD|sniper")],
        [InlineKeyboardButton(text="🔙 Menú Principal", callback_data="CMD|start")]
    ])
    
    await callback.message.edit_text(msg, reply_markup=keyboard, parse_mode="Markdown")
