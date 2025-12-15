"""
Antigravity Bot - Authentication & Authorization
Centralized Role-Based Access Control (RBAC) Module
"""
import os
from functools import wraps
from aiogram.types import Message, CallbackQuery
from utils.db import get_user_role

# --- HELPERS ---

def is_authorized_admin(chat_id: str) -> bool:
    """Check if user has ADMIN or OWNER role."""
    allowed, role = get_user_role(str(chat_id))
    return allowed and role in ['owner', 'admin']

def is_authorized_owner(chat_id: str) -> bool:
    """Check if user is OWNER (SuperAdmin)."""
    allowed, role = get_user_role(str(chat_id))
    return allowed and role == 'owner'

def is_authorized_user(chat_id: str) -> bool:
    """Check if user has any valid access (USER, ADMIN, OWNER)."""
    allowed, _ = get_user_role(str(chat_id))
    return allowed

# --- DECORATORS ---

def admin_only(func):
    """Decorator: restrict handler to ADMIN or OWNER only."""
    @wraps(func)
    async def wrapper(event, *args, **kwargs):
        # Determine user and chat_id from event type
        user = None
        chat_id = None
        
        if isinstance(event, Message):
            user = event.from_user
            chat_id = str(event.chat.id)
        elif isinstance(event, CallbackQuery):
            user = event.from_user
            chat_id = str(event.message.chat.id)
            
        if not chat_id or not is_authorized_admin(chat_id):
            # Block Access
            if isinstance(event, Message):
                await event.answer("⛔ **Acceso Denegado**\nComando reservado para administradores.", parse_mode="Markdown")
            elif isinstance(event, CallbackQuery):
                await event.answer("⛔ Reservado para administradores", show_alert=True)
            return
            
        return await func(event, *args, **kwargs)
    return wrapper

def owner_only(func):
    """Decorator: restrict handler to OWNER only."""
    @wraps(func)
    async def wrapper(event, *args, **kwargs):
        user = None
        chat_id = None
        
        if isinstance(event, Message):
            user = event.from_user
            chat_id = str(event.chat.id)
        elif isinstance(event, CallbackQuery):
            user = event.from_user
            chat_id = str(event.message.chat.id)
            
        if not chat_id or not is_authorized_owner(chat_id):
            if isinstance(event, Message):
                await event.answer("⛔ **Acceso Denegado**\nComando reservado para el DUEÑO.", parse_mode="Markdown")
            elif isinstance(event, CallbackQuery):
                await event.answer("⛔ Reservado para el Owner", show_alert=True)
            return
            
        return await func(event, *args, **kwargs)
    return wrapper
