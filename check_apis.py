#!/usr/bin/env python3
"""
Script temporal para verificar configuración de APIs
"""

import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

print("🔍 VERIFICACIÓN DE APIs CONFIGURADAS")
print("=" * 40)

apis_to_check = [
    'OPENAI_API_KEY',
    'XAI_API_KEY',
    'APCA_API_KEY_ID',
    'APCA_API_SECRET_KEY',
    'BINANCE_API_KEY',
    'BINANCE_SECRET',
    'BYBIT_API_KEY',
    'BYBIT_API_SECRET',
    'CMC_API_KEY',
    'TELEGRAM_TOKEN'
]

for api in apis_to_check:
    value = os.getenv(api)
    if value:
        # Mostrar solo primeros y últimos caracteres por seguridad
        masked = value[:10] + "..." + value[-10:] if len(value) > 20 else value
        print(f"✅ {api}: {masked}")
    else:
        print(f"❌ {api}: No configurada")

print("\n💡 Si faltan APIs, configura el archivo .env")



