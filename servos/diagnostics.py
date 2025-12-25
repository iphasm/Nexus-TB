import os
import sys
import requests
import traceback
from binance.client import Client

def get_asset_diagnostics(symbol: str) -> dict:
    """
    Fetch market data and calculate all signal indicators for an asset.
    Returns a dict with all indicator values.
    """
    try:
        from servos.fetcher import get_market_data
        from strategies.engine import StrategyEngine
        
        # Fetch data (needs 200+ candles for EMA200)
        df = get_market_data(symbol, timeframe='15m', limit=250)
        
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

def run_diagnostics(api_key: str = None, api_secret: str = None):
    """
    Run system diagnostics.
    
    Args:
        api_key: Optional API key (uses env var if not provided)
        api_secret: Optional API secret (uses env var if not provided)
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
    report.append(f"- API Key Present: {'✅' if used_api_key else '❌'}")
    if used_api_key:
        report.append(f"- API Key Masked: {used_api_key[:4]}...{used_api_key[-4:]}")
    report.append(f"- Secret Present: {'✅' if used_api_secret else '❌'}")
    
    # 3. IP Check (Crucial for Geo-blocking)
    report.append("\n**🌍 Network / IP Check:**")
    
    # Proxy Check
    proxy_url = os.getenv('PROXY_URL')
    proxies = {'https': proxy_url} if proxy_url else None
    
    if proxy_url:
        report.append(f"🔄 Proxy Configured: `Yes`")
    else:
        report.append(f"🔄 Proxy Configured: `No`")

    try:
        # Check Direct IP
        try:
            direct_ip = requests.get("https://api.ipify.org?format=json", timeout=5).json().get('ip', 'Unknown')
            report.append(f"- Direct IP (Server): `{direct_ip}`")
        except:
            report.append(f"- Direct IP: Failed to resolve")

        # Check Proxy IP (what Binance sees)
        ip_data = requests.get("https://api.ipify.org?format=json", proxies=proxies, timeout=10).json()
        ip_addr = ip_data.get('ip', 'Unknown')
        report.append(f"- Effective IP (Outgoing): `{ip_addr}`")
        
        # Optional: Get Geolocation attempt
        try:
            geo = requests.get(f"http://ip-api.com/json/{ip_addr}", timeout=5).json()
            country = geo.get('country', 'Unknown')
            region = geo.get('regionName', 'Unknown')
            report.append(f"- Location: {country} ({region})")
            
            if country == "United States":
                report.append("\n⚠️ **WARNING: Effective IP is in US. Binance International may block this.**")
            else:
                report.append("\n✅ **Location looks good (Not US).**")
        except:
            report.append("- Location: Could not determine")
            
    except Exception as e:
        report.append(f"❌ Failed to get IP: {str(e)}")

    # 4. Binance Public Connectivity
    report.append("\n**📡 Binance Public API (api.binance.com):**")
    try:
        request_params = {'proxies': proxies} if proxies else None
        client = Client(tld='com', requests_params=request_params)
        # Test Ping
        client.ping()
        report.append("✅ Ping: Success")
        
        # Test Data Fetch
        klines = client.get_klines(symbol='BTCUSDT', interval='15m', limit=1)
        if klines:
            report.append(f"✅ Data Fetch: Success (BTC price: {klines[0][4]})")
        else:
            report.append("❌ Data Fetch: Empty response")
            
    except Exception as e:
        report.append(f"❌ Public Connection Failed:\n`{str(e)}`")

    # 5. Binance Authenticated Connectivity
    if used_api_key and used_api_secret:
        report.append("\n**🔐 Binance Authenticated API:**")
        try:
            request_params = {'proxies': proxies} if proxies else None
            auth_client = Client(used_api_key, used_api_secret, tld='com', requests_params=request_params)
            account = auth_client.get_account()
            can_trade = account.get('canTrade', False)
            report.append(f"✅ Auth Success!")
            report.append(f"- Can Trade: {can_trade}")
            report.append(f"- Account Type: {account.get('accountType', 'Unknown')}")
            
            # Check Futures Balance specifically if that's what we use
            try:
                futures_bal = auth_client.futures_account_balance()
                usdt_bal = next((item['balance'] for item in futures_bal if item['asset'] == 'USDT'), 0)
                report.append(f"- Futures USDT Balance: {float(usdt_bal):.2f}")
            except Exception as fe:
                report.append(f"- Futures check failed: {str(fe)}")
                
        except Exception as e:
            report.append(f"❌ Auth Failed:\n`{str(e)}`")
    else:
        report.append("\n**🔐 Auth Test Skipped (No Keys)**")

    # 6. Full Asset Signal Diagnostics (BTC + TSLA)
    report.append("\n\n📊 **SIGNAL GENERATION DIAGNOSTICS**")
    report.append("━━━━━━━━━━━━━━━━━━")
    
    # Test BTC (Crypto)
    try:
        btc_data = get_asset_diagnostics("BTCUSDT")
        report.append(format_indicator_report(btc_data))
    except Exception as e:
        report.append(f"\n❌ BTC Diagnostics Error: {e}")
    
    # Test TSLA (Stock)
    try:
        tsla_data = get_asset_diagnostics("TSLA")
        report.append(format_indicator_report(tsla_data))
    except Exception as e:
        report.append(f"\n❌ TSLA Diagnostics Error: {e}")

    return "\n".join(report)

if __name__ == "__main__":
    print(run_diagnostics())


