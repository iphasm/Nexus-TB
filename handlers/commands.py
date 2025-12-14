"""
Antigravity Bot - Command Handlers
Basic commands: /start, /help, /status, /wallet, /price, /pnl
EXACT REPLICA of main.py interface
"""

import asyncio
from aiogram import Router, F
from aiogram.filters import Command, CommandStart
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
import os
import requests

router = Router(name="commands")

# --- ASSET CONFIGURATION (Centralized) ---
from config import ASSET_GROUPS, GROUP_CONFIG, TICKER_MAP, get_display_name


def get_fear_and_greed_index() -> str:
    """Fetch Fear and Greed Index from alternative.me"""
    try:
        url = "https://api.alternative.me/fng/"
        resp = requests.get(url, timeout=5)
        data = resp.json()
        if 'data' in data and len(data['data']) > 0:
            item = data['data'][0]
            val = int(item['value'])
            classification = item['value_classification']
            
            icon = "😐"
            if val >= 75: icon = "🤑"
            elif val >= 55: icon = "😏"
            elif val <= 25: icon = "😱"
            elif val <= 45: icon = "😨"
            
            return f"{icon} *{classification}* ({val}/100)"
    except Exception as e:
        print(f"F&G Error: {e}")
    
    return "N/A"


@router.message(CommandStart())
async def cmd_start(message: Message, **kwargs):
    """Bienvenida Profesional con Efecto de Carga - EXACT REPLICA"""
    # 1. Mensaje de carga inicial
    msg_load = await message.answer("🔄 _Despertando funciones cognitivas..._", parse_mode="Markdown")
    
    # Simular micro-check
    await asyncio.sleep(0.5)
    
    # 2. Verificar estado
    bot = message.bot
    me = await bot.get_me()
    status_icon = "🟢" if me else "🔴"
    status_text = "SISTEMA ONLINE" if me else "ERROR DE CONEXIÓN"
    
    chat_id = str(message.chat.id)
    session_manager = kwargs.get('session_manager')
    session = session_manager.get_session(chat_id) if session_manager else None
    
    # 3. Datos de Sesión
    mode = "WATCHER"
    auth = "🔒 Sin Credenciales"
    
    if session:
        cfg = session.get_configuration()
        mode = cfg.get('mode', 'WATCHER')
        
        # Build Auth String
        auth_list = []
        if session.client:
            auth_list.append("Binance")
        if session.alpaca_client:
            auth_list.append("🦙 Alpaca")
            
        if auth_list:
            auth = "🔑 " + " + ".join(auth_list)
    
    # Get Personality
    p_key = session.config.get('personality', 'NEXUS') if session else 'NEXUS'

    # 4. Mensaje Final (Styled like original)
    welcome = (
        f"{status_icon} *{status_text}*\n\n"
        "🤖 *ANTIGRAVITY BOT v3.5 (Async)*\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        f"🎮 Modo: `{mode}`\n"
        f"{auth}\n\n"
        "_Usa los botones o escribe /help_"
    )
    
    # Interactive Menu (Buttons) - EXACT REPLICA
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        # Row 1: Status | Wallet
        [
            InlineKeyboardButton(text="📊 Estado", callback_data="CMD|status"),
            InlineKeyboardButton(text="💰 Cartera", callback_data="CMD|wallet")
        ],
        # Row 2: Watcher | Copilot
        [
            InlineKeyboardButton(text="🔎 Watcher", callback_data="CMD|watcher"),
            InlineKeyboardButton(text="🦾 Copilot", callback_data="CMD|copilot")
        ],
        # Row 3: Pilot (Big)
        [
            InlineKeyboardButton(text="🤖 Pilot Mode", callback_data="CMD|pilot")
        ],
        # Row 4: AI Commands
        [
            InlineKeyboardButton(text="📰 News", callback_data="CMD|news"),
            InlineKeyboardButton(text="🧠 Sentiment", callback_data="CMD|sentiment"),
            InlineKeyboardButton(text="🎯 Sniper", callback_data="CMD|sniper")
        ],
        # Row 5: Presets
        [
            InlineKeyboardButton(text="⚔️ Ronin", callback_data="CMD|mode_RONIN"),
            InlineKeyboardButton(text="🛡️ Guardian", callback_data="CMD|mode_GUARDIAN"),
            InlineKeyboardButton(text="🌌 Quantum", callback_data="CMD|mode_QUANTUM")
        ],
        # Row 6: Config / Personality / Help
        [
            InlineKeyboardButton(text="🧠 Persona", callback_data="CMD|personality"),
            InlineKeyboardButton(text="⚙️ Config", callback_data="CMD|config"),
            InlineKeyboardButton(text="❓ Ayuda", callback_data="CMD|help")
        ]
    ])
    
    await msg_load.edit_text(welcome, parse_mode="Markdown", reply_markup=keyboard)


