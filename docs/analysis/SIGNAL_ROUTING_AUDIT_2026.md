# 🔍 AUDITORÍA COMPLETA: Sistema de Señales y Enrutamiento a Exchanges
## Nexus Trading Bot - Enero 2026

---

## 📋 RESUMEN EJECUTIVO

Esta auditoría analiza el flujo completo desde la generación de señales hasta la ejecución de órdenes en modo PILOT para Binance y Bybit. Se identificaron **7 bugs críticos** y **5 problemas de diseño** que afectan la integridad del sistema.

---

## 🏗️ ARQUITECTURA ACTUAL

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           FLUJO DE SEÑALES                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  1. GENERACIÓN DE SEÑALES                                                   │
│     ┌─────────────┐    ┌──────────────┐    ┌────────────────┐              │
│     │ MarketStream│───>│ NexusCore    │───>│StrategyFactory │              │
│     │ (WebSocket) │    │ (engine.py)  │    │ (factory.py)   │              │
│     └─────────────┘    └──────────────┘    └────────────────┘              │
│           │                   │                    │                        │
│           v                   v                    v                        │
│     ┌─────────────┐    ┌──────────────┐    ┌────────────────┐              │
│     │ Candle Data │    │ Risk Manager │    │ ML/Rule-Based  │              │
│     │ (OHLCV)     │    │ (shield)     │    │ Classifier     │              │
│     └─────────────┘    └──────────────┘    └────────────────┘              │
│                               │                    │                        │
│                               v                    v                        │
│                        ┌──────────────────────────────┐                    │
│                        │        Signal Object         │                    │
│                        │ {symbol, action, confidence} │                    │
│                        └──────────────────────────────┘                    │
│                                      │                                      │
│  2. DESPACHO DE SEÑALES             v                                      │
│     ┌─────────────────────────────────────────────────┐                    │
│     │         dispatch_nexus_signal()                 │                    │
│     │         (nexus_loader.py:222)                   │                    │
│     └─────────────────────────────────────────────────┘                    │
│                         │                                                   │
│       ┌─────────────────┼─────────────────┐                                │
│       v                 v                 v                                │
│  ┌─────────┐      ┌─────────┐      ┌─────────┐                             │
│  │ WATCHER │      │ COPILOT │      │ PILOT   │                             │
│  │ (notify)│      │ (ask)   │      │(execute)│                             │
│  └─────────┘      └─────────┘      └─────────┘                             │
│                                          │                                  │
│  3. ENRUTAMIENTO Y EJECUCIÓN            v                                  │
│     ┌─────────────────────────────────────────────────┐                    │
│     │          AsyncTradingSession                    │                    │
│     │   execute_long_position() / execute_short_...   │                    │
│     └─────────────────────────────────────────────────┘                    │
│                         │                                                   │
│                         v                                                   │
│     ┌─────────────────────────────────────────────────┐                    │
│     │              NexusBridge                        │                    │
│     │    _route_symbol() -> place_order()             │                    │
│     └─────────────────────────────────────────────────┘                    │
│               │                │                │                          │
│               v                v                v                          │
│     ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                   │
│     │BinanceAdapter│  │BybitAdapter  │  │AlpacaAdapter │                   │
│     └──────────────┘  └──────────────┘  └──────────────┘                   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 🐛 BUGS CRÍTICOS IDENTIFICADOS

### BUG #1: `NexusBridge.get_positions()` NO EXISTE ❌

**Ubicación:** `servos/trading_manager.py` líneas 980, 1026, 1545, 1851

**Problema:**
```python
# trading_manager.py llama a:
positions = await self.bridge.get_positions()

# PERO NexusBridge NO tiene este método!
# Solo tiene: get_position(symbol) (singular, con símbolo específico)
```

**Impacto:** El código fallará con `AttributeError` cuando intente obtener posiciones.

**Solución:**
```python
# nexus_system/core/nexus_bridge.py - AGREGAR MÉTODO:

async def get_positions(self, exchange: str = None) -> List[Dict[str, Any]]:
    """
    Obtener todas las posiciones activas de todos los exchanges conectados,
    o de un exchange específico si se proporciona.
    
    Args:
        exchange: Nombre del exchange específico (opcional)
        
    Returns:
        Lista unificada de posiciones de todos los adapters
    """
    all_positions = []
    
    target_adapters = {}
    if exchange:
        if exchange.upper() in self.adapters:
            target_adapters = {exchange.upper(): self.adapters[exchange.upper()]}
    else:
        target_adapters = self.adapters
    
    for name, adapter in target_adapters.items():
        try:
            positions = await adapter.get_positions()
            # Normalizar símbolos y agregar exchange de origen
            for pos in positions:
                pos['exchange'] = name
                pos['symbol'] = self.normalize_symbol(pos.get('symbol', ''))
                all_positions.append(pos)
        except Exception as e:
            print(f"⚠️ NexusBridge: Error getting positions from {name}: {e}")
    
    return all_positions
```

