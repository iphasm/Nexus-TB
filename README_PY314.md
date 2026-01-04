# Nexus ML Trainer - Python 3.14 Edition

## ⚠️ Versión Especial para Python 3.14

Esta versión está optimizada específicamente para Python 3.14 y excluye algunas dependencias que aún no son compatibles.

## 🔧 Limitaciones

### ❌ Dependencias Excluidas
- **pandas-ta**: No compatible con Python 3.14 (requiere numba)
- **numba**: No soporta Python 3.14 aún

### ✅ Funcionalidades Disponibles
- ✅ XGBoost para ML training
- ✅ Scikit-learn para preprocessing
- ✅ Pandas para data handling
- ✅ YFinance para descarga de datos
- ✅ Interfaz gráfica completa

### ⚠️ Funcionalidades Afectadas
- **Análisis técnico avanzado**: Limitado sin pandas-ta
- **Indicadores técnicos**: Usará implementación básica
- **Performance**: Sin optimizaciones de numba

## 🚀 Instalación

### Opción 1: Instalador Automatizado
```bash
python scripts/setup_ml_trainer_py314.py
```

### Opción 2: Manual
```bash
# Instalar dependencias compatibles
pip install xgboost>=2.0.0 scikit-learn>=1.4.0 pandas>=2.1.0
pip install yfinance>=0.2.40 pyinstaller>=6.0.0

# Crear ejecutable
python scripts/create_ml_trainer_exe.py
```

## 📊 Comparación de Features

| Feature | Python 3.11-3.13 | Python 3.14 |
|---------|------------------|-------------|
| pandas-ta | ✅ Completo | ❌ Excluido |
| Indicadores técnicos | ✅ Avanzados | ⚠️ Básicos |
| Performance | ✅ Optimizada | ⚠️ Estándar |
| Compatibilidad | ✅ Completa | ✅ Funcional |

## 🔄 Actualización Futura

Cuando pandas-ta y numba sean compatibles con Python 3.14, esta versión especial será actualizada automáticamente.

## 📞 Soporte

Para problemas específicos de Python 3.14:
1. Verificar que todas las dependencias están instaladas
2. Comprobar logs de error detallados
3. Considerar usar Python 3.11-3.13 para features completas

---
*Versión especial para Python 3.14 - Generado automáticamente*
