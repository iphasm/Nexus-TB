"""
Antigravity Bot - Async Trading Manager
Async version of TradingSession using python-binance AsyncClient

NOTE: This is a wrapper that provides async interfaces while maintaining 
backward compatibility with the sync TradingSession for gradual migration.
"""

import os
import json
import time
import aiohttp
import asyncio
from typing import Optional, Dict, Any, Tuple, List

# Binance Async Client
from binance import AsyncClient

# AI Analyst
from utils.ai_analyst import QuantumAnalyst

# Alpaca (still sync, but wrapped)
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest, TakeProfitRequest, StopLossRequest
from alpaca.trading.enums import OrderSide, TimeInForce


class AsyncTradingSession:
    """
    Async Trading Session using python-binance AsyncClient.
    Designed for native async/await operations in aiogram.
    """
    
    def __init__(self, chat_id: str, api_key: str, api_secret: str, config: Optional[Dict] = None):
        self.chat_id = chat_id
        self.api_key = api_key
        self.api_secret = api_secret
        self.client: Optional[AsyncClient] = None
        self.alpaca_client: Optional[TradingClient] = None
        
        # Default Config
        self.config = {
            "mode": "WATCHER",
            "leverage": 5,
            "max_capital_pct": 0.10,
            "stop_loss_pct": 0.02,
            "spot_allocation_pct": 0.20,
            "personality": "STANDARD_ES",
            "sentiment_filter": False,
            "atr_multiplier": 2.0,
            "alpaca_key": None,
            "alpaca_secret": None
        }
        
        if config:
            self.config.update(config)
        
        
        # --- MULTI-TENANT CONFIG INITIALIZATION ---
        # SECURE DEFAULTS: Start with everything DISABLED for new sessions
        if 'strategies' not in self.config:
            # Empty dict means all False by default
            self.config['strategies'] = {}
            
        if 'groups' not in self.config:
            # Empty dict means all False by default
            self.config['groups'] = {}
             
        if 'disabled_assets' not in self.config:
             self.config['disabled_assets'] = []
             
        self.mode = self.config.get('mode', 'WATCHER')
        
        # Circuit Breaker State
        self.cb_ignore_until = 0  # Timestamp (ms) to ignore previous losses
        
        # AI Analyst
        self.ai_analyst = QuantumAnalyst()
        
        # Operation Lock: Prevent concurrent/spam operations per symbol
        self._operation_locks = {}  # {symbol: timestamp}
        self._lock_duration = 30  # seconds
        
        # Proxy Setup
        self._proxy = os.getenv('PROXY_URL') or os.getenv('HTTPS_PROXY') or os.getenv('HTTP_PROXY')
    
    async def initialize(self) -> bool:
        """Async initialization of exchange clients."""
        success = True
        
        # 1. Initialize Binance Async Client
        if self.api_key and self.api_secret:
            try:
                self.client = await AsyncClient.create(
                    self.api_key, 
                    self.api_secret
                )
                
                # Direct proxy assignment to avoid kwargs conflict
                # This ensures python-binance uses the proxy param internally
                if self._proxy:
                    print(f"🔄 [Chat {self.chat_id}] Configuring Proxy Session...")
                    
                    # 1. Preserve Defaults (User-Agent, potentially others)
                    headers = self.client.session._default_headers
                    if not headers:
                        headers = {"User-Agent": "binance-connector-python/1.0.0"} # Fallback

                    # 2. Close default session
                    await self.client.close_connection()
                    
                    # 3. Set Env Vars
                    os.environ['HTTPS_PROXY'] = self._proxy
                    os.environ['HTTP_PROXY'] = self._proxy
                    
                    # 4. Create NEW session with trust_env=True AND preserved headers
                    # Increase timeout to 45s for slow proxies
                    timeout = aiohttp.ClientTimeout(total=45)
                    self.client.session = aiohttp.ClientSession(
                        timeout=timeout,
                        headers=headers,
                        trust_env=True
                    )
                
                print(f"✅ [Chat {self.chat_id}] Binance Client Init (Proxy: Forced, Key: ...{self.api_key[-4:]})")
            except Exception as e:
                self._init_error = str(e)
                print(f"❌ [Chat {self.chat_id}] Binance Init Error: {e}")
                self.client = None
                success = False
        
        # 2. Initialize Alpaca (still sync but wrapped)
        await self.initialize_alpaca()
        
        return success
    
    async def initialize_alpaca(self):
        """Initialize Alpaca client from config or env."""
        ak = self.config.get('alpaca_key') or os.getenv('APCA_API_KEY_ID', '').strip().strip("'\"")
        ask = self.config.get('alpaca_secret') or os.getenv('APCA_API_SECRET_KEY', '').strip().strip("'\"")
        base_url = os.getenv('APCA_API_BASE_URL', '').strip().strip("'\"")
        
        if ak and ask:
            try:
                # Determine paper mode
                paper = True
                if base_url:
                    if base_url.endswith('/v2'):
                        base_url = base_url[:-3]
                    if 'paper' not in base_url and 'api.alpaca' in base_url:
                        paper = False
                
                self.alpaca_client = TradingClient(ak, ask, paper=paper, url_override=base_url)
                print(f"✅ [Chat {self.chat_id}] Alpaca Client Initialized (Paper: {paper})")
            except Exception as e:
                print(f"❌ [Chat {self.chat_id}] Alpaca Init Error: {e}")
    
    async def close(self):
        """Cleanup resources."""
        if self.client:
            await self.client.close_connection()
            self.client = None
    
    # --- CONFIG METHODS ---
    
    def set_mode(self, mode: str) -> bool:
        """Set operation mode."""
        if mode in ['WATCHER', 'COPILOT', 'PILOT']:
            self.mode = mode
            self.config['mode'] = mode
            return True
        return False
    
    async def update_config(self, key: str, value: Any) -> bool:
        """Update a config value."""
        self.config[key] = value
        return True
    
    def get_configuration(self) -> Dict:
        """Get current configuration."""
        return {
            "mode": self.mode,
            "leverage": self.config['leverage'],
            "max_capital_pct": self.config['max_capital_pct'],
            "stop_loss_pct": self.config['stop_loss_pct'],
            "has_keys": bool(self.client),
            "strategies": self.config.get('strategies', {}),
            "groups": self.config.get('groups', {}),
            "disabled_assets": self.config.get('disabled_assets', [])
        }
        
    def toggle_strategy(self, strategy: str) -> bool:
        """Toggle a specific strategy on/off."""
        strategies = self.config.get('strategies', {})
        current = strategies.get(strategy, False)
        strategies[strategy] = not current
        self.config['strategies'] = strategies
        return strategies[strategy]

    def is_strategy_enabled(self, strategy: str) -> bool:
        """Check if strategy is enabled."""
        return self.config.get('strategies', {}).get(strategy, False)

    def toggle_group(self, group: str) -> bool:
        """Toggle a specific asset group on/off."""
        groups = self.config.get('groups', {})
        current = groups.get(group, False)
        groups[group] = not current
        self.config['groups'] = groups
        return groups[group]

    def is_group_enabled(self, group: str) -> bool:
        """Check if group is enabled."""
        return self.config.get('groups', {}).get(group, False)

    def toggle_asset_blacklist(self, symbol: str) -> bool:
        """Toggle asset in blacklist. Returns True if now DISABLED (in list)."""
        disabled = self.config.get('disabled_assets', [])
        if symbol in disabled:
            disabled.remove(symbol)
            result = False
        else:
            disabled.append(symbol)
            result = True
        self.config['disabled_assets'] = disabled
        return result

    def is_asset_disabled(self, symbol: str) -> bool:
        """Check if asset is in blacklist."""
        return symbol in self.config.get('disabled_assets', [])
    
    # --- HELPER METHODS ---
    
    async def get_symbol_precision(self, symbol: str) -> Tuple[int, int, float]:
        """Returns (quantityPrecision, pricePrecision, minNotional)"""
        if not self.client:
            return 2, 2, 5.0
        
        try:
            info = await self.client.futures_exchange_info()
            for s in info['symbols']:
                if s['symbol'] == symbol:
                    min_notional = 5.0
                    for f in s['filters']:
                        if f['filterType'] == 'MIN_NOTIONAL':
                            min_notional = float(f.get('notional', 5.0))
                            break
                    return s['quantityPrecision'], s['pricePrecision'], min_notional
        except Exception as e:
            print(f"Precision Error for {symbol}: {e}")
        
        return 2, 2, 5.0
    
    # --- TRADING METHODS ---
    
    async def _ensure_client(self) -> Tuple[bool, str]:
        """Ensure Binance client is initialized."""
        if self.client:
            return True, ""
        
        # Try to re-initialize lazy
        print(f"🔄 [Chat {self.chat_id}] Attempting lazy re-initialization...")
        await self.initialize()
        err = getattr(self, '_init_error', 'Unknown Error')
        return False, f"Client Connection Failed: {err}"

    async def _place_order_with_retry(self, func, **kwargs):
        """Helper: Place order with retries for -1007/Timeout"""
        for attempt in range(1, 4):
            try:
                return await func(**kwargs)
            except Exception as e:
                if "timeout" in str(e).lower() or "network" in str(e).lower() or "-1007" in str(e):
                    if attempt < 3:
                        await asyncio.sleep(attempt)
                        continue
                raise e
        raise Exception("Max retries exceeded")

    async def synchronize_sl_tp_safe(self, symbol: str, quantity: float, sl_price: float, tp_price: float, side: str, min_notional: float, qty_precision: int, entry_price: float = 0.0) -> Tuple[bool, str]:
        """
        Surgical SL/TP Synchronization (V2 - Anti-Spam):
        1. Check if valid SL/TP already exists (skip if within 1% tolerance).
        2. Cancel existing STOP_MARKET / TAKE_PROFIT_MARKET / TRAILING_STOP_MARKET.
        3. Verify cancellation succeeded before proceeding.
        4. Place new SL/TP with reduceOnly=True.
        """
        try:
            # 1. Fetch existing orders
            orders = await self.client.futures_get_open_orders(symbol=symbol)
            
            existing_sl = None
            existing_tp_count = 0
            to_cancel = []
            
            for o in orders:
                order_type = o.get('type', '')
                if order_type == 'STOP_MARKET':
                    existing_sl = float(o.get('stopPrice', 0))
                    to_cancel.append(o['orderId'])
                elif order_type in ['TAKE_PROFIT_MARKET', 'TRAILING_STOP_MARKET']:
                    existing_tp_count += 1
                    to_cancel.append(o['orderId'])
            
            # 2. Check if existing SL is within 1% tolerance - SKIP UPDATE
            if existing_sl and sl_price > 0:
                tolerance = abs(existing_sl - sl_price) / sl_price
                if tolerance < 0.01 and existing_tp_count >= 1:
                    return True, f"✅ SL/TP ya configurados (SL: {existing_sl:.2f}, TP count: {existing_tp_count}). Sin cambios."
            
            # 3. Cancel existing SL/TP orders
            if to_cancel:
                print(f"🔄 {symbol}: Cancelling {len(to_cancel)} existing SL/TP orders...")
                for oid in to_cancel:
                    try:
                        await self.client.futures_cancel_order(symbol=symbol, orderId=oid)
                    except Exception as ce:
                        if 'Unknown order' not in str(ce):
                            print(f"⚠️ Cancel warning for {oid}: {ce}")
                
                # 4. VERIFY cancellation succeeded
                await asyncio.sleep(0.5)
                remaining = await self.client.futures_get_open_orders(symbol=symbol)
                remaining_sltp = [o for o in remaining if o.get('type', '') in ['STOP_MARKET', 'TAKE_PROFIT_MARKET', 'TRAILING_STOP_MARKET']]
                
                if remaining_sltp:
                    print(f"⚠️ {symbol}: {len(remaining_sltp)} orders still exist after cancel. Force retry...")
                    for o in remaining_sltp:
                        try:
                            await self.client.futures_cancel_order(symbol=symbol, orderId=o['orderId'])
                        except:
                            pass
                    await asyncio.sleep(0.5)
            
            # 5. Place new SL (reduceOnly)
            sl_msg = ""
            abs_qty = abs(quantity)
            if sl_price > 0:
                sl_side = 'SELL' if side == 'LONG' else 'BUY'
                await self._place_order_with_retry(
                    self.client.futures_create_order,
                    symbol=symbol, side=sl_side, type='STOP_MARKET',
                    stopPrice=sl_price, quantity=abs_qty, reduceOnly=True
                )
                sl_msg = f"SL: {sl_price}"
                
            # 6. Place TP (split or single trailing)
            tp_msg = ""
            sl_side = 'SELL' if side == 'LONG' else 'BUY'
            
            qty_tp1 = float(round(abs_qty / 2, qty_precision))
            qty_trail = float(round(abs_qty - qty_tp1, qty_precision))
            
            # Check split feasibility
            current_price = sl_price if sl_price > 0 else tp_price
            is_split = current_price > 0 and (qty_tp1 * current_price) > min_notional and (qty_trail * current_price) > min_notional
            
            if is_split:
                # TP1 (fixed)
                await self._place_order_with_retry(
                    self.client.futures_create_order,
                    symbol=symbol, side=sl_side, type='TAKE_PROFIT_MARKET',
                    stopPrice=tp_price, quantity=qty_tp1, reduceOnly=True
                )
                # Trailing for rest
                activation = entry_price if entry_price > 0 else tp_price
                await self._place_order_with_retry(
                    self.client.futures_create_order,
                    symbol=symbol, side=sl_side, type='TRAILING_STOP_MARKET',
                    quantity=qty_trail, callbackRate=2.0, activationPrice=activation, reduceOnly=True
                )
                tp_msg = f"TP1: {tp_price} | Trail: 2.0% (Act: {activation})"
            else:
                # Full trailing
                activation = entry_price if entry_price > 0 else tp_price
                await self._place_order_with_retry(
                    self.client.futures_create_order,
                    symbol=symbol, side=sl_side, type='TRAILING_STOP_MARKET',
                    quantity=abs_qty, callbackRate=2.0, activationPrice=activation, reduceOnly=True
                )
                tp_msg = f"Trail: {activation} (2.0%)"
            
            return True, f"{sl_msg}\n{tp_msg}"
            
        except Exception as e:
            return False, f"Sync Error: {e}"

    async def execute_long_position(self, symbol: str, atr: Optional[float] = None) -> Tuple[bool, str]:
        """Execute a LONG position asynchronously."""
        
        # Route non-crypto to Alpaca
        if 'USDT' not in symbol:
            return await self._execute_alpaca_order(symbol, 'LONG', atr)
        
        # Ensure Client with retry
        ok, err = await self._ensure_client()
        if not ok:
            return False, err
        
        # --- AI SENTIMENT & MACRO FILTER ---
        vol_risk = 'LOW'  # Default for later use
        from antigravity_quantum.config import AI_FILTER_ENABLED
        if AI_FILTER_ENABLED and self.config.get('sentiment_filter', True) and self.ai_analyst and self.ai_analyst.client:
            try:
                print(f"🧠 Checking Sentiment for {symbol}...")
                sent = self.ai_analyst.check_market_sentiment(symbol)
                score = sent.get('score', 0)
                vol_risk = sent.get('volatility_risk', 'LOW')
                
                # Filter: BAD Sentiment
                thresh = self.config.get('sentiment_threshold', -0.6)
                if score < thresh:
                    return False, f"⛔ **IA FILTER [{symbol}]**: Mercado muy negativo ({score:.2f} < {thresh}).\nMotivo: {sent.get('reason', 'N/A')}"
                
                # Macro Shield: Reduce Leverage on High Volatility
                if vol_risk in ['HIGH', 'EXTREME']:
                    current_lev = self.config['leverage']
                    if current_lev > 3:
                        print(f"⚠️ High Volatility ({vol_risk}). Reducing Leverage to 3x.")
                        self.config['leverage'] = 3
            except Exception as e:
                print(f"⚠️ AI Filter Error (continuing): {e}")
        
        try:
            leverage = self.config['leverage']
            max_capital_pct = self.config['max_capital_pct']
            stop_loss_pct = self.config['stop_loss_pct']
            
            # 1. Check Existing Position
            positions = await self.client.futures_position_information(symbol=symbol)
            net_qty = sum(float(p['positionAmt']) for p in positions)
            
            if net_qty != 0:
                if net_qty > 0:
                    return await self.execute_update_sltp(symbol, 'LONG', atr)
                else:
                    # Auto-Flip: Long requested but Short exists
                    print(f"🔄 Auto-Flip Triggered: Long requested for {symbol} (Current: Short)")
                    return await self.execute_flip_position(symbol, 'LONG', atr)
            
            # 2. Set Leverage
            await self.client.futures_change_leverage(symbol=symbol, leverage=leverage)
            
            # 3. Cancel Existing Orders (Robust with Retry)
            try:
                # Retry cancellation up to 3 times
                for _ in range(3):
                    try:
                        await self.client.futures_cancel_all_open_orders(symbol=symbol)
                        break
                    except Exception as e:
                        if "Unknown order" in str(e): break # Already clear
                        await asyncio.sleep(0.5)
                
                # Wait for propagation (increased to prevent timeout)
                await asyncio.sleep(0.6)
            except Exception as e:
                print(f"⚠️ Cancel Order Warning: {e}")
            
            # 4. Get Account & Price Info
            acc_info = await self.client.futures_account()
            total_equity = float(acc_info.get('totalMarginBalance', 0))
            
            ticker = await self.client.futures_symbol_ticker(symbol=symbol)
            current_price = float(ticker['price'])
            
            qty_precision, price_precision, min_notional = await self.get_symbol_precision(symbol)
            
            # 5. Calculate Position Size
            if atr and atr > 0:
                mult = self.config.get('atr_multiplier', 2.0)
                sl_dist = mult * atr
                sl_price = round(current_price - sl_dist, price_precision)
                
                risk_amount = total_equity * 0.02
                raw_quantity = risk_amount / sl_dist
                
                # Min notional check (increased buffer to 1.15x to prevent rounding issues)
                notional = raw_quantity * current_price
                if notional < min_notional:
                    raw_quantity = (min_notional * 1.15) / current_price
                
                # Max allocation check
                if (raw_quantity * current_price / leverage) > (total_equity * max_capital_pct):
                    raw_quantity = (total_equity * max_capital_pct * leverage) / current_price
                
                tp_price = round(current_price + (1.5 * sl_dist), price_precision)
            else:
                margin_assignment = total_equity * max_capital_pct
                raw_quantity = (margin_assignment * leverage) / current_price
                sl_price = round(current_price * (1 - stop_loss_pct), price_precision)
                tp_price = round(current_price * (1 + (stop_loss_pct * 3)), price_precision)
            
            quantity = float(round(raw_quantity, qty_precision))
            
            # Final notional check
            final_notional = quantity * current_price
            if final_notional < min_notional:
                return False, f"❌ {symbol}: Insufficient capital for min notional ({min_notional} USDT)."
            
            if quantity <= 0:
                return False, "Position size too small."
            
            # 6. Execute Market Buy (Retry Logic for Timeouts)
            try:
                order = None
                for attempt in range(1, 4):  # 3 Attempts
                    try:
                        order = await self.client.futures_create_order(
                            symbol=symbol, side='BUY', type='MARKET', quantity=quantity
                        )
                        break
                    except Exception as e:
                        # Retry only on timeouts or network errors
                        if "timeout" in str(e).lower() or "network" in str(e).lower() or "-1007" in str(e):
                            if attempt < 3:
                                wait_time = 2 * (2 ** (attempt - 1))  # 2s, 4s
                                print(f"⚠️ Timeout opening {symbol} (Attempt {attempt}/3). Retrying in {wait_time}s...")
                                await asyncio.sleep(wait_time)
                                continue
                        raise e
                
                if not order:
                    raise Exception("Max retries exceeded for order placement")
                    
                entry_price = float(order.get('avgPrice', current_price)) or current_price
            except Exception as e:
                return False, f"❌ Failed to open position: {e}"
            
            # 7. Place SL/TP Orders (Using reduceOnly to avoid -4130)
            try:
                # Stop Loss with explicit quantity
                if sl_price > 0:
                    await self.client.futures_create_order(
                        symbol=symbol, side='SELL', type='STOP_MARKET',
                        stopPrice=sl_price, reduceOnly=True, quantity=quantity
                    )
                
                # Logic: TP1 (50%) + Trailing Stop (50%)
                qty_tp1 = float(round(quantity / 2, qty_precision))
                qty_trail = float(round(quantity - qty_tp1, qty_precision))
                
                # Check Min Notional for split (must be > 5 USDT each approx)
                is_split = (qty_tp1 * current_price) > min_notional and (qty_trail * current_price) > min_notional
                
                if is_split:
                    # TP1: Take 50% Prophet
                    await self.client.futures_create_order(
                        symbol=symbol, side='SELL', type='TAKE_PROFIT_MARKET',
                        stopPrice=tp_price, quantity=qty_tp1, reduceOnly=True
                    )
                    # Trailing: Let the rest run (Activate at Entry, Callback 2.0%)
                    await self.client.futures_create_order(
                        symbol=symbol, side='SELL', type='TRAILING_STOP_MARKET',
                        quantity=qty_trail, callbackRate=2.0, activationPrice=entry_price, reduceOnly=True
                    )
                    tp_msg = f"TP1: {tp_price} (50%) | Trail: 2.0% (Act: {entry_price})"
                else:
                    # Capital too small: Full Trailing Stop
                    await self.client.futures_create_order(
                        symbol=symbol, side='SELL', type='TRAILING_STOP_MARKET',
                        quantity=quantity, callbackRate=2.0, activationPrice=entry_price, reduceOnly=True
                    )
                    tp_msg = f"Trailing Stop: {entry_price} (2.0%)"
                
                success_msg = (
                    f"Long {symbol} (x{leverage})\n"
                    f"Entry: {entry_price}\n"
                    f"Qty: {quantity}\n"
                    f"SL: {sl_price}\n"
                    f"TP: {tp_msg}"
                )
                
                return True, success_msg
                
            except Exception as e:
                # Rollback: Close position if SL/TP fails
                print(f"⚠️ SL/TP Failed: {e}. Closing position...")
                try:
                    await self.client.futures_create_order(
                        symbol=symbol, side='SELL', type='MARKET',
                        quantity=quantity, reduceOnly=True
                    )
                except:
                    pass
                return False, f"⚠️ SL/TP placement failed ({e}). Position closed for safety."
        
        except Exception as e:
            return False, f"[{symbol}] Error: {str(e)}"
    
    async def execute_short_position(self, symbol: str, atr: Optional[float] = None) -> Tuple[bool, str]:
        """Execute a SHORT position asynchronously."""
        
        # Route non-crypto to Alpaca
        if 'USDT' not in symbol:
            return await self._execute_alpaca_order(symbol, 'SHORT', atr)
        
        if not self.client:
            return False, "No valid API Keys provided."
        
        # --- AI SENTIMENT FILTER (Inverse for Shorts) ---
        from antigravity_quantum.config import AI_FILTER_ENABLED
        if AI_FILTER_ENABLED and self.config.get('sentiment_filter', True) and self.ai_analyst and self.ai_analyst.client:
            try:
                print(f"🧠 Checking Sentiment for {symbol} (SHORT)...")
                sent = self.ai_analyst.check_market_sentiment(symbol)
                score = sent.get('score', 0)
                
                # Filter: BULLISH Sentiment (bad for shorts)
                if score > 0.6:
                    return False, f"⛔ **IA FILTER [{symbol}]**: Mercado muy alcista ({score:.2f}).\nMotivo: {sent.get('reason', 'N/A')}"
            except Exception as e:
                print(f"⚠️ AI Filter Error (continuing): {e}")
        
        try:
            leverage = self.config['leverage']
            max_capital_pct = self.config['max_capital_pct']
            stop_loss_pct = self.config['stop_loss_pct']
            
            # 1. Check Existing Position
            positions = await self.client.futures_position_information(symbol=symbol)
            net_qty = sum(float(p['positionAmt']) for p in positions)
            
            if net_qty != 0:
                if net_qty < 0:
                    return await self.execute_update_sltp(symbol, 'SHORT', atr)
                else:
                    # Auto-Flip: Short requested but Long exists
                    print(f"🔄 Auto-Flip Triggered: Short requested for {symbol} (Current: Long)")
                    return await self.execute_flip_position(symbol, 'SHORT', atr)
            
            # 2. Set Leverage & Cancel Orders
            await self.client.futures_change_leverage(symbol=symbol, leverage=leverage)
            try:
                # Retry cancellation up to 3 times
                for _ in range(3):
                    try:
                        await self.client.futures_cancel_all_open_orders(symbol=symbol)
                        break
                    except Exception as e:
                        if "Unknown order" in str(e): break
                        await asyncio.sleep(0.5)
                
                await asyncio.sleep(0.6)
            except Exception as e:
                print(f"⚠️ Cancel Order Warning: {e}")
            
            # 3. Get Info
            qty_precision, price_precision, min_notional = await self.get_symbol_precision(symbol)
            ticker = await self.client.futures_ticker(symbol=symbol)
            current_price = float(ticker['lastPrice'])
            
            acc = await self.client.futures_account()
            equity = float(acc['totalWalletBalance'])
            
            # 4. Calculate Size
            if atr and atr > 0:
                mult = self.config.get('atr_multiplier', 2.0)
                sl_dist = mult * atr
                sl_price = round(current_price + sl_dist, price_precision)
                tp_price = round(current_price - (1.5 * sl_dist), price_precision)
            else:
                sl_price = round(current_price * (1 + stop_loss_pct), price_precision)
                tp_price = round(current_price * (1 - (stop_loss_pct * 3)), price_precision)
            
            dist_to_stop = abs(sl_price - current_price) or (current_price * 0.01)
            risk_amount = equity * 0.02
            raw_quantity = risk_amount / dist_to_stop
            
            # Min notional check (increased buffer to 1.15x to prevent rounding issues)
            notional = raw_quantity * current_price
            if notional < min_notional:
                raw_quantity = (min_notional * 1.15) / current_price
            
            max_alloc = equity * max_capital_pct
            if (raw_quantity * current_price) > max_alloc:
                raw_quantity = max_alloc / current_price
            
            quantity = float(round(raw_quantity, qty_precision))
            
            if (quantity * current_price) < min_notional:
                return False, f"❌ {symbol}: Insufficient capital for min notional."
            
            if quantity <= 0:
                return False, "Position size too small."
            
            # 5. Execute Market Sell (Retry Logic)
            try:
                order = None
                for attempt in range(1, 4):  # 3 Attempts
                    try:
                        order = await self.client.futures_create_order(
                            symbol=symbol, side='SELL', type='MARKET', quantity=quantity
                        )
                        break
                    except Exception as e:
                        if "timeout" in str(e).lower() or "network" in str(e).lower() or "-1007" in str(e):
                            if attempt < 3:
                                wait_time = 2 * (2 ** (attempt - 1))
                                print(f"⚠️ Timeout opening {symbol} (Attempt {attempt}/3). Retrying in {wait_time}s...")
                                await asyncio.sleep(wait_time)
                                continue
                        raise e
                
                if not order:
                    raise Exception("Max retries exceeded")
                
                entry_price = float(order.get('avgPrice', current_price)) or current_price
            except Exception as e:
                return False, f"❌ Failed to open position: {e}"
            
            # 6. Place SL/TP (Using reduceOnly to avoid -4130)
            try:
                if sl_price > 0:
                    await self.client.futures_create_order(
                        symbol=symbol, side='BUY', type='STOP_MARKET',
                        stopPrice=sl_price, reduceOnly=True, quantity=quantity
                    )
                
                # Logic: TP1 (50%) + Trailing Stop (50%)
                qty_tp1 = float(round(quantity / 2, qty_precision))
                qty_trail = float(round(quantity - qty_tp1, qty_precision))
                
                is_split = (qty_tp1 * current_price) > min_notional and (qty_trail * current_price) > min_notional
                
                if is_split:
                    # TP1 (50%)
                    await self.client.futures_create_order(
                        symbol=symbol, side='BUY', type='TAKE_PROFIT_MARKET',
                        stopPrice=tp_price, quantity=qty_tp1, reduceOnly=True
                    )
                    # Trailing Stop (50%)
                    await self.client.futures_create_order(
                        symbol=symbol, side='BUY', type='TRAILING_STOP_MARKET',
                        quantity=qty_trail, callbackRate=2.0, activationPrice=entry_price, reduceOnly=True
                    )
                    tp_msg = f"TP1: {tp_price} (50%) | Trail: 2.0% (Act: {entry_price})"
                else:
                    await self.client.futures_create_order(
                        symbol=symbol, side='BUY', type='TRAILING_STOP_MARKET',
                        quantity=quantity, callbackRate=2.0, activationPrice=entry_price, reduceOnly=True
                    )
                    tp_msg = f"Trailing Stop: {entry_price} (2.0%)"
                
                return True, (
                    f"Short {symbol} (x{leverage})\n"
                    f"Entry: {entry_price}\n"
                    f"Qty: {quantity}\n"
                    f"SL: {sl_price}\n"
                    f"TP: {tp_msg}"
                )
                
            except Exception as e:
                print(f"⚠️ SL/TP Failed: {e}. Closing position...")
                try:
                    await self.client.futures_create_order(
                        symbol=symbol, side='BUY', type='MARKET',
                        quantity=quantity, reduceOnly=True
                    )
                except:
                    pass
                return False, f"⚠️ SL/TP failed ({e}). Position closed for safety."
        
        except Exception as e:
            return False, f"[{symbol}] Error: {str(e)}"
    
    async def execute_close_position(self, symbol: str) -> Tuple[bool, str]:
        """Close position for a symbol."""
        
        # Route non-crypto to Alpaca
        if 'USDT' not in symbol and self.alpaca_client:
            try:
                self.alpaca_client.cancel_orders()
                self.alpaca_client.close_position(symbol)
                return True, f"✅ (Alpaca) Closed {symbol}."
            except Exception as e:
                return False, f"Alpaca Error: {e}"
        
        if not self.client:
            return False, "No valid session."
        
        try:
            # Cancel orders (Retry Logic)
            for _ in range(3):
                try:
                    await self.client.futures_cancel_all_open_orders(symbol=symbol)
                    break
                except Exception as e:
                    if "Unknown order" in str(e): break
                    await asyncio.sleep(0.5)
            
            # Get position
            positions = await self.client.futures_position_information(symbol=symbol)
            qty = 0.0
            for p in positions:
                if p['symbol'] == symbol:
                    qty = float(p['positionAmt'])
                    break
            
            if qty == 0:
                return True, f"⚠️ No position found for {symbol}, orders canceled."
            
            # Close (Retry Logic)
            side = 'SELL' if qty > 0 else 'BUY'
            
            for attempt in range(1, 4):
                try:
                    await self.client.futures_create_order(
                        symbol=symbol, side=side, type='MARKET',
                        reduceOnly=True, quantity=abs(qty)
                    )
                    break
                except Exception as e:
                    if "timeout" in str(e).lower() or "-1007" in str(e):
                        if attempt < 3:
                            await asyncio.sleep(1.0)
                            continue
                    raise e
            
            return True, f"✅ Closed {symbol} ({qty})."
            
        except Exception as e:
            return False, f"Error: {e}"
    
    async def execute_close_all(self) -> Tuple[bool, str]:
        """Close all open positions."""
        if not self.client:
            return False, "No valid session."
        
        active = await self.get_active_positions()
        if not active:
            return False, "No active positions."
        
        results = []
        for p in active:
            sym = p['symbol']
            success, msg = await self.execute_close_position(sym)
            results.append(f"{sym}: {'✅' if success else '❌'}")
        
        return True, "Batch Close:\n" + "\n".join(results)

    async def execute_refresh_all_orders(self) -> str:
        """
        Refresh SL/TP/Trailing for ALL active positions.
        Forces update based on CURRENT price (Trailing) and Config (SL/TP %).
        """
        if not self.client:
            return "❌ No invalid session."

        try:
            active_pos = await self.get_active_positions()
            if not active_pos:
                return "ℹ️ No hay posiciones activas para sincronizar."

            report = ["🔄 **Reporte de Sincronización:**", ""]
            
            for p in active_pos:
                symbol = p['symbol']
                qty = float(p['positionAmt'])
                if qty == 0: continue

                side = 'LONG' if qty > 0 else 'SHORT'
                entry_price = float(p['entryPrice'])
                
                # Get current price
                ticker = await self.client.futures_symbol_ticker(symbol=symbol)
                current_price = float(ticker['price'])
                
                # Get precision
                qty_prec, price_prec, min_notional = await self.get_symbol_precision(symbol)

                # Calculate standard SL/TP based on entry (or current if preferred, but usually entry for fixed SL)
                # However, for TRAILING activation, we want to use ENTRY PRICE as per user request.
                # Standard SL/TP logic:
                stop_loss_pct = self.config['stop_loss_pct']
                
                if side == 'LONG':
                    # SL is below entry
                    sl_price = round(entry_price * (1 - stop_loss_pct), price_prec)
                    # TP is above entry
                    tp_price = round(entry_price * (1 + (stop_loss_pct * 3)), price_prec)
                else:
                    # SL is above entry
                    sl_price = round(entry_price * (1 + stop_loss_pct), price_prec)
                    # TP is below entry
                    tp_price = round(entry_price * (1 - (stop_loss_pct * 3)), price_prec)

                # Execute Sync
                success, msg = await self.synchronize_sl_tp_safe(
                    symbol, qty, sl_price, tp_price, side, min_notional, qty_prec, entry_price=entry_price
                )
                
                status_icon = "✅" if success else "⚠️"
                report.append(f"**{symbol}** ({side}) {status_icon}")
                if success:
                    report.append(f"   SL: {sl_price} | TP: {tp_price}")
                    report.append(f"   TS Act: {entry_price} (Entry)")
                else:
                    report.append(f"   Err: {msg}")
                report.append("")

            return "\n".join(report)

        except Exception as e:
            return f"❌ Error Critical en Sync: {e}"
    
    async def execute_update_sltp(self, symbol: str, side: str, atr: Optional[float] = None) -> Tuple[bool, str]:
        """Update SL/TP for existing position. Includes spam protection."""
        if not self.client:
            return False, "No session."
        
        # PERSISTENT COOLDOWN: Check global per-symbol cooldown
        from antigravity_quantum.config import SLTP_UPDATE_COOLDOWN, SLTP_LAST_UPDATE
        now = time.time()
        last_update = SLTP_LAST_UPDATE.get(symbol, 0)
        
        if now - last_update < SLTP_UPDATE_COOLDOWN:
            remaining = int(SLTP_UPDATE_COOLDOWN - (now - last_update))
            return False, f"⏳ {symbol} SL/TP updated recently. Wait {remaining//60}m {remaining%60}s."
        
        # OPERATION LOCK: Short-term lock to prevent concurrent updates
        if symbol in self._operation_locks:
            elapsed = now - self._operation_locks[symbol]
            if elapsed < self._lock_duration:
                remaining = int(self._lock_duration - elapsed)
                return False, f"⏳ {symbol} update in progress. Wait {remaining}s."
        
        # Lock this symbol
        self._operation_locks[symbol] = now
        
        try:
            # Get position
            positions = await self.client.futures_position_information(symbol=symbol)
            qty = 0.0
            for p in positions:
                amt = float(p['positionAmt'])
                if amt != 0:
                    qty = amt
                    break
            
            if qty == 0:
                return False, "No position found to update."
            
            curr_side = 'LONG' if qty > 0 else 'SHORT'
            if curr_side != side:
                return False, f"Side mismatch (Req: {side}, Has: {curr_side})."
            
            # Get new price info
            ticker = await self.client.futures_symbol_ticker(symbol=symbol)
            current_price = float(ticker['price'])
            qty_precision, price_precision, min_notional = await self.get_symbol_precision(symbol)
            
            stop_loss_pct = self.config['stop_loss_pct']
            
            # Calculate updated SL/TP
            if atr and atr > 0:
                mult = self.config.get('atr_multiplier', 2.0)
                sl_dist = mult * atr
                if side == 'LONG':
                    sl_price = round(current_price - sl_dist, price_precision)
                    tp_price = round(current_price + (1.5 * sl_dist), price_precision)
                else:
                    sl_price = round(current_price + sl_dist, price_precision)
                    tp_price = round(current_price - (1.5 * sl_dist), price_precision)
            else:
                if side == 'LONG':
                    sl_price = round(current_price * (1 - stop_loss_pct), price_precision)
                    tp_price = round(current_price * (1 + (stop_loss_pct * 3)), price_precision)
                else:
                    sl_price = round(current_price * (1 + stop_loss_pct), price_precision)
                    tp_price = round(current_price * (1 - (stop_loss_pct * 3)), price_precision)
            
            # Delegate to Surgical Sync
            success, sync_msg = await self.synchronize_sl_tp_safe(
                symbol, qty, sl_price, tp_price, side, min_notional, qty_precision, entry_price=current_price
            )
            
            if success:
                # Update persistent cooldown timestamp
                SLTP_LAST_UPDATE[symbol] = time.time()
                return True, (
                    f"🔄 SL/TP Updated (Surgical) for {symbol}\n"
                    f"{sync_msg}"
                )
            else:
                return False, sync_msg
            
        except Exception as e:
            return False, f"Update Error: {e}"
        finally:
            self._operation_locks.pop(symbol, None)
    
    async def cleanup_orphaned_orders(self) -> Tuple[bool, str]:
        """Cancel orders for symbols without positions."""
        if not self.client:
            return False, "No valid session."
        
        try:
            all_orders = await self.client.futures_get_open_orders()
            active_pos = await self.get_active_positions()
            active_symbols = set(p['symbol'] for p in active_pos)
            
            orphaned = set()
            for order in all_orders:
                sym = order['symbol']
                if sym not in active_symbols:
                    orphaned.add(sym)
            
            if not orphaned:
                return True, f"✅ No orphaned orders found. ({len(all_orders)} orders, {len(active_symbols)} positions)"
            
            canceled = 0
            for sym in orphaned:
                try:
                    await self.client.futures_cancel_all_open_orders(symbol=sym)
                    canceled += 1
                except Exception as e:
                    print(f"Error canceling {sym}: {e}")
            
            return True, f"🧹 Cleaned {canceled} symbols: {', '.join(orphaned)}"
            
        except Exception as e:
            return False, f"Cleanup Error: {e}"
    
    async def execute_spot_buy(self, symbol: str) -> Tuple[bool, str]:
        """Execute SPOT market buy."""
        if not self.client:
            return False, "No valid session."
        
        try:
            # Get account
            acc = await self.client.get_account()
            usdt_balance = 0.0
            for asset in acc['balances']:
                if asset['asset'] == 'USDT':
                    usdt_balance = float(asset['free'])
                    break
            
            alloc_pct = self.config.get('spot_allocation_pct', 0.20)
            buy_amount = usdt_balance * alloc_pct
            
            if buy_amount < 10:
                return False, f"❌ Insufficient USDT ({usdt_balance:.2f} * {alloc_pct*100}% = {buy_amount:.2f})"
            
            # Get price
            ticker = await self.client.get_symbol_ticker(symbol=symbol)
            price = float(ticker['price'])
            
            # Calculate quantity
            raw_qty = buy_amount / price
            info = await self.client.get_symbol_info(symbol)
            step_size = 0.001
            for f in info['filters']:
                if f['filterType'] == 'LOT_SIZE':
                    step_size = float(f['stepSize'])
                    break
            
            precision = len(str(step_size).rstrip('0').split('.')[-1])
            quantity = round(raw_qty - (raw_qty % step_size), precision)
            
            if quantity <= 0:
                return False, "Quantity too small."
            
            # Execute
            order = await self.client.order_market_buy(symbol=symbol, quantity=quantity)
            
            fill_price = float(order.get('fills', [{}])[0].get('price', price))
            return True, f"Bought {quantity} {symbol} @ {fill_price}"
            
        except Exception as e:
            return False, f"Spot Buy Error: {e}"
    
    async def get_active_positions(self) -> List[Dict]:
        """Get list of active futures positions."""
        if not self.client:
            return []
        
        try:
            positions = await self.client.futures_position_information()
            active = []
            for p in positions:
                amt = float(p['positionAmt'])
                if abs(amt) > 0.0001:  # Filter dust
                    active.append({
                        'symbol': p['symbol'],
                        'amt': amt,
                        'entry': float(p['entryPrice']),
                        'pnl': float(p.get('unrealizedProfit', 0))
                    })
            return active
        except Exception as e:
            print(f"Position fetch error: {e}")
            return []
    
    async def get_wallet_details(self) -> Dict:
        """Get wallet balances including Alpaca and Earn products."""
        if not self.client:
            return {"error": "No session"}
        
        try:
            # Futures
            futures_acc = await self.client.futures_account()
            futures_balance = float(futures_acc.get('totalWalletBalance', 0))
            futures_pnl = float(futures_acc.get('totalUnrealizedProfit', 0))
            
            # Spot
            spot_acc = await self.client.get_account()
            spot_usdt = 0.0
            for asset in spot_acc['balances']:
                if asset['asset'] == 'USDT':
                    spot_usdt = float(asset['free']) + float(asset['locked'])
                    break
            
            # Earn (Flexible Savings)
            earn_usdt = 0.0
            try:
                # Fetch Simple Earn Flexible positions
                earn_data = await self.client.get_simple_earn_flexible_position()
                if earn_data and 'rows' in earn_data:
                    for row in earn_data['rows']:
                        if row.get('asset') == 'USDT':
                            earn_usdt += float(row.get('totalAmount', 0))
            except Exception as e:
                print(f"⚠️ Earn fetch warning: {e}")
            
            # Alpaca Equity
            alpaca_equity = 0.0
            if self.alpaca_client:
                try:
                    loop = asyncio.get_event_loop()
                    acct = await loop.run_in_executor(None, self.alpaca_client.get_account)
                    alpaca_equity = float(acct.equity) if acct else 0.0
                except Exception as e:
                    print(f"⚠️ Alpaca equity warning: {e}")
            
            total = spot_usdt + futures_balance + earn_usdt + alpaca_equity
            
            return {
                "spot_usdt": spot_usdt,
                "earn_usdt": earn_usdt,
                "futures_balance": futures_balance,
                "futures_pnl": futures_pnl,
                "alpaca_equity": alpaca_equity,
                "total": total
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    async def _execute_alpaca_order(self, symbol: str, side: str, atr: Optional[float] = None) -> Tuple[bool, str]:
        """Execute order via Alpaca (runs sync code in executor)."""
        if not self.alpaca_client:
            return False, "⚠️ Alpaca Client not initialized."
        
        # Run sync Alpaca code in thread pool
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, 
            self._alpaca_order_sync, 
            symbol, side, atr
        )
    
    def _alpaca_order_sync(self, symbol: str, side: str, atr: Optional[float]) -> Tuple[bool, str]:
        """Sync Alpaca order execution (called via run_in_executor)."""
        try:
            import yfinance as yf
            
            # Check existing position
            try:
                pos = self.alpaca_client.get_open_position(symbol)
                if pos:
                    return False, f"⚠️ Position already open for {symbol}."
            except:
                pass
            
            # Get account
            acct = self.alpaca_client.get_account()
            equity = float(acct.equity)
            
            # Get price
            ticker = yf.Ticker(symbol)
            try:
                current_price = ticker.fast_info['last_price']
            except:
                hist = ticker.history(period="1d")
                if not hist.empty:
                    current_price = hist['Close'].iloc[-1]
                else:
                    return False, f"❌ Failed to fetch price for {symbol}"
            
            if not current_price:
                return False, "❌ Price is zero/null."
            
            # Calculate SL/TP
            if atr and atr > 0:
                mult = self.config.get('atr_multiplier', 2.0)
                sl_dist = mult * atr
                if side == 'LONG':
                    sl_price = current_price - sl_dist
                    tp_price = current_price + (1.5 * sl_dist)
                else:
                    sl_price = current_price + sl_dist
                    tp_price = current_price - (1.5 * sl_dist)
            else:
                sl_pct = 0.02
                if side == 'LONG':
                    sl_price = current_price * (1 - sl_pct)
                    tp_price = current_price * (1 + (sl_pct * 3))
                else:
                    sl_price = current_price * (1 + sl_pct)
                    tp_price = current_price * (1 - (sl_pct * 3))
            
            # Size calculation
            dist_to_stop = abs(current_price - sl_price) or 0.01
            risk_amt = equity * 0.02
            qty = risk_amt / dist_to_stop
            
            max_alloc = equity * 0.20
            if (qty * current_price) > max_alloc:
                qty = max_alloc / current_price
            
            qty = round(qty, 2)
            if side == 'SHORT':
                qty = int(qty)
            
            if qty < 0.01:
                return False, f"Quantity too small ({qty})."
            
            # Submit order
            side_enum = OrderSide.BUY if side == 'LONG' else OrderSide.SELL
            
            req = MarketOrderRequest(
                symbol=symbol,
                qty=qty,
                side=side_enum,
                time_in_force=TimeInForce.DAY,
                take_profit=TakeProfitRequest(limit_price=round(tp_price, 2)),
                stop_loss=StopLossRequest(stop_price=round(sl_price, 2))
            )
            
            res = self.alpaca_client.submit_order(req)
            
            status_str = str(res.status).replace('OrderStatus.', '').replace('_', ' ').title()
            
            return True, (
                f"✅ Alpaca {side} {symbol}\n"
                f"Qty: {qty}\n"
                f"SL: {sl_price:.2f}\n"
                f"TP: {tp_price:.2f}\n"
                f"Status: {status_str}"
            )
            
        except Exception as e:
            return False, f"Alpaca Error: {e}"

    # --- RESTORED METHODS FROM SYNC ---
    
    def get_trade_preview(self, symbol: str, side: str, current_price: float, atr: Optional[float] = None) -> Tuple[float, float]:
        """
        Calculates TP and SL prices without executing the trade.
        Returns: (sl_price, tp_price)
        """
        try:
            price_precision = 2
            if current_price < 1.0: price_precision = 4
            if current_price < 0.01: price_precision = 6
            
            if atr and atr > 0:
                mult = self.config.get('atr_multiplier', 2.0)
                sl_dist = mult * atr
                
                if side == 'LONG':
                    sl_price = round(current_price - sl_dist, price_precision)
                    tp_price = round(current_price + (1.5 * sl_dist), price_precision)
                else:
                    sl_price = round(current_price + sl_dist, price_precision)
                    tp_price = round(current_price - (1.5 * sl_dist), price_precision)
            else:
                sl_pct = self.config.get('stop_loss_pct', 0.02)
                tp_pct = sl_pct * 1.5
                
                if side == 'LONG':
                    sl_price = round(current_price * (1 - sl_pct), price_precision)
                    tp_price = round(current_price * (1 + tp_pct), price_precision)
                else:
                    sl_price = round(current_price * (1 + sl_pct), price_precision)
                    tp_price = round(current_price * (1 - tp_pct), price_precision)
            
            return sl_price, tp_price
        except Exception as e:
            print(f"Preview Error: {e}")
            return 0.0, 0.0

    async def execute_flip_position(self, symbol: str, new_side: str, atr: Optional[float] = None) -> Tuple[bool, str]:
        """
        FLIP LOGIC:
        1. Cancel Open Orders.
        2. Close Current Position.
        3. Wait 3s for stability.
        4. Verify position is closed
        5. Open New Position (Reverse).
        """
        if not self.client:
            return False, "No valid session."
        
        # 1. Close Current
        success_close, msg_close = await self.execute_close_position(symbol)
        
        if not success_close and "No open position" not in msg_close:
            return False, f"Flip Aborted: Failed to close ({msg_close})"
        
        # 2. Safety Wait (Binance sequencing - tripled for stability)
        await asyncio.sleep(3.0)
        
        # 3. Verify position is actually closed before opening new
        try:
            positions = await self.client.futures_position_information(symbol=symbol)
            for pos in positions:
                if float(pos.get('positionAmt', 0)) != 0:
                    return False, f"Flip Aborted: Position still open ({pos.get('positionAmt')} contracts)"
        except Exception as e:
            print(f"⚠️ Warning: Could not verify position closure: {e}")
        
        # 4. Open New
        if new_side == 'LONG':
            return await self.execute_long_position(symbol, atr)
        elif new_side == 'SHORT':
            return await self.execute_short_position(symbol, atr)
        else:
            return False, f"Invalid Side: {new_side}"

    def reset_circuit_breaker(self) -> None:
        """
        Resets the circuit breaker logic by updating the 'ignore_until' timestamp.
        Any losses recorded before this timestamp will not count towards the streak.
        """
        self.cb_ignore_until = int(time.time() * 1000)
        print(f"✅ [Chat {self.chat_id}] Circuit Breaker Reset. Ignoring history before {self.cb_ignore_until}")

    async def check_circuit_breaker(self) -> Tuple[bool, str]:
        """
        Circuit Breaker / Safety Switch
        If detects 5 consecutive losses (Realized PnL < 0) in PILOT mode,
        automatically downgrades to COPILOT to stop the bleeding.
        Returns: (Triggered: bool, Message: str)
        """
        if self.mode != 'PILOT':
            return False, ""
        
        if not self.client:
            return False, ""
        
        try:
            # Fetch last 20 Income entries (REALIZED_PNL only)
            income = await self.client.futures_income_history(incomeType='REALIZED_PNL', limit=20)
            
            # Sort descending by time (Newest first)
            income.sort(key=lambda x: x['time'], reverse=True)
            
            consecutive_losses = 0
            for trade in income:
                pnl = float(trade['income'])
                if pnl < 0:
                    # CHECK: Ignore if before reset time
                    if trade['time'] < self.cb_ignore_until:
                        break
                    consecutive_losses += 1
                else:
                    break
            
            # Threshold Check
            if consecutive_losses >= 5:
                old_mode = self.mode
                self.set_mode('COPILOT')
                
                msg = (
                    f"⚠️ **CIRCUIT BREAKER ACTIVADO** ⚠️\n"
                    f"Se han detectado {consecutive_losses} pérdidas consecutivas en modo PILOT.\n"
                    f"🛡️ El sistema ha cambiado automáticamente a **COPILOT** para proteger tu capital.\n"
                    f"Revisa el mercado manualmente antes de reactivar."
                )
                return True, msg
        
        except Exception as e:
            print(f"Error checking circuit breaker: {e}")
        
        return False, ""

    async def get_pnl_history(self, days: int = 1) -> Tuple[float, List[Dict]]:
        """Fetches Realized PnL from Binance for the last N days"""
        if not self.client:
            return 0.0, []
        
        try:
            start_time = int((time.time() - (days * 86400)) * 1000)
            
            # Fetch Realized PnL
            income = await self.client.futures_income_history(
                incomeType='REALIZED_PNL',
                startTime=start_time,
                limit=100
            )
            # Fetch Commission (to subtract for Net PnL)
            commission = await self.client.futures_income_history(
                incomeType='COMMISSION',
                startTime=start_time,
                limit=100
            )
            
            total_pnl = 0.0
            details = []
            
            for item in income:
                amt = float(item['income'])
                total_pnl += amt
                details.append({'symbol': item['symbol'], 'amount': amt, 'time': item['time'], 'type': 'PNL'})
            
            for item in commission:
                amt = float(item['income'])
                total_pnl += amt  # Commission is negative
            
            return total_pnl, details
        
        except Exception as e:
            print(f"Error fetching PnL: {e}")
            return 0.0, []

    def _log_trade(self, symbol: str, entry: float, qty: float, sl: float, tp: float, side: str = 'LONG') -> None:
        """Logs trade to local JSON file for history"""
        try:
            log_file = 'data/trades.json'
            entry_data = {
                "timestamp": time.time(),
                "date": time.strftime('%Y-%m-%d %H:%M:%S'),
                "chat_id": self.chat_id,
                "symbol": symbol,
                "side": side,
                "entry_price": entry,
                "quantity": qty,
                "sl": sl,
                "tp": tp
            }
            
            data = []
            if os.path.exists(log_file):
                with open(log_file, 'r') as f:
                    try:
                        data = json.load(f)
                    except:
                        pass
            
            data.append(entry_data)
            
            with open(log_file, 'w') as f:
                json.dump(data, f, indent=4)
        
        except Exception as e:
            print(f"⚠️ Failed to log trade: {e}")


