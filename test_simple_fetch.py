#!/usr/bin/env python3
"""
Test simple de fetch sin timeouts complejos
"""
import time
import signal

interrupted = False

def signal_handler(signum, frame):
    global interrupted
    interrupted = True
    print("\n⚠️  Test interrumpido", flush=True)

def test_basic_binance():
    """Test básico de conexión a Binance"""
    print("🔍 Testing basic Binance connection...", flush=True)

    try:
        from binance.client import Client
        print("✅ Binance import OK", flush=True)

        # Test client creation
        print("🔧 Creating client...", end=" ", flush=True)
        start_time = time.time()
        client = Client()
        client_time = time.time() - start_time
        print(".2f")
        # Test a simple ping
        print("📡 Testing ping...", end=" ", flush=True)
        ping_start = time.time()
        result = client.ping()
        ping_time = time.time() - ping_start
        print(".2f")
        return True

    except Exception as e:
        print(f"❌ FAILED: {e}", flush=True)
        return False

def test_simple_fetch():
    """Test de fetch simple sin timeout wrapper"""
    print("🔍 Testing simple fetch...", flush=True)

    try:
        from binance.client import Client

        symbol = "BTCUSDT"
        print(f"📊 Fetching {symbol}...", flush=True)

        client = Client()
        start_time = time.time()

        # Simple fetch with small limit
        klines = client.futures_klines(
            symbol=symbol,
            interval="15m",
            limit=10  # Very small limit for quick test
        )

        fetch_time = time.time() - start_time
        print(".2f")
        print(f"   📈 Got {len(klines)} klines", flush=True)

        if klines:
            # Show first kline
            first_kline = klines[0]
            timestamp = first_kline[0]
            open_price = float(first_kline[1])
            print(f"   💰 First kline: {timestamp} -> ${open_price}", flush=True)

        return True

    except Exception as e:
        print(f"❌ FAILED: {e}", flush=True)
        return False

def main():
    signal.signal(signal.SIGINT, signal_handler)

    print("=" * 50)
    print("🧪 TEST SIMPLE FETCH")
    print("=" * 50)

    # Test 1: Basic Binance connection
    print("\nTEST 1: Conexión básica a Binance")
    if not test_basic_binance():
        print("❌ Test 1 falló - problema de conexión básica")
        return

    if interrupted:
        print("⏹️  Interrumpido por usuario")
        return

    # Test 2: Simple fetch
    print("\nTEST 2: Fetch simple de datos")
    if not test_simple_fetch():
        print("❌ Test 2 falló - problema de fetch")
        return

    print("\n" + "=" * 50)
    print("✅ TODOS LOS TESTS PASARON")
    print("🎯 La conexión a Binance funciona correctamente")
    print("💡 El problema debe estar en los timeouts complejos")
    print("=" * 50)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 Test cancelado")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
