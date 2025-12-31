"""
Nexus Trading Bot (NTB) - System Loader
Main bot application using aiogram 3.x with native async/await
"""

import asyncio
import os
import sys
import logging
import random
from typing import Any, Awaitable, Callable, Dict

from aiogram import Bot, Dispatcher, BaseMiddleware
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import TelegramObject, FSInputFile
from dotenv import load_dotenv

# Import compatibility layer for backward compatibility with reorganized code
try:
    import compatibility_imports
except ImportError:
    print("⚠️  Compatibility imports not found - some features may not work")

from servos.db import get_user_name
from servos.media_manager import MediaManager

# Load Environment Variables
load_dotenv()

# --- NEXUS BANNER ---
def print_nexus_banner():
    # ANSI Color Codes
    CYAN = "\033[36m"
    BLUE = "\033[94m"
    RESET = "\033[0m"
    
    print(f"{CYAN}")
    print(r"""
    _   _    _______   __  __   _    _    _____
   | \ | |  |  _____|  \ \/ /  | |  | |  / ____|
   |  \| |  | |__       \  /   | |  | | | (___  
   | . ` |  |  __|      /  \   | |  | |  \___ \ 
   | |\  |  | |____    / /\ \  | |__| |  ____) |
   |_| \_|  |______|  /_/  \_\  \____/  |_____/ 
     N E X U S   C O R E
    """)
    print(f"{BLUE}> SYSTEM INITIALIZED. LINK ESTABLISHED. AWAITING DIRECTIVES.{RESET}")

# --- AUTO-TRAIN CORTEX (ML) IF MISSING ---
# This ensures the ML model exists on Railway's persistent volume
ML_MODEL_PATH = os.path.join('nexus_system', 'memory_archives', 'ml_model.pkl')
if not os.path.exists(ML_MODEL_PATH):
    print("🧠 Cortex Model not found! Initializing training sequence...")
    print("   This may take 2-3 minutes on first deployment.")
    try:
        import subprocess
        result = subprocess.run(
            [sys.executable, 'train_cortex.py'],
            capture_output=True,
            text=True,
            timeout=600  # 10 min max
        )
        if result.returncode == 0:
            print("✅ Cortex trained and synaptic weights saved successfully!")
        else:
            print(f"⚠️ Cortex Training failed: {result.stderr[-500:]}")
    except Exception as e:
        print(f"⚠️ Cortex Auto-training error: {e}")
else:
    print(f"✅ Cortex Model found: {ML_MODEL_PATH}")

# --- SUPPRESS NOISY WARNINGS ---
import warnings
warnings.filterwarnings('ignore', message='.*sklearn.utils.parallel.delayed.*')
warnings.filterwarnings('ignore', category=UserWarning, module='sklearn')

# --- CONFIGURATION ---
# Usar NexusLogger para agrupación de logs
from nexus_system.utils.logger import get_logger
logger = get_logger('NTB_Loader')

# Suppress noisy loggers
logging.getLogger('httpx').setLevel(logging.WARNING)
logging.getLogger('aiogram').setLevel(logging.INFO)

# --- CONFIGURATION ---
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_ADMIN_ID = os.getenv('TELEGRAM_ADMIN_ID')

# --- DIAGNOSTICS: LOG ENV VARS (Agrupado) ---
_vars_to_log = ['TELEGRAM_ADMIN_ID', 'BINANCE_API_KEY', 'BINANCE_SECRET', 'BYBIT_API_KEY', 'BYBIT_API_SECRET', 'OPENAI_API_KEY', 'PROXY_URL', 'APCA_API_KEY_ID', 'APCA_API_SECRET_KEY', 'APCA_API_BASE_URL']
status_parts = []
for v in _vars_to_log:
    val = os.getenv(v, '').strip().strip("'\"")
    found = "✅" if val else "❌"
    short_name = v.replace('TELEGRAM_', '').replace('BINANCE_', 'BIN_').replace('BYBIT_', 'BYB_').replace('OPENAI_', 'AI_').replace('APCA_API_', 'ALP_').replace('_KEY', '').replace('_SECRET', '').replace('_ID', '').replace('_URL', '')
    if v == 'PROXY_URL': short_name = "PROXY"
    status_parts.append(f"{short_name}:{found}")
logger.info(f"🔧 Env Vars: {' | '.join(status_parts)}", group=False)  # No agrupar, es un resumen único

# ------------------------------------------


