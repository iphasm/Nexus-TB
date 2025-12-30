# Análisis: Problema con `/sync` y Órdenes Condicionales de Binance

## Problema Identificado

El comando `/sync` está diseñado para borrar órdenes condicionales existentes y crear nuevas, pero nunca ha funcionado correctamente con Binance.

## Causas Principales

### 1. **Cambios en la API de Binance (Diciembre 2024)**
- **Antes**: Las órdenes condicionales (STOP_MARKET, TAKE_PROFIT_MARKET, TRAILING_STOP_MARKET) estaban en un servicio separado "Algo Orders" con endpoints específicos.
- **Después**: Binance migró las órdenes condicionales al endpoint regular de órdenes abiertas (`/fapi/v1/openOrders`).
- **Impacto**: El código que intenta usar endpoints de "Algo Orders" ya no es necesario o puede fallar.

### 2. **Limitaciones de CCXT `cancel_all_orders()`**
- CCXT `cancel_all_orders()` puede no cancelar correctamente las órdenes condicionales.
- En algunos casos, solo cancela órdenes estándar (LIMIT, MARKET) pero no las condicionales.
- Necesita cancelar cada orden condicional individualmente usando `cancel_order(order_id)`.

### 3. **Falta de Cancelación Individual**
- El código actual usa `bridge.cancel_orders()` que llama a `exchange.cancel_all_orders()`.
- Si `cancel_all_orders()` no funciona para órdenes condicionales, las órdenes no se cancelan.
- El resultado: se intentan crear nuevas órdenes mientras las antiguas siguen activas, causando duplicados o errores.

### 4. **Problema de Timing y Verificación**
- Incluso si la cancelación tiene éxito, puede haber un delay antes de que Binance actualice el estado.
- La verificación inmediata puede mostrar órdenes que aún no han sido procesadas como canceladas.
- Esto puede causar que el sync falle incorrectamente.

## Solución Propuesta

### Opción 1: Cancelación Individual (Recomendada)
1. Obtener todas las órdenes abiertas (incluyendo condicionales) usando `get_open_orders()`.
2. Filtrar las órdenes condicionales (STOP_MARKET, TAKE_PROFIT_MARKET, TRAILING_STOP_MARKET).
3. Cancelar cada orden condicional individualmente usando `cancel_order(order_id)`.
4. Verificar que todas las órdenes fueron canceladas antes de crear nuevas.

### Opción 2: Híbrida (cancel_all_orders + cancelación individual)
1. Intentar `cancel_all_orders()` primero.
2. Verificar si quedan órdenes condicionales.
3. Si quedan, cancelarlas individualmente.
4. Verificar nuevamente antes de crear nuevas órdenes.

### Opción 3: Usar API Directa de Binance (si CCXT falla)
1. Si CCXT no maneja correctamente las órdenes condicionales, usar la API directa de Binance.
2. Endpoint: `DELETE /fapi/v1/order` o `DELETE /fapi/v1/algo/order` (si aún está disponible).
3. Cancelar cada orden por su `orderId`.

## Cambios Necesarios en el Código

### Archivo: `nexus_system/uplink/adapters/binance_adapter.py`
- Mejorar `cancel_orders()` para cancelar órdenes condicionales individualmente.
- Agregar método `cancel_conditional_orders()` que cancela solo órdenes condicionales.

### Archivo: `servos/trading_manager.py`
- Mejorar `_cancel_all_robust()` para:
  1. Obtener todas las órdenes (incluyendo condicionales).
  2. Cancelar cada orden condicional individualmente.
  3. Verificar que todas fueron canceladas.
  4. Agregar retry logic con delays apropiados.

## Comparación con Bybit

Bybit tiene una ventaja aquí: su API permite cancelar todas las órdenes (incluyendo condicionales) con una sola llamada (`cancel_all_orders()`), mientras que Binance requiere cancelación individual o puede no funcionar correctamente con `cancel_all_orders()`.

## Próximos Pasos

1. Implementar cancelación individual de órdenes condicionales.
2. Agregar retry logic y delays apropiados.
3. Mejorar verificación post-cancelación.
4. Probar exhaustivamente con órdenes condicionales reales.

