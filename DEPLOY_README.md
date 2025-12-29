# 🚀 Guía de Despliegue Automático - Nexus Trading Bot

Este proyecto incluye scripts para automatizar el proceso de push a GitHub, que activa automáticamente el despliegue en Railway.

## 📋 Opciones Disponibles

### 1. Script PowerShell (Recomendado para Windows)

```powershell
# Uso básico (mensaje auto-generado)
.\deploy.ps1

# Con mensaje personalizado
.\deploy.ps1 -Message "Fix: Corrección de órdenes condicionales"

# Agregar todos los cambios (incluyendo eliminados)
.\deploy.ps1 -Message "Update" -All

# Solo ver estado (sin hacer commit)
.\deploy.ps1 -Status
```

### 2. Script Python (Multiplataforma)

```bash
# Uso básico
python deploy.py

# Con mensaje personalizado
python deploy.py -m "Fix: Corrección de órdenes condicionales"

# Agregar todos los cambios
python deploy.py -a -m "Update"

# Solo commit local (sin push)
python deploy.py -m "Update" --no-push

# Solo ver estado
python deploy.py -s
```

### 3. Script Batch (Windows Simple)

```cmd
# Ejecutar y seguir las instrucciones
deploy.bat
```

### 4. Git Aliases (Más Rápido)

Primero, configura los aliases:

```bash
# Copiar aliases a tu .gitconfig
cat .gitconfig-aliases.txt >> ~/.gitconfig

# O manualmente:
git config --global alias.deploy '!f() { git add . && git commit -m "$1" && git push; }; f'
```

Luego usa:

```bash
# Deploy rápido
git deploy "Mensaje de commit"

# Deploy con mensaje auto-generado
git deploy-auto
```

## 🔄 Flujo de Despliegue

```
1. Haces cambios en el código
2. Ejecutas el script de deploy
3. Script hace: git add → commit → push
4. GitHub recibe el push
5. Railway detecta el cambio automáticamente
6. Railway despliega la nueva versión
```

## ⚙️ Configuración de Railway

Asegúrate de que Railway esté configurado para:

1. **Auto-Deploy desde GitHub**: Conectado a tu repositorio
2. **Branch**: Generalmente `main` o `master`
3. **Build Command**: Automático (detecta Dockerfile o requirements.txt)
4. **Start Command**: `python nexus_loader.py`

## 📝 Mensajes de Commit

El script auto-genera mensajes basados en los archivos modificados:

- `[Bridge/Adapters]` - Cambios en NexusBridge o adapters
- `[Trading]` - Cambios en trading_manager
- `[Strategies]` - Cambios en estrategias
- `[Handlers]` - Cambios en handlers de Telegram

## 💾 Backup Automático (Nuevo)

Antes de cada deploy, se crea automáticamente un backup de archivos críticos:

### Archivos respaldados:
- `system_directive.py` - Configuración central
- `nexus_loader.py` - Punto de entrada
- `railway.json` - Configuración Railway
- `requirements.txt` - Dependencias
- `nexus_system/core/` - Core del sistema
- `nexus_system/cortex/` - Estrategias
- `servos/` - Servicios auxiliares

### Gestión de backups:
- Se guardan en `backups/backup_YYYYMMDD_HHMMSS/`
- Se mantienen los últimos 5 backups automáticamente
- Los más antiguos se eliminan automáticamente

### Restaurar un backup:

```bash
# Listar backups disponibles
python backup_restore.py list

# Restaurar un backup específico
python backup_restore.py restore --backup backup_20241215_143022

# Simular restauración (sin cambios)
python backup_restore.py restore --backup backup_20241215_143022 --dry-run
```

## 🔍 Validaciones Pre-Deploy (Nuevo)

Los scripts ahora incluyen validaciones automáticas antes de hacer push:

### 0. Backup Automático
- Crea backup de archivos críticos antes del deploy
- Se guardan en `backups/backup_TIMESTAMP/`
- Mantiene últimos 5 backups automáticamente
- **Siempre se ejecuta** (protección de datos)

### 1. Verificación de Dependencias
- Verifica que todas las dependencias de `requirements.txt` estén instaladas
- Detecta paquetes faltantes antes del deploy
- Muestra lista de dependencias faltantes
- **Se puede omitir** (pregunta si continuar)