# --- ASSET CONFIGURATION (Centralized) ---
from system_directive import ASSET_GROUPS, GROUP_CONFIG, get_all_assets, get_display_name


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
from servos.db import get_user_role

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
                # REJECTION LOGIC
                logger.warning(f"⛔ Shield Protocol Activated: Access Denied for {chat_id} ({user.first_name}) - Role: {role}")
                
                # Get owner contact from env (username link preferred, fallback to chat_id)
                owner_contact = os.getenv('OWNER_CONTACT', '').strip()
                if not owner_contact:
                    admin_id = os.getenv('TELEGRAM_ADMIN_ID', os.getenv('TELEGRAM_CHAT_ID', ''))
                    owner_contact = f"ID: {admin_id}" if admin_id else "_No configurado_"
                
                # Reply with rejection message (only for private chats to avoid spam in groups)
                if isinstance(event, Message) and event.chat.type == 'private':
                    try:
                        await event.answer(
                            f"⛔ **SHIELD PROTOCOL: ACTIVE**\n\n"
                            f"Acceso al Nexus System denegado.\n\n"
                            f"📋 **ID de Unidad:** `{chat_id}`\n"
                            f"👤 **Admin:** {owner_contact}\n\n"
                            f"_Solicite autorización manual._",
                            parse_mode="Markdown"
                        )
                    except:
                        pass
                elif isinstance(event, CallbackQuery):
                     try:
                         await event.answer("⛔ Access Denied by Shield", show_alert=True)
                     except:
                         pass
                         
                return # Block execution
                
            # Optional: Inject role into data handler
            data['user_role'] = role
            
        return await handler(event, data)


# --- SIGNAL DISPATCH ---

# Global Personality Manager instance
from servos.personalities import PersonalityManager
personality_manager = PersonalityManager()

# === DYNAMIC COOLDOWN MANAGER ===
# Intelligent per-symbol cooldown with frequency and volatility tracking
from servos.cooldown_manager import DynamicCooldownManager
import time

cooldown_manager = DynamicCooldownManager(default_cooldown=300)  # 5 min default

# === STRATEGY NAME MAPPING ===
# Maps strategy.name values from StrategyFactory to session config keys
# This is CRITICAL for signal filtering to work correctly
from system_directive import STRATEGY_CONFIG_MAP as STRATEGY_NAME_TO_CONFIG_KEY

