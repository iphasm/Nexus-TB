"""
Antigravity Bot - Async Entry Point
Main bot application using aiogram 3.x with native async/await

This replaces main.py for the async architecture migration.
"""

import asyncio
import os
import logging
from typing import Any, Awaitable, Callable, Dict

from aiogram import Bot, Dispatcher, BaseMiddleware
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import TelegramObject
from dotenv import load_dotenv

# Load Environment Variables
load_dotenv()

# --- CONFIGURATION ---
# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Suppress noisy loggers
logging.getLogger('httpx').setLevel(logging.WARNING)
logging.getLogger('aiogram').setLevel(logging.INFO)

# --- CONFIGURATION ---
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_ADMIN_ID = os.getenv('TELEGRAM_ADMIN_ID')

# --- DIAGNOSTICS: LOG ENV VARS (Masked) ---
# Debugging Railway Env Var Issues
_vars_to_log = ['TELEGRAM_ADMIN_ID', 'BINANCE_API_KEY', 'BINANCE_SECRET', 'OPENAI_API_KEY', 'PROXY_URL', 'APCA_API_KEY_ID', 'APCA_API_SECRET_KEY', 'APCA_API_BASE_URL']
logger.info("🔧 ENVIRONMENT VARIABLE CHECK:")
for v in _vars_to_log:
    val = os.getenv(v, '').strip().strip("'\"")
    status = "✅ FOUND" if val else "❌ MISSING"
    masked = f"{val[:4]}...{val[-4:]}" if val and len(val) > 8 else "N/A"
    if v == 'PROXY_URL' and val: masked = "CONFIGURED"
    logger.info(f"   - {v}: {status} [{masked}]")
# ------------------------------------------


# --- ASSET CONFIGURATION (Centralized) ---
from config import ASSET_GROUPS, GROUP_CONFIG, get_all_assets, get_display_name


# --- MIDDLEWARE ---
class SessionMiddleware(BaseMiddleware):
    """
    Injects session_manager into handler kwargs.
    This allows handlers to access session_manager without global state.
    """
    
    def __init__(self, session_manager):
        self.session_manager = session_manager
        super().__init__()
    
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        data['session_manager'] = self.session_manager
        return await handler(event, data)


# --- GATEKEEPER MIDDLEWARE (Auth) ---
from utils.db import get_user_role

class GatekeeperMiddleware(BaseMiddleware):
    """
    Enforces subscription/admin access for every message.
    """
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        # Only check Messages (callbacks usually safe if message was ok, but ideally check both)
        from aiogram.types import Message, CallbackQuery
        user = None
        chat_id = None
        
        if isinstance(event, Message):
            user = event.from_user
            chat_id = str(event.chat.id)
        elif isinstance(event, CallbackQuery):
            user = event.from_user
            chat_id = str(event.message.chat.id)
            
        if user and chat_id:
            # Check DB / ENV
            allowed, role = get_user_role(str(user.id))
            
            if not allowed:
                # Silent blocking to avoid spam, or one-time warning?
                # Let's just ignore for now or print log
                print(f"⛔ Access Denied: {user.id} ({user.first_name}) - Role: {role}")
                return # Block execution
                
            # Optional: Inject role into data handler
            data['user_role'] = role
            
        return await handler(event, data)


# --- SIGNAL DISPATCH ---

# Global Personality Manager instance
from utils.personalities import PersonalityManager
personality_manager = PersonalityManager()

# === DYNAMIC COOLDOWN MANAGER ===
# Intelligent per-symbol cooldown with frequency and volatility tracking
from utils.cooldown_manager import DynamicCooldownManager
import time

cooldown_manager = DynamicCooldownManager(default_cooldown=300)  # 5 min default

