# 🧠 Nexus Cortex ML Training Guide

## 🚀 Inicio Rápido

### 📦 PASO 0: Instalar Dependencias
Antes de cualquier cosa, instala las dependencias requeridas:

**Opción A: Automática (Recomendado)**
```cmd
# Instala todas las dependencias automáticamente
install_dependencies.bat
```

**Opción B: Verificación Rápida**
```cmd
# Solo verifica si ya están instaladas
check_dependencies.bat
```

**Opción C: Manual**
```cmd
pip install -r requirements.txt
```

### 🔧 PASO 1: Diagnóstico del Sistema
Una vez instaladas las dependencias, verifica que todo funcione:

```cmd
# Ejecuta las pruebas de diagnóstico completas
debug_training.bat
```

Esto verificará:
- ✅ Librerías instaladas (pandas, numpy, xgboost, joblib, etc.)
- ✅ Configuración de símbolos cargada
- ✅ Conexión a APIs de datos (Binance + Yahoo Finance)
- ✅ Funcionalidad básica de descarga con progreso detallado

### 🎯 PASO 2: Entrenamiento ML
Si el diagnóstico pasa exitosamente, ejecuta el entrenamiento:

### Opción 1: Ejecutar con .bat (Recomendado para Windows)
```cmd
# Entrenamiento completo con input manual
train_ml.bat
```

### Opción 2: Ejecutar con PowerShell
```powershell
# Entrenamiento completo con input manual
.\train_ml.ps1
```

### Opción 3: Ejecutar directamente con Python
```cmd
# Modo automático con 15,000 velas
python train_cortex.py

# Con cantidad específica de velas
python train_cortex.py --candles 5000

# Modo interactivo (pide input)
python train_cortex.py --interactive

# Modo test (solo 3 símbolos)
python train_cortex.py --symbols 3
```

### Opción 4: Test Rápido
```cmd
# Test con configuración mínima
test_training.bat
```

### Opción 5: Debug Detallado
```cmd
# Diagnóstico completo con progreso por símbolo
debug_training.bat
```

## 📊 Configuración de Parámetros

### Cantidad de Velas
- **5000 velas** = ~5.2 días de datos históricos
- **15000 velas** = ~15.6 días de datos históricos (recomendado)
- **35000 velas** = ~36.5 días de datos históricos

### Intervalo Temporal
- **Fijo en 15 minutos** - Optimizado para estrategias de corto/medio plazo

### Símbolos Procesados
- **Por defecto**: Todos los activos configurados (~47 símbolos)
- **Para testing**: Usa `--symbols N` para limitar a N símbolos

## 📈 Progreso en Tiempo Real

El script muestra progreso detallado en 6 fases:

### 📥 Fase 1: Descarga de Datos
- Descarga datos históricos de cada símbolo
- Muestra progreso: `[1/47] Procesando BTCUSDT...`
- Tiempos por símbolo y estadísticas de éxito

### 🔧 Fase 2: Preparación de Datos
- Unión de datasets de todos los símbolos
- Cálculo de estadísticas del dataset
- Validación de calidad de datos

### 🔄 Fase 3: Preprocesamiento
- Encoding de etiquetas de estrategia
- Aplicación de RobustScaler
- Configuración de TimeSeriesSplit

### 🚀 Fase 4: Entrenamiento XGBoost
- Validación cruzada chronológica (5-fold)
- Barras de progreso detalladas
- Métricas en tiempo real por fold

### 🏋️ Fase 5: Evaluación Final
- Entrenamiento en dataset completo
- Evaluación en conjunto de test
- Análisis de importancia de features

### 💾 Fase 6: Guardado
- Modelo guardado en `nexus_system/memory_archives/ml_model.pkl`
- Scaler guardado en `nexus_system/memory_archives/scaler.pkl`

## 🎯 Salida del Entrenamiento

### Resultados Esperados
```
📊 ESTADÍSTICAS DEL DATASET:
   • mean_rev: 50,000 (44.0%) ███████████████
   • trend: 35,000 (30.6%) ███████████
   • grid: 27,000 (23.7%) ████████
   • scalp: 2,000 (1.6%) █

📊 RESULTADOS CROSS-VALIDATION:
   • Accuracy promedio: 0.554
   • Desviación estándar: 0.074

🔑 TOP FEATURES MÁS IMPORTANTES:
   🥇 atr_pct          0.495 ████████████████████████
   🥈 adx             0.163 ████████
   🥉 bb_width        0.134 ██████
```

### Archivos Generados
- `nexus_system/memory_archives/ml_model.pkl` - Modelo entrenado
- `nexus_system/memory_archives/scaler.pkl` - Scaler para normalización
- `train_output.log` - Log completo del entrenamiento
- `train_error.log` - Log de errores (si los hay)

