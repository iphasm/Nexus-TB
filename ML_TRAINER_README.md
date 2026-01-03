# 🚀 Nexus ML Trainer GUI - Ejecutable

## Interfaz Gráfica para Entrenamiento ML

**Versión:** 2.0
**Plataforma:** Windows 10/11 (64-bit)
**Tamaño aproximado:** 150-300 MB (dependiendo de dependencias)

---

## 📦 Instalación

### Opción 1: Instalador Automatizado (Recomendado)
```bash
# Ejecutar el instalador automatizado
python scripts/setup_ml_trainer.py
```
Este script:
- ✅ Verifica dependencias
- ✅ Instala paquetes faltantes
- ✅ Crea el ejecutable optimizado
- ✅ Genera paquete portable
- ✅ Crea acceso directo en escritorio

### Opción 2: Instalación Manual
```bash
# Instalar dependencias
pip install pyinstaller xgboost scikit-learn pandas joblib yfinance pandas-ta

# Crear ejecutable
python scripts/create_ml_trainer_exe.py
```

---

## 🎯 Uso Básico

### Inicio
1. **Extraer** el ZIP del paquete portable
2. **Ejecutar** `Nexus_ML_Trainer.exe`
3. **Configurar** parámetros (opcional)
4. **Clic en** "🚀 Iniciar Entrenamiento"

### Configuración Recomendada
```
📊 Velas: 5000
🎯 Símbolos: [Vacío = Todos habilitados]
📝 Verbose: ✅ Activado
💾 Backup: ✅ Activado
```

### Proceso Típico
1. **Inicio** (10-30 segundos)
2. **Descarga de datos** (2-5 minutos)
3. **Entrenamiento ML** (5-15 minutos)
4. **Guardado de modelo** (30 segundos)
5. **Completado** ✅

---

## 🖥️ Interfaz de Usuario

### Panel Principal
- **Título:** Nexus ML Trainer v2.0
- **Información del sistema:** Activos habilitados, modelo actual
- **Configuración:** Parámetros de entrenamiento
- **Logs:** Área de texto con scroll para seguimiento en tiempo real
- **Progreso:** Barra de progreso visual
- **Estado:** Mensajes de estado en la parte inferior

### Controles
- **🚀 Iniciar Entrenamiento:** Botón principal verde
- **⏹️ Detener:** Botón rojo (solo durante entrenamiento)
- **🧹 Limpiar Logs:** Limpia el área de logs
- **💾 Guardar Logs:** Exporta logs a archivo de texto

### Atajos de Teclado
- **F5:** Iniciar entrenamiento
- **Escape:** Detener entrenamiento
- **Ctrl+S:** Guardar logs
- **Ctrl+L:** Limpiar logs

---

## ⚙️ Parámetros Avanzados

### Velas de Entrenamiento
- **Recomendado:** 5000
- **Mínimo:** 1000 (para pruebas rápidas)
- **Máximo:** 50000 (solo para investigación)
- **Impacto:** Más velas = mejor modelo pero más tiempo

### Límite de Símbolos
- **Vacío:** Usa todos los activos habilitados (~60-70 símbolos)
- **Número:** Limita para pruebas rápidas (ej: 10)
- **Recomendación:** Dejar vacío para producción

### Opciones
- **Verbose:** Muestra logs detallados (recomendado)
- **Backup:** Crea copia del modelo anterior (recomendado)

---

## 📊 Resultados del Entrenamiento

### Archivos Generados
```
nexus_system/memory_archives/
├── ml_model.pkl          # Modelo XGBoost entrenado
├── scaler.pkl            # Scaler para normalización
└── ml_model_backup_*.pkl # Backup automático (opcional)
```

### Información del Modelo
- **Features:** ~45 características técnicas
- **Algoritmo:** XGBoost con regularización
- **Precisión esperada:** 70-85% (depende de datos)
- **Tamaño:** ~50-200 MB

### Logs de Entrenamiento
- **Archivo:** `ml_training_logs_YYYYMMDD_HHMMSS.txt`
- **Contenido:** Progreso completo, errores, métricas
- **Ubicación:** Directorio actual o seleccionado por usuario

---

## 🔧 Solución de Problemas

### Error: "Python no encontrado"
```
Solución: Instalar Python 3.8+ desde python.org
Verificar: python --version
```

### Error: "Dependencias faltantes"
```bash
pip install xgboost scikit-learn pandas joblib yfinance pandas-ta pyinstaller
```