@router.message(Command("help"))
async def cmd_help(message: Message):
    """Command reference - EXACT REPLICA"""
    help_text = (
        "🤖 *ANTIGRAVITY BOT v3.5*\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        
        "📊 *INFO & MERCADO*\n"
        "• /start - Menú principal\n"
        "• /price - Precios y señales\n"
        "• /status - Estado del sistema\n"
        "• /wallet - Ver cartera\n"
        "• /analyze `<SYM>` - Análisis IA\n\n"
        
        "💹 *TRADING MANUAL*\n"
        "• /long `<SYM>` - Abrir LONG\n"
        "• /short `<SYM>` - Abrir SHORT\n"
        "• /buy `<SYM>` - Compra SPOT\n"
        "• /sell `<SYM>` - Cerrar/Flip\n"
        "• /close `<SYM>` - Cerrar posición\n"
        "• /closeall - Cerrar TODO\n\n"
        
        "🎮 *MODOS OPERATIVOS*\n"
        "• /pilot - Automático\n"
        "• /copilot - Asistido\n"
        "• /watcher - Solo alertas\n"
        "• /mode `<PRESET>` - Ronin/Guardian/Quantum\n\n"
        
        "⚙️ *CONFIGURACIÓN*\n"
        "• /config - Panel de ajustes\n"
        "• /strategies - Motores activos\n"
        "• /set\\_leverage - Apalancamiento\n"
        "• /set\\_margin - Margen máximo\n"
        "• /set\\_keys - API Keys Binance\n"
        "• /set\\_alpaca - API Keys Alpaca\n"
        "• /delete\\_keys - Borrar sesión\n"
        "• /togglegroup - Filtrar grupos\n"
        "• /assets - Config activos\n"
        "• /personality - Cambiar voz\n\n"
        
        "🧠 *AI & SENTIMIENTO*\n"
        "• /news - Boletín IA\n"
        "• /sentiment - Radar global\n"
        "• /sniper - Oportunidades\n"
        "• /fomc - Análisis FED\n\n"
        
        "🛡️ *SEGURIDAD*\n"
        "• /risk - Gestión de riesgo\n"
        "• /resetpilot - Reset breaker\n"
        "• /debug - Diagnóstico\n\n"
        
        "📖 *DOCS*\n"
        "• /about - Sobre el bot\n"
        "• /strategy - Lógica de trading"
    )
    
    try:
        await message.answer(help_text, parse_mode="Markdown")
    except:
        # Fallback sin markdown
        await message.answer(help_text.replace('*', '').replace('`', '').replace('\\_', '_'))


