import sys
sys.path.insert(0, r'C:\Python314\Lib\site-packages')

try:
    import ccxt
    print(f"✅ CCXT Version: {ccxt.__version__}")
    # Note: ccxt.version was removed in CCXT 4.5.31

    # Check Bybit availability
    if 'bybit' in ccxt.exchanges:
        print("✅ Bybit adapter: Available")
    else:
        print("❌ Bybit adapter: Not available")

    # Check Binance availability
    if 'binance' in ccxt.exchanges:
        print("✅ Binance adapter: Available")
    else:
        print("❌ Binance adapter: Not available")

    print("\n🎉 CCXT successfully upgraded to 4.5.31!")

except ImportError as e:
    print(f"❌ Import error: {e}")
except Exception as e:
    print(f"❌ Error: {e}")
