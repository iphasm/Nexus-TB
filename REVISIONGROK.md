# Solicitud de Revisión de Código: Órdenes Condicionales

## Contexto
Se realizaron correcciones críticas al sistema de colocación de órdenes condicionales (Stop Loss, Take Profit, Trailing Stop) para los exchanges Binance y Bybit. Necesito que revises estos cambios para validar su correctitud.

---

## Archivos a Revisar

### 1. bybit_adapter.py
**Ruta:** `nexus_system/uplink/adapters/bybit_adapter.py`
**Función:** `place_order` (órdenes condicionales + trailing)

**Cambios realizados:**
- Se corrigió la lógica de `triggerDirection` para TAKE_PROFIT y TRAILING_STOP
- Se añadió parámetro `tpslMode = 'Partial'`
- **Fix crítico:** `TRAILING_STOP_MARKET` ahora se coloca como orden nativa `trailing_stop_market`
  - `callbackRate` se interpreta como **%** (igual que Binance) y se convierte a **distancia**: `dist = activationPrice * (callbackRate/100)`
  - se envía `trailingStop=dist` y `activePrice=activationPrice`
  - se evita enviar `triggerPrice=None` (causaba 110092/110093)

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

Trailing Stop:
  - Para Bybit, se usa orden nativa `trailing_stop_market` con `trailingStop` (DISTANCIA) y `activePrice` (activación).
  - NO aplica `triggerDirection/triggerPrice` en este modo.
```

**Código actual a validar:**
```python
if 'STOP' in order_type_upper and 'TAKE_PROFIT' not in order_type_upper:
    params['triggerDirection'] = 2 if side.upper() == 'SELL' else 1
    params['tpslMode'] = 'Partial'
elif 'TAKE_PROFIT' in order_type_upper:
    params['triggerDirection'] = 1 if side.upper() == 'SELL' else 2
    params['tpslMode'] = 'Partial'

# TRAILING_STOP_MARKET (Bybit):
# trailing_distance = activationPrice * (callbackRatePct/100)
# create_order(type='trailing_stop_market',
#              params={'trailingStop': trailing_distance, 'activePrice': activationPrice, 'reduceOnly': True})
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
3. **Fix crítico (multi-exchange):** `_set_protection_binance()` ahora fuerza `exchange="BINANCE"` en `place_order()` (evita misrouting por `_route_symbol`)
4. **Fix crítico (cancelación):** `cancel_protection_orders()` cancela en el exchange explícito (BINANCE/BYBIT), no por routing
5. **Fix trailing:** soporta `trailing["pct"]` además de `trailing["callback_rate_pct"]`

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
    exchange="BINANCE",
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
- **Fix crítico:** `get_open_algo_orders()` ya no requiere `self.client` (funciona en BYBIT-only) y acepta `exchange=...`
- **Fix:** `smart_breakeven_check()` y `execute_refresh_all_orders()` actualizados a la nueva firma de precisión (tuple de 5 valores) y a operar en el exchange correcto

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

## Pseudocódigo (Implementación Final Recomendada)

### A) Capa común: aplicar protección en un exchange explícito
```text
function CLOSE_SIDE(positionSide):
    return "SELL" if positionSide == "LONG" else "BUY"

function APPLY_PROTECTION(symbol, exchange, positionSide, qty, sl, tp, trailing):
    # 1) Cancelar protección previa EN EL MISMO exchange (no routing)
    cancel_protection_orders(symbol, exchange)

    if exchange == "BINANCE":
        place_order(exchange="BINANCE", type="STOP_MARKET", side=CLOSE_SIDE(positionSide),
                   qty=qty, stopPrice=sl, reduceOnly=True, workingType="MARK_PRICE")
        place_order(exchange="BINANCE", type="TAKE_PROFIT_MARKET", side=CLOSE_SIDE(positionSide),
                   qty=qty, stopPrice=tp, reduceOnly=True, workingType="MARK_PRICE")

        if trailing enabled:
            place_order(exchange="BINANCE", type="TRAILING_STOP_MARKET", side=CLOSE_SIDE(positionSide),
                       qty=trailing.qty, activationPrice=trailing.activation_price,
                       callbackRatePct=trailing.pct, reduceOnly=True)

        verify (openOrders contains SL and TP)
        return ok

    if exchange == "BYBIT":
        # Preferir server-side trading-stop
        trailingDistance = trailing.activation_price * (trailing.pct/100)  # DISTANCIA
        res = set_trading_stop(stopLoss=sl, takeProfit=tp,
                               trailingStop=trailingDistance,
                               activePrice=trailing.activation_price)

        verify position.takeProfit/stopLoss applied
        if SL missing:
            place conditional STOP_MARKET with triggerPrice=sl and triggerDirection based on close_side
        if TP missing:
            place conditional TAKE_PROFIT_MARKET with triggerPrice=tp and triggerDirection based on close_side

        if trailing requested and not applied:
            place trailing_stop_market with trailingStop=trailingDistance and activePrice=activationPrice

        return ok
```

### B) Bybit `triggerDirection` (solo STOP/TP condicionales)
```text
close_side = CLOSE_SIDE(positionSide)

if orderType == "STOP_MARKET":
    triggerDirection = 2 if close_side == "SELL" else 1

if orderType == "TAKE_PROFIT_MARKET":
    triggerDirection = 1 if close_side == "SELL" else 2
```

## Preguntas para Validación

1. **Bybit triggerDirection:** ¿Es correcta la lógica para cada combinación de position side (LONG/SHORT) y order type **(SL/TP)**? (Trailing ahora usa `trailing_stop_market` nativo).

2. **Binance workingType:** ¿Es `MARK_PRICE` el valor correcto por defecto para órdenes de protección?

3. **Parámetros:** ¿El cambio de `price` a `stopPrice`/`activationPrice` es correcto según las APIs de ambos exchanges?

4. **Retry Logic:** ¿La verificación de órdenes existentes antes del retry previene efectivamente duplicados?

5. **tpslMode:** ¿Es correcto usar `'Partial'` para órdenes con cantidad específica en Bybit V5?

---

## Referencias API

- **Bybit V5 Create Order:** https://bybit-exchange.github.io/docs/v5/order/create-order
- **Binance Futures New Order:** https://developers.binance.com/docs/derivatives/usds-margined-futures/trade/rest-api/New-Order