@router.message(Command("status"))
async def cmd_status(message: Message, **kwargs):
    """Muestra estado del sistema (Diseño: Clean Glass) - EXACT REPLICA"""
    session_manager = kwargs.get('session_manager')
    session = None
    
    if session_manager:
        session = session_manager.get_session(str(message.chat.id))
    
    mode = "WATCHER"
    has_keys = False
    
    if session:
        cfg = session.get_configuration()
        mode = cfg.get('mode', 'WATCHER')
        has_keys = cfg.get('has_keys', False)
    
    # Fear & Greed
    fg_text = get_fear_and_greed_index()
    
    # Mode display
    mode_map = {
        'WATCHER': 'WATCHER (Observador)',
        'COPILOT': 'COPILOT (Asistido)',
        'PILOT': 'PILOT (Automático)'
    }
    mode_display = mode_map.get(mode, mode)
    
    # Build asset list
    active_radars = ""
    for group, enabled in GROUP_CONFIG.items():
        icon = "🟢" if enabled else "⚪"
        name_map = {
            'CRYPTO': 'Criptomonedas',
            'STOCKS': 'Acciones',
            'COMMODITY': 'Materias Primas'
        }
        name = name_map.get(group, group)
        count = len(ASSET_GROUPS.get(group, [])) if enabled else 0
        count_str = f"({count})" if enabled else ""
        active_radars += f"{icon} {name} {count_str}\n"
    
    status = (
        "🤖 **Estado de Antigravity**\n\n"
        
        "**Modo de Operación**\n"
        f"🕹️ `{mode_display}`\n\n"
        
        "**Entorno de Mercado**\n"
        f"🌡️ Sentimiento: {fg_text}\n"
        f"💻 Conexión: **{'Estable' if has_keys else 'Desconectado'}**\n\n"
        
        "**Escáneres Activos**\n"
        f"{active_radars}\n"
        "_Sistema ejecutándose correctamente._"
    )
    
    await message.answer(status, parse_mode="Markdown")


@router.message(Command("wallet"))
async def cmd_wallet(message: Message, **kwargs):
    """Muestra detalles completos de la cartera - EXACT REPLICA"""
    session_manager = kwargs.get('session_manager')
    if not session_manager:
        await message.answer("⚠️ Error interno.")
        return
    
    session = session_manager.get_session(str(message.chat.id))
    if not session:
        await message.answer("⚠️ Sin sesión activa. Usa /set\\_keys.")
        return
    
    loading = await message.answer("⏳ Consultando Blockchain y Binance...")
    
    try:
        details = await session.get_wallet_details()
        if not details or 'error' in details:
            await loading.edit_text(f"❌ Error: {details.get('error', 'Unknown')}")
            return
        
        # Unpack
        spot_bal = details.get('spot_usdt', 0.0)
        earn_bal = details.get('earn_usdt', 0.0)
        spot_total = spot_bal + earn_bal
        
        fut_bal = details.get('futures_balance', 0.0)
        fut_pnl = details.get('futures_pnl', 0.0)
        fut_total = details.get('total', fut_bal)
        alpaca_native = details.get('alpaca_equity', 0.0)
        
        net_worth = spot_total + fut_total + alpaca_native
        
        pnl_icon = "🟢" if fut_pnl >= 0 else "🔴"
        
        msg = (
            "💼 *CARTERA ANTIGRAVITY*\n"
            "〰️〰️〰️〰️〰️〰️\n"
            f"🏦 *SPOT (USDT):* `${spot_bal:,.2f}`\n"
            f"🐷 *EARN (Ahorros):* `${earn_bal:,.2f}`\n"
            "〰️〰️〰️〰️〰️〰️\n"
            f"🚀 *FUTUROS Balance:* `${fut_bal:,.2f}`\n"
            f"📊 *FUTUROS PnL:* {pnl_icon} `${fut_pnl:,.2f}`\n"
            f"💰 *FUTUROS Total:* `${fut_total:,.2f}`\n"
            "〰️〰️〰️〰️〰️〰️\n"
            f"🦙 *ALPACA (Stocks):* `${alpaca_native:,.2f}`\n"
            "〰️〰️〰️〰️〰️〰️\n"
            f"🏆 *NET WORTH TOTAL:* `${net_worth:,.2f}`"
        )
        
        await loading.edit_text(msg, parse_mode="Markdown")
        
    except Exception as e:
        await loading.edit_text(f"❌ Error: {e}")


@router.message(Command("watcher"))
async def cmd_watcher(message: Message, **kwargs):
    """Switch to Watcher mode"""
    session_manager = kwargs.get('session_manager')
    if not session_manager:
        await message.answer("⚠️ Error interno.")
        return
        
    session = session_manager.get_session(str(message.chat.id))
    if not session:
        await message.answer("⚠️ Sin sesión activa. Usa /set\\_keys primero.")
        return
    
    session.set_mode('WATCHER')
    await session_manager.save_sessions()
    
    await message.answer(
        "👁️ *Modo WATCHER Activado*\n\n"
        "Solo recibirás alertas de señales.\n"
        "No se ejecutarán operaciones automáticas.",
        parse_mode="Markdown"
    )


