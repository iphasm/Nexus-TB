"""
Nexus Trading Bot - Async System Diagnostics
Migrated from synchronous requests to async aiohttp.
"""
import os
import sys
import aiohttp
import traceback
from typing import Optional
from binance.client import Client  # Keep for now, can be migrated to CCXT later

# Import config constants
try:
    from system_directive import (
        IPIFY_URL,
        IP_GEO_URL,
        DIAG_SYMBOL_CRYPTO,
        DIAG_SYMBOL_STOCK,
        DIAG_TIMEFRAME,
        DIAG_CANDLE_LIMIT,
        DIAG_CANDLE_LIMIT_SHORT,
        HTTP_TIMEOUT_SHORT,
        HTTP_TIMEOUT
    )
except ImportError:
    # Fallbacks
    IPIFY_URL = "https://api.ipify.org?format=json"
    IP_GEO_URL = "http://ip-api.com/json/{ip_addr}"
    DIAG_SYMBOL_CRYPTO = "BTCUSDT"
    DIAG_SYMBOL_STOCK = "TSLA"
    DIAG_TIMEFRAME = "15m"
    DIAG_CANDLE_LIMIT = 250
    DIAG_CANDLE_LIMIT_SHORT = 1
    HTTP_TIMEOUT_SHORT = 5
    HTTP_TIMEOUT = 10

async def get_asset_diagnostics(symbol: str) -> dict:
    """
    Fetch market data and calculate all signal indicators for an asset.
    Returns a dict with all indicator values.
    """
    try:
        from nexus_system.utils.market_data import get_market_data_async
        from strategies.engine import StrategyEngine
        
        # Obtener datos de forma async (necesita 200+ velas para EMA200)
        df = await get_market_data_async(symbol, timeframe=DIAG_TIMEFRAME, limit=DIAG_CANDLE_LIMIT)
        
        if df.empty or len(df) < 100:
            return {"error": f"Datos insuficientes para {symbol}", "symbol": symbol}
        
        # Run full strategy analysis
        engine = StrategyEngine(df)
        result = engine.analyze()
        
        # Get current values from the dataframe after calculate_indicators
        curr = engine.df.iloc[-1]
        
        return {
            "symbol": symbol,
            "price": float(curr['close']),
            "rsi": float(curr['rsi']) if 'rsi' in curr else 0,
            "adx": float(curr['adx']) if 'adx' in curr else 0,
            "bb_upper": float(curr['bb_upper']) if 'bb_upper' in curr else 0,
            "bb_lower": float(curr['bb_lower']) if 'bb_lower' in curr else 0,
            "hma_55": float(curr['hma_55']) if 'hma_55' in curr else 0,
            "kc_upper": float(curr['kc_upper']) if 'kc_upper' in curr else 0,
            "kc_lower": float(curr['kc_lower']) if 'kc_lower' in curr else 0,
            "stoch_k": float(curr['stoch_k']) if 'stoch_k' in curr else 0,
            "stoch_d": float(curr['stoch_d']) if 'stoch_d' in curr else 0,
            "atr": float(curr['atr']) if 'atr' in curr else 0,
            "ema_200": float(curr['ema_200']) if 'ema_200' in curr else 0,
            "volume": float(curr['volume']) if 'volume' in curr else 0,
            "vol_sma": float(curr['vol_sma']) if 'vol_sma' in curr else 0,
            "squeeze_on": result.get('metrics', {}).get('squeeze_on', False),
            "signal": result.get('signal_futures', 'N/A'),
            "reason": result.get('reason_futures', 'N/A'),
            "error": None
        }
    except Exception as e:
        return {"error": str(e), "symbol": symbol}

