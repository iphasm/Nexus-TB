# Implementation Plan: Fix Container Startup Errors

**Date:** 2025-12-30  
**Priority:** CRITICAL  
**Status:** In Progress

---

## 📋 Summary of Errors

### 1. ❌ **CRITICAL: Aiogram Timeout Type Error** (Blocking)
```
TypeError: unsupported operand type(s) for +: 'ClientTimeout' and 'int'
kwargs["request_timeout"] = int(bot.session.timeout + polling_timeout)
```

**Root Cause:**  
The `AiohttpSession` was initialized with `timeout=ClientTimeout(...)`, but aiogram's dispatcher expects `bot.session.timeout` to be an **integer/float** (in seconds), not a `ClientTimeout` object. When it tries to add `polling_timeout` (int) to `ClientTimeout`, it fails.

**Fix Location:** `nexus_loader.py` lines 554-565

---

### 2. ⚠️ **Session Close Error** (Non-blocking)
```
property 'client' of 'AsyncTradingSession' object has no setter
```

**Root Cause:**  
In `AsyncTradingSession.close()` (line 473-478), after calling `await self.client.close()`, the code tries to set `self.client = None`. However, `client` is a **property** (read-only), not a regular attribute.

**Fix Location:** `servos/trading_manager.py` lines 473-478

---

### 3. ⚠️ **Unclosed CCXT Sessions** (Warning)
```
bybit requires to release all resources with an explicit call to the .close() coroutine
Unclosed client session / Unclosed connector
```

**Root Cause:**  
The `close()` method in `AsyncTradingSession` only closes the Binance client (`self.client`). It doesn't close:
- Bybit adapter
- Alpaca adapter  
- NexusBridge connections

**Fix Location:** `servos/trading_manager.py` lines 473-478

---

## 🔧 Implementation Steps

### Step 1: Fix Aiogram Timeout Configuration (CRITICAL)
**File:** `nexus_loader.py`

The issue is that `AiohttpSession.timeout` stores the `ClientTimeout` object, but aiogram needs an integer for its polling calculations. We need to either:

**Option A (Recommended):** Don't pass timeout to AiohttpSession; use default and let aiogram handle it.

**Option B:** Create session with explicit connector timeout separately.

```python
# BEFORE (Broken):
from aiohttp import ClientTimeout
from aiogram.client.session.aiohttp import AiohttpSession

timeout = ClientTimeout(total=60.0, sock_read=30.0, sock_connect=30.0)
session = AiohttpSession(timeout=timeout)

bot = Bot(
    token=TELEGRAM_TOKEN,
    session=session,
    default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN)
)

# AFTER (Fixed - Option A):
# Simply use default AiohttpSession without custom timeout
# Aiogram 3.x handles timeouts internally

bot = Bot(
    token=TELEGRAM_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN)
)
```

**Rationale:** The default `AiohttpSession` in aiogram 3.x already has reasonable timeouts configured. For Railway deployments, the network issues are usually at the container/proxy level, not HTTP timeout level.

---

### Step 2: Fix AsyncTradingSession.close() Method
**File:** `servos/trading_manager.py`

```python
# BEFORE (Broken):
async def close(self):
    """Cleanup resources."""
    if self.client:
        await self.client.close()
        self.client = None  # ❌ ERROR: client is a property

# AFTER (Fixed):
async def close(self):
    """Cleanup all resources including NexusBridge adapters."""
    try:
        # Close NexusBridge (handles all adapters: Binance, Bybit, Alpaca)
        if self.bridge:
            await self.bridge.close_all()
    except Exception as e:
        print(f"⚠️ Error closing bridge: {e}")
```

**Rationale:**  
- `client` is a `@property` that returns `self.bridge.adapters['BINANCE']._exchange`, so setting it to `None` fails.
- The proper cleanup is to call `self.bridge.close_all()` which handles all exchange adapters.

---

### Step 3: Verify NexusBridge.close_all() Implementation
**File:** `nexus_system/core/nexus_bridge.py`

Ensure the `close_all()` method properly closes all CCXT exchange instances:

```python
async def close_all(self):
    """Close all exchange connections gracefully."""
    for name, adapter in self.adapters.items():
        try:
            if hasattr(adapter, '_exchange') and adapter._exchange:
                await adapter._exchange.close()
            elif hasattr(adapter, 'close'):
                await adapter.close()
            print(f"✅ Closed {name} adapter")
        except Exception as e:
            print(f"⚠️ Error closing {name}: {e}")
    self.adapters.clear()
```

---

## 📍 Files to Modify

| File | Changes | Priority |
|------|---------|----------|
| `nexus_loader.py` | Remove custom timeout, use default session | CRITICAL |
| `servos/trading_manager.py` | Fix `close()` to use `bridge.close_all()` | HIGH |
| `nexus_system/core/nexus_bridge.py` | Verify `close_all()` implementation | MEDIUM |

---

## ✅ Acceptance Criteria

1. Container starts without `TypeError` on polling
2. No "property has no setter" errors during shutdown
3. No "Unclosed client session" warnings for any exchange
4. Graceful shutdown completes without errors

---

## 🚀 Next Steps

1. Apply Step 1 fix to `nexus_loader.py`
2. Apply Step 2 fix to `servos/trading_manager.py`
3. Verify Step 3 in `nexus_bridge.py`
4. Push to GitHub
5. Verify container starts successfully