@router.message(Command("copilot"))
async def cmd_copilot(message: Message, **kwargs):
    """Switch to Copilot mode"""
    session_manager = kwargs.get('session_manager')
    if not session_manager:
        await message.answer("⚠️ Error interno.")
        return
        
    session = session_manager.get_session(str(message.chat.id))
    if not session:
        await message.answer("⚠️ Sin sesión activa. Usa /set\\_keys primero.")
        return
    
    session.set_mode('COPILOT')
    await session_manager.save_sessions()
    
    await message.answer(
        "🦾 *Modo COPILOT Activado*\n\n"
        "Recibirás propuestas de trading con botones.\n"
        "Tú decides si ejecutar o rechazar cada operación.",
        parse_mode="Markdown"
    )


@router.message(Command("pilot"))
async def cmd_pilot(message: Message, **kwargs):
    """Switch to Pilot mode"""
    session_manager = kwargs.get('session_manager')
    if not session_manager:
        await message.answer("⚠️ Error interno.")
        return
        
    session = session_manager.get_session(str(message.chat.id))
    if not session:
        await message.answer("⚠️ Sin sesión activa. Usa /set\\_keys primero.")
        return
    
    session.set_mode('PILOT')
    await session_manager.save_sessions()
    
    await message.answer(
        "🤖 *Modo PILOT Activado*\n\n"
        "El bot ejecutará operaciones automáticamente.\n"
        "⚠️ _Asegúrate de tener configurado tu riesgo correctamente._",
        parse_mode="Markdown"
    )


@router.message(Command("pnl"))
async def cmd_pnl(message: Message, **kwargs):
    """Show PnL history"""
    session_manager = kwargs.get('session_manager')
    if not session_manager:
        await message.answer("⚠️ Error interno.")
        return
    
    session = session_manager.get_session(str(message.chat.id))
    if not session:
        await message.answer("⚠️ Sin sesión activa. Usa /set\\_keys.")
        return
    
    loading = await message.answer("⏳ Consultando historial de PnL...")
    
    try:
        # Get PnL from session
        if hasattr(session, 'get_pnl_history'):
            pnl_data = await session.get_pnl_history(days=7)
        else:
            pnl_data = []
        
        if not pnl_data:
            await loading.edit_text("📊 No hay historial de PnL disponible.")
            return
        
        # Format output
        msg = "📊 *HISTORIAL DE PnL (7 días)*\n━━━━━━━━━━━━━━━━━━\n\n"
        total = 0.0
        
        for entry in pnl_data[-10:]:  # Last 10 entries
            symbol = entry.get('symbol', 'N/A')
            pnl = float(entry.get('realizedPnl', 0))
            total += pnl
            icon = "🟢" if pnl >= 0 else "🔴"
            msg += f"{icon} {symbol}: `${pnl:,.2f}`\n"
        
        total_icon = "🟢" if total >= 0 else "🔴"
        msg += f"\n━━━━━━━━━━━━━━━━━━\n{total_icon} *TOTAL:* `${total:,.2f}`"
        
        await loading.edit_text(msg, parse_mode="Markdown")
        
    except Exception as e:
        await loading.edit_text(f"❌ Error: {e}")


@router.message(Command("debug"))
async def cmd_debug(message: Message, **kwargs):
    """System diagnostics - Full Network Report"""
    # Import locally to avoid circular deps if any
    from utils.diagnostics import run_diagnostics
    
    msg = await message.answer("⏳ Ejecutando diagnóstico de red y sistema...")
    
    try:
        # Run blocking diagnostics in thread pool
        loop = asyncio.get_running_loop()
        report = await loop.run_in_executor(None, run_diagnostics)
        
        # Split report if too long (Telegram limit 4096)
        if len(report) > 4000:
            for i in range(0, len(report), 4000):
                await message.answer(report[i:i+4000], parse_mode="Markdown")
        else:
            await msg.edit_text(report, parse_mode="Markdown")
            
    except Exception as e:
        await msg.edit_text(f"❌ Error en diagnóstico: {e}")


# ============================================
# --- RESTORED COMMANDS FROM SYNC VERSION ---
# ============================================

