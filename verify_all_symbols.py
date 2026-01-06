#!/usr/bin/env python3
"""
Verify that ALL active symbols are included in the ML model
"""

import joblib
from system_directive import get_all_assets, ASSET_GROUPS

def main():
    # Get expected symbols from system configuration
    expected_all = set(get_all_assets())
    expected_crypto = set(ASSET_GROUPS.get('CRYPTO', []))
    expected_stocks = set(ASSET_GROUPS.get('STOCKS', []))
    expected_etfs = set(ASSET_GROUPS.get('ETFS', []))

    print(f"📊 Expected symbols from system config:")
    print(f"   Total: {len(expected_all)}")
    print(f"   Crypto: {len(expected_crypto)}")
    print(f"   Stocks: {len(expected_stocks)}")
    print(f"   ETFs: {len(expected_etfs)}")
    print()

    # Load current model
    model_path = 'nexus_system/memory_archives/ml_model.pkl'
    model_data = joblib.load(model_path)

    if isinstance(model_data, dict):
        metadata = model_data.get('metadata', {})
        model_symbols = set(metadata.get('symbols', []))

        print(f"🧠 Current ML model symbols:")
        print(f"   Total: {len(model_symbols)}")
        print(f"   Crypto: {len([s for s in model_symbols if 'USDT' in s])}")
        print(f"   Stocks: {len([s for s in model_symbols if s in ['AAPL', 'AMD', 'AMZN', 'BAC', 'GOOGL', 'JPM', 'META', 'MSFT', 'NVDA', 'TSLA']])}")
        print(f"   ETFs: {len([s for s in model_symbols if s in ['GLD', 'IWM', 'QQQ', 'SPY', 'TLT']])}")
        print()

        # Check for missing symbols
        missing_symbols = expected_all - model_symbols
        extra_symbols = model_symbols - expected_all

        if missing_symbols:
            print(f"❌ MISSING SYMBOLS ({len(missing_symbols)}):")
            for symbol in sorted(missing_symbols):
                print(f"   • {symbol}")
            print()
        else:
            print("✅ All expected symbols are included")

        if extra_symbols:
            print(f"⚠️ EXTRA SYMBOLS ({len(extra_symbols)}):")
            for symbol in sorted(extra_symbols):
                print(f"   • {symbol}")
            print()

        # Specific checks
        key_symbols = ['SOLUSDT', 'BTCUSDT', 'AAPL', 'TSLA', 'SPY', 'QQQ']
        print("🎯 Key symbols check:")
        for symbol in key_symbols:
            status = "✅" if symbol in model_symbols else "❌"
            print(f"   {status} {symbol}")
        print()

        # Summary
        total_expected = len(expected_all)
        total_model = len(model_symbols)
        match_percentage = (total_expected - len(missing_symbols)) / total_expected * 100

        print(f"📈 SUMMARY:")
        print(f"   Expected: {total_expected} symbols")
        print(f"   In model: {total_model} symbols")
        print(f"   Missing: {len(missing_symbols)} symbols")
        print(f"   Coverage: {match_percentage:.1f}%")

        if len(missing_symbols) == 0:
            print("🎉 SUCCESS: All 41 symbols are included in the ML model!")
        else:
            print(f"⚠️ WARNING: {len(missing_symbols)} symbols are missing from the model")

    else:
        print("❌ Model format error - not a dict")

if __name__ == "__main__":
    main()
