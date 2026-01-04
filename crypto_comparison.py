#!/usr/bin/env python3
"""
Tabla Comparativa de Criptomonedas
Análisis comparativo de BTC, ETH, XRP y SOL
"""

import os
import json
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Importar librerías necesarias
try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    YFINANCE_AVAILABLE = False
    print("⚠️ yfinance no disponible")

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
    print("⚠️ pandas no disponible")


class CryptoComparison:
    """Clase para comparación de criptomonedas."""

    def __init__(self):
        self.symbols = ['BTC-USD', 'ETH-USD', 'XRP-USD', 'SOL-USD']
        self.names = ['Bitcoin', 'Ethereum', 'XRP', 'Solana']
        self.symbol_short = ['BTC', 'ETH', 'XRP', 'SOL']

        if not YFINANCE_AVAILABLE:
            raise ImportError("yfinance es requerido para este análisis")

        print("🪙 Crypto Comparison Tool Inicializado")
        print(f"   Analizando: {', '.join(self.symbol_short)}")

    def get_crypto_data(self, symbol: str) -> Dict[str, Any]:
        """
        Obtener datos completos de una criptomoneda.

        Args:
            symbol: Símbolo de yfinance (ej: 'BTC-USD')

        Returns:
            Dict con todos los datos de mercado
        """
        try:
            # Obtener datos históricos para diferentes periodos
            ticker = yf.Ticker(symbol)

            # Precio actual
            current_price = ticker.history(period="1d", interval="1m").iloc[-1]['Close']

            # Datos de 1 hora
            hourly_data = ticker.history(period="1d", interval="1h")
            price_1h_ago = hourly_data.iloc[-2]['Close'] if len(hourly_data) > 1 else current_price
            change_1h = ((current_price - price_1h_ago) / price_1h_ago) * 100

            # Datos de 24 horas
            daily_data = ticker.history(period="2d", interval="1h")
            price_24h_ago = daily_data.iloc[0]['Close'] if len(daily_data) > 24 else current_price
            change_24h = ((current_price - price_24h_ago) / price_24h_ago) * 100

            # Datos de 7 días
            weekly_data = ticker.history(period="8d", interval="1d")
            if len(weekly_data) >= 7:
                price_7d_ago = weekly_data.iloc[-8]['Close'] if len(weekly_data) > 7 else weekly_data.iloc[0]['Close']
                change_7d = ((current_price - price_7d_ago) / price_7d_ago) * 100
            else:
                change_7d = 0

            # Volumen
            volume_24h = daily_data['Volume'].tail(24).sum() if len(daily_data) >= 24 else 0

            # Información adicional
            info = ticker.info

            return {
                "symbol": symbol,
                "name": info.get("name", symbol.replace("-USD", "")),
                "current_price": round(current_price, 2),
                "change_1h_pct": round(change_1h, 2),
                "change_24h_pct": round(change_24h, 2),
                "change_7d_pct": round(change_7d, 2),
                "volume_24h": int(volume_24h),
                "market_cap": info.get("marketCap", 0),
                "volume_24h_usd": round(volume_24h * current_price, 2) if volume_24h > 0 else 0,
                "timestamp": datetime.now().isoformat(),
                "success": True
            }

        except Exception as e:
            return {
                "symbol": symbol,
                "error": str(e),
                "success": False
            }

    def get_all_crypto_data(self) -> List[Dict[str, Any]]:
        """
        Obtener datos de todas las criptomonedas.

        Returns:
            Lista con datos de todas las criptos
        """
        all_data = []

        print("\n📊 Obteniendo datos de criptomonedas...")

        for i, symbol in enumerate(self.symbols):
            print(f"   🔍 {self.symbol_short[i]} ({symbol})...")
            data = self.get_crypto_data(symbol)

            if data["success"]:
                print(f"      ✅ ${data['current_price']:,.2f}")
            else:
                print(f"      ❌ Error: {data.get('error', 'Desconocido')}")

            all_data.append(data)
            time.sleep(1)  # Pequeña pausa para no sobrecargar la API

        return all_data

    def format_volume(self, volume: float) -> str:
        """Formatear volumen de forma legible."""
        if volume >= 1e12:
            return ".2f"
        elif volume >= 1e9:
            return ".2f"
        elif volume >= 1e6:
            return ".2f"
        elif volume >= 1e3:
            return ".2f"
        else:
            return ".2f"

    def format_price(self, price: float) -> str:
        """Formatear precio de forma legible."""
        if price >= 1000:
            return ",.0f"
        elif price >= 1:
            return ",.2f"
        else:
            return ".6f"

    def print_comparison_table(self, data: List[Dict[str, Any]]):
        """Imprimir tabla comparativa formateada."""

        print("\n" + "=" * 80)
        print("🪙 TABLA COMPARATIVA DE CRIPTOMONEDAS")
        print("=" * 80)

        # Mostrar datos de cada cripto
        for i, crypto in enumerate(data):
            if not crypto.get("success", False):
                symbol = self.symbol_short[i]
                print(f"\n❌ {symbol}: ERROR - Datos no disponibles")
                continue

            name = self.names[i]
            symbol = self.symbol_short[i]
            price = crypto["current_price"]
            change_1h = crypto["change_1h_pct"]
            change_24h = crypto["change_24h_pct"]
            change_7d = crypto["change_7d_pct"]
            volume = crypto["volume_24h_usd"]

            # Formatear precio y volumen
            price_str = self.format_price(price)
            volume_str = self.format_volume(volume)

            print(f"\n🪙 {name} ({symbol})")
            print(f"   💰 Precio: ${price_str}")
            print(f"   ⏰ 1h: {'+' if change_1h >= 0 else ''}{change_1h:.2f}%")
            print(f"   📅 24h: {'+' if change_24h >= 0 else ''}{change_24h:.2f}%")
            print(f"   📈 7d: {'+' if change_7d >= 0 else ''}{change_7d:.2f}%")
            print(f"   📊 Volumen 24h: ${volume_str}")

        print("\n" + "=" * 80)

        # Rankings
        self.print_rankings(data)

        # Resumen
        successful = sum(1 for c in data if c.get("success", False))
        print(f"\n✅ Datos obtenidos: {successful}/{len(data)} criptomonedas")
        print(f"📅 Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    def print_rankings(self, data: List[Dict[str, Any]]):
        """Mostrar rankings por diferentes métricas."""

        successful_data = [c for c in data if c.get("success", False)]

        if len(successful_data) < 2:
            return

        print("\n🏆 RANKINGS:")

        # Mejor rendimiento 24h
        best_24h = max(successful_data, key=lambda x: x["change_24h_pct"])
        symbol_24h = self.symbol_short[data.index(best_24h)]
        print(f"   🚀 Mejor rendimiento 24h: {symbol_24h} (+{best_24h['change_24h_pct']:.2f}%)")
        # Mejor rendimiento 7d
        best_7d = max(successful_data, key=lambda x: x["change_7d_pct"])
        symbol_7d = self.symbol_short[data.index(best_7d)]
        print(f"   📈 Mejor rendimiento 7d: {symbol_7d} (+{best_7d['change_7d_pct']:.2f}%)")
        # Mayor volumen
        highest_volume = max(successful_data, key=lambda x: x["volume_24h_usd"])
        symbol_vol = self.symbol_short[data.index(highest_volume)]
        volume_str = self.format_volume(highest_volume["volume_24h_usd"])
        print(f"   💰 Mayor volumen 24h: {symbol_vol} (${volume_str})")

        # Mayor market cap
        if all(c.get("market_cap", 0) > 0 for c in successful_data):
            largest_mc = max(successful_data, key=lambda x: x["market_cap"])
            symbol_mc = self.symbol_short[data.index(largest_mc)]
            mc_str = self.format_volume(largest_mc["market_cap"])
            print(f"   🏦 Mayor market cap: {symbol_mc} (${mc_str})")

    def export_to_json(self, data: List[Dict[str, Any]], filename: str = None):
        """Exportar datos a archivo JSON."""

        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"crypto_comparison_{timestamp}.json"

        export_data = {
            "timestamp": datetime.now().isoformat(),
            "cryptocurrencies": self.symbol_short,
            "data": data
        }

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)

        print(f"\n💾 Datos exportados a: {filename}")
        return filename

    def run_full_comparison(self, export: bool = True):
        """
        Ejecutar comparación completa.

        Args:
            export: Si exportar resultados a JSON
        """
        # Obtener datos
        data = self.get_all_crypto_data()

        # Mostrar tabla
        self.print_comparison_table(data)

        # Exportar si solicitado
        if export:
            filename = self.export_to_json(data)
            return data, filename

        return data, None


def main():
    """Función principal."""

    print("🚀 COMPARACIÓN DE CRIPTOMONEDAS")
    print("Analizando BTC, ETH, XRP y SOL")
    print("=" * 50)

    try:
        # Crear comparador
        comparator = CryptoComparison()

        # Ejecutar comparación completa
        data, export_file = comparator.run_full_comparison(export=True)

        print("\n✅ Comparación completada exitosamente!")
        print("\n💡 Interpretación:")
        print("   🟢 Verde: Cambio positivo")
        print("   🔴 Rojo: Cambio negativo")
        print("   ⚪ Blanco: Sin cambio")

    except Exception as e:
        print(f"❌ Error en la comparación: {e}")
        return


if __name__ == "__main__":
    main()