@router.message(Command("mode"))
async def cmd_mode(message: Message, **kwargs):
    """Risk presets: /mode RONIN|GUARDIAN|QUANTUM"""
    session_manager = kwargs.get('session_manager')
    if not session_manager:
        await message.answer("⚠️ Session manager not available.")
        return
    
    chat_id = str(message.chat.id)
    session = session_manager.get_session(chat_id)
    
    if not session:
        await message.answer("⚠️ Sin sesión activa. Usa /set_keys.")
        return
    
    args = message.text.upper().split()
    if len(args) < 2:
        await message.answer("⚠️ Uso: `/mode <RONIN | GUARDIAN | QUANTUM>`", parse_mode='Markdown')
        return
    
    profile = args[1]
    
    if profile == 'RONIN':
        # Aggressive
        session.update_config('leverage', 20)
        session.update_config('stop_loss_pct', 0.015)
        session.update_config('atr_multiplier', 1.5)
        session.update_config('sentiment_threshold', -0.8)
        session_manager.save_sessions()
        await message.answer(
            "⚔️ **MODO RONIN ACTIVADO**\n"
            "- Apalancamiento: 20x\n"
            "- Stop Loss: Apretado (1.5 ATR)\n"
            "- Filtro IA: Laxo (-0.8)\n"
            "_Ojo: Alto Riesgo._",
            parse_mode='Markdown'
        )
    elif profile == 'GUARDIAN':
        # Conservative
        session.update_config('leverage', 3)
        session.update_config('stop_loss_pct', 0.03)
        session.update_config('atr_multiplier', 3.0)
        session.update_config('sentiment_threshold', -0.3)
        session_manager.save_sessions()
        await message.answer(
            "🛡️ **MODO GUARDIAN ACTIVADO**\n"
            "- Apalancamiento: 3x\n"
            "- Stop Loss: Amplio (3.0 ATR)\n"
            "- Filtro IA: Estricto (-0.3)\n"
            "_Prioridad: Protección de Capital._",
            parse_mode='Markdown'
        )
    elif profile == 'QUANTUM':
        # Balanced
        session.update_config('leverage', 5)
        session.update_config('stop_loss_pct', 0.02)
        session.update_config('atr_multiplier', 2.0)
        session.update_config('sentiment_threshold', -0.6)
        session_manager.save_sessions()
        await message.answer(
            "🌌 **MODO QUANTUM ACTIVADO**\n"
            "- Apalancamiento: 5x\n"
            "- Stop Loss: Estándar (2.0 ATR)\n"
            "- Filtro IA: Balanceado (-0.6)\n"
            "_Equilibrio Matemático._",
            parse_mode='Markdown'
        )
    else:
        await message.answer("⚠️ Perfil desconocido. Usa: RONIN, GUARDIAN, QUANTUM.")


@router.message(Command("resetpilot"))
async def cmd_resetpilot(message: Message, **kwargs):
    """Reset circuit breaker"""
    session_manager = kwargs.get('session_manager')
    if not session_manager:
        await message.answer("⚠️ Session manager not available.")
        return
    
    chat_id = str(message.chat.id)
    session = session_manager.get_session(chat_id)
    
    if not session:
        await message.answer("⚠️ Sin sesión activa.")
        return
    
    session.reset_circuit_breaker()
    await message.answer(
        "🔄 **Circuit Breaker Reseteado**\n"
        "El contador de pérdidas consecutivas se ha reiniciado.\n"
        "Ahora puedes volver a activar modo PILOT con `/pilot`.",
        parse_mode='Markdown'
    )


