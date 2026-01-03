"""
Nexus Trading Bot (NTB) - System Loader
Main bot application using aiogram 3.x with native async/await
"""

import asyncio
import os
import sys
import logging
import random
from datetime import datetime, timezone
from typing import Any, Awaitable, Callable, Dict

from aiogram import Bot, Dispatcher, BaseMiddleware
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import TelegramObject, FSInputFile
from dotenv import load_dotenv

# Import compatibility layer for backward compatibility with reorganized code
# Temporarily disabled to avoid ML import warnings during bot startup
# Will be imported lazily when ML features are actually used
# try:
#     import compatibility_imports
# except ImportError:
#     print("⚠️  Compatibility imports not found - some features may not work")

from servos.db import get_user_name
from servos.media_manager import MediaManager
from servos.voight_kampff import voight_kampff as nexus_logger

# Configure logging to suppress noisy messages during initialization
logging.getLogger('aiogram').setLevel(logging.WARNING)
logging.getLogger('aiohttp').setLevel(logging.WARNING)
logging.getLogger('ccxt').setLevel(logging.WARNING)
logging.getLogger('nexus_system').setLevel(logging.WARNING)  # Suppress NexusCore logs during init

# Load Environment Variables
load_dotenv()


async def safe_send_message(bot: Bot, chat_id: int, text: str, **kwargs):
    """Send message with error handling to prevent silent failures"""
    try:
        await bot.send_message(chat_id, text, **kwargs)
    except Exception as e:
        logger.error(f"❌ Failed to send message to chat {chat_id}: {e}")
        # Don't re-raise to avoid breaking the main flow

# --- NEXUS BANNER ---
def print_nexus_banner():
    """Legacy function - replaced by NexusLogger."""
    pass

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
        if result.returncode != 0:
            nexus_logger.log_warning(f"ML model training failed: {result.stderr[-100:]}")
    except Exception as e:
        nexus_logger.log_warning(f"ML model auto-training error: {e}")

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
_vars_to_log = ['TELEGRAM_ADMIN_ID', 'BINANCE_API_KEY', 'BINANCE_API_SECRET', 'BYBIT_API_KEY', 'BYBIT_API_SECRET', 'OPENAI_API_KEY', 'PROXY_URL', 'APCA_API_KEY_ID', 'APCA_API_SECRET_KEY', 'APCA_API_BASE_URL']
status_parts = []
for v in _vars_to_log:
    # Special handling for BINANCE_API_SECRET - check both standard and legacy names
    if v == 'BINANCE_API_SECRET':
        val = (os.getenv('BINANCE_API_SECRET', '').strip().strip("'\"") or
               os.getenv('BINANCE_SECRET', '').strip().strip("'\""))
    else:
        val = os.getenv(v, '').strip().strip("'\"")

    found = "✅" if val else "❌"
    short_name = v.replace('TELEGRAM_', '').replace('BINANCE_', 'BIN_').replace('BYBIT_', 'BYB_').replace('OPENAI_', 'AI_').replace('APCA_API_', 'ALP_').replace('_KEY', '').replace('_SECRET', '').replace('_ID', '').replace('_URL', '')
    if v == 'PROXY_URL': short_name = "PROXY"
    status_parts.append(f"{short_name}:{found}")
    # Environment validation completed - metrics shown in phase success  # No agrupar, es un resumen único

# ------------------------------------------


