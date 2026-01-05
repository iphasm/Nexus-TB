"""
Strategic Crypto Asset Correlation Analysis
============================================
This script analyzes correlations between crypto assets to identify:
1. Highly correlated pairs (should avoid trading both simultaneously)
2. Low-correlation assets (good for portfolio diversification)
3. Optimal asset list for ML training

Uses yfinance for historical data (6 months) to calculate correlation matrix.
"""

import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Current CRYPTO_SUBGROUPS from system_directive.py
CRYPTO_SUBGROUPS = {
    'MAJOR_CAPS': [
        "BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "XRPUSDT", "ADAUSDT",
        "AVAXUSDT", "DOTUSDT", "LINKUSDT", "TRXUSDT"
    ],
    'MEME_COINS': [
        "DOGEUSDT", "WIFUSDT", "BRETTUSDT", "MEWUSDT", "BOMEUSDT",
        "1000PEPEUSDT", "PONKEUSDT"
    ],
    'DEFI': [
        "UNIUSDT", "AAVEUSDT", "CRVUSDT", "COMPUSDT", "SNXUSDT",
        "LDOUSDT", "ENAUSDT", "DYDXUSDT", "INJUSDT"
    ],
    'AI_TECH': [
        "TAOUSDT", "WLDUSDT", "GRTUSDT", "ARKMUSDT", "TRBUSDT", "TIAUSDT"
    ],
    'GAMING_METAVERSE': [
        "AXSUSDT", "SANDUSDT", "MANAUSDT", "IMXUSDT", "GALAUSDT", "ENJUSDT",
        "ILVUSDT", "PIXELUSDT"
    ],
    'LAYER1_INFRA': [
        "SUIUSDT", "SEIUSDT", "NEARUSDT", "MATICUSDT", "APTUSDT",
        "OPUSDT", "ARBUSDT", "ATOMUSDT", "ETCUSDT", "LTCUSDT", "BCHUSDT",
        "ALGOUSDT", "VETUSDT"
    ],
}

# Mapping to Yahoo Finance tickers
YF_MAPPING = {
    'BTCUSDT': 'BTC-USD',
    'ETHUSDT': 'ETH-USD',
    'BNBUSDT': 'BNB-USD',
    'SOLUSDT': 'SOL-USD',
    'XRPUSDT': 'XRP-USD',
    'ADAUSDT': 'ADA-USD',
    'AVAXUSDT': 'AVAX-USD',
    'DOTUSDT': 'DOT-USD',
    'LINKUSDT': 'LINK-USD',
    'TRXUSDT': 'TRX-USD',
    'DOGEUSDT': 'DOGE-USD',
    'UNIUSDT': 'UNI-USD',
    'AAVEUSDT': 'AAVE-USD',
    'MATICUSDT': 'MATIC-USD',
    'ATOMUSDT': 'ATOM-USD',
    'LTCUSDT': 'LTC-USD',
    'BCHUSDT': 'BCH-USD',
    'ETCUSDT': 'ETC-USD',
    'NEARUSDT': 'NEAR-USD',
    'ALGOUSDT': 'ALGO-USD',
    'VETUSDT': 'VET-USD',
    'AXSUSDT': 'AXS-USD',
    'SANDUSDT': 'SAND-USD',
    'MANAUSDT': 'MANA-USD',
    'GALAUSDT': 'GALA-USD',
    'IMXUSDT': 'IMX-USD',
    'ENJUSDT': 'ENJ-USD',
    'GRTUSDT': 'GRT-USD',
    'CRVUSDT': 'CRV-USD',
    'COMPUSDT': 'COMP-USD',
    'SNXUSDT': 'SNX-USD',
    'APTUSDT': 'APT-USD',
    'OPUSDT': 'OP-USD',
    'ARBUSDT': 'ARB-USD',
    'SUIUSDT': 'SUI-USD',
    'SEIUSDT': 'SEI-USD',
    'INJUSDT': 'INJ-USD',
    'WLDUSDT': 'WLD-USD',
    'LDOUSDT': 'LDO-USD',
    'DYDXUSDT': 'DYDX-USD',
    # Meme coins with limited yfinance data
    'WIFUSDT': 'WIF-USD',
    '1000PEPEUSDT': 'PEPE-USD',
    'TAOUSDT': 'TAO-USD',
    'TIAUSDT': 'TIA-USD',
}


def fetch_historical_data(symbols: list, period: str = "6mo") -> pd.DataFrame:
    """Fetch historical closing prices for all symbols."""
    print(f"📥 Downloading historical data for {len(symbols)} assets...")
    
    all_data = {}
    for symbol in symbols:
        yf_symbol = YF_MAPPING.get(symbol)
        if not yf_symbol:
            continue
            
        try:
            ticker = yf.Ticker(yf_symbol)
            df = ticker.history(period=period)
            if not df.empty and len(df) > 30:
                all_data[symbol] = df['Close']
                print(f"   ✓ {symbol}: {len(df)} days")
            else:
                print(f"   ✗ {symbol}: No data")
        except Exception as e:
            print(f"   ✗ {symbol}: Error - {str(e)[:30]}")
    
    if not all_data:
        return pd.DataFrame()
    
    return pd.DataFrame(all_data)


def calculate_correlation_matrix(prices_df: pd.DataFrame) -> pd.DataFrame:
    """Calculate correlation matrix from price returns."""
    # Use log returns for better correlation analysis
    returns = np.log(prices_df / prices_df.shift(1)).dropna()
    return returns.corr()


