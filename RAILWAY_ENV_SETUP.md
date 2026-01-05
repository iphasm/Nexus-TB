# 🚀 Configuración de Variables de Entorno - Railway

Este documento explica cómo configurar las variables de entorno necesarias para el sistema de valoración de criptomonedas con GPT-4o Mini en Railway.

## 📋 Variables de Entorno Requeridas

### 🤖 APIs de IA y Modelos

| Variable | Descripción | Requerida | Cómo obtener |
|----------|-------------|-----------|--------------|
| `OPENAI_API_KEY` | API Key de OpenAI para GPT-4o Mini | ✅ Sí | [OpenAI Platform](https://platform.openai.com/api-keys) |
| `XAI_API_KEY` | API Key de xAI (opcional, para análisis híbrido) | ❌ No | [xAI Platform](https://x.ai/) |

### 🪙 APIs de Datos de Criptomonedas

| Variable | Descripción | Requerida | Cómo obtener |
|----------|-------------|-----------|--------------|
| `COINGECKO_API_KEY` | API Key gratuita de CoinGecko | ✅ Sí | [CoinGecko API](https://www.coingecko.com/en/api) |
| `CRYPTOPANIC_API_KEY` | API Key de CryptoPanic (opcional) | ❌ No | [CryptoPanic API](https://cryptopanic.com/developers/api/) |

### 🗄️ Base de Datos (si aplica)

| Variable | Descripción | Requerida | Ejemplo |
|----------|-------------|-----------|---------|
| `DATABASE_URL` | URL de conexión a PostgreSQL | ❌ No | `postgresql://user:pass@host:5432/db` |

## ⚙️ Configuración en Railway

### Paso 1: Acceder a las Variables de Entorno
1. Ve al dashboard de tu proyecto en Railway
2. Selecciona tu servicio
3. Ve a la pestaña "Variables"

### Paso 2: Agregar Variables de Entorno

#### Variables Obligatorias:
```
OPENAI_API_KEY=sk-proj-tu_clave_de_openai_aqui...
COINGECKO_API_KEY=CG-tu_clave_de_coingecko_aqui...
```

#### Variables Opcionales:
```
XAI_API_KEY=xai-tu_clave_de_xai_aqui...
CRYPTOPANIC_API_KEY=tu_clave_de_cryptopanic_aqui...
DATABASE_URL=postgresql://usuario:contraseña@host:5432/base_datos
```

### Paso 3: Reiniciar el Servicio
Después de agregar las variables, reinicia tu servicio para que tome los cambios.

## 🔍 Verificación de Configuración

Ejecuta este comando para verificar que todas las APIs estén configuradas:

```bash
python verify_apis_integration.py
```

### Salida Esperada:
```
🪙 COINGECKO API:
   ✅ API Key configurada: CG-9oCX...
   ✅ Disponibilidad: ✅

📰 CRYPTOPANIC API:
   ✅ API Key configurada: 25991acc...
   ✅ Disponibilidad: ✅

🤖 INTEGRACIÓN EN PROMPTS DE IA:
   ✅ GPT-4o Mini incluye:
      - Métricas CoinGecko detalladas ✅
      - Análisis de sentimiento CryptoPanic ✅
      - Fear & Greed Index ✅
      - Datos globales de mercado ✅

🎯 MODELO PRINCIPAL CONFIGURADO:
   🤖 Modelo: GPT-4o Mini
   🆔 ID: gpt-4o-mini
   💰 Costo estimado: $0.002 por análisis
   📊 Precisión: 94% de GPT-4o completo
```

## 🛠️ Solución de Problemas

### ❌ "CoinGecko API no configurada"
- Verifica que la variable `COINGECKO_API_KEY` esté configurada en Railway
- Asegúrate de que la API key sea válida (empieza con "CG-")

### ❌ "OpenAI API no configurada"
- Verifica que la variable `OPENAI_API_KEY` esté configurada
- Asegúrate de que tengas créditos disponibles en OpenAI

### ❌ "CryptoPanic API no configurada"
- Esta API es opcional, pero mejora el análisis de sentimiento
- Configura `CRYPTOPANIC_API_KEY` si deseas análisis de noticias

## 💰 Costos Estimados

| Servicio | Costo por Uso | Frecuencia Típica |
|----------|----------------|-------------------|
| **OpenAI (GPT-4o Mini)** | ~$0.002 | Por valoración completa |
| **CoinGecko** | $0.00 | Gratuito (plan demo) |
| **CryptoPanic** | $0.00 | Incluido en valoración |
| **Railway** | Variable | Según plan y uso |

## 🚀 Uso del Sistema

Una vez configuradas las variables de entorno:

```bash
# Valoración completa optimizada
python run_optimized_valuation.py

# Demo del AI Filter integrado
python demo_ai_filter_integrated.py

# Verificación de APIs
python verify_apis_integration.py
```

## 🔒 Seguridad

- ✅ **Nunca incluyas API keys en el código**
- ✅ **Las variables de entorno están encriptadas en Railway**
- ✅ **Las keys no aparecen en logs ni archivos**
- ✅ **Acceso restringido a variables sensibles**

## 📞 Soporte

Si tienes problemas con la configuración:

1. Verifica que las variables estén escritas correctamente (case-sensitive)
2. Reinicia el servicio después de cambios
3. Revisa los logs de Railway para errores específicos
4. Usa `python verify_apis_integration.py` para diagnosticar

---

**✅ Configuración completada correctamente garantiza el funcionamiento óptimo del sistema de valoración con GPT-4o Mini.**