---

### BUG #2: Lógica de Routing Siempre Prefiere Bybit ❌

**Ubicación:** `nexus_system/core/nexus_bridge.py` líneas 401-407

**Problema:**
```python
# Código actual:
if normalized_symbol in ASSET_GROUPS.get('CRYPTO', []):
    if is_exchange_available('BYBIT'):
        return 'BYBIT'  # ← SIEMPRE prefiere Bybit!
    elif is_exchange_available('BINANCE'):
        return 'BINANCE'
```

**Impacto:** Aunque el usuario tenga `primary_exchange = 'BINANCE'` y ambos exchanges habilitados, siempre se enviará a Bybit.

**Solución:**
```python
# nexus_system/core/nexus_bridge.py - CORREGIR _route_symbol():

if normalized_symbol in ASSET_GROUPS.get('CRYPTO', []):
    # RESPETAR primary_exchange del usuario
    if is_exchange_available(self.primary_exchange):
        return self.primary_exchange
    
    # Fallback al otro exchange crypto si el primario no está disponible
    fallback_crypto = 'BYBIT' if self.primary_exchange == 'BINANCE' else 'BINANCE'
    if is_exchange_available(fallback_crypto):
        return fallback_crypto
```

---

### BUG #3: primary_exchange Nunca Se Actualiza Desde Config ❌

**Ubicación:** `nexus_system/core/nexus_bridge.py` línea 51

**Problema:**
```python
# NexusBridge siempre usa:
self.primary_exchange = 'BINANCE'  # Hardcoded!

# El config del usuario tiene:
session.config.get('crypto_exchange', 'BINANCE')  # PERO NO SE SINCRONIZA
```

**Impacto:** Las preferencias del usuario para exchange principal son ignoradas.

**Solución:**
```python
# servos/trading_manager.py - En initialize() agregar:

# Después de conectar exchanges, sincronizar preferencia del usuario
user_primary = self.config.get('crypto_exchange', 'BINANCE')
if self.bridge:
    self.bridge.primary_exchange = user_primary.upper()
    print(f"🎯 Bridge: Primary exchange set to {user_primary}")
```

---

### BUG #4: Formato de Símbolo Inconsistente Entre Adapters ⚠️

**Ubicación:** Múltiples archivos

**Problema:**
```python
# BinanceAdapter normaliza: BTCUSDT -> BTC/USDT:USDT
# BybitAdapter normaliza: BTCUSDT -> BTC/USDT:USDT
# PERO el símbolo devuelto en posiciones varía:
# - Binance: .replace('/USDT:USDT', 'USDT')  ✓
# - Bybit: self._unformat_symbol()  (¿implementado correctamente?)
```

**Verificación necesaria:**
```python
# bybit_adapter.py - Verificar que _unformat_symbol existe y funciona:
def _unformat_symbol(self, symbol: str) -> str:
    """BTC/USDT:USDT -> BTCUSDT"""
    if not symbol:
        return symbol
    # Remover sufijos de formato CCXT
    return symbol.replace('/USDT:USDT', 'USDT').replace('/USDT', 'USDT')
```

---

### BUG #5: ShadowWallet No Sincroniza Posiciones Correctamente ⚠️

**Ubicación:** `servos/trading_manager.py` líneas 1543-1556, 1849-1862

**Problema:**
```python
# Código actual intenta sincronizar pero tiene problemas:
positions = await self.bridge.get_positions()  # ❌ Método no existe
for pos in positions:
    pos_symbol = pos.get('symbol', '')
    # ...
    self.bridge.shadow_wallet.update_position(symbol, {...})
```

**Impacto:** Las posiciones en ShadowWallet pueden estar desactualizadas.

