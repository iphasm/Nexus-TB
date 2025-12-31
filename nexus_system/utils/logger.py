"""
Nexus Trading Bot - Sistema de Logging Optimizado para Railway

Este módulo proporciona un sistema de logging avanzado que:
- Agrupa mensajes similares para reducir spam
- Implementa debouncing para logs repetitivos
- Formatea logs de forma estructurada para Railway
- Permite control granular de verbosidad
"""
import logging
import os
import sys
import time
from typing import Dict, List, Optional
from collections import defaultdict
from threading import Lock

# Environment Configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
LOG_GROUP_INTERVAL = float(os.getenv("LOG_GROUP_INTERVAL", "5.0"))  # Agrupar logs cada 5 segundos
LOG_MAX_GROUP_SIZE = int(os.getenv("LOG_MAX_GROUP_SIZE", "10"))  # Máximo de mensajes por grupo

# Configure Root Logger con formato optimizado para Railway
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="[%(levelname)s] %(name)s: %(message)s",  # Formato más compacto
    datefmt="%H:%M:%S",
    handlers=[logging.StreamHandler(sys.stdout)]
)

# Silenciar librerías ruidosas
logging.getLogger("websockets").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("asyncio").setLevel(logging.WARNING)
logging.getLogger("yfinance").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("aiogram").setLevel(logging.INFO)
logging.getLogger("ccxt").setLevel(logging.WARNING)

# Configuración específica para Railway
QUIET_MODE = os.getenv("QUIET_MODE", "false").lower() == "true"
if QUIET_MODE:
    # En modo silencioso, reducir aún más los logs
    LOG_LEVEL = "WARNING"
    logging.getLogger().setLevel(logging.WARNING)


class GroupedLogger:
    """
    Logger que agrupa mensajes similares para reducir spam en Railway.
    """
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, LOG_LEVEL, logging.INFO))
        self._last_log: Dict[str, float] = {}
        self._grouped_logs: Dict[str, List[tuple]] = defaultdict(list)  # {pattern: [(time, msg), ...]}
        self._group_lock = Lock()
        self._last_flush = time.time()
    
    def _get_pattern(self, msg: str) -> Optional[str]:
        """
        Extrae un patrón del mensaje para agrupar logs similares.
        Reemplaza valores dinámicos con placeholders.
        """
        # Patrones comunes para agrupar
        patterns = [
            (r'Signal for \w+ skipped', 'Signal skipped'),
            (r'Session \d+.*disabled', 'Session disabled'),
            (r'Asset \w+.*blacklisted', 'Asset blacklisted'),
            (r'Active \w+ position exists', 'Position exists'),
            (r'FLIP DETECTED.*switching', 'Position flip'),
            (r'Order placed.*ID: \d+', 'Order placed'),
            (r'Balance sync.*\w+', 'Balance sync'),
            (r'Position sync.*\w+', 'Position sync'),
        ]
        
        import re
        for pattern, replacement in patterns:
            if re.search(pattern, msg):
                return replacement
        
        # Si no hay patrón, no agrupar
        return None
    
    def _flush_groups(self, force: bool = False):
        """Flush grupos de logs acumulados."""
        now = time.time()
        should_flush = force or (now - self._last_flush) >= LOG_GROUP_INTERVAL
        
        if not should_flush:
            return
        
        with self._group_lock:
            for pattern, messages in list(self._grouped_logs.items()):
                if not messages:
                    continue
                
                count = len(messages)
                if count > 1:
                    # Agrupar mensajes similares
                    latest_msg = messages[-1][1]  # Último mensaje
                    if count <= LOG_MAX_GROUP_SIZE:
                        self.logger.info(f"[{pattern}] x{count} - {latest_msg}")
                    else:
                        self.logger.info(f"[{pattern}] x{count} (último: {latest_msg})")
                else:
                    # Solo un mensaje, log normal
                    self.logger.info(messages[0][1])
                
                # Limpiar grupo
                self._grouped_logs[pattern] = []
            
            self._last_flush = now
    
    def info(self, msg: str, group: bool = True):
        """
        Log info con opción de agrupación.
        
        Args:
            msg: Mensaje a loguear
            group: Si True, intenta agrupar con mensajes similares
        """
        if group:
            pattern = self._get_pattern(msg)
            if pattern:
                with self._group_lock:
                    self._grouped_logs[pattern].append((time.time(), msg))
                    # Flush si el grupo está lleno
                    if len(self._grouped_logs[pattern]) >= LOG_MAX_GROUP_SIZE:
                        self._flush_groups(force=True)
                return
        
        # Log directo si no se agrupa
        self.logger.info(msg)
        self._flush_groups()  # Flush grupos pendientes
    
    def debug(self, msg: str):
        """Log debug (siempre directo, no se agrupa)."""
        self.logger.debug(msg)
    
    def warning(self, msg: str, group: bool = False):
        """Log warning con opción de agrupación."""
        if group:
            pattern = self._get_pattern(msg)
            if pattern:
                with self._group_lock:
                    self._grouped_logs[pattern].append((time.time(), msg))
                return
        
        self.logger.warning(msg)
        self._flush_groups()
    
    def error(self, msg: str):
        """Log error (siempre directo, crítico)."""
        self.logger.error(msg)
        self._flush_groups(force=True)  # Flush inmediato para errores
    
    def info_debounced(self, msg: str, interval: float = 60.0):
        """
        Log info solo si han pasado 'interval' segundos desde el último log idéntico.
        """
        now = time.time()
        last_time = self._last_log.get(msg, 0)
        
        if now - last_time > interval:
            self.info(msg, group=False)  # No agrupar logs debounced
            self._last_log[msg] = now
    
    def warning_debounced(self, msg: str, interval: float = 60.0):
        """Log warning solo si han pasado 'interval' segundos."""
        now = time.time()
        last_time = self._last_log.get(msg, 0)
        
        if now - last_time > interval:
            self.warning(msg, group=False)
            self._last_log[msg] = now
    
    def error_debounced(self, msg: str, interval: float = 60.0):
        """Log error solo si han pasado 'interval' segundos."""
        now = time.time()
        last_time = self._last_log.get(msg, 0)
        
        if now - last_time > interval:
            self.error(msg)
            self._last_log[msg] = now
    
    def flush(self):
        """Fuerza el flush de todos los grupos pendientes."""
        self._flush_groups(force=True)