## ⚠️ Solución de Problemas

### "El script se queda colgado después de configuración"
**Síntomas**: Muestra configuración pero no avanza
```cmd
🚀 Iniciando entrenamiento ML...
📊 Velas configuradas: 5000
💡 Presiona Ctrl+C para cancelar en cualquier momento

[se queda aquí sin hacer nada]
```

**Diagnóstico**:
```cmd
# Ejecuta el debug primero
debug_training.bat
```

**Causas comunes**:
- ❌ Librerías faltantes o corruptas
- ❌ Error en configuración de símbolos
- ❌ Problema con APIs de datos

### "Error de importación"
**Síntoma**: `ImportError` al inicio
**Solución**:
```cmd
pip install -r requirements.txt
```

### "No veo progreso en tiempo real"
**Causas**:
- Ejecutando desde IDE en lugar de terminal
- Buffer de output no se está flushing
- Script ejecutándose en background

**Solución**: Ejecuta desde Command Prompt/PowerShell

### "Error de conexión a Binance"
**Síntomas**:
- `ConnectionError` o `Timeout`
- API rate limits

**Solución**:
- Verifica conexión a internet
- Espera unos minutos (rate limiting)
- Reduce número de símbolos (`--symbols 5`)

### "Memoria insuficiente"
**Síntomas**:
- `MemoryError`
- Sistema se congela

**Solución**:
```cmd
# Reduce cantidad de datos
python train_cortex.py --candles 5000 --symbols 10
```

### "Script termina inmediatamente"
**Causa**: Error en argumentos
**Verificación**:
```cmd
python train_cortex.py --help
```

### "Problemas con colores ANSI en Windows"
**Síntoma**: Caracteres extraños `←[36m`
**Solución**: Los colores están diseñados para terminals modernos, no afectan funcionalidad

### "Archivos no se guardan"
**Causa**: Permisos de escritura
**Solución**: Ejecuta como administrador o verifica permisos en `nexus_system/memory_archives/`

## 🔍 Proceso de Debug Paso a Paso

Si el script se queda colgado, sigue este proceso:

### 1. Ejecuta Diagnóstico
```cmd
debug_training.bat
```

### 2. Revisa Resultados
- ✅ **Si todas las pruebas pasan**: El problema está en el entrenamiento principal
- ❌ **Si fallan importaciones**: Reinstala dependencias
- ❌ **Si falla configuración**: Verifica `system_directive.py`
- ❌ **Si falla descarga**: Problema de conectividad/API

### 3. Test con Configuración Mínima
```cmd
python train_cortex.py --candles 100 --symbols 2
```

### 4. Escala Progresivamente
- ✅ **Funciona**: Aumenta velas a 1000
- ✅ **Funciona**: Aumenta símbolos a 5
- ✅ **Funciona**: Prueba configuración completa

### 5. Usa Modo Verbose para Progreso Detallado
```cmd
# Muestra progreso detallado de cada request HTTP
python train_cortex.py --candles 1000 --verbose

# O en modo interactivo
python train_cortex.py --interactive --verbose
```

**Qué verás en modo verbose:**
```
📊 Testing BTCUSDT (Binance Crypto)...
  📡 Conectando a Binance API para BTCUSDT...
  📊 Request 1: 0/50 velas (0.0%)...
    ⏱️  Request 1 completado en 0.45s
  ✅ BTCUSDT: 50 filas en 0.47s
```

### 6. Logs de Debug
Revisa estos archivos después de fallos:
- `train_output.log` - Salida del entrenamiento
- `train_error.log` - Errores específicos

## 📞 Soporte Adicional

Si después de seguir estos pasos aún tienes problemas:

1. **Captura el output completo** del comando que falla
2. **Incluye información del sistema**:
   - Versión de Python: `python --version`
   - Sistema operativo y versión
   - Output de `pip list | findstr "pandas numpy xgboost"`

3. **Describe exactamente dónde se queda colgado** el script

## ⏱️ Tiempos Estimados

| Configuración | Símbolos | Tiempo Aprox | RAM Necesaria |
|---------------|----------|--------------|---------------|
| 5000 velas   | 47      | 15-25 min   | 2-4 GB       |
| 15000 velas  | 47      | 45-75 min   | 4-8 GB       |
| 35000 velas  | 47      | 120-180 min | 8-16 GB      |

## 🎯 Estrategias ML Soportadas

### 1. **mean_rev** (Mean Reversion)
- Estrategia: Compra en oversold, venta en overbought
- Condiciones: RSI < 35 o RSI > 65
- Accuracy típica: ~83%

