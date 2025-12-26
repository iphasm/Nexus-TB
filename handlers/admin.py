from aiogram import Router, types
from aiogram.filters import Command
from aiogram.types import Message
import os
from servos.db import add_system_user, remove_system_user, get_all_system_users, get_user_role
from datetime import datetime
from servos.auth import admin_only, owner_only

router = Router()


@router.message(Command("addsub"))
@admin_only
async def cmd_addsub(message: Message):
        
    try:
        args = message.text.split()
        if len(args) < 4:
            await message.answer("⚠️ Uso: /addsub [Nombre] [ChatID] [Días]")
            return
            
        name = args[1]
        target_chat_id = args[2]
        days = int(args[3])
        
        success, res = add_system_user(name, target_chat_id, days, 'user')
        
        if success:
            expiry = datetime.now().timestamp() + (days * 86400)
            date_str = datetime.fromtimestamp(expiry).strftime('%d/%m/%Y')
            await message.answer(f"✅ Suscriptor Agregado\n👤 {name} (ID: {res})\n⏳ Vence: {date_str}")
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
            await message.answer("⚠️ Uso: /addadmin [Nombre] [ChatID]")
            return
            
        name = args[1]
        target_chat_id = args[2]
        
        success, res = add_system_user(name, target_chat_id, None, 'admin')
        
        if success:
            await message.answer(f"✅ Admin Agregado\n🛡️ {name} (ID: {res})\n♾️ Acceso Permanente")
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
            await message.answer("⚠️ Uso: /remsub [ID_Numerico]")
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

import system_directive as qconfig

@router.message(Command("ml_mode"))
@admin_only
async def cmd_ml_mode(message: Message):
    """
    Activa o desactiva el módulo de clasificación por Machine Learning.
    """
    args = message.text.split()
    if len(args) < 2:
        state = "✅ ACTIVADO" if qconfig.ML_CLASSIFIER_ENABLED else "❌ DESACTIVADO"
        model_exists = "📦 (Modelo Encontrado)" if os.path.exists(os.path.join(os.getcwd(), 'nexus_system', 'memory_archives', 'ml_model.pkl')) else "⚠️ (Modelo NO Encontrado)"
        
        await message.answer(f"🤖 Estado ML Classifier: {state} {model_exists}\n\nUso: /ml_mode [on/off]")
        return

    mode = args[1].lower()
    if mode == 'on':
        qconfig.ML_CLASSIFIER_ENABLED = True
        await message.answer("🧠 ML Classifier ACTIVADO\nEl bot intentará usar el modelo predictivo para seleccionar estrategias.\nNota: Si no hay modelo, usará fallback a lógica clásica.")
    elif mode == 'off':
        qconfig.ML_CLASSIFIER_ENABLED = False
        await message.answer("🛑 ML Classifier DESACTIVADO\nEl bot usará exclusivamente la lógica clásica basada en reglas.")
    else:
        await message.answer("⚠️ Uso: /ml_mode [on/off]")


