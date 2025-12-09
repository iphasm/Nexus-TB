import time
import os
import threading
import telebot
from dotenv import load_dotenv

# Importar módulos internos
from data.fetcher import get_market_data
from strategies.analyzer import analyze_market
from utils.trading_manager import SessionManager

# Cargar variables de entorno
load_dotenv()

# --- CONFIGURACIÓN ---
WATCHLIST = [
    'BTCUSDT', 'ETHUSDT', 'XRPUSDT', 'SOLUSDT', 'SUIUSDT', 'ZECUSDT',
    'TSLA', 'NVDA', 'MSFT',
    'GC=F', 'CL=F']

# Configuración Global de Estrategia
STRATEGY_CONFIG = {
    'mean_reversion': True,
    'trend_velocity': True
}

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_ADMIN_ID = os.getenv('TELEGRAM_ADMIN_ID')
# Nota: TELEGRAM_CHAT_IDS es menos relevante para comandos ahora, ¿pero útil para transmisiones?
# Usaremos sesiones válidas para transmisiones potencialmente, o mantendremos la variable de entorno para alertas de administrador.
TELEGRAM_CHAT_IDS = [id.strip() for id in os.getenv('TELEGRAM_CHAT_ID', '').split(',') if id.strip()]

# Inicializar Bot
bot = None
session_manager = None # Gestor de sesiones global

if TELEGRAM_TOKEN:
    bot = telebot.TeleBot(TELEGRAM_TOKEN)
else:
    print("ADVERTENCIA: No se encontró TELEGRAM_TOKEN.")

def send_alert(message):
    """Transmite el mensaje a todas las sesiones registradas + IDs de chat del entorno"""
    # 1. IDs de chat del entorno
    targets = set(TELEGRAM_CHAT_IDS)
    
    # 2. Agregar Sesiones Activas
    if session_manager:
        for s in session_manager.get_all_sessions():
            targets.add(s.chat_id)
            
    if bot and targets:
        for chat_id in targets:
            try:
                bot.send_message(chat_id, message, parse_mode='Markdown')
            except Exception as e:
                print(f"Error enviando alerta a {chat_id}: {e}")
    else:
        print(f"ALERTA (Sin Telegram): {message}")

# --- MANEJADORES DE COMANDOS DEL BOT ---

@bot.message_handler(commands=['strategies'])
def handle_strategies_status(message):
    """Muestra el estado actual de la estrategia"""
    status_text = "🧠 **Estrategias Activas**\n\n"
    
    mr_icon = "✅" if STRATEGY_CONFIG['mean_reversion'] else "🔴"
    tv_icon = "✅" if STRATEGY_CONFIG['trend_velocity'] else "🔴"
    
    status_text += f"{mr_icon} **Reversión a la Media** (`mr`)\n"
    status_text += f"{tv_icon} **Velocidad de Tendencia** (`tv`)\n\n"
    status_text += "Usa `/toggle <nombre>` para cambiar."
    
    bot.reply_to(message, status_text, parse_mode='Markdown')

@bot.message_handler(commands=['toggle'])
def handle_toggle_strategy(message):
    """Activa/Desactiva una estrategia"""
    try:
        args = message.text.split()
        if len(args) < 2:
            bot.reply_to(message, "⚠️ Uso: `/toggle mr` o `/toggle tv`", parse_mode='Markdown')
            return
            
        target = args[1].lower()
        
        if target in ['mr', 'mean_reversion']:
            key = 'mean_reversion'
            name = "Reversión a la Media"
        elif target in ['tv', 'trend_velocity', 'trend']:
            key = 'trend_velocity'
            name = "Velocidad de Tendencia"
        else:
            bot.reply_to(message, "❌ Estrategia desconocida. Usa `mr` o `tv`.")
            return
            
        # Cambiar estado
        STRATEGY_CONFIG[key] = not STRATEGY_CONFIG[key]
        state = "✅ ACTIVADA" if STRATEGY_CONFIG[key] else "🔴 DESACTIVADA"
        
        bot.reply_to(message, f"🔄 **{name}** está ahora {state}")
        print(f"Actualización de Estrategia: {STRATEGY_CONFIG}")
        
    except Exception as e:
        bot.reply_to(message, f"❌ Error: {e}")

