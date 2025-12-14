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
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_ADMIN_ID = os.getenv('TELEGRAM_ADMIN_ID')

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Suppress noisy loggers
logging.getLogger('httpx').setLevel(logging.WARNING)
logging.getLogger('aiogram').setLevel(logging.INFO)


# --- ASSET CONFIGURATION ---
ASSET_GROUPS = {
    'CRYPTO': [
        'BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'SOLUSDT', 'ADAUSDT', 'XRPUSDT', 
        'AVAXUSDT', 'LTCUSDT', 'DOTUSDT', 'MATICUSDT', 'LINKUSDT', 
        'NEARUSDT', 'ATOMUSDT', 'ICPUSDT', 'BCHUSDT',
        'WIFUSDT', '1000PEPEUSDT', 'DOGEUSDT', 'SHIBUSDT', 'SUIUSDT', 
        'RENDERUSDT', 'FETUSDT', 'INJUSDT', 'FTMUSDT', 'SEIUSDT',
        'BONKUSDT', 'FLOKIUSDT', 'TRBUSDT', 'ZECUSDT', 'EOSUSDT',
        'UNIUSDT', 'AAVEUSDT', 'XLMUSDT', 'CRVUSDT'
    ],
    'STOCKS': ['TSLA', 'NVDA', 'MSFT', 'AAPL', 'AMD'],
    'COMMODITY': ['GLD', 'USO', 'SLV', 'CPER', 'UNG']
}


def get_all_assets():
    """Get flat list of all tradeable assets."""
    assets = []
    for group in ASSET_GROUPS.values():
        assets.extend(group)
    return list(set(assets))


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


# --- SIGNAL DISPATCH ---
async def dispatch_quantum_signal(bot: Bot, signal, session_manager):
    """
    Dispatch trading signals from QuantumEngine to all active sessions.
    This runs in the same event loop as the bot.
    """
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    
    symbol = signal.symbol
    action = signal.action.upper()  # BUY, SELL, HOLD
    confidence = getattr(signal, 'confidence', 0.5)
    strategy = getattr(signal, 'strategy', 'UNKNOWN')
    
    # Skip non-actionable signals
    if action in ['HOLD', 'WAIT', 'EXIT_ALL']:
        return
    
    # Map action to side
    side = 'LONG' if action == 'BUY' else 'SHORT'
    
    logger.info(f"📡 Signal: {action} {symbol} (Conf: {confidence:.2f}, Strategy: {strategy})")
    
    # Dispatch to all sessions
    for session in session_manager.get_all_sessions():
        try:
            mode = session.mode
            
            if mode == 'WATCHER':
                # Just send alert
                msg = (
                    f"📡 *SEÑAL DETECTADA*\n\n"
                    f"Activo: `{symbol}`\n"
                    f"Acción: *{action}*\n"
                    f"Confianza: {confidence:.0%}\n"
                    f"Estrategia: {strategy}"
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
                
                msg = (
                    f"🤝 *PROPUESTA DE TRADING*\n\n"
                    f"Activo: `{symbol}`\n"
                    f"Operación: *{side}*\n"
                    f"Confianza: {confidence:.0%}\n"
                    f"Estrategia: {strategy}\n\n"
                    f"¿Deseas ejecutar esta operación?"
                )
                await bot.send_message(
                    session.chat_id, msg, 
                    reply_markup=keyboard, 
                    parse_mode="Markdown"
                )
                
            elif mode == 'PILOT':
                # Auto-execute
                await bot.send_message(
                    session.chat_id,
                    f"🚀 *EJECUTANDO {side}* en `{symbol}`...",
                    parse_mode="Markdown"
                )
                
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
                else:
                    await bot.send_message(
                        session.chat_id,
                        f"❌ Error: {result}"
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
    
    # 3. Initialize Session Manager
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
    
    dp.include_router(commands_router)
    dp.include_router(trading_router)
    dp.include_router(config_router)
    dp.include_router(callbacks_router)
    
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
    
    # 7. Startup Message
    logger.info("🚀 Antigravity Bot (Async) starting...")
    
    if TELEGRAM_ADMIN_ID:
        try:
            await bot.send_message(
                TELEGRAM_ADMIN_ID,
                "🟢 *Antigravity Bot Online*\n\n"
                f"Sesiones: {len(session_manager.sessions)}\n"
                f"Activos: {len(get_all_assets())}\n"
                f"Quantum: {'✅' if USE_QUANTUM_ENGINE else '❌'}",
                parse_mode="Markdown"
            )
        except Exception as e:
            logger.warning(f"Could not send startup message: {e}")
    
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