@router.message(Command("sniper"))
async def cmd_sniper(message: Message, **kwargs):
    """Scan for instant trading opportunities"""
    from utils.ai_analyst import QuantumAnalyst
    from data.fetcher import get_market_data
    from strategies.strategy_engine import StrategyEngine
    
    session_manager = kwargs.get('session_manager')
    if not session_manager:
        await message.answer("⚠️ Session manager not available.")
        return
    
    chat_id = str(message.chat.id)
    session = session_manager.get_session(chat_id)
    
    msg = await message.answer("🎯 **SNIPER MODE ACTIVADO**\n👁️ Escaneando 5 activos principales...")
    
    targets = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'BNBUSDT', 'DOGEUSDT']
    best_candidate = None
    best_score = -999
    
    try:
        analyst = QuantumAnalyst()
        
        for asset in targets:
            # 1. Tech Analysis
            df = get_market_data(asset, timeframe='15m', limit=100)
            if df.empty:
                continue
            
            engine = StrategyEngine(df)
            res = engine.analyze()
            
            # Score Technicals
            tech_score = 0
            sig = res.get('signal_futures', 'NEUTRAL')
            if sig == 'BUY':
                tech_score = 1
            elif sig == 'SHORT':
                tech_score = -1
            else:
                continue
            
            # 2. AI Confirmation
            if analyst.client:
                sentiment = analyst.check_market_sentiment(asset)
                sent_score = sentiment.get('score', 0)
                
                # Congruence Check
                total_score = 0
                if sig == 'BUY' and sent_score > 0.2:
                    total_score = 1 + sent_score
                elif sig == 'SHORT' and sent_score < -0.2:
                    total_score = 1 + abs(sent_score)
                
                if total_score > best_score:
                    best_score = total_score
                    best_candidate = {
                        'asset': asset,
                        'signal': sig,
                        'price': res.get('metrics', {}).get('close', 0),
                        'reason_tech': res.get('reason_futures', 'N/A'),
                        'reason_ai': sentiment.get('reason', 'N/A'),
                        'vol_risk': sentiment.get('volatility_risk', 'LOW')
                    }
        
        if best_candidate and best_score > 0:
            c = best_candidate
            icon = "🚀" if c['signal'] == 'BUY' else "🩸"
            
            result = (
                f"🎯 **BLANCO ENCONTRADO: {c['asset']}**\n"
                f"{icon} Señal: **{c['signal']}** @ ${c['price']:,.2f}\n\n"
                f"📊 **Técnico:** {c['reason_tech']}\n"
                f"🧠 **AI:** {c['reason_ai']}\n"
                f"⚠️ Riesgo: {c['vol_risk']}\n\n"
                f"👇 Ejecutar con: `/{c['signal'].lower()} {c['asset']}`"
            )
            await msg.edit_text(result, parse_mode='Markdown')
        else:
            await msg.edit_text("🤷‍♂️ **Sin blancos claros.**\nEl mercado está mixto. Recomiendo esperar.")
    
    except Exception as e:
        await msg.edit_text(f"❌ Error Sniper: {e}")


@router.message(Command("news"))
async def cmd_news(message: Message, **kwargs):
    """AI market briefing"""
    from utils.ai_analyst import QuantumAnalyst
    
    msg = await message.answer("🗞️ *Leyendo las noticias...* (Consultando via AI)", parse_mode='Markdown')
    
    try:
        analyst = QuantumAnalyst()
        if not analyst.client:
            await msg.edit_text("⚠️ IA no disponible. Configura OPENAI_API_KEY.")
            return
        
        report = analyst.generate_market_briefing()
        await msg.edit_text(f"📰 **BOLETÍN DE MERCADO**\n\n{report}", parse_mode='Markdown')
    except Exception as e:
        await msg.edit_text(f"❌ Error: {e}")


@router.message(Command("sentiment"))
async def cmd_sentiment(message: Message, **kwargs):
    """Global sentiment analysis"""
    from utils.ai_analyst import QuantumAnalyst
    
    msg = await message.answer("🧠 *Escaneando Redes y Noticias...*", parse_mode='Markdown')
    
    try:
        analyst = QuantumAnalyst()
        if not analyst.client:
            await msg.edit_text("⚠️ IA no disponible. Configura OPENAI_API_KEY.")
            return
        
        res_btc = analyst.check_market_sentiment('BTCUSDT')
        res_macro = analyst.check_market_sentiment('^GSPC')  # S&P 500
        
        score_btc = res_btc.get('score', 0)
        score_macro = res_macro.get('score', 0)
        
        def interpret(s):
            if s > 0.3: return "🟢 BULLISH"
            if s < -0.3: return "🔴 BEARISH"
            return "⚪ NEUTRAL"
        
        result = (
            "🧠 **SENTIMIENTO GLOBAL DEL MERCADO**\n"
            "-----------------------------------\n"
            f"💎 **Cripto (BTC):** {score_btc:.2f} | {interpret(score_btc)}\n"
            f"_{res_btc.get('reason', 'N/A')}_\n\n"
            f"🌍 **Macro (S&P500):** {score_macro:.2f} | {interpret(score_macro)}\n"
            f"_{res_macro.get('reason', 'N/A')}_\n\n"
            f"⚠️ **Riesgo Volatilidad:** `{res_macro.get('volatility_risk', 'LOW')}`"
        )
        await msg.edit_text(result, parse_mode='Markdown')
    
    except Exception as e:
        await msg.edit_text(f"❌ Error: {e}")