async def dispatch_quantum_signal(bot: Bot, signal, session_manager):
    """
    Dispatch trading signals from QuantumEngine to all active sessions.
    This runs in the same event loop as the bot.
    Includes DYNAMIC TEMPORAL FILTER to prevent spam.
    """
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    
    symbol = signal.symbol
    action = signal.action.upper()  # BUY, SELL, HOLD
    confidence = getattr(signal, 'confidence', 0.5)
    strategy = getattr(signal, 'strategy', 'UNKNOWN')
    price = getattr(signal, 'price', 0)
    
    # Skip non-actionable signals
    if action in ['HOLD', 'WAIT', 'EXIT_ALL']:
        return
    
    # === TEMPORAL FILTER: Skip if on cooldown ===
    if cooldown_manager.is_on_cooldown(symbol):
        logger.debug(f"⏳ Signal for {symbol} skipped (cooldown active)")
        return
    
    # Mark as alerted with ATR if available
    atr = getattr(signal, 'atr', None)
    cooldown_manager.set_cooldown(symbol, atr=atr)
    
    # Map action to side
    side = 'LONG' if action == 'BUY' else 'SHORT'
    reason = f"{strategy} (C: {confidence:.0%})"
    
    logger.info(f"📡 Signal: {action} {symbol} (Conf: {confidence:.2f}, Strategy: {strategy})")
    
    # Dispatch to all sessions
    for session in session_manager.get_all_sessions():
        try:
            mode = session.mode
            p_key = session.config.get('personality', 'NEXUS')
            
            # Calculate SL/TP preview
            sl_prev, tp_prev = session.get_trade_preview(symbol, side, price) if price else (0, 0)
            
            if mode == 'WATCHER':
                # Use personality message
                if side == 'LONG':
                    msg = personality_manager.get_message(
                        p_key, 'TRADE_LONG',
                        asset=symbol, price=price, reason=reason,
                        tp=tp_prev, sl=sl_prev
                    )
                else:
                    msg = personality_manager.get_message(
                        p_key, 'TRADE_SHORT',
                        asset=symbol, price=price, reason=reason,
                        tp=tp_prev, sl=sl_prev
                    )
                await bot.send_message(session.chat_id, msg, parse_mode="Markdown")
                
            elif mode == 'COPILOT':
                # Send proposal with buttons
                keyboard = InlineKeyboardMarkup(inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="✅ Aceptar",
                            callback_data=f"TRADE|ACCEPT|{symbol}|{side}"
                        ),
                        InlineKeyboardButton(
                            text="❌ Rechazar",
                            callback_data=f"TRADE|REJECT|{symbol}|{side}"
                        )
                    ]
                ])
                
                if side == 'LONG':
                    msg = personality_manager.get_message(
                        p_key, 'TRADE_LONG',
                        asset=symbol, price=price, reason=reason,
                        tp=tp_prev, sl=sl_prev
                    )
                else:
                    msg = personality_manager.get_message(
                        p_key, 'TRADE_SHORT',
                        asset=symbol, price=price, reason=reason,
                        tp=tp_prev, sl=sl_prev
                    )
                await bot.send_message(
                    session.chat_id, msg, 
                    reply_markup=keyboard, 
                    parse_mode="Markdown"
                )
                
            elif mode == 'PILOT':
                # Auto-execute (no "entering pilot mode" message)
                if side == 'LONG':
                    success, result = await session.execute_long_position(symbol)
                else:
                    success, result = await session.execute_short_position(symbol)
                
                if success:
                    await bot.send_message(
                        session.chat_id,
                        f"✅ *{side} EJECUTADO*\n{result}",
                        parse_mode="Markdown"
                    )
                    
                    # Check circuit breaker after trade
                    cb_triggered, cb_msg = await session.check_circuit_breaker()
                    if cb_triggered:
                        cb_alert = personality_manager.get_message(p_key, 'CB_TRIGGER')
                        await bot.send_message(session.chat_id, cb_alert, parse_mode="Markdown")
                else:
                    await bot.send_message(
                        session.chat_id,
                        f"❌ Error: {result}",
                        parse_mode="Markdown"
                    )
                    
        except Exception as e:
            logger.error(f"Signal dispatch error for {session.chat_id}: {e}")