@bot.message_handler(commands=['set_keys'])
def handle_set_keys(message):
    """
    Uso: /set_keys <API_KEY> <API_SECRET>
    """
    chat_id = str(message.chat.id)
    try:
        args = message.text.split()
        if len(args) < 3:
            bot.reply_to(message, "⚠️ Uso: `/set_keys <API_KEY> <API_SECRET>`\n\n_Recomendamos borrar este mensaje después de enviarlo._", parse_mode='Markdown')
            return
        
        api_key = args[1]
        api_secret = args[2]
        
        # Crear o Actualizar Sesión
        session = session_manager.create_or_update_session(chat_id, api_key, api_secret)
        
        if session.client:
            bot.reply_to(message, "✅ **¡Claves API Registradas!**\nAhora puedes operar. Configuración predeterminada: Apalancamiento 5x, Margen 10%. Usa /config para ver.")
        else:
            bot.reply_to(message, "❌ Claves guardadas, pero **Falló la Conexión con Binance**. Por favor verifica tus claves y permisos.")
            
    except Exception as e:
        bot.reply_to(message, f"❌ Error: {e}")

@bot.message_handler(commands=['delete_keys'])
def handle_delete_keys(message):
    chat_id = str(message.chat.id)
    if session_manager.delete_session(chat_id):
        bot.reply_to(message, "🗑️ **Sesión Eliminada.** Tus claves han sido eliminadas de este bot.")
    else:
        bot.reply_to(message, "⚠️ No se encontró ninguna sesión para eliminar.")

@bot.message_handler(commands=['long'])
def handle_long_position(message):
    """Activa manualmente una posición LONG para la sesión de chat actual"""
    chat_id = str(message.chat.id)
    session = session_manager.get_session(chat_id)
    
    if not session or not session.client:
        bot.reply_to(message, "⛔ **Sin Sesión Activa.**\nPor favor registra tus claves API de Binance primero usando:\n`/set_keys <API_KEY> <API_SECRET>`", parse_mode='Markdown')
        return

    # Analizar mensaje: /long BTC
    try:
        args = message.text.split()
        if len(args) < 2:
            bot.reply_to(message, "⚠️ Uso: `/long <SIMBOLO>` (ej., `/long BTC`)", parse_mode='Markdown')
            return
            
        symbol = args[1].upper()
        if 'USDT' not in symbol:
            symbol += 'USDT'
            
        bot.reply_to(message, f"⚡ Ejecutando LONG para **{symbol}**...", parse_mode='Markdown')
        
        # Ejecutar en sesión específica
        success, msg = session.execute_long_position(symbol)
        if success:
            bot.reply_to(message, f"✅ {msg}")
        else:
            bot.reply_to(message, f"❌ Operación Fallida: {msg}")

    except Exception as e:
        bot.reply_to(message, f"❌ Error: {e}")

@bot.message_handler(commands=['sell', 'close'])
def handle_sell_position(message):
    """Cierra manualmente una posición"""
    chat_id = str(message.chat.id)
    session = session_manager.get_session(chat_id)
    if not session:
        bot.reply_to(message, "⛔ Sesión no encontrada.") 
        return

    try:
        args = message.text.split()
        if len(args) < 2:
            bot.reply_to(message, "⚠️ Uso: `/sell <SIMBOLO>` (ej. `/sell BTC`)", parse_mode='Markdown')
            return
            
        symbol = args[1].upper()
        if 'USDT' not in symbol: symbol += 'USDT'
        
        bot.reply_to(message, f"📉 Cerrando posición para **{symbol}**...", parse_mode='Markdown')
        
        success, msg = session.execute_close_position(symbol)
        bot.reply_to(message, msg if success else f"⚠️ {msg}", parse_mode='Markdown')

    except Exception as e:
        bot.reply_to(message, f"❌ Error: {e}")