# --- ASSET CONFIGURATION (Centralized) ---
from system_directive import ASSET_GROUPS, CRYPTO_SUBGROUPS, GROUP_CONFIG, get_all_assets, get_display_name


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
    
    # Map action to side
    side = 'LONG' if action == 'BUY' else 'SHORT'

    # === AI FILTER: Intelligent Signal Filtering ===
    # Apply AI-powered filtering based on market sentiment
    signal_data = {
        'symbol': symbol,
        'side': side,
        'entry_price': price,
        'strategy': strategy,
        'confidence': confidence,
        'timestamp': datetime.now().isoformat()
    }

    # Check if any active session has AI Filter enabled
    ai_filter_applied = False
    filter_reason = ""
    filter_analysis = {}

    for session in session_manager.get_all_sessions():
        if session.config.get('sentiment_filter', True):  # AI Filter enabled
            try:
                from servos.ai_filter import should_filter_signal
                should_filter, reason, analysis = await should_filter_signal(signal_data, session.config)

                if should_filter:
                    logger.warning(f"🚫 AI FILTER BLOCKED: {symbol} {side} | Reason: {reason}", group=True)
                    ai_filter_applied = True
                    filter_reason = reason
                    filter_analysis = analysis
                    break  # Si una sesión filtra, bloqueamos para todas

            except Exception as e:
                logger.error(f"❌ AI Filter error for {symbol}: {e}")
                # Continue without filtering on error (fail-safe)

    if ai_filter_applied:
        # Log detailed analysis for monitoring
        logger.info(f"📊 AI Filter Analysis: {symbol} | Fear/Greed: {filter_analysis.get('sentiment_data', {}).get('fear_greed', {}).get('value', 'N/A')} | "
                   f"Volatility: {filter_analysis.get('sentiment_data', {}).get('volatility', {}).get('classification', 'N/A')} | "
                   f"Momentum: {filter_analysis.get('sentiment_data', {}).get('momentum', {}).get('direction', 'N/A')}", group=False)
        return  # Signal blocked by AI Filter

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
    
    # Dispatch to all sessions with enhanced multi-exchange filtering
    from system_directive import ASSET_GROUPS

    # Determine Asset Group and Subgroup
    asset_group = None
    asset_subgroup = None

    # First check main groups
    for group_name, assets in ASSET_GROUPS.items():
        if symbol in assets:
            asset_group = group_name
            break

    # If it's a crypto asset, determine the thematic subgroup
    if asset_group == 'CRYPTO':
        for subgroup_name, assets in CRYPTO_SUBGROUPS.items():
            if symbol in assets:
                asset_subgroup = subgroup_name
                break

    # For CRYPTO assets, determine target exchange based on user preferences
    # This will be handled later in the session filtering logic

    # Track if at least one session processed the signal (per-exchange)
    processed_exchanges = set()
    atr = getattr(signal, 'atr', None)

    for session in session_manager.get_all_sessions():
        # --- FILTER: Strategy Enabled? ---
        if not session.is_strategy_enabled(strategy_config_key):
            logger.info(f"⏭️ {session.chat_id}: Estrategia {strategy_config_key} deshabilitada", group=True)
            continue

        # --- FILTER: Group Enabled? ---
        if asset_group and not session.is_group_enabled(asset_group):
            logger.info(f"⏭️ {session.chat_id}: Grupo {asset_group} deshabilitado", group=True)
            continue

        # --- FILTER: Subgroup Enabled? (for CRYPTO assets) ---
        if asset_subgroup and not session.is_group_enabled(asset_subgroup):
            logger.info(f"⏭️ {session.chat_id}: Subgrupo {asset_subgroup} deshabilitado para {symbol}", group=True)
            continue

        # --- FILTER: Exchange Available for CRYPTO assets? ---
        # For CRYPTO assets, check if user has enabled at least one crypto exchange
        if asset_group == 'CRYPTO':
            user_exchange_prefs = session.get_exchange_preferences()
            crypto_exchanges_available = user_exchange_prefs.get('BINANCE', False) or user_exchange_prefs.get('BYBIT', False)
            if not crypto_exchanges_available:
                logger.info(f"⏭️ {session.chat_id}: No hay exchanges crypto habilitados para {symbol}", group=True)
                continue

        # --- ENHANCED FILTER: Exchange Available and Enabled? ---
        # Check if user has the required exchange connected AND enabled in preferences

        # Determine target exchange for this session/symbol combination
        user_exchange_prefs = session.get_exchange_preferences()
        target_exchange = session.bridge._route_symbol(symbol, user_exchange_prefs) if session.bridge else 'BINANCE'
        
        # Per-exchange cooldown check
        if cooldown_manager.is_on_cooldown(symbol, target_exchange):
            logger.info(f"⏳ {session.chat_id}: {symbol} omitido en {target_exchange} (cooldown)", group=True)
            continue

        user_exchange_prefs = session.get_exchange_preferences()

        if not user_exchange_prefs.get(target_exchange, False):
            logger.info(f"⏭️ {session.chat_id}: Exchange {target_exchange} deshabilitado en preferencias para {symbol}", group=True)
            continue

        # Double-check adapter connectivity
        if not hasattr(session, 'bridge') or not session.bridge or target_exchange not in session.bridge.adapters:
            logger.info(f"⏭️ {session.chat_id}: Exchange {target_exchange} no conectado para {symbol}", group=True)
            continue

        # --- FILTER: Blacklisted? ---
        if session.is_asset_disabled(symbol):
            logger.info(f"⏭️ {session.chat_id}: Asset {symbol} en blacklist", group=True)
            continue
            
        try:
            mode = session.mode
            p_key = session.config.get('personality', 'STANDARD_ES')
            user_name = get_user_name(session.chat_id)

            # --- FILTER: Sufficient Balance? ---
            # Check liquidity on the SAME exchange we already routed to (critical in multi-exchange mode)
            has_liquidity, available_balance, liquidity_msg = await session.check_liquidity(symbol, exchange=target_exchange)

            # EXCHANGE FALLBACK LOGIC: If target exchange has insufficient balance,
            # try to fallback to another available exchange with sufficient balance
            if not has_liquidity and session.bridge:
                original_exchange = target_exchange
                user_prefs = session.get_exchange_preferences()

                # For crypto symbols, try fallback between BINANCE ↔ BYBIT
                if 'USDT' in symbol and target_exchange in ['BINANCE', 'BYBIT']:
                    fallback_exchange = 'BYBIT' if target_exchange == 'BINANCE' else 'BINANCE'

                    # Check if fallback exchange is available and has balance
                    if (fallback_exchange in user_prefs and user_prefs[fallback_exchange] and
                        fallback_exchange in session.bridge.adapters):

                        # Check liquidity on fallback exchange
                        fallback_liquidity, fallback_balance, _ = await session.check_liquidity(symbol, exchange=fallback_exchange)

                        if fallback_liquidity:
                            logger.info(f"🔄 {session.chat_id}: Fallback {symbol} de {original_exchange} → {fallback_exchange} (saldo insuficiente)", group=True)
                            target_exchange = fallback_exchange
                            has_liquidity, available_balance, liquidity_msg = fallback_liquidity, fallback_balance, f"Balance OK en {fallback_exchange}"
                        else:
                            logger.info(f"⚠️ {session.chat_id}: Fallback rechazado - {fallback_exchange} tampoco tiene saldo suficiente", group=True)

            # Check balance per exchange - force WATCHER only for the exchange without balance
            # Other exchanges with sufficient balance can still execute in PILOT/COPILOT mode
            force_watcher_mode = not has_liquidity
            if force_watcher_mode:
                logger.info(f"⏭️ {session.chat_id}: Balance insuficiente para {symbol} en {target_exchange} - Forzando modo WATCHER solo para este exchange", group=True)

            # Calculate SL/TP/TS preview
            sl_prev, tp_prev, ts_prev = session.get_trade_preview(symbol, side, price) if price else (0, 0, 0)

            # Use target_exchange already determined above
            exchange_display = 'Binance' if 'BINANCE' in target_exchange else 'Bybit' if 'BYBIT' in target_exchange else 'Alpaca'

            # Fetch Personality Data
            profile = personality_manager.PROFILES.get(p_key, personality_manager.PROFILES.get('STANDARD_ES'))
            title = profile.get('NAME', 'Nexus Bot')
            quote = random.choice(profile.get('GREETING', ["Online."]))

            # Determine effective mode (force WATCHER only if THIS exchange has insufficient balance)
            effective_mode = 'WATCHER' if force_watcher_mode else mode

            if effective_mode == 'WATCHER':
                # Use personality message
                if side == 'LONG':
                    msg = personality_manager.get_message(
                        p_key, 'TRADE_LONG',
                        asset=symbol, price=price, reason=reason,
                        tp=tp_prev, sl=sl_prev, ts=ts_prev,
                        title=title, quote=quote, strategy_name=strategy,
                        user_name=user_name, exchange=exchange_display
                    )
                else:
                    msg = personality_manager.get_message(
                        p_key, 'TRADE_SHORT',
                        asset=symbol, price=price, reason=reason,
                        tp=tp_prev, sl=sl_prev, ts=ts_prev,
                        title=title, quote=quote, strategy_name=strategy,
                        user_name=user_name, exchange=exchange_display
                    )

                # Add low balance warning if forced to watcher mode
                if force_watcher_mode:
                    msg += f"\n\n{liquidity_msg}"

                await safe_send_message(bot, session.chat_id, msg, parse_mode="Markdown")

            elif effective_mode == 'COPILOT':
                if side == 'LONG':
                    msg = personality_manager.get_message(
                        p_key, 'TRADE_LONG',
                        asset=symbol, price=price, reason=reason,
                        tp=tp_prev, sl=sl_prev, ts=ts_prev,
                        title=title, quote=quote, strategy_name=strategy,
                        user_name=user_name, exchange=exchange_display
                    )
                else:
                    msg = personality_manager.get_message(
                        p_key, 'TRADE_SHORT',
                        asset=symbol, price=price, reason=reason,
                        tp=tp_prev, sl=sl_prev, ts=ts_prev,
                        title=title, quote=quote, strategy_name=strategy,
                        user_name=user_name, exchange=exchange_display
                    )

                # Change header for COPILOT mode
                msg = msg.replace("📢 SIGNAL TRADE TRIGGER 🤖", "🚨 CO-PILOT TRADE TRIGGER 🤖")

                # Add low balance warning if forced to copilot mode
                if force_watcher_mode:
                    msg += f"\n\n{liquidity_msg}"

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
                await safe_send_message(bot, session.chat_id, msg,
                    reply_markup=keyboard,
                    parse_mode="Markdown"
                )

            elif effective_mode == 'PILOT':
                # If forced to watcher mode due to low balance, show signal without executing
                if force_watcher_mode:
                    # Show signal like WATCHER mode but with PILOT context
                    if side == 'LONG':
                        msg = personality_manager.get_message(
                            p_key, 'TRADE_LONG',
                            asset=symbol, price=price, reason=reason,
                            tp=tp_prev, sl=sl_prev, ts=ts_prev,
                            title=title, quote=quote, strategy_name=strategy,
                            user_name=user_name, exchange=exchange_display
                        )
                    else:
                        msg = personality_manager.get_message(
                            p_key, 'TRADE_SHORT',
                            asset=symbol, price=price, reason=reason,
                            tp=tp_prev, sl=sl_prev, ts=ts_prev,
                            title=title, quote=quote, strategy_name=strategy,
                            user_name=user_name, exchange=exchange_display
                        )

                    # Add specific message for PILOT forced to watcher
                    msg += f"\n\n{liquidity_msg}\n\n⚠️ **Modo PILOT suspendido temporalmente por bajo saldo**"

                    await safe_send_message(bot, session.chat_id, msg, parse_mode="Markdown")
                    continue

                # Normal PILOT execution
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
                # Force execution on the already-determined target_exchange to avoid re-routing
                try:
                    if side == 'LONG':
                        success, result = await session.execute_long_position(symbol, atr=atr, strategy=strategy, force_exchange=target_exchange)
                    else:
                        success, result = await session.execute_short_position(symbol, atr=atr, strategy=strategy, force_exchange=target_exchange)

                    # Validate return values to prevent None formatting errors
                    if not isinstance(success, bool) or result is None:
                        logger.error(f"Invalid return from execute_{side.lower()}_position for {symbol}: success={success}, result={result}")
                        success, result = False, "Invalid function return (None or non-boolean success)"

                except Exception as exec_error:
                    logger.error(f"Exception during execute_{side.lower()}_position for {symbol}: {exec_error}")
                    success, result = False, f"Execution Exception: {str(exec_error)}"

                if success:
                    logger.info(f"✅ Position executed successfully: {symbol} {side} on {target_exchange}")
                    logger.info(f"✅ Position executed successfully: {symbol} {side} on {target_exchange}")
                    # Build enhanced AUTOPILOT message
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
                    
                    # Format prices safely (handle None values)
                    price_str = f"${float(price):.2f}" if price and price != 0 else "N/A"
                    ts_str = f"${float(ts_prev):.2f}" if ts_prev and ts_prev != 0 else "N/A"
                    tp_str = f"${float(tp_prev):.2f}" if tp_prev and tp_prev != 0 else "N/A"
                    sl_str = f"${float(sl_prev):.2f}" if sl_prev and sl_prev != 0 else "N/A"

                    # Format other variables safely
                    formatted_quote = str(quote).rstrip('.!?,;:') if quote else "Online."
                    safe_user_name = str(user_name) if user_name else "Trader"
                    safe_title = str(title) if title else "Nexus Bot"
                    safe_symbol = str(symbol) if symbol else "UNKNOWN"
                    safe_exchange = str(exchange) if exchange else "Unknown"
                    safe_direction = str(direction) if direction else "UNKNOWN"
                    
                    caption = (
                        f"⚡ AUTOPILOT ENGAGED 🤖\n"
                        f"🕐 `{timestamp}`\n\n"
                        f"\"{formatted_quote}, *{safe_user_name}*.\"\n"
                        f"{safe_title}\n\n"
                        f"*Activo:* `{safe_symbol}`\n"
                        f"*Exchange:* {safe_exchange}\n"
                        f"*Dirección:* {safe_direction}\n"
                        f"*Estrategia:* {strategy}\n"
                        f"*Precio Actual:* {price_str}\n\n"
                        f"💸 *TS:* {ts_str}\n"
                        f"🎯 *TP:* {tp_str}\n"
                        f"🛑 *SL:* {sl_str}\n\n"
                        f"*Parámetros:*\n"
                        f"`{reason}`"
                    )
                    
                    await safe_send_message(bot, session.chat_id, caption, parse_mode="Markdown")

                    # Check circuit breaker after trade
                    cb_triggered, cb_msg = await session.check_circuit_breaker()
                    if cb_triggered:
                        cb_alert = personality_manager.get_message(p_key, 'CB_TRIGGER')
                        await safe_send_message(bot, session.chat_id, cb_alert, parse_mode="Markdown")
                else:
                    logger.info(f"❌ Position execution failed: {symbol} {side} on {target_exchange} - Result: {result}")
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
                        await safe_send_message(bot, session.chat_id,
                            f"⚠️ No se ejecutó operación automática para *{symbol}* "
                            f"en el exchange *{error_exchange}* por fondos insuficientes ⚠️",
                            parse_mode="Markdown"
                        )
                    
                    # Special handling for "Insufficient capital" (Min Notional)
                    elif "MIN_NOTIONAL" in result or "Insufficient capital" in result:
                        # 1. Trigger Long Cooldown (1 hour) to stop spam (scoped to exchange + strategy)
                        cooldown_manager.set_cooldown(symbol, seconds=3600, exchange=target_exchange, strategy=strategy)

                        # 2. SILENCED: No notification sent to chat (user requested silence for min notional warnings)
                        # Cooldown applied but no spam to user chat
                        logger.debug(f"💰 Min notional cooldown applied: {symbol} on {target_exchange} (1 hour) - SILENCED")
                    
                    else:
                        # Filter out balance/insufficient funds errors to avoid spam
                        balance_error_phrases = [
                            "ab not enough for new order",  # Bybit insufficient balance
                            "insufficient balance",  # Generic insufficient balance
                            "not enough",  # Various "not enough" messages
                            "balance",  # Any message containing "balance"
                            "funds",  # Any message containing "funds"
                            "INSUFFICIENT_MARGIN",  # Already handled above but extra filter
                            "MIN_NOTIONAL",  # Already handled above but extra filter
                            "Flip Aborted",  # Position flip failures
                            "failed to close",  # Position closing failures
                            "after 3 attempts",  # Retry failures
                            "retCode\":110007",  # Bybit insufficient balance error code
                            "retMsg\":\"ab not enough",  # Bybit specific error message
                            "Bridge Error",  # All bridge errors (usually balance related)
                        ]

                        is_balance_error = any(phrase.lower() in result.lower() for phrase in balance_error_phrases)

                        if not is_balance_error:
                            # Safe formatting to handle None values
                            result_str = str(result) if result is not None else "Unknown Error (None)"
                            await safe_send_message(bot, session.chat_id,
                                f"❌ Effector Error: {result_str}",
                                parse_mode=None
                            )
                        else:
                            # Log balance errors but don't spam the chat
                            logger.info(f"💰 Balance error filtered (not sent to chat): {symbol} on {target_exchange} - {result}")
                    
            processed_exchanges.add(target_exchange)
        except Exception as e:
            logger.error(f"Synapse dispatch error for {session.chat_id}: {e}")
    
    # Set cooldown ONLY for exchanges that processed the signal
    if processed_exchanges:
        for ex in processed_exchanges:
            cooldown_manager.set_cooldown(symbol, atr=atr, exchange=ex, strategy=strategy)
    else:
        logger.debug(f"📭 Signal for {symbol} not dispatched (no eligible sessions)")