@router.message(Command("retrain"))
@owner_only
async def cmd_retrain(message: Message):
    """
    Fuerza el reentrenamiento del modelo ML.
    Solo disponible para el owner. Operación pesada (~3-5 min).
    """
    import subprocess
    import sys
    import asyncio
    
    await message.answer(
        "🧠 **REENTRENAMIENTO ML INICIADO**\n\n"
        "⏳ Este proceso toma ~3-5 minutos.\n"
        "📊 Se elimina el modelo anterior y entrena uno nuevo.\n\n"
        "_Recibirás un mensaje cuando termine..._"
    )
    
    model_path = os.path.join(os.getcwd(), 'nexus_system', 'memory_archives', 'ml_model.pkl')
    
    # 1. Delete old model
    if os.path.exists(model_path):
        try:
            os.remove(model_path)
            await message.answer("🗑️ Modelo anterior eliminado.")
        except Exception as e:
            await message.answer(f"⚠️ No se pudo eliminar modelo: {e}")
    
    # 2. Run training in background
    try:
        # Run training script asynchronously
        process = await asyncio.create_subprocess_exec(
            sys.executable, 'train_cortex.py',
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=os.getcwd()
        )
        
        stdout, stderr = await asyncio.wait_for(
            process.communicate(), 
            timeout=6000  # 100 min max
        )
        
        if process.returncode == 0:
            # Parse output for key stats
            output = stdout.decode('utf-8', errors='ignore')
            
            # Extract accuracy from output
            accuracy = "N/A"
            if "accuracy" in output.lower():
                for line in output.split('\n'):
                    if "accuracy" in line.lower() and "0." in line:
                        parts = line.split()
                        for p in parts:
                            try:
                                val = float(p)
                                if 0 < val < 1:
                                    accuracy = f"{val:.1%}"
                                    break
                            except:
                                pass
            
            await message.answer(
                "✅ **REENTRENAMIENTO COMPLETADO**\n\n"
                f"📦 Modelo guardado en: `ml_model.pkl`\n"
                f"📊 Accuracy: {accuracy}\n\n"
                "🔄 El nuevo modelo ya está activo."
            )
            
            # Force reload of model
            try:
                from nexus_system.cortex.ml_classifier import MLClassifier
                MLClassifier._model_loaded = False
                MLClassifier._model = None
                MLClassifier.load_model()
            except:
                pass
                
        else:
            error_msg = stderr.decode('utf-8', errors='ignore')[-500:]
            await message.answer(f"❌ ERROR EN ENTRENAMIENTO\n\n{error_msg}")
            
    except asyncio.TimeoutError:
        await message.answer("❌ TIMEOUT: El entrenamiento tardó más de 10 minutos.")
    except Exception as e:
        await message.answer(f"❌ ERROR: {e}")


@router.message(Command("wsstatus"))
@admin_only
async def cmd_wsstatus(message: Message, **kwargs):
    """
    Muestra el estado del WebSocket de datos de mercado.
    """
    try:
        # Try to get the engine instance from the session manager
        session_manager = kwargs.get('session_manager')
        
        msg = "📡 **WEBSOCKET STATUS**\n━━━━━━━━━━━━━━━━━━\n\n"
        
        # Check if ws_manager module exists
        try:
            from nexus_system.uplink.ws_manager import BinanceWSManager
            from nexus_system.uplink.price_cache import get_price_cache
            
            cache = get_price_cache()
            stats = cache.get_stats()
            
            if stats['symbols'] > 0:
                msg += f"✅ **Cache Activo**\n"
                msg += f"📊 Símbolos: `{stats['symbols']}`\n"
                msg += f"🕯️ Candles totales: `{stats['total_candles']}`\n\n"
                
                msg += "**Últimas actualizaciones:**\n"
                for symbol, details in list(stats['symbols_detail'].items())[:5]:
                    count = details['count']
                    last = details.get('last_update', 'N/A')
                    if hasattr(last, 'strftime'):
                        last = last.strftime('%H:%M:%S')
                    msg += f"• `{symbol}`: {count} candles | {last}\n"
            else:
                msg += "⚠️ **Cache Vacío**\n"
                msg += "_El WebSocket puede no estar conectado o aún no ha recibido datos._\n"
                
        except ImportError:
            msg += "❌ **Módulo WebSocket no disponible**\n"
            msg += "_Ejecuta: pip install websockets_\n"
        except Exception as e:
            msg += f"⚠️ Error obteniendo stats: {e}\n"
        
        msg += "\n━━━━━━━━━━━━━━━━━━\n"
        msg += "💡 Usa `/diag [SYMBOL]` para diagnóstico completo."
        
        await message.answer(msg, parse_mode="Markdown")
        
    except Exception as e:
        await message.answer(f"❌ Error: {e}")