@bot.message_handler(commands=['pnl', 'profit'])
def handle_pnl_request(message):
    """Muestra el PnL realizado de Binance"""
    chat_id = str(message.chat.id)
    session = session_manager.get_session(chat_id)
    if not session: 
        bot.reply_to(message, "⛔ Sesión no encontrada.")
        return
    
    bot.send_chat_action(message.chat.id, 'typing')
    
    # Obtener Últimas 24h
    total_pnl, history = session.get_pnl_history(days=1)
    
    icon = "🟢" if total_pnl >= 0 else "🔴"
    
    report = (
        f"💰 **Comprobación Diaria de PnL**\n"
        f"Total (24h): {icon} **${total_pnl:.2f}**\n\n"
        f"**Operaciones Recientes:**\n"
    )
    
    if not history:
        report += "No se encontraron operaciones realizadas en las últimas 24h."
    else:
        # Mostrar últimas 5
        for trade in history[-5:]: 
            s_icon = "🟢" if trade['amount'] > 0 else "🔴"
            t_str = time.strftime('%H:%M', time.localtime(trade['time']/1000))
            report += f"{s_icon} {trade['symbol']}: ${trade['amount']:.2f} ({t_str})\n"
            
    bot.reply_to(message, report, parse_mode='Markdown')

@bot.message_handler(commands=['balance', 'wallet', 'saldo'])
def handle_balance(message):
    """Muestra el saldo y patrimonio actual de la billetera"""
    chat_id = str(message.chat.id)
    session = session_manager.get_session(chat_id)
    if not session: 
        bot.reply_to(message, "⛔ Sesión no encontrada.")
        return
        
    avail, total = session.get_balance_details()
    
    msg = (
        f"💳 **SALDO DE BILLETERA (USDT)**\n\n"
        f"💵 **Disponible:** `${avail:,.2f}`\n"
        f"💰 **Patrimonio Total:** `${total:,.2f}`\n"
        f"_(Incluye PnL No Realizado basado en posiciones abiertas)_"
    )
    bot.reply_to(message, msg, parse_mode='Markdown')