def analyze_correlations(corr_matrix: pd.DataFrame, threshold: float = 0.85):
    """Analyze correlation matrix to find highly correlated pairs."""
    high_corr_pairs = []
    
    for i, sym1 in enumerate(corr_matrix.columns):
        for j, sym2 in enumerate(corr_matrix.columns):
            if i >= j:  # Skip diagonal and lower triangle
                continue
            corr = corr_matrix.loc[sym1, sym2]
            if abs(corr) > threshold:
                high_corr_pairs.append({
                    'pair': f"{sym1} <-> {sym2}",
                    'correlation': corr,
                    'action': 'REMOVE ONE' if corr > 0 else 'INVERSE PAIR'
                })
    
    return sorted(high_corr_pairs, key=lambda x: -abs(x['correlation']))


def identify_optimal_assets(corr_matrix: pd.DataFrame, threshold: float = 0.85) -> list:
    """
    Identify optimal assets by removing highly correlated ones.
    Strategy: Keep asset with highest average daily volume (proxy: keep alphabetically first).
    """
    # Priority list (assets to keep if there's a conflict)
    priority = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'BNBUSDT', 'XRPUSDT', 'ADAUSDT', 
                'AVAXUSDT', 'LINKUSDT', 'DOGEUSDT', 'UNIUSDT', 'MATICUSDT', 'ATOMUSDT']
    
    to_remove = set()
    
    for i, sym1 in enumerate(corr_matrix.columns):
        if sym1 in to_remove:
            continue
        for j, sym2 in enumerate(corr_matrix.columns):
            if i >= j or sym2 in to_remove:
                continue
            
            corr = corr_matrix.loc[sym1, sym2]
            if abs(corr) > threshold:
                # Keep the one with higher priority, remove the other
                if sym1 in priority and sym2 not in priority:
                    to_remove.add(sym2)
                elif sym2 in priority and sym1 not in priority:
                    to_remove.add(sym1)
                else:
                    # Both are priority or both are not - keep first in priority list
                    idx1 = priority.index(sym1) if sym1 in priority else 999
                    idx2 = priority.index(sym2) if sym2 in priority else 999
                    if idx1 <= idx2:
                        to_remove.add(sym2)
                    else:
                        to_remove.add(sym1)
    
    optimal = [s for s in corr_matrix.columns if s not in to_remove]
    return optimal, to_remove


def main():
    print("=" * 70)
    print("🔬 STRATEGIC CRYPTO ASSET CORRELATION ANALYSIS")
    print("=" * 70)
    print(f"⏰ Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print()
    
    # Collect all unique assets
    all_assets = []
    for group, assets in CRYPTO_SUBGROUPS.items():
        for asset in assets:
            if asset not in all_assets and asset in YF_MAPPING:
                all_assets.append(asset)
    
    print(f"📊 Total assets to analyze: {len(all_assets)}")
    print(f"📋 Assets with yfinance mapping: {len([a for a in all_assets if a in YF_MAPPING])}")
    print()
    
    # Fetch data
    prices_df = fetch_historical_data(all_assets, period="6mo")
    
    if prices_df.empty:
        print("❌ No data fetched. Exiting.")
        return
    
    print(f"\n✅ Data fetched for {len(prices_df.columns)} assets")
    print()
    
    # Calculate correlation matrix
    print("📈 Calculating correlation matrix...")
    corr_matrix = calculate_correlation_matrix(prices_df)
    
    # Analyze high correlations
    print("\n" + "=" * 70)
    print("🚨 HIGHLY CORRELATED PAIRS (> 0.85)")
    print("=" * 70)
    
    high_corr = analyze_correlations(corr_matrix, threshold=0.85)
    
    if high_corr:
        for pair in high_corr[:20]:  # Top 20
            print(f"   {pair['pair']:35} | Corr: {pair['correlation']:.3f}")
    else:
        print("   ✅ No highly correlated pairs found!")
    
    # Identify optimal assets
    print("\n" + "=" * 70)
    print("✂️ RECOMMENDED REMOVALS (to reduce overexposure)")
    print("=" * 70)
    
    optimal, to_remove = identify_optimal_assets(corr_matrix, threshold=0.85)
    
    if to_remove:
        print(f"\n   Assets to REMOVE ({len(to_remove)}):")
        for asset in sorted(to_remove):
            print(f"      ❌ {asset}")
    else:
        print("   ✅ No assets need to be removed!")
    
    # Final recommended list
    print("\n" + "=" * 70)
    print("✅ RECOMMENDED ASSET LIST FOR ML TRAINING")
    print("=" * 70)
    
    print(f"\n   Optimal Assets ({len(optimal)}):")
    for i, asset in enumerate(optimal, 1):
        print(f"      {i:2d}. {asset}")
    
    # Output as Python list for easy copy
    print("\n" + "=" * 70)
    print("📋 COPY-PASTE FOR train_cortex.py")
    print("=" * 70)
    print()
    print("DEFAULT_SYMBOLS = [")
    for i, asset in enumerate(optimal):
        comma = "," if i < len(optimal) - 1 else ""
        print(f"    '{asset}'{comma}")
    print("]")
    
    # Summary statistics
    print("\n" + "=" * 70)
    print("📊 SUMMARY")
    print("=" * 70)
    print(f"   Total analyzed: {len(all_assets)}")
    print(f"   With valid data: {len(prices_df.columns)}")
    print(f"   Highly correlated pairs: {len(high_corr)}")
    print(f"   Recommended removals: {len(to_remove)}")
    print(f"   Final asset count: {len(optimal)}")
    print(f"   Correlation threshold: 0.85")


if __name__ == "__main__":
    main()
