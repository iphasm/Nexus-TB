# Health Checker Service

El servicio de health check permite a Railway monitorear el estado de salud de la aplicación Nexus Trading Bot.

## Endpoints Disponibles

### `/` - Información Básica
- **Método:** GET
- **Respuesta:** Información básica del servicio
- **Código:** Siempre 200 OK

```json
{
  "service": "Nexus Trading Bot",
  "status": "healthy",
  "version": "1.0.0",
  "uptime": "3600.5s"
}
```

### `/health` - Health Check Principal
- **Método:** GET
- **Uso:** Endpoint principal para Railway health checks
- **Respuesta:**
  - `200 OK` cuando el servicio está saludable
  - `503 Service Unavailable` cuando hay problemas

```json
{
  "service": "Nexus Trading Bot",
  "status": "healthy",
  "timestamp": "2024-01-05T22:00:00.000Z",
  "uptime_seconds": 3600.5,
  "version": "1.0.0",
  "components": {
    "telegram_bot": {
      "status": "healthy",
      "last_check": "2024-01-05T22:00:00.000Z"
    },
    "database": {
      "status": "healthy",
      "last_check": "2024-01-05T22:00:00.000Z"
    },
    "exchanges": {
      "status": "healthy",
      "last_check": "2024-01-05T22:00:00.000Z"
    },
    "nexus_core": {
      "status": "healthy",
      "last_check": "2024-01-05T22:00:00.000Z"
    }
  }
}
```

### `/health/detailed` - Health Check Detallado
- **Método:** GET
- **Respuesta:** Información completa de health check
- **Código:** Siempre 200 OK (para debugging)

### `/health/{component}` - Health Check por Componente
- **Método:** GET
- **Parámetros:** `component` - Nombre del componente
- **Respuesta:** Estado de un componente específico
- **Códigos:**
  - `200 OK` - Componente encontrado
  - `404 Not Found` - Componente no existe

**Componentes disponibles:**
- `telegram_bot`
- `database`
- `exchanges`
- `nexus_core`

## Estados de Salud

### Estado General del Servicio
- `healthy` - Todos los componentes funcionando correctamente
- `degraded` - Algunos componentes con problemas
- `starting` - Servicio iniciándose
- `unhealthy` - Servicio con problemas críticos

### Estado de Componentes
- `healthy` - Componente funcionando correctamente
- `unhealthy` - Componente con problemas
- `unknown` - Estado no determinado
- `disabled` - Componente deshabilitado

## Configuración en Railway

### railway.json
```json
{
  "deploy": {
    "healthcheckPath": "/health",
    "healthcheckTimeout": 30,
    "healthcheckInterval": 30
  }
}
```

### Variables de Entorno
- `PORT` - Puerto donde escuchar el servidor web (default: 8000 para Railway)

## Arquitectura

El health checker se ejecuta como un servidor web FastAPI concurrente con el bot de Telegram:

1. **Servidor Web:** FastAPI + Uvicorn en puerto configurable
2. **Bot de Telegram:** Aiogram ejecutándose concurrentemente
3. **Health Status:** Estado compartido entre ambos servicios

## Monitoreo

Railway automáticamente:
- Hace requests GET a `/health` cada 30 segundos
- Espera respuesta dentro de 30 segundos timeout
- Reinicia el servicio si recibe 503 o timeouts repetidos

## Actualización de Estados

El código puede actualizar el estado de salud usando las funciones del módulo:

```python
from servos.health_checker import update_health_status, mark_service_healthy

# Actualizar estado de componente
update_health_status("database", "unhealthy", {"error": "Connection failed"})

# Marcar servicio como saludable
mark_service_healthy()
```

## Logs

Los cambios de estado se registran automáticamente en los logs del servicio para debugging y monitoreo.
