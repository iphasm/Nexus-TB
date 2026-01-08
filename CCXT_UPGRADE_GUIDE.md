# 🚀 CCXT Upgrade Guide: Versión 4.4.0+

## ⚠️ **Importancia Crítica de la Actualización**

### Problemas con Versiones Antiguas:
- **Órdenes condicionales defectuosas** en Bybit (triggerDirection incorrecto)
- **Trailing stops no funcionan** en versiones < 4.3.0
- **Errores 110092/110093** por parámetros inválidos
- **Incompatibilidad con API V5** de Bybit
- **Riesgo de posiciones sin protección** (SL/TP fallidos)

### Beneficios de CCXT 4.4.0+:
- ✅ **API Bybit V5 completa** soporte
- ✅ **Trailing stops nativos** funcionales
- ✅ **Órdenes condicionales estables**
- ✅ **Mejor manejo de errores**
- ✅ **Paridad con documentación oficial**

---

## 📦 **Instalación**

```bash
# Actualizar a versión compatible
pip install "ccxt>=4.4.0,<5.0.0"

# Verificar instalación
python3 check_ccxt_version.py
```

---

## 🔧 **Cambios Necesarios en el Código**

### 1. **Bybit Adapter - Trailing Stops**
```python
# ✅ CORRECTO en CCXT 4.4.0+
trailing_stop_order = await exchange.create_order(
    symbol='BTCUSDT',
    type='trailing_stop_market',
    side='sell',
    amount=0.001,
    params={
        'trailingStop': distance,  # Distancia absoluta
        'activePrice': activation_price,
        'reduceOnly': True
    }
)
```

### 2. **Parámetros de Órdenes Condicionales**
```python
# ✅ Bybit V5 - triggerDirection corregido
params = {
    'triggerDirection': 2,  # 1=rise above, 2=fall below
    'tpslMode': 'Partial',  # Importante para compatibilidad
    'workingType': 'MARK_PRICE'  # Para Binance
}
```

### 3. **Manejo de Errores Mejorado**
```python
# ✅ CCXT 4.4.0+ tiene mejores códigos de error
try:
    result = await exchange.create_order(...)
except ccxt.InvalidOrder as e:
    if '110092' in str(e):  # triggerPrice inválido
        # Reintentar sin triggerPrice para trailing stops
    elif '110043' in str(e):  # leverage no modificado
        # Es OK, no es error
```

---

## 🧪 **Verificación Post-Upgrade**

Ejecutar después de actualizar:

```bash
# 1. Verificar versión
python3 check_ccxt_version.py

# 2. Probar órdenes condicionales
# Crear una posición pequeña y verificar SL/TP

# 3. Probar trailing stops
# Verificar que se activen correctamente
```

---

## 🚨 **Issues Conocidos Resueltos**

### Issue #1: triggerDirection Incorrecto
- **Antes:** SL/TP se activaban en dirección opuesta
- **Después:** Correcto según API Bybit V5

### Issue #2: Trailing Stops No Funcionan
- **Antes:** Parámetros incorrectos causaban errores
- **Después:** Soporte nativo trailing_stop_market

### Issue #3: Órdenes Duplicadas
- **Antes:** Sin verificación pre-retry
- **Después:** Validación antes de reintentar

---

## 📊 **Compatibilidad**

| CCXT Version | Bybit V5 | Trailing Stops | Órdenes Condicionales |
|-------------|----------|----------------|----------------------|
| < 4.0.0    | ❌       | ❌             | ❌                   |
| 4.0.x-4.2.x| ⚠️       | ⚠️             | ⚠️                   |
| 4.3.x-4.3.x| ✅       | ⚠️             | ✅                   |
| **4.4.0+** | ✅       | ✅             | ✅                   |

---

## 🎯 **Recomendaciones**

1. **Actualizar inmediatamente** si usas versiones < 4.4.0
2. **Probar en staging** antes de producción
3. **Monitorear logs** después de actualizar
4. **Tener plan de rollback** si hay issues

---

## 📞 **Soporte**

Si encuentras problemas después de actualizar:
1. Ejecutar `python3 check_ccxt_version.py`
2. Revisar logs para códigos de error específicos
3. Verificar compatibilidad con exchange APIs
4. Reportar issues con versión exacta de CCXT