### 2. **trend** (Trend Following)
- Estrategia: Seguir tendencia con ADX
- Condiciones: ADX > 25
- Accuracy típica: ~49%

### 3. **grid** (Grid Trading)
- Estrategia: Trading en rangos
- Condiciones: ATR% < 0.8%
- Accuracy típica: ~50%

### 4. **scalp** (Scalping)
- Estrategia: Operaciones de muy corto plazo
- Condiciones: ATR% > 1.5%
- Accuracy típica: ~29%

## 🚀 Activación en el Bot

Después del entrenamiento exitoso:

```bash
# Reinicia el bot
# O ejecuta en Telegram:
/ml_mode on
```

El bot ahora usará el modelo ML para clasificar automáticamente la mejor estrategia de trading según las condiciones de mercado actuales.

---

**💡 Tip**: Para resultados óptimos, entrena con al menos 15,000 velas y verifica que el accuracy CV esté por encima de 0.50.

---

## 🛡️ **Timeouts y Manejo de Interrupciones**

### **Prevención de Scripts Colgados**

Todos los scripts incluyen ahora protección contra operaciones bloqueantes:

- **⏱️ Timeouts de 30 segundos** en operaciones de red
- **🔄 Reintentos automáticos** (máximo 3 intentos)
- **🛑 Manejo de Ctrl+C** para interrupción graceful
- **📊 Logging progresivo** para seguimiento en tiempo real

### **Operaciones con Timeout**

**Descargas de Datos:**
- Binance API: 30s timeout por request HTTP
- Yahoo Finance: 30s timeout total por símbolo
- Reintentos con backoff exponencial (1s, 2s, 4s)

**Procesamiento:**
- Lotes de 5 símbolos para evitar sobrecarga de API
- Checks de interrupción cada operación significativa
- Logging cada request completado

### **Interrupción Graceful**

Durante cualquier operación, presiona `Ctrl+C`:

```cmd
⚠️  Interrupción detectada (Ctrl+C). Finalizando operaciones pendientes...
🧹 Operación interrumpida - realizando cleanup...
✅ Proceso terminado correctamente
```

### **Monitoreo de Progreso**

Los scripts muestran progreso constante:

```
📊 [1/47] Descargando BTCUSDT...
  📡 Conectando a Binance API para BTCUSDT...
  📊 Request 1: 0/1500 velas (0.0%)...
    ⏱️  Request 1 completado en 0.45s
  ✅ BTCUSDT completado - 1485 muestras válidas
```

### **Diagnóstico de Timeouts**

**Si un script se cuelga:**

1. **Espera 30 segundos** - timeout automático
2. **Presiona Ctrl+C** para interrupción manual
3. **Ejecuta diagnóstico:**
```cmd
python test_timeout.py
```

**Posibles causas de timeout:**
- Conexión a internet lenta
- Rate limiting de APIs
- Servidores congestionados
- Firewall/antivirus bloqueando requests

### **Configuración de Timeouts**

```python
# En train_cortex.py
REQUEST_TIMEOUT = 30  # segundos para requests HTTP
MAX_RETRIES = 3       # reintentos por operación
BATCH_SIZE = 5        # símbolos procesados por lote
```

**Para debugging avanzado:**
```cmd
# Verificar conectividad de red
python test_timeout.py

# Debug detallado de features
python debug_features.py
```

---

## 📦 Instalación de Dependencias

### Archivos de Instalación Disponibles

```
Scripts de Instalación:
├── install_dependencies.bat       ← INSTALACIÓN COMPLETA AUTOMÁTICA
├── install_py314.bat              ← ESPECIAL PARA PYTHON 3.14
├── install_minimal_py314.bat      ← MÍNIMA PARA PYTHON 3.14
├── install_clean_py314.bat        ← ÚLTIMO RECURSO (ENTORNO VIRTUAL)
├── install_dependencies.ps1       ← Instalación en PowerShell
├── check_dependencies.bat         ← Verificación rápida de dependencias
├── check_dependencies.py          ← Script de verificación en Python

Scripts de Evaluación ML:
├── run_ml_evaluation.bat          ← MENU INTERACTIVO DE EVALUACIONES
├── walk_forward_validation.py     ← VALIDACIÓN WALK-FORWARD CHRONOLÓGICA
├── performance_evaluation.py      ← EVALUACIÓN COMPLETA DE RENDIMIENTO
├── analyze_features.py            ← ANÁLISIS DE FEATURES DEL MODELO
├── debug_features.py              ← DEBUG DE EXPANSIÓN DE FEATURES
```

### Proceso de Instalación Recomendado

**PASO 1: Verificar Estado Actual**
```cmd
check_dependencies.bat
```