**Solución Integral:**
```python
# Crear método de sincronización robusto en NexusBridge:

async def sync_all_positions(self) -> int:
    """
    Sincroniza todas las posiciones de todos los exchanges al ShadowWallet.
    
    Returns:
        int: Número de posiciones sincronizadas
    """
    synced = 0
    
    for name, adapter in self.adapters.items():
        try:
            positions = await adapter.get_positions()
            for pos in positions:
                normalized_symbol = self.normalize_symbol(pos.get('symbol', ''))
                self.shadow_wallet.update_position(normalized_symbol, {
                    'symbol': normalized_symbol,
                    'quantity': pos.get('quantity', 0),
                    'side': pos.get('side', 'LONG'),
                    'entry_price': pos.get('entryPrice', 0),
                    'unrealized_pnl': pos.get('unrealizedPnl', 0),
                    'exchange': name
                })
                synced += 1
        except Exception as e:
            print(f"⚠️ Position sync failed for {name}: {e}")
    
    return synced
```

---

### BUG #6: Cooldown Global vs Per-Exchange ⚠️

**Ubicación:** `nexus_loader.py` línea 269

**Problema:**
```python
# Cooldown es global por símbolo:
if cooldown_manager.is_on_cooldown(symbol):
    return  # ← Bloquea para TODOS los exchanges

# PERO: Un usuario podría tener Binance y Bybit
# Si recibe señal de BTC y ejecuta en Binance, 
# NO debería bloquear ejecución de BTC en Bybit
```

**Solución:**
```python
# servos/cooldown_manager.py - Modificar para soportar per-exchange:

def is_on_cooldown(self, symbol: str, exchange: str = None) -> bool:
    key = f"{symbol}:{exchange}" if exchange else symbol
    return key in self._cooldowns and time.time() < self._cooldowns[key]

def set_cooldown(self, symbol: str, exchange: str = None, seconds: int = 300):
    key = f"{symbol}:{exchange}" if exchange else symbol
    self._cooldowns[key] = time.time() + seconds
```

---

### BUG #7: Bybit Ticker Mapping No Se Aplica en place_order ⚠️

**Ubicación:** `nexus_system/uplink/adapters/bybit_adapter.py`

**Problema:**
```python
# El sistema tiene BYBIT_TICKER_MAPPING definido:
BYBIT_TICKER_MAPPING = {
    "1000SHIBUSDT": "SHIBUSDT",
    "1000PEPEUSDT": "PEPEUSDT",
    # ...
}

# PERO _format_symbol() en bybit_adapter no lo usa!
def _format_symbol(self, symbol: str) -> str:
    # Solo hace: BTCUSDT -> BTC/USDT:USDT
    # NO aplica las correcciones de ticker
```

**Solución:**
```python
# bybit_adapter.py - Modificar _format_symbol():

def _format_symbol(self, symbol: str) -> str:
    """Format symbol for CCXT: BTCUSDT -> BTC/USDT:USDT with Bybit corrections."""
    if not symbol:
        return symbol
    
    # 1. Aplicar correcciones de Bybit primero
    try:
        from system_directive import get_bybit_corrected_ticker
        symbol = get_bybit_corrected_ticker(symbol)
    except ImportError:
        pass
    
    # 2. Formatear para CCXT
    if 'USDT' in symbol and '/' not in symbol and ':' not in symbol:
        base = symbol.replace('USDT', '')
        return f"{base}/USDT:USDT"
    
    return symbol
```

---

## 🔧 PSEUDOCÓDIGO: FLUJO CORREGIDO COMPLETO

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    PSEUDOCÓDIGO: FLUJO DE EJECUCIÓN PILOT                  │
├─────────────────────────────────────────────────────────────────────────────┤