@router.message(Command("fomc"))
async def cmd_fomc(message: Message, **kwargs):
    """Federal Reserve (FED) analysis"""
    from utils.ai_analyst import QuantumAnalyst
    
    session_manager = kwargs.get('session_manager')
    chat_id = str(message.chat.id)
    session = session_manager.get_session(chat_id) if session_manager else None
    
    p_key = session.config.get('personality', 'Standard') if session else 'Standard'
    
    msg = await message.answer("🏦 *Analizando situación de la FED...* (Tasas, Bonos, Powell)", parse_mode='Markdown')
    
    try:
        analyst = QuantumAnalyst()
        if not analyst.client:
            await msg.edit_text("⚠️ IA no disponible. Configura OPENAI_API_KEY.")
            return
        
        report = analyst.analyze_fomc(personality=p_key)
        await msg.edit_text(f"🏦 **ANÁLISIS FOMC (FED)**\n\n{report}", parse_mode='Markdown')
    except Exception as e:
        await msg.edit_text(f"❌ Error: {e}")


@router.message(Command("analyze"))
async def cmd_analyze(message: Message, **kwargs):
    """Per-asset AI analysis: /analyze BTC"""
    from utils.ai_analyst import QuantumAnalyst
    from data.fetcher import get_market_data
    
    args = message.text.split()
    if len(args) < 2:
        await message.answer("⚠️ Uso: `/analyze <SYMBOL>`\nEjemplo: `/analyze BTC`", parse_mode='Markdown')
        return
    
    symbol = args[1].upper()
    if 'USDT' not in symbol:
        symbol = f"{symbol}USDT"
    
    msg = await message.answer(f"🔍 Analizando {symbol}...")
    
    try:
        # Get data
        df = get_market_data(symbol, timeframe='1h', limit=50)
        if df.empty:
            await msg.edit_text(f"❌ No data for {symbol}")
            return
        
        current_price = float(df['close'].iloc[-1])
        rsi = float(df['RSI'].iloc[-1]) if 'RSI' in df.columns else 50
        
        analyst = QuantumAnalyst()
        if not analyst.client:
            await msg.edit_text("⚠️ IA no disponible.")
            return
        
        indicators = {
            'price': current_price,
            'rsi': rsi,
            'gap': 0
        }
        analysis = analyst.analyze_signal(symbol, '1h', indicators)
        
        await msg.edit_text(
            f"🔬 **ANÁLISIS: {symbol}**\n\n"
            f"💵 Precio: ${current_price:,.2f}\n"
            f"📊 RSI: {rsi:.1f}\n\n"
            f"🧠 **IA:**\n{analysis}",
            parse_mode='Markdown'
        )
    except Exception as e:
        await msg.edit_text(f"❌ Error: {e}")


# =================================================================
# /cooldown - Configure Signal Alert Cooldown
# =================================================================
@router.message(Command("cooldown"))
async def cmd_cooldown(message: Message, **kwargs):
    """Configure or view signal alert cooldown."""
    import bot_async
    
    args = message.text.split()
    
    if len(args) < 2:
        # Show current value
        current = bot_async.SIGNAL_COOLDOWN_SECONDS // 60
        await message.reply(
            f"⏱️ **COOLDOWN ACTUAL**\n\n"
            f"Intervalo anti-spam: `{current}` minutos\n\n"
            f"Uso: `/cooldown <minutos>`\n"
            f"Ejemplo: `/cooldown 10`",
            parse_mode="Markdown"
        )
        return
    
    try:
        minutes = int(args[1])
        if minutes < 1 or minutes > 60:
            await message.reply("❌ El valor debe estar entre 1 y 60 minutos.")
            return
        
        # Update global
        bot_async.SIGNAL_COOLDOWN_SECONDS = minutes * 60
        
        # Clear existing cooldowns
        bot_async._signal_cooldowns.clear()
        
        await message.reply(
            f"✅ **COOLDOWN ACTUALIZADO**\n\n"
            f"Nuevo intervalo: `{minutes}` minutos\n\n"
            f"Las alertas de señales ahora esperarán al menos "
            f"{minutes} minutos antes de repetir el mismo activo.",
            parse_mode="Markdown"
        )
    except ValueError:
        await message.reply("❌ Valor inválido. Usa: `/cooldown 10`", parse_mode="Markdown")


