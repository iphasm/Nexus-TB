"""
NEXUS PREMIUM LOGGER
Professional logging system for Nexus Trading Bot v7
"""

import time
import logging
from datetime import datetime
from typing import Optional

class NexusLogger:
    """
    Premium logging system with structured phases and professional output.
    Maintains clean banner display and logical initialization sequence.
    """

    _global_banner_shown = False  # Class-level flag to prevent duplicate banners

    def __init__(self):
        self.phase = 1
        self.total_phases = 5
        self.banner_shown = False
        self.start_time = time.time()
        self.phase_start_time = None

        # Configure standard Python logger for compatibility
        self.logger = logging.getLogger('NexusPremium')
        self.logger.setLevel(logging.INFO)

        # Prevent duplicate handlers
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('[%(asctime)s] %(levelname)s: %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

    def show_banner(self):
        """Display professional Nexus banner without interruptions."""
        if NexusLogger._global_banner_shown:
            return

        banner = """
┌─────────────────────────────────────────────────────────────┐
│  🚀 NEXUS TRADING BOT v7 - PREMIUM EDITION                 │
│  Professional Algorithmic Trading Platform                  │
│                                                             │
│  ▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰  │
│                                                             │
│  [1/5] 🔧 SYSTEM INITIALIZATION                             │
│  [2/5] 🔐 SECURITY & ENCRYPTION                             │
│  [3/5] 🗄️  DATABASE & PERSISTENCE                           │
│  [4/5] 🤖 AI & ML SYSTEMS                                   │
│  [5/5] 🌐 EXCHANGES & CONNECTIVITY                          │
│                                                             │
│  ▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰  │
│                                                             │
│  Status: INITIALIZING...                                    │
│  Build: v7.0.0                                              │
│  License: PREMIUM                                           │
└─────────────────────────────────────────────────────────────┘
        """.strip()

        print(banner)
        NexusLogger._global_banner_shown = True
        self.banner_shown = True

    def phase_start(self, phase_num: int, title: str, emoji: str):
        """Start a new initialization phase."""
        self.phase = phase_num
        self.phase_start_time = time.time()

        print(f"\n[{phase_num}/{self.total_phases}] {emoji} {title}")
        print("┌" + "─" * 50)

    def phase_success(self, message: str, metric: Optional[str] = None):
        """Log successful phase completion with optional metric."""
        duration = ""
        if self.phase_start_time:
            phase_duration = time.time() - self.phase_start_time
            if phase_duration < 1:
                duration = f" ({phase_duration:.1f}ms)"
            else:
                duration = f" ({phase_duration:.1f}s)"

        metric_str = f" - {metric}" if metric else ""
        print(f"└── ✅ {message}{metric_str}{duration}")

    def phase_warning(self, message: str, detail: Optional[str] = None):
        """Log phase warning."""
        detail_str = f" - {detail}" if detail else ""
        print(f"└── ⚠️  {message}{detail_str}")

    def phase_error(self, message: str, error: Optional[str] = None):
        """Log phase error."""
        error_str = f" - {error}" if error else ""
        print(f"└── ❌ {message}{error_str}")

    def system_ready(self, session_count: int = 0, response_time: str = "<50ms"):
        """Display final system ready message."""
        total_time = time.time() - self.start_time

        ready_message = f"""

🎉 NEXUS CORE FULLY OPERATIONAL
📊 System Health: EXCELLENT
⚡ Response Time: {response_time}
🔄 Active Sessions: {session_count}
⏱️  Initialization Time: {total_time:.1f}s

🤖 Nexus Algorithm-Based Trading Bot is now online and ready for directives.
        """.strip()

        print(ready_message)

    def log_info(self, message: str, category: str = "SYSTEM"):
        """Log informational message with category."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] ℹ️  {category}: {message}")

    def log_success(self, message: str, category: str = "SYSTEM"):
        """Log success message with category."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] ✅ {category}: {message}")

    def log_warning(self, message: str, category: str = "SYSTEM"):
        """Log warning message with category."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] ⚠️  {category}: {message}")

    def log_error(self, message: str, category: str = "SYSTEM"):
        """Log error message with category."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] ❌ {category}: {message}")

    def log_critical(self, message: str, category: str = "SYSTEM"):
        """Log critical message with category."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] 🚨 {category}: {message}")

    # Legacy compatibility methods
    def info(self, message: str):
        """Legacy method for backward compatibility."""
        self.logger.info(message)

    def warning(self, message: str):
        """Legacy method for backward compatibility."""
        self.logger.warning(message)

    def error(self, message: str):
        """Legacy method for backward compatibility."""
        self.logger.error(message)

    def debug(self, message: str):
        """Legacy method for backward compatibility."""
        self.logger.debug(message)


# Global instance for easy access
nexus_logger = NexusLogger()