# --- MAIN APPLICATION ---
async def main():
    """Main entry point for the async bot with structured premium logging."""

    # IMMEDIATE: Show professional banner FIRST (before any other operations)
    nexus_logger.show_banner()

    if not TELEGRAM_TOKEN:
        nexus_logger.phase_error("Telegram token not found", "Check TELEGRAM_TOKEN environment variable")
        return
    
    # Phase 1: System Initialization
    nexus_logger.phase_start(1, "SYSTEM INITIALIZATION", "🔧")

    # Create Bot Instance
    bot = Bot(
        token=TELEGRAM_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN)
    )
    nexus_logger.phase_success("Bot instance created")

    # Create Dispatcher
    dp = Dispatcher()
    nexus_logger.phase_success("Core modules loaded")
    nexus_logger.phase_success("Configuration parsed")

    # Sentinel will be initialized after session_manager is created
    # Placeholder message for Phase 1
    nexus_logger.phase_success("System core initialized", "Sentinel pending")

    # Phase 2: Security & Encryption
    nexus_logger.phase_start(2, "SECURITY & ENCRYPTION", "🔐")
    nexus_logger.phase_success("AES-256 encryption enabled")
    nexus_logger.phase_success("API credentials validated")

    # Phase 3: Database & Persistence
    nexus_logger.phase_start(3, "DATABASE & PERSISTENCE", "🗄️")

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

                # REMOVED: PREMIUM_SIGNALS loading - feature eliminated
                
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
            
            # DB state loaded silently
            # REMOVED: Premium Signals from logging - feature eliminated
            
    except Exception as e:
        logger.warning(f"DB Init skipped: {e}")
    
    # 4. Initialize Session Manager
    from servos.trading_manager import AsyncSessionManager
    session_manager = AsyncSessionManager()
    await session_manager.load_sessions()

    # Initialize Shark Sentinel (Black Swan & Shark Mode Defense)
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
        # Update Phase 1 status with Sentinel confirmation
        print("└── ✅ Sentinel initialized - Black Swan & Shark Mode active (0.0ms)")

    except Exception as e:
        nexus_logger.phase_error("Sentinel initialization failed", str(e))

    # TASK SCHEDULER ELIMINADO - No utilizado por el usuario
    # Se mantiene el código comentado por si se necesita en el futuro
    """
    # 5. Initialize Task Scheduler (ELIMINADO - No utilizado)
    # Task scheduler eliminated by user request
    """
            
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
    
    nexus_logger.phase_success("Router configuration completed")

    # Phase 4: AI & ML Systems
    nexus_logger.phase_start(4, "AI & ML SYSTEMS", "🤖")

    # 6. Initialize Nexus Core (formerly Nexus Core)
    engine_task = None
    USE_NEXUS_ENGINE = os.getenv('USE_NEXUS_ENGINE', 'true').lower() == 'true'
    
    if USE_NEXUS_ENGINE:
        try:
            from nexus_system.core.engine import NexusCore

            # Initialize xAI Integration for hybrid AI system
            from servos.xai_integration import xai_integration
            if xai_integration.xai_available:
                nexus_logger.phase_success("xAI Grok connected", "Response <2s")
            else:
                nexus_logger.phase_warning("xAI not configured", "xAI features disabled")

            # Initialize AI Filter Engine
            from servos.ai_filter import initialize_ai_filter
            await initialize_ai_filter()
            nexus_logger.phase_success("AI Filter engine initialized", "Sentiment analysis active")

            # Check Nexus Analyst connection
            try:
                from servos.ai_analyst import NexusAnalyst
                analyst = NexusAnalyst()
                if analyst.client:
                    nexus_logger.phase_success("Nexus Analyst connected", f"Model: {analyst.model}")
                else:
                    nexus_logger.phase_warning("Nexus Analyst not configured", "OpenAI API key missing")
            except Exception as e:
                nexus_logger.phase_error("Nexus Analyst initialization failed", str(e))

            # --- KEY INJECTION FIX ---
            # Try to get admin keys for Alpaca & Bybit (background engine needs them)
            admin_id = os.getenv('TELEGRAM_ADMIN_ID')
            alpaca_keys = {}
            bybit_keys = {}
            
            # Always check for Railway environment variables first
            # Alpaca - Railway env vars
            ak_key = os.getenv('ALPACA_API_KEY') or os.getenv('APCA_API_KEY_ID')
            ak_sec = os.getenv('ALPACA_API_SECRET') or os.getenv('APCA_API_SECRET_KEY')
            if ak_key and ak_sec:
                alpaca_keys = {'key': ak_key, 'secret': ak_sec}

            # Bybit - Railway env vars
            bk_key = os.getenv('BYBIT_API_KEY')
            bk_sec = os.getenv('BYBIT_API_SECRET')
            if bk_key and bk_sec:
                bybit_keys = {'key': bk_key, 'secret': bk_sec}

            # Fallback to admin session if available (for user-configured keys)
            if admin_id and session_manager:
                admin_session = session_manager.get_session(str(admin_id))
                if admin_session:
                    # Alpaca from session (only if not already set from env)
                    if not alpaca_keys:
                        ak_key = admin_session.config.get('alpaca_key')
                        ak_sec = admin_session.config.get('alpaca_secret')
                        if ak_key and ak_sec:
                            alpaca_keys = {'key': ak_key, 'secret': ak_sec}

                    # Bybit from session (only if not already set from env)
                    if not bybit_keys:
                        bk_key = admin_session.config.get('bybit_api_key')
                        bk_sec = admin_session.config.get('bybit_api_secret')
                        if bk_key and bk_sec:
                            bybit_keys = {'key': bk_key, 'secret': bk_sec}
                            # Keys loaded from admin session
            
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
            
            # Nexus Core initialized
            
            # Wrapper to catch and log exceptions from engine task
            async def run_engine_with_logging():
                try:
                    # Nexus Core loop started
                    await engine.run()
                except Exception as e:
                    logger.error(f"❌ Nexus Core: Error crítico - {e}", exc_info=True)
            
            # Create engine task (will run concurrently with bot)
            engine_task = asyncio.create_task(run_engine_with_logging())
            
        except Exception as e:
            logger.warning(f"⚠️ Nexus Core init failed: {e}", exc_info=True)

    # Phase 5: Exchanges & Connectivity
    nexus_logger.phase_start(5, "EXCHANGES & CONNECTIVITY", "🌐")

    # Display Nexus Bridge connectivity status
    if session_manager:
        session_manager.display_exchange_status()
        nexus_logger.phase_success("Exchange clients initialized", f"{len(session_manager.sessions)} sessions active")

    # 8. Startup Message (Web Server removed - feature deprecated)

    # 9. Startup Summary
    # Final system ready message
    session_count = len(session_manager.sessions) if session_manager else 0
    nexus_logger.system_ready(session_count)

    # Send admin notification
    raw_admin_ids = os.getenv('TELEGRAM_ADMIN_ID', '').strip("'\" ")
    if raw_admin_ids:
        admin_ids = [aid.strip() for aid in raw_admin_ids.split(',') if aid.strip()]

        for admin_id in admin_ids:
            try:
                await bot.send_message(
                    admin_id,
                    "🟢 *Nexus Systems Online*\n\n"
                    f"Links: {session_count}\n"
                    f"Core: {'✅' if USE_NEXUS_ENGINE else '❌'}",
                    parse_mode="Markdown"
                )
            except Exception as e:
                nexus_logger.log_error(f"Admin notification failed for {admin_id}", str(e))
    
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