FUNCTION execute_trade_from_signal(signal, session):
    """
    Ejecutar trade desde señal en modo PILOT.
    Este es el flujo completo corregido.
    """
    
    symbol = signal.symbol
    action = signal.action  # BUY o SELL
    side = 'LONG' if action == 'BUY' else 'SHORT'
    
    # ─────────────────────────────────────────────────────────────
    # PASO 1: VALIDAR CONFIGURACIÓN DEL USUARIO
    # ─────────────────────────────────────────────────────────────
    
    IF session.mode != 'PILOT':
        RETURN (notificar_solo, sin_ejecutar)
    
    IF NOT session.is_strategy_enabled(signal.strategy):
        LOG "Estrategia deshabilitada"
        RETURN skip
    
    IF NOT session.is_group_enabled(get_asset_group(symbol)):
        LOG "Grupo de activo deshabilitado"
        RETURN skip
    
    # ─────────────────────────────────────────────────────────────
    # PASO 2: DETERMINAR EXCHANGE DESTINO (CORREGIDO)
    # ─────────────────────────────────────────────────────────────
    
    user_prefs = session.get_exchange_preferences()
    # Resultado: {'BINANCE': True, 'BYBIT': False, 'ALPACA': True}
    
    user_primary = session.config.get('crypto_exchange', 'BINANCE')
    
    is_crypto = 'USDT' in symbol
    
    IF is_crypto:
        # NUEVO: Respetar preferencia del usuario
        IF user_primary IN session.bridge.adapters AND user_prefs.get(user_primary):
            target_exchange = user_primary
        ELSE:
            # Fallback al otro exchange crypto disponible
            fallback = 'BYBIT' if user_primary == 'BINANCE' else 'BINANCE'
            IF fallback IN session.bridge.adapters AND user_prefs.get(fallback):
                target_exchange = fallback
            ELSE:
                RETURN error("No hay exchanges crypto disponibles")
    ELSE:
        IF 'ALPACA' IN session.bridge.adapters AND user_prefs.get('ALPACA'):
            target_exchange = 'ALPACA'
        ELSE:
            RETURN error("Alpaca no disponible para stocks")
    
    LOG f"🌉 Routing {symbol} -> {target_exchange}"
    
    # ─────────────────────────────────────────────────────────────
    # PASO 3: VERIFICAR COOLDOWN PER-EXCHANGE
    # ─────────────────────────────────────────────────────────────
    
    IF cooldown_manager.is_on_cooldown(symbol, target_exchange):
        LOG "En cooldown para este exchange"
        RETURN skip
    
    # ─────────────────────────────────────────────────────────────
    # PASO 4: SINCRONIZAR DATOS FRESCOS
    # ─────────────────────────────────────────────────────────────
    
    # 4.1 Sincronizar balance
    TRY:
        fresh_balance = AWAIT adapter.get_account_balance()
        shadow_wallet.update_balance(target_exchange, fresh_balance)
    CATCH:
        LOG "Balance sync failed - using cached"
    
    # 4.2 Sincronizar posiciones (USANDO NUEVO MÉTODO)
    TRY:
        positions = AWAIT bridge.get_positions(exchange=target_exchange)
        FOR pos IN positions:
            shadow_wallet.update_position(pos.symbol, pos)
    CATCH:
        LOG "Position sync failed"
    
    # ─────────────────────────────────────────────────────────────
    # PASO 5: VERIFICAR POSICIÓN EXISTENTE
    # ─────────────────────────────────────────────────────────────
    
    current_pos = shadow_wallet.get_position(symbol)
    net_qty = current_pos.quantity
    current_side = current_pos.side
    
    IF abs(net_qty) > 0.001:  # Posición significativa
        IF current_side == side:
            # Misma dirección - solo actualizar SL/TP
            RETURN execute_update_sltp(symbol, side, atr)
        ELSE:
            # Dirección opuesta - FLIP
            LOG f"🔄 FLIP: {current_side} -> {side}"
            RETURN execute_flip_position(symbol, side, atr)
    
    # ─────────────────────────────────────────────────────────────
    # PASO 6: VERIFICAR LIQUIDEZ
    # ─────────────────────────────────────────────────────────────
    
    has_liquidity, balance, msg = AWAIT check_liquidity(symbol)
    IF NOT has_liquidity:
        RETURN error(msg)
    
    # ─────────────────────────────────────────────────────────────
    # PASO 7: OBTENER DATOS DE MERCADO
    # ─────────────────────────────────────────────────────────────
    
    current_price = AWAIT bridge.get_last_price(symbol)
    IF current_price <= 0:
        RETURN error("No se pudo obtener precio")
    
    symbol_info = AWAIT bridge.get_symbol_info(symbol)
    qty_precision = symbol_info.quantity_precision
    price_precision = symbol_info.price_precision
    tick_size = symbol_info.tick_size
    min_notional = symbol_info.min_notional
    
    # ─────────────────────────────────────────────────────────────
    # PASO 8: CALCULAR PARÁMETROS DE RIESGO (RESPETANDO PERFILES)
    # ─────────────────────────────────────────────────────────────
    
    base_leverage = config.leverage
    max_allowed_leverage = config.max_leverage_allowed
    leverage = MIN(base_leverage, max_allowed_leverage)
    
    base_capital_pct = config.max_capital_pct
    max_allowed_capital = config.max_capital_pct_allowed
    size_pct = MIN(base_capital_pct, max_allowed_capital)
    
    # ─────────────────────────────────────────────────────────────
    # PASO 9: CALCULAR SL/TP (ATR-BASED)
    # ─────────────────────────────────────────────────────────────
    
    IF atr AND atr > 0:
        multiplier = config.atr_multiplier  # Default: 2.0
        
        IF side == 'LONG':
            sl_price = current_price - (atr * multiplier)
            tp_price = current_price + (atr * multiplier * config.tp_ratio)
        ELSE:  # SHORT
            sl_price = current_price + (atr * multiplier)
            tp_price = current_price - (atr * multiplier * config.tp_ratio)
    ELSE:
        # Fallback a porcentaje fijo
        sl_pct = config.stop_loss_pct
        IF side == 'LONG':
            sl_price = current_price * (1 - sl_pct)
            tp_price = current_price * (1 + sl_pct * config.tp_ratio)
        ELSE:
            sl_price = current_price * (1 + sl_pct)
            tp_price = current_price * (1 - sl_pct * config.tp_ratio)
    
    # Redondear a precisión de precio
    sl_price = ROUND_TO_TICK(sl_price, tick_size)
    tp_price = ROUND_TO_TICK(tp_price, tick_size)
    
    # ─────────────────────────────────────────────────────────────
    # PASO 10: CALCULAR TAMAÑO DE POSICIÓN
    # ─────────────────────────────────────────────────────────────
    
    equity = shadow_wallet.balances[target_exchange].total
    margin_to_use = equity * size_pct
    notional_value = margin_to_use * leverage
    quantity = notional_value / current_price
    
    # Redondear a precisión de cantidad
    quantity = ROUND_DOWN(quantity, qty_precision)
    
    # Verificar mínimo notional
    IF quantity * current_price < min_notional:
        RETURN error(f"Notional {quantity * current_price} < min {min_notional}")
    
    # ─────────────────────────────────────────────────────────────
    # PASO 11: APLICAR TICKER MAPPING PARA BYBIT
    # ─────────────────────────────────────────────────────────────
    
    IF target_exchange == 'BYBIT':
        symbol = apply_bybit_ticker_mapping(symbol)
        # 1000PEPEUSDT -> PEPEUSDT
    
    # ─────────────────────────────────────────────────────────────
    # PASO 12: SET LEVERAGE (ANTES DE ORDEN)
    # ─────────────────────────────────────────────────────────────
    
    AWAIT bridge.set_leverage(symbol, leverage)
    
    # ─────────────────────────────────────────────────────────────
    # PASO 13: EJECUTAR ORDEN DE ENTRADA
    # ─────────────────────────────────────────────────────────────
    
    order_side = 'BUY' if side == 'LONG' else 'SELL'
    
    result = AWAIT bridge.place_order(
        symbol=symbol,
        side=order_side,
        order_type='MARKET',
        quantity=quantity,
        exchange=target_exchange  # ← Forzar exchange específico
    )
    
    IF 'error' IN result:
        RETURN error(result.error)
    
    entry_price = result.price OR current_price
    
    # ─────────────────────────────────────────────────────────────
    # PASO 14: COLOCAR ÓRDENES CONDICIONALES (SL/TP)
    # ─────────────────────────────────────────────────────────────
    
    # Asegurar separación mínima de precios
    sl_price = ensure_price_separation(sl_price, entry_price, tick_size, side, is_sl=True)
    tp_price = ensure_price_separation(tp_price, entry_price, tick_size, side, is_sl=False)
    
    # SL Order
    IF side == 'LONG':
        IF entry_price > sl_price:  # Validar: Entry debe ser mayor que SL
            TRY:
                AWAIT bridge.place_order(
                    symbol=symbol,
                    side='SELL',  # Cerrar long
                    order_type='STOP_MARKET',
                    quantity=quantity,
                    price=sl_price,  # stopPrice
                    exchange=target_exchange
                )
                LOG f"✅ SL placed at {sl_price}"
            CATCH Exception as e:
                LOG f"⚠️ SL failed: {e}"
    ELSE:  # SHORT
        IF entry_price < sl_price:  # Validar: Entry debe ser menor que SL
            TRY:
                AWAIT bridge.place_order(
                    symbol=symbol,
                    side='BUY',  # Cerrar short
                    order_type='STOP_MARKET',
                    quantity=quantity,
                    price=sl_price,
                    exchange=target_exchange
                )
            CATCH:
                LOG "SL failed"
    
    # TP Order (similar lógica)
    TRY:
        tp_side = 'SELL' if side == 'LONG' else 'BUY'
        AWAIT bridge.place_order(
            symbol=symbol,
            side=tp_side,
            order_type='TAKE_PROFIT_MARKET',
            quantity=quantity,
            price=tp_price,
            exchange=target_exchange
        )
        LOG f"✅ TP placed at {tp_price}"
    CATCH:
        LOG "TP failed"
    
    # ─────────────────────────────────────────────────────────────
    # PASO 15: REGISTRAR Y NOTIFICAR
    # ─────────────────────────────────────────────────────────────
    
    # Establecer cooldown para este símbolo+exchange
    cooldown_manager.set_cooldown(symbol, target_exchange, 300)
    
    # Actualizar ShadowWallet
    shadow_wallet.update_position(symbol, {
        'quantity': quantity,
        'side': side,
        'entry_price': entry_price,
        'sl_price': sl_price,
        'tp_price': tp_price,
        'exchange': target_exchange
    })
    
    # Generar mensaje de confirmación
    message = format_position_message(
        symbol=symbol,
        side=side,
        quantity=quantity,
        entry_price=entry_price,
        sl_price=sl_price,
        tp_price=tp_price,
        leverage=leverage,
        total_equity=equity,
        margin_used=margin_to_use,
        target_exchange=target_exchange,
        atr_value=atr,
        strategy=signal.strategy
    )
    
    AWAIT send_telegram_message(session.chat_id, message)
    
    RETURN (True, message)