class AsyncSessionManager:
    """
    Manages multiple AsyncTradingSessions.
    Provides persistence and lookup by chat_id.
    """
    
    def __init__(self, data_file: str = 'data/sessions.json'):
        self.data_file = data_file
        self.sessions: Dict[str, AsyncTradingSession] = {}
        self._lock = asyncio.Lock()
    
    async def load_sessions(self):
        """Load sessions from PostgreSQL (with JSON fallback)."""
        async with self._lock:
            # Try PostgreSQL first
            try:
                from utils.db import load_all_sessions
                db_sessions = load_all_sessions()
                
                if db_sessions is not None:
                    for chat_id, info in db_sessions.items():
                        # SANITIZE: Check authorization
                        from utils.db import get_user_role
                        allowed, role = get_user_role(str(chat_id))
                        
                        config = info.get('config', {})
                        
                        # FORCE DEFAULTS if unauthorized (Fixes persistent old config issue)
                        api_key = info.get('api_key', '')
                        api_secret = info.get('api_secret', '')
                        
                        if not allowed:
                            print(f"🔒 Locking down Unauthorized session: {chat_id}")
                            config.update({
                                "mode": "WATCHER",
                                "strategies": {},
                                "groups": {},
                                "sentiment_filter": False,
                                "personality": "STANDARD_ES"
                            })
                            # Force Clear Keys
                            api_key = ""
                            api_secret = ""
                        
                        session = AsyncTradingSession(
                            chat_id=chat_id,
                            api_key=api_key,
                            api_secret=api_secret,
                            config=config
                        )
                        await session.initialize()
                        self.sessions[chat_id] = session
                    
                    print(f"🐘 Loaded {len(self.sessions)} sessions from PostgreSQL")
                    await self._ensure_admin_session()
                    return
            except Exception as e:
                print(f"⚠️ PostgreSQL load failed, using JSON fallback: {e}")
            
            # Fallback to JSON
            if not os.path.exists(self.data_file):
                await self._ensure_admin_session()
                return
            
            try:
                with open(self.data_file, 'r') as f:
                    data = json.load(f)
                
                for chat_id, info in data.items():
                    # SANITIZE: Check authorization
                    from utils.db import get_user_role
                    allowed, role = get_user_role(str(chat_id))
                    
                    config = info.get('config', {})
                    
                    if not allowed:
                        print(f"🔒 Locking down Unauthorized session (JSON): {chat_id}")
                        config.update({
                            "mode": "WATCHER",
                            "strategies": {},
                            "groups": {},
                            "sentiment_filter": False,
                            "personality": "STANDARD_ES"
                        })
                        # Force Clear Keys in Info dict (for init below)
                        info['api_key'] = ""
                        info['api_secret'] = ""

                    session = AsyncTradingSession(
                        chat_id=chat_id,
                        api_key=info.get('api_key', ''),
                        api_secret=info.get('api_secret', ''),
                        config=config
                    )
                    await session.initialize()
                    self.sessions[chat_id] = session
                
                print(f"📁 Loaded {len(self.sessions)} sessions from {self.data_file}")
                
            except Exception as e:
                print(f"❌ Session Load Error: {e}")
        
        await self._ensure_admin_session()
    
    async def _ensure_admin_session(self):
        """Create or update admin sessions from env vars (supports comma-separated IDs)."""
        # Sanitize inputs
        raw_admin_ids = os.getenv('TELEGRAM_ADMIN_ID', '').strip().strip("'\"")
        api_key = os.getenv('BINANCE_API_KEY', '').strip().strip("'\"")
        api_secret = os.getenv('BINANCE_SECRET', '').strip().strip("'\"")
        
        if not raw_admin_ids or not api_key or not api_secret:
            return

        # Split multiple IDs (e.g. "123,456,789")
        admin_ids = [aid.strip() for aid in raw_admin_ids.split(',') if aid.strip()]

        for admin_id in admin_ids:
            # Case 1: Session does not exist -> Create it
            if admin_id not in self.sessions:
                session = AsyncTradingSession(admin_id, api_key, api_secret)
                await session.initialize()
                self.sessions[admin_id] = session
                print(f"🔑 Admin session created for {admin_id} (Env Vars)")
            
            # Case 2: Session exists but Keys mismatch -> Update it
            else:
                session = self.sessions[admin_id]
                if session.api_key != api_key or session.api_secret != api_secret:
                    session.api_key = api_key
                    session.api_secret = api_secret
                    # Re-init client with new keys
                    await session.initialize()
                    print(f"🔄 Admin session updated for {admin_id} from Env Vars")
    
    async def save_sessions(self):
        """Persist sessions to PostgreSQL and JSON (redundancy)."""
        async with self._lock:
            data = {}
            for chat_id, session in self.sessions.items():
                data[chat_id] = {
                    'api_key': session.api_key,
                    'api_secret': session.api_secret,
                    'config': session.config
                }
            
            # 1. Save to PostgreSQL
            try:
                from utils.db import save_all_sessions
                if save_all_sessions(data):
                    print(f"🐘 Saved {len(data)} sessions to PostgreSQL")
            except Exception as e:
                print(f"⚠️ PostgreSQL save failed: {e}")
            
            # 2. Save to JSON (backup)
            os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
            with open(self.data_file, 'w') as f:
                json.dump(data, f, indent=2)
    
    def get_session(self, chat_id: str) -> Optional[AsyncTradingSession]:
        """Get session by chat_id."""
        return self.sessions.get(chat_id)
    
    async def create_or_update_session(
        self, chat_id: str, api_key: str, api_secret: str
    ) -> AsyncTradingSession:
        """Create or update a session."""
        
        existing = self.sessions.get(chat_id)
        config = existing.config if existing else None
        
        session = AsyncTradingSession(chat_id, api_key, api_secret, config)
        await session.initialize()
        
        self.sessions[chat_id] = session
        await self.save_sessions()
        
        return session
    
    async def delete_session(self, chat_id: str) -> bool:
        """Delete a session."""
        if chat_id in self.sessions:
            session = self.sessions.pop(chat_id)
            await session.close()
            await self.save_sessions()
            return True
        return False
    
    def get_all_sessions(self) -> List[AsyncTradingSession]:
        """Get all active sessions."""
        return list(self.sessions.values())
    
    async def close_all(self):
        """Cleanup all sessions."""
        for session in self.sessions.values():
            await session.close()
        self.sessions.clear()
