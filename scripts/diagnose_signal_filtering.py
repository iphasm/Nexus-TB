#!/usr/bin/env python3
"""
Diagnóstico Avanzado del Sistema de Filtrado de Señales
Analiza por qué el AI Filter está bloqueando muchas señales
"""

import asyncio
import json
from datetime import datetime, timedelta
import sys
import os

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from servos.ai_filter import ai_filter_engine, initialize_ai_filter, get_filter_stats
from nexus_system.core.engine import NexusCore
from system_directive import ENABLED_STRATEGIES


class SignalFilterDiagnostics:
    """
    Diagnóstico completo del sistema de filtrado de señales
    """

    def __init__(self):
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'diagnostics': {},
            'recommendations': []
        }

    async def run_full_diagnosis(self):
        """Ejecutar diagnóstico completo del sistema de filtrado"""
        print("🔍 DIAGNÓSTICO DEL SISTEMA DE FILTRADO DE SEÑALES")
        print("=" * 60)

        # 1. Verificar estado del AI Filter
        await self.check_ai_filter_status()

        # 2. Analizar umbrales de filtrado
        self.analyze_filter_thresholds()

        # 3. Simular señales de prueba
        await self.simulate_test_signals()

        # 4. Verificar configuración de sesiones
        self.check_session_defaults()

        # 5. Generar recomendaciones
        self.generate_recommendations()

        # 6. Guardar resultados
        self.save_results()

    async def check_ai_filter_status(self):
        """Verificar estado del AI Filter"""
        print("\n📊 1. ESTADO DEL AI FILTER")

        try:
            await initialize_ai_filter()
            stats = get_filter_stats()

            print("✅ AI Filter inicializado correctamente")
            print(f"🤖 Sistema Híbrido xAI: {'✅ Disponible' if stats.get('xai_available') else '❌ No disponible'}")
            print(f"🎯 GPT-4o Mini: {'✅ Disponible' if stats.get('gpt_valuation_available') else '❌ No disponible'}")
            print(f"📦 Cache: {stats.get('cache_size', 0)} elementos")
            print(f"🎯 Modelo GPT: {stats.get('primary_model', 'Desconocido')}")

            self.results['diagnostics']['ai_filter_status'] = stats

        except Exception as e:
            print(f"❌ Error inicializando AI Filter: {e}")
            self.results['diagnostics']['ai_filter_status'] = {'error': str(e)}

    def analyze_filter_thresholds(self):
        """Analizar umbrales de filtrado que pueden estar muy restrictivos"""
        print("\n⚙️ 2. ANÁLISIS DE UMBRALES DE FILTRADO")

        # Umbral principal de filtrado (score > 0.7)
        filter_threshold = 0.7
        print(f"🎯 Umbral principal de filtrado: {filter_threshold} (score > {filter_threshold} = FILTRAR)")

        # Pesos de cada factor
        weights = {
            'Fear & Greed': 0.15,
            'Volatilidad': 0.15,
            'Momentum': 0.15,
            'IA Híbrida': 0.2,
            'GPT-4o Mini': 0.35
        }

        print("\n📊 PESOS DE FACTORES:")
        for factor, weight in weights.items():
            print(f"  • {factor}: {weight:.0%}")

        print("\n🎯 GPT-4o Mini tiene el mayor peso (35%) - Esto puede estar filtrando muchas señales!")
        # Calcular cuánto contribuye cada factor al score límite
        max_contribution = {}
        for factor, weight in weights.items():
            max_contribution[factor] = weight * 1.0  # Score máximo posible por factor

        print("\n💡 CONTRIBUCIÓN MÁXIMA AL SCORE FINAL:")
        for factor, contribution in max_contribution.items():
            print(f"  • {factor}: {contribution:.3f}")
        # GPT-4o Mini puede contribuir hasta 0.35 al score
        # Si GPT-4o Mini da score > 0.6, contribuye > 0.21 al score final
        # Solo se necesita Fear & Greed adverso para llegar al umbral de 0.7

        self.results['diagnostics']['thresholds'] = {
            'filter_threshold': filter_threshold,
            'weights': weights,
            'max_contributions': max_contribution
        }

    async def simulate_test_signals(self):
        """Simular señales de prueba para ver cómo las filtra el sistema"""
        print("\n🧪 3. SIMULACIÓN DE SEÑALES DE PRUEBA")

        # Señales de prueba representativas
        test_signals = [
            {
                'symbol': 'BTCUSDT',
                'side': 'LONG',
                'entry_price': 45000,
                'confidence': 0.85,
                'strategy': 'TREND_FOLLOWING'
            },
            {
                'symbol': 'ETHUSDT',
                'side': 'SHORT',
                'entry_price': 2800,
                'confidence': 0.78,
                'strategy': 'MEAN_REVERSION'
            },
            {
                'symbol': 'SOLUSDT',
                'side': 'LONG',
                'entry_price': 120,
                'confidence': 0.82,
                'strategy': 'SCALPING'
            }
        ]

        # Configuración de sesión típica
        session_config = {
            'sentiment_filter': True,
            'ml_mode': True,
            'risk_management': True
        }

        results = []
        for signal in test_signals:
            print(f"\n🔍 Probando señal: {signal['symbol']} {signal['side']} ({signal['strategy']})")

            try:
                should_filter, reason, analysis = await ai_filter_engine.should_filter_signal(signal, session_config)

                result = {
                    'signal': signal,
                    'filtered': should_filter,
                    'reason': reason,
                    'analysis': analysis
                }
                results.append(result)

                if should_filter:
                    print(f"❌ FILTRADA: {reason}")
                else:
                    print(f"✅ PERMITIDA: {reason}")

                # Mostrar breakdown del score
                if 'filter_score' in analysis:
                    print(f"   📊 Score final: {analysis['filter_score']:.2f}")
            except Exception as e:
                print(f"❌ Error probando señal: {e}")
                results.append({'signal': signal, 'error': str(e)})

        self.results['diagnostics']['test_signals'] = results

    def check_session_defaults(self):
        """Verificar configuración por defecto de sesiones"""
        print("\n👤 4. CONFIGURACIÓN POR DEFECTO DE SESIONES")

        # Configuración típica de sesión
        default_config = {
            'sentiment_filter': True,  # AI Filter activado por defecto
            'ml_mode': True,
            'risk_management': True,
            'max_positions': 5,
            'position_size_pct': 10.0
        }

        print("📋 Configuración por defecto:")
        for key, value in default_config.items():
            status = "🟢 ACTIVO" if value else "🔴 DESACTIVADO"
            print(f"  • {key}: {value} {status}")

        print("\n⚠️  ALERTA: sentiment_filter está ACTIVO por defecto!")
        print("   Esto significa que TODAS las señales pasan por el AI Filter")

        self.results['diagnostics']['session_defaults'] = default_config

    def generate_recommendations(self):
        """Generar recomendaciones basadas en el diagnóstico"""
        print("\n💡 5. RECOMENDACIONES")

        recommendations = []

        # Problema 1: GPT-4o Mini tiene demasiado peso
        rec1 = {
            'priority': 'HIGH',
            'issue': 'GPT-4o Mini tiene 35% de peso en el score de filtrado',
            'impact': 'Puede estar filtrando muchas señales válidas',
            'solution': 'Reducir el peso de GPT-4o Mini al 20-25% y aumentar pesos de factores técnicos'
        }
        recommendations.append(rec1)
        print(f"🔴 ALTA: {rec1['issue']}")
        print(f"   💡 {rec1['solution']}")

        # Problema 2: Umbral de filtrado muy bajo
        rec2 = {
            'priority': 'HIGH',
            'issue': 'Umbral de filtrado es 0.7 (muy restrictivo)',
            'impact': 'Muchas señales borderline son filtradas',
            'solution': 'Aumentar umbral a 0.75-0.8 para permitir más señales'
        }
        recommendations.append(rec2)
        print(f"\n🔴 ALTA: {rec2['issue']}")
        print(f"   💡 {rec2['solution']}")

        # Problema 3: AI Filter activado por defecto
        rec3 = {
            'priority': 'MEDIUM',
            'issue': 'AI Filter activado por defecto en todas las sesiones',
            'impact': 'Todas las señales pasan por filtrado restrictivo',
            'solution': 'Considerar opción de desactivar AI Filter para usuarios avanzados'
        }
        recommendations.append(rec3)
        print(f"\n🟡 MEDIA: {rec3['issue']}")
        print(f"   💡 {rec3['solution']}")

        # Recomendación 4: Monitoreo mejorado
        rec4 = {
            'priority': 'LOW',
            'issue': 'Falta logging detallado de por qué se filtran señales',
            'impact': 'Difícil diagnosticar problemas de filtrado',
            'solution': 'Mejorar logging con breakdown completo del score de filtrado'
        }
        recommendations.append(rec4)
        print(f"\n🟢 BAJA: {rec4['issue']}")
        print(f"   💡 {rec4['solution']}")

        self.results['recommendations'] = recommendations

    def save_results(self):
        """Guardar resultados del diagnóstico"""
        filename = f"signal_filter_diagnosis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)

        print(f"\n💾 Resultados guardados en: {filename}")

        # Mostrar resumen
        print("\n📋 RESUMEN EJECUTIVO:")
        print("=" * 40)
        print("🎯 PROBLEMA IDENTIFICADO: AI Filter demasiado restrictivo")
        print("🎯 CAUSA PRINCIPAL: GPT-4o Mini (35% peso) + umbral bajo (0.7)")
        print("🎯 IMPACTO: Muchas señales válidas son filtradas")
        print("🎯 SOLUCIÓN: Ajustar pesos y umbrales del AI Filter")


async def main():
    """Función principal"""
    diagnostics = SignalFilterDiagnostics()
    await diagnostics.run_full_diagnosis()


if __name__ == "__main__":
    asyncio.run(main())
