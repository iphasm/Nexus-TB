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

# 🐳 Despliegue en Railway con Docker

## 🎯 OPCIONES DE DESPLIEGUE

### **Opción A: Proyecto Dedicado (Recomendado para testing)**
Crear un proyecto completamente separado solo para ML training.
- ✅ Aislamiento completo
- ✅ Costos separados
- ✅ Reinicio independiente
- ✅ Configuración más simple

### **Opción B: Servicio Paralelo (Recomendado para producción)**
Agregar el servicio ML a tu proyecto existente del bot.
- ✅ Costos compartidos
- ✅ Gestión unificada
- ✅ Comunicación interna más fácil
- ✅ Monitoreo centralizado

---

## 🚀 PASO A PASO: Configuración Completa

### **ESCENARIO 1: Agregar a Proyecto Existente (Más Común)**

#### **PASO 1: Verificar Railway CLI**
```bash
railway --version
railway whoami  # Verificar login
```

#### **PASO 2: Linkear al proyecto existente**
```bash
# Si tienes el project ID específico:
railway link -p 7674fd20-f218-4ff2-aa5d-427994c7ff70

# O seleccionar interactivamente:
railway link
```

#### **PASO 3: Agregar servicio ML**
```bash
python add_ml_service_to_railway.py
```

#### **PASO 4: Configurar variables de entorno**
En Railway Dashboard → Tu proyecto → Variables:
```
BINANCE_API_KEY=tu_api_key_real
BINANCE_API_SECRET=tu_secret_real
ALPHA_VANTAGE_API_KEY=tu_alpha_key_opcional
```

#### **PASO 5: Obtener URL del servicio ML**
```bash
railway domain --service ml-training
```

#### **PASO 6: Configurar bot principal**
```bash
export RAILWAY_ML_URL="https://tu-servicio-ml.up.railway.app"
```

---

### **ESCENARIO 2: Proyecto Dedicado Nuevo**

### **PASO 1: Preparación del Entorno**
```bash
# 1. Instalar Railway CLI
npm install -g @railway/cli

# 2. Login en Railway
railway login

# 3. Verificar instalación
railway --version
docker --version
```

### **PASO 2: Configurar Proyecto Railway**
```bash
# 1. Inicializar proyecto Railway
railway init --name nexus-ml-training-docker

# 2. Linkear al proyecto (si ya existe)
railway link

# 3. Verificar estado
railway status
```

### **PASO 3: Configurar Variables de Entorno**
```bash
# Variables requeridas (configurar UNA POR UNA)
railway variables set BINANCE_API_KEY="tu_binance_api_key_aqui"
railway variables set BINANCE_API_SECRET="tu_binance_secret_aqui"
railway variables set ALPHA_VANTAGE_API_KEY="tu_alpha_vantage_key"  # Opcional
railway variables set PYTHONUNBUFFERED="1"
railway variables set LOG_LEVEL="INFO"
railway variables set TRAINING_ENV="railway"
railway variables set PORT="8000"
```

### **PASO 4: Verificar Archivos de Configuración**
Asegúrate de que estos archivos existan en tu directorio:
```
✅ Dockerfile.railway     (Dockerfile optimizado)
✅ railway_ml_train.py    (Servicio Flask ML)
✅ requirements-railway.txt (Dependencias Python)
✅ railway-ml.json        (Configuración Railway)
✅ .dockerignore         (Optimización build)
```

### **PASO 5: Construir y Desplegar**
```bash
# Opción A: Deployment automático (recomendado)
python setup_railway_docker.py

# Opción B: Deployment manual
railway up --service railway-ml
```

### **PASO 6: Verificar Deployment**
```bash
# 1. Verificar logs del build
railway logs

# 2. Obtener URL del servicio
railway domain
# Output: https://nexus-ml-training-docker.up.railway.app

# 3. Probar health check
curl https://tu-url.up.railway.app/health
```

### **PASO 7: Probar Servicio Completo**
```bash
# Opción A: Test automático
python setup_railway_docker.py --test-only

# Opción B: Test manual con Docker local
docker build -f Dockerfile.railway -t ml-test .
docker run -p 8000:8000 -e BINANCE_API_KEY=test ml-test
curl http://localhost:8000/health
```

### **PASO 8: Configurar Bot Principal**
```bash
# 1. Obtener la URL del servicio Railway
railway domain
# Ejemplo: https://nexus-ml-training-docker.up.railway.app

# 2. Configurar en tu bot principal
export RAILWAY_ML_URL="https://nexus-ml-training-docker.up.railway.app"

# 3. Reiniciar tu bot para que tome la nueva configuración
```

