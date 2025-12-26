"""
NEXUS TRADING BOT - Task Scheduler
LLM-powered task scheduling using APScheduler and OpenAI.
"""

import os
import json
import asyncio
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any, Callable
from zoneinfo import ZoneInfo

import openai
from dotenv import load_dotenv

load_dotenv()

# Maximum tasks per user
MAX_TASKS_PER_USER = 10


class TaskScheduler:
    """
    Manages scheduled tasks using APScheduler with PostgreSQL job store.
    Uses OpenAI to parse natural language scheduling requests.
    """
    
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY", "").strip("'\" ")
        self.client = None
        self.scheduler = None
        self.action_handlers: Dict[str, Callable] = {}
        self._initialized = False
        
        if self.api_key:
            try:
                self.client = openai.OpenAI(api_key=self.api_key)
                print("✅ TaskScheduler: OpenAI client initialized")
            except Exception as e:
                print(f"⚠️ TaskScheduler: OpenAI init failed: {e}")
        else:
            print("⚠️ TaskScheduler: No OPENAI_API_KEY found")
    
    async def initialize(self, bot=None):
        """Initialize the APScheduler with async support."""
        if self._initialized:
            return
        
        try:
            from apscheduler.schedulers.asyncio import AsyncIOScheduler
            from apscheduler.jobstores.memory import MemoryJobStore
            
            # Use memory store for simplicity (can upgrade to SQLAlchemy later)
            jobstores = {
                'default': MemoryJobStore()
            }
            
            self.scheduler = AsyncIOScheduler(jobstores=jobstores, timezone='UTC')
            self.bot = bot
            self._initialized = True
            print("✅ TaskScheduler: APScheduler initialized")
        except ImportError as e:
            print(f"⚠️ TaskScheduler: APScheduler not installed: {e}")
        except Exception as e:
            print(f"⚠️ TaskScheduler: Init error: {e}")
    
    def start(self):
        """Start the scheduler."""
        if self.scheduler and not self.scheduler.running:
            self.scheduler.start()
            print("🚀 TaskScheduler: Scheduler started")
    
    def shutdown(self, wait: bool = True):
        """Shutdown the scheduler gracefully."""
        if self.scheduler and self.scheduler.running:
            self.scheduler.shutdown(wait=wait)
            print("🛑 TaskScheduler: Scheduler stopped")
    
    def register_action(self, name: str, handler: Callable):
        """Register an action handler that can be scheduled."""
        self.action_handlers[name] = handler
        # print(f"📝 TaskScheduler: Registered action '{name}'")
    
    async def parse_task_with_llm(self, user_input: str, user_id: int, user_timezone: str = "UTC") -> Dict[str, Any]:
        """
        Use OpenAI to parse natural language task request into structured data.
        
        Returns:
            {
                "action": "analyze|sniper|news|alert|...",
                "params": {"symbol": "BTC", ...},
                "schedule": {
                    "type": "cron|date|interval",
                    "value": "..."
                },
                "description": "Human readable summary",
                "error": None or "Error message"
            }
        """
        if not self.client:
            return {"error": "IA no disponible. Configura OPENAI_API_KEY."}
        
        try:
            from servos.timezone_manager import get_current_time_str
            current_time = get_current_time_str(user_id)
        except:
            current_time = datetime.now().isoformat()
        
        system_prompt = """You are a task scheduling assistant for a trading bot. Parse the user's natural language request into a JSON object.

Available actions:
- "analyze": Analyze an asset (params: {"symbol": "BTC"})
- "sniper": Scan for trading opportunities (params: {})
- "news": Get market briefing (params: {})
- "sentiment": Check market sentiment (params: {"symbol": "BTC"} optional)
- "fomc": Federal Reserve analysis (params: {})
- "alert": Send a custom message (params: {"message": "..."})
- "dashboard": Send trading dashboard (params: {})
- "price_alert": Monitor price target (params: {"symbol": "BTC", "target": 90000, "condition": "above" | "below"})

Schedule types:
- "cron": For recurring tasks. Value is cron expression, e.g. "0 9 * * *" for daily at 9am
- "date": For one-time tasks. Value is ISO datetime, e.g. "2024-01-15T14:30:00"
- "interval": For repeating intervals. Value is like "5m", "1h", "30s"

IMPORTANT:
- All times should be converted to UTC based on the user's timezone.
- For "price alerts" (e.g. "Notify me when BTC hits 90k"), set action to "price_alert", schedule type to "interval", and value to "1m" (check every minute). Set 'condition' to 'above' if target > current price (implied), or 'below' otherwise.

Respond ONLY with valid JSON, no markdown or extra text."""

        user_prompt = f"""User timezone: {user_timezone}
Current time (user's local): {current_time}

Parse this request: "{user_input}"

Respond with JSON:
{{
  "action": "command_name",
  "params": {{}},
  "schedule": {{
    "type": "cron|date|interval",
    "value": "..."
  }},
  "description": "human readable summary in Spanish"
}}"""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=500,
                temperature=0.3
            )
            
            content = response.choices[0].message.content.strip()
            
            # Clean up potential markdown wrapping
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
            content = content.strip()
            
            result = json.loads(content)
            result["error"] = None
            return result
            
        except json.JSONDecodeError as e:
            return {"error": f"Error al parsear respuesta de IA: {e}"}
        except Exception as e:
            return {"error": f"Error de IA: {e}"}
    
    async def schedule_task(
        self, 
        user_id: int, 
        action: str, 
        params: Dict[str, Any], 
        schedule: Dict[str, str],
        description: str
    ) -> tuple[bool, str, Optional[str]]:
        """
        Schedule a new task.
        
        Returns: (success, message, task_id)
        """
        if not self.scheduler:
            return False, "❌ Scheduler no inicializado", None
        
        if action not in self.action_handlers:
            return False, f"❌ Acción desconocida: `{action}`", None
        
        # Check task limit
        from servos.db import get_scheduled_tasks
        existing = get_scheduled_tasks(user_id)
        if len(existing) >= MAX_TASKS_PER_USER:
            return False, f"❌ Límite alcanzado ({MAX_TASKS_PER_USER} tareas máximo)", None
        
        try:
            schedule_type = schedule.get("type", "date")
            schedule_value = schedule.get("value", "")
            
            job_kwargs = {
                "func": self._execute_task,
                "args": [user_id, action, params],
                "id": f"task_{user_id}_{datetime.utcnow().timestamp()}",
                "replace_existing": True
            }
            
            if schedule_type == "cron":
                # Parse cron expression: minute hour day month day_of_week
                parts = schedule_value.split()
                if len(parts) >= 5:
                    from apscheduler.triggers.cron import CronTrigger
                    trigger = CronTrigger(
                        minute=parts[0],
                        hour=parts[1],
                        day=parts[2],
                        month=parts[3],
                        day_of_week=parts[4],
                        timezone='UTC'
                    )
                    job_kwargs["trigger"] = trigger
                else:
                    return False, f"❌ Expresión cron inválida: `{schedule_value}`", None
                    
            elif schedule_type == "interval":
                from apscheduler.triggers.interval import IntervalTrigger
                # Parse interval: 5m, 1h, 30s
                value = schedule_value.lower()
                if value.endswith('m'):
                    minutes = int(value[:-1])
                    trigger = IntervalTrigger(minutes=minutes)
                elif value.endswith('h'):
                    hours = int(value[:-1])
                    trigger = IntervalTrigger(hours=hours)
                elif value.endswith('s'):
                    seconds = int(value[:-1])
                    trigger = IntervalTrigger(seconds=seconds)
                else:
                    return False, f"❌ Intervalo inválido: `{schedule_value}`", None
                job_kwargs["trigger"] = trigger
                
            elif schedule_type == "date":
                from apscheduler.triggers.date import DateTrigger
                run_date = datetime.fromisoformat(schedule_value.replace('Z', '+00:00'))
                trigger = DateTrigger(run_date=run_date, timezone='UTC')
                job_kwargs["trigger"] = trigger
            else:
                return False, f"❌ Tipo de schedule inválido: `{schedule_type}`", None
            
            # Add the job
            job = self.scheduler.add_job(**job_kwargs)
            
            # Save to database
            from servos.db import save_scheduled_task
            task_data = {
                "job_id": job.id,
                "action": action,
                "params": params,
                "schedule_type": schedule_type,
                "schedule_value": schedule_value,
                "description": description,
                "next_run": job.next_run_time.isoformat() if job.next_run_time else None
            }
            db_id = save_scheduled_task(user_id, task_data)
            
            next_run_str = job.next_run_time.strftime("%Y-%m-%d %H:%M UTC") if job.next_run_time else "N/A"
            
            return True, f"✅ Tarea programada!\n📋 {description}\n⏰ Próxima ejecución: `{next_run_str}`", job.id
            
        except Exception as e:
            return False, f"❌ Error al programar: {e}", None
    
    async def _execute_task(self, user_id: int, action: str, params: Dict[str, Any]):
        """Execute a scheduled task."""
        try:
            handler = self.action_handlers.get(action)
            if handler:
                print(f"⚡ Executing scheduled task: {action} for user {user_id}")
                await handler(user_id, params, self.bot)
            else:
                print(f"⚠️ No handler for action: {action}")
        except Exception as e:
            print(f"❌ Task execution error: {e}")
    
    def cancel_task(self, user_id: int, task_id: str) -> tuple[bool, str]:
        """Cancel a scheduled task."""
        if not self.scheduler:
            return False, "❌ Scheduler no inicializado"
        
        try:
            # Get task from DB to verify ownership
            from servos.db import get_scheduled_tasks, delete_scheduled_task
            tasks = get_scheduled_tasks(user_id)
            
            task = None
            for t in tasks:
                if str(t.get('id')) == str(task_id) or t.get('job_id') == task_id:
                    task = t
                    break
            
            if not task:
                return False, f"❌ Tarea no encontrada: `{task_id}`"
            
            # Remove from scheduler
            job_id = task.get('job_id')
            if job_id:
                try:
                    self.scheduler.remove_job(job_id)
                except:
                    pass  # Job may already be gone
            
            # Remove from DB
            delete_scheduled_task(task.get('id'))
            
            return True, f"✅ Tarea cancelada: {task.get('description', task_id)}"
            
        except Exception as e:
            return False, f"❌ Error al cancelar: {e}"
    
    def list_tasks(self, user_id: int) -> List[Dict[str, Any]]:
        """List all scheduled tasks for a user."""
        try:
            from servos.db import get_scheduled_tasks
            return get_scheduled_tasks(user_id)
        except Exception as e:
            print(f"⚠️ Error listing tasks: {e}")
            return []


# Global scheduler instance
_scheduler: Optional[TaskScheduler] = None


def get_scheduler() -> TaskScheduler:
    """Get or create the global scheduler instance."""
    global _scheduler
    if _scheduler is None:
        _scheduler = TaskScheduler()
    return _scheduler

