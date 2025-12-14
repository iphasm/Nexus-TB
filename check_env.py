import os
from dotenv import load_dotenv

load_dotenv()

print("🔍 VERIFICACIÓN DE VARIABLES DE ENTORNO")
print("=======================================")

vars_to_check = [
    'TELEGRAM_TOKEN',
    'TELEGRAM_ADMIN_ID',
    'BINANCE_API_KEY',
    'BINANCE_SECRET',
    'PROXY_URL'
]

all_ok = True

for v in vars_to_check:
    val = os.getenv(v)
    if val:
        masked = val[:4] + "..." + val[-4:] if len(val) > 8 else "***"
        print(f"✅ {v}: {masked}")
    else:
        print(f"❌ {v}: NO ENCONTRADO")
        all_ok = False

if not all_ok:
    print("\n⚠️ FALTAN VARIABLES IMPORTANTE.")
    print("Asegúrate de tener un archivo .env con tus credenciales.")
    print("Puedes copiar .env.example a .env y editarlo.")
else:
    print("\n✅ Todas las variables críticas parecen estar presentes.")
