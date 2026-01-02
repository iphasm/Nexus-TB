#!/usr/bin/env python3
"""
VERIFICACIÓN COMPLETA DE INTEGRACIÓN - NEXUS TRADING BOT
Prueba la consistencia lógica entre todos los componentes del sistema.
"""

import asyncio
import sys
import os
from typing import Dict, Any, List
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from system_directive import (
    ASSET_GROUPS, CRYPTO_SUBGROUPS, GROUP_CONFIG,
    get_crypto_assets, get_bybit_corrected_ticker, BYBIT_TICKER_MAPPING
)

class IntegrationVerifier:
    """Verificador completo de integración del sistema Nexus."""

    def __init__(self):
        self.results = {
            'data_fetcher': False,
            'adapters': False,
            'strategies': False,
            'trading_manager': False,
            'pilot_mode': False,
            'integration': False
        }
        self.errors = []

    async def verify_data_fetcher(self) -> bool:
        """Verificar que el data fetcher funciona correctamente."""
        print("🔍 Verificando Data Fetcher...")

        try:
            from nexus_system.utils.market_data import get_market_data_async, calculate_atr_async

            # Probar obtención de datos
            df = await get_market_data_async('BTCUSDT', '1h', 10)
            if df.empty:
                self.errors.append("❌ Data Fetcher: No se pudieron obtener datos de BTCUSDT")
                return False

            # Verificar columnas necesarias
            required_cols = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
            for col in required_cols:
                if col not in df.columns:
                    self.errors.append(f"❌ Data Fetcher: Falta columna {col}")
                    return False

            # Probar cálculo de ATR
            atr = await calculate_atr_async(df)
            if atr <= 0:
                self.errors.append("❌ Data Fetcher: ATR calculado es inválido")
                return False

            print("✅ Data Fetcher: OK")
            return True

        except Exception as e:
            self.errors.append(f"❌ Data Fetcher Error: {e}")
            return False

    async def verify_adapters(self) -> bool:
        """Verificar que los adapters de exchange funcionan."""
        print("🔍 Verificando Adapters de Exchange...")

        try:
            # Verificar Binance Adapter
            from nexus_system.uplink.adapters.binance_adapter import BinanceAdapter
            binance_adapter = BinanceAdapter()
            binance_ok = await binance_adapter.initialize()

            if binance_ok:
                # Probar obtención de balance (sin credenciales debería fallar gracefully)
                try:
                    balance = await binance_adapter.get_account_balance()
                    # Si llega aquí sin error, las credenciales están configuradas
                    print("✅ Binance Adapter: OK (con credenciales)")
                except Exception as e:
                    if "api key" in str(e).lower() or "credentials" in str(e).lower():
                        print("✅ Binance Adapter: OK (sin credenciales)")
                    else:
                        self.errors.append(f"❌ Binance Adapter Error: {e}")
                        return False
            else:
                self.errors.append("❌ Binance Adapter: Falló inicialización")
                return False

            # Verificar Bybit Adapter
            from nexus_system.uplink.adapters.bybit_adapter import BybitAdapter
            bybit_adapter = BybitAdapter()
            bybit_ok = await bybit_adapter.initialize()

            if bybit_ok:
                # Probar obtención de balance
                try:
                    balance = await bybit_adapter.get_account_balance()
                    print("✅ Bybit Adapter: OK (con credenciales)")
                except Exception as e:
                    if "api key" in str(e).lower() or "credentials" in str(e).lower():
                        print("✅ Bybit Adapter: OK (sin credenciales)")
                    else:
                        self.errors.append(f"❌ Bybit Adapter Error: {e}")
                        return False
            else:
                self.errors.append("❌ Bybit Adapter: Falló inicialización")
                return False

            # Verificar Alpaca Adapter
            from nexus_system.uplink.adapters.alpaca_adapter import AlpacaAdapter
            alpaca_adapter = AlpacaAdapter()
            alpaca_ok = await alpaca_adapter.initialize()

            if alpaca_ok:
                try:
                    balance = await alpaca_adapter.get_account_balance()
                    print("✅ Alpaca Adapter: OK (con credenciales)")
                except Exception as e:
                    if "api key" in str(e).lower() or "credentials" in str(e).lower():
                        print("✅ Alpaca Adapter: OK (sin credenciales)")
                    else:
                        self.errors.append(f"❌ Alpaca Adapter Error: {e}")
                        return False
            else:
                self.errors.append("❌ Alpaca Adapter: Falló inicialización")
                return False

            print("✅ Adapters: OK")
            return True

        except Exception as e:
            self.errors.append(f"❌ Adapters Error: {e}")
            return False

    async def verify_strategies(self) -> bool:
        """Verificar que las estrategias funcionan correctamente."""
        print("🔍 Verificando Estrategias...")

        try:
            from nexus_system.cortex.factory import StrategyFactory
            from nexus_system.utils.market_data import get_market_data_async

            # Obtener datos de prueba
            df = await get_market_data_async('BTCUSDT', '1h', 50)
            if df.empty:
                self.errors.append("❌ Strategies: No hay datos para probar estrategias")
                return False

            market_data = {'dataframe': df}

            # Probar Mean Reversion Strategy
            strategy = StrategyFactory.get_strategy('BTCUSDT', market_data)
            if strategy is None:
                self.errors.append("❌ Strategies: No se pudo obtener estrategia")
                return False

            # Probar análisis
            signal = await strategy.analyze(market_data)
            if signal is None:
                self.errors.append("❌ Strategies: La estrategia no generó señal")
                return False

            # Verificar estructura de señal
            required_attrs = ['symbol', 'action', 'confidence', 'price']
            for attr in required_attrs:
                if not hasattr(signal, attr):
                    self.errors.append(f"❌ Strategies: Señal falta atributo {attr}")
                    return False

            print(f"✅ Estrategias: OK (Generó señal: {signal.action})")
            return True

        except Exception as e:
            self.errors.append(f"❌ Strategies Error: {e}")
            return False

    async def verify_trading_manager(self) -> bool:
        """Verificar que el trading manager funciona correctamente."""
        print("🔍 Verificando Trading Manager...")

        try:
            from servos.trading_manager import NexusTradingSession
            from nexus_system.core.shadow_wallet import ShadowWallet
            from nexus_system.core.nexus_bridge import NexusBridge

            # Crear componentes necesarios
            shadow_wallet = ShadowWallet()
            bridge = NexusBridge(shadow_wallet)

            # Crear sesión de trading (sin credenciales reales)
            session = NexusTradingSession(
                user_id="test_user",
                bridge=bridge,
                shadow_wallet=shadow_wallet
            )

            # Verificar que se inicializa correctamente
            if session.mode not in ['WATCHER', 'COPILOT', 'PILOT']:
                self.errors.append("❌ Trading Manager: Modo inicial inválido")
                return False

            # Verificar cambio de modo
            if not session.set_mode('PILOT'):
                self.errors.append("❌ Trading Manager: No puede cambiar a modo PILOT")
                return False

            if session.mode != 'PILOT':
                self.errors.append("❌ Trading Manager: Modo PILOT no se aplicó")
                return False

            # Verificar configuración de exchanges
            configured = session.get_configured_exchanges()
            if not isinstance(configured, dict):
                self.errors.append("❌ Trading Manager: get_configured_exchanges no retorna dict")
                return False

            print("✅ Trading Manager: OK")
            return True

        except Exception as e:
            self.errors.append(f"❌ Trading Manager Error: {e}")
            return False

    async def verify_pilot_mode(self) -> bool:
        """Verificar que el modo pilot funciona correctamente."""
        print("🔍 Verificando Modo PILOT...")

        try:
            from servos.trading_manager import NexusTradingSession
            from nexus_system.core.shadow_wallet import ShadowWallet
            from nexus_system.core.nexus_bridge import NexusBridge

            # Crear componentes
            shadow_wallet = ShadowWallet()
            bridge = NexusBridge(shadow_wallet)
            session = NexusTradingSession(
                user_id="test_user",
                bridge=bridge,
                shadow_wallet=shadow_wallet
            )

            # Configurar modo PILOT
            session.set_mode('PILOT')

            # Verificar que el modo está configurado correctamente
            if session.mode != 'PILOT':
                self.errors.append("❌ Pilot Mode: Modo no configurado correctamente")
                return False

            # Verificar configuración del circuit breaker
            config = session.config
            if 'circuit_breaker_enabled' not in config:
                self.errors.append("❌ Pilot Mode: Circuit breaker no configurado")
                return False

            # Verificar métodos de ejecución (sin ejecutar realmente)
            if not hasattr(session, 'execute_long_position'):
                self.errors.append("❌ Pilot Mode: Falta método execute_long_position")
                return False

            if not hasattr(session, 'execute_short_position'):
                self.errors.append("❌ Pilot Mode: Falta método execute_short_position")
                return False

            print("✅ Modo PILOT: OK")
            return True

        except Exception as e:
            self.errors.append(f"❌ Pilot Mode Error: {e}")
            return False

    async def verify_integration(self) -> bool:
        """Verificar la integración completa entre componentes."""
        print("🔍 Verificando Integración Completa...")

        try:
            # Verificar que los activos están correctamente configurados
            crypto_assets = get_crypto_assets()
            if len(crypto_assets) != 60:  # Deberían ser 60 después de la optimización
                self.errors.append(f"❌ Integration: Número incorrecto de activos crypto ({len(crypto_assets)})")
                return False

            # Verificar que los subgrupos están habilitados correctamente
            enabled_subgroups = [sg for sg in CRYPTO_SUBGROUPS.keys() if GROUP_CONFIG.get(sg, True)]
            if len(enabled_subgroups) != 6:  # Deberían ser 6 habilitados (excepto BYBIT_EXCLUSIVE)
                self.errors.append(f"❌ Integration: Número incorrecto de subgrupos habilitados ({len(enabled_subgroups)})")
                return False

            # Verificar mapping de Bybit
            test_ticker = '1000SHIBUSDT'
            corrected = get_bybit_corrected_ticker(test_ticker)
            if corrected != 'SHIBUSDT':
                self.errors.append(f"❌ Integration: Bybit mapping incorrecto ({corrected})")
                return False

            # Verificar que el bridge puede normalizar tickers
            from nexus_system.core.nexus_bridge import NexusBridge
            bridge = NexusBridge(ShadowWallet())

            test_cases = ['BTCUSDT', 'BTC/USDT', 'BTC/USDT:USDT']
            for ticker in test_cases:
                normalized = bridge.normalize_symbol(ticker)
                if normalized != 'BTCUSDT':
                    self.errors.append(f"❌ Integration: Normalización incorrecta para {ticker}")
                    return False

            print("✅ Integración Completa: OK")
            return True

        except Exception as e:
            self.errors.append(f"❌ Integration Error: {e}")
            return False

    async def run_verification(self) -> Dict[str, Any]:
        """Ejecutar todas las verificaciones."""
        print("🚀 INICIANDO VERIFICACIÓN DE INTEGRACIÓN - NEXUS TRADING BOT")
        print("=" * 70)

        # Ejecutar todas las verificaciones
        self.results['data_fetcher'] = await self.verify_data_fetcher()
        self.results['adapters'] = await self.verify_adapters()
        self.results['strategies'] = await self.verify_strategies()
        self.results['trading_manager'] = await self.verify_trading_manager()
        self.results['pilot_mode'] = await self.verify_pilot_mode()
        self.results['integration'] = await self.verify_integration()

        # Calcular resultado general
        all_passed = all(self.results.values())

        print("\n" + "=" * 70)
        print("📊 RESULTADOS DE VERIFICACIÓN:")
        print("=" * 70)

        for component, passed in self.results.items():
            status = "✅ PASÓ" if passed else "❌ FALLÓ"
            component_name = component.replace('_', ' ').title()
            print(f"{status} {component_name}")

        if self.errors:
            print("\n❌ ERRORES ENCONTRADOS:")
            for error in self.errors:
                print(f"   {error}")

        if all_passed:
            print("\n🎉 ¡TODAS LAS VERIFICACIONES PASARON!")
            print("✅ El bot está operativo y puede ejecutar operaciones en modo PILOT")
        else:
            print(f"\n⚠️ {len([r for r in self.results.values() if not r])} verificaciones fallaron")
            print("❌ Revisar errores antes de usar en modo PILOT")

        return {
            'success': all_passed,
            'results': self.results,
            'errors': self.errors,
            'timestamp': datetime.now().isoformat()
        }


async def main():
    """Función principal."""
    verifier = IntegrationVerifier()
    result = await verifier.run_verification()

    # Exit code based on success
    sys.exit(0 if result['success'] else 1)


if __name__ == "__main__":
    asyncio.run(main())