async def dispatch_nexus_signal(bot: Bot, signal, session_manager):
    """
    Dispatch trading signals from NexusCore to all active sessions.
    The 'Synapse' dispatch system.
    """
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    
    symbol = signal.symbol
    action = signal.action.upper()  # BUY, SELL, HOLD
    confidence = getattr(signal, 'confidence', 0.5)
    strategy = getattr(signal, 'strategy', 'UNKNOWN')
    price = getattr(signal, 'price', 0)
    
    # Skip non-actionable signals (Hold/Wait)
    # EXIT_ALL and EXIT_LONG are processed below immediately
    if action in ['HOLD', 'WAIT']:
        return
        
    # === SENTINEL / PANIC HANDLING ===
    if action == 'EXIT_LONG':
        logger.warning(f"🚨 SENTINEL: EXIT_LONG {symbol}", group=True)
        import asyncio
        for session in session_manager.get_all_sessions():
             # Fire and forget (concurrent)
             asyncio.create_task(session.execute_close_position(symbol, only_side='LONG'))
        return

    if action == 'EXIT_ALL':
        logger.warning(f"🚨 SENTINEL: EXIT_ALL {symbol}", group=True)
        for session in session_manager.get_all_sessions():
             asyncio.create_task(session.execute_close_position(symbol))
        return

    # === CLOSE HANDLING (Trend Reversal / Exit Signals) ===
    if action in ['CLOSE_LONG', 'EXIT_LONG']:
        logger.info(f"📉 SIGNAL: Salida LONG {symbol}", group=True)
        for session in session_manager.get_all_sessions():
             asyncio.create_task(session.execute_close_position(symbol, only_side='LONG'))
        return

    if action in ['CLOSE_SHORT', 'EXIT_SHORT']:
        logger.info(f"📈 SIGNAL: Salida SHORT {symbol}", group=True)
        for session in session_manager.get_all_sessions():
             asyncio.create_task(session.execute_close_position(symbol, only_side='SHORT'))
        return
    
    # === TEMPORAL FILTER: Skip if on cooldown ===
    if cooldown_manager.is_on_cooldown(symbol):
        logger.info(f"⏳ Signal {symbol} omitido (cooldown)", group=True)
        return
    
    # Map action to side
    side = 'LONG' if action == 'BUY' else 'SHORT'
    
    # Map strategy name to config key for filtering
    strategy_config_key = STRATEGY_NAME_TO_CONFIG_KEY.get(strategy, strategy.upper())
    
    # Format Reason with Metadata
    # User Format: [Strategy | Conf: 85% | Param1: Val1]
    meta_params = []
    if getattr(signal, 'metadata', None):
        for k, v in signal.metadata.items():
            if k.lower() == 'strategy': continue
            
            # Emoji Logic for TREND
            if k.upper() == 'TREND':
                if str(v).upper() == 'UP':
                    v = f"{v} 🐂"
                elif str(v).upper() == 'DOWN':
                    v = f"{v} 🐻"
            
            if isinstance(v, float):
                meta_params.append(f"{k.upper()}: {v:.1f}")
            else:
                meta_params.append(f"{k.upper()}: {v}")
    
    params_str = " | ".join(meta_params)
    reason = f"[{strategy} | Conf: {confidence:.0%} | {params_str}]"
    
    logger.info(f"📡 Signal: {action} {symbol} (Conf: {confidence:.0%}, {strategy})", group=True)
    
    # Dispatch to all sessions
    from system_directive import ASSET_GROUPS
    
    # Determine Asset Group
    asset_group = None
    for group_name, assets in ASSET_GROUPS.items():
        if symbol in assets:
            asset_group = group_name
            break
    
    # Track if at least one session processed the signal
    signal_processed = False
    atr = getattr(signal, 'atr', None)
            
    for session in session_manager.get_all_sessions():
        # --- FILTER: Strategy Enabled? ---
        # Use mapped config key instead of raw strategy name
        if not session.is_strategy_enabled(strategy_config_key):
            logger.info(f"⏭️ {session.chat_id}: Estrategia {strategy_config_key} deshabilitada", group=True)
            continue
            
        # --- FILTER: Group Enabled? ---
        if asset_group and not session.is_group_enabled(asset_group):
            logger.info(f"⏭️ {session.chat_id}: Grupo {asset_group} deshabilitado", group=True)
            continue
            
        # --- FILTER: Blacklisted? ---
        if session.is_asset_disabled(symbol):
            logger.info(f"⏭️ {session.chat_id}: Asset {symbol} en blacklist", group=True)
            continue
            
        try:
            mode = session.mode
            p_key = session.config.get('personality', 'STANDARD_ES')
            user_name = get_user_name(session.chat_id)
            
            # Calculate SL/TP/TS preview
            sl_prev, tp_prev, ts_prev = session.get_trade_preview(symbol, side, price) if price else (0, 0, 0)
            
            # Fetch Personality Data
            profile = personality_manager.PROFILES.get(p_key, personality_manager.PROFILES.get('STANDARD_ES'))
            title = profile.get('NAME', 'Nexus Bot')
            quote = random.choice(profile.get('GREETING', ["Online."]))
            
            if mode == 'WATCHER':
                # Use personality message
                if side == 'LONG':
                    msg = personality_manager.get_message(
                        p_key, 'TRADE_LONG',
                        asset=symbol, price=price, reason=reason,
                        tp=tp_prev, sl=sl_prev, ts=ts_prev,
                        title=title, quote=quote, strategy_name=strategy,
                        user_name=user_name
                    )
                else:
                    msg = personality_manager.get_message(
                        p_key, 'TRADE_SHORT',
                        asset=symbol, price=price, reason=reason,
                        tp=tp_prev, sl=sl_prev, ts=ts_prev,
                        title=title, quote=quote, strategy_name=strategy,
                        user_name=user_name
                    )
                await bot.send_message(session.chat_id, msg, parse_mode="Markdown")
                
            elif mode == 'COPILOT':
                if side == 'LONG':
                    msg = personality_manager.get_message(
                        p_key, 'TRADE_LONG',
                        asset=symbol, price=price, reason=reason,
                        tp=tp_prev, sl=sl_prev, ts=ts_prev,
                        title=title, quote=quote, strategy_name=strategy,
                        user_name=user_name
                    )
                else:
                    msg = personality_manager.get_message(
                        p_key, 'TRADE_SHORT',
                        asset=symbol, price=price, reason=reason,
                        tp=tp_prev, sl=sl_prev, ts=ts_prev,
                        title=title, quote=quote, strategy_name=strategy,
                        user_name=user_name
                    )
                    
                keyboard = InlineKeyboardMarkup(inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="✅ Execute Protocol",
                            callback_data=f"TRADE|ACCEPT|{symbol}|{side}|{strategy}"
                        ),
                        InlineKeyboardButton(
                            text="❌ Abort",
                            callback_data=f"TRADE|REJECT|{symbol}|{side}|{strategy}"
                        )
                    ]
                ])
                await bot.send_message(
                    session.chat_id, msg, 
                    reply_markup=keyboard, 
                    parse_mode="Markdown"
                )
                
            elif mode == 'PILOT':
                # Check if position already exists - DON'T trigger update on every signal
                # Check if position already exists
                try:
                    positions = await session.get_active_positions()
                    existing_pos = next((p for p in positions if p['symbol'] == symbol), None)
                    
                    if existing_pos:
                        # Check for Reversal / Flip opportunity
                        existing_amt = float(existing_pos.get('amt', 0))
                        is_existing_long = existing_amt > 0
                        is_signal_long = (side == 'LONG')
                        
                        if is_existing_long == is_signal_long:
                             logger.info(f"⏭️ {symbol}: Posición {side} activa, omitiendo", group=True)
                             continue
                        else:
                             logger.info(f"🔄 FLIP: {symbol} {'LONG→SHORT' if is_existing_long else 'SHORT→LONG'}", group=True)
                             # Proceed to execution (trading_manager handles the flip)
                except:
                    pass  # If check fails, proceed with trade attempt
                
                # Auto-execute (no "entering pilot mode" message)
                if side == 'LONG':
                    success, result = await session.execute_long_position(symbol, atr=atr, strategy=strategy)
                else:
                    success, result = await session.execute_short_position(symbol, atr=atr, strategy=strategy)
                
                if success:
                    # Build enhanced AUTOPILOT message
                    from datetime import datetime, timezone
                    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
                    
                    # Determine exchange based on Bridge routing
                    if 'USDT' not in symbol:
                        exchange = "Alpaca"
                    else:
                        # Use Bridge routing if available
                        if session.bridge:
                            routed_exchange = session.bridge._route_symbol(symbol)
                            exchange = routed_exchange.title()  # BYBIT -> Bybit
                        elif session.config.get('primary_exchange', 'BINANCE') == 'BYBIT':
                            exchange = "Bybit"
                        else:
                            exchange = "Binance"

                    
                    # Direction styling
                    direction = "🟢 LONG (Activo)" if side == 'LONG' else "🔴 SHORT (Activo)"
                    
                    # Format prices safely
                    price_str = f"${price:.2f}" if price else "N/A"
                    ts_str = f"${ts_prev:.2f}" if ts_prev else "N/A"
                    tp_str = f"${tp_prev:.2f}" if tp_prev else "N/A"
                    sl_str = f"${sl_prev:.2f}" if sl_prev else "N/A"
                    
                    # Format quote with username
                    formatted_quote = quote.rstrip('.!?,;:')
                    
                    caption = (
                        f"✅ *AUTOPILOT ENGAGED: {side}*\n"
                        f"🕐 `{timestamp}`\n\n"
                        f"\"{formatted_quote}, *{user_name}*.\"\n"
                        f"{title}\n\n"
                        f"*Activo:* `{symbol}`\n"
                        f"*Exchange:* {exchange}\n"
                        f"*Dirección:* {direction}\n"
                        f"*Estrategia:* {strategy}\n"
                        f"*Precio Actual:* {price_str}\n\n"
                        f"💸 *TS:* {ts_str}\n"
                        f"🎯 *TP:* {tp_str}\n"
                        f"🛑 *SL:* {sl_str}\n\n"
                        f"*Parámetros:*\n"
                        f"`{reason}`"
                    )
                    
                    await bot.send_message(
                        session.chat_id,
                        caption,
                        parse_mode="Markdown"
                    )
                    
                    # Check circuit breaker after trade
                    cb_triggered, cb_msg = await session.check_circuit_breaker()
                    if cb_triggered:
                        cb_alert = personality_manager.get_message(p_key, 'CB_TRIGGER')
                        await bot.send_message(session.chat_id, cb_alert, parse_mode="Markdown")
                else:
                    # Only log errors, don't spam user with cooldown messages
                    ignore_phrases = ["Wait", "cooldown", "duplicate", "Alpaca Client not initialized", "SILENT_REJECTION", "Cupo lleno"]
                    
                    if any(x in result for x in ignore_phrases):
                        continue

                    # Determine exchange for error messages using Bridge routing
                    if 'USDT' not in symbol:
                        error_exchange = "Alpaca"
                    elif session.bridge:
                        error_exchange = session.bridge._route_symbol(symbol).title()
                    elif session.config.get('primary_exchange', 'BINANCE') == 'BYBIT':
                        error_exchange = "Bybit"
                    else:
                        error_exchange = "Binance"

                    
                    # Handle Margin Insufficient errors with friendly message
                    if "INSUFFICIENT_MARGIN" in result or "Margin is insufficient" in result:
                        await bot.send_message(
                            session.chat_id,
                            f"⚠️ No se ejecutó operación automática para *{symbol}* "
                            f"en el exchange *{error_exchange}* por fondos insuficientes ⚠️",
                            parse_mode="Markdown"
                        )
                    
                    # Special handling for "Insufficient capital" (Min Notional)
                    elif "MIN_NOTIONAL" in result or "Insufficient capital" in result:
                        # 1. Trigger Long Cooldown (1 hour) to stop spam
                        from system_directive import COOLDOWN_SECONDS
                        cooldown_manager.set_cooldown(symbol, 3600)
                        
                        # 2. Notify User only once
                        await bot.send_message(
                            session.chat_id,
                            f"⚠️ **CAPITAL INSUFICIENTE: {symbol}**\n\n"
                            f"Tamaño de posición por debajo del mínimo del exchange.\n"
                            f"❄️ **Acción:** {symbol} congelado por 1 hora.",
                            parse_mode="Markdown"
                        )
                    
                    else:
                        await bot.send_message(
                            session.chat_id,
                            f"❌ Effector Error: {result}",
                            parse_mode=None
                        )
                    
            signal_processed = True
        except Exception as e:
            logger.error(f"Synapse dispatch error for {session.chat_id}: {e}")
    
    # Set cooldown ONLY if at least one session processed the signal
    if signal_processed:
        cooldown_manager.set_cooldown(symbol, atr=atr)
    else:
        logger.debug(f"📭 Signal for {symbol} not dispatched (no eligible sessions)")


