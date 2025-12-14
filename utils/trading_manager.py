"""
Antigravity Bot - Async Trading Manager
Async version of TradingSession using python-binance AsyncClient

NOTE: This is a wrapper that provides async interfaces while maintaining 
backward compatibility with the sync TradingSession for gradual migration.
"""

import os
import json
import aiohttp
import asyncio
from typing import Optional, Dict, Any, Tuple, List

# Binance Async Client
from binance import AsyncClient

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
            "personality": "NEXUS",
            "sentiment_filter": True,
            "atr_multiplier": 2.0,
            "alpaca_key": None,
            "alpaca_secret": None
        }
        
        if config:
            self.config.update(config)
        
        self.mode = self.config.get('mode', 'WATCHER')
        
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
                
                # --- PROXY FORCE VIA SESSION REPLACEMENT ---
                # aiohttp requires 'trust_env=True' in Constructor to honor env vars
                if self._proxy:
                    print(f"🔄 [Chat {self.chat_id}] Configuring Proxy Session...")
                    # Close default session
                    await self.client.close_connection()
                    
                    # Set Env Vars
                    os.environ['HTTPS_PROXY'] = self._proxy
                    os.environ['HTTP_PROXY'] = self._proxy
                    
                    # Create NEW session with trust_env=True
                    # This forces aiohttp to use the Env Vars we just set
                    self.client.session = aiohttp.ClientSession(trust_env=True)
                
                print(f"✅ [Chat {self.chat_id}] Binance Async Client Initialized (Proxy Forced).")
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
            "has_keys": bool(self.client)
        }
    
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
        if self.client:
            return True, ""
        
        err = getattr(self, '_init_error', 'Unknown Error')
        return False, f"Client Connection Failed: {err}"

    async def execute_long_position(self, symbol: str, atr: Optional[float] = None) -> Tuple[bool, str]:
        """Execute a LONG position asynchronously."""
        
        # Route non-crypto to Alpaca
        if 'USDT' not in symbol:
            return await self._execute_alpaca_order(symbol, 'LONG', atr)
        
        # Ensure Client with retry
        ok, err = await self._ensure_client()
        if not ok:
            return False, err
        
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
                    return False, f"⚠️ {symbol} has an open SHORT. Close it first."
            
            # 2. Set Leverage
            await self.client.futures_change_leverage(symbol=symbol, leverage=leverage)
            
            # 3. Cancel Existing Orders
            try:
                await self.client.futures_cancel_all_open_orders(symbol=symbol)
            except:
                pass
            
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
                
                # Min notional check
                notional = raw_quantity * current_price
                if notional < min_notional:
                    raw_quantity = (min_notional * 1.05) / current_price
                
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
            
            # 6. Execute Market Buy
            try:
                order = await self.client.futures_create_order(
                    symbol=symbol, side='BUY', type='MARKET', quantity=quantity
                )
                entry_price = float(order.get('avgPrice', current_price)) or current_price
            except Exception as e:
                return False, f"❌ Failed to open position: {e}"
            
            # 7. Place SL/TP Orders
            try:
                # Stop Loss
                if sl_price > 0:
                    await self.client.futures_create_order(
                        symbol=symbol, side='SELL', type='STOP_MARKET',
                        stopPrice=sl_price, closePosition=True
                    )
                
                # Take Profit
                await self.client.futures_create_order(
                    symbol=symbol, side='SELL', type='TAKE_PROFIT_MARKET',
                    stopPrice=tp_price, quantity=quantity, reduceOnly=True
                )
                
                success_msg = (
                    f"Long {symbol} (x{leverage})\n"
                    f"Entry: {entry_price}\n"
                    f"Qty: {quantity}\n"
                    f"SL: {sl_price}\n"
                    f"TP: {tp_price}"
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
                    return False, f"⚠️ {symbol} has an open LONG. Close it first."
            
            # 2. Set Leverage & Cancel Orders
            await self.client.futures_change_leverage(symbol=symbol, leverage=leverage)
            try:
                await self.client.futures_cancel_all_open_orders(symbol=symbol)
            except:
                pass
            
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
            
            max_alloc = equity * max_capital_pct
            if (raw_quantity * current_price) > max_alloc:
                raw_quantity = max_alloc / current_price
            
            quantity = float(round(raw_quantity, qty_precision))
            
            if (quantity * current_price) < min_notional:
                return False, f"❌ {symbol}: Insufficient capital for min notional."
            
            if quantity <= 0:
                return False, "Position size too small."
            
            # 5. Execute Market Sell
            try:
                order = await self.client.futures_create_order(
                    symbol=symbol, side='SELL', type='MARKET', quantity=quantity
                )
                entry_price = float(order.get('avgPrice', current_price)) or current_price
            except Exception as e:
                return False, f"❌ Failed to open position: {e}"
            
            # 6. Place SL/TP
            try:
                if sl_price > 0:
                    await self.client.futures_create_order(
                        symbol=symbol, side='BUY', type='STOP_MARKET',
                        stopPrice=sl_price, closePosition=True
                    )
                
                await self.client.futures_create_order(
                    symbol=symbol, side='BUY', type='TAKE_PROFIT_MARKET',
                    stopPrice=tp_price, quantity=quantity, reduceOnly=True
                )
                
                return True, (
                    f"Short {symbol} (x{leverage})\n"
                    f"Entry: {entry_price}\n"
                    f"Qty: {quantity}\n"
                    f"SL: {sl_price}\n"
                    f"TP: {tp_price}"
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
            # Cancel orders
            await self.client.futures_cancel_all_open_orders(symbol=symbol)
            
            # Get position
            positions = await self.client.futures_position_information(symbol=symbol)
            qty = 0.0
            for p in positions:
                if p['symbol'] == symbol:
                    qty = float(p['positionAmt'])
                    break
            
            if qty == 0:
                return True, f"⚠️ No position found for {symbol}, orders canceled."
            
            # Close
            side = 'SELL' if qty > 0 else 'BUY'
            await self.client.futures_create_order(
                symbol=symbol, side=side, type='MARKET',
                reduceOnly=True, quantity=abs(qty)
            )
            
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
    
    async def execute_update_sltp(self, symbol: str, side: str, atr: Optional[float] = None) -> Tuple[bool, str]:
        """Update SL/TP for existing position."""
        if not self.client:
            return False, "No session."
        
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
            
            # Cancel old orders
            await self.client.futures_cancel_all_open_orders(symbol=symbol)
            await asyncio.sleep(0.5)
            
            # Get new price info
            ticker = await self.client.futures_symbol_ticker(symbol=symbol)
            current_price = float(ticker['price'])
            qty_precision, price_precision, min_notional = await self.get_symbol_precision(symbol)
            
            abs_qty = abs(qty)
            stop_loss_pct = self.config['stop_loss_pct']
            
            # Calculate new SL/TP
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
                    tp_price = round(current_price * (1 + (stop_loss_pct * 1.5)), price_precision)
                else:
                    sl_price = round(current_price * (1 + stop_loss_pct), price_precision)
                    tp_price = round(current_price * (1 - (stop_loss_pct * 1.5)), price_precision)
            
            # Place new orders
            sl_side = 'SELL' if side == 'LONG' else 'BUY'
            
            await self.client.futures_create_order(
                symbol=symbol, side=sl_side, type='STOP_MARKET',
                stopPrice=sl_price, reduceOnly=True, quantity=abs_qty
            )
            
            await self.client.futures_create_order(
                symbol=symbol, side=sl_side, type='TAKE_PROFIT_MARKET',
                stopPrice=tp_price, reduceOnly=True, quantity=abs_qty
            )
            
            return True, (
                f"🔄 SL/TP Updated for {symbol}\n"
                f"New SL: {sl_price}\n"
                f"New TP: {tp_price}"
            )
            
        except Exception as e:
            return False, f"Update Error: {e}"
    
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
        """Get wallet balances."""
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
            
            return {
                "spot_usdt": spot_usdt,
                "futures_balance": futures_balance,
                "futures_pnl": futures_pnl,
                "total": spot_usdt + futures_balance
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
        """Load sessions from JSON file."""
        async with self._lock:
            if not os.path.exists(self.data_file):
                # Check for admin keys in env
                await self._ensure_admin_session()
                return
            
            try:
                with open(self.data_file, 'r') as f:
                    data = json.load(f)
                
                for chat_id, info in data.items():
                    session = AsyncTradingSession(
                        chat_id=chat_id,
                        api_key=info.get('api_key', ''),
                        api_secret=info.get('api_secret', ''),
                        config=info.get('config')
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
        """Persist sessions to JSON file."""
        async with self._lock:
            data = {}
            for chat_id, session in self.sessions.items():
                data[chat_id] = {
                    'api_key': session.api_key,
                    'api_secret': session.api_secret,
                    'config': session.config
                }
            
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
