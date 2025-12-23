"""
Antigravity Bot - Timezone Manager
Handles user timezone preferences and time conversions.
"""

import os
from datetime import datetime, timezone as tz
from zoneinfo import ZoneInfo
from typing import Optional
from utils.db import get_connection

# Default timezone for all users
DEFAULT_TIMEZONE = "GMT-4"


def get_user_timezone(user_id: int) -> str:
    """Get user's timezone from database, returns DEFAULT_TIMEZONE if not set."""
    try:
        conn = get_connection()
        if not conn:
            return DEFAULT_TIMEZONE
        
        cur = conn.cursor()
        # Use chat_id (VARCHAR) which is the primary key column
        cur.execute("SELECT timezone FROM users WHERE chat_id = %s", (str(user_id),))
        row = cur.fetchone()
        cur.close()
        conn.close()
        
        if row and row[0]:
            return row[0]
        return DEFAULT_TIMEZONE
    except Exception as e:
        print(f"⚠️ Timezone fetch error: {e}")
        return DEFAULT_TIMEZONE


def set_user_timezone(user_id: int, tz_name: str) -> tuple[bool, str]:
    """
    Set user's timezone. Returns (success, message).
    Validates timezone name before saving.
    """
    # Validate timezone
    try:
        ZoneInfo(tz_name)
    except Exception:
        return False, f"❌ Zona horaria inválida: `{tz_name}`\nEjemplos válidos: `UTC`, `America/New_York`, `Europe/Madrid`"
    
    try:
        conn = get_connection()
        if not conn:
            return False, "❌ Error de conexión a base de datos"
        
        cur = conn.cursor()
        # Use chat_id (VARCHAR) which has the UNIQUE constraint
        chat_id_str = str(user_id)
        
        # Try update first, then insert if no rows affected
        cur.execute("""
            UPDATE users SET timezone = %s WHERE chat_id = %s
        """, (tz_name, chat_id_str))
        
        if cur.rowcount == 0:
            # User doesn't exist, insert new row
            cur.execute("""
                INSERT INTO users (chat_id, timezone) VALUES (%s, %s)
                ON CONFLICT (chat_id) DO UPDATE SET timezone = EXCLUDED.timezone
            """, (chat_id_str, tz_name))
        
        conn.commit()
        cur.close()
        conn.close()
        
        return True, f"✅ Zona horaria configurada: `{tz_name}`"
    except Exception as e:
        print(f"⚠️ Timezone save error: {e}")
        return False, f"❌ Error al guardar: {e}"


def get_current_time(user_id: int) -> datetime:
    """Get current time in user's timezone."""
    tz_name = get_user_timezone(user_id)
    try:
        user_tz = ZoneInfo(tz_name)
        return datetime.now(user_tz)
    except Exception:
        return datetime.now(tz.utc)


def get_current_time_str(user_id: int, fmt: str = "%Y-%m-%d %H:%M:%S %Z") -> str:
    """Get formatted current time string in user's timezone."""
    return get_current_time(user_id).strftime(fmt)


def convert_to_utc(dt: datetime, user_id: int) -> datetime:
    """Convert a naive datetime from user's timezone to UTC."""
    tz_name = get_user_timezone(user_id)
    try:
        user_tz = ZoneInfo(tz_name)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=user_tz)
        return dt.astimezone(tz.utc)
    except Exception:
        return dt.replace(tzinfo=tz.utc)


def convert_from_utc(dt: datetime, user_id: int) -> datetime:
    """Convert a UTC datetime to user's timezone."""
    tz_name = get_user_timezone(user_id)
    try:
        user_tz = ZoneInfo(tz_name)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=tz.utc)
        return dt.astimezone(user_tz)
    except Exception:
        return dt


# Common timezone aliases for user convenience
TIMEZONE_ALIASES = {
    "EST": "America/New_York",
    "PST": "America/Los_Angeles",
    "CST": "America/Chicago",
    "MST": "America/Denver",
    "CET": "Europe/Paris",
    "GMT": "Etc/GMT",
    "JST": "Asia/Tokyo",
    "AEST": "Australia/Sydney",
    # Caribbean / Dominican Republic
    "AST": "America/Santo_Domingo",
    "RD": "America/Santo_Domingo",
    "GMT-4": "America/Santo_Domingo",
}


def resolve_timezone(tz_input: str) -> str:
    """Resolve common timezone aliases to IANA names."""
    upper = tz_input.upper()
    if upper in TIMEZONE_ALIASES:
        return TIMEZONE_ALIASES[upper]
    return tz_input