# --- MAIN APPLICATION ---
async def main():
    """Main entry point for the async bot."""
    
    # Print Banner
    print_nexus_banner()
    
    if not TELEGRAM_TOKEN:
        logger.error("❌ TELEGRAM_TOKEN not found in environment!")
        return
    
    # 1. Create Bot Instance
    from aiohttp import ClientTimeout
    from aiogram.client.session.aiohttp import AiohttpSession

    # Configure longer timeouts for Railway deployment
    timeout = ClientTimeout(total=60.0, sock_read=30.0, sock_connect=30.0)
    session = AiohttpSession(timeout=timeout)

    bot = Bot(
        token=TELEGRAM_TOKEN,
        session=session,
        default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN)
    )
    
    # 2. Create Dispatcher
    dp = Dispatcher()
    
    # 3. Initialize Database (PostgreSQL)
    try:
        from servos.db import init_db, load_bot_state
        init_db()
        
        # Load persisted strategies from DB
        bot_state = load_bot_state()
        if bot_state:
            from system_directive import ENABLED_STRATEGIES, GROUP_CONFIG, DISABLED_ASSETS
            import system_directive as system_directive
            
            # 1. Strategies
            if bot_state.get('enabled_strategies'):
                ENABLED_STRATEGIES.update(bot_state['enabled_strategies'])
            
            # 2. Group Config (check for embedded AI_FILTER and ML_CLASSIFIER)
            if bot_state.get('group_config'):
                gc = bot_state['group_config']
                
                # Extract AI Filter state if present
                if '_AI_FILTER' in gc:
                    system_directive.AI_FILTER_ENABLED = gc.pop('_AI_FILTER')
                
                # Extract ML Classifier state if present
                if '_ML_CLASSIFIER' in gc:
                    system_directive.ML_CLASSIFIER_ENABLED = gc.pop('_ML_CLASSIFIER')
                
                # --- MIGRATION: COMMODITY -> ETFS ---
                if 'COMMODITY' in gc:
                    val = gc.pop('COMMODITY')
                    if 'ETFS' not in gc:
                        gc['ETFS'] = val
                    logger.info("🔄 Migrated legacy 'COMMODITY' state to 'ETFS'")
                
                GROUP_CONFIG.update(gc)
                
                # Persist migration immediately
                from servos.db import save_bot_state
                save_bot_state(ENABLED_STRATEGIES, GROUP_CONFIG, list(DISABLED_ASSETS), system_directive.AI_FILTER_ENABLED)
                
            # 3. Disabled Assets
            if bot_state.get('disabled_assets'):
                DISABLED_ASSETS.clear()
                # Ensure it's a list/iterable
                assets = bot_state['disabled_assets']
                if isinstance(assets, list):
                    for asset in assets:
                         DISABLED_ASSETS.add(asset)
            
            logger.info(f"✅ Estado cargado: {len(DISABLED_ASSETS)} assets deshabilitados, AI: {system_directive.AI_FILTER_ENABLED}, ML: {system_directive.ML_CLASSIFIER_ENABLED}", group=False)
            
    except Exception as e:
        logger.warning(f"DB Init skipped: {e}")
    
    # 4. Initialize Session Manager
    from servos.trading_manager import AsyncSessionManager
    session_manager = AsyncSessionManager()
    await session_manager.load_sessions()
    
    # 5. Initialize Task Scheduler
    scheduler = None
    try:
        from servos.task_scheduler import get_scheduler
        scheduler = get_scheduler()
        await scheduler.initialize(bot)
        
        # Register action handlers for scheduled tasks
        async def handle_analyze(user_id, params, bot_instance):
            """
            Handler async para análisis programado de activos.
            Usa MarketStream para obtener datos de forma async.
            """
            symbol = params.get('symbol', 'BTC')
            from servos.ai_analyst import NexusAnalyst
            from nexus_system.utils.market_data import get_market_data_async
            
            analyst = NexusAnalyst()
            # Obtener datos de forma async
            df = await get_market_data_async(f"{symbol}USDT", timeframe='4h', limit=50)
            if not df.empty:
                indicators = {
                    'rsi': df['rsi'].iloc[-1] if 'rsi' in df.columns else 50,
                    'trend': 'UP' if df['close'].iloc[-1] > df['close'].iloc[-5] else 'DOWN'
                }
                session = session_manager.get_session(str(user_id))
                p_key = session.config.get('personality', 'STANDARD_ES') if session else 'STANDARD_ES'
                analysis = await asyncio.get_event_loop().run_in_executor(
                    None, analyst.analyze_signal, symbol, '4h', indicators, p_key
                )
                await bot_instance.send_message(user_id, f"📊 **Nexus Analysis: {symbol}**\n\n{analysis}", parse_mode="Markdown")
        
        async def handle_news(user_id, params, bot_instance):
            from servos.ai_analyst import NexusAnalyst
            analyst = NexusAnalyst()
            briefing = await asyncio.get_event_loop().run_in_executor(None, analyst.generate_market_briefing)
            await bot_instance.send_message(user_id, f"📰 **Nexus Intelligence Briefing**\n\n{briefing}", parse_mode="Markdown")
        
        async def handle_sniper(user_id, params, bot_instance):
            await bot_instance.send_message(user_id, "🎯 **Sniper Scan Initiated...**\n/sniper to view results.", parse_mode="Markdown")
        
        async def handle_dashboard(user_id, params, bot_instance):
            session = session_manager.get_session(str(user_id))
            if session:
                data = await session.get_dashboard_summary()
                wallet = data.get('wallet', {})
                net = wallet.get('total', 0)
                await bot_instance.send_message(user_id, f"📊 **System Status Report**\n💰 Capital: `${net:,.2f}`", parse_mode="Markdown")
        
        async def handle_sentiment(user_id, params, bot_instance):
            from servos.ai_analyst import NexusAnalyst
            analyst = NexusAnalyst()
            symbol = params.get('symbol', 'BTC')
            if analyst.client:
                sent = analyst.check_market_sentiment(f"{symbol}USDT")
                score = sent.get('score', 0)
                reason = sent.get('reason', 'N/A')
                icon = "🟢" if score > 0.2 else "🔴" if score < -0.2 else "🟡"
                await bot_instance.send_message(user_id, f"🧠 **Sentiment Analysis: {symbol}**\n{icon} Score: `{score:.2f}`\n📝 {reason}", parse_mode="Markdown")

        async def handle_price_alert(user_id, params, bot_instance):
            """Check if price target is met, notify, and cancel task."""
            symbol = params.get('symbol', 'BTC').upper()
            target = float(params.get('target', 0))
            condition = params.get('condition', 'above') # above or below
            
            # Use a session to get price (or created temp)
            session = session_manager.get_session(str(user_id))
            if not session:
                return # Can't check price without session/client
                
            try:
                # 1. Get Current Price
                current_price = await session.get_symbol_price(symbol)
                if not current_price:
                    return

                # 2. Check Condition
                triggered = False
                if condition == 'above' and current_price >= target:
                    triggered = True
                elif condition == 'below' and current_price <= target:
                    triggered = True
                
                # 3. Notify and Cancel if Triggered
                if triggered:
                    msg = (
                        f"🚨 **NEXUS ALERT: {symbol}**\n\n"
                        f"Target hit: `${target:,.2f}`\n"
                        f"Current: `${current_price:,.2f}`\n"
                        f"📈 Cond: {condition.upper()}"
                    )
                    await bot_instance.send_message(user_id, msg, parse_mode="Markdown")
                    
                    # Search and cancel this specific task
                    # We need to find the task_id. Since we don't have it passed directly, we look it up.
                    # This is a bit inefficient but works for now.
                    #Ideally, scheduler should pass task_id to handler.
                    scheduler = get_scheduler()
                    tasks = scheduler.list_tasks(user_id)
                    for t in tasks:
                        # Match params to identify the task
                        t_params = t.get('params', {})
                        if (t.get('action') == 'price_alert' and 
                            t_params.get('symbol') == symbol and 
                            float(t_params.get('target', 0)) == target):
                            
                            scheduler.cancel_task(user_id, t['id'])
                            await bot_instance.send_message(user_id, f"✅ Alert Directive for {symbol} executed and archived.", parse_mode="Markdown")
                            break
            except Exception as e:
                logger.error(f"Price alert check failed: {e}")

        # Register Actions
        scheduler.register_action('analyze', handle_analyze)
        scheduler.register_action('news', handle_news)
        scheduler.register_action('sniper', handle_sniper)
        scheduler.register_action('dashboard', handle_dashboard)
        scheduler.register_action('sentiment', handle_sentiment)
        scheduler.register_action('fomc', handle_news)  # Alias
        scheduler.register_action('price_alert', handle_price_alert)
        scheduler.register_action('alert', handle_price_alert) # Fallback alias
        
        scheduler.start()
        
        # Aggregated Log
        actions = list(scheduler.action_handlers.keys())
        logger.info(f"📅 TaskScheduler: {len(actions)} acciones registradas", group=False)
        
    except Exception as e:
        logger.warning(f"⚠️ Task Scheduler init skipped: {e}")
            
    # 6. Register Middleware (BEFORE ROUTERS!)
    # GatekeeperMiddleware must be registered first so it blocks before other handlers run
    dp.message.middleware(GatekeeperMiddleware())
    dp.callback_query.middleware(GatekeeperMiddleware())
    
    # SessionMiddleware injects session_manager
    dp.message.middleware(SessionMiddleware(session_manager))
    dp.callback_query.middleware(SessionMiddleware(session_manager))
    
    # 7. Register Routers
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
    
    logger.info("✅ Routers registrados", group=False)

    # 6. Initialize Nexus Core (formerly Nexus Core)
    engine_task = None
    USE_NEXUS_ENGINE = os.getenv('USE_NEXUS_ENGINE', 'true').lower() == 'true'
    
    if USE_NEXUS_ENGINE:
        try:
            from nexus_system.core.engine import NexusCore
            
            # --- KEY INJECTION FIX ---
            # Try to get admin keys for Alpaca & Bybit (background engine needs them)
            admin_id = os.getenv('TELEGRAM_ADMIN_ID')
            alpaca_keys = {}
            bybit_keys = {}
            
            if admin_id and session_manager:
                admin_session = session_manager.get_session(str(admin_id))
                if admin_session:
                    # Alpaca
                    ak_key = admin_session.config.get('alpaca_key')
                    ak_sec = admin_session.config.get('alpaca_secret')
                    if ak_key and ak_sec:
                        alpaca_keys = {'key': ak_key, 'secret': ak_sec}
                        logger.info(f"🔑 NexusCore: Keys Alpaca inyectadas desde Admin", group=False)
                    
                    # Bybit
                    bk_key = admin_session.config.get('bybit_api_key') or os.getenv('BYBIT_API_KEY')
                    bk_sec = admin_session.config.get('bybit_api_secret') or os.getenv('BYBIT_API_SECRET')
                    if bk_key and bk_sec:
                        bybit_keys = {'key': bk_key, 'secret': bk_sec}
                        logger.info(f"🔑 NexusCore: Keys Bybit inyectadas", group=False)
            
            engine = NexusCore(
                assets=get_all_assets(), 
                alpaca_keys=alpaca_keys, 
                bybit_keys=bybit_keys,
                session_manager=session_manager
            )
            
            # --- BRIDGE: Inject Engine into Session Manager for Dashboard Data ---
            if session_manager:
                session_manager.set_nexus_engine(engine)
            
            # Set callback for signal dispatch
            async def on_signal(signal):
                await dispatch_nexus_signal(bot, signal, session_manager)
            
            engine.set_callback(on_signal)
            
            logger.info("🌌 Nexus Core inicializado", group=False)
            
            # Wrapper to catch and log exceptions from engine task
            async def run_engine_with_logging():
                try:
                    logger.info("🚀 Nexus Core: Loop iniciado", group=False)
                    await engine.run()
                except Exception as e:
                    logger.error(f"❌ Nexus Core: Error crítico - {e}", exc_info=True)
            
            # Create engine task (will run concurrently with bot)
            engine_task = asyncio.create_task(run_engine_with_logging())
            
        except Exception as e:
            logger.warning(f"⚠️ Nexus Core init failed: {e}", exc_info=True)

    # 7. Start Shark Sentinel (Black Swan Defense) - Async Version
    try:
        from strategies.shark_mode import SharkSentinel
        
        async def notify_send(msg):
             # Broadcast alert to all active sessions (async)
             chat_ids = session_manager.get_active_chat_ids()
             tasks = [
                 bot.send_message(chat_id, msg, parse_mode='Markdown')
                 for chat_id in chat_ids
             ]
             if tasks:
                 await asyncio.gather(*tasks, return_exceptions=True)

        # Check function for Sentinel
        def is_shark_enabled():
             from system_directive import ENABLED_STRATEGIES
             return ENABLED_STRATEGIES.get('BLACK_SWAN', True) or ENABLED_STRATEGIES.get('SHARK', False)

        sentinel = SharkSentinel(
            session_manager=session_manager,
            notify_callback=notify_send,
            enabled_check_callback=is_shark_enabled
        )
        await sentinel.start()  # Async start
        logger.info("🦈 Shark Sentinel: Activo (Async)", group=False)
        
    except Exception as e:
        logger.error(f"❌ Failed to start Shark Sentinel: {e}", exc_info=True)

    # 8. Startup Message (Web Server removed - feature deprecated)

    # 9. Startup Summary
    from nexus_system.utils.logger import log_startup_summary
    startup_components = {
        'DB': True,  # Asumimos OK si no hay excepción
        'SessionManager': True,
        'TaskScheduler': scheduler is not None,
        'NexusCore': engine_task is not None,
        'SharkSentinel': True  # Asumimos OK si no hay excepción
    }
    log_startup_summary(logger, startup_components)
    
    raw_admin_ids = os.getenv('TELEGRAM_ADMIN_ID', '').strip("'\" ")
    if raw_admin_ids:
        admin_ids = [aid.strip() for aid in raw_admin_ids.split(',') if aid.strip()]
        
        for admin_id in admin_ids:
            try:
                await bot.send_message(
                    admin_id,
                    "🟢 *Nexus Systems Online*\n\n"
                    f"Links: {len(session_manager.sessions)}\n"
                    f"Assets: {len(get_all_assets())}\n"
                    f"Core: {'✅' if USE_NEXUS_ENGINE else '❌'}",
                    parse_mode="Markdown"
                )
            except Exception as e:
                logger.warning(f"Could not send startup message to {admin_id}: {e}")
    
    # 8. Start Polling with Error Handling
    try:
        logger.info("🔄 Starting Telegram bot polling...")
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"❌ Fatal error during bot polling: {e}")
        logger.error("🔄 Attempting graceful shutdown...")
        raise  # Re-raise to ensure cleanup happens
    finally:
        # Cleanup
        logger.info("🛑 Nexus Core Shutdown Sequence Initiated...")
        
        # Shutdown scheduler
        if scheduler:
            scheduler.shutdown(wait=False)
        
        if engine_task:
            # Signal engine to stop gracefullly first
            if 'engine' in locals() and engine:
                 await engine.stop()
            
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
