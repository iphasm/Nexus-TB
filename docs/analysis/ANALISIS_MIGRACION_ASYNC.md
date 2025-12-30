# Análisis de Migración: Síncrono → Asíncrono, REST → WebSocket, Arquitectura Modular

## Fecha: 2024-12-29

## Resumen Ejecutivo

Se identificaron **7 áreas críticas** que requieren migración completa de código síncrono a asíncrono, eliminación de REST APIs en favor de WebSockets, y optimización de la arquitectura modular.

---

## 1. PROBLEMAS CRÍTICOS ENCONTRADOS

### 1.1 ❌ `strategies/shark_mode.py` - Threading Síncrono
**Estado**: ❌ CRÍTICO - Usa `threading.Thread`, `requests.get()`, `time.sleep()`, `ThreadPoolExecutor`

**Problemas**:
- Usa `threading.Thread` en lugar de `asyncio.Task`
- `requests.get()` bloquea el event loop
- `time.sleep()` bloquea en lugar de `asyncio.sleep()`
- `ThreadPoolExecutor` para operaciones que deberían ser async
- Hardcoded: `url = "https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT"`
- Hardcoded: `timeout=5`, `max_workers=10`
- Hardcoded fallback: `['1000PEPEUSDT', 'SOLUSDT', 'WIFUSDT', 'RENDERUSDT', 'SUIUSDT']`

**Impacto**: 
- Bloquea el event loop principal
- No se integra con el sistema async del bot
- No puede usar WebSocket para precios en tiempo real

**Solución**: Migrar completamente a async usando `asyncio`, `aiohttp`, y WebSocket para precios

---

### 1.2 ❌ `servos/fetcher.py` - Binance Client Síncrono
**Estado**: ❌ CRÍTICO - Usa `binance.client.Client` síncrono

**Problemas**:
- Usa `binance.client.Client` (síncrono) en lugar de CCXT async
- No usa WebSocket para datos en tiempo real
- Duplica funcionalidad que ya existe en `nexus_system/uplink/stream.py`

**Impacto**:
- Bloquea cuando se llama desde código async
- No aprovecha WebSocket para datos en tiempo real
- Código duplicado

**Solución**: 
- Eliminar este módulo o convertirlo en wrapper async
- Usar `nexus_system/uplink/stream.py` que ya tiene WebSocket + REST fallback

---

### 1.3 ❌ `servos/diagnostics.py` - Requests Síncrono
**Estado**: ⚠️ MEDIO - Usa `requests.get()` síncrono

**Problemas**:
- `requests.get()` bloquea el event loop
- Hardcoded: `timeout=5`, `timeout=10`
- Hardcoded: `symbol='BTCUSDT'`, `symbol="TSLA"`

**Impacto**: 
- Bloquea cuando se ejecuta desde handlers async
- Ya se ejecuta en `run_in_executor` pero debería ser nativo async

**Solución**: Migrar a `aiohttp` async

---

### 1.4 ❌ `servos/db.py` - PostgreSQL Síncrono
**Estado**: ⚠️ MEDIO - Usa `psycopg2` síncrono

**Problemas**:
- `psycopg2` es síncrono y bloquea
- Todas las funciones son síncronas: `get_connection()`, `init_db()`, `load_all_sessions()`, etc.
- Se ejecuta en `run_in_executor` pero debería ser nativo async

**Impacto**: 
- Bloquea el event loop cuando se ejecuta
- No aprovecha conexiones async de PostgreSQL

**Solución**: Migrar a `asyncpg` para PostgreSQL async nativo

---

### 1.5 ❌ `servos/notifier.py` - Requests Síncrono
**Estado**: ⚠️ MEDIO - Usa `requests.post()` síncrono

**Problemas**:
- `requests.post()` bloquea el event loop
- Hardcoded: `timeout=10`
- No es async

**Impacto**: 
- Bloquea cuando se envía notificación desde código async

**Solución**: Migrar a `aiohttp` async

---

### 1.6 ⚠️ Hardcodes Problemáticos

**Encontrados en múltiples archivos**:

1. **URLs Hardcodeadas**:
   - `strategies/shark_mode.py`: `"https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT"`
   - `servos/diagnostics.py`: `"https://api.ipify.org?format=json"`, `"http://ip-api.com/json/{ip_addr}"`
   - `servos/notifier.py`: `f"https://api.telegram.org/bot{token}/sendMessage"`

2. **Timeouts Hardcodeados**:
   - `timeout=5`, `timeout=10` en múltiples lugares
   - Deberían estar en `system_directive.py` o config

3. **Símbolos Hardcodeados**:
   - `strategies/shark_mode.py`: Fallback `['1000PEPEUSDT', 'SOLUSDT', 'WIFUSDT', 'RENDERUSDT', 'SUIUSDT']`
   - `servos/diagnostics.py`: `'BTCUSDT'`, `"TSLA"`

4. **Configuración Hardcodeada**:
   - `strategies/shark_mode.py`: `max_workers=10`, `window_seconds=60`, `crash_threshold_pct=3.0`
   - `servos/diagnostics.py`: `interval='15m'`, `limit=1`, `limit=250`

