#!/usr/bin/env python3
"""
Análisis Simple de Modelos basado en Datos Históricos
"""

import json
from datetime import datetime

def analyze_models():
    print("🔬 ANÁLISIS ACTUALIZADO DE MODELOS IA")
    print("=" * 60)

    # Datos de rendimiento basados en análisis anterior
    model_data = {
        "GPT-4o": {
            "precision": 0.425,
            "velocidad": 3.97,
            "confianza": 0.85,
            "exito": 0.75,
            "costo": "~$0.03",
            "tipo": "OpenAI"
        },
        "GPT-4o Mini": {
            "precision": 0.400,
            "velocidad": 7.35,
            "confianza": 0.70,
            "exito": 0.75,
            "costo": "~$0.002",
            "tipo": "OpenAI"
        },
        "Grok-4.1 Fast": {
            "precision": 0.363,
            "velocidad": 10.53,
            "confianza": 0.75,
            "exito": 0.50,
            "costo": "$0.00",
            "tipo": "xAI"
        },
        "Grok-3": {
            "precision": 0.338,
            "velocidad": 12.52,
            "confianza": 0.80,
            "exito": 0.50,
            "costo": "$0.00",
            "tipo": "xAI"
        }
    }

    # Rankings
    print("🏆 RANKING POR PRECISIÓN:")
    precision_sorted = sorted(model_data.items(), key=lambda x: x[1]['precision'], reverse=True)
    for i, (model, data) in enumerate(precision_sorted, 1):
        print(f"{i}. {model:<15} | Precisión: {data['precision']:.3f} | Tipo: {data['tipo']}")
    print("\n⚡ RANKING POR VELOCIDAD:")
    speed_sorted = sorted(model_data.items(), key=lambda x: x[1]['velocidad'])
    for i, (model, data) in enumerate(speed_sorted, 1):
        print(f"{i}. {model:<15} | Velocidad: {data['velocidad']:.2f}s | Tipo: {data['tipo']}")
    print("\n🎯 RANKING POR CONFIANZA:")
    confidence_sorted = sorted(model_data.items(), key=lambda x: x[1]['confianza'], reverse=True)
    for i, (model, data) in enumerate(confidence_sorted, 1):
        print(f"{i}. {model:<15} | Velocidad: {data['velocidad']:.2f}s | Tipo: {data['tipo']}")
    print("\n💰 RANKING POR RELACIÓN COSTO-BENEFICIO:")
    cost_benefit_sorted = sorted(model_data.items(),
                               key=lambda x: x[1]['precision'] / (0.001 if x[1]['costo'] == "$0.00" else float(x[1]['costo'].replace('~$', '').replace('$', ''))),
                               reverse=True)
    for i, (model, data) in enumerate(cost_benefit_sorted, 1):
        cost_value = 0.001 if data['costo'] == "$0.00" else float(data['costo'].replace('~$', '').replace('$', ''))
        benefit_ratio = data['precision'] / cost_value if cost_value > 0 else float('inf')
        print(f"{i}. {model:<15} | Velocidad: {data['velocidad']:.2f}s | Tipo: {data['tipo']}")
    # Análisis por tipo
    print("\n📊 ANÁLISIS POR TIPO DE MODELO:")
    openai_models = {k: v for k, v in model_data.items() if v['tipo'] == 'OpenAI'}
    xai_models = {k: v for k, v in model_data.items() if v['tipo'] == 'xAI'}

    print("🤖 MODELOS OPENAI:")
    for model, data in openai_models.items():
        print(f"   {model}: Precisión {data['precision']:.3f}, Velocidad {data['velocidad']:.2f}s, Costo {data['costo']}")
    print("\n🧠 MODELOS XAI:")
    for model, data in xai_models.items():
        print(f"   {model}: Precisión {data['precision']:.3f}, Velocidad {data['velocidad']:.2f}s, Costo {data['costo']}")
    # Conclusiones
    print("\n🏁 CONCLUSIONES:")
    print("=" * 60)

    best_precision = precision_sorted[0][0]
    best_speed = speed_sorted[0][0]
    best_confidence = confidence_sorted[0][0]
    best_cost_benefit = cost_benefit_sorted[0][0]

    print(f"🎖️  Mayor Precisión: {best_precision} ({model_data[best_precision]['precision']:.3f})")
    print(f"⚡ Más Rápido: {best_speed} ({model_data[best_speed]['velocidad']:.2f}s)")
    print(f"🎯 Más Confiado: {best_confidence} ({model_data[best_confidence]['confianza']:.1%})")
    print(f"💰 Mejor Relación Costo-Beneficio: {best_cost_benefit}")

    # Recomendación final
    print("\n🎯 RECOMENDACIÓN FINAL:")
    print("-" * 40)

    if best_precision == best_confidence and best_precision == best_speed:
        winner = best_precision
        print(f"🏆 GANADOR ABSOLUTO: {winner}")
        print("   ✅ Mejor en precisión, velocidad y confianza")
    else:
        print("⚖️  RECOMENDACIONES ESPECÍFICAS:")
        print(f"   🚀 Para análisis profesional: {best_precision} (precisión crítica)")
        print(f"   💰 Para uso económico: {best_cost_benefit} (mejor valor)")
        print(f"   ⚡ Para análisis rápido: {best_speed} (velocidad máxima)")

    print("\n💡 NOTAS IMPORTANTES:")
    print("   • Los modelos OpenAI ofrecen mayor precisión pero tienen costo")
    print("   • Los modelos xAI son gratuitos pero pueden ser menos consistentes")
    print("   • GPT-4o Mini ofrece el mejor balance general")
    print("   • Considera combinar múltiples modelos para mejores resultados")

    # Guardar resultados
    result = {
        "timestamp": datetime.now().isoformat(),
        "analysis": "model_comparison_update",
        "rankings": {
            "precision": [m[0] for m in precision_sorted],
            "speed": [m[0] for m in speed_sorted],
            "confidence": [m[0] for m in confidence_sorted],
            "cost_benefit": [m[0] for m in cost_benefit_sorted]
        },
        "recommendations": {
            "best_precision": best_precision,
            "best_speed": best_speed,
            "best_confidence": best_confidence,
            "best_cost_benefit": best_cost_benefit
        }
    }

    filename = f"model_analysis_update_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"\n💾 Resultados guardados en: {filename}")

if __name__ == "__main__":
    analyze_models()
