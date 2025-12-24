from aiogram import Router, types
from aiogram.filters import Command
from aiogram.types import Message
import os
from utils.db import add_system_user, remove_system_user, get_all_system_users, get_user_role
from datetime import datetime

router = Router()

from utils.auth import admin_only, owner_only


@router.message(Command("addsub"))
@admin_only
async def cmd_addsub(message: Message):
        
    try:
        args = message.text.split()
        if len(args) < 4:
            await message.answer("⚠️ Uso: `/addsub [Nombre] [ChatID] [Días]`")
            return
            
        name = args[1]
        target_chat_id = args[2]
        days = int(args[3])
        
        success, res = add_system_user(name, target_chat_id, days, 'user')
        
        if success:
            expiry = datetime.now().timestamp() + (days * 86400)
            date_str = datetime.fromtimestamp(expiry).strftime('%d/%m/%Y')
            await message.answer(f"✅ **Suscriptor Agregado**\n👤 {name} (ID: `{res}`)\n⏳ Vence: {date_str}")
        else:
            await message.answer(f"❌ Error: {res}")
            
    except ValueError:
        await message.answer("❌ 'Días' debe ser un número.")
    except Exception as e:
        await message.answer(f"❌ Error: {e}")

@router.message(Command("addadmin"))
@owner_only
async def cmd_addadmin(message: Message):
        
    try:
        args = message.text.split()
        if len(args) < 3:
            await message.answer("⚠️ Uso: `/addadmin [Nombre] [ChatID]`")
            return
            
        name = args[1]
        target_chat_id = args[2]
        
        success, res = add_system_user(name, target_chat_id, None, 'admin')
        
        if success:
            await message.answer(f"✅ **Admin Agregado**\n🛡️ {name} (ID: `{res}`)\n♾️ Acceso Permanente")
        else:
            await message.answer(f"❌ Error: {res}")
            
    except Exception as e:
        await message.answer(f"❌ Error: {e}")

@router.message(Command("remsub"))
@admin_only
async def cmd_remsub(message: Message):
        
    try:
        args = message.text.split()
        if len(args) < 2:
            await message.answer("⚠️ Uso: `/remsub [ID_Numerico]`")
            return
            
        user_id = int(args[1])
        if remove_system_user(user_id):
            await message.answer(f"🗑️ Usuario {user_id} eliminado de la DB.")
        else:
            await message.answer(f"⚠️ No se encontró el ID {user_id}.")
            
    except ValueError:
        await message.answer("❌ ID debe ser número.")

@router.message(Command("subs"))
@admin_only
async def cmd_subs(message: Message):
        
    users = get_all_system_users()
    
    # Get Owner from ENV for display
    env_owner = os.getenv('TELEGRAM_CHAT_ID', '').split(',')
    
    msg = "📂 **LISTADO DE USUARIOS**\n\n"
    msg += "👑 **SUPER OWNER (ENV)**:\n"
    for o in env_owner:
        if o: msg += f"• `{o}`\n"
    
    admins = [u for u in users if u['role'] == 'admin']
    subs = [u for u in users if u['role'] == 'user']
    
    msg += "\n🛡️ **ADMINS DB**:\n"
    if not admins: msg += "_Ninguno_\n"
    for a in admins:
        msg += f"🆔 `{a['id']}` | {a['name']} (`{a['chat_id']}`)\n"
        
    msg += "\n👥 **SUSCRIPTORES**:\n"
    if not subs: msg += "_Ninguno_\n"
    for s in subs:
        expiry = "???"
        if s['expires_at']:
            days_left = (s['expires_at'] - datetime.now()).days
            expiry = f"{days_left}d" if days_left >= 0 else "VENCIDO"
            
        msg += f"🆔 `{s['id']}` | {s['name']} | ⏳ {expiry}\n"
        
    await message.answer(msg, parse_mode="Markdown")

import antigravity_quantum.config as qconfig

@router.message(Command("ml_mode"))
@admin_only
async def cmd_ml_mode(message: Message):
    """
    Activa o desactiva el módulo de clasificación por Machine Learning.
    """
    args = message.text.split()
    if len(args) < 2:
        state = "✅ ACTIVADO" if qconfig.ML_CLASSIFIER_ENABLED else "❌ DESACTIVADO"
        model_exists = "📦 (Modelo Encontrado)" if os.path.exists(os.path.join(os.getcwd(), 'antigravity_quantum', 'data', 'ml_model.pkl')) else "⚠️ (Modelo NO Encontrado)"
        
        await message.answer(f"🤖 **Estado ML Classifier**: {state} {model_exists}\n\nUso: `/ml_mode [on/off]`")
        return

    mode = args[1].lower()
    if mode == 'on':
        qconfig.ML_CLASSIFIER_ENABLED = True
        await message.answer("🧠 **ML Classifier ACTIVADO**\nEl bot intentará usar el modelo predictivo para seleccionar estrategias.\n_Nota: Si no hay modelo, usará fallback a lógica clásica._")
    elif mode == 'off':
        qconfig.ML_CLASSIFIER_ENABLED = False
        await message.answer("🛑 **ML Classifier DESACTIVADO**\nEl bot usará exclusivamente la lógica clásica basada en reglas.")
    else:
        await message.answer("⚠️ Uso: `/ml_mode [on/off]`")