### **PASO 9: Probar Integración Completa**
```telegram
# En Telegram, probar los comandos:
/ml_train     # Inicia entrenamiento
/ml_status    # Verifica progreso
/ml_logs      # Revisa logs
```

## 🧪 Testing y Desarrollo Local

### **Desarrollo Local con Docker Compose**
```bash
# 1. Construir y ejecutar localmente
docker-compose -f docker-compose.railway.yml up --build

# 2. Probar con cliente de test
docker-compose -f docker-compose.railway.yml --profile test up

# 3. Acceder al servicio
curl http://localhost:8000/health
```

### **Debugging del Contenedor**
```bash
# Ver logs del contenedor
docker logs <container_id>

# Acceder al contenedor
docker exec -it <container_id> bash

# Verificar instalación de dependencias
docker exec -it <container_id> pip list
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

### **Problemas Específicos de Docker**

#### ❌ "Docker build fails - no space left on device"
```bash
# Limpiar Docker system
docker system prune -a --volumes

# Verificar espacio en disco
df -h

# Usar Docker buildkit para builds más eficientes
export DOCKER_BUILDKIT=1
```

#### ❌ "Container exits immediately"
```bash
# Verificar logs del contenedor
docker logs <container_id>

# Ejecutar en modo interactivo para debug
docker run -it --entrypoint bash railway-ml-training

# Verificar que railway_ml_train.py existe y es ejecutable
ls -la railway_ml_train.py
```

#### ❌ "Import errors in container"
```bash
# Verificar instalación de dependencias
docker exec -it <container_id> pip list

# Verificar PYTHONPATH
docker exec -it <container_id> env | grep PYTHON

# Acceder al container para debugging
docker exec -it <container_id> bash
cd /app && python -c "import sys; print(sys.path)"
```

#### ❌ "Railway build fails with Docker"
```bash
# Verificar Dockerfile.railway localmente
docker build -f Dockerfile.railway -t test-build .

# Revisar logs de Railway
railway logs

# Verificar que .dockerignore no excluya archivos necesarios
cat .dockerignore
```

#### ❌ "Memory issues during training"
```bash
# Verificar límites de memoria del contenedor
docker stats <container_id>

# En Railway, upgrade a plan con más RAM
# Hobby (512MB) → Pro (4GB+)
```

#### ❌ "Network issues in container"
```bash
# Probar conectividad desde el contenedor
docker exec -it <container_id> curl -I https://api.binance.com

# Verificar DNS resolution
docker exec -it <container_id> nslookup api.binance.com

# Verificar variables de proxy
docker exec -it <container_id> env | grep -i proxy
```

### **Comandos Útiles para Debugging**

```bash
# Ver estado del proyecto Railway
railway status
railway services
railway variables

# Debug Docker local
docker build --no-cache -f Dockerfile.railway -t debug-build .
docker run --rm -it debug-build bash

# Verificar archivos incluidos en build
tar -tzf <(docker save railway-ml-training) | head -20

# Monitoreo de recursos
docker stats
railway logs --follow
```

### **Configuración de Troubleshooting**

#### **Variables de Debug**
```bash
# Agregar estas variables para más logging
railway variables set LOG_LEVEL=DEBUG
railway variables set PYTHONUNBUFFERED=1
railway variables set TRAINING_ENV=railway-debug
```

#### **Health Checks Avanzados**
```bash
# Test específico de dependencias
curl https://tu-servicio.up.railway.app/health

# Test de capacidad de entrenamiento
curl -X POST https://tu-servicio.up.railway.app/train \
  -H "Content-Type: application/json" \
  -d '{"candles": 100, "symbols": 1}'
```

## 🔧 Desarrollo Local

### **Opción A: Desarrollo Nativo**
```bash
# Instalar dependencias
pip install -r requirements-railway.txt

# Ejecutar servicio localmente
python railway_ml_train.py

# Probar API
curl http://localhost:8000/health
```

### **Opción B: Desarrollo con Docker**
```bash
# Construir imagen
docker build -f Dockerfile.railway -t railway-ml-dev .

# Ejecutar contenedor
docker run -p 8000:8000 \
  -e BINANCE_API_KEY=tu_key \
  -e BINANCE_API_SECRET=tu_secret \
  railway-ml-dev

# Probar
curl http://localhost:8000/health
```

### **Opción C: Desarrollo con Docker Compose**
```bash
# Ejecutar stack completo
docker-compose -f docker-compose.railway.yml up --build

# Ejecutar con testing
docker-compose -f docker-compose.railway.yml --profile test up --build
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
