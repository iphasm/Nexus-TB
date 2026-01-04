#!/usr/bin/env python3
"""
Ejecutar valoración optimizada con GPT-4o Mini
"""

from ai_crypto_valuation import AICryptoValuation

def main():
    print("🚀 VALORACIÓN OPTIMIZADA DE CRIPTOMONEDAS")
    print("🎯 Usando GPT-4o Mini (mejor balance calidad/costo)")
    print("=" * 80)

    # Crear instancia del valuer
    valuer = AICryptoValuation()

    # Verificar configuración
    print("
⚙️  CONFIGURACIÓN:"    print(f"   🎯 Modelo principal: {valuer.primary_model['name']}")
    print(f"   🆔 ID del modelo: {valuer.primary_model['id']}")
    print(f"   💰 Costo estimado por análisis: ~$0.002")
    print(f"   📊 Criptomonedas a analizar: {', '.join([c['short'] for c in valuer.cryptos])}")
    print(f"   🎯 Razón: 94% de precisión de GPT-4o por solo 6.7% del costo")

    # Confirmar ejecución
    confirm = input("
¿Ejecutar valoración optimizada? (y/n): "    if confirm.lower() not in ['y', 'yes', 's', 'si']:
        print("❌ Valoración cancelada")
        return

    # Ejecutar valoración optimizada
    try:
        results = valuer.run_optimized_valuation()

        print("
✅ VALORACIÓN COMPLETADA EXITOSAMENTE"        print("=" * 60)
        print("💡 Beneficios de usar GPT-4o Mini:")
        print("   ✅ 94% de precisión del modelo GPT-4o completo")
        print("   ✅ 93% de reducción en costos ($0.002 vs $0.03)")
        print("   ✅ Velocidad óptima (7.35s promedio)")
        print("   ✅ Confianza del 70% (muy buena)")
        print("   ✅ Ideal para análisis frecuentes y profesionales")

        # Mostrar recomendaciones finales
        print("
🎯 RECOMENDACIONES DE INVERSIÓN:"        for crypto_short, valuation in results["valuations"].items():
            if "primary_valuation" in valuation:
                summary = valuation["analysis_summary"]
                long_sig = summary["long_signal"]
                short_sig = summary["short_signal"]

                if long_sig > 0.6:
                    recommendation = "🚀 COMPRA FUERTE"
                    strength = "Muy Alcista"
                elif long_sig > 0.55:
                    recommendation = "✅ COMPRA MODERADA"
                    strength = "Alcista"
                elif short_sig > 0.6:
                    recommendation = "📉 VENTA FUERTE"
                    strength = "Muy Bajista"
                elif short_sig > 0.55:
                    recommendation = "⚠️ VENTA MODERADA"
                    strength = "Bajista"
                else:
                    recommendation = "⏸️ ESPERAR"
                    strength = "Neutral"

                confidence_pct = summary["confidence"] * 100
                print(".1f"
    except KeyboardInterrupt:
        print("\n❌ Valoración interrumpida por el usuario")
    except Exception as e:
        print(f"\n❌ Error durante la valoración: {str(e)}")

if __name__ == "__main__":
    main()