def format_indicator_report(data: dict) -> str:
    """Format asset indicators into readable report."""
    if data.get("error"):
        return f"❌ {data.get('symbol', 'N/A')}: {data['error']}"
    
    price = data.get('price', 0)
    rsi = data.get('rsi', 0)
    adx = data.get('adx', 0)
    squeeze = "🔴 ACTIVO" if data.get('squeeze_on') else "⚪ NO"
    signal = data.get('signal', 'N/A')
    
    # Signal icon
    sig_icon = "🟡"
    if signal == "BUY": sig_icon = "🟢"
    elif signal == "SHORT": sig_icon = "🔴"
    elif "CLOSE" in signal: sig_icon = "🟠"
    
    # RSI condition
    rsi_icon = "🟡" 
    if rsi > 70: rsi_icon = "🔴 (Sobrecompra)"
    elif rsi < 30: rsi_icon = "🟢 (Sobreventa)"
    elif rsi > 50: rsi_icon = "🟢"
    elif rsi < 50: rsi_icon = "🔴"
    
    # ADX interpretation
    adx_strength = "Débil" if adx < 20 else "Moderado" if adx < 40 else "Fuerte"
    
    return f"""
**{data.get('symbol', 'N/A')}**
• Precio: `${price:,.2f}`
• RSI (14): `{rsi:.1f}` {rsi_icon}
• ADX (14): `{adx:.1f}` ({adx_strength})
• Bollinger Bands: `{data.get('bb_lower', 0):,.2f}` - `{data.get('bb_upper', 0):,.2f}`
• Keltner Channels: `{data.get('kc_lower', 0):,.2f}` - `{data.get('kc_upper', 0):,.2f}`
• HMA (55): `{data.get('hma_55', 0):,.2f}`
• EMA (200): `{data.get('ema_200', 0):,.2f}`
• StochRSI K/D: `{data.get('stoch_k', 0):.1f}` / `{data.get('stoch_d', 0):.1f}`
• ATR (14): `{data.get('atr', 0):.4f}`
• Volume/SMA: `{data.get('volume', 0):,.0f}` / `{data.get('vol_sma', 0):,.0f}`
• Squeeze: {squeeze}
• **Señal**: {sig_icon} `{signal}`
• Razón: _{data.get('reason', 'N/A')}_"""

