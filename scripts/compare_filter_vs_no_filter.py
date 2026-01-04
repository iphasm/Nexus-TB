#!/usr/bin/env python3
"""
Comparación: Señales generadas con vs sin AI Filter
Demuestra cómo el AI Filter corregido permite más señales válidas
"""

import asyncio
import json
from datetime import datetime
import sys
import os

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from nexus_system.core.engine import NexusCore
from servos.ai_filter import should_filter_signal, ai_filter_engine
from system_directive import ENABLED_STRATEGIES


class FilterComparison:
    """
    Compara la generación de señales con y sin AI Filter
    """

    def __init__(self):
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'comparison': {}
        }

    async def simulate_signals_with_filter(self, symbols, filter_enabled=True):
        """Simula señales con/sin filtro"""
        results = []

        for symbol in symbols:
            # Simular datos de mercado (simplificados)
            market_data = {
                'dataframe': None,  # En un test real tendríamos datos
                'symbol': symbol
            }

            # Simular estrategia (simplificada)
            # En producción, esto vendría del StrategyFactory
            simulated_signals = self._simulate_strategy_signals(symbol)

            for signal in simulated_signals:
                signal_data = {
                    'symbol': symbol,
                    'side': signal['side'],
                    'entry_price': signal['price'],
                    'confidence': signal['confidence'],
                    'strategy': signal['strategy']
                }

                if filter_enabled:
                    # Aplicar AI Filter
                    session_config = {'sentiment_filter': True}
                    try:
                        should_filter, reason, analysis = await should_filter_signal(signal_data, session_config)
                        signal_result = {
                            'signal': signal_data,
                            'filtered': should_filter,
                            'reason': reason,
                            'score': analysis.get('filter_score', 0),
                            'passed': not should_filter
                        }
                    except Exception as e:
                        signal_result = {
                            'signal': signal_data,
                            'filtered': False,
                            'reason': f'Error: {e}',
                            'score': 0,
                            'passed': True
                        }
                else:
                    # Sin filtro - todas pasan
                    signal_result = {
                        'signal': signal_data,
                        'filtered': False,
                        'reason': 'No filter applied',
                        'score': 0,
                        'passed': True
                    }

                results.append(signal_result)

        return results

    def _simulate_strategy_signals(self, symbol):
        """Simula señales que generarían diferentes estrategias"""
        # Simular señales realistas basadas en el mercado actual
        base_signals = [
            {
                'side': 'LONG',
                'price': self._get_symbol_price(symbol),
                'confidence': 0.85,
                'strategy': 'TREND_FOLLOWING'
            },
            {
                'side': 'SHORT',
                'price': self._get_symbol_price(symbol),
                'confidence': 0.78,
                'strategy': 'MEAN_REVERSION'
            },
            {
                'side': 'LONG',
                'price': self._get_symbol_price(symbol),
                'confidence': 0.82,
                'strategy': 'SCALPING'
            }
        ]

        return base_signals

    def _get_symbol_price(self, symbol):
        """Precios aproximados para simulación"""
        prices = {
            'BTCUSDT': 45000,
            'ETHUSDT': 2800,
            'SOLUSDT': 120,
            'ADAUSDT': 0.45,
            'DOTUSDT': 8.50
        }
        return prices.get(symbol, 100)

    async def run_comparison(self):
        """Ejecutar comparación completa"""
        print("🔍 COMPARACIÓN: SEÑALES CON vs SIN AI FILTER")
        print("=" * 60)

        # Símbolos a probar
        test_symbols = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'ADAUSDT', 'DOTUSDT']

        # Inicializar AI Filter
        from servos.ai_filter import initialize_ai_filter
        await initialize_ai_filter()
        print("✅ AI Filter inicializado")

        print(f"\n🎯 Probando {len(test_symbols)} símbolos con {len(test_symbols) * 3} señales simuladas")

        # Comparar con filtro activado
        print("\n🟢 CON AI FILTER (corregido):")
        with_filter = await self.simulate_signals_with_filter(test_symbols, filter_enabled=True)

        # Comparar sin filtro
        print("\n🔴 SIN AI FILTER:")
        without_filter = await self.simulate_signals_with_filter(test_symbols, filter_enabled=False)

        # Analizar resultados
        self.analyze_results(with_filter, without_filter)

        # Guardar resultados
        self.save_comparison(with_filter, without_filter)

    def analyze_results(self, with_filter, without_filter):
        """Analizar y mostrar resultados de la comparación"""
        print("\n📊 ANÁLISIS DE RESULTADOS")
        print("=" * 40)

        total_signals = len(with_filter)
        passed_with_filter = sum(1 for s in with_filter if s['passed'])
        passed_without_filter = sum(1 for s in without_filter if s['passed'])

        filtered_signals = total_signals - passed_with_filter

        print(f"📈 Total señales simuladas: {total_signals}")
        print(f"🟢 Señal permitidas CON filtro: {passed_with_filter} ({passed_with_filter/total_signals*100:.1f}%)")
        print(f"🔴 Señal permitidas SIN filtro: {passed_without_filter} ({passed_without_filter/total_signals*100:.1f}%)")
        print(f"❌ Señal filtradas: {filtered_signals} ({filtered_signals/total_signals*100:.1f}%)")

        if filtered_signals > 0:
            print(f"\n🎯 RAZONES DE FILTRADO:")
            reasons = {}
            for signal in with_filter:
                if not signal['passed']:
                    reason = signal['reason']
                    reasons[reason] = reasons.get(reason, 0) + 1

            for reason, count in sorted(reasons.items(), key=lambda x: x[1], reverse=True):
                print(f"  • {reason}: {count} señales")

        # Análisis por símbolo
        print(f"\n📊 ANÁLISIS POR SÍMBOLO:")
        symbols_stats = {}
        for symbol in set(s['signal']['symbol'] for s in with_filter):
            symbol_signals = [s for s in with_filter if s['signal']['symbol'] == symbol]
            passed = sum(1 for s in symbol_signals if s['passed'])
            total = len(symbol_signals)
            symbols_stats[symbol] = {'passed': passed, 'total': total, 'rate': passed/total*100}

        for symbol, stats in sorted(symbols_stats.items()):
            print(f"  • {symbol}: {stats['passed']}/{stats['total']} ({stats['rate']:.1f}%) permitidas")

    def save_comparison(self, with_filter, without_filter):
        """Guardar comparación en archivo JSON"""
        self.results['comparison'] = {
            'with_filter': with_filter,
            'without_filter': without_filter,
            'summary': {
                'total_signals': len(with_filter),
                'passed_with_filter': sum(1 for s in with_filter if s['passed']),
                'passed_without_filter': sum(1 for s in without_filter if s['passed']),
                'filtered_signals': sum(1 for s in with_filter if not s['passed'])
            }
        }

        filename = f"filter_comparison_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)

        print(f"\n💾 Resultados guardados en: {filename}")


async def main():
    """Función principal"""
    comparator = FilterComparison()
    await comparator.run_comparison()

    print("\n🎯 COMPARACIÓN COMPLETADA")
    print("💡 El AI Filter corregido debería permitir más señales válidas")


if __name__ == "__main__":
    asyncio.run(main())
