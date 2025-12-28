"""
NEXUS TRADING BOT - Async Trading Manager
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
from servos.ai_analyst import QuantumAnalyst

# Shield 2.0
from nexus_system.shield.correlation import CorrelationManager

# Bybit Adapter
from nexus_system.uplink.adapters.bybit_adapter import BybitAdapter

import pandas as pd

# Alpaca (still sync, but wrapped)
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest, TakeProfitRequest, StopLossRequest
from alpaca.trading.enums import OrderSide, TimeInForce


class AsyncTradingSession:
    """
    Async Trading Session using python-binance AsyncClient.
    Designed for native async/await operations in aiogram.
    """
    
    def __init__(self, chat_id: str, api_key: str, api_secret: str, config: Optional[Dict] = None, manager=None):
        self.chat_id = chat_id
        self.api_key = api_key
        self.api_secret = api_secret
        self.client: Optional[AsyncClient] = None
        self.alpaca_client: Optional[TradingClient] = None
        self.bybit_client: Optional[BybitAdapter] = None
        self.manager = manager
        
        from system_directive import DEFAULT_SESSION_CONFIG
        
        # Initialize with centralized defaults
        self.config = dict(DEFAULT_SESSION_CONFIG)
        
        if config:
            self.config.update(config)
        
        self.mode = self.config.get('mode', 'WATCHER')
        
        # Circuit Breaker State (Can be disabled via config)
        self.cb_ignore_until = 0  
        
        # AI Analyst
        self.ai_analyst = QuantumAnalyst()

        # Shield 2.0: Portfolio Correlation Guard
        self.correlation_manager = CorrelationManager()
        
        # Operation Lock: Prevent concurrent/spam operations per symbol
        self._operation_locks = {}  # {symbol: timestamp}
        self._lock_duration = 30  # seconds
        
        # Algo Order Tracking: Track algoIds for selective cancellation
        self.active_algo_orders = {}  # {symbol: {'sl_id': str, 'tp_id': str}}
        
        # Proxy Setup
        self._proxy = os.getenv('PROXY_URL') or os.getenv('HTTPS_PROXY') or os.getenv('HTTP_PROXY')
    


    async def initialize(self, verbose: bool = True) -> bool:
        """Async initialization of exchange clients."""
        if verbose:
            print("🧠 Nexus Analyst: CONNECTED.")
        success = True
        
        # 1. Initialize Binance Async Client
        if self.api_key and self.api_secret:
            try:
                # Set environment variables BEFORE creating client
                # This ensures aiohttp session picks them up with trust_env=True
                if self._proxy:
                    os.environ['HTTPS_PROXY'] = self._proxy
                    os.environ['HTTP_PROXY'] = self._proxy
                    if verbose:
                        print(f"🔄 [Chat {self.chat_id}] Proxy configured: {self._proxy[:30]}...")

                
                # Create client - use https_proxy parameter if available
                if self._proxy:
                    self.client = await AsyncClient.create(
                        self.api_key, 
                        self.api_secret,
                        https_proxy=self._proxy
                    )
                else:
                    self.client = await AsyncClient.create(
                        self.api_key, 
                        self.api_secret
                    )
                
                if verbose:
                    proxy_status = "✅ Proxy" if self._proxy else "⚠️ Direct"
                    print(f"✅ [Chat {self.chat_id}] Binance Client Init ({proxy_status}, Key: ...{self.api_key[-4:]})")
            except Exception as e:
                self._init_error = str(e)
                if verbose:
                    print(f"❌ [Chat {self.chat_id}] Binance Init Error: {e}")
                self.client = None
                success = False
        
        # 2. Initialize Alpaca (still sync but wrapped)
        await self.initialize_alpaca(verbose=verbose)

        # 3. Initialize Bybit
        bybit_key = self.config.get('bybit_api_key') or os.getenv('BYBIT_API_KEY')
        bybit_secret = self.config.get('bybit_api_secret') or os.getenv('BYBIT_API_SECRET')
        
        if bybit_key and bybit_secret:
             self.bybit_client = BybitAdapter(bybit_key, bybit_secret)
             if await self.bybit_client.initialize():
                 if verbose: print(f"✅ [Chat {self.chat_id}] Bybit Client Initialized")
             else:
                 self.bybit_client = None
                 if verbose: print(f"❌ [Chat {self.chat_id}] Bybit Client Init Failed")
        
        return success
    
    # --- RISK HELPER ---
    def calculate_dynamic_size(self, equity: float, price: float, sl_price: float, leverage: int, min_notional: float) -> float:
        """
        Calculates position size based on Risk Per Trade (e.g. 1% of Equity).
        Formula: Risk Amount / Distance to SL
        """
        from system_directive import RISK_PER_TRADE_PCT
        
        # 1. Determine Risk Percentage
        risk_pct = RISK_PER_TRADE_PCT
        
        # --- KELLY CRITERION LOGIC ---
        if self.config.get('use_kelly_criterion', False):
            try:
                p = self.config.get('win_rate_est', 0.55)
                b = self.config.get('risk_reward_est', 1.5)
                fraction = self.config.get('kelly_fraction', 0.5)
                
                # Kelly Formula: f = p - (q / b)
                q = 1 - p
                kelly_optimal = p - (q / b)
                
                # Apply Fraction (Safety)
                kelly_risk = kelly_optimal * fraction
                
                if kelly_risk > 0:
                    # Log the difference if significant
                    if abs(kelly_risk - risk_pct) > 0.01:
                         print(f"🧠 Kelly Sizing: {kelly_risk:.2%} risk (vs Base {risk_pct:.2%})")
                    risk_pct = kelly_risk
                else:
                    print("⚠️ Kelly suggests 0% or negative allocation. Reverting to base risk.")
            except Exception as e:
                print(f"⚠️ Kelly Calculation Error: {e}")
                
        # 2. Calculate Risk Amount ($)
        risk_amount = equity * risk_pct
        
        # 3. Calculate Distance to SL
        dist_to_sl = abs(price - sl_price)
        if dist_to_sl <= 0: return 0.0
        
        # 4. Raw Quantity (Units)
        raw_qty = risk_amount / dist_to_sl
        
        # 4. Cap at Max Capital Allocation (Safety Net)
        max_cap_val = equity * self.config.get('max_capital_pct', 0.10) * leverage
        max_qty = max_cap_val / price
        
        final_qty = min(raw_qty, max_qty)
        
        # 5. Min Notional Check
        if (final_qty * price) < min_notional:
             # If risk-based size is too small, check if we can bump to min_notional 
             # without exceeding 2x risk. If so, allowed. Else, skip.
             min_qty = (min_notional * 1.05) / price
             implied_risk = min_qty * dist_to_sl
             if implied_risk <= (risk_amount * 2): # Allow slight risk stretch for small accounts
                 return min_qty
             else:
                 return 0.0 # Too risky for this account size
                 
        return final_qty
    

    async def initialize_alpaca(self, verbose: bool = True):
        """Initialize Alpaca client from per-user config, with ENV fallback for admins only."""
        # Check if this user is an admin (allow ENV fallback for owners)
        admin_ids = os.getenv('TELEGRAM_ADMIN_ID', '').replace(' ', '').split(',')
        is_admin = str(self.chat_id) in admin_ids
        
        # Get credentials: per-user config first, ENV fallback only for admins
        ak = self.config.get('alpaca_key', '').strip() if self.config.get('alpaca_key') else ''
        ask = self.config.get('alpaca_secret', '').strip() if self.config.get('alpaca_secret') else ''
        
        # ENV fallback ONLY for admins
        if not ak and is_admin:
            ak = os.getenv('APCA_API_KEY_ID', '').strip().strip("'\"")
        if not ask and is_admin:
            ask = os.getenv('APCA_API_SECRET_KEY', '').strip().strip("'\"")
        
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
                
                if verbose:
                    print(f"✅ [Chat {self.chat_id}] Alpaca Client Initialized (Paper: {paper})")
            except Exception as e:
                if verbose:
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
        """Check if strategy is enabled. Default TRUE for most strategies."""
        # Default to True for most strategies (except SHARK which is aggressive)
        default = False if strategy == 'SHARK' else True
        return self.config.get('strategies', {}).get(strategy, default)

    def toggle_group(self, group: str) -> bool:
        """Toggle a specific asset group on/off."""
        groups = self.config.get('groups', {})
        current = groups.get(group, False)
        groups[group] = not current
        self.config['groups'] = groups
        return groups[group]

    def is_group_enabled(self, group: str) -> bool:
        """
        Check if group is enabled FOR THIS USER.
        Fetches from DB (per-user preferences) first, falls back to session config.
        """
        # Try DB first (per-user preferences)
        from servos.db import get_user_enabled_groups
        user_groups = get_user_enabled_groups(self.chat_id)
        if user_groups:
            return user_groups.get(group, True)
        # Fallback to session config (legacy)
        return self.config.get('groups', {}).get(group, True)

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
    
    async def _fetch_ohlcv_for_chart(self, symbol: str, limit: int = 100) -> Optional[pd.DataFrame]:
        """Fetch historical klines for chart generation."""
        try:
            klines = await self.client.futures_klines(symbol=symbol, interval='15m', limit=limit)
            data = []
            for k in klines:
                data.append({
                    'timestamp': int(k[0]),
                    'open': float(k[1]),
                    'high': float(k[2]),
                    'low': float(k[3]),
                    'close': float(k[4]),
                    'volume': float(k[5])
                })
            return pd.DataFrame(data)
        except Exception as e:
            print(f"⚠️ Chart Data Fetch Error: {e}")
            return None

    # --- RISK HELPER: CORRELATION GUARD (Shield 2.0) ---
    async def _check_correlation_safeguard(self, candidate_symbol: str) -> Tuple[bool, str]:
        """
        Checks if adding candidate_symbol violates portfolio correlation limits.
        Uses cached market data from NexusCore engine via SessionManager.
        """
        if not self.manager or not self.manager.engine:
            # Fallback: If no engine (standalone mode), skip check or be strict?
            # Defaulting to Safe to not block trading if engine is offline, but logging warning.
            return True, ""
            
        try:
            # 1. Get Active Positions
            active_pos = await self.get_active_positions()
            active_symbols = [p['symbol'] for p in active_pos if 'USDT' in p['symbol']] # Crypto only
            
            # Filter out self (if re-entering/adding to same pos)
            active_symbols = [s for s in active_symbols if s != candidate_symbol]
            
            if not active_symbols:
                return True, ""
            
            # 2. Update History for Active Positions
            # Fetch from Engine's MarketStream (Memory Cache)
            stream = self.manager.engine.market_stream
            
            # Prepare Candidate Data first
            cand_data = await stream.get_candles(candidate_symbol, limit=60)
            if cand_data['dataframe'].empty:
                return True, "" # Not enough data to correlation check
                
            cand_prices = cand_data['dataframe']['close']
            
            # Check against each active position
            # We pass the active_symbols list to manager, but manager needs their history updated first
            for pos_sym in active_symbols:
                pos_data = await stream.get_candles(pos_sym, limit=60)
                if not pos_data['dataframe'].empty:
                    self.correlation_manager.update_price_history(pos_sym, pos_data['dataframe']['close'])
            
            # 3. Perform Check
            is_safe = self.correlation_manager.check_correlation(
                candidate_symbol, 
                cand_prices, 
                active_symbols
            )
            
            if not is_safe:
                return False, f"🚫 **Shield Protocol**: Alta correlación detectada."
                
            return True, ""
            
        except Exception as e:
            print(f"⚠️ Correlation Check Error: {e}")
            return True, "" # Fail Safe (Allow trade)

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

    async def get_open_algo_orders(self, symbol: str) -> list:
        """
        Fetch open algo orders (conditional orders like SL/TP/Trailing).
        Binance uses futures_get_open_orders for both standard and algo orders.
        """
        try:
            if not self.client:
                return []
            
            # Binance Futures API returns all open orders including conditional ones
            orders = await self.client.futures_get_open_orders(symbol=symbol)
            
            # Filter for algo-type orders (conditional orders)
            algo_types = ['STOP_MARKET', 'TAKE_PROFIT_MARKET', 'TRAILING_STOP_MARKET', 
                         'STOP', 'TAKE_PROFIT', 'TRAILING_STOP']
            algo_orders = [o for o in orders if o.get('type') in algo_types]
            
            return algo_orders
        except Exception as e:
            print(f"⚠️ Error fetching algo orders for {symbol}: {e}")
            return []

    async def _cancel_all_robust(self, symbol: str, verify: bool = True) -> bool:
        """
        Robustly cancel all open orders for a symbol (standard + algo).
        
        Anti-Accumulation Logic:
        1. Fetch all open orders
        2. Cancel each order individually
        3. Verify no orders remain (optional)
        4. Clear tracked algo orders
        
        Returns: True if all orders cleared, False if some remain
        """
        if not self.client:
            return True  # No client means no orders
            
        try:
            # 1. Get all open orders
            all_orders = await self.client.futures_get_open_orders(symbol=symbol)
            
            if not all_orders:
                # Clear tracking dict
                if symbol in self.active_algo_orders:
                    del self.active_algo_orders[symbol]
                return True
                
            print(f"🧹 {symbol}: Cancelling {len(all_orders)} existing orders...")
            
            # 2. Cancel each order
            cancelled_count = 0
            for order in all_orders:
                try:
                    order_id = order.get('orderId')
                    if order_id:
                        await self.client.futures_cancel_order(
                            symbol=symbol, 
                            orderId=order_id
                        )
                        cancelled_count += 1
                except Exception as e:
                    # Order might already be filled/cancelled
                    if '-2011' not in str(e):  # Unknown order
                        print(f"⚠️ Cancel failed for order {order_id}: {e}")
                        
            print(f"✅ {symbol}: Cancelled {cancelled_count}/{len(all_orders)} orders")
            
            # 3. Clear tracked algo orders
            if symbol in self.active_algo_orders:
                del self.active_algo_orders[symbol]
            
            # 4. Verify (optional, adds latency)
            if verify:
                await asyncio.sleep(0.3)  # Small delay for order state to propagate
                remaining = await self.client.futures_get_open_orders(symbol=symbol)
                if remaining:
                    print(f"⚠️ {symbol}: {len(remaining)} orders still remain after cancel")
                    return False
                    
            return True
            
        except Exception as e:
            print(f"❌ _cancel_all_robust error for {symbol}: {e}")
            return False


    async def _place_conditional_with_tracking(
        self, symbol: str, order_type: str, side: str, 
        quantity: float, stop_price: float, **kwargs
    ) -> Tuple[bool, str, Optional[str]]:
        """
        Place conditional order and track algoId for later cancellation.
        
        Args:
            symbol: Trading pair
            order_type: STOP_MARKET, TAKE_PROFIT_MARKET, TRAILING_STOP_MARKET
            side: BUY or SELL
            quantity: Order quantity
            stop_price: Trigger price (or activation for trailing)
            **kwargs: Additional params (callbackRate for trailing, etc)
            
        Returns: (success, message, algoId)
        """
        try:
            result = await self._place_order_with_retry(
                self.client.futures_create_order,
                symbol=symbol, side=side, type=order_type,
                stopPrice=stop_price, quantity=quantity,
                reduceOnly=True, **kwargs
            )
            
            # Extract algoId (or orderId for standard)
            algo_id = str(result.get('algoId') or result.get('orderId', ''))
            
            # Store in tracking dict
            if symbol not in self.active_algo_orders:
                self.active_algo_orders[symbol] = {}
            
            # Determine key based on order type
            if 'STOP' in order_type and 'TRAILING' not in order_type and 'TAKE_PROFIT' not in order_type:
                type_key = 'sl_id'
            elif 'TAKE_PROFIT' in order_type:
                type_key = 'tp_id'
            else:
                type_key = 'trail_id'
                
            self.active_algo_orders[symbol][type_key] = algo_id
            print(f"✅ {symbol}: Placed {order_type} @ {stop_price} (ID: {algo_id})")
            
            return True, f"{order_type} @ {stop_price}", algo_id
            
        except Exception as e:
            print(f"⚠️ {symbol}: Failed to place {order_type}: {e}")
            return False, str(e), None

    async def synchronize_sl_tp_safe(self, symbol: str, quantity: float, sl_price: float, tp_price: float, side: str, min_notional: float, qty_precision: int, entry_price: float = 0.0, current_price: float = 0.0) -> Tuple[bool, str]:
        """
        Surgical SL/TP Synchronization (V2 - Anti-Spam):
        1. Check if valid SL/TP already exists (skip if within 1% tolerance).
        2. Cancel existing STOP_MARKET / TAKE_PROFIT_MARKET / TRAILING_STOP_MARKET.
        3. Verify cancellation succeeded before proceeding.
        4. Place new SL/TP with reduceOnly=True.
        5. V3: Validate triggers against current price to avoid -2021.
        """
        try:
            # 1. Fetch existing orders (BOTH standard AND algo)
            standard_orders = await self.client.futures_get_open_orders(symbol=symbol)
            algo_orders = await self.get_open_algo_orders(symbol)
            orders = standard_orders + algo_orders
            
            existing_sl = None
            existing_tp_count = 0
            
            for o in orders:
                # Handle both standard and algo order formats
                order_type = o.get('type', '') or o.get('algoType', '')
                if order_type in ['STOP_MARKET', 'STOP']:
                    existing_sl = float(o.get('stopPrice', 0) or o.get('triggerPrice', 0))
                elif order_type in ['TAKE_PROFIT_MARKET', 'TAKE_PROFIT', 'TRAILING_STOP_MARKET', 'TRAILING_STOP']:
                    existing_tp_count += 1
            
            # 2. Check if existing SL is within 1% tolerance - SKIP UPDATE
            if existing_sl and sl_price > 0:
                tolerance = abs(existing_sl - sl_price) / sl_price
                if tolerance < 0.01 and existing_tp_count >= 1:
                    return True, f"✅ SL/TP ya configurados (SL: {existing_sl:.2f}, TP count: {existing_tp_count}). Sin cambios."
            
            # 3. Cancel existing SL/TP orders - FORCE CLEANUP (Standard + Algo)
            # Uses _cancel_all_robust which now includes verification
            # 3. Cancel existing SL/TP orders - FORCE CLEANUP (Standard + Algo)
            # Uses _cancel_all_robust which now includes verification
            try:
                # Retry loop for cancellation
                cleared = False
                for _ in range(2):
                    cleared = await self._cancel_all_robust(symbol, verify=True)
                    if cleared:
                        break
                    await asyncio.sleep(0.5)
                
                if not cleared:
                    print(f"⚠️ {symbol}: Cancellation failed (orders remain). Aborting Sync to avoid duplicates.")
                    return False, "⚠️ Sync Aborted: Could not clear existing orders."
                    
            except Exception as e:
                print(f"⚠️ Error cancelling orders for {symbol}: {e}")
                return False, f"Sync Error (Cancel): {e}"
            
            # 5. Place new SL (reduceOnly) with -2021 check
            sl_msg = ""
            abs_qty = abs(quantity)
            sl_side = 'SELL' if side == 'LONG' else 'BUY'
            
            # Validation SL
            valid_sl = True
            if current_price > 0:
                if side == 'LONG' and sl_price >= current_price:
                    sl_msg = f"⚠️ SL Skipped: Price ({current_price}) < Stop ({sl_price})"
                    valid_sl = False
                elif side == 'SHORT' and sl_price <= current_price:
                    sl_msg = f"⚠️ SL Skipped: Price ({current_price}) > Stop ({sl_price})"
                    valid_sl = False
            
            if sl_price > 0 and valid_sl:
                await self._place_order_with_retry(
                    self.client.futures_create_order,
                    symbol=symbol, side=sl_side, type='STOP_MARKET',
                    stopPrice=sl_price, quantity=abs_qty, reduceOnly=True
                )
                sl_msg = f"SL: {sl_price}"
                
            # 6. Place TP (split or single trailing) with -2021 check
            tp_msg = ""
            
            qty_tp1 = float(round(abs_qty / 2, qty_precision))
            qty_trail = float(round(abs_qty - qty_tp1, qty_precision))
            
            # Check split feasibility
            ref_price = current_price if current_price > 0 else (sl_price if sl_price > 0 else tp_price)
            is_split = ref_price > 0 and (qty_tp1 * ref_price) > min_notional and (qty_trail * ref_price) > min_notional
            
            if not is_split:
                print(f"ℹ️ {symbol}: Skipping TP1 split (Position value < 2x MinNotional). Using Full Trailing.")
            
            if is_split:
                # Validation TP1
                valid_tp = True
                if current_price > 0:
                    if side == 'LONG' and tp_price <= current_price:
                        tp_msg = f"⚠️ TP1 Skipped: Price ({current_price}) > TP ({tp_price})"
                        valid_tp = False
                    elif side == 'SHORT' and tp_price >= current_price:
                        tp_msg = f"⚠️ TP1 Skipped: Price ({current_price}) < TP ({tp_price})"
                        valid_tp = False

                # TP1 (fixed)
                if valid_tp:
                    await self._place_order_with_retry(
                        self.client.futures_create_order,
                        symbol=symbol, side=sl_side, type='TAKE_PROFIT_MARKET',
                        stopPrice=tp_price, quantity=qty_tp1, reduceOnly=True
                    )
                # Trailing for rest
                activation = tp_price  # Activate at TP1
                await self._place_order_with_retry(
                    self.client.futures_create_order,
                    symbol=symbol, side=sl_side, type='TRAILING_STOP_MARKET',
                    quantity=qty_trail, callbackRate=1.0, activationPrice=activation, reduceOnly=True
                )
                tp_msg = f"TP1: {tp_price} | Trail: 1.0% (Act: {activation})"
            else:
                # Full trailing
                # Fix: Use tp_price as activation. entry_price can be invalid if currently in profit
                # (e.g. SHORT Entry 100, Current 90. Activation cannot be 100 for BUY Trailing)
                activation = tp_price 
                await self._place_order_with_retry(
                    self.client.futures_create_order,
                    symbol=symbol, side=sl_side, type='TRAILING_STOP_MARKET',
                    quantity=abs_qty, callbackRate=1.0, activationPrice=activation, reduceOnly=True
                )
                tp_msg = f"Trail: {activation} (1.0%)"
            
            return True, f"{sl_msg}\n{tp_msg}"
            
        except Exception as e:
            return False, f"Sync Error: {e}"

    async def execute_long_position(self, symbol: str, atr: Optional[float] = None, strategy: str = "Manual") -> Tuple[bool, str]:
        """Execute a LONG position asynchronously."""
        
        # Route non-crypto to Alpaca
        # Route non-crypto to Alpaca
        if 'USDT' not in symbol:
            return await self._execute_alpaca_order(symbol, 'LONG', atr)

        # [NEW] Primary Exchange Routing
        target = self.config.get('primary_exchange', 'BINANCE')
        if ':' in symbol:
             parts = symbol.split(':')
             target = parts[0].upper()
             symbol = parts[1]
             
        if target == 'BYBIT':
             return await self._execute_bybit_order(symbol, 'LONG', strategy, atr)
        
        # Ensure Client with retry
        ok, err = await self._ensure_client()
        if not ok:
            return False, err
        
        # --- AI SENTIMENT & MACRO FILTER ---
        vol_risk = 'LOW'  # Default for later use
        from system_directive import AI_FILTER_ENABLED
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
        
        # --- SHIELD 2.0: CORRELATION CHECK ---
        # Checks if adding this asset over-correlates the portfolio
        if self.config.get('correlation_guard_enabled', True):
            is_safe, shield_msg = await self._check_correlation_safeguard(symbol)
            if not is_safe:
                return False, shield_msg

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
            
            # 3. Cancel Existing Orders (Robust with Verification)
            # Uses _cancel_all_robust to handle both standard and algo orders
            cleared = await self._cancel_all_robust(symbol, verify=True)
            if not cleared:
                print(f"⚠️ {symbol}: Could not verify all orders cleared before entry")
            
            # 4. Get Account & Price Info
            acc_info = await self.client.futures_account()
            total_equity = float(acc_info.get('totalMarginBalance', 0))
            
            ticker = await self.client.futures_symbol_ticker(symbol=symbol)
            current_price = float(ticker['price'])
            
            qty_precision, price_precision, min_notional = await self.get_symbol_precision(symbol)
            
            # 5. Calculate Position Size (Dynamic Risk)
            tp_ratio = self.config.get('tp_ratio', 1.5)
            if atr and atr > 0:
                mult = self.config.get('atr_multiplier', 2.0)
                sl_dist = mult * atr
                sl_price = round(current_price - sl_dist, price_precision)
                tp_price = round(current_price + (tp_ratio * sl_dist), price_precision)
                
                # Use Helper for Risk Sizing
                raw_quantity = self.calculate_dynamic_size(total_equity, current_price, sl_price, leverage, min_notional)
            else:
                margin_assignment = total_equity * max_capital_pct
                raw_quantity = (margin_assignment * leverage) / current_price
                sl_price = round(current_price * (1 - stop_loss_pct), price_precision)
                tp_price = round(current_price * (1 + (stop_loss_pct * tp_ratio * 2)), price_precision)
            
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
            
            # 7. Place SL/TP Orders (Using tracked helpers for anti-accumulation)
            try:
                # Stop Loss with tracking
                if sl_price > 0:
                    sl_ok, sl_result, _ = await self._place_conditional_with_tracking(
                        symbol, 'STOP_MARKET', 'SELL', quantity, sl_price
                    )
                    if not sl_ok:
                        print(f"⚠️ SL placement issue: {sl_result}")
                
                # Logic: TP1 (50%) + Trailing Stop (50%)
                qty_tp1 = float(round(quantity / 2, qty_precision))
                qty_trail = float(round(quantity - qty_tp1, qty_precision))
                
                # Check Min Notional for split (must be > 5 USDT each approx)
                is_split = (qty_tp1 * current_price) > min_notional and (qty_trail * current_price) > min_notional
                
                if is_split:
                    # TP1: Take 50% Profit with tracking
                    tp1_ok, tp1_result, _ = await self._place_conditional_with_tracking(
                        symbol, 'TAKE_PROFIT_MARKET', 'SELL', qty_tp1, tp_price
                    )
                    # Trailing: Let the rest run (Activate at TP1, Callback 1.0%)
                    trail_ok, trail_result, _ = await self._place_conditional_with_tracking(
                        symbol, 'TRAILING_STOP_MARKET', 'SELL', qty_trail, tp_price,
                        callbackRate=1.0, activationPrice=tp_price
                    )
                    tp_msg = f"TP1: {tp_price} (50%) | Trail: 1.0% (Act: {tp_price})"
                else:
                    # Capital too small: Full Trailing Stop with tracking
                    trail_ok, trail_result, _ = await self._place_conditional_with_tracking(
                        symbol, 'TRAILING_STOP_MARKET', 'SELL', quantity, entry_price,
                        callbackRate=1.0, activationPrice=entry_price
                    )
                    tp_msg = f"Trailing Stop: {entry_price} (1.0%)"

                
                success_msg = (
                    f"⚡ {symbol} (x{leverage})\n"
                    f"🧠 Estrategia: {strategy.replace('_', ' ')}\n\n"
                    f"📈 Entrada: {entry_price}\n"
                    f"📦 Tamaño: {quantity}\n\n"
                    f"🛑 SL: {sl_price}\n"
                    f"🎯 TP: {tp_msg}"
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
            error_msg = str(e) if str(e) else f"{type(e).__name__}: {repr(e)}"
            return False, f"[{symbol}] Error: {error_msg}"
    
    async def execute_short_position(self, symbol: str, atr: Optional[float] = None, strategy: str = "Manual") -> Tuple[bool, str]:
        """Execute a SHORT position asynchronously."""
        
        # Route non-crypto to Alpaca
        # Route non-crypto to Alpaca
        if 'USDT' not in symbol:
            return await self._execute_alpaca_order(symbol, 'SHORT', atr)

        # [NEW] Primary Exchange Routing
        target = self.config.get('primary_exchange', 'BINANCE')
        if ':' in symbol:
             parts = symbol.split(':')
             target = parts[0].upper()
             symbol = parts[1]
             
        if target == 'BYBIT':
             return await self._execute_bybit_order(symbol, 'SHORT', strategy, atr)
        
        if not self.client:
            return False, "No valid API Keys provided."
        
        # --- AI SENTIMENT FILTER (Inverse for Shorts) ---
        from system_directive import AI_FILTER_ENABLED
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
        
        # --- SHIELD 2.0: CORRELATION CHECK ---
        # Checks if adding this asset over-correlates the portfolio
        if self.config.get('correlation_guard_enabled', True):
            is_safe, shield_msg = await self._check_correlation_safeguard(symbol)
            if not is_safe:
                return False, shield_msg

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
            # 3. Cancel Existing Orders (Robust with Verification)
            # Uses _cancel_all_robust to handle both standard and algo orders
            cleared = await self._cancel_all_robust(symbol, verify=True)
            if not cleared:
                print(f"⚠️ {symbol}: Could not verify all orders cleared before entry")
            
            # 3. Get Info
            qty_precision, price_precision, min_notional = await self.get_symbol_precision(symbol)
            ticker = await self.client.futures_ticker(symbol=symbol)
            current_price = float(ticker['lastPrice'])
            
            acc = await self.client.futures_account()
            equity = float(acc['totalWalletBalance'])
            
            # 4. Calculate Size (Dynamic Risk)
            tp_ratio = self.config.get('tp_ratio', 1.5)
            if atr and atr > 0:
                mult = self.config.get('atr_multiplier', 2.0)
                sl_dist = mult * atr
                sl_price = round(current_price + sl_dist, price_precision)
                tp_price = round(current_price - (tp_ratio * sl_dist), price_precision)
                
                raw_quantity = self.calculate_dynamic_size(equity, current_price, sl_price, leverage, min_notional)
            else:
                sl_price = round(current_price * (1 + stop_loss_pct), price_precision)
                tp_price = round(current_price * (1 - (stop_loss_pct * tp_ratio * 2)), price_precision)
                
                max_alloc = equity * max_capital_pct
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
            
            # 6. Place SL/TP Orders (Using tracked helpers for anti-accumulation)
            try:
                # Stop Loss with tracking
                if sl_price > 0:
                    sl_ok, sl_result, _ = await self._place_conditional_with_tracking(
                        symbol, 'STOP_MARKET', 'BUY', quantity, sl_price
                    )
                    if not sl_ok:
                        print(f"⚠️ SL placement issue: {sl_result}")
                
                # Logic: TP1 (50%) + Trailing Stop (50%)
                qty_tp1 = float(round(quantity / 2, qty_precision))
                qty_trail = float(round(quantity - qty_tp1, qty_precision))
                
                is_split = (qty_tp1 * current_price) > min_notional and (qty_trail * current_price) > min_notional
                
                if is_split:
                    # TP1: Take 50% Profit with tracking
                    tp1_ok, tp1_result, _ = await self._place_conditional_with_tracking(
                        symbol, 'TAKE_PROFIT_MARKET', 'BUY', qty_tp1, tp_price
                    )
                    # Trailing: Let the rest run (Activate at TP1, Callback 1.0%)
                    trail_ok, trail_result, _ = await self._place_conditional_with_tracking(
                        symbol, 'TRAILING_STOP_MARKET', 'BUY', qty_trail, tp_price,
                        callbackRate=1.0, activationPrice=tp_price
                    )
                    tp_msg = f"TP1: {tp_price} (50%) | Trail: 1.0% (Act: {tp_price})"
                else:
                    # Capital too small: Full Trailing Stop with tracking
                    trail_ok, trail_result, _ = await self._place_conditional_with_tracking(
                        symbol, 'TRAILING_STOP_MARKET', 'BUY', quantity, entry_price,
                        callbackRate=1.0, activationPrice=entry_price
                    )
                    tp_msg = f"Trailing Stop: {entry_price} (1.0%)"

                
                success_msg = (
                    f"⚡ {symbol} (x{leverage})\n"
                    f"🧠 Estrategia: {strategy.replace('_', ' ')}\n\n"
                    f"📉 Entrada: {entry_price}\n"
                    f"📦 Tamaño: {quantity}\n\n"
                    f"🛑 SL: {sl_price}\n"
                    f"🎯 TP: {tp_msg}"
                )
                

                return True, success_msg

                
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
            error_msg = str(e) if str(e) else f"{type(e).__name__}: {repr(e)}"
            return False, f"[{symbol}] Error: {error_msg}"
    
    async def cancel_algo_orders(self, symbol: str) -> int:
        """
        Cancel ALL conditional orders (SL/TP/Trailing) for a symbol.
        
        After Dec 2024 Binance migration, conditional orders appear in standard
        futures_get_open_orders endpoint with 'orderId', NOT in algo endpoint.
        This method handles BOTH cases for maximum compatibility.
        
        Returns: Number of cancelled orders
        """
        if not self.client: return 0
        
        cancelled = 0
        try:
            # 1. Get all conditional orders for this symbol
            orders = await self.get_open_algo_orders(symbol)
            
            if not orders:
                return 0
            
            # 2. Cancel each order - try orderId first (standard), then algoId (algo service)
            for order in orders:
                order_id = order.get('orderId')
                algo_id = order.get('algoId')
                
                try:
                    if order_id:
                        # Standard cancel using orderId (works for post-Dec 2024 orders)
                        await self.client.futures_cancel_order(symbol=symbol, orderId=order_id)
                        cancelled += 1
                        print(f"✅ Cancelled order {order_id} for {symbol}")
                    elif algo_id:
                        # Algo service cancel (legacy)
                        await self.client._request(
                            'delete', 'algo/order', signed=True,
                            data={'symbol': symbol, 'algoId': algo_id}
                        )
                        cancelled += 1
                        print(f"✅ Cancelled algo {algo_id} for {symbol}")
                except Exception as e:
                    error_str = str(e)
                    # -2011 = Already cancelled/filled, -1007 = Timeout
                    if "-2011" not in error_str and "-1007" not in error_str and "Unknown order" not in error_str:
                        print(f"⚠️ Cancel order error: {e}")
            
            if cancelled > 0:
                print(f"✅ Total: Cancelled {cancelled} conditional orders for {symbol}")
                
        except Exception as e:
            print(f"⚠️ Cancel Orders Error ({symbol}): {e}")
        
        return cancelled

    async def get_open_algo_orders(self, symbol: str = None) -> List[Dict]:
        """
        Get open ALGO orders (conditional orders) for a symbol.
        
        NOTE: The Algo Service endpoint may not be available for all accounts.
        After Dec 2024, conditional orders (STOP_MARKET, TAKE_PROFIT_MARKET, 
        TRAILING_STOP_MARKET) should appear in regular futures_get_open_orders.
        
        This function checks both the Algo Service AND filters standard orders
        for conditional types.
        """
        if not self.client: return []
        
        conditional_orders = []
        
        # 1. First, check standard open orders for conditional types
        # (This is the reliable fallback that always works)
        try:
            standard_orders = await self.client.futures_get_open_orders(symbol=symbol)
            conditional_types = ['STOP_MARKET', 'TAKE_PROFIT_MARKET', 'TRAILING_STOP_MARKET', 
                                'STOP', 'TAKE_PROFIT', 'TRAILING_STOP']
            
            for order in standard_orders:
                if order.get('type', '') in conditional_types:
                    conditional_orders.append(order)
        except Exception as e:
            print(f"⚠️ Standard order check error ({symbol}): {e}")
        
        # 2. Try Algo Service endpoint (may not be available for all accounts)
        # Silently fail if not available - the standard orders check above is the fallback
        try:
            params = {'symbol': symbol} if symbol else {}
            
            # Try the algo endpoint - this may return 404 or error for some accounts
            result = await self.client._request(
                'get', 'algo/openOrders', signed=True, data=params
            )
            
            if isinstance(result, dict) and 'orders' in result:
                conditional_orders.extend(result['orders'])
            elif isinstance(result, list):
                conditional_orders.extend(result)
                
        except Exception:
            # Algo endpoint not available - that's OK, standard orders fallback works
            pass
        
        return conditional_orders

    async def wait_until_orders_cleared(self, symbol: str, timeout: float = 3.0) -> bool:
        """
        Wait until ALL orders (standard + algo) are confirmed cleared.
        Handles propagation latency after cancellation.
        
        Returns: True if cleared, False if timeout
        """
        import time
        start = time.time()
        
        while (time.time() - start) < timeout:
            try:
                # Check standard orders
                standard = await self.client.futures_get_open_orders(symbol=symbol)
                # Check algo orders
                algo = await self.get_open_algo_orders(symbol)
                
                if not standard and not algo:
                    print(f"✅ {symbol}: All orders cleared")
                    return True
                
                remaining = len(standard) + len(algo)
                print(f"⏳ {symbol}: Waiting for {remaining} orders to clear...")
                
            except Exception as e:
                print(f"⚠️ Order check error: {e}")
            
            await asyncio.sleep(0.5)
        
        print(f"⚠️ {symbol}: Timeout waiting for orders to clear")
        return False

    async def _cancel_all_robust(self, symbol: str, verify: bool = True) -> bool:
        """
        Robust cancellation of ALL orders (Standard + Algo).
        Handles -4120 (STOP_ORDER_SWITCH_ALGO) error after Dec 2024 migration.
        
        Args:
            symbol: Trading pair symbol
            verify: If True, wait and confirm all orders cleared
            
        Returns: True if all orders confirmed cleared (or verify=False)
        """
        # 1. Cancel Standard Orders (Limit, Market)
        try:
            await self.client.futures_cancel_all_open_orders(symbol=symbol)
        except Exception as e:
            error_str = str(e)
            # -4120 = STOP_ORDER_SWITCH_ALGO (expected for conditional orders after migration)
            # -2011 = Unknown order (nothing to cancel)
            if "-4120" not in error_str and "-2011" not in error_str and "Unknown order" not in error_str:
                print(f"⚠️ Standard Cancel ({symbol}): {e}")
        
        # 2. Cancel Algo Orders (Stop Loss, Take Profit, Trailing)
        await self.cancel_algo_orders(symbol)
        
        # 3. Verify all orders cleared (optional but recommended)
        if verify:
            return await self.wait_until_orders_cleared(symbol, timeout=3.0)
        
        return True



    async def execute_close_position(self, symbol: str, only_side: str = None) -> Tuple[bool, str]:
        """
        Close position for a symbol.
        Args:
            symbol: Asset to close.
            only_side: If 'LONG' or 'SHORT', will only close if position matches.
        """
        
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
            # 1. Cancel ALL orders BEFORE closing (Standard + Algo)
            # Use verify=False here since we'll verify at the end
            for _ in range(3):
                try:
                    await self._cancel_all_robust(symbol, verify=False)
                    break
                except Exception as e:
                    await asyncio.sleep(0.5)
            
            # 2. Get position
            positions = await self.client.futures_position_information(symbol=symbol)
            qty = 0.0
            for p in positions:
                if p['symbol'] == symbol:
                    qty = float(p['positionAmt'])
                    break
            
            if qty == 0:
                # No position, but ensure all orders are cleared
                await self.wait_until_orders_cleared(symbol, timeout=2.0)
                return True, f"⚠️ No position found for {symbol}, orders canceled."

            # SIDE CHECK: For Black Swan (Exit Longs Only)
            current_side = 'LONG' if qty > 0 else 'SHORT'
            if only_side and current_side != only_side:
                 return True, f"ℹ️ Skipped Close: {symbol} is {current_side}, target was {only_side}"
            
            # 3. Close position (Retry Logic)
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
            
            # 4. FINAL CLEANUP: Ensure all orders (including algo) are gone
            # Sometimes closing triggers new algo fills, so cancel again with verification
            cleared = await self._cancel_all_robust(symbol, verify=True)
            
            if not cleared:
                print(f"⚠️ {symbol}: Some orders may remain after close")
            
            return True, f"✅ Closed {symbol} ({qty})."
            
        except Exception as e:
            return False, f"Error: {e}"
    
    async def execute_close_all(self) -> Tuple[bool, str]:
        """
        NUCLEAR CLOSE: Close ALL open positions and cancel ALL open orders for ALL symbols.
        Ensures no orphaned orders (standard or algo) remain anywhere in the account.
        """
        if not self.client:
            return False, "No valid session."
        
        try:
            # 1. Get symbols with active positions
            active = await self.get_active_positions()
            pos_symbols = {p['symbol'] for p in active}
            
            # 2. Get symbols with standard open orders
            # (Executing without symbol returns all open orders)
            all_standard = await self.client.futures_get_open_orders()
            std_order_symbols = {o['symbol'] for o in all_standard}
            
            # 3. Get symbols with algo orders
            all_algo = await self.get_open_algo_orders()
            algo_order_symbols = {o['symbol'] for o in all_algo}
            
            # 4. Merge all unique symbols
            all_symbols = pos_symbols.union(std_order_symbols).union(algo_order_symbols)
            
            if not all_symbols:
                return True, "✅ No hay posiciones ni órdenes activas."
            
            print(f"☢️ NUCLEAR CLOSE: Cleansing {len(all_symbols)} symbols: {all_symbols}")
            
            results = []
            for sym in sorted(list(all_symbols)):
                # execute_close_position robustly cancels (pre & post) and closes position
                success, msg = await self.execute_close_position(sym)
                results.append(f"{sym}: {'✅' if success else '❌'}")
            
            return True, "🔥 Limpieza Total:\n" + "\n".join(results)
            
        except Exception as e:
            print(f"❌ Error in execute_close_all: {e}")
            return False, f"Error en Limpieza Total: {e}"

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

            # Filter: Only sync Binance positions (Alpaca uses different SL/TP mechanism)
            binance_pos = [p for p in active_pos if p.get('source') == 'BINANCE']
            alpaca_count = len([p for p in active_pos if p.get('source') == 'ALPACA'])
            
            if not binance_pos:
                if alpaca_count > 0:
                    return f"ℹ️ {alpaca_count} posiciones Alpaca activas (no requieren sync de SL/TP)."
                return "ℹ️ No hay posiciones activas para sincronizar."

            report = ["🔄 **Reporte de Sincronización:**", ""]
            if alpaca_count > 0:
                report.append(f"ℹ️ {alpaca_count} posiciones Alpaca omitidas (Binance sync only)")
                report.append("")
            
            for p in binance_pos:
                symbol = p['symbol']
                qty = float(p['amt'])
                if qty == 0: continue

                side = 'LONG' if qty > 0 else 'SHORT'
                entry_price = float(p['entry'])
                
                # Get current price
                ticker = await self.client.futures_symbol_ticker(symbol=symbol)
                current_price = float(ticker['price'])
                
                # Get precision
                qty_prec, price_prec, min_notional = await self.get_symbol_precision(symbol)

                # Standard SL/TP logic:
                stop_loss_pct = self.config.get('stop_loss_pct', 0.02)
                
                # BREAKEVEN LOGIC: If profit > 1%, Move SL to Entry
                pnl_pct = (current_price - entry_price) / entry_price if side == 'LONG' else (entry_price - current_price) / entry_price
                is_in_profit_1pct = pnl_pct >= 0.01
                
                if side == 'LONG':
                    # If in 1% profit, SL = Entry. Else, SL = Entry - Default %
                    if is_in_profit_1pct:
                        sl_price = round(entry_price, price_prec)
                        sl_label = "Breakeven"
                    else:
                        sl_price = round(entry_price * (1 - stop_loss_pct), price_prec)
                        sl_label = f"{stop_loss_pct*100}%"
                    
                    tp_price = round(entry_price * (1 + (stop_loss_pct * 3)), price_prec)
                else:
                    # Short: If in 1% profit, SL = Entry. Else, SL = Entry + Default %
                    if is_in_profit_1pct:
                        sl_price = round(entry_price, price_prec)
                        sl_label = "Breakeven"
                    else:
                        sl_price = round(entry_price * (1 + stop_loss_pct), price_prec)
                        sl_label = f"{stop_loss_pct*100}%"
                        
                    tp_price = round(entry_price * (1 - (stop_loss_pct * 3)), price_prec)

                # Execute Sync
                success, msg = await self.synchronize_sl_tp_safe(
                    symbol, qty, sl_price, tp_price, side, min_notional, qty_prec, entry_price=entry_price, current_price=current_price
                )
                
                status_icon = "✅" if success else "⚠️"
                report.append(f"**{symbol}** ({side}) {status_icon}")
                if success:
                    report.append(f"   SL: {sl_price} ({sl_label}) | TP: {tp_price}")
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
        from system_directive import SLTP_UPDATE_COOLDOWN
        from nexus_system.directive import SLTP_LAST_UPDATE
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
        """
        Cancel orders for symbols without positions (Standard + Algo).
        Also detects 'messy' active positions (too many orders) and advises sync.
        """
        if not self.client:
            return False, "No valid session."
        
        try:
            # Get BOTH standard AND algo orders
            all_orders = await self.client.futures_get_open_orders()
            algo_orders = await self.get_open_algo_orders()
            
            active_pos = await self.get_active_positions()
            active_symbols = set(p['symbol'] for p in active_pos)
            
            orphaned = set()
            messy_active = []
            
            # Logic: Group orders by symbol
            orders_by_symbol = {s: 0 for s in active_symbols}
            
            # Check standard orders
            for order in all_orders:
                sym = order['symbol']
                if sym not in active_symbols:
                    orphaned.add(sym)
                else:
                    orders_by_symbol[sym] += 1
            
            # Check algo orders (SL/TP/Trailing)
            for order in algo_orders:
                sym = order.get('symbol', '')
                if sym and sym not in active_symbols:
                    orphaned.add(sym)
                elif sym in active_symbols:
                    orders_by_symbol[sym] += 1
            
            # Identify Messy Active Positions (> 4 orders is suspicious for single position)
            for sym, count in orders_by_symbol.items():
                if count > 4:
                    messy_active.append(f"{sym} ({count})")
            
            total_orders = len(all_orders) + len(algo_orders)
            
            # 1. Cancel Orphans
            probs = []
            if orphaned:
                canceled = 0
                for sym in orphaned:
                    try:
                        await self._cancel_all_robust(sym)
                        canceled += 1
                    except Exception as e:
                        print(f"Error canceling {sym}: {e}")
                probs.append(f"🧹 Cleaned {canceled} orphaned symbols ({', '.join(orphaned)})")
            
            # 2. Report Messy Active
            if messy_active:
                probs.append(f"⚠️ Messy positions: {', '.join(messy_active)}. Run /sync to fix.")
            
            if not probs:
                return True, f"✅ No orphaned orders. ({total_orders} orders total, {len(active_symbols)} positions)"
            
            return True, "\n".join(probs)
            
        except Exception as e:
            return False, f"Cleanup Error: {e}"
    
    async def smart_breakeven_check(self, breakeven_roi_threshold: float = 0.10) -> str:
        """
        Smart Breakeven Manager - Protects profits by moving SL to breakeven.
        
        Rules:
        - If ROI >= 10% (threshold): Move SL to entry price + small buffer
        - This locks in breakeven and prevents winning trades from going negative
        
        Called periodically or after position opens.
        """
        if not self.client:
            return "❌ No session."
        
        try:
            active_pos = await self.get_active_positions()
            if not active_pos:
                return "ℹ️ No positions to check."
            
            report = ["📊 **Breakeven Check Report:**", ""]
            modified = 0
            
            for p in active_pos:
                symbol = p['symbol']
                qty = float(p['amt'])
                entry_price = float(p['entry'])
                unrealized_pnl = float(p.get('pnl', 0))
                leverage = int(p.get('leverage', self.config.get('leverage', 5)))
                
                if qty == 0 or entry_price == 0:
                    continue
                
                side = 'LONG' if qty > 0 else 'SHORT'
                
                # Get current price
                ticker = await self.client.futures_symbol_ticker(symbol=symbol)
                current_price = float(ticker['price'])
                
                # Use unrealized PnL from API (confirmed correct by user)
                pnl = unrealized_pnl
                
                # Calculate ROI using Binance formula:
                # ROI = PnL / Initial_Margin
                # Initial_Margin = Notional / Leverage = (qty * entry_price) / leverage
                notional = abs(qty) * entry_price
                initial_margin = notional / leverage if leverage > 0 else notional
                
                # ROI = PnL / Initial_Margin
                if initial_margin > 0:
                    roi = pnl / initial_margin
                else:
                    roi = 0
                
                roi_pct = roi * 100
                
                # Check if ROI >= threshold (10%)
                if roi >= breakeven_roi_threshold:
                    # Time to move SL to breakeven!
                    qty_prec, price_prec, min_notional = await self.get_symbol_precision(symbol)
                    
                    # Breakeven SL with small buffer (0.1% above entry for LONG, below for SHORT)
                    buffer = 0.001  # 0.1% buffer to cover fees
                    if side == 'LONG':
                        new_sl = round(entry_price * (1 + buffer), price_prec)
                        new_tp = round(current_price * 1.15, price_prec)  # Keep TP at +15% from current
                    else:
                        new_sl = round(entry_price * (1 - buffer), price_prec)
                        new_tp = round(current_price * 0.85, price_prec)  # Keep TP at -15% from current
                    
                    # Apply the new SL
                    try:
                        success, msg = await self.synchronize_sl_tp_safe(
                            symbol, qty, new_sl, new_tp, side, min_notional, qty_prec, 
                            entry_price=entry_price, current_price=current_price
                        )
                        if success:
                            modified += 1
                            report.append(f"✅ **{symbol}** - ROI: {roi_pct:.1f}% (PnL: ${pnl:.2f}) → SL moved to breakeven ({new_sl})")
                        else:
                            report.append(f"⚠️ **{symbol}** - ROI: {roi_pct:.1f}% → Failed: {msg}")
                    except Exception as e:
                        report.append(f"❌ **{symbol}** - Error: {e}")
                else:
                    report.append(f"⏳ **{symbol}** ({leverage}x) - ROI: {roi_pct:.1f}% (PnL: ${pnl:.2f}, Margin: ${initial_margin:.2f}) < {breakeven_roi_threshold*100:.0f}%")
            
            if modified > 0:
                report.append("")
                report.append(f"📈 **{modified} positions moved to breakeven!**")
            
            return "\n".join(report)
            
        except Exception as e:
            return f"❌ Breakeven Check Error: {e}"

    
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
        """Get list of active positions (Binance + Alpaca)."""
        active = []
        
        # 1. Binance Futures
        if self.client:
            try:
                # Use futures_account to get positions with correct leverage
                account = await self.client.futures_account()
                positions = account.get('positions', [])
                
                for p in positions:
                    amt = float(p.get('positionAmt', 0))
                    if abs(amt) > 0.0001:  # Filter dust
                        # Get leverage from position data
                        lev = p.get('leverage', '5')
                        active.append({
                            'symbol': p['symbol'],
                            'amt': amt,
                            'entry': float(p.get('entryPrice', 0)),
                            'pnl': float(p.get('unrealizedProfit', 0)),
                            'leverage': int(lev) if isinstance(lev, (int, float)) else int(lev),
                            'source': 'BINANCE'
                        })
            except Exception as e:
                print(f"Binance Position error: {e}")
        
        # 2. Alpaca Stocks
        if self.alpaca_client:
            try:
                loop = asyncio.get_event_loop()
                # Run sync Alpaca call in executor
                alp_positions = await loop.run_in_executor(None, self.alpaca_client.get_all_positions)
                
                for p in alp_positions:
                    amt = float(p.qty)
                    if p.side == 'short':
                        amt = -abs(amt)
                        
                    active.append({
                        'symbol': p.symbol,
                        'amt': amt,
                        'entry': float(p.avg_entry_price),
                        'pnl': float(p.unrealized_pl),
                        'leverage': 1, # Stocks usually 1:1 or 1:2, hard to track per pos via API simply
                        'source': 'ALPACA'
                    })
            except Exception as e:
                print(f"Alpaca Position error: {e}")

        return active
    
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
            
            # Alpaca Equity
            alpaca_equity = 0.0
            if self.alpaca_client:
                try:
                    loop = asyncio.get_event_loop()
                    acct = await loop.run_in_executor(None, self.alpaca_client.get_account)
                    alpaca_equity = float(acct.equity) if acct else 0.0
                except Exception as e:
                    print(f"⚠️ Alpaca equity warning: {e}")
            
            total = spot_usdt + futures_balance + alpaca_equity
            
            return {
                "spot_usdt": spot_usdt,
                "earn_usdt": 0.0,  # Deprecated
                "futures_balance": futures_balance,
                "futures_pnl": futures_pnl,
                "alpaca_equity": alpaca_equity,
                "total": total
            }
            
        except Exception as e:
            return {"error": str(e)}

    async def get_dashboard_summary(self) -> Dict:
        """
        Aggregates all data for the Unified Dashboard.
        - Wallet (Binance/Alpaca)
        - Active Positions (Count/PnL)
        - Mode/Risk Status
        """
        # 1. Wallet Data
        wallet = await self.get_wallet_details()
        if 'error' in wallet:
            wallet = {k: 0.0 for k in ['spot_usdt','earn_usdt','futures_balance','futures_pnl','alpaca_equity','total']}
            wallet['error'] = True
            
        # 2. Active Positions
        positions = await self.get_active_positions()
        pos_count = len(positions)
        longs = len([p for p in positions if p['amt'] > 0])
        shorts = len([p for p in positions if p['amt'] < 0])
        
        # Split by Exchange
        bin_pos = [p for p in positions if p.get('source') == 'BINANCE'] # Default if None
        alp_pos = [p for p in positions if p.get('source') == 'ALPACA']
        
        bin_longs = len([p for p in bin_pos if p['amt'] > 0])
        bin_shorts = len([p for p in bin_pos if p['amt'] < 0])
        
        alp_longs = len([p for p in alp_pos if p['amt'] > 0])
        alp_shorts = len([p for p in alp_pos if p['amt'] < 0])

        # 3. Aggregated PnL
        calc_pnl = sum(p['pnl'] for p in positions)
        bin_pnl = sum(p['pnl'] for p in bin_pos)
        alp_pnl = sum(p['pnl'] for p in alp_pos)
        
        # 4. Allocations
        total_equity = wallet['total']
        if total_equity > 0:
            alloc_binance_fut = (wallet['futures_balance'] / total_equity) * 100
            alloc_binance_spot = ((wallet['spot_usdt'] + wallet['earn_usdt']) / total_equity) * 100
            alloc_alpaca = (wallet['alpaca_equity'] / total_equity) * 100
        else:
            alloc_binance_fut = alloc_binance_spot = alloc_alpaca = 0

        # 5. Macro Stats
        macro = {"btc_dominance": 0.0, "global_state": "N/A"}
        if self.manager and hasattr(self.manager, 'get_macro_stats'):
             macro = self.manager.get_macro_stats()

        return {
            "wallet": wallet,
            "positions": {
                "count": pos_count,
                "longs": longs,
                "shorts": shorts,
                "total_pnl": calc_pnl,
                # Detailed breakdown
                "binance": {
                    "count": len(bin_pos),
                    "longs": bin_longs,
                    "shorts": bin_shorts,
                    "pnl": bin_pnl
                },
                "alpaca": {
                    "count": len(alp_pos),
                    "longs": alp_longs,
                    "shorts": alp_shorts,
                    "pnl": alp_pnl
                }
            },
            "allocation": {
                "binance_futures": alloc_binance_fut,
                "binance_spot": alloc_binance_spot,
                "alpaca": alloc_alpaca
            },
            "macro": macro,
            "config": self.config
        }
    
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

    async def _execute_bybit_order(self, symbol: str, side: str, strategy: str = "Manual", atr: Optional[float] = None) -> Tuple[bool, str]:
        """Execute order via Bybit Adapter."""
        if not self.bybit_client:
            return False, "⚠️ Bybit Client not initialized."
            
        try:
            # 1. Get Account Info
            bal = await self.bybit_client.get_account_balance()
            total_equity = bal['total']
            
            # 2. Get Price
            current_price = await self.bybit_client.get_market_price(symbol)
            if current_price <= 0:
                return False, f"❌ Failed to fetch price for {symbol}"
                
            # 3. Leverage
            leverage = self.config['leverage']
            await self.bybit_client.set_leverage(symbol, leverage)
            
            # 4. Sizing & SL/TP
            tp_ratio = self.config.get('tp_ratio', 1.5)
            stop_loss_pct = self.config['stop_loss_pct']
            
            if atr and atr > 0:
                 mult = self.config.get('atr_multiplier', 2.0)
                 sl_dist = mult * atr
                 if side == 'LONG':
                     sl_price = round(current_price - sl_dist, 2)
                     tp_price = round(current_price + (tp_ratio * sl_dist), 2)
                 else:
                     sl_price = round(current_price + sl_dist, 2)
                     tp_price = round(current_price - (tp_ratio * sl_dist), 2)
                 
                 # Dynamic Sizing (Approx)
                 risk_amt = total_equity * 0.01 
                 dist_to_sl = sl_dist
                 raw_quantity = risk_amt / dist_to_sl if dist_to_sl > 0 else 0
            else:
                 margin_assignment = total_equity * self.config['max_capital_pct']
                 raw_quantity = (margin_assignment * leverage) / current_price
                 
                 if side == 'LONG':
                     sl_price = round(current_price * (1 - stop_loss_pct), 2)
                     tp_price = round(current_price * (1 + (stop_loss_pct * 3)), 2)
                 else:
                     sl_price = round(current_price * (1 + stop_loss_pct), 2)
                     tp_price = round(current_price * (1 - (stop_loss_pct * 3)), 2)

            quantity = round(raw_quantity, 4) 
            
            if quantity <= 0: return False, "Quantity too small."
            
            # 5. Execute
            res = await self.bybit_client.place_order(
                symbol, side, 'MARKET', quantity, 
                takeProfit=str(tp_price), stopLoss=str(sl_price)
            )
            
            if 'error' in res:
                return False, f"Bybit Error: {res['error']}"
                
            return True, (
                f"✅ Bybit {side} {symbol}\n"
                f"Qty: {quantity}\n"
                f"Entry: {current_price}\n"
                f"SL: {sl_price}\n"
                f"TP: {tp_price}"
            )

        except Exception as e:
            return False, f"Bybit Execution Error: {e}"
    
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
            buying_power = float(acct.buying_power)
            
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
            
            # Cap at Buying Power (leave 2% buffer for fees/fluctuation)
            if max_alloc > (buying_power * 0.98):
                max_alloc = buying_power * 0.98
                
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
            error_str = str(e)
            if "insufficient buying power" in error_str:
                return False, f"❌ Alpaca: Insufficient Buying Power (BP: {getattr(acct, 'buying_power', 'N/A')})"
            return False, f"Alpaca Error: {e}"

    # --- RESTORED METHODS FROM SYNC ---
    
    def get_trade_preview(self, symbol: str, side: str, current_price: float, atr: Optional[float] = None) -> Tuple[float, float, float]:
        """
        Calculates TP, SL, and TS (Trailing Stop Activation) prices without executing the trade.
        Returns: (sl_price, tp_price, ts_price)
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
            
            # TS Activation is usually set to TP1 price in our logic
            ts_price = tp_price
            
            return sl_price, tp_price, ts_price
        except Exception as e:
            print(f"Preview Error: {e}")
            return 0.0, 0.0, 0.0

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
        
        # Check if enabled in config
        if not self.config.get('circuit_breaker_enabled', True):
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
        self.engine = None
        
    def set_nexus_engine(self, engine):
        """Inject NexusCore engine reference."""
        self.engine = engine
        
    def get_macro_stats(self) -> Dict:
        """Retrieve Global Macro Stats from Engine (RiskGuardian)."""
        if self.engine and self.engine.risk_guardian:
             rg = self.engine.risk_guardian
             return {
                 "btc_dominance": getattr(rg, 'btc_dominance', 0.0),
                 "global_state": getattr(rg, 'global_state', 'NORMAL'),
                 "total_cap": getattr(rg, 'total_cap', 0.0)
             }
        return {"btc_dominance": 0.0, "global_state": "N/A", "total_cap": 0.0}
    

    async def load_sessions(self):
        """Load sessions from PostgreSQL (with JSON fallback)."""
        async with self._lock:
            loaded_source = "NONE"
            
            # Try PostgreSQL first
            postgresql_success = False
            try:
                from servos.db import load_all_sessions
                db_sessions = load_all_sessions()
                
                if db_sessions is not None:
                    for chat_id, info in db_sessions.items():
                        # SANITIZE: Check authorization
                        from servos.db import get_user_role
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
                            config=config,
                            manager=self
                        )
                        await session.initialize(verbose=False)
                        self.sessions[chat_id] = session
                    
                    print(f"🐘 Loaded {len(self.sessions)} sessions from PostgreSQL")
                    postgresql_success = True
                    loaded_source = "POSTGRESQL"
            except Exception as e:
                print(f"⚠️ PostgreSQL load failed, using JSON fallback: {e}")
            
            # Fallback to JSON if PostgreSQL failed
            if not postgresql_success:
                if not os.path.exists(self.data_file):
                    pass # Will ensure admin below
                else:
                    try:
                        with open(self.data_file, 'r') as f:
                            data = json.load(f)
                        
                        for chat_id, info in data.items():
                            # SANITIZE: Check authorization
                            from servos.db import get_user_role
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
                                config=config,
                                manager=self
                            )
                            await session.initialize(verbose=False)
                            self.sessions[chat_id] = session
                        
                        print(f"📁 Loaded {len(self.sessions)} sessions from {self.data_file}")
                        loaded_source = "JSON"
                        
                    except Exception as e:
                        print(f"❌ Session Load Error: {e}")
        
        # Ensure Admin Session (Silent)
        await self._ensure_admin_session(verbose=False)
        
        # --- AGGREGATED STARTUP LOG ---
        print("🧠 Nexus Analyst: CONNECTED.")
        
        proxied_users = []
        binance_users = []
        alpaca_users = []
        
        # Extract proxy URL from first available session for display
        proxy_url_display = ""
        
        for s in self.sessions.values():
            if s._proxy:
                proxied_users.append(s.chat_id)
                if not proxy_url_display:
                    proxy_url_display = s._proxy
            
            if s.client:
                binance_users.append(s.chat_id)
            
            if s.alpaca_client:
                alpaca_users.append(s.chat_id)
        
        if proxied_users:
            print(f"🔄 Proxy configured: [{len(proxied_users):02d} Users]")
        
        if binance_users:
            print(f"✅ Binance Client Init (✅ Proxy): [{len(binance_users):02d} Users]")
            
        if alpaca_users:
            print(f"✅ Alpaca Client Initialized (Paper: Mixed): [{len(alpaca_users):02d} Users]")
    

    async def _ensure_admin_session(self, verbose: bool = True):
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
                session = AsyncTradingSession(admin_id, api_key, api_secret, manager=self)
                await session.initialize(verbose=verbose)
                self.sessions[admin_id] = session
                if verbose:
                    print(f"🔑 Admin session created for {admin_id} (Env Vars)")
            
            # Case 2: Session exists but Keys mismatch -> Update it
            else:
                session = self.sessions[admin_id]
                if session.api_key != api_key or session.api_secret != api_secret:
                    session.api_key = api_key
                    session.api_secret = api_secret
                    # Re-init client with new keys
                    await session.initialize(verbose=verbose)
                    if verbose:
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
                from servos.db import save_all_sessions
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
        
        session = AsyncTradingSession(chat_id, api_key, api_secret, config, manager=self)
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

