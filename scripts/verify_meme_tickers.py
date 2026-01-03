#!/usr/bin/env python3
"""
Verify 1000PEPEUSDT and PONKEUSDT availability on Binance and Bybit
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from nexus_system.uplink.adapters.binance_adapter import BinanceAdapter
from nexus_system.uplink.adapters.bybit_adapter import BybitAdapter

async def verify_ticker_availability():
    """Verify if tickers are available on both exchanges."""

    print("🔍 Verifying 1000PEPEUSDT and PONKEUSDT availability")
    print("=" * 60)

    tickers_to_check = ['1000PEPEUSDT', 'PONKEUSDT']
    exchanges = []

    # Initialize adapters
    binance = BinanceAdapter()
    bybit = BybitAdapter()

    try:
        # Initialize Binance
        print("📡 Initializing Binance adapter...")
        binance_ok = await binance.initialize(verbose=False)
        if binance_ok:
            exchanges.append(('Binance', binance))
            print("✅ Binance adapter ready")
        else:
            print("❌ Binance adapter failed")

        # Initialize Bybit
        print("📡 Initializing Bybit adapter...")
        bybit_ok = await bybit.initialize(verbose=False)
        if bybit_ok:
            exchanges.append(('Bybit', bybit))
            print("✅ Bybit adapter ready")
        else:
            print("❌ Bybit adapter failed")

        if not exchanges:
            print("❌ No adapters available for verification")
            return False

        print("\n🔍 Checking ticker availability...")
        print("-" * 40)

        results = {}

        for ticker in tickers_to_check:
            print(f"\n🐕 Checking {ticker}:")
            results[ticker] = {}

            for exchange_name, adapter in exchanges:
                try:
                    # Try to get ticker price
                    if hasattr(adapter, 'get_market_price'):
                        price = await adapter.get_market_price(ticker)
                    elif hasattr(adapter, 'get_ticker_price'):
                        price = await adapter.get_ticker_price(ticker)
                    else:
                        print(f"  ❌ {exchange_name}: No price method available")
                        results[ticker][exchange_name] = False
                        continue
                    if price and price > 0:
                        print(f"  ✅ {exchange_name}: ${price:.6f}")
                        results[ticker][exchange_name] = True
                    else:
                        print(f"  ❌ {exchange_name}: No price data")
                        results[ticker][exchange_name] = False

                except Exception as e:
                    print(f"  ❌ {exchange_name}: Error - {str(e)[:50]}")
                    results[ticker][exchange_name] = False

                # Small delay to avoid rate limits
                await asyncio.sleep(0.1)

        # Summary
        print("\n📊 SUMMARY")
        print("=" * 60)

        all_available = True
        for ticker, exchanges_status in results.items():
            binance_ok = exchanges_status.get('Binance', False)
            bybit_ok = exchanges_status.get('Bybit', False)

            status_icon = "✅" if (binance_ok and bybit_ok) else "⚠️" if (binance_ok or bybit_ok) else "❌"

            print(f"{status_icon} {ticker}:")
            print(f"   Binance: {'✅' if binance_ok else '❌'}")
            print(f"   Bybit:   {'✅' if bybit_ok else '❌'}")

            if not (binance_ok and bybit_ok):
                all_available = False

        print("=" * 60)

        if all_available:
            print("🎉 SUCCESS: Both tickers available on Binance and Bybit!")
            print("✅ Ready to add to MEME_COINS category")
        else:
            print("⚠️  WARNING: Some tickers not available on both exchanges")
            print("🔧 Check exchange availability before adding to categories")

        return all_available

    except Exception as e:
        print(f"💥 Verification failed: {e}")
        return False

    finally:
        # Cleanup resources
        try:
            if 'bybit' in locals() and bybit._exchange:
                await bybit._exchange.close()
        except:
            pass

async def main():
    """Main verification function."""
    success = await verify_ticker_availability()
    return 0 if success else 1

if __name__ == "__main__":
    exit(asyncio.run(main()))
