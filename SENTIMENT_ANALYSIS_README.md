# 🤖 Análisis de Sentimiento de Mercado - OpenAI vs xAI

Sistema de prueba para análisis de sentimiento de mercado y valoración de oportunidades de trading usando APIs de OpenAI y xAI (Grok).

## 📋 Descripción

Este sistema obtiene datos de mercado en tiempo real y los analiza con ambas APIs para proporcionar:

- **Análisis de sentimiento** basado en noticias recientes
- **Valoración técnica** del momentum actual
- **Recomendación numérica** para operaciones LONG en BTC
- **Comparación** entre resultados de ambas APIs

## 🚀 Archivos del Sistema

### `sentiment_trading_test.py`
Script principal que ejecuta la prueba completa con datos reales:
- Obtiene precio actual de BTC desde yfinance
- Recopila noticias recientes de mercado
- Envía análisis estructurado a OpenAI y xAI
- Compara resultados y genera consenso

### `sentiment_trading_demo.py`
Demo con datos simulados para mostrar funcionamiento sin APIs reales.

## ⚙️ Configuración

### Variables de Entorno Requeridas

```bash
# API Key de OpenAI (requerida)
export OPENAI_API_KEY="tu_openai_api_key_aqui"

# API Key de xAI (opcional, para comparación)
export XAI_API_KEY="tu_xai_api_key_aqui"
```

### Dependencias

Asegúrate de tener instaladas las librerías:

```bash
pip install openai yfinance requests python-dotenv
```

## 🎯 Cómo Usar

### 1. Demo con Datos Simulados

```bash
python sentiment_trading_demo.py
```

Muestra cómo funciona el sistema con datos ficticios.

### 2. Prueba Completa con Datos Reales

```bash
python sentiment_trading_test.py
```

Requiere al menos una API key configurada.

## 📊 Salida del Sistema

### Estructura JSON de Análisis

Cada API devuelve un JSON estructurado:

```json
{
  "sentiment_score": 0.75,
  "technical_momentum": "bullish",
  "recommendation": "BUY_LONG",
  "confidence_level": 0.82,
  "key_factors": [
    "Ruptura de resistencia de $45,000",
    "Noticias positivas de FED",
    "Momentum técnico alcista"
  ],
  "analysis": "Explicación detallada del análisis"
}
```

### Interpretación de Scores

- **+1.0**: Muy positivo, oportunidad excelente para LONG
- **+0.5**: Positivo moderado, considerar LONG
- **0.0**: Neutral, esperar o evitar
- **-0.5**: Negativo moderado, evitar LONG
- **-1.0**: Muy negativo, no comprar LONG

### Recomendaciones

- **BUY_LONG**: Entrar en posición larga
- **AVOID**: Evitar entrada, esperar mejor momento
- **HOLD**: Mantener posición existente si aplica

## 🔍 Funcionalidades

### 1. Obtención de Datos de Mercado
- Precio actual de BTC/USD
- Cambios porcentuales (1h, 24h)
- Volumen de trading
- Datos técnicos básicos

### 2. Recopilación de Noticias
- Noticias de BTC desde yfinance
- Artículos de mercados tradicionales (S&P 500, Nasdaq)
- Fuentes múltiples para análisis comprehensivo

### 3. Análisis con OpenAI GPT-4o
- Modelo avanzado para análisis complejo
- Procesamiento de lenguaje natural sofisticado
- Análisis técnico y fundamental integrado

### 4. Análisis con xAI Grok
- IA más reciente con conocimientos actualizados
- Enfoque directo y conciso
- Comparación objetiva con OpenAI

### 5. Sistema de Consenso
- Comparación automática de resultados
- Cálculo de acuerdo entre APIs
- Señal de consenso final
- Nivel de confianza del análisis

## 📈 Ejemplo de Salida

```
🚀 PRUEBA DE ANÁLISIS DE SENTIMIENTO DE MERCADO
============================================================
🚀 Sentiment Trading Test Inicializado
   OpenAI: ✅
   xAI: ✅
   yfinance: ✅

📊 Fase 1: Obteniendo datos de BTC...
✅ BTC: $45230.75 (2.45% 24h)

📰 Fase 2: Obteniendo noticias de mercado...
✅ 5 noticias obtenidas

🤖 Fase 4: Análisis con OpenAI GPT-4o...
✅ OpenAI: Score 0.75, BUY_LONG (2.3s)

🧠 Fase 5: Análisis con xAI Grok...
✅ xAI: Score 0.68, BUY_LONG (1.8s)

📊 RESULTADOS FINALES:
🤖 OpenAI GPT-4o:
   Score: 0.75
   Recomendación: BUY_LONG
   Confianza: 0.82

🧠 xAI Grok:
   Score: 0.68
   Recomendación: BUY_LONG
   Confianza: 0.79

⚖️ Acuerdo entre APIs:
   Dirección: ✅
   Recomendación: ✅
   Diferencia score: 0.07
   Score promedio: 0.715

🎯 Consenso Final:
   Señal: BULLISH
   Fuerza: STRONG
   Confianza: 0.79
```

## 🛠️ Personalización

### Modificar Fuentes de Datos

En `sentiment_trading_test.py`, puedes cambiar:

```python
# Añadir más tickers para noticias
tickers = ["BTC-USD", "^GSPC", "^IXIC", "ETH-USD", "TSLA"]
```

### Ajustar Prompts de Análisis

Modificar los prompts en las funciones `analyze_with_openai()` y `analyze_with_xai()` para cambiar el enfoque del análisis.

### Cambiar Modelo de OpenAI

```python
self.openai_model = "gpt-4o-mini"  # Para respuestas más rápidas
```

## ⚡ Rendimiento

- **OpenAI GPT-4o**: ~2-3 segundos por análisis
- **xAI Grok**: ~1-2 segundos por análisis
- **Obtención de datos**: ~3-5 segundos

## 💰 Costos

### OpenAI
- GPT-4o: ~$0.03 por análisis (input + output)
- GPT-4o-mini: ~$0.002 por análisis

### xAI
- Actualmente gratuito para desarrolladores
- Límites diarios por determinar

## 🔧 Solución de Problemas

### Error: "OPENAI_API_KEY no encontrada"
```bash
export OPENAI_API_KEY="tu_clave_aqui"
```

### Error: "yfinance no disponible"
```bash
pip install yfinance
```

### Error: "xAI API Error"
- Verificar XAI_API_KEY
- Revisar límites de rate de xAI

## 📝 Notas Técnicas

- El sistema usa async/await para operaciones eficientes
- Caché automático para evitar llamadas duplicadas
- Validación robusta de respuestas JSON
- Logging detallado para debugging

## 🎯 Casos de Uso

1. **Pre-trade Analysis**: Evaluar condiciones antes de entrar
2. **Risk Assessment**: Medir nivel de riesgo basado en sentimiento
3. **Portfolio Optimization**: Ajustar posiciones basado en consenso
4. **Alert System**: Notificaciones automáticas de cambios de sentimiento
5. **Backtesting**: Evaluar efectividad del análisis histórico

## 🤝 Contribución

Para mejorar el sistema:

1. Añadir más fuentes de noticias (Bloomberg, Reuters APIs)
2. Implementar análisis técnico avanzado
3. Añadir indicadores adicionales (RSI, MACD, etc.)
4. Crear dashboard web para visualización
5. Implementar machine learning para predicción

---

**Desarrollado para Nexus Trading Bot** - Sistema híbrido OpenAI + xAI