@bot.message_handler(commands=['price', 'precios'])
def handle_price_request(message):
    """Maneja el comando /price para mostrar el estado actual de todos los activos"""
    # Comando público, ¿accesible para cualquiera o restringido?
    # ¿Mantenerlo abierto o restringir a sesiones conocidas/admin?
    # Por ahora, abierto.
    
    bot.reply_to(message, "⏳ Obteniendo precios... por favor espere.")
    
    # Categorías
    groups = {
        "📉 CRYPTO": [],
        "💵 ACCIONES": [], 
        "🛢️ MATERIAS PRIMAS": []
    }
    
    # Nombres Amigables
    name_map = {
        'GC=F': 'Oro (Gold)',
        'CL=F': 'Petróleo (Oil)',
        'BTCUSDT': 'Bitcoin (BTC)',
        'ETHUSDT': 'Ethereum (ETH)',
        'XRPUSDT': 'Ripple (XRP)',
        'SOLUSDT': 'Solana (SOL)',
        'SUIUSDT': 'SUI (SUI)',
        'ZECUSDT': 'Zcash (ZEC)',
        'TSLA': 'Tesla (TSLA)',
        'NVDA': 'Nvidia (NVDA)',
        'MSFT': 'Microsoft (MSFT)'
    }

    # Iconos
    icon_map = {
        'BTCUSDT': '₿',
        'ETHUSDT': 'Ξ',
        'XRPUSDT': '✕',
        'SOLUSDT': '◎',
        'SUIUSDT': '💧',
        'ZECUSDT': '🛡️',
        'TSLA': '🚗',
        'NVDA': '🟢',
        'MSFT': '🪟',
        'GC=F': '🥇',
        'CL=F': '🛢️'
    }

    for asset in WATCHLIST:
        try:
            # Determinar Categoría
            category = "💵 ACCIONES"
            if 'USDT' in asset: category = "📉 CRYPTO"
            elif '=F' in asset: category = "🛢️ MATERIAS PRIMAS"
            
            # Obtener datos
            df = get_market_data(asset, timeframe='15m', limit=300)
            if df.empty: continue
                
            latest = df.iloc[-1]
            price = latest['close']
            
            # Analizar mercado con configuración actual
            _, metrics = analyze_market(df, enabled_strategies=STRATEGY_CONFIG)
            
            rsi = metrics.get('rsi', 0)
            stoch_k = metrics.get('stoch_k', 0)
            stoch_d = metrics.get('stoch_d', 0)
            vol_ratio = metrics.get('vol_ratio', 0)
            ema_200 = metrics.get('ema_200', 0)
            source = metrics.get('source', 'None')
            
            trend_icon = "📈" if price > ema_200 else "🐻"
            display_name = name_map.get(asset, asset)
            asset_icon = icon_map.get(asset, '💎')
            
            sig_icon = ""
            if source != 'None':
                sig_icon = "🔥 COMPRA"
            
            entry = (
                f"{asset_icon} **{display_name}** {sig_icon}\n"
                f"💰 ${price:,.2f} {trend_icon}\n"
                f"📉 RSI: {rsi:.1f} | 🌊 Vol: {vol_ratio}x\n"
                f"📊 Stoch: {stoch_k:.1f}/{stoch_d:.1f}\n"
            )
            groups[category].append(entry)
            
        except Exception as e:
            print(f"Error {asset}: {e}")

    # Construir Reporte Final
    report = "📋 **REPORTE ACTUAL DE PRECIOS**\n"
    # Mostrar Estado de Estrategia en Encabezado
    report += f"_(Activa: {'MR' if STRATEGY_CONFIG['mean_reversion'] else ''} {'TV' if STRATEGY_CONFIG['trend_velocity'] else ''})_\n\n"
    
    for cat_name, items in groups.items():
        if items:
            report += f"{cat_name}\n" + "―"*15 + "\n"
            report += "\n".join(items)
            report += "\n\n"
    
    # Evitar error de mensaje vacío
    if len(report) < 50: report = "❌ Sin datos disponibles."
    
    bot.send_message(message.chat.id, report, parse_mode='Markdown')

@bot.message_handler(commands=['debug'])
def handle_debug(message):
    """Ejecuta diagnósticos del sistema"""
    user_id = str(message.chat.id)
    if TELEGRAM_ADMIN_ID and user_id != TELEGRAM_ADMIN_ID:
        bot.reply_to(message, "⛔ Acceso Denegado.")
        return

    bot.reply_to(message, "🕵️ Ejecutando diagnósticos...")
    try:
        from utils.diagnostics import run_diagnostics
        report = run_diagnostics()
        if len(report) > 4000:
            for x in range(0, len(report), 4000):
                bot.send_message(message.chat.id, report[x:x+4000], parse_mode='Markdown')
        else:
            bot.send_message(message.chat.id, report, parse_mode='Markdown')
    except Exception as e:
        bot.reply_to(message, f"❌ diagnóstico fallido: {e}")

# --- COMANDOS DE CONFIGURACIÓN ---

