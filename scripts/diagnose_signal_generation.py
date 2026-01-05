#!/usr/bin/env python3
"""
Diagnóstico de Generación de Señales - Nexus-TB
Script para identificar por qué se están generando muy pocas señales.
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta
import pandas as pd

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from nexus_system.uplink.stream import MarketStream
from nexus_system.cortex.factory import StrategyFactory
from nexus_system.cortex.classifier import MarketClassifier
from nexus_system.cortex.ml_classifier import MLClassifier
from servos.ai_filter import should_filter_signal, ai_filter_engine
from system_directive import ENABLED_STRATEGIES, ML_CLASSIFIER_ENABLED

class SignalDiagnostics:
    """Diagnóstico completo del sistema de señales."""

    def __init__(self):
        self.market_stream = MarketStream()
        self.diagnostics = {
            'market_data': {},
            'classifier_results': {},
            'strategy_results': {},
            'filter_results': {},
            'overall_stats': {}
        }

    async def run_full_diagnostic(self, symbols=None):
        """Ejecutar diagnóstico completo."""
        print("🔍 INICIANDO DIAGNÓSTICO COMPLETO DEL SISTEMA DE SEÑALES")
        print("=" * 60)

        # Símbolos a probar
        if symbols is None:
            symbols = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'ADAUSDT', 'DOTUSDT']

        print(f"📊 Probando con {len(symbols)} símbolos: {symbols}")
        print()

        # 1. Verificar estado del sistema
        await self.check_system_status()

        # 2. Obtener datos de mercado
        await self.check_market_data(symbols)

        # 3. Probar clasificadores
        await self.test_classifiers(symbols)

        # 4. Probar estrategias
        await self.test_strategies(symbols)

        # 5. Probar filtros
        await self.test_filters(symbols)

        # 6. Generar reporte final
        self.generate_report()

    async def check_system_status(self):
        """Verificar estado del sistema."""
        print("🔧 VERIFICANDO ESTADO DEL SISTEMA")
        print("-" * 40)

        # Verificar estrategias habilitadas
        print(f"📋 Estrategias habilitadas: {ENABLED_STRATEGIES}")
        print(f"🤖 ML Classifier: {'HABILITADO' if ML_CLASSIFIER_ENABLED else 'DESHABILITADO'}")

        # Verificar AI Filter
        try:
            await ai_filter_engine.initialize()
            filter_stats = ai_filter_engine.get_filter_stats()
            print(f"🎯 AI Filter: {'FUNCIONANDO' if filter_stats['xai_available'] else 'SIN SISTEMA HÍBRIDO'}")
            print(f"🎯 GPT-4o Mini: {'DISPONIBLE' if filter_stats['gpt_valuation_available'] else 'NO DISPONIBLE'}")
        except Exception as e:
            print(f"❌ Error en AI Filter: {e}")

        print()

    async def check_market_data(self, symbols):
        """Verificar obtención de datos de mercado."""
        print("📊 VERIFICANDO DATOS DE MERCADO")
        print("-" * 40)

        await self.market_stream.initialize()

        for symbol in symbols:
            try:
                print(f"🔄 Obteniendo datos para {symbol}...")
                market_data = await self.market_stream.get_candles(symbol)

                if market_data.get('dataframe') is None or market_data['dataframe'].empty:
                    print(f"❌ No hay datos para {symbol}")
                    continue

                df = market_data['dataframe']
                last_row = df.iloc[-1]

                # Verificar indicadores técnicos críticos
                indicators_status = {
                    'rsi': last_row.get('rsi'),
                    'adx': last_row.get('adx'),
                    'atr': last_row.get('atr'),
                    'ema_20': last_row.get('ema_20'),
                    'ema_50': last_row.get('ema_50'),
                    'ema_200': last_row.get('ema_200'),
                    'close': last_row.get('close')
                }

                self.diagnostics['market_data'][symbol] = {
                    'rows': len(df),
                    'last_close': last_row.get('close'),
                    'indicators': indicators_status,
                    'missing_indicators': [k for k, v in indicators_status.items() if v is None or pd.isna(v)]
                }

                print(f"✅ {symbol}: {len(df)} velas, Close: ${last_row.get('close', 0):.2f}")

                if indicators_status['missing_indicators']:
                    print(f"⚠️  Indicadores faltantes: {indicators_status['missing_indicators']}")

            except Exception as e:
                print(f"❌ Error obteniendo datos para {symbol}: {e}")
                self.diagnostics['market_data'][symbol] = {'error': str(e)}

        print()

    async def test_classifiers(self, symbols):
        """Probar los clasificadores de mercado."""
        print("🧠 PROBANDO CLASIFICADORES")
        print("-" * 40)

        for symbol in symbols:
            if symbol not in self.diagnostics['market_data'] or 'error' in self.diagnostics['market_data'][symbol]:
                continue

            market_data = await self.market_stream.get_candles(symbol)

            print(f"🔍 Clasificando {symbol}...")

            # Probar ML Classifier
            ml_result = None
            if ML_CLASSIFIER_ENABLED:
                try:
                    ml_result = MLClassifier.classify(market_data)
                    print(f"🤖 ML: {ml_result.regime} → {ml_result.suggested_strategy} (Conf: {ml_result.confidence:.2f})")
                except Exception as e:
                    print(f"❌ ML Classifier error: {e}")

            # Probar Rule-Based Classifier
            try:
                rule_result = MarketClassifier.classify(market_data)
                print(f"📊 Rule-Based: {rule_result.regime} → {rule_result.suggested_strategy} (Conf: {rule_result.confidence:.2f})")
            except Exception as e:
                print(f"❌ Rule-Based Classifier error: {e}")
                continue

            # Determinar cuál se usará
            final_result = ml_result if ml_result else rule_result
            final_source = "ML" if ml_result else "Rule-Based"

            self.diagnostics['classifier_results'][symbol] = {
                'ml_result': ml_result.__dict__ if ml_result else None,
                'rule_result': rule_result.__dict__,
                'final_result': final_result.__dict__,
                'source': final_source
            }

            print(f"🎯 Final: {final_result.regime} → {final_result.suggested_strategy} ({final_source})")
            print()

    async def test_strategies(self, symbols):
        """Probar las estrategias."""
        print("📈 PROBANDO ESTRATEGIAS")
        print("-" * 40)

        for symbol in symbols:
            if symbol not in self.diagnostics['classifier_results']:
                continue

            market_data = await self.market_stream.get_candles(symbol)
            classifier_result = self.diagnostics['classifier_results'][symbol]['final_result']

            print(f"⚡ Probando estrategia para {symbol}...")

            try:
                # Obtener estrategia
                strategy = StrategyFactory.get_strategy(symbol, market_data)

                if strategy:
                    print(f"📦 Estrategia asignada: {strategy.name}")

                    # Ejecutar análisis
                    signal = await strategy.analyze(market_data)

                    if signal:
                        print(f"🟢 SEÑAL GENERADA: {signal.action} (Conf: {signal.confidence:.2f})")
                        print(f"   Precio: ${signal.price:.2f}, RSI: {signal.metadata.get('rsi', 'N/A')}")
                    else:
                        print(f"🟡 Sin señal (HOLD)")

                    self.diagnostics['strategy_results'][symbol] = {
                        'strategy_name': strategy.name,
                        'signal': signal.__dict__ if signal else None,
                        'regime_meta': getattr(strategy, 'regime_meta', None)
                    }
                else:
                    print(f"❌ No se pudo asignar estrategia")
                    self.diagnostics['strategy_results'][symbol] = {'error': 'No strategy assigned'}

            except Exception as e:
                print(f"❌ Error en estrategia: {e}")
                self.diagnostics['strategy_results'][symbol] = {'error': str(e)}

            print()

    async def test_filters(self, symbols):
        """Probar los filtros de señales."""
        print("🎯 PROBANDO FILTROS DE SEÑALES")
        print("-" * 40)

        # Configuración de sesión de ejemplo
        session_config = {
            'sentiment_filter': True,
            'atr_multiplier': 2.2,
            'circuit_breaker_enabled': True
        }

        for symbol in symbols:
            if symbol not in self.diagnostics['strategy_results'] or not self.diagnostics['strategy_results'][symbol].get('signal'):
                continue

            signal = self.diagnostics['strategy_results'][symbol]['signal']

            print(f"🔍 Filtrando señal {signal['action']} para {symbol}...")

            try:
                # Crear datos de señal para el filtro
                signal_data = {
                    'symbol': symbol,
                    'side': signal['action'],
                    'entry_price': signal['price'],
                    'confidence': signal['confidence']
                }

                # Aplicar filtro
                should_filter, reason, analysis_data = await should_filter_signal(signal_data, session_config)

                if should_filter:
                    print(f"❌ SEÑAL FILTRADA: {reason}")
                else:
                    print(f"✅ SEÑAL APROBADA: {reason}")

                self.diagnostics['filter_results'][symbol] = {
                    'original_signal': signal,
                    'should_filter': should_filter,
                    'reason': reason,
                    'analysis_data': analysis_data
                }

            except Exception as e:
                print(f"❌ Error en filtro: {e}")
                self.diagnostics['filter_results'][symbol] = {'error': str(e)}

            print()

    def generate_report(self):
        """Generar reporte final."""
        print("📋 REPORTE FINAL DE DIAGNÓSTICO")
        print("=" * 60)

        total_symbols = len(self.diagnostics['market_data'])
        successful_market_data = sum(1 for d in self.diagnostics['market_data'].values() if 'error' not in d)
        successful_classifiers = len(self.diagnostics['classifier_results'])
        successful_strategies = len(self.diagnostics['strategy_results'])
        generated_signals = sum(1 for d in self.diagnostics['strategy_results'].values() if d.get('signal'))
        approved_signals = sum(1 for d in self.diagnostics['filter_results'].values() if not d.get('should_filter', True))

        print(f"📊 Símbolos analizados: {total_symbols}")
        print(f"📈 Datos de mercado exitosos: {successful_market_data}/{total_symbols}")
        print(f"🧠 Clasificadores exitosos: {successful_classifiers}/{total_symbols}")
        print(f"⚡ Estrategias probadas: {successful_strategies}/{total_symbols}")
        print(f"🟢 Señales generadas: {generated_signals}/{total_symbols}")
        print(f"✅ Señales aprobadas: {approved_signals}/{total_symbols}")
        print()

        # Análisis de cuellos de botella
        print("🔍 ANÁLISIS DE CUELLOS DE BOTELLA:")
        print("-" * 40)

        if successful_market_data < total_symbols:
            print("❌ PROBLEMA: Datos de mercado faltantes - Verificar conexiones API")

        if generated_signals == 0:
            print("❌ PROBLEMA CRÍTICO: Ninguna estrategia genera señales")
            print("   Posibles causas:")
            print("   - Umbrales de RSI demasiado restrictivos")
            print("   - Lógica de trend incorrecta")
            print("   - Datos de indicadores faltantes")
        elif generated_signals < successful_strategies * 0.5:
            print("⚠️  PROBLEMA: Pocas señales generadas por estrategias")
            print("   Posibles causas:")
            print("   - Umbrales de entrada demasiado conservadores")
            print("   - Condiciones de mercado no favorables")

        if approved_signals < generated_signals:
            filtered_signals = generated_signals - approved_signals
            filter_rate = filtered_signals / generated_signals * 100
            print(f"⚠️  PROBLEMA: Alto porcentaje de señales filtradas ({filter_rate:.1f}%)")
            print("   Posibles causas:")
            print("   - AI Filter demasiado restrictivo")
            print("   - GPT-4o Mini filtrando señales válidas")
            print("   - Umbrales de Fear & Greed muy estrictos")

        print()
        print("💡 RECOMENDACIONES:")
        print("-" * 40)

        if generated_signals == 0:
            print("1. Revisar umbrales de RSI en estrategias (actualmente <45 para LONG, >55 para SHORT)")
            print("2. Verificar lógica de trend (price > EMA200)")
            print("3. Comprobar que los indicadores técnicos se calculan correctamente")

        if approved_signals < generated_signals:
            print("1. Revisar configuración del AI Filter")
            print("2. Considerar desactivar temporalmente filtros muy restrictivos")
            print("3. Ajustar pesos en la lógica de decisión del filtro")

        if successful_market_data < total_symbols:
            print("1. Verificar conexiones a APIs de Binance/Bybit")
            print("2. Comprobar que los símbolos existen en los exchanges")

        print()
        print("🎯 PRÓXIMOS PASOS:")
        print("1. Ejecutar con más símbolos para estadísticas robustas")
        print("2. Monitorear en tiempo real durante mercado volátil")
        print("3. Ajustar parámetros basados en resultados")

async def main():
    """Función principal."""
    diagnostics = SignalDiagnostics()
    await diagnostics.run_full_diagnostic()

if __name__ == "__main__":
    asyncio.run(main())
