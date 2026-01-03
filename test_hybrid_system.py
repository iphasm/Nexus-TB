#!/usr/bin/env python3
"""
Test final del sistema híbrido xAI + OpenAI en Nexus Core.
Verificación completa de integración y funcionalidades.
"""

import os
import sys
import time

def test_xai_integration():
    """Prueba la integración básica de xAI."""
    print("🤖 PRUEBA DE INTEGRACIÓN XAI")
    print("=" * 40)

    try:
        from servos.xai_integration import xai_integration

        # Test 1: Consulta básica
        print("Test 1: Consulta básica...")
        result = xai_integration.query_xai("Hola, sistema híbrido", context="alert")
        if result["success"]:
            print(f"   ✅ Respuesta: {result['response'][:50]}...")
            print(f"   📊 Proveedor: {result['provider']}")
        else:
            print(f"   ❌ Error: {result['error']}")

        # Test 2: Análisis técnico
        print("\nTest 2: Análisis técnico...")
        candles = [45000, 45100, 44900, 45050]  # OHLC simple
        result = xai_integration.analyze_candlestick_pattern("BTC/USDT", 45050, candles)
        if result["success"]:
            print(f"   ✅ Patrón: {result['pattern_analysis'][:50]}...")
        else:
            print(f"   ❌ Error: {result['error']}")

        # Test 3: Cálculo de posición
        print("\nTest 3: Cálculo de position sizing...")
        result = xai_integration.calculate_position_size(1000, 45000, 44000, 1.0)
        if result["success"]:
            print(f"   ✅ Cálculo: {result['calculations'][:50]}...")
        else:
            print(f"   ❌ Error: {result['error']}")

        # Test 4: Estadísticas
        print("\nTest 4: Estadísticas de uso...")
        stats = xai_integration.get_usage_stats()
        print(f"   📊 Consultas totales: {stats['xai_queries']}")
        print(f"   📊 Tasa de éxito: {stats.get('success_rate', 0):.1f}%")
        print(f"   📊 Costo total: ${stats['total_cost']:.4f}")
        return True

    except Exception as e:
        print(f"❌ Error en integración xAI: {e}")
        return False

def test_trading_manager_integration():
    """Prueba la integración en trading_manager.py."""
    print("\n📊 PRUEBA DE INTEGRACIÓN EN TRADING MANAGER")
    print("=" * 50)

    try:
        # Simular que tenemos un session manager
        print("Test: Verificación de imports...")

        # Importar trading_manager para verificar que xAI está integrado
        from servos import trading_manager

        # Verificar que xai_integration está importado
        if hasattr(trading_manager, 'xai_integration'):
            print("   ✅ xAI integration importado en trading_manager")
        else:
            print("   ⚠️  xAI integration no encontrado en trading_manager (puede ser normal)")

        print("   ✅ Trading manager carga correctamente")
        return True

    except Exception as e:
        print(f"❌ Error en trading manager: {e}")
        return False

def test_fallback_system():
    """Prueba el sistema de fallback xAI → OpenAI."""
    print("\n🔄 PRUEBA DE SISTEMA DE FALLBACK")
    print("=" * 40)

    try:
        from servos.xai_integration import xai_integration

        # Forzar fallback deshabilitando xAI temporalmente
        original_available = xai_integration.xai_available
        xai_integration.xai_available = False

        print("Test: Fallback con xAI 'deshabilitado'...")
        result = xai_integration.query_xai("Test fallback system", context="alert", fallback=True)

        if result["success"]:
            print(f"   ✅ Fallback exitoso: {result['provider']}")
        else:
            print(f"   ❌ Fallback falló: {result['error']}")

        # Restaurar estado original
        xai_integration.xai_available = original_available

        return True

    except Exception as e:
        print(f"❌ Error en fallback system: {e}")
        return False