**PASO 2: Instalar si es Necesario**
```cmd
install_dependencies.bat
```

**PASO 3: Verificar Instalación**
```cmd
python check_dependencies.py
```

### Dependencias Críticas para ML

- **pandas** - Manipulación de datos tabulares
- **numpy** - Computación numérica
- **scikit-learn** - Algoritmos de Machine Learning
- **xgboost** - Modelo de gradient boosting
- **joblib** - Serialización de modelos
- **yfinance** - API de Yahoo Finance
- **pandas-ta** - Indicadores técnicos
- **tqdm** - Barras de progreso

### Solución de Problemas de Instalación

#### **Python 3.14.0 - Problemas de Entorno**

**Síntoma:** Diagnóstico muestra dependencias OK pero scripts fallan con "No module named"

**Causa:** Python 3.14 puede usar diferentes entornos/instalaciones

**Solución:**
```cmd
# 1. Diagnóstico completo
diagnose_python.bat

# 2. Si diagnóstico OK pero scripts fallan, usar Python específico
"C:\Python314\python.exe" debug_training.py

# 3. O reinstalar
install_minimal_py314.bat
```

#### **Instalación Normal (Python < 3.14)**

**Opción 1: Instalación por Pasos (Recomendado)**
```cmd
install_py314.bat
```

**Opción 2: Instalación Mínima**
```cmd
install_minimal_py314.bat
```

**Opción 3: Entorno Virtual Limpio (Último Recurso)**
```cmd
install_clean_py314.bat
```

**Opción 4: Manual (si las anteriores fallan)**
```cmd
pip install numpy==1.26.3 pandas==2.2.0 scikit-learn==1.4.0 xgboost==2.0.0 joblib==1.4.0 yfinance
```

#### **Error: "Microsoft Visual C++"**
```cmd
# Instala Build Tools
# Descarga desde: https://visualstudio.microsoft.com/visual-cpp-build-tools/
```

#### **Error: "pip" no encontrado**
```cmd
# Asegúrate de que Python esté en PATH
python -m ensurepip --upgrade
```

#### **Instalación lenta**
```cmd
# Usa mirror local
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple/
```

#### **Verificación de Instalación**
```cmd
# Verifica dependencias críticas
check_dependencies.bat

# Diagnóstico completo
debug_training.bat
```

## 🔬 **Evaluación Avanzada del Modelo ML**

### **Scripts de Evaluación Disponibles**

```
Evaluación ML:
├── run_ml_evaluation.bat          ← MENU INTERACTIVO PRINCIPAL
├── walk_forward_validation.py     ← VALIDACIÓN WALK-FORWARD
├── performance_evaluation.py      ← EVALUACIÓN DE RENDIMIENTO
├── analyze_features.py            ← ANÁLISIS DE FEATURES
├── debug_features.py              ← DEBUG DE FEATURES
```

### **Flujo de Evaluación Recomendado**

1. **Análisis Básico**:
   ```cmd
   python analyze_features.py
   ```
   *Revisa importancia de features y dependencia ATR*

2. **Validación Chronológica**:
   ```cmd
   python walk_forward_validation.py
   ```
   *Evalúa estabilidad temporal sin data leakage*

3. **Evaluación Completa**:
   ```cmd
   python performance_evaluation.py
   ```
   *Análisis detallado por estrategia y condiciones*

4. **Menú Interactivo**:
   ```cmd
   run_ml_evaluation.bat
   ```
   *Elige el tipo de evaluación deseada*

### **Interpretación de Métricas**

#### **Walk-Forward Validation**
- **Accuracy promedio > 55%**: Excelente
- **Desviación estándar < 5%**: Muy estable
- **ATR < 25%**: Dependencia optimizada

#### **Evaluación de Rendimiento**
- **Mejor estrategia > 65%**: Especialización exitosa
- **Variabilidad < 10%**: Consistente
- **Confianza > 70%**: Predicciones confiables

### **Archivos de Resultados**

```
results/
├── wf_validation_results.pkl      ← Resultados walk-forward
├── performance_results.pkl        ← Evaluación completa
└── ml_model_expanded.pkl          ← Modelo con features expandidas
```

### **Próximos Pasos Basados en Resultados**

**Si ATR > 30%**:
- Agregar features de correlación inter-mercado
- Implementar análisis de order book
- Incluir indicadores de sentimiento

**Si Accuracy < 50%**:
- Revisar balance de clases
- Experimentar con hiperparámetros
- Considerar ensemble methods

**Si Variabilidad Alta**:
- Implementar modelos adaptativos
- Segmentar por condiciones de mercado
- Usar técnicas de domain adaptation
