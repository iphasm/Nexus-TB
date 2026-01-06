# 🪙 Comparación de Criptomonedas

Herramienta para comparar métricas de BTC, ETH, XRP y SOL en tiempo real.

## 📊 Características

- **Precios actuales** de las principales criptomonedas
- **Cambios porcentuales**: 1 hora, 24 horas, 7 días
- **Volumen de trading** en 24 horas
- **Capitalización de mercado**
- **Rankings** por diferentes métricas
- **Exportación** automática a JSON

## 🚀 Uso

### Ejecución básica

```bash
python crypto_comparison.py
```

### Salida de ejemplo

```
🪙 Bitcoin (BTC)
   💰 Precio: $91,397
   ⏰ 1h: +0.04%
   📅 24h: +1.44%
   📈 7d: +4.05%
   📊 Volumen 24h: $375B

🪙 Ethereum (ETH)
   💰 Precio: $3,148
   ⏰ 1h: +0.02%
   📅 24h: +0.55%
   📈 7d: +6.76%
   📊 Volumen 24h: $15.6B

🪙 XRP (XRP)
   💰 Precio: $2.07
   ⏰ 1h: +0.31%
   📅 24h: +2.39%
   📈 7d: +10.81%
   📊 Volumen 24h: $914M

🪙 Solana (SOL)
   💰 Precio: $134.44
   ⏰ 1h: +0.11%
   📅 24h: +1.36%
   📈 7d: +7.38%
   📊 Volumen 24h: $3.8B

🏆 RANKINGS:
   🚀 Mejor rendimiento 24h: XRP (+2.39%)
   📈 Mejor rendimiento 7d: XRP (+10.81%)
   💰 Mayor volumen 24h: BTC ($375B)
   🏦 Mayor market cap: BTC ($1.82T)
```

## 📋 Criptomonedas Analizadas

| Símbolo | Nombre | Descripción |
|---------|--------|-------------|
| **BTC** | Bitcoin | La criptomoneda original, reserva de valor digital |
| **ETH** | Ethereum | Plataforma de contratos inteligentes líder |
| **XRP** | XRP | Criptomoneda de Ripple para transferencias internacionales |
| **SOL** | Solana | Blockchain de alta velocidad para DeFi y NFTs |

## 📈 Métricas

### Precio Actual
- Precio en USD con formato adecuado
- Actualizado en tiempo real desde Yahoo Finance

### Cambios Porcentuales
- **1h**: Cambio en la última hora
- **24h**: Cambio en las últimas 24 horas
- **7d**: Cambio en los últimos 7 días

### Volumen y Market Cap
- **Volumen 24h**: Volumen de trading total en 24 horas
- **Market Cap**: Capitalización total del mercado

## 🏆 Rankings

La herramienta calcula automáticamente:

- **🚀 Mejor rendimiento 24h**: Cripto con mayor ganancia diaria
- **📈 Mejor rendimiento 7d**: Cripto con mayor ganancia semanal
- **💰 Mayor volumen 24h**: Cripto con mayor volumen de trading
- **🏦 Mayor market cap**: Cripto con mayor capitalización

## 💾 Exportación de Datos

Cada ejecución genera automáticamente un archivo JSON con:

- Timestamp de la consulta
- Datos completos de todas las criptomonedas
- Formato estructurado para análisis posterior

```json
{
  "timestamp": "2026-01-04T01:56:06.902185",
  "cryptocurrencies": ["BTC", "ETH", "XRP", "SOL"],
  "data": [
    {
      "symbol": "BTC-USD",
      "name": "Bitcoin",
      "current_price": 91397.2,
      "change_1h_pct": 0.04,
      "change_24h_pct": 1.44,
      "change_7d_pct": 4.05,
      "volume_24h": 375000000000.0,
      "market_cap": 1825325973504,
      "timestamp": "2026-01-04T01:55:56.399767",
      "success": true
    }
  ]
}
```

## ⚙️ Configuración

### Dependencias

```bash
pip install yfinance pandas python-dotenv
```

### Variables de Entorno

El script usa las APIs configuradas en `.env`:
- OpenAI API (opcional)
- xAI API (opcional)
- Otras APIs del proyecto

## 🔧 Personalización

### Modificar criptomonedas

Para cambiar las criptomonedas analizadas, editar:

```python
self.symbols = ['BTC-USD', 'ETH-USD', 'ADA-USD', 'DOT-USD']  # Nuevas criptos
self.names = ['Bitcoin', 'Ethereum', 'Cardano', 'Polkadot']  # Nombres completos
self.symbol_short = ['BTC', 'ETH', 'ADA', 'DOT']  # Símbolos cortos
```

### Añadir más métricas

El script puede extenderse para incluir:
- RSI (Relative Strength Index)
- MACD (Moving Average Convergence Divergence)
- Bandas de Bollinger
- Volatilidad histórica

## 📊 Interpretación

### Tendencias de Mercado
- **XRP liderando**: Mayor rendimiento reciente sugiere momentum alcista
- **BTC estable**: Como reserva de valor, muestra crecimiento consistente
- **ETH crecimiento**: Beneficiándose de upgrades y DeFi
- **SOL volátil**: Alta volatilidad típica de altcoins

### Señales de Trading
- **Cambios positivos**: Indican momentum alcista
- **Alto volumen**: Confirma interés institucional
- **Market cap**: Indica tamaño relativo del proyecto

## ⏰ Frecuencia de Actualización

- **Precios**: Actualizados cada minuto desde Yahoo Finance
- **Datos históricos**: Cálculos basados en períodos de 1h, 24h, 7d
- **Volumen**: Datos de 24 horas rolling

## 🚨 Notas Importantes

- Los datos provienen de Yahoo Finance
- Precios pueden tener ligeros delays
- Recomendado ejecutar durante horario de mercado
- No constituye consejo financiero

## 📁 Archivos Generados

- `crypto_comparison_YYYYMMDD_HHMMSS.json`: Datos completos exportados
- Archivos anteriores se preservan automáticamente

---

**Herramienta integrada en Nexus Trading Bot** - Análisis de mercado automatizado


