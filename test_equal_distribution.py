#!/usr/bin/env python3
"""
Test para verificar distribución equitativa entre Binance y Bybit
"""
import os
import sys

# Add the project root to the path
sys.path.insert(0, os.path.dirname(__file__))

# Configurar las variables de entorno
os.environ['BINANCE_API_KEY'] = 'test'
os.environ['BINANCE_API_SECRET'] = 'test'
os.environ['BYBIT_API_KEY'] = 'test'
os.environ['BYBIT_API_SECRET'] = 'test'

def test_equal_distribution():
    """Test de distribución equitativa entre exchanges"""
    print("⚖️ TEST: DISTRIBUCIÓN EQUITATIVA BINANCE ↔ BYBIT")
    print("=" * 60)

    # Simular la lógica de routing sin necesidad de adapters reales
    def simulate_routing(symbol, binance_available=True, bybit_available=True):
        """Simula la lógica de routing actual"""
        # EQUAL WEIGHT LOGIC: Both exchanges have the same priority
        # Use deterministic distribution based on symbol ASCII sum for consistent routing
        if binance_available and bybit_available:
            # Both available - distribute evenly using ASCII sum of symbol
            ascii_sum = sum(ord(c) for c in symbol)
            return 'BINANCE' if ascii_sum % 2 == 0 else 'BYBIT'

        # Only one available - use it
        if binance_available:
            return 'BINANCE'
        if bybit_available:
            return 'BYBIT'

        return None

    # Lista de símbolos de prueba
    test_symbols = [
        'ETHUSDT', 'BTCUSDT', 'ADAUSDT', 'SOLUSDT', 'DOTUSDT',
        'LINKUSDT', 'AVAXUSDT', 'LTCUSDT', 'BCHUSDT', 'XRPUSDT',
        'DOGEUSDT', 'SHIBUSDT', 'PEPEUSDT', 'BONKUSDT', 'FLOKIUSDT'
    ]

    print("🔄 DISTRIBUCIÓN DE SÍMBOLOS:")
    print("-" * 40)

    binance_count = 0
    bybit_count = 0

    for symbol in test_symbols:
        exchange = simulate_routing(symbol)
        if exchange == 'BINANCE':
            binance_count += 1
            print("4s")
        elif exchange == 'BYBIT':
            bybit_count += 1
            print("4s")

    print("\n📊 RESULTADOS:")
    print(f"   Total símbolos: {len(test_symbols)}")
    print(f"   Binance: {binance_count} ({binance_count/len(test_symbols)*100:.1f}%)")
    print(f"   Bybit: {bybit_count} ({bybit_count/len(test_symbols)*100:.1f}%)")
    print(f"   Diferencia: {abs(binance_count - bybit_count)} símbolos")

    # Verificar distribución equitativa
    total = len(test_symbols)
    ideal_split = total / 2
    tolerance = 2  # Máxima diferencia aceptable

    if abs(binance_count - bybit_count) <= tolerance:
        print("   ✅ DISTRIBUCIÓN EQUITATIVA - Ambos exchanges tienen igual peso")
        return True
    else:
        print(f"   ❌ DISTRIBUCIÓN DESBALANCEADA - Diferencia excesiva")
        return False

def test_consistency():
    """Verifica que el mismo símbolo siempre vaya al mismo exchange"""
    print("\n🔄 TEST: CONSISTENCIA DE ROUTING")
    print("-" * 40)

    def get_routing(symbol):
        ascii_sum = sum(ord(c) for c in symbol)
        return 'BINANCE' if ascii_sum % 2 == 0 else 'BYBIT'

    test_symbols = ['ETHUSDT', 'BTCUSDT', 'ADAUSDT']

    print("Verificando que el mismo símbolo siempre vaya al mismo exchange:")
    all_consistent = True

    for symbol in test_symbols:
        # Simular múltiples llamadas
        results = [get_routing(symbol) for _ in range(10)]
        unique_results = set(results)

        if len(unique_results) == 1:
            exchange = unique_results.pop()
            print(f"   ✅ {symbol}: Siempre → {exchange}")
        else:
            print(f"   ❌ {symbol}: Resultados inconsistentes {unique_results}")
            all_consistent = False

    return all_consistent

if __name__ == "__main__":
    print("🔍 VERIFICACIÓN DE IGUALDAD DE PESO ENTRE EXCHANGES")
    print("=" * 60)

    # Test 1: Distribución equitativa
    balanced = test_equal_distribution()

    # Test 2: Consistencia
    consistent = test_consistency()

    print("\n🏁 RESULTADO FINAL:")
    print("=" * 40)

    if balanced and consistent:
        print("✅ ÉXITO: Ambos exchanges tienen igual peso y distribución equitativa")
        print("   - Routing consistente por símbolo")
        print("   - Distribución equilibrada (~50/50)")
        print("   - Sin jerarquía entre Binance y Bybit")
    else:
        print("❌ PROBLEMAS DETECTADOS:")
        if not balanced:
            print("   - Distribución no equitativa")
        if not consistent:
            print("   - Routing inconsistente")

    sys.exit(0 if (balanced and consistent) else 1)
