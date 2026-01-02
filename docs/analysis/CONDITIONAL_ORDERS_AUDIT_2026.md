# Informe: Auditoría de Órdenes Condicionales (SL/TP/Trailing) — Binance & Bybit (2026)

## Contexto
Actualmente el bot genera señales y, en **modo PILOT**, intenta ejecutar entradas y colocar protección mediante:

- **`servos/trading_manager.py` (`AsyncTradingSession`)**: calcula tamaño, SL/TP, ejecuta entrada y coloca órdenes condicionales.
- **`nexus_system/core/nexus_bridge.py` (`NexusBridge`)**: enruta operaciones a adapters.
- **Adapters**:
  - **Binance**: `nexus_system/uplink/adapters/binance_adapter.py` (CCXT `binanceusdm`)
  - **Bybit**: `nexus_system/uplink/adapters/bybit_adapter.py` (CCXT `bybit` + endpoint privado V5 `position/trading-stop`)
- **Dispatcher**: `nexus_loader.py` decide `target_exchange`, aplica cooldown y hace un `check_liquidity()` antes de ejecutar en PILOT.

El objetivo de esta auditoría es **cerrar el tema de SL/TP/Trailing Stop**, garantizando que:

- Toda operación (manual/automática) coloque **SL, TP y Trailing Stop** en el exchange correcto.
- La verificación de balance se haga contra el **capital disponible** real (no “equity” ni “buying power” inflado) y en el **exchange correcto**.
- El sistema sea **determinista**: una vez elegido `target_exchange`, *todas* las llamadas de trading/órdenes usan ese exchange.

---

## Hallazgos principales (Root Cause)

### 1) Inconsistencia crítica: “target_exchange” se calcula, pero NO se usa en todas las llamadas
En `nexus_loader.py` se determina `target_exchange` antes de ejecutar, pero luego:

- `session.check_liquidity(symbol)` se llama **sin** pasar `target_exchange`.
- `session.execute_long_position(...)` / `execute_short_position(...)` se llaman **sin** forzar el exchange ya elegido.

Dentro de `AsyncTradingSession` ocurre lo mismo:

- `bridge.set_leverage(...)` no recibe exchange → vuelve a enrutar.
- `bridge.place_order(...)` para entrada y para SL/TP vuelve a enrutar.
- `get_symbol_info` y `get_last_price` vuelven a enrutar.

**Impacto**:
- Se ejecuta entrada en un exchange y la protección (SL/TP) se intenta poner en otro.
- Se fuerza “WATCHER por bajo saldo” revisando balance en Binance (0) aunque el trade iba a Bybit (83 USDT).
- Se registran operaciones con `exchange=target_exchange` aunque la orden real pudo haber ido a otro exchange.

### 2) `NexusBridge` no es “exchange-aware” para órdenes/consultas de órdenes
Métodos como:

- `get_open_orders(symbol)`
- `cancel_orders(symbol)`
- `get_symbol_info(symbol)`
- `get_last_price(symbol)`
- `set_leverage(symbol, leverage)`

usan `_route_symbol(symbol)` internamente si no se especifica exchange.

**Impacto**:
En multi-exchange, es fácil consultar/cancelar/actualizar órdenes en el exchange equivocado, especialmente para SL/TP/Trailing.

### 3) Binance: Trailing Stop está mal parametrizado (usa `stopPrice` para todo)
En `binance_adapter.py`, el flujo de órdenes condicionales fuerza `params['stopPrice']=...` incluso para `TRAILING_STOP_MARKET`.

En Binance Futures, el trailing nativo requiere típicamente:

- `callbackRate` (porcentaje 0.1–5.0)
- `activationPrice` (opcional pero muy recomendado)

**Impacto**:
Trailing stop falla o es rechazado (o se crea de forma incorrecta).

### 4) Bybit: el flujo actual mezcla 2 mecanismos y el tipo de orden condicional es frágil
`bybit_adapter.py` tiene:

- `set_trading_stop()` (endpoint V5 `position/trading-stop`) — es el mecanismo más confiable para “protección por posición”.
- lógica en `place_order()` para STOP/TP condicionales que usa strings tipo `StopLoss`/`TakeProfit` (no siempre compatibles con CCXT unificado).
- `place_trailing_stop()` que usa `trailingStop` como si fuera porcentaje (en Bybit suele ser **distancia** en precio), y no se integra de forma consistente con el flujo principal.

**Impacto**:
SL/TP/Trailing en Bybit puede:
- no colocarse,
- colocarse con parámetros inválidos,
- colocarse en el exchange incorrecto por re-enrutamiento.

### 5) Dependencias no fijadas (especialmente `ccxt`)
`requirements.txt` no fija versión de `ccxt`. CCXT cambia con frecuencia:

- nombres/tipos de órdenes,
- mapping de parámetros (stopPrice vs triggerPrice vs activePrice),
- soporte de endpoints privados.

**Impacto**:
Un deploy en Railway puede cambiar comportamiento sin cambios en tu repo → “funcionaba ayer, hoy no”.

---

## Recomendación de corrección (arquitectura mínima y robusta)

### Principio A: Determinismo de exchange (source-of-truth)
Una vez calculado `target_exchange` para un símbolo/usuario:

