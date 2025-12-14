"""
Antigravity Bot - Callback Query Handlers
Handles all inline keyboard button presses
"""

from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

router = Router(name="callbacks")


@router.callback_query(F.data.startswith("CMD|"))
async def handle_cmd_callback(callback: CallbackQuery, **kwargs):
    """Handle command shortcuts from buttons"""
    cmd = callback.data.split("|")[1]
    
    # Acknowledge the callback
    await callback.answer()
    
    # Dispatch to appropriate handler
    if cmd == "strategies":
        await callback.message.answer("🎛️ Usa el comando `/strategies` directamente.", parse_mode="Markdown")
    elif cmd == "togglegroup":
        await callback.message.answer("📡 Usa el comando `/togglegroup` directamente.", parse_mode="Markdown")
    elif cmd == "assets":
        await callback.message.answer("🪙 Usa el comando `/assets` directamente.", parse_mode="Markdown")
    elif cmd == "personality":
        await callback.message.answer("🧠 Usa el comando `/personality` directamente.", parse_mode="Markdown")


@router.callback_query(F.data.startswith("CFG|"))
async def handle_config_callback(callback: CallbackQuery, **kwargs):
    """Handle configuration changes"""
    session_manager = kwargs.get('session_manager')
    
    parts = callback.data.split("|")
    action = parts[1]
    
    await callback.answer()
    
    if action == "LEV_MENU":
        # Show leverage selection
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
        # Show margin selection
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
        # Set leverage value
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
            await callback.message.edit_text(f"✅ Apalancamiento: *{value}x* (sesión temporal)", parse_mode="Markdown")
            
    elif action == "MARGIN" and len(parts) >= 3:
        # Set margin percentage
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
            await callback.message.edit_text(f"✅ Margen: *{value}%* (sesión temporal)", parse_mode="Markdown")


@router.callback_query(F.data.startswith("TOGGLE|"))
async def handle_strategy_toggle(callback: CallbackQuery, **kwargs):
    """Toggle strategy on/off"""
    strategy = callback.data.split("|")[1]
    
    try:
        from antigravity_quantum.config import ENABLED_STRATEGIES
        
        # Toggle
        current = ENABLED_STRATEGIES.get(strategy, True)
        ENABLED_STRATEGIES[strategy] = not current
        
        new_state = "✅ ACTIVADO" if ENABLED_STRATEGIES[strategy] else "❌ DESACTIVADO"
        await callback.answer(f"{strategy}: {new_state}")
        
        # Rebuild keyboard with updated states
        s_state = "✅" if ENABLED_STRATEGIES.get('SCALPING', True) else "❌"
        g_state = "✅" if ENABLED_STRATEGIES.get('GRID', True) else "❌"
        m_state = "✅" if ENABLED_STRATEGIES.get('MEAN_REVERSION', True) else "❌"
        sh_state = "✅" if ENABLED_STRATEGIES.get('SHARK', True) else "❌"
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=f"⚡ Scalping: {s_state}", callback_data="TOGGLE|SCALPING")],
            [InlineKeyboardButton(text=f"🕸️ Grid: {g_state}", callback_data="TOGGLE|GRID")],
            [InlineKeyboardButton(text=f"📉 Mean Rev: {m_state}", callback_data="TOGGLE|MEAN_REVERSION")],
            [InlineKeyboardButton(text=f"🦈 Shark Mode: {sh_state}", callback_data="TOGGLE|SHARK")]
        ])
        
        await callback.message.edit_reply_markup(reply_markup=keyboard)
        
    except Exception as e:
        await callback.answer(f"Error: {e}", show_alert=True)


@router.callback_query(F.data.startswith("TOGGLEGRP|"))
async def handle_group_toggle(callback: CallbackQuery, **kwargs):
    """Toggle asset group on/off"""
    group = callback.data.split("|")[1]
    
    # Import mutable config
    from handlers.commands import GROUP_CONFIG
    
    # Toggle
    current = GROUP_CONFIG.get(group, True)
    GROUP_CONFIG[group] = not current
    
    new_state = "✅ ACTIVADO" if GROUP_CONFIG[group] else "❌ DESACTIVADO"
    await callback.answer(f"{group}: {new_state}")
    
    # Rebuild keyboard
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=f"{'✅' if enabled else '❌'} {grp}",
            callback_data=f"TOGGLEGRP|{grp}"
        )] for grp, enabled in GROUP_CONFIG.items()
    ])
    
    await callback.message.edit_reply_markup(reply_markup=keyboard)


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
    """Handle Copilot trade proposals (Accept/Reject)"""
    session_manager = kwargs.get('session_manager')
    
    parts = callback.data.split("|")
    # Format: TRADE|ACTION|SYMBOL|SIDE
    # e.g., TRADE|ACCEPT|BTCUSDT|LONG or TRADE|REJECT|ETHUSDT|SHORT
    
    if len(parts) < 4:
        await callback.answer("❌ Datos inválidos", show_alert=True)
        return
    
    action = parts[1]  # ACCEPT or REJECT
    symbol = parts[2]
    side = parts[3]    # LONG or SHORT
    
    await callback.answer()
    
    if action == "REJECT":
        await callback.message.edit_text(
            f"❌ *Propuesta Rechazada*\n"
            f"Operación {side} en {symbol} cancelada.",
            parse_mode="Markdown"
        )
        return
    
    # ACCEPT - Execute trade
    if not session_manager:
        await callback.message.edit_text("⚠️ Error: SessionManager no disponible.")
        return
    
    session = session_manager.get_session(str(callback.message.chat.id))
    if not session:
        await callback.message.edit_text("⚠️ No tienes sesión activa. Usa /set\\_keys.")
        return
    
    await callback.message.edit_text(f"⏳ Ejecutando {side} en {symbol}...")
    
    try:
        if side == "LONG":
            success, msg = await session.execute_long_position(symbol)
        else:
            success, msg = await session.execute_short_position(symbol)
        
        if success:
            await callback.message.edit_text(
                f"✅ *{side} EJECUTADO*\n{msg}",
                parse_mode="Markdown"
            )
        else:
            await callback.message.edit_text(f"❌ Error: {msg}")
            
    except Exception as e:
        await callback.message.edit_text(f"❌ Error crítico: {e}")


@router.callback_query(F.data.startswith("ASSETS|"))
async def handle_assets_menu(callback: CallbackQuery, **kwargs):
    """Handle asset module selection"""
    module = callback.data.split("|")[1]
    
    await callback.answer()
    
    # TODO: Implement asset list per module
    # For now, show placeholder
    await callback.message.edit_text(
        f"📦 *Módulo: {module}*\n\n"
        "Funcionalidad en desarrollo...\n"
        "Usa `/config` para volver al menú principal.",
        parse_mode="Markdown"
    )