# =================================================================
# MANUAL TRADING COMMANDS
# =================================================================

@router.message(Command("long", "buy"))
async def cmd_long(message: Message, **kwargs):
    """Manually trigger a LONG position with Dynamic ATR."""
    session_manager = kwargs.get('session_manager')
    if not session_manager: return
    
    session = session_manager.get_session(str(message.chat.id))
    if not session:
        await message.reply("⚠️ Sin sesión activa.")
        return

    args = message.text.split()
    if len(args) < 2:
        await message.reply("⚠️ Uso: `/long <SYMBOL>` (ej: `/long BTC`)", parse_mode="Markdown")
        return
    
    # Smart Symbol Resolution
    from config import resolve_symbol
    raw_symbol = args[1]
    symbol = resolve_symbol(raw_symbol)
    
    # Calculate ATR
    msg_wait = await message.reply(f"⏳ Analizando volatilidad (ATR) para `{symbol}`...", parse_mode="Markdown")
    
    try:
        from data.fetcher import get_market_data, calculate_atr
        
        # Determine asset type for proper fetching
        is_crypto = 'USDT' in symbol
        
        # Fetch 1h candles
        df = get_market_data(symbol, timeframe='1h', limit=50)
        atr_value = calculate_atr(df, period=14)
        
        atr_msg = f" (ATR: {atr_value:.4f})" if atr_value > 0 else " (ATR: N/A, usando default)"
        
        await msg_wait.edit_text(f"🚀 Iniciando **LONG** en `{symbol}`{atr_msg}...", parse_mode="Markdown")
        
        # Execute with ATR
        success, res_msg = await session.execute_long_position(symbol, atr=atr_value)
        await message.reply(res_msg, parse_mode="Markdown")
        
    except Exception as e:
        await msg_wait.edit_text(f"❌ Error iniciando operación: {e}")


@router.message(Command("short", "sell"))
async def cmd_short(message: Message, **kwargs):
    """Manually trigger a SHORT position with Dynamic ATR."""
    session_manager = kwargs.get('session_manager')
    if not session_manager: return
    
    session = session_manager.get_session(str(message.chat.id))
    if not session:
        await message.reply("⚠️ Sin sesión activa.")
        return

    args = message.text.split()
    if len(args) < 2:
        await message.reply("⚠️ Uso: `/short <SYMBOL>` (ej: `/short ETH`)", parse_mode="Markdown")
        return
    
    # Smart Symbol Resolution
    from config import resolve_symbol
    raw_symbol = args[1]
    symbol = resolve_symbol(raw_symbol)
    
    # Calculate ATR
    msg_wait = await message.reply(f"⏳ Analizando volatilidad (ATR) para `{symbol}`...", parse_mode="Markdown")
    
    try:
        from data.fetcher import get_market_data, calculate_atr
        
        # Fetch 1h candles
        df = get_market_data(symbol, timeframe='1h', limit=50)
        atr_value = calculate_atr(df, period=14)
        
        atr_msg = f" (ATR: {atr_value:.4f})" if atr_value > 0 else " (ATR: N/A, usando default)"
        
        await msg_wait.edit_text(f"🐻 Iniciando **SHORT** en `{symbol}`{atr_msg}...", parse_mode="Markdown")
        
        # Execute with ATR
        success, res_msg = await session.execute_short_position(symbol, atr=atr_value)
        await message.reply(res_msg, parse_mode="Markdown")
        
    except Exception as e:
        await msg_wait.edit_text(f"❌ Error iniciando operación: {e}")