- **todas** las llamadas posteriores deben usar ese exchange explícitamente.
- las protecciones deben colocarse **en el mismo exchange donde está la posición**.

### Principio B: Protección por “Position Protection Layer”
Crear un flujo único post-entrada:

- **Paso 1**: Entry fill
- **Paso 2**: Colocar protección (SL/TP/Trailing)
- **Paso 3**: Verificar protección (read-back) y reintentar si faltan piezas

### Principio C: Diferenciar trailing por exchange
No intentar “una sola implementación” para ambos exchanges; el trailing nativo es distinto:

- **Binance**: `TRAILING_STOP_MARKET` con `callbackRate` + `activationPrice`.
- **Bybit**: preferir `position/trading-stop` con `trailingStop` + `activePrice` (y/o órdenes condicionales CCXT correctas).

---

## Pseudocódigo propuesto (corrección estructurada)

### 1) Dispatcher (nexus_loader) — “decidir una vez”

```python
target_exchange = bridge.route_symbol(symbol, user_exchange_prefs)

# 1) Balance check DEBE usar target_exchange
ok, avail, msg = session.check_liquidity(symbol, exchange=target_exchange)
if not ok:
    send_signal_as_watcher(...)
    return

# 2) PILOT execution DEBE forzar el mismo exchange
if side == "LONG":
    session.execute_long_position(symbol, atr=atr, strategy=strategy, force_exchange=target_exchange)
else:
    session.execute_short_position(symbol, atr=atr, strategy=strategy, force_exchange=target_exchange)
```

### 2) Ejecución (AsyncTradingSession) — “entry + protection”

```python
def execute_position(symbol, side, force_exchange):
    exchange = force_exchange or route(symbol, prefs)

    # A) Pre-trade
    sync_balance(exchange)
    sync_positions(exchange)  # opcional

    # B) Tamaño y parámetros
    price = bridge.get_last_price(symbol, exchange=exchange)
    prec = bridge.get_symbol_info(symbol, exchange=exchange)
    qty = compute_size(..., exchange_balance_available, prec)

    # C) Entry
    bridge.set_leverage(symbol, leverage, exchange=exchange)
    entry = bridge.place_order(symbol, entry_side, "MARKET", qty, exchange=exchange)
    entry_price = entry.fill_price

    # D) Protección (siempre, para manual/auto)
    protection = build_protection_plan(entry_price, side, prec, config)
    apply_protection(exchange, symbol, side, qty, protection)

    # E) Verificación y reintentos
    verify = verify_protection(exchange, symbol, expected=protection)
    if not verify.ok:
        retry_apply_protection(...)
        if still not ok:
            alert_admin_or_user("Protección incompleta", details)

    return ok
```

### 3) Protección por exchange

```python
def apply_protection(exchange, symbol, side, qty, protection):
    cancel_existing_protection(exchange, symbol)

    if exchange == "BINANCE":
        # SL: STOP_MARKET (reduceOnly)
        place_order(symbol, close_side(side), "STOP_MARKET",
                    qty, stopPrice=protection.sl, reduceOnly=True,
                    exchange="BINANCE")

        # TP: TAKE_PROFIT_MARKET (reduceOnly)
        place_order(symbol, close_side(side), "TAKE_PROFIT_MARKET",
                    qty, stopPrice=protection.tp, reduceOnly=True,
                    exchange="BINANCE")

        # Trailing: TRAILING_STOP_MARKET (reduceOnly) con activationPrice/callbackRate
        place_order(symbol, close_side(side), "TRAILING_STOP_MARKET",
                    protection.trailing_qty, activationPrice=protection.trailing_activation,
                    callbackRate=protection.trailing_pct, reduceOnly=True,
                    exchange="BINANCE")

    elif exchange == "BYBIT":
        # Opción robusta: position/trading-stop
        bybit.set_trading_stop(symbol,
                               stop_loss=protection.sl,
                               take_profit=protection.tp,
                               trailing_stop=protection.trailing_distance,
                               activation_price=protection.trailing_activation)

        # Alternativa (si se requiere split qty):
        # - TP parcial con take_profit_market reduceOnly
        # - trailing_stop_market con trailingStop(distance) + activePrice
```

---

## Acciones concretas recomendadas (orden de implementación)

1. **Exchange determinista**: agregar `exchange` opcional a métodos del bridge (y usarlo desde `nexus_loader` y `trading_manager`).
2. **Bybit protección**: estandarizar SL/TP/Trailing usando `position/trading-stop` o, si se requiere split, implementar órdenes condicionales CCXT correctamente (triggerPrice/activePrice + reduceOnly).
3. **Binance trailing stop**: corregir `TRAILING_STOP_MARKET` usando `activationPrice` + `callbackRate`.
4. **Verificación post-colocación**: leer `open_orders` y confirmar que SL/TP/Trailing están presentes; reintentar si no.
5. **Pinning**: fijar versión de `ccxt` (y aiogram) para Railway, con una matriz de compatibilidad probada.

---

## Nota de infraestructura (Railway)

- Railway usa `Dockerfile` y ejecuta `python nexus_loader.py`.
- `requirements.txt` instala `ccxt` sin versión → se recomienda fijar versión en producción.