@bot.message_handler(commands=['config'])
def handle_config(message):
    chat_id = str(message.chat.id)
    session = session_manager.get_session(chat_id)
    
    if not session:
        bot.reply_to(message, "❌ Sesión no encontrada. Usa `/set_keys` primero.")
        return

    cfg = session.get_configuration()
    
    msg = (
        "⚙️ **TU CONFIGURACIÓN**\n\n"
        f"🔑 **Acceso API:** {'✅ Listo' if cfg['has_keys'] else '❌ Faltante/Inválido'}\n"
        f"🕹️ **Apalancamiento:** {cfg['leverage']}x\n"
        f"💰 **Margen Máx:** {cfg['max_capital_pct']*100:.1f}% del saldo\n"
        f"🛡️ **Stop Loss:** {cfg['stop_loss_pct']*100:.1f}%\n"
        f"🌍 **Proxy:** {'Habilitado' if cfg['proxy_enabled'] else 'Deshabilitado'}\n\n"
        "Para cambiar:\n"
        "`/set_leverage 10`\n"
        "`/set_margin 0.1`\n"
        "`/set_sl 0.02`"
    )
    bot.reply_to(message, msg, parse_mode='Markdown')

@bot.message_handler(commands=['set_leverage'])
def handle_set_leverage(message):
    chat_id = str(message.chat.id)
    session = session_manager.get_session(chat_id)
    if not session: return

    try:
        args = message.text.split()
        if len(args) < 2:
            bot.reply_to(message, "⚠️ Uso: `/set_leverage 10` (Entero 1-125)")
            return
            
        val = int(args[1])
        if 1 <= val <= 125:
            new_val = session.update_config('leverage', val)
            session_manager.save_sessions()
            bot.reply_to(message, f"✅ Apalancamiento establecido en **{new_val}x**")
        else:
            bot.reply_to(message, "❌ Valor inválido. Debe ser 1-125.")
    except Exception as e:
        bot.reply_to(message, f"❌ Error: {e}")

@bot.message_handler(commands=['set_margin'])
def handle_set_margin(message):
    chat_id = str(message.chat.id)
    session = session_manager.get_session(chat_id)
    if not session: return

    try:
        args = message.text.split()
        if len(args) < 2:
            bot.reply_to(message, "⚠️ Uso: `/set_margin 0.1` (Decimal 0.01-1.0)")
            return
            
        val = float(args[1])
        if 0.01 <= val <= 1.0:
            new_val = session.update_config('max_capital_pct', val)
            session_manager.save_sessions()
            bot.reply_to(message, f"✅ Margen Máx establecido en **{new_val*100:.1f}%**")
        else:
            bot.reply_to(message, "❌ Valor inválido. Debe ser 0.01 - 1.0")
    except Exception as e:
        bot.reply_to(message, f"❌ Error: {e}")

@bot.message_handler(commands=['set_sl'])
def handle_set_sl(message):
    chat_id = str(message.chat.id)
    session = session_manager.get_session(chat_id)
    if not session: return

    try:
        args = message.text.split()
        if len(args) < 2:
            bot.reply_to(message, "⚠️ Uso: `/set_sl 0.02` (Decimal 0.005-0.5)")
            return
            
        val = float(args[1])
        if 0.001 <= val <= 0.5:
            new_val = session.update_config('stop_loss_pct', val)
            session_manager.save_sessions()
            bot.reply_to(message, f"✅ Stop Loss establecido en **{new_val*100:.2f}%**")
        else:
            bot.reply_to(message, "❌ Valor inválido. Debe ser 0.001 - 0.5")
    except Exception as e:
        bot.reply_to(message, f"❌ Error: {e}")

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    help_text = (
        "🤖 **AYUDA DE ANTIGRAVITY BOT v2.0**\n\n"
        "**🎮 Control de Estrategia**\n"
        "`/strategies` — Ver estado de estrategias activas.\n"
        "`/toggle <mr/tv>` — Activar/Desactivar Reversión a la Media / Velocidad de Tendencia.\n"
        "   • `mr`: Reversión a la Media (Compra en caídas)\n"
        "   • `tv`: Velocidad de Tendencia (Momento)\n\n"
        
        "**📊 Inteligencia de Mercado**\n"
        "`/price` — Reporte Detallado Multi-Activo (Cripto/Acciones/Materias Primas).\n"
        "`/pnl` — PnL Diario e Historial de Operaciones.\n"
        "`/balance` — Patrimonio en Billetera y Margen Disponible.\n\n"
        
        "**⚙️ Riesgo y Configuración**\n"
        "`/config` — Ver parámetros actuales.\n"
        "`/set_leverage <1-125>` — Establecer Apalancamiento.\n"
        "`/set_margin <0.01-1.0>` — Margen Máx por operación (%).\n"
        "`/set_sl <0.005-0.5>` — Stop Loss (%).\n"
        "`/set_keys` — Registrar API de Binance.\n\n"
        
        "**⚡ Acciones Manuales**\n"
        "`/long <SIMBOLO>` — Forzar una posición Long.\n"
        "`/sell <SIMBOLO>` — Forzar cierre de posición.\n"
        "`/debug` — Diagnósticos del Sistema."
    )
    bot.reply_to(message, help_text, parse_mode='Markdown')

