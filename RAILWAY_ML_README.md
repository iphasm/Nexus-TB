# 🚀 Railway ML Training Service

Servicio de entrenamiento de modelos ML para Nexus Trading Bot desplegado en Railway.

## 📋 Descripción

Este servicio permite entrenar modelos de Machine Learning en la nube usando Railway, separando la carga computacional del bot principal. El servicio incluye:

- ✅ Entrenamiento automático de modelos XGBoost
- ✅ API REST para control remoto
- ✅ Monitoreo de progreso en tiempo real
- ✅ Almacenamiento automático de modelos entrenados
- ✅ Integración completa con bot Telegram

## 🛠️ Arquitectura

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Telegram Bot  │────│  Railway ML API  │────│   ML Training   │
│   /ml_train     │    │  /train          │    │   Scripts       │
│   /ml_status    │    │  /status         │    │                 │
│   /ml_logs      │    │  /logs           │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
        │                        │                        │
        └─ Control remoto ───────┼─ HTTP API ─────────────┘
                                 │
                    ┌────────────┴────────────┐
                    │  Modelo ML Actualizado  │
                    │  nexus_system/         │
                    │  memory_archives/      │
                    └─────────────────────────┘
```

## 🚀 Despliegue en Railway

### Paso 1: Preparación
```bash
# Instalar Railway CLI
npm install -g @railway/cli

# Login en Railway
railway login
```

### Paso 2: Configurar Variables de Entorno
```bash
# Variables requeridas para el servicio ML
railway variables set BINANCE_API_KEY=tu_api_key
railway variables set BINANCE_API_SECRET=tu_api_secret
railway variables set ALPHA_VANTAGE_API_KEY=tu_alpha_vantage_key  # Opcional
railway variables set PYTHONUNBUFFERED=1
railway variables set LOG_LEVEL=INFO
```

### Paso 3: Desplegar Servicio
```bash
# Opción A: Despliegue automático
python deploy_railway_ml.py

# Opción B: Despliegue manual
railway init --name nexus-ml-training
railway up --service railway-ml
```

### Paso 4: Obtener URL del Servicio
```bash
railway domain
# Output: https://nexus-ml-training.up.railway.app
```

### Paso 5: Configurar Bot Principal
```bash
# En tu bot principal, configura la variable de entorno
export RAILWAY_ML_URL=https://nexus-ml-training.up.railway.app
```

## 📡 API Endpoints

### `GET /health`
Verifica que el servicio esté funcionando.

**Respuesta:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "service": "railway-ml-trainer"
}
```

### `POST /train`
Inicia entrenamiento de modelo ML.

**Body:**
```json
{
  "candles": 15000,
  "symbols": 50,
  "verbose": true
}
```

**Respuesta:**
```json
{
  "status": "success",
  "data": {
    "success": true,
    "job_id": "train_1705312200",
    "message": "ML training started successfully"
  }
}
```

### `GET /status`
Obtiene estado del entrenamiento actual.

**Respuesta:**
```json
{
  "status": "success",
  "data": {
    "status": "running",
    "progress": 65,
    "current_symbol": "BTCUSDT",
    "symbols_processed": 32,
    "total_symbols": 50,
    "start_time": "2024-01-15T09:30:00Z"
  }
}
```

### `GET /logs`
Obtiene logs recientes del entrenamiento.

### `GET /model`
Obtiene información del modelo entrenado.

## 🎮 Comandos de Telegram

Una vez configurado, el bot principal tendrá estos comandos:

### `/ml_train`
Inicia entrenamiento ML en Railway.

### `/ml_status`
Verifica estado del entrenamiento actual.

### `/ml_logs`
Muestra logs recientes del entrenamiento.

## ⚙️ Configuración

### Recursos Recomendados en Railway
- **RAM:** 2GB mínimo (4GB recomendado)
- **CPU:** 1 vCPU mínimo (2 vCPU recomendado)
- **Disco:** 5GB mínimo

### Variables de Entorno
```bash
# Requeridas
BINANCE_API_KEY=tu_api_key_aqui
BINANCE_API_SECRET=tu_api_secret_aqui

# Opcionales
ALPHA_VANTAGE_API_KEY=fallback_api_key
LOG_LEVEL=INFO|DEBUG|WARNING
TRAINING_ENV=railway

# Bot principal
RAILWAY_ML_URL=https://tu-servicio.up.railway.app
```

## 📊 Monitoreo y Troubleshooting

### Verificar Estado del Servicio
```bash
# Health check
curl https://tu-servicio.up.railway.app/health

# Ver logs de Railway
railway logs
```

### Problemas Comunes

#### ❌ "Model not found"
- Verifica que `nexus_system/memory_archives/` exista
- Modelo se crea después del primer entrenamiento exitoso

#### ❌ "API Key missing"
- Configura variables de entorno en Railway
- Reinicia el servicio después de cambios

#### ❌ "Memory limit exceeded"
- Aumenta RAM del servicio (4GB recomendado)
- Reduce `symbols` en configuración de entrenamiento

#### ❌ "Training timeout"
- Entrenamientos largos (>30min) pueden ser terminados por Railway
- Considera entrenamientos más pequeños o upgrades de plan

## 🔧 Desarrollo Local

Para desarrollo local antes del despliegue:

```bash
# Instalar dependencias
pip install -r requirements-railway.txt

# Ejecutar servicio localmente
python railway_ml_train.py

# Probar API
curl http://localhost:8000/health
```

## 📈 Costos Estimados

### Railway Hobby Plan (~$5/mes)
- ✅ 512MB RAM, 1 vCPU
- ⚠️ Puede ser limitado para entrenamientos grandes
- 💡 Recomendado para testing

### Railway Pro Plan (~$10/mes)
- ✅ 4GB RAM, 2 vCPU, 10GB disco
- ✅ Ideal para entrenamientos completos
- 💡 Recomendado para producción

## 🎯 Próximos Pasos

1. **Testing:** Probar con datasets pequeños primero
2. **Optimización:** Ajustar configuración para mejor performance
3. **Automatización:** Programar re-entrenamientos periódicos
4. **Backup:** Implementar backup automático de modelos

## 📞 Soporte

Para problemas específicos:
1. Revisa logs de Railway: `railway logs`
2. Verifica variables de entorno: `railway variables`
3. Test API endpoints individualmente
4. Contacta soporte de Railway si es problema de infraestructura

---

**Estado:** 🚀 Listo para producción
**Última actualización:** Enero 2025
**Versión:** v1.0.0