**Solución**: Mover todos a `system_directive.py` o archivo de configuración

---

### 1.7 ⚠️ Distribución de Módulos

**Problemas Identificados**:

1. **Duplicación de Funcionalidad**:
   - `servos/fetcher.py` duplica `nexus_system/uplink/stream.py`
   - Ambos hacen fetch de datos de mercado

2. **Dependencias Circulares Potenciales**:
   - `strategies/shark_mode.py` importa `system_directive` dentro de funciones
   - `servos/diagnostics.py` importa `servos/fetcher.py` y `strategies/engine.py`

3. **Responsabilidades Mezcladas**:
   - `servos/fetcher.py` tiene lógica de cálculo de ATR que debería estar en `servos/indicators.py`
   - `strategies/shark_mode.py` tiene lógica de notificación que debería estar en `servos/notifier.py`

**Solución**: 
- Consolidar `servos/fetcher.py` en `nexus_system/uplink/stream.py`
- Mover cálculos de indicadores a módulos apropiados
- Separar responsabilidades claramente

---

## 2. PLAN DE CORRECCIÓN

### Fase 1: Migración Crítica (Prioridad Alta)
1. ✅ Migrar `strategies/shark_mode.py` a async completo
2. ✅ Migrar `servos/notifier.py` a async
3. ✅ Eliminar o migrar `servos/fetcher.py`

### Fase 2: Migración Media (Prioridad Media)
4. ⏳ Migrar `servos/diagnostics.py` a async
5. ⏳ Migrar `servos/db.py` a asyncpg

### Fase 3: Limpieza y Optimización (Prioridad Baja)
6. ⏳ Eliminar hardcodes y mover a configuración
7. ⏳ Reorganizar distribución de módulos
8. ⏳ Eliminar dependencias circulares

---

## 3. ARCHIVOS A MODIFICAR

### Archivos Críticos (Requieren Cambios Inmediatos)
1. `strategies/shark_mode.py` - Migración completa a async
2. `servos/notifier.py` - Migración a aiohttp
3. `servos/fetcher.py` - Eliminar o convertir a wrapper async

### Archivos Medios (Mejoras Importantes)
4. `servos/diagnostics.py` - Migración a aiohttp
5. `servos/db.py` - Migración a asyncpg

### Archivos de Configuración (Limpieza)
6. `system_directive.py` - Agregar constantes para timeouts, URLs, etc.

### Archivos que Usan los Módulos (Actualización)
7. `nexus_loader.py` - Actualizar uso de shark_mode
8. `handlers/commands.py` - Actualizar uso de diagnostics

---

## 4. MÉTRICAS DE ÉXITO

- ✅ 0 funciones síncronas bloqueantes en código principal
- ✅ 0 usos de `requests` en favor de `aiohttp`
- ✅ 0 usos de `threading.Thread` en favor de `asyncio.Task`
- ✅ 0 hardcodes de URLs, timeouts, símbolos
- ✅ 0 duplicación de funcionalidad entre módulos
- ✅ 0 dependencias circulares

---

## 5. NOTAS DE IMPLEMENTACIÓN

### Para `strategies/shark_mode.py`:
- Convertir `SharkSentinel(threading.Thread)` a clase async con `asyncio.Task`
- Reemplazar `requests.get()` con `aiohttp` o usar WebSocket de `MarketStream`
- Reemplazar `time.sleep()` con `asyncio.sleep()`
- Reemplazar `ThreadPoolExecutor` con `asyncio.gather()` o `asyncio.create_task()`
- Mover configuración a `system_directive.py`

### Para `servos/notifier.py`:
- Convertir a función async
- Usar `aiohttp.ClientSession()` en lugar de `requests.post()`
- Mover timeout a configuración

### Para `servos/fetcher.py`:
- Opción 1: Eliminar completamente y usar `nexus_system/uplink/stream.py`
- Opción 2: Convertir a wrapper async que llama a `MarketStream`

### Para `servos/db.py`:
- Migrar a `asyncpg` para PostgreSQL async nativo
- Convertir todas las funciones a async
- Usar connection pooling async

---

## 6. RIESGOS Y CONSIDERACIONES

### Riesgos:
1. **Breaking Changes**: Cambios en interfaces pueden romper código existente
2. **Testing**: Necesario probar todas las funciones migradas
3. **Performance**: Async puede tener overhead en operaciones CPU-bound

### Mitigación:
1. Mantener compatibilidad hacia atrás donde sea posible
2. Testing exhaustivo antes de deploy
3. Usar `run_in_executor` para operaciones CPU-bound si es necesario

---

## CONCLUSIÓN

La migración es **necesaria y urgente** para:
- Mejorar rendimiento y escalabilidad
- Eliminar bloqueos del event loop
- Aprovechar WebSocket para datos en tiempo real
- Mantener código limpio y mantenible

**Prioridad**: ALTA para archivos críticos, MEDIA para el resto.