### 2. Verificación de Sintaxis Python
- Compila todos los archivos `.py` modificados
- Detecta errores de sintaxis antes del deploy
- **No se puede omitir** (crítico)

### 3. Verificación de Linter (Opcional)
- Ejecuta `pylint` o `flake8` si está disponible
- Detecta problemas de estilo y código
- Se puede omitir con `--skip-lint` o `-SkipLint`

### 4. Ejecución de Tests (Opcional)
- Ejecuta `pytest tests` antes del deploy
- Detecta regresiones
- Se puede omitir con `--skip-tests` o `-SkipTests`
- Si fallan, pregunta si continuar

### Ejemplo con Validaciones:

```powershell
# Deploy con todas las validaciones (recomendado)
.\deploy.ps1 -Message "Fix: Bug crítico"
# Ejecuta: Backup → Dependencias → Sintaxis → Linter → Tests → Deploy

# Deploy omitiendo tests (más rápido)
.\deploy.ps1 -Message "Fix: Typo" -SkipTests
# Ejecuta: Backup → Dependencias → Sintaxis → Linter → Deploy

# Deploy omitiendo linter y tests (muy rápido)
.\deploy.ps1 -Message "Fix: Comentario" -SkipLint -SkipTests
# Ejecuta: Backup → Dependencias → Sintaxis → Deploy
```

### Orden de Ejecución:

```
1. 💾 Backup automático (siempre)
2. 📦 Verificación de dependencias
3. ✅ Verificación de sintaxis Python (obligatorio)
4. 🔍 Verificación de linter (opcional)
5. 🧪 Ejecución de tests (opcional)
6. 📝 Commit
7. 🚀 Push
8. 📧 Notificación (opcional)
```

## 📧 Notificaciones (Nuevo)

Puedes recibir notificaciones en Telegram cuando el deploy sea exitoso:

### Configuración:

1. Asegúrate de tener estas variables en tu `.env`:
   ```
   TELEGRAM_BOT_TOKEN=tu_bot_token
   TELEGRAM_ADMIN_ID=tu_chat_id
   ```

2. Usa el flag `--notify` o `-Notify`:

```powershell
# Deploy con notificación
.\deploy.ps1 -Message "Fix: Bug" -Notify
```

La notificación incluirá:
- ✅ Estado del deploy
- 📝 Mensaje de commit
- 🌿 Branch actual
- ⏰ Timestamp

## 🛡️ Seguridad

**IMPORTANTE**: Los scripts NO incluyen:
- Variables de entorno (`.env`)
- Archivos sensibles
- Credenciales

Estos están en `.gitignore` y NO se subirán a GitHub.

## 🐛 Troubleshooting

### Error: "Git no está instalado"
- Instala Git desde: https://git-scm.com/downloads
- Asegúrate de que esté en PATH

### Error: "No estás en un repositorio Git"
- Ejecuta el script desde la raíz del proyecto
- Verifica que exista la carpeta `.git`

### Error: "Error al hacer push"
- Verifica tu conexión a internet
- Confirma que tienes permisos en el repositorio
- Intenta: `git push origin main` manualmente

### Railway no despliega automáticamente
- Verifica la conexión GitHub → Railway en el dashboard
- Revisa los logs de Railway
- Confirma que el branch está configurado correctamente

## 💡 Tips

1. **Siempre revisa los cambios antes de deployar**:
   ```bash
   git status
   git diff
   ```

2. **Usa mensajes descriptivos**:
   ```bash
   .\deploy.ps1 -Message "Fix: Corrección de órdenes condicionales en BinanceAdapter"
   ```

3. **Para cambios grandes, haz commits pequeños**:
   - Mejor: Varios commits pequeños
   - Evita: Un commit gigante con todo

4. **Monitorea el despliegue en Railway**:
   - Dashboard: https://railway.app
   - Revisa logs en tiempo real

## 📚 Recursos

- [Railway Docs](https://docs.railway.app)
- [Git Documentation](https://git-scm.com/doc)
- [GitHub Actions](https://docs.github.com/en/actions) (Alternativa avanzada)