async def run_diagnostics(
    api_key: Optional[str] = None, 
    api_secret: Optional[str] = None, 
    proxy_url: Optional[str] = None,
    session: Optional[aiohttp.ClientSession] = None
) -> str:
    """
    Async system diagnostics using aiohttp.
    
    Args:
        api_key: Optional API key
        api_secret: Optional API secret
        proxy_url: Optional Proxy URL (overrides env)
        session: Optional aiohttp session (creates new if not provided)
    
    Returns:
        Diagnostic report as string
    """
    report = ["🔍 **SYSTEM DIAGNOSTICS REPORT** 🔍\n"]
    
    # 1. System Info
    report.append(f"**Python Version:** {sys.version.split()[0]}")
    report.append(f"**Platform:** {sys.platform}")
    
    # 2. Credentials - Use provided or fallback to env
    used_api_key = api_key or os.getenv('BINANCE_API_KEY')
    used_api_secret = api_secret or os.getenv('BINANCE_SECRET')
    
    # Indicate source of credentials
    cred_source = "Session" if api_key else "Environment"
    
    report.append(f"\n**🔑 Credentials Check ({cred_source}):**")
    report.append(f"- Binance Key Present: {'✅' if used_api_key else '❌'}")
    if used_api_key:
        report.append(f"- Binance Key Masked: {used_api_key[:4]}...{used_api_key[-4:]}")
    
    # Bybit Keys
    bybit_key = os.getenv('BYBIT_API_KEY')
    bybit_secret = os.getenv('BYBIT_API_SECRET')
    report.append(f"- Bybit Key Present: {'✅' if bybit_key else '❌'}")
    if bybit_key:
        report.append(f"- Bybit Key Masked: {bybit_key[:4]}...{bybit_key[-4:]}")
    
    # 3. IP Check (Crucial for Geo-blocking) - Async
    report.append("\n**🌍 Network / IP Check:**")
    
    # Proxy Check
    proxy_url = proxy_url or os.getenv('PROXY_URL')
    
    if proxy_url:
        report.append(f"🔄 Proxy Configured: `Yes`")
    else:
        report.append(f"🔄 Proxy Configured: `No`")

    # Use provided session or create new one
    should_close = session is None
    if session is None:
        connector = aiohttp.TCPConnector()
        timeout = aiohttp.ClientTimeout(total=HTTP_TIMEOUT)
        session = aiohttp.ClientSession(connector=connector, timeout=timeout)

    try:
        # Check Direct IP (async)
        try:
            async with session.get(IPIFY_URL) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    direct_ip = data.get('ip', 'Unknown')
                    report.append(f"- Direct IP (Server): `{direct_ip}`")
                else:
                    report.append(f"- Direct IP: Failed (HTTP {resp.status})")
        except Exception as e:
            report.append(f"- Direct IP: Failed to resolve ({str(e)})")

        # Check Proxy IP (what Binance sees) - async
        try:
            # Use proxy if configured
            proxy = proxy_url if proxy_url else None
            async with session.get(IPIFY_URL, proxy=proxy) as resp:
                if resp.status == 200:
                    ip_data = await resp.json()
                    ip_addr = ip_data.get('ip', 'Unknown')
                    report.append(f"- Effective IP (Outgoing): `{ip_addr}`")
                    
                    # Optional: Get Geolocation attempt (async)
                    try:
                        geo_url = IP_GEO_URL.format(ip_addr=ip_addr)
                        async with session.get(geo_url, timeout=aiohttp.ClientTimeout(total=HTTP_TIMEOUT_SHORT)) as geo_resp:
                            if geo_resp.status == 200:
                                geo = await geo_resp.json()
                                country = geo.get('country', 'Unknown')
                                region = geo.get('regionName', 'Unknown')
                                report.append(f"- Location: {country} ({region})")
                                
                                if country == "United States":
                                    report.append("\n⚠️ **WARNING: Effective IP is in US. Binance International may block this.**")
                                else:
                                    report.append("\n✅ **Location looks good (Not US).**")
                            else:
                                report.append("- Location: Could not determine (HTTP error)")
                    except Exception as geo_e:
                        report.append(f"- Location: Could not determine ({str(geo_e)})")
                else:
                    report.append(f"- Effective IP: Failed (HTTP {resp.status})")
        except Exception as e:
            report.append(f"❌ Failed to get IP: {str(e)}")
            
    except Exception as e:
        report.append(f"❌ Network Diagnosis Error: {str(e)}")

    # 4. Binance Public Connectivity
    report.append("\n**📡 Binance Public API (api.binance.com):**")
    try:
        # Format proxy for python-binance Client
        request_params = None
        if proxy_url:
            request_params = {'proxies': {'http': proxy_url, 'https': proxy_url}}
        client = Client(tld='com', requests_params=request_params)
        # Test Ping
        client.ping()
        report.append("✅ Ping: Success")
        
        # Test Data Fetch
        klines = client.get_klines(symbol=DIAG_SYMBOL_CRYPTO, interval=DIAG_TIMEFRAME, limit=DIAG_CANDLE_LIMIT_SHORT)
        if klines:
            report.append(f"✅ Data Fetch: Success (BTC price: {klines[0][4]})")
        else:
            report.append("❌ Data Fetch: Empty response")
            
    except Exception as e:
        report.append(f"❌ Binance Public Connection Failed:\n`{str(e)}`")

    # 4b. Bybit Public Connectivity
    report.append("\n**📡 Bybit Public API (v5):**")
    try:
        from nexus_system.uplink.adapters.bybit_adapter import BybitAdapter
        bybit_temp = BybitAdapter()
        if await bybit_temp.initialize():
            df = await bybit_temp.fetch_candles("BTCUSDT", limit=1)
            if not df.empty:
                report.append(f"✅ Data Fetch: Success (BTC price: {df['close'].iloc[-1]})")
            else:
                report.append("❌ Data Fetch: Empty response")
            await bybit_temp.close()
        else:
            report.append("❌ Bybit initialization failed")
    except Exception as e:
        report.append(f"❌ Bybit Connection Failed: {e}")

    # 5. Binance Authenticated Connectivity
    if used_api_key and used_api_secret:
        report.append("\n**🔐 Binance Authenticated API:**")
        try:
            # Format proxy for python-binance Client
            request_params = None
            if proxy_url:
                request_params = {'proxies': {'http': proxy_url, 'https': proxy_url}}
            auth_client = Client(used_api_key, used_api_secret, tld='com', requests_params=request_params)
            account = auth_client.get_account()
            can_trade = account.get('canTrade', False)
            report.append(f"✅ Auth Success!")
            report.append(f"- Can Trade: {can_trade}")
            report.append(f"- Account Type: {account.get('accountType', 'Unknown')}")
            
            # Check Futures Balance specifically if that's what we use
            try:
                futures_bal = auth_client.futures_account_balance()
                usdt_bal = next((item['balance'] for item in futures_bal if item.get('asset') == 'USDT'), 0)
                report.append(f"- Futures USDT Balance: {float(usdt_bal):.2f}")
            except Exception as fe:
                report.append(f"- Futures check failed: {str(fe)}")
                
        except Exception as e:
            report.append(f"❌ Binance Auth Failed:\n`{str(e)}`")
    else:
        report.append("\n**🔐 Binance Auth Test Skipped (No Keys)**")

    # 5b. Bybit Authenticated Connectivity
    if bybit_key and bybit_secret:
        report.append("\n**🔐 Bybit Authenticated API:**")
        try:
            from nexus_system.uplink.adapters.bybit_adapter import BybitAdapter
            bybit_auth = BybitAdapter(api_key=bybit_key, api_secret=bybit_secret)
            if await bybit_auth.initialize():
                balance = await bybit_auth.get_account_balance()
                report.append(f"✅ Auth Success!")
                report.append(f"- Total Balance: ${balance.get('total', 0):,.2f} USDT")
                report.append(f"- Available: ${balance.get('available', 0):,.2f} USDT")
                await bybit_auth.close()
            else:
                report.append("❌ Bybit Auth Initialization Failed")
        except Exception as e:
            report.append(f"❌ Bybit Auth Failed: {e}")
    else:
        report.append("\n**🔐 Bybit Auth Test Skipped (No Keys)**")


    # 6. Full Asset Signal Diagnostics (BTC + TSLA)
    report.append("\n\n📊 **SIGNAL GENERATION DIAGNOSTICS**")
    report.append("━━━━━━━━━━━━━━━━━━")
    
    # Test BTC (Crypto) - Async
    try:
        btc_data = await get_asset_diagnostics(DIAG_SYMBOL_CRYPTO)
        report.append(format_indicator_report(btc_data))
    except Exception as e:
        report.append(f"\n❌ BTC Diagnostics Error: {e}")
    
    # Test TSLA (Stock) - Async
    try:
        tsla_data = await get_asset_diagnostics(DIAG_SYMBOL_STOCK)
        report.append(format_indicator_report(tsla_data))
    except Exception as e:
        report.append(f"\n❌ TSLA Diagnostics Error: {e}")

    finally:
        # Close session if we created it
        if should_close and session:
            await session.close()

    return "\n".join(report)


# Backward compatibility: Sync wrapper (deprecated, use async version)
def run_diagnostics_sync(api_key: str = None, api_secret: str = None, proxy_url: str = None):
    """
    DEPRECATED: Synchronous wrapper for backward compatibility.
    Use run_diagnostics() async version instead.
    """
    import asyncio
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If loop is running, this shouldn't be called
            raise RuntimeError("Cannot run sync wrapper in async context. Use async run_diagnostics() instead.")
        else:
            return loop.run_until_complete(run_diagnostics(api_key, api_secret, proxy_url))
    except RuntimeError:
        # No event loop, create new one
        return asyncio.run(run_diagnostics(api_key, api_secret, proxy_url))

if __name__ == "__main__":
    print(run_diagnostics())