class NexusLogger:
    """
    Logger principal con funcionalidades de agrupación y debouncing.
    Mantiene compatibilidad con la API anterior.
    """
    def __init__(self, name: str):
        self._grouped = GroupedLogger(name)
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, LOG_LEVEL, logging.INFO))
        self._last_log: Dict[str, float] = {}
    
    def info(self, msg: str, group: bool = True):
        """Log info con agrupación opcional."""
        self._grouped.info(msg, group=group)
    
    def debug(self, msg: str):
        """Log debug."""
        self._grouped.debug(msg)
    
    def warning(self, msg: str, group: bool = False):
        """Log warning con agrupación opcional."""
        self._grouped.warning(msg, group=group)
    
    def error(self, msg: str):
        """Log error (siempre directo)."""
        self._grouped.error(msg)
    
    def info_debounced(self, msg: str, interval: float = 60.0):
        """Log info debounced."""
        self._grouped.info_debounced(msg, interval)
    
    def warning_debounced(self, msg: str, interval: float = 60.0):
        """Log warning debounced."""
        self._grouped.warning_debounced(msg, interval)
    
    def error_debounced(self, msg: str, interval: float = 60.0):
        """Log error debounced."""
        self._grouped.error_debounced(msg, interval)
    
    def flush(self):
        """Fuerza flush de grupos."""
        self._grouped.flush()


def get_logger(name: str) -> NexusLogger:
    """
    Obtiene un logger Nexus con agrupación y debouncing.
    
    Args:
        name: Nombre del logger (ej: 'NexusCore', 'MarketStream')
    
    Returns:
        NexusLogger instance
    """
    return NexusLogger(name)


def log_startup_summary(logger: NexusLogger, components: Dict[str, bool]):
    """
    Log un resumen de inicio agrupado.
    
    Args:
        logger: Instancia de logger
        components: Dict con nombre de componente y estado (True/False)
    """
    success = [name for name, status in components.items() if status]
    failed = [name for name, status in components.items() if not status]
    
    summary = f"🚀 Inicio: {len(success)}/{len(components)} componentes OK"
    if failed:
        summary += f" | Fallos: {', '.join(failed)}"
    
    logger.info(summary, group=False)  # No agrupar resumen de inicio


# Funciones de utilidad para logging condicional
def conditional_log(level: str, message: str, condition: bool = True, logger_name: str = "NexusCore"):
    """
    Log condicional basado en nivel y condición.

    Args:
        level: Nivel de log ('DEBUG', 'INFO', 'WARNING', 'ERROR')
        message: Mensaje a loguear
        condition: Condición para loguear (default: True)
        logger_name: Nombre del logger (default: 'NexusCore')
    """
    if not condition:
        return

    logger = get_logger(logger_name)
    level = level.upper()

    if level == 'DEBUG':
        logger.debug(message)
    elif level == 'INFO':
        logger.info(message)
    elif level == 'WARNING':
        logger.warning(message)
    elif level == 'ERROR':
        logger.error(message)


def quiet_log(message: str, logger_name: str = "NexusCore"):
    """
    Log solo en modo DEBUG o cuando no está QUIET_MODE activado.
    Útil para reducir ruido en producción.
    """
    if QUIET_MODE and LOG_LEVEL != "DEBUG":
        return

    logger = get_logger(logger_name)
    logger.debug(message)