└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 📊 MATRIZ DE COMPATIBILIDAD

| Función | Binance | Bybit | Alpaca | Estado |
|---------|---------|-------|--------|--------|
| Market Orders | ✅ | ✅ | ✅ | OK |
| Limit Orders | ✅ | ✅ | ✅ | OK |
| STOP_MARKET | ✅ | ✅ | ❌ | Alpaca no soporta |
| TAKE_PROFIT_MARKET | ✅ | ✅ | ❌ | Alpaca no soporta |
| Trailing Stop | ✅ | ✅ | ❌ | Parcial |
| get_positions() | ✅ | ✅ | ✅ | OK en adapters |
| NexusBridge.get_positions() | ❌ | ❌ | ❌ | **BUG** - No implementado |
| Ticker Mapping | N/A | ⚠️ | N/A | Parcial |
| Symbol Normalization | ✅ | ⚠️ | ✅ | Verificar Bybit |

---

## 🔧 PLAN DE CORRECCIÓN

### Prioridad ALTA (Bloquean ejecución):

1. **Implementar `NexusBridge.get_positions()`** - 30 min
2. **Corregir lógica de routing en `_route_symbol()`** - 15 min
3. **Sincronizar `primary_exchange` desde config** - 10 min

### Prioridad MEDIA (Afectan precisión):