# --- PUNTO DE ENTRADA ---

def start_bot():
    global session_manager
    # 1. Inicializar Gestor de Sesiones
    session_manager = SessionManager()
    
    # 2. Iniciar Polling de Telegram
    if bot:
        print("📡 Iniciando Polling de Telegram...")
        t = threading.Thread(target=bot.infinity_polling, kwargs={'interval': 1, 'timeout': 20}) 
        t.daemon = True 
        t.start()
    
    # 3. Ejecutar Bucle de Trading
    print("🚀 Bucle de Trading Iniciado (intervalo de 60s)...")
    cycle_count = 0
    
    # Rastreo de Enfriamiento de Alertas
    # Formato: {'BTCUSDT': timestamp_de_ultima_alerta}
    last_alert_times = {}
    COOLDOWN_SECONDS = 900 # 15 Minutos (1 vela)
    
    while True:
        cycle_count += 1
        
        # Latido
        if cycle_count % 60 == 0:
            print(f"🟢 Ciclo {cycle_count}: Bot en línea.")
        
        for asset in WATCHLIST:
            try:
                # 1. Obtener Datos
                df = get_market_data(asset, timeframe='15m', limit=300)
                if df.empty: continue

                # 2. Analizar (con Configuración Global de Estrategia)
                buy_signal, metrics = analyze_market(df, enabled_strategies=STRATEGY_CONFIG)
                
                # 3. Lógica de Alerta y Trading
                if buy_signal:
                    now = time.time()
                    last_time = last_alert_times.get(asset, 0)
                    
                    # Verificación de Enfriamiento
                    if (now - last_time) < COOLDOWN_SECONDS:
                        # La señal existe pero la ignoramos (prevención de spam)
                        continue
                        
                    # Nueva Alerta Válida
                    last_alert_times[asset] = now
                    
                    price = metrics['close']
                    source = metrics.get('source', 'Desconocido')
                    
                    msg = (
                        f"🚀 **SEÑAL DE COMPRA: {asset}**\n"
                        f"estrategia: `{source}`\n"
                        f"precio: `${price:,.2f}`\n"
                        f"rsi: {metrics.get('rsi',0):.1f} | adx: {metrics.get('adx',0):.1f}"
                    )
                    send_alert(msg)
                    print(f"✅ ALERTA ENVIADA: {asset} ({source})")
                    
                    # Ejecutar Operación (Iterar todas las sesiones)
                    # Por seguridad, restringimos el trading automático o solo alertamos por ahora.
                    if session_manager:
                        for session in session_manager.get_all_sessions():
                            # Lógica de auto-trading iría aquí
                            # success, res = session.execute_long_position(asset)
                            pass

            except Exception as e:
                print(f"❌ Error en bucle ({asset}): {e}")
                
        time.sleep(60)

if __name__ == "__main__":
    start_bot()
