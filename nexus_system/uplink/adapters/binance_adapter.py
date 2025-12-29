"""
Binance Futures Adapter.
Implements IExchangeAdapter for Binance USD-M Futures.
"""

import os
import pandas as pd
from typing import Dict, Any, List, Optional, Callable
import ccxt.async_support as ccxt

from .base import IExchangeAdapter


class BinanceAdapter(IExchangeAdapter):
    """
    Binance USD-M Futures implementation.
    Uses CCXT for REST and custom WebSocket for streaming.
    """

    def __init__(self, api_key: str = None, api_secret: str = None, **kwargs):
        self._api_key = api_key or os.getenv('BINANCE_API_KEY', '')
        self._api_secret = api_secret or os.getenv('BINANCE_SECRET', '')
        self._ws_manager = None
        self._price_cache = None
        self._is_hedge_mode = False # Default to One-Way

    @property
    def name(self) -> str:
        return "binance"

    def _format_symbol(self, symbol: str) -> str:
        """Format symbol for CCXT: BTCUSDT -> BTC/USDT:USDT"""
        if not symbol:
            return symbol
        if 'USDT' in symbol and '/' not in symbol and ':' not in symbol:
            return symbol.replace('USDT', '/USDT:USDT')
        return symbol

    async def initialize(self, verbose: bool = False, **kwargs) -> bool:
        """Initialize Binance connection."""
        try:
            # Clean credentials (strip whitespace/quotes potentially left from env)
            self._api_key = self._api_key.strip().strip("'\"") if self._api_key else ''
            self._api_secret = self._api_secret.strip().strip("'\"") if self._api_secret else ''

            # Validate credentials
            if not self._api_key or not self._api_secret:
                print(f"❌ BinanceAdapter: Missing API credentials!")
                return False
            
            # Diagnostic: Show masked credentials for debugging (with repr to show hidden chars)
            key_preview = f"{self._api_key[:4]}...{self._api_key[-4:]}" if len(self._api_key) > 8 else "TOO_SHORT"
            print(f"🔑 BinanceAdapter: Using key [{key_preview}] (len={len(self._api_key)})")
            
            # Diagnostic: Check Public IP (to verify Proxy/Whitelist match)
            try:
                import aiohttp
                async with aiohttp.ClientSession() as session:
                    # Check explicit proxy if set for this check
                    proxy_url = kwargs.get('http_proxy') or os.getenv('PROXY_URL')
                    async with session.get('https://api.ipify.org', proxy=proxy_url) as resp:
                        if resp.status == 200:
                            ip = await resp.text()
                            print(f"🌍 BinanceAdapter: Public IP -> {ip} (Proxy: {'Yes' if proxy_url else 'No'})")
            except Exception as ip_err:
                 print(f"⚠️ BinanceAdapter: IP Check failed - {ip_err}")
            
            config = {
                'apiKey': self._api_key,
                'secret': self._api_secret,
                'enableRateLimit': True,
                'options': {'defaultType': 'future'}
            }
            
            # Check for testnet mode
            use_testnet = kwargs.get('testnet') or os.getenv('BINANCE_TESTNET', '').lower() == 'true'
            if use_testnet:
                config['options']['defaultType'] = 'future'
                config['options']['test'] = True
                print(f"🧪 BinanceAdapter: TESTNET mode enabled")
            
            # Unified Proxy Config (CCXT Async uses aiohttp_proxy, NOT proxies dict)
            http_proxy = kwargs.get('http_proxy') or os.getenv('PROXY_URL') or os.getenv('HTTP_PROXY') or os.getenv('http_proxy')

            self._exchange = ccxt.binanceusdm(config)
            
            # For async CCXT, proxy must be set via aiohttp_proxy property AFTER creation
            if http_proxy:
                self._exchange.aiohttp_proxy = http_proxy
            
            # Step 1: Test public endpoint first (no auth needed)
            try:
                await self._exchange.load_markets()
                print(f"✅ BinanceAdapter: Markets loaded (public endpoint OK)")
            except Exception as market_err:
                print(f"⚠️ BinanceAdapter: load_markets failed - {market_err}")
                # Markets load can fail for non-auth reasons, try to continue
            
            # Step 2: Test authenticated endpoint
            try:
                balance = await self._exchange.fetch_balance()
                print(f"✅ BinanceAdapter: Auth OK (balance fetched)")
                
                # Step 3: Detect Position Mode (Hedge vs One-Way)
                try:
                    mode_info = await self._exchange.fapiPrivateGetPositionSideDual()
                    # Response format: {"dualSidePosition": true} for Hedge, false for One-Way
                    self._is_hedge_mode = mode_info.get('dualSidePosition', False)
                    mode_str = "HEDGE" if self._is_hedge_mode else "ONE-WAY"
                    print(f"⚙️ BinanceAdapter: Position Mode -> {mode_str}")
                except Exception as mode_err:
                    print(f"⚠️ BinanceAdapter: Could not detect Position Mode - {mode_err}")
                    # Keep default _is_hedge_mode = False
                
                return True
            except Exception as auth_err:
                err_str = str(auth_err)
                print(f"❌ BinanceAdapter: Auth failed - {auth_err}")
                
                # Specific error guidance
                if '-2015' in err_str:
                    print(f"   💡 Error -2015 = Invalid API-key, IP not whitelisted, or missing Futures permission")
                    print(f"   💡 Check: 1) API key exists in Binance, 2) IP whitelisted, 3) 'Enable Futures' checked")
                    print(f"   💡 Ensure the IP {kwargs.get('discovered_ip', 'DETECTED_ABOVE')} is whitelisted.")
                elif '-1021' in err_str:
                    print(f"   💡 Error -1021 = Timestamp sync issue. Server time differs from Binance.")
                elif '-2014' in err_str:
                    print(f"   💡 Error -2014 = API key format is invalid")
                    
                raise auth_err
                
        except Exception as e:
            print(f"❌ BinanceAdapter: Init failed - {e}")
            # Clean up resources to prevent "Unclosed client session" warnings
            if self._exchange:
                try:
                    await self._exchange.close()
                except:
                    pass
                self._exchange = None
            return False

    async def fetch_candles(
        self, 
        symbol: str, 
        timeframe: str = '15m', 
        limit: int = 100
    ) -> pd.DataFrame:
        """Fetch OHLCV data from Binance Futures."""
        if not self._exchange:
            return pd.DataFrame()
            
        try:
            # Format symbol for CCXT (BTC/USDT:USDT for futures)
            formatted = self._format_symbol(symbol)
            ohlcv = await self._exchange.fetch_ohlcv(formatted, timeframe, limit=limit)
            
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            return df
            
        except Exception as e:
            # Parse error
            err_msg = str(e)
            import re, json
            match = re.search(r'\{.*"code":.*\}', err_msg)
            if match:
                 try:
                     data = json.loads(match.group(0))
                     err_msg = f"Binance Error {data.get('code')}: {data.get('msg')}"
                 except: pass
                 
            print(f"⚠️ BinanceAdapter: fetch_candles error ({symbol}): {err_msg}")
            return pd.DataFrame()

    async def get_account_balance(self) -> Dict[str, float]:
        """Get Binance Futures account balance."""
        if not self._exchange:
            return {'total': 0, 'available': 0, 'currency': 'USDT'}
            
        try:
            balance = await self._exchange.fetch_balance()
            usdt = balance.get('USDT', {})
            return {
                'total': float(usdt.get('total', 0)),
                'available': float(usdt.get('free', 0)),
                'currency': 'USDT'
            }
        except Exception as e:
            # Parse error
            err_msg = str(e)
            import re, json
            match = re.search(r'\{.*"code":.*\}', err_msg)
            if match:
                 try:
                     data = json.loads(match.group(0))
                     err_msg = f"Binance Error {data.get('code')}: {data.get('msg')}"
                 except: pass
            
            print(f"⚠️ BinanceAdapter: get_balance error: {err_msg}")
            return {'total': 0, 'available': 0, 'currency': 'USDT'}

    async def set_leverage(self, symbol: str, leverage: int) -> bool:
        """Set leverage for a symbol (required before placing orders)."""
        if not self._exchange:
            return False
        try:
            # Format symbol for CCXT
            formatted = self._format_symbol(symbol)
            await self._exchange.set_leverage(leverage, formatted)
            print(f"✅ BinanceAdapter: Leverage set to {leverage}x for {symbol}")
            return True
        except Exception as e:
            # Leverage already set is not an error
            if 'leverage not changed' in str(e).lower() or 'no need to change' in str(e).lower():
                return True
            print(f"⚠️ BinanceAdapter: set_leverage error ({symbol}, {leverage}x): {e}")
            return False

    async def set_margin_mode(self, symbol: str, mode: str = 'CROSS') -> bool:
        """Set margin mode (CROSS or ISOLATED) for a symbol."""
        if not self._exchange:
            return False
        try:
            formatted = self._format_symbol(symbol)
            await self._exchange.set_margin_mode(mode.lower(), formatted)
            return True
        except Exception as e:
            # Already set to requested mode is not an error
            if 'no need to change' in str(e).lower() or 'already' in str(e).lower():
                return True
            print(f"⚠️ BinanceAdapter: set_margin_mode error ({symbol}, {mode}): {e}")
            return False

    async def get_symbol_info(self, symbol: str) -> Dict[str, Any]:
        """Get symbol precision and limits."""
        if not self._exchange: return {}
        
        try:
            formatted = self._format_symbol(symbol)
            # Check if market is loaded?
            # CCXT usually loads on init. But safe to check?
            # Just try .market()
            try:
                market = self._exchange.market(formatted)
            except:
                # Reload if missing
                await self._exchange.load_markets()
                market = self._exchange.market(formatted)

            return {
                'symbol': symbol,
                # CCXT precision mode for Binance is DECIMAL_PLACES (int)
                'price_precision': int(market['precision']['price']),
                'quantity_precision': int(market['precision']['amount']),
                'min_notional': float(market['limits']['cost']['min']) if 'cost' in market['limits'] else 5.0
            }
        except Exception as e:
            print(f"⚠️ BinanceAdapter Info Error: {e}")
            return {}

    async def place_order(
        self, 
        symbol: str, 
        side: str,
        order_type: str,
        quantity: float,
        price: Optional[float] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Place order on Binance Futures."""
        if not self._exchange:
            return {'error': 'Not initialized'}
        
        # FIX: Ensure quantity is positive for CCXT
        quantity = abs(quantity)

        # Format symbol for CCXT (BTCUSDT -> BTC/USDT:USDT)
        symbol = self._format_symbol(symbol)
        
        # Log de orden a colocar (solo en modo debug)
        # self.logger.debug(f"Colocando orden: {symbol} {side} {order_type} Qty={quantity} Price={price}")

        try:
            params = kwargs.copy()
            
            # --- FIX: Unpack nested 'params' dict if present ---
            # trading_manager sometimes passes params={'stopPrice': ..., 'reduceOnly': True}
            # while the adapter expects these as direct kwargs. Merge them.
            if 'params' in params:
                nested = params.pop('params')
                if isinstance(nested, dict):
                    params.update(nested)
            # ---------------------------------------------------
            
            # --- POSITION MODE HANDLING ---
            # Strip positionSide if account is in One-Way mode
            if not self._is_hedge_mode and 'positionSide' in params:
                 # In One-Way mode, Binance rejects positionSide parameter
                 params.pop('positionSide')
            # ------------------------------

            
            if order_type.upper() == 'MARKET':
                result = await self._exchange.create_order(
                    symbol, 'market', side.lower(), quantity, None, params
                )
            elif order_type.upper() == 'LIMIT':
                result = await self._exchange.create_order(
                    symbol, 'limit', side.lower(), quantity, price, params
                )
            else:
                # For conditional orders (STOP_MARKET, TAKE_PROFIT_MARKET, etc.)
                # CCXT requires specific handling for conditional orders
                
                # Extract stopPrice from params if passed, otherwise use price arg
                stop_price = params.pop('stopPrice', None) or price
                
                if not stop_price:
                    return {'error': 'stopPrice is required for conditional orders'}
                
                # For MARKET conditional orders, limit_price must be None
                # For LIMIT conditional orders, limit_price is the execution price
                limit_price = None
                if 'MARKET' not in order_type.upper():
                    # STOP_LIMIT or TAKE_PROFIT_LIMIT - use price as limit execution price
                    limit_price = params.pop('price', stop_price)  # Default to stop_price if not provided
                
                # Map order types to CCXT format
                # CCXT uses lowercase with underscores: stop_market, take_profit_market
                # Convert STOP_MARKET -> stop_market, TAKE_PROFIT_MARKET -> take_profit_market
                ccxt_order_type = order_type.lower()
                
                # Ensure reduceOnly is in params (not as kwarg)
                if 'reduceOnly' not in params and kwargs.get('reduceOnly'):
                    params['reduceOnly'] = kwargs.pop('reduceOnly')
                
                # Set stopPrice in params (required by Binance)
                params['stopPrice'] = stop_price
                
                # --- RETRY LOGIC FOR INVALID SYMBOL (-1121) ---
                try:
                    # Use the correct order type for CCXT
                    result = await self._exchange.create_order(
                        symbol, ccxt_order_type, side.lower(), quantity, limit_price, params
                    )
                except Exception as e_order:
                    # Check for Invalid Symbol / Param (-1121)
                    err_str = str(e_order)
                    if "-1121" in err_str or "Invalid symbol" in err_str:
                        print(f"⚠️ Symbol {symbol} rejected (-1121). Retrying alternates...", flush=True)
                        # Alternate 1: Standard (UNI/USDT)
                        alt1 = symbol.replace(':USDT', '')
                        # Alternate 2: Raw (UNIUSDT)
                        alt2 = symbol.replace('/USDT:USDT', 'USDT').replace('/', '')
                        
                        success_alt = False
                        for alt in [alt1, alt2]:
                            try:
                                print(f"🔄 Retrying with: {alt}", flush=True)
                                # Retry with original order type (not 'market')
                                # Keep the conditional order type for SL/TP orders
                                result = await self._exchange.create_order(
                                    alt, ccxt_order_type, side.lower(), quantity, limit_price, params
                                )
                                symbol = alt # Update symbol for return
                                success_alt = True
                                break
                            except Exception as e_alt:
                                print(f"⚠️ Retry {alt} failed: {e_alt}", flush=True)
                        
                        if not success_alt:
                            print(f"❌ ALL RETRIES FAILED for {symbol}", flush=True)
                            raise e_order # Raise original if all fail
                    else:
                        raise e_order # Raise other errors
                # ---------------------------------------------
            
            ret = {
                'orderId': result.get('id'),
                'status': result.get('status'),
                'symbol': symbol,
                'side': side,
                'quantity': quantity,
                'price': result.get('price') or price
            }
            # Log de resultado de orden (solo en modo debug)
            # self.logger.debug(f"Orden colocada: ID={result.get('id')} Status={result.get('status')}")
            return ret
            
        except Exception as e:
            # Log de excepción (ya se maneja más abajo)
            # Standardized Error Handling
            error_msg = str(e)
            
            # 1. Parse JSON if present (CCXT often wraps exchange errors)
            import json, re
            code = None
            msg = ""
            
            # Try to find JSON block
            match = re.search(r'\{.*"code":.*\}', error_msg)
            if match:
                try:
                    data = json.loads(match.group(0))
                    code = data.get('code')
                    msg = data.get('msg', '')
                except:
                    pass
            
            # 2. Map Critical Errors
            if code == -2015:
                return {'error': 'INVALID_API_KEY'}
            elif code == -2011:
                return {'error': 'UNKNOWN_ORDER'}
            elif code == -4003: # Quantity too large?
                return {'error': f'QUANTITY_ERROR: {msg}'}
            elif code == -2019: # Margin is insufficient
                return {'error': f'INSUFFICIENT_MARGIN: {msg}'}
            elif code == -2021: # ORDER_WOULD_IMMEDIATELY_TRIGGER
                return {'error': 'ORDER_WOULD_IMMEDIATELY_TRIGGER', 'code': -2021, 'message': 'El precio de activación ya fue alcanzado. Ajusta el stopPrice.'}
            elif code == -1121: # Invalid symbol
                return {'error': 'INVALID_SYMBOL', 'code': -1121, 'message': f'Símbolo inválido: {msg}'}
            
            # Fallback text matching (if code parsing failed)
            lower_msg = error_msg.lower()
            if "insufficient margin" in lower_msg:
                return {'error': f'INSUFFICIENT_MARGIN: {error_msg}'}
            elif "min_notional" in lower_msg:
                return {'error': f'MIN_NOTIONAL: {error_msg}'}
            elif "would immediately trigger" in lower_msg or "-2021" in error_msg:
                return {'error': 'ORDER_WOULD_IMMEDIATELY_TRIGGER', 'message': 'El precio de activación ya fue alcanzado. Ajusta el stopPrice.'}
            
            clean_msg = f"Binance Error {code}: {msg}" if code else f"Error: {error_msg}"
            return {'error': clean_msg}

    async def cancel_order(self, symbol: str, order_id: str) -> bool:
        """Cancel an order."""
        if not self._exchange:
            return False
            
        try:
            await self._exchange.cancel_order(order_id, symbol)
            return True
        except Exception as e:
            print(f"⚠️ BinanceAdapter: cancel_order error: {e}")
            return False

    async def get_positions(self) -> List[Dict[str, Any]]:
        """Get active positions."""
        if not self._exchange:
            return []
            
        try:
            positions = await self._exchange.fetch_positions()
            active = []
            for p in positions:
                amt = float(p.get('contracts') or 0)
                if amt != 0:
                    active.append({
                        'symbol': p.get('symbol', '').replace('/USDT:USDT', 'USDT'),
                        'side': p.get('side', '').upper() if p.get('side') else ('LONG' if float(p.get('info', {}).get('positionAmt', amt)) > 0 else 'SHORT'),
                        'quantity': abs(amt),
                        'entryPrice': float(p.get('entryPrice') or 0),
                        'unrealizedPnl': float(p.get('unrealizedPnl') or 0),
                        'leverage': int(p.get('leverage') or 1),
                        'exchange': 'BINANCE'
                    })
            return active
        except Exception as e:
            # Parse error
            err_msg = str(e)
            import re, json
            match = re.search(r'\{.*"code":.*\}', err_msg)
            if match:
                 try:
                     data = json.loads(match.group(0))
                     err_msg = f"Binance Error {data.get('code')}: {data.get('msg')}"
                 except: pass
                 
            print(f"⚠️ BinanceAdapter: get_positions error: {err_msg}")
            return []

    async def get_open_orders(self, symbol: str = None) -> List[Dict[str, Any]]:
        """Get open orders for a symbol (or all if symbol is None)."""
        if not self._exchange:
            return []
        try:
            formatted = None
            if symbol:
                formatted = symbol.replace('USDT', '/USDT:USDT') if 'USDT' in symbol and ':' not in symbol and '/' not in symbol else symbol
            
            orders = await self._exchange.fetch_open_orders(formatted)
            
            result = []
            for o in orders:
                result.append({
                    'orderId': o.get('id'),
                    'symbol': o.get('symbol', '').replace('/USDT:USDT', 'USDT'),
                    'type': o.get('type', '').upper(),
                    'side': o.get('side', '').upper(),
                    'quantity': float(o.get('amount') or 0),
                    'price': float(o.get('price') or 0),
                    'stopPrice': float(o.get('stopPrice') or o.get('triggerPrice') or 0),
                    'status': o.get('status')
                })
            return result
        except Exception as e:
            print(f"⚠️ BinanceAdapter: get_open_orders error: {e}")
            return []

    async def cancel_orders(self, symbol: str) -> bool:
        """Cancel all open orders for symbol."""
        if not self._exchange: return False
        try:
            formatted = symbol.replace('USDT', '/USDT:USDT') if 'USDT' in symbol and '/' not in symbol else symbol
            await self._exchange.cancel_all_orders(formatted)
            return True
        except Exception as e:
            print(f"⚠️ BinanceAdapter Cancel Error ({symbol}): {e}")
            return False

    async def close_position(self, symbol: str) -> bool:
        """Close specific position (Market)."""
        if not self._exchange: return False
        try:
            # 1. Get Position
            positions = await self.get_positions()
            
            # Normalize symbol for comparison (remove USDT suffix variations)
            normalized = symbol.replace('/USDT:USDT', 'USDT').replace('USDT', '')
            target_pos = next((p for p in positions if p['symbol'].replace('USDT', '') == normalized), None)
            
            if not target_pos: 
                print(f"ℹ️ BinanceAdapter: No position found for {symbol} (already closed)")
                return True # Already closed
            
            qty = target_pos['quantity']
            side = target_pos['side']
            
            if qty == 0: return True
            
            # 2. Execute Close (Opposite Side) - CCXT uses lowercase
            close_side = 'sell' if side == 'LONG' else 'buy'
            
            formatted = symbol.replace('USDT', '/USDT:USDT') if 'USDT' in symbol and '/' not in symbol else symbol
            
            print(f"🔒 BinanceAdapter: Closing {symbol} - {close_side} {qty} (reduceOnly)")
            
            # Use param 'reduceOnly': True explicitly
            await self._exchange.create_order(
                formatted, 'market', close_side, qty, params={'reduceOnly': True}
            )
            return True
        except Exception as e:
            err_str = str(e)
            # Parse Binance error code if present
            import re, json
            match = re.search(r'\{.*"code":.*\}', err_str)
            if match:
                try:
                    data = json.loads(match.group(0))
                    err_str = f"Binance Error {data.get('code')}: {data.get('msg')}"
                except: pass
            print(f"⚠️ BinanceAdapter Close Error ({symbol}): {err_str}")
            return False

    async def close(self):
        """Close connections."""
        if self._exchange:
            await self._exchange.close()
            self._exchange = None

    def supports_websocket(self) -> bool:
        return True

    async def stream_candles(
        self, 
        symbols: List[str], 
        callback: Callable[[str, dict], None]
    ):
        """Stream real-time candle updates via WebSocket."""
        from ..ws_manager import BinanceWSManager
        from ..price_cache import get_price_cache
        
        self._price_cache = get_price_cache()
        self._ws_manager = BinanceWSManager(symbols, timeframe='15m')
        
        async def on_candle(symbol: str, candle: dict):
            self._price_cache.update_candle(symbol, candle)
            await callback(symbol, candle)
        
        self._ws_manager.add_callback(on_candle)
        
        if await self._ws_manager.connect():
            await self._ws_manager.listen()
