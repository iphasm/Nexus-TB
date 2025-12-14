"""
Antigravity Bot - Trading Handlers
Manual trading: /long, /short, /close, /closeall, /buy, /sell
"""

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

router = Router(name="trading")


def resolve_symbol(raw: str) -> str:
    """Normalize symbol input to exchange format"""
    symbol = raw.upper().strip()
    
    # Handle common aliases
    aliases = {
        'BTC': 'BTCUSDT', 'ETH': 'ETHUSDT', 'SOL': 'SOLUSDT',
        'BNB': 'BNBUSDT', 'XRP': 'XRPUSDT', 'ADA': 'ADAUSDT',
        'DOGE': 'DOGEUSDT', 'LTC': 'LTCUSDT', 'LINK': 'LINKUSDT',
        'AVAX': 'AVAXUSDT', 'DOT': 'DOTUSDT', 'MATIC': 'MATICUSDT'
    }
    
    if symbol in aliases:
        return aliases[symbol]
    
    # Add USDT if missing for crypto
    if not symbol.endswith('USDT') and len(symbol) <= 5:
        return f"{symbol}USDT"
    
    return symbol


@router.message(Command("long"))
async def cmd_long(message: Message, **kwargs):
    """Execute LONG position"""
    session_manager = kwargs.get('session_manager')
    if not session_manager:
        await message.answer("⚠️ Error interno: SessionManager no disponible.")
        return
    
    chat_id = str(message.chat.id)
    session = session_manager.get_session(chat_id)
    
    if not session:
        await message.answer("⚠️ No tienes sesión activa. Usa /set\\_keys.")
        return
    
    # Parse arguments
    args = message.text.split()
    if len(args) < 2:
        await message.answer("⚠️ Uso: `/long <SYMBOL>` (Ej: BTCUSDT o BTC)", parse_mode="Markdown")
        return
    
    symbol = resolve_symbol(args[1])
    
    # Send processing message
    processing = await message.answer(f"⏳ Analizando {symbol} (ATR) y Ejecutando LONG...")
    
    try:
        # Get ATR for dynamic SL/TP
        atr_val = None
        # TODO: Implement async process_asset
        
        # Execute trade
        success, msg = await session.execute_long_position(symbol, atr=atr_val)
        
        if success:
            await processing.edit_text(f"✅ *LONG EJECUTADO*\n{msg}", parse_mode="Markdown")
        else:
            await processing.edit_text(f"❌ Error: {msg}")
            
    except Exception as e:
        await processing.edit_text(f"❌ Error crítico: {e}")


@router.message(Command("short"))
async def cmd_short(message: Message, **kwargs):
    """Execute SHORT position"""
    session_manager = kwargs.get('session_manager')
    if not session_manager:
        await message.answer("⚠️ Error interno.")
        return
    
    chat_id = str(message.chat.id)
    session = session_manager.get_session(chat_id)
    
    if not session:
        await message.answer("⚠️ No tienes sesión activa. Usa /set\\_keys.")
        return
    
    args = message.text.split()
    if len(args) < 2:
        await message.answer("⚠️ Uso: `/short <SYMBOL>` (Ej: ETHUSDT)", parse_mode="Markdown")
        return
    
    symbol = resolve_symbol(args[1])
    processing = await message.answer(f"⏳ Analizando {symbol} (ATR) y Ejecutando SHORT...")
    
    try:
        atr_val = None
        success, msg = await session.execute_short_position(symbol, atr=atr_val)
        
        if success:
            await processing.edit_text(f"✅ *SHORT EJECUTADO*\n{msg}", parse_mode="Markdown")
        else:
            await processing.edit_text(f"❌ Error: {msg}")
            
    except Exception as e:
        await processing.edit_text(f"❌ Error crítico: {e}")


@router.message(Command("close"))
async def cmd_close(message: Message, **kwargs):
    """Close position for a symbol"""
    session_manager = kwargs.get('session_manager')
    if not session_manager:
        await message.answer("⚠️ Error interno.")
        return
    
    chat_id = str(message.chat.id)
    session = session_manager.get_session(chat_id)
    
    if not session:
        await message.answer("⚠️ No tienes sesión activa. Usa /set\\_keys.")
        return
    
    args = message.text.split()
    if len(args) < 2:
        await message.answer("⚠️ Uso: `/close <SYMBOL>`", parse_mode="Markdown")
        return
    
    symbol = resolve_symbol(args[1])
    processing = await message.answer(f"⏳ Cerrando posición en {symbol}...")
    
    try:
        success, msg = await session.execute_close_position(symbol)
        await processing.edit_text(msg)
    except Exception as e:
        await processing.edit_text(f"❌ Error: {e}")


@router.message(Command("closeall"))
async def cmd_closeall(message: Message, **kwargs):
    """Close ALL open positions"""
    session_manager = kwargs.get('session_manager')
    if not session_manager:
        await message.answer("⚠️ Error interno.")
        return
    
    chat_id = str(message.chat.id)
    session = session_manager.get_session(chat_id)
    
    if not session:
        await message.answer("⚠️ No tienes sesión activa. Usa /set\\_keys.")
        return
    
    processing = await message.answer("🚨 Ejecutando CLOSE ALL...")
    
    try:
        success, msg = await session.execute_close_all()
        await processing.edit_text(msg)
    except Exception as e:
        await processing.edit_text(f"❌ Error: {e}")


@router.message(Command("cleanup"))
async def cmd_cleanup(message: Message, **kwargs):
    """Cancel orphaned orders (orders without position)"""
    session_manager = kwargs.get('session_manager')
    if not session_manager:
        await message.answer("⚠️ Error interno.")
        return
    
    chat_id = str(message.chat.id)
    session = session_manager.get_session(chat_id)
    
    if not session:
        await message.answer("⚠️ No tienes sesión activa. Usa /set\\_keys.")
        return
    
    processing = await message.answer("⏳ Buscando órdenes huérfanas...")
    
    try:
        success, msg = await session.cleanup_orphaned_orders()
        await processing.edit_text(msg)
    except Exception as e:
        await processing.edit_text(f"❌ Error: {e}")


@router.message(Command("buy"))
async def cmd_buy_spot(message: Message, **kwargs):
    """Execute SPOT buy"""
    session_manager = kwargs.get('session_manager')
    if not session_manager:
        await message.answer("⚠️ Error interno.")
        return
    
    chat_id = str(message.chat.id)
    session = session_manager.get_session(chat_id)
    
    if not session:
        await message.answer("⚠️ No tienes sesión activa. Usa /set\\_keys.")
        return
    
    args = message.text.split()
    if len(args) < 2:
        await message.answer("⚠️ Uso: `/buy <SYMBOL>` (Ej: BTCUSDT)", parse_mode="Markdown")
        return
    
    symbol = resolve_symbol(args[1])
    processing = await message.answer(f"⏳ Ejecutando compra SPOT de {symbol}...")
    
    try:
        success, msg = await session.execute_spot_buy(symbol)
        
        if success:
            await processing.edit_text(f"✅ *COMPRA SPOT EJECUTADA*\n{msg}", parse_mode="Markdown")
        else:
            await processing.edit_text(f"❌ Error: {msg}")
            
    except Exception as e:
        await processing.edit_text(f"❌ Error crítico: {e}")