### Error: "No se puede crear ejecutable"
```
Solución:
1. Ejecutar como administrador
2. Verificar espacio en disco (>500MB)
3. Cerrar otros programas que usen memoria
4. Reintentar: python scripts/setup_ml_trainer.py
```

### Error: "Memoria insuficiente durante entrenamiento"
```
Solución:
1. Reducir velas: 3000 en lugar de 5000
2. Limitar símbolos: 20 en lugar de todos
3. Cerrar otras aplicaciones
4. Usar máquina con más RAM (16GB+ recomendado)
```

### Error: "Conexión de red fallida"
```
Problema: Descarga de datos de mercado
Solución:
1. Verificar conexión a internet
2. Esperar y reintentar (los APIs pueden estar limitados)
3. Usar datos offline si disponibles
```

### Aplicación no responde
```
Solución:
1. Esperar - el entrenamiento puede tomar tiempo
2. Verificar logs para progreso
3. Si se congela >30min, forzar cierre y reintentar con menos datos
```

---

## 📈 Rendimiento Esperado

### En máquina típica (8GB RAM, SSD)
- **Inicio:** 10-30 segundos
- **Descarga datos (5000 velas x 60 símbolos):** 3-8 minutos
- **Entrenamiento ML:** 5-15 minutos
- **Guardado:** 30 segundos
- **Total:** 10-30 minutos

### Factores que afectan rendimiento
- **RAM:** Más memoria = más rápido
- **CPU:** Más núcleos = más rápido
- **Disco:** SSD > HDD
- **Red:** Conexión estable para descarga de datos
- **Antivirus:** Puede ralentizar el proceso

---

## 🔄 Actualizaciones

### Versión Actual: 2.0
- ✅ Interfaz gráfica completa
- ✅ Entrenamiento automatizado
- ✅ Backup automático
- ✅ Logs en tiempo real
- ✅ Configuración persistente
- ✅ Empaquetado portable

### Próximas Versiones
- 🔄 Soporte multi-idioma
- 🔄 Gráficos de rendimiento en tiempo real
- 🔄 Entrenamiento distribuido
- 🔄 Interfaz web alternativa

---

## 📞 Soporte Técnico

### Diagnóstico Automatizado
```bash
# Verificar integridad del sistema ML
python scripts/diagnose_ml_system.py
```

### Logs de Debug
- Los logs de la aplicación incluyen información detallada
- Guardar logs con "💾 Guardar Logs" para análisis
- Incluir logs al reportar problemas

### Reportar Problemas
1. **Guardar logs** completos del entrenamiento
2. **Incluir información del sistema:**
   - Windows versión
   - RAM disponible
   - Espacio en disco
   - Conexión a internet
3. **Describir el error** con pasos para reproducirlo

---

## 📋 Checklist Pre-Entrenamiento

### ✅ Verificación del Sistema
- [ ] Windows 10/11 (64-bit)
- [ ] 8GB RAM mínimo disponible
- [ ] 500MB espacio libre
- [ ] Conexión a internet estable
- [ ] Antivirus no bloqueando (temporalmente)

### ✅ Verificación de Dependencias
- [ ] Python 3.8+ instalado
- [ ] Todas las dependencias instaladas
- [ ] Ejecutable creado correctamente
- [ ] Permisos de escritura en carpeta

### ✅ Configuración
- [ ] Parámetros adecuados (velas: 5000)
- [ ] Backup automático activado
- [ ] Verbose activado para monitoreo
- [ ] Antivirus pausado si es necesario

### ✅ Ambiente
- [ ] Otras aplicaciones cerradas
- [ ] Suficiente batería (si laptop)
- [ ] Conexión estable (no móvil)
- [ ] Tiempo disponible (30+ minutos)

---

## 🎯 Conclusión

El **Nexus ML Trainer GUI** proporciona una manera sencilla y visual de entrenar modelos de Machine Learning para el sistema Nexus. Con esta herramienta, usuarios sin conocimientos técnicos avanzados pueden:

- ✅ Configurar parámetros de entrenamiento fácilmente
- ✅ Monitorear progreso en tiempo real
- ✅ Resolver problemas comunes automáticamente
- ✅ Obtener modelos optimizados para trading algorítmico

**¡La interfaz gráfica hace que el entrenamiento ML sea accesible para todos!** 🚀

---

*Documento generado automáticamente - Nexus ML Trainer Package*