4. **Aplicar Bybit Ticker Mapping en `_format_symbol()`** - 20 min
5. **Verificar `_unformat_symbol()` en BybitAdapter** - 15 min
6. **Implementar cooldown per-exchange** - 25 min

### Prioridad BAJA (Mejoras):

7. **Agregar logging estructurado para debugging** - 20 min
8. **Crear tests unitarios para routing** - 45 min

---

## ✅ CHECKLIST DE VALIDACIÓN

- [ ] `bridge.get_positions()` devuelve posiciones de todos los exchanges
- [ ] `_route_symbol()` respeta `primary_exchange` del usuario
- [ ] Símbolos como `1000PEPEUSDT` se mapean correctamente a Bybit
- [ ] SL/TP se colocan con precios válidos (separación mínima)
- [ ] Cooldown funciona per-exchange (no bloquea otros exchanges)
- [ ] Posiciones se sincronizan correctamente al ShadowWallet
- [ ] Modo PILOT ejecuta órdenes en el exchange correcto

---

## 📝 NOTAS ADICIONALES

1. **Test Case Crítico:** Ejecutar señal BTC en modo PILOT con ambos exchanges habilitados y `crypto_exchange = 'BINANCE'`. Verificar que la orden va a Binance, no a Bybit.

2. **Monitoreo:** Agregar métricas de latencia de ejecución por exchange para identificar cuellos de botella.

3. **Rollback:** Mantener versión anterior de `nexus_bridge.py` como backup antes de aplicar cambios.

---

*Auditoría realizada: Enero 2, 2026*
*Versión del sistema: FORCE branch*

