# 🏗️ **NEXUS-TB PROJECT STRUCTURE**

## 📁 **Nueva Estructura Organizada**

Esta estructura ha sido optimizada para **máxima claridad, mantenibilidad y escalabilidad**.

```
nexus-tb/
├── 📂 src/                          # Código fuente principal (eliminado - ahora usa ML Cloud Trainer)
│   └── README: ML training moved to separate repository
│
├── 📂 scripts/                     # Scripts ejecutables organizados
│   ├── analysis/                  # Scripts de análisis de datos/modelos
│   ├── demos/                     # Scripts de demostración
│   ├── utils/                     # Scripts utilitarios
│   ├── setup/                     # Scripts de instalación
│   │   ├── check_dependencies.py  # Verificación dependencias
│   │   └── diagnose_python.py     # Diagnóstico Python
│   └── evaluation/                # Scripts de evaluación
│       └── run_ml_evaluation.bat  # Launcher principal
│
├── 📂 models/                      # Modelos entrenados
│   ├── ml_model.pkl              # Modelo principal
│   └── scaler.pkl                # Scaler de features
│
├── 📂 docs/                       # Documentación
│   ├── guides/                   # Guías de uso
│   └── analysis/                 # Documentos de análisis
│       ├── TRAINING_README.md    # Guía ML completa
│       ├── WHITEPAPER.md         # Documentación técnica
│       └── ANALISIS_*.md         # Análisis específicos
│
├── 📂 data/                       # Datos y dependencias externas
│   └── external/                 # Dependencias externas
│       └── pandas_ta_openbb-0.4.22/  # Fork pandas-ta
│
├── 📂 nexus_system/               # Sistema principal (existente)
│   ├── memory_archives/          # Modelos (enlace a models/)
│   ├── cortex/                   # Lógica de estrategias
│   ├── uplink/                   # Conexiones externas
│   ├── shield/                   # Gestión de riesgo
│   └── utils/                    # Utilidades del sistema
│
├── 📂 temp_logs/                  # Logs temporales (no versionar)
├── 📂 tests/                      # Tests unitarios (pytest)
├── 📂 tools/                      # Herramientas de desarrollo
├── 📂 handlers/                   # Handlers del bot
├── 📂 servos/                     # Servicios del bot
└── 📂 strategies/                 # Estrategias de trading
```

## 🎯 **Principios de Organización**

### **1. Separación por Responsabilidades**
- **`tests/`**: Testing y verificación
- **`deploy/`**: Deployment e infraestructura
- **`analysis/`**: Análisis y comparación de datos
- **`examples/`**: Demos y ejemplos de uso
- **`config/`**: Configuración y mantenimiento
- **`tools/`**: Utilidades y herramientas
- **`scripts/`**: Scripts organizados por función
- **`models/`**: Artefactos de ML entrenados
- **`docs/`**: Documentación completa
- **`nexus_system/`**: Sistema principal (core)

### **2. Jerarquía Lógica**
- **Testing**: Tests y verificación → `tests/`
- **Deployment**: Infraestructura → `deploy/`
- **Analysis**: Investigación y comparación → `analysis/`
- **Examples**: Demostraciones → `examples/`
- **Configuration**: Setup y mantenimiento → `config/`
- **Utilities**: Herramientas → `tools/`

### **3. Compatibilidad Backward**
- **`nexus_system/`**: Estructura existente preservada
- **Modelos**: Disponibles en `models/` y `nexus_system/memory_archives/`
- **Imports**: Sistema de compatibilidad para código existente

## 🚀 **Cómo Usar la Nueva Estructura**

### **Entrenamiento ML:**
```bash
# Desde raíz del proyecto
python src/ml/train_cortex.py --candles 2000 --symbols 5

# O usando el script organizado
python scripts/train_ml.py --candles 2000 --symbols 5
```

### **Evaluación Completa:**
```bash
# Launcher interactivo
scripts/evaluation/run_ml_evaluation.bat
```

### **Testing y Debug:**
```bash
# Testing completo
python scripts/testing/debug_training.py

# Test específico
python scripts/testing/test_timeout.py
```

### **Instalación:**
```bash
# Verificar dependencias
python scripts/setup/check_dependencies.py

# Instalar para Python 3.14
scripts/setup/install_py314.bat
```

## 📋 **Beneficios de la Nueva Estructura**

### **✅ Claridad**
- Cada directorio tiene un propósito específico
- Nombres descriptivos y consistentes
- Estructura jerárquica intuitiva

### **✅ Mantenibilidad**
- Código organizado por funcionalidad
- Fácil localizar archivos específicos
- Separación clara entre concerns

### **✅ Escalabilidad**
- Fácil agregar nuevas funcionalidades
- Estructura preparada para crecimiento
- Modularidad mejorada

### **✅ Colaboración**
- Estructura estándar de proyectos Python
- Fácil onboarding de nuevos desarrolladores
- Documentación clara de ubicación de archivos

## 🔧 **Migración y Compatibilidad**

### **Imports Actualizados:**
```python
# ✅ Nueva estructura (recomendada)
from src.ml.train_cortex import fetch_data
from src.ml.add_new_features import add_all_new_features

# ✅ Compatibilidad backward (todavía funciona)
from train_cortex import fetch_data
from add_new_features import add_all_new_features
```

### **Scripts Actualizados:**
- Todos los `.bat` y `.py` ejecutables actualizados
- Rutas absolutas convertidas a rutas relativas
- Compatibilidad mantenida con comandos existentes

### **Modelos:**
- Disponibles en ambas ubicaciones para compatibilidad
- `models/` para nueva estructura
- `nexus_system/memory_archives/` para código existente

## 📚 **Documentación**

- **`PROJECT_STRUCTURE.md`**: Esta guía completa
- **`docs/guides/`**: Guías específicas de uso
- **`docs/analysis/TRAINING_README.md`**: Documentación ML completa
- **`.gitignore`**: Actualizado para nueva estructura

---

## 🎉 **Resultado Final**

**Estructura completamente organizada y optimizada** que facilita:

- 🚀 **Desarrollo rápido** con código bien organizado
- 🔧 **Mantenimiento fácil** con responsabilidades claras
- 📈 **Escalabilidad** preparada para crecimiento
- 🤝 **Colaboración efectiva** con estructura estándar
- 🛡️ **Compatibilidad total** con código existente

**¡El proyecto está ahora estructurado como un sistema profesional de grado producción!** ✨