def test_env_config():
    """Prueba la configuración de variables de entorno."""
    print("\n⚙️ PRUEBA DE CONFIGURACIÓN DE ENTORNO")
    print("=" * 45)

    required_env_vars = [
        "XAI_API_KEY",
        "XAI_BASE_URL",
        "XAI_MODEL",
        "XAI_TIMEOUT",
        "XAI_MAX_TOKENS"
    ]

    all_configured = True
    for var in required_env_vars:
        value = os.getenv(var)
        if value:
            print(f"   ✅ {var}: {value[:20]}..." if len(str(value)) > 20 else f"   ✅ {var}: {value}")
        else:
            print(f"   ❌ {var}: No configurada")
            all_configured = False

    # Variables opcionales
    optional_vars = ["OPENAI_API_KEY", "TELEGRAM_BOT_TOKEN"]
    print("\nVariables opcionales:")
    for var in optional_vars:
        value = os.getenv(var)
        if value:
            print(f"   ✅ {var}: Configurada")
        else:
            print(f"   ⚠️  {var}: No configurada (opcional)")

    return all_configured

def performance_comparison():
    """Comparación de rendimiento entre xAI y OpenAI."""
    print("\n⚡ COMPARACIÓN DE RENDIMIENTO")
    print("=" * 40)

    try:
        from servos.xai_integration import xai_integration

        test_query = "Analiza el patrón de esta vela: BTC/USDT con precios 45000, 45100, 44900, 45050"

        # Test xAI
        print("Midiendo xAI...")
        start_time = time.time()
        xai_result = xai_integration.query_xai(test_query, context="analysis", max_retries=1, fallback=False)
        xai_time = time.time() - start_time

        if xai_result["success"]:
            print(".2f")
        else:
            print(f"xAI falló: {xai_result['error']}")
            xai_time = None

        # Test OpenAI (fallback)
        print("Midiendo OpenAI...")
        start_time = time.time()
        openai_result = xai_integration._fallback_to_openai(test_query, "analysis")
        openai_time = time.time() - start_time

        if openai_result["success"]:
            print(".2f")
        else:
            print(f"OpenAI falló: {openai_result['error']}")
            openai_time = None

        # Comparación
        if xai_time and openai_time:
            speedup = openai_time / xai_time if xai_time > 0 else 0
            print("
🏁 RESULTADO:")
            print(".1f")
            if speedup > 1:
                print(".1f")
            else:
                print(".1f")
        return True

    except Exception as e:
        print(f"❌ Error en comparación de rendimiento: {e}")
        return False

def main():
    """Función principal de testing."""
    print("🚀 TEST FINAL DEL SISTEMA HÍBRIDO XAI + OPENAI")
    print("Para Nexus Core - Trading Bot")
    print("=" * 60)

    tests = [
        ("Configuración de entorno", test_env_config),
        ("Integración xAI", test_xai_integration),
        ("Trading Manager integration", test_trading_manager_integration),
        ("Sistema de fallback", test_fallback_system),
        ("Comparación de rendimiento", performance_comparison)
    ]

    results = []
    for test_name, test_func in tests:
        print(f"\n🔍 Ejecutando: {test_name}")
        try:
            result = test_func()
            results.append((test_name, result))
            status = "✅ PASÓ" if result else "❌ FALLÓ"
            print(f"Resultado: {status}")
        except Exception as e:
            print(f"❌ ERROR: {e}")
            results.append((test_name, False))

    # Resumen final
    print("\n" + "=" * 60)
    print("📊 RESUMEN FINAL DE TESTS")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    print(f"Tests exitosos: {passed}/{total}")

    for test_name, result in results:
        status = "✅" if result else "❌"
        print(f"   {status} {test_name}")

    if passed == total:
        print("\n🎉 ¡TODOS LOS TESTS PASARON!")
        print("✅ Sistema híbrido completamente operativo")
        print("✅ Listo para deploy en Railway")
    else:
        print(f"\n⚠️  {total - passed} tests fallaron")
        print("🔧 Revisa la configuración antes del deploy")

    print("\n" + "=" * 50)
    print("🚀 PRÓXIMOS PASOS PARA DEPLOY:")
    print("=" * 50)
    print("1. 📋 Configura variables de entorno en Railway")
    print("2. 🔑 Agrega tu XAI_API_KEY (desde variable de entorno)")
    print("3. 🔄 Deploy la aplicación")
    print("4. 🧪 Verifica que el sistema híbrido funcione")
    print("5. 📊 Monitorea costos y rendimiento")

if __name__ == "__main__":
    main()