# --- MAIN APPLICATION ---
async def main():
    """Main entry point for the async bot."""
    
    if not TELEGRAM_TOKEN:
        logger.error("❌ TELEGRAM_TOKEN not found in environment!")
        return
    
    # 1. Create Bot Instance
    bot = Bot(
        token=TELEGRAM_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN)
    )
    
    # 2. Create Dispatcher
    dp = Dispatcher()
    
    # 3. Initialize Database (PostgreSQL)
    try:
        from utils.db import init_db
        init_db()
    except Exception as e:
        logger.warning(f"DB Init skipped: {e}")
    
    # 4. Initialize Session Manager
    from utils.trading_manager import AsyncSessionManager
    session_manager = AsyncSessionManager()
    await session_manager.load_sessions()
            
    # 4. Register Middleware
    dp.message.middleware(SessionMiddleware(session_manager))
    dp.callback_query.middleware(SessionMiddleware(session_manager))
    
    # 5. Register Routers
    from handlers.commands import router as commands_router
    from handlers.trading import router as trading_router
    from handlers.config import router as config_router
    from handlers.callbacks import router as callbacks_router
    from handlers.admin import router as admin_router
    
    dp.include_router(admin_router)
    dp.include_router(commands_router)
    dp.include_router(config_router)
    dp.include_router(trading_router)
    dp.include_router(callbacks_router)
    
    # 5. Register Middleware
    # Session middleware for all handlers
    dp.update.middleware(SessionMiddleware(session_manager))
    dp.update.middleware(GatekeeperMiddleware())
    
    logger.info("✅ Routers and Middleware registered.")

    # 6. Initialize Quantum Engine (Optional)
    engine_task = None
    USE_QUANTUM_ENGINE = os.getenv('USE_QUANTUM_ENGINE', 'true').lower() == 'true'
    
    if USE_QUANTUM_ENGINE:
        try:
            from antigravity_quantum.core.engine import QuantumEngine
            
            engine = QuantumEngine(assets=get_all_assets())
            
            # Set callback for signal dispatch
            async def on_signal(signal):
                await dispatch_quantum_signal(bot, signal, session_manager)
            
            engine.set_callback(on_signal)
            
            logger.info("🌌 Quantum Engine initialized and ready.")
            
            # Create engine task (will run concurrently with bot)
            engine_task = asyncio.create_task(engine.run())
            
        except Exception as e:
            logger.warning(f"⚠️ Quantum Engine init failed: {e}")

    # 7. Start Shark Sentinel (Black Swan Defense)
    try:
        from antigravity_quantum.strategies.shark_mode import SharkSentinel
        
        def notify_send(msg):
             # Broadcast alert to all active sessions
             for chat_id in session_manager.get_active_chat_ids():
                 asyncio.create_task(bot.send_message(chat_id, msg, parse_mode='Markdown'))

        # Check function for Sentinel
        def is_shark_enabled():
             from antigravity_quantum.config import ENABLED_STRATEGIES
             return ENABLED_STRATEGIES.get('BLACK_SWAN', True) or ENABLED_STRATEGIES.get('SHARK', False)

        sentinel = SharkSentinel(
            session_manager=session_manager,
            notify_callback=notify_send,
            enabled_check_callback=is_shark_enabled
        )
        sentinel.start()
        logger.info("🦈 Shark Sentinel (Black Swan Defense) STARTED.")
        
    except Exception as e:
        logger.error(f"❌ Failed to start Shark Sentinel: {e}")

    # 8. Startup Message
    logger.info("🚀 Antigravity Bot (Async) starting...")
    
    raw_admin_ids = os.getenv('TELEGRAM_ADMIN_ID', '').strip("'\" ")
    if raw_admin_ids:
        admin_ids = [aid.strip() for aid in raw_admin_ids.split(',') if aid.strip()]
        
        for admin_id in admin_ids:
            try:
                await bot.send_message(
                    admin_id,
                    "🟢 *Antigravity Bot Online*\n\n"
                    f"Sesiones: {len(session_manager.sessions)}\n"
                    f"Activos: {len(get_all_assets())}\n"
                    f"Quantum: {'✅' if USE_QUANTUM_ENGINE else '❌'}",
                    parse_mode="Markdown"
                )
            except Exception as e:
                logger.warning(f"Could not send startup message to {admin_id}: {e}")
    
    # 8. Start Polling
    try:
        await dp.start_polling(bot)
    finally:
        # Cleanup
        logger.info("🛑 Shutting down...")
        
        if engine_task:
            engine_task.cancel()
            try:
                await engine_task
            except asyncio.CancelledError:
                pass
        
        await session_manager.close_all()
        await bot.session.close()


if __name__ == "__main__":
    # Windows-specific event loop policy
    import platform
    if platform.system() == 'Windows':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    asyncio.run(main())
