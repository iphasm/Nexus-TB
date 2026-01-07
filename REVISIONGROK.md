# Solicitud de Revisión de Código: Órdenes Condicionales

## Contexto
Se realizaron correcciones críticas al sistema de colocación de órdenes condicionales (Stop Loss, Take Profit, Trailing Stop) para los exchanges Binance y Bybit. Necesito que revises estos cambios para validar su correctitud.

---

## Archivos a Revisar

### 1. bybit_adapter.py
**Ruta:** `nexus_system/uplink/adapters/bybit_adapter.py`
**Líneas:** 411-438 (función `place_order`)

**Cambios realizados:**
- Se corrigió la lógica de `triggerDirection` para TAKE_PROFIT y TRAILING_STOP
- Se añadió parámetro `tpslMode = 'Partial'`

**Validar según API Bybit V5:**
```
triggerDirection:
  1 = triggers when price RISES ABOVE triggerPrice
  2 = triggers when price FALLS BELOW triggerPrice

Para cerrar posición LONG (side=SELL):
  - SL: direction=2 (precio CAE debajo del stop)
  - TP: direction=1 (precio SUBE arriba del target)
  
Para cerrar posición SHORT (side=BUY):
  - SL: direction=1 (precio SUBE arriba del stop)
  - TP: direction=2 (precio CAE debajo del target)

Trailing Stop sigue la misma lógica que SL
```

**Código actual a validar:**
```python
if 'STOP' in order_type_upper and 'TAKE_PROFIT' not in order_type_upper:
    params['triggerDirection'] = 2 if side.upper() == 'SELL' else 1
    params['tpslMode'] = 'Partial'
elif 'TAKE_PROFIT' in order_type_upper:
    params['triggerDirection'] = 1 if side.upper() == 'SELL' else 2
    params['tpslMode'] = 'Partial'
elif 'TRAILING' in order_type_upper:
    params['triggerDirection'] = 2 if side.upper() == 'SELL' else 1
```

---

### 2. binance_adapter.py
**Ruta:** `nexus_system/uplink/adapters/binance_adapter.py`
**Líneas:** 465-469 (función `place_order`)

**Cambios realizados:**
- Se añadió `workingType = 'MARK_PRICE'` para órdenes condicionales

**Validar según API Binance Futures:**
```
workingType:
  - MARK_PRICE (default, recomendado para protección)
  - CONTRACT_PRICE (precio del contrato)
```

**Código actual a validar:**
```python
params['stopPrice'] = stop_price

if 'workingType' not in params:
    params['workingType'] = kwargs.get('workingType', 'MARK_PRICE')
```

---

### 3. nexus_bridge.py
**Ruta:** `nexus_system/core/nexus_bridge.py`
**Líneas:** 508-562, 571-577 (función `_set_protection_binance`)

**Cambios realizados:**
1. Cambio de `price=` a `stopPrice=` para SL/TP
2. Añadida verificación pre-retry para evitar órdenes duplicadas

**Código actual a validar:**
```python
# SL order
sl_res = await self.place_order(
    symbol=symbol,
    side=close_side,
    order_type="STOP_MARKET",
    quantity=qty,
    stopPrice=sl,  # <-- Antes era: price=sl
    reduceOnly=True,
    workingType=config.get("protection_trigger_by", "MARK_PRICE"),
)

# Retry logic con verificación de duplicados
if "ORDER_WOULD_IMMEDIATELY_TRIGGER" in error_msg:
    existing_orders = await self.get_open_orders(symbol, exchange="BINANCE")
    has_existing_sl = any(o.get('type', '').upper() in ['STOP_MARKET', 'STOP'] for o in existing_orders)
    if has_existing_sl:
        applied["sl"] = True  # Skip retry
    else:
        # Proceed with adjusted price retry
```

---

### 4. trading_manager.py
**Ruta:** `servos/trading_manager.py`
**Líneas:** 1187-1188, 1205-1206, 1479-1480, 1525-1526, 1540, 1558

**Cambios realizados:**
- Cambio de `price=` a `stopPrice=` para SL/TP
- Cambio de `price=` a `activationPrice=` para Trailing Stop

**Código actual a validar:**
```python
# Para SL
await self.bridge.place_order(
    symbol, order_side, 'STOP_MARKET', 
    quantity=qty, stopPrice=sl_price, reduceOnly=True
)

# Para TP
await self.bridge.place_order(
    symbol, order_side, 'TAKE_PROFIT_MARKET', 
    quantity=qty, stopPrice=tp_price, reduceOnly=True
)

# Para Trailing Stop
await self.bridge.place_order(
    symbol, order_side, 'TRAILING_STOP_MARKET',
    quantity=qty, activationPrice=activation,
    callbackRate=trailing_pct, reduceOnly=True
)
```

---

## Preguntas para Validación

1. **Bybit triggerDirection:** ¿Es correcta la lógica para cada combinación de position side (LONG/SHORT) y order type (SL/TP/Trailing)?

2. **Binance workingType:** ¿Es `MARK_PRICE` el valor correcto por defecto para órdenes de protección?

3. **Parámetros:** ¿El cambio de `price` a `stopPrice`/`activationPrice` es correcto según las APIs de ambos exchanges?

4. **Retry Logic:** ¿La verificación de órdenes existentes antes del retry previene efectivamente duplicados?

5. **tpslMode:** ¿Es correcto usar `'Partial'` para órdenes con cantidad específica en Bybit V5?

---

## Referencias API

- **Bybit V5 Create Order:** https://bybit-exchange.github.io/docs/v5/order/create-order
- **Binance Futures New Order:** https://developers.binance.com/docs/derivatives/usds-margined-futures/trade/rest-api/New-Order
