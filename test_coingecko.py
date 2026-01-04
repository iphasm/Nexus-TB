#!/usr/bin/env python3
"""
Test script para verificar CoinGecko API
"""

import os
import requests

def test_coingecko():
    print("🪙 TESTEANDO COINGECKO API")
    print("=" * 50)

    # Usar variable de entorno (Railway)
    api_key = os.getenv("COINGECKO_API_KEY")

    if not api_key:
        print("❌ COINGECKO_API_KEY no configurada")
        print("   Configurar variable de entorno COINGECKO_API_KEY en Railway")
        print("   Obtener API key gratuita: https://www.coingecko.com/en/api")
        return False
    base_url = "https://api.coingecko.com/api/v3"

    try:
        # Hacer llamada directa con requests
        headers = {"x-cg-demo-api-key": api_key}
        url = f"{base_url}/coins/bitcoin"

        params = {
            'localization': 'false',
            'tickers': 'false',
            'market_data': 'true',
            'community_data': 'true',
            'developer_data': 'true',
            'sparkline': 'false'
        }

        print(f"🌐 Llamando a: {url}")
        response = requests.get(url, headers=headers, params=params, timeout=10)

        if response.status_code == 200:
            coin_data = response.json()
            print("✅ Datos obtenidos exitosamente")
        else:
            print(f"❌ Error HTTP {response.status_code}: {response.text}")
            return False

        print(f"📈 Nombre: {coin_data.get('name', 'N/A')}")
        print(f"🏷️  Símbolo: {coin_data.get('symbol', 'N/A')}")
        print(f"📊 Community Score: {coin_data.get('community_score', 'N/A')}")
        print(f"🛠️  Developer Score: {coin_data.get('developer_score', 'N/A')}")
        print(f"💧 Liquidity Score: {coin_data.get('liquidity_score', 'N/A')}")

        # Verificar datos de comunidad
        community = coin_data.get('community_data', {})
        print("\n👥 DATOS DE COMUNIDAD:")
        print(f"   Twitter Followers: {community.get('twitter_followers', 'N/A')}")
        print(f"   Reddit Subscribers: {community.get('reddit_subscribers', 'N/A')}")
        print(f"   Telegram Users: {community.get('telegram_channel_user_count', 'N/A')}")

        # Verificar datos de desarrollo
        developer = coin_data.get('developer_data', {})
        print("\n🛠️  DATOS DE DESARROLLO:")
        print(f"   Repositorios: {len(developer.get('repos', []))}")
        if developer.get('repos'):
            total_stars = sum(repo.get('stargazers_count', 0) for repo in developer.get('repos', []))
            total_forks = sum(repo.get('forks_count', 0) for repo in developer.get('repos', []))
            print(f"   Total Stars: {total_stars}")
            print(f"   Total Forks: {total_forks}")
            print(f"   Commits 4 semanas: {developer.get('commit_count_4_weeks', 'N/A')}")
            print(f"   Contributors: {developer.get('pull_request_contributors', 'N/A')}")

        # Verificar datos de mercado
        market = coin_data.get('market_data', {})
        print("\n💰 DATOS DE MERCADO:")
        print(f"   Market Cap Rank: #{coin_data.get('market_cap_rank', 'N/A')}")
        print(f"   Total Supply: {market.get('total_supply', 'N/A')}")
        print(f"   Circulating Supply: {market.get('circulating_supply', 'N/A')}")
        print(f"   Max Supply: {market.get('max_supply', 'N/A')}")

        print("\n✅ TEST COMPLETADO - CoinGecko API funciona correctamente")
        return True
        print("✅ Cliente CoinGecko inicializado")

        # Probar obtener datos de Bitcoin
        print("\n📊 Probando datos de Bitcoin...")
        coin_data = cg.get_coin_by_id(
            id='bitcoin',
            localization=False,
            tickers=False,
            market_data=True,
            community_data=True,
            developer_data=True,
            sparkline=False
        )

        print("✅ Datos obtenidos exitosamente")
        print(f"📈 Nombre: {coin_data.get('name', 'N/A')}")
        print(f"🏷️  Símbolo: {coin_data.get('symbol', 'N/A')}")
        print(f"📊 Community Score: {coin_data.get('community_score', 'N/A')}")
        print(f"🛠️  Developer Score: {coin_data.get('developer_score', 'N/A')}")
        print(f"💧 Liquidity Score: {coin_data.get('liquidity_score', 'N/A')}")

        # Verificar datos de comunidad
        community = coin_data.get('community_data', {})
        print("\n👥 DATOS DE COMUNIDAD:")
        print(f"   Twitter Followers: {community.get('twitter_followers', 'N/A')}")
        print(f"   Reddit Subscribers: {community.get('reddit_subscribers', 'N/A')}")
        print(f"   Telegram Users: {community.get('telegram_channel_user_count', 'N/A')}")

        # Verificar datos de desarrollo
        developer = coin_data.get('developer_data', {})
        print("\n🛠️  DATOS DE DESARROLLO:")
        print(f"   Repositorios: {len(developer.get('repos', []))}")
        if developer.get('repos'):
            total_stars = sum(repo.get('stargazers_count', 0) for repo in developer.get('repos', []))
            total_forks = sum(repo.get('forks_count', 0) for repo in developer.get('repos', []))
            print(f"   Total Stars: {total_stars}")
            print(f"   Total Forks: {total_forks}")
            print(f"   Commits 4 semanas: {developer.get('commit_count_4_weeks', 'N/A')}")
            print(f"   Contributors: {developer.get('pull_request_contributors', 'N/A')}")

        # Verificar datos de mercado
        market = coin_data.get('market_data', {})
        print("\n💰 DATOS DE MERCADO:")
        print(f"   Market Cap Rank: #{coin_data.get('market_cap_rank', 'N/A')}")
        print(f"   Total Supply: {market.get('total_supply', 'N/A')}")
        print(f"   Circulating Supply: {market.get('circulating_supply', 'N/A')}")
        print(f"   Max Supply: {market.get('max_supply', 'N/A')}")

        print("\n✅ TEST COMPLETADO - CoinGecko API funciona correctamente")
        return True

    except Exception as e:
        print(f"❌ Error en CoinGecko API: {e}")
        print("💡 Posibles causas:")
        print("   • API key inválida")
        print("   • Límites de rate excedidos")
        print("   • Endpoint no disponible")
        print("   • Problemas de red")
        return False

if __name__ == "__main__":
    test_coingecko()
