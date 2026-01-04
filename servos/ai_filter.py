#!/usr/bin/env python3
"""
AI Filter Engine - Sistema Avanzado de Filtrado de Señales
Utiliza el sistema híbrido xAI + GPT-4o para filtrar señales basado en múltiples factores.
"""

import os
import time
import asyncio
import aiohttp
from typing import Dict, Any, Optional, Tuple, List
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

# Importar el sistema de valoración optimizado
try:
    from ai_crypto_valuation import AICryptoValuation
    VALUATION_SYSTEM_AVAILABLE = True
except ImportError:
    VALUATION_SYSTEM_AVAILABLE = False
    logger.warning("⚠️ Sistema de valoración no disponible")

class AIFilterEngine:
    """
    Motor de filtrado inteligente de señales usando IA híbrida.

    Filtra señales basado en:
    - Fear & Greed Index
    - Análisis de sentimiento social (X/Twitter)
    - Volatilidad del mercado
    - Momentum técnico
    - Análisis fundamental contextual
    """

    def __init__(self):
        self.cache = {}
        self.cache_timeout = 300  # 5 minutos
        self.xai_integration = None
        self.valuation_system = None
        self.valuation_cache = {}  # Cache para valoraciones por cripto
        self.valuation_cache_timeout = 600  # 10 minutos para valoraciones

    async def initialize(self):
        """Inicializar el motor de filtrado."""
        try:
            from servos.xai_integration import xai_integration
            self.xai_integration = xai_integration
            logger.info("🤖 AI Filter Engine inicializado con sistema híbrido")
        except ImportError:
            logger.warning("⚠️ AI Filter: Sistema híbrido no disponible, usando modo limitado")

        # Inicializar sistema de valoración optimizado
        if VALUATION_SYSTEM_AVAILABLE:
            try:
                self.valuation_system = AICryptoValuation()
                logger.info("🎯 Sistema de valoración GPT-4o Mini integrado al AI Filter")
            except Exception as e:
                logger.warning(f"⚠️ Error inicializando sistema de valoración: {e}")
        else:
            logger.warning("⚠️ Sistema de valoración no disponible para AI Filter")

    async def should_filter_signal(self, signal_data: Dict[str, Any],
                                 session_config: Dict[str, Any]) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Determina si una señal debe ser filtrada.

        Args:
            signal_data: Datos de la señal (symbol, side, entry_price, etc.)
            session_config: Configuración de la sesión del usuario

        Returns:
            Tuple: (should_filter, reason, analysis_data)
        """
        if not session_config.get('sentiment_filter', True):
            return False, "AI Filter desactivado", {}

        try:
            # 1. Obtener datos de sentimiento múltiples
            sentiment_data = await self._gather_sentiment_data(signal_data['symbol'])

            # 2. Analizar con IA híbrida
            ai_analysis = await self._analyze_with_hybrid_ai(signal_data, sentiment_data)

            # 3. Calcular score de filtrado
            filter_score, should_filter, reason = self._calculate_filter_decision(
                signal_data, sentiment_data, ai_analysis
            )

            # 4. Preparar datos de análisis para logging
            analysis_data = {
                'sentiment_data': sentiment_data,
                'ai_analysis': ai_analysis,
                'filter_score': filter_score,
                'timestamp': datetime.now().isoformat(),
                'symbol': signal_data['symbol']
            }

            logger.info(f"🤖 AI Filter | {signal_data['symbol']} | Score: {filter_score:.2f} | "
                       f"Decision: {'FILTER' if should_filter else 'ALLOW'} | Reason: {reason}")

            return should_filter, reason, analysis_data

        except Exception as e:
            logger.error(f"❌ AI Filter error: {e}")
            # En caso de error, permitir la señal (fail-safe)
            return False, f"Error en AI Filter: {e}", {}

    async def _gather_sentiment_data(self, symbol: str) -> Dict[str, Any]:
        """Reunir datos de sentimiento de múltiples fuentes."""
        sentiment_data = {}

        try:
            # 1. Fear & Greed Index
            fng_data = await self._get_fear_greed_index()
            sentiment_data['fear_greed'] = fng_data

            # 2. Volatilidad del mercado (usando ATR o volatilidad histórica)
            volatility = await self._calculate_market_volatility(symbol)
            sentiment_data['volatility'] = volatility

            # 3. Momentum técnico (RSI, MACD, etc.)
            momentum = await self._calculate_technical_momentum(symbol)
            sentiment_data['momentum'] = momentum

            # 4. Sentimiento social (si está disponible a través del sistema híbrido)
            social_sentiment = await self._get_social_sentiment(symbol)
            sentiment_data['social_sentiment'] = social_sentiment

            # 5. 🎯 VALORACIÓN GPT-4o MINI (NUEVO - INTEGRACIÓN PRINCIPAL)
            if self.valuation_system:
                ai_valuation = await self._get_ai_valuation(symbol)
                sentiment_data['ai_valuation'] = ai_valuation
            else:
                sentiment_data['ai_valuation'] = {'available': False, 'reason': 'Sistema de valoración no disponible'}

        except Exception as e:
            logger.warning(f"⚠️ Error obteniendo datos de sentimiento: {e}")
            sentiment_data['error'] = str(e)

        return sentiment_data

    async def _get_fear_greed_index(self) -> Dict[str, Any]:
        """Obtener Fear & Greed Index."""
        cache_key = 'fear_greed'
        if cache_key in self.cache:
            cached_data, timestamp = self.cache[cache_key]
            if time.time() - timestamp < self.cache_timeout:
                return cached_data

        try:
            url = "https://api.alternative.me/fng/"
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        fng_value = int(data['data'][0]['value'])
                        fng_classification = data['data'][0]['value_classification']

                        result = {
                            'value': fng_value,
                            'classification': fng_classification,
                            'timestamp': datetime.now().isoformat()
                        }

                        self.cache[cache_key] = (result, time.time())
                        return result

        except Exception as e:
            logger.warning(f"⚠️ Error obteniendo Fear & Greed Index: {e}")

        # Fallback
        return {
            'value': 50,  # Neutral
            'classification': 'Neutral',
            'error': 'No disponible'
        }

    async def _calculate_market_volatility(self, symbol: str) -> Dict[str, Any]:
        """Calcular volatilidad del mercado."""
        try:
            # Aquí podríamos integrar con el bridge para obtener datos de volatilidad
            # Por ahora, devolver un valor simulado basado en el símbolo
            if 'BTC' in symbol:
                volatility = 0.8  # Alta volatilidad para BTC
            elif 'ETH' in symbol:
                volatility = 0.7
            else:
                volatility = 0.5  # Volatilidad media

            return {
                'level': volatility,
                'classification': 'High' if volatility > 0.7 else 'Medium' if volatility > 0.5 else 'Low'
            }

        except Exception as e:
            return {'level': 0.5, 'classification': 'Medium', 'error': str(e)}

    async def _calculate_technical_momentum(self, symbol: str) -> Dict[str, Any]:
        """Calcular momentum técnico."""
        try:
            # Aquí podríamos calcular RSI, MACD, etc.
            # Por ahora, devolver valores simulados
            momentum_score = 0.6  # Momentum neutral positivo

            return {
                'score': momentum_score,
                'direction': 'Bullish' if momentum_score > 0.6 else 'Bearish' if momentum_score < 0.4 else 'Neutral',
                'strength': 'Strong' if abs(momentum_score - 0.5) > 0.3 else 'Weak'
            }

        except Exception as e:
            return {'score': 0.5, 'direction': 'Neutral', 'strength': 'Unknown', 'error': str(e)}

    async def _get_social_sentiment(self, symbol: str) -> Dict[str, Any]:
        """Obtener sentimiento social usando el sistema híbrido."""
        if not self.xai_integration:
            return {'available': False, 'reason': 'Sistema híbrido no disponible'}

        try:
            # Usar xAI para analizar sentimiento social
            query = f"Analiza el sentimiento actual en redes sociales para {symbol}. ¿Es predominantemente positivo, negativo o neutral? Proporciona un score de -1 a 1."

            result = self.xai_integration.query_xai(query, context="analysis", max_retries=1)

            if result['success']:
                # Intentar extraer un score numérico de la respuesta
                response_text = result['response'].lower()
                if 'positivo' in response_text or 'bullish' in response_text:
                    score = 0.7
                elif 'negativo' in response_text or 'bearish' in response_text:
                    score = -0.7
                else:
                    score = 0.0

                return {
                    'available': True,
                    'score': score,
                    'analysis': result['response'][:200],
                    'provider': result['provider']
                }
            else:
                return {'available': False, 'reason': 'Análisis falló', 'error': result.get('error')}

        except Exception as e:
            return {'available': False, 'reason': 'Error en análisis', 'error': str(e)}

    async def _get_ai_valuation(self, symbol: str) -> Dict[str, Any]:
        """Obtener valoración completa de GPT-4o Mini para el símbolo."""
        if not self.valuation_system:
            return {'available': False, 'reason': 'Sistema de valoración no disponible'}

        # Verificar cache primero
        cache_key = f"valuation_{symbol}"
        if cache_key in self.valuation_cache:
            cached_data, timestamp = self.valuation_cache[cache_key]
            if time.time() - timestamp < self.valuation_cache_timeout:
                return cached_data

        try:
            # Ejecutar valoración en thread separado (ya que es síncrona)
            valuation_result = await asyncio.to_thread(self._run_valuation_sync, symbol)

            if valuation_result.get('success'):
                # Extraer datos relevantes para el filtro
                crypto_data = valuation_result.get('crypto_data', {})
                primary_valuation = valuation_result.get('primary_valuation', {})

                if primary_valuation.get('success'):
                    valuation_details = primary_valuation['valuation']['result']

                    ai_data = {
                        'available': True,
                        'long_signal': valuation_details.get('long_signal', 0.5),
                        'short_signal': valuation_details.get('short_signal', 0.5),
                        'confidence': valuation_details.get('confidence_level', 0.5),
                        'price_target_long': valuation_details.get('price_target_long'),
                        'price_target_short': valuation_details.get('price_target_short'),
                        'market_sentiment': valuation_details.get('market_sentiment', 'NEUTRAL'),
                        'current_price': crypto_data.get('price', 0),
                        'change_24h': crypto_data.get('change_24h', 0),
                        'valuation_timestamp': datetime.now().isoformat(),
                        'model_used': primary_valuation.get('primary_model', 'GPT-4o Mini')
                    }

                    # Cachear resultado
                    self.valuation_cache[cache_key] = (ai_data, time.time())

                    logger.info(f"🎯 AI Valuation obtenida para {symbol}: LONG {ai_data['long_signal']:.3f} | SHORT {ai_data['short_signal']:.3f}")
                    return ai_data

            # Si falla la valoración, devolver datos básicos
            return {
                'available': False,
                'reason': 'Valoración falló',
                'error': valuation_result.get('error', 'Error desconocido'),
                'fallback': True
            }

        except Exception as e:
            logger.error(f"❌ Error obteniendo valoración AI para {symbol}: {e}")
            return {
                'available': False,
                'reason': 'Error en valoración AI',
                'error': str(e),
                'fallback': True
            }

    def _run_valuation_sync(self, symbol: str) -> Dict[str, Any]:
        """Ejecutar valoración de forma síncrona (para usar en thread)."""
        try:
            # Crear payload para valoración individual
            crypto_info = self._get_crypto_info(symbol)

            # Obtener datos básicos
            market_data = {symbol: self.valuation_system.get_crypto_data(f"{symbol}-USD")}
            coingecko_data = {symbol: self.valuation_system.get_coingecko_metrics(crypto_info['coingecko_id'])}
            global_crypto = self.valuation_system.get_global_crypto_data()
            fear_greed = self.valuation_system.get_fear_greed_index()
            trending_coins = self.valuation_system.get_trending_coins()
            cryptopanic_news = self.valuation_system.get_cryptopanic_news(limit=5)

            # Crear payload
            payload = self.valuation_system.create_valuation_payload(
                crypto_info, market_data[symbol], coingecko_data[symbol],
                [], cryptopanic_news, {"contexto": "AI Filter analysis"},
                fear_greed, global_crypto, trending_coins
            )

            # Obtener valoración principal
            primary_valuation = self.valuation_system.get_primary_valuation(crypto_info, payload)

            return {
                'success': True,
                'crypto_data': market_data[symbol],
                'coingecko_data': coingecko_data[symbol],
                'primary_valuation': primary_valuation
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _get_crypto_info(self, symbol: str) -> Dict[str, Any]:
        """Obtener información básica de la cripto."""
        # Mapear símbolos comunes
        crypto_map = {
            'BTC': {'short': 'BTC', 'symbol': 'BTC', 'name': 'Bitcoin', 'coingecko_id': 'bitcoin'},
            'ETH': {'short': 'ETH', 'symbol': 'ETH', 'name': 'Ethereum', 'coingecko_id': 'ethereum'},
            'XRP': {'short': 'XRP', 'symbol': 'XRP', 'name': 'XRP', 'coingecko_id': 'ripple'},
            'SOL': {'short': 'SOL', 'symbol': 'SOL', 'name': 'Solana', 'coingecko_id': 'solana'},
            'ADA': {'short': 'ADA', 'symbol': 'ADA', 'name': 'Cardano', 'coingecko_id': 'cardano'},
            'DOT': {'short': 'DOT', 'symbol': 'DOT', 'name': 'Polkadot', 'coingecko_id': 'polkadot'},
            'LINK': {'short': 'LINK', 'symbol': 'LINK', 'name': 'Chainlink', 'coingecko_id': 'chainlink'},
            'LTC': {'short': 'LTC', 'symbol': 'LTC', 'name': 'Litecoin', 'coingecko_id': 'litecoin'},
            'BNB': {'short': 'BNB', 'symbol': 'BNB', 'name': 'Binance Coin', 'coingecko_id': 'binancecoin'},
            'MATIC': {'short': 'MATIC', 'symbol': 'MATIC', 'name': 'Polygon', 'coingecko_id': 'matic-network'}
        }

        # Si es un par de trading, extraer el símbolo base
        base_symbol = symbol.split('/')[0].split('-')[0].replace('USDT', '').replace('USD', '')

        return crypto_map.get(base_symbol.upper(), {
            'short': base_symbol.upper(),
            'symbol': symbol,
            'name': base_symbol.upper(),
            'coingecko_id': base_symbol.lower()
        })

    async def _analyze_with_hybrid_ai(self, signal_data: Dict[str, Any],
                                    sentiment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analizar la señal con IA híbrida."""
        if not self.xai_integration:
            return {'available': False, 'reason': 'Sistema híbrido no disponible'}

        try:
            # Crear un prompt inteligente para el análisis
            prompt = f"""Analiza si esta señal de trading debería ser filtrada:

SÍMBOLO: {signal_data['symbol']}
DIRECCIÓN: {signal_data.get('side', 'UNKNOWN')}
PRECIO ENTRADA: ${signal_data.get('entry_price', 0):.2f}

DATOS DE SENTIMIENTO:
- Fear & Greed Index: {sentiment_data.get('fear_greed', {}).get('value', 'N/A')} ({sentiment_data.get('fear_greed', {}).get('classification', 'N/A')})
- Volatilidad: {sentiment_data.get('volatility', {}).get('classification', 'N/A')}
- Momentum: {sentiment_data.get('momentum', {}).get('direction', 'N/A')} ({sentiment_data.get('momentum', {}).get('strength', 'N/A')})

¿Debería filtrarse esta señal? Considera:
1. ¿El sentimiento del mercado es favorable para esta dirección?
2. ¿La volatilidad es apropiada para esta señal?
3. ¿El momentum técnico confirma la dirección?
4. ¿Hay riesgos de reversión basados en sentimiento?

Responde SÍ/NO para filtrar, con explicación concisa."""

            result = self.xai_integration.query_xai(prompt, context="alert", max_retries=1)

            if result['success']:
                response = result['response'].upper()
                should_filter = 'SÍ' in response or 'SI' in response or 'FILTER' in response

                return {
                    'available': True,
                    'should_filter': should_filter,
                    'analysis': result['response'],
                    'confidence': 0.8,  # Podríamos calcular esto basado en la respuesta
                    'provider': result['provider']
                }
            else:
                return {
                    'available': False,
                    'should_filter': False,  # Default: no filtrar si falla
                    'reason': 'Análisis falló',
                    'error': result.get('error')
                }

        except Exception as e:
            return {
                'available': False,
                'should_filter': False,
                'reason': 'Error en análisis IA',
                'error': str(e)
            }

    def _calculate_filter_decision(self, signal_data: Dict[str, Any],
                                 sentiment_data: Dict[str, Any],
                                 ai_analysis: Dict[str, Any]) -> Tuple[float, bool, str]:
        """
        Calcular la decisión final de filtrado basada en múltiples factores.

        Returns:
            Tuple: (filter_score, should_filter, reason)
        """
        try:
            scores = []

            # 1. Fear & Greed Index (0-100, ideal: 40-60 para señales)
            fng = sentiment_data.get('fear_greed', {}).get('value', 50)
            if fng < 30:  # Extreme Fear - Favorable para LONG
                fng_score = 0.2 if signal_data.get('side') == 'LONG' else 0.8
            elif fng > 70:  # Extreme Greed - Favorable para SHORT
                fng_score = 0.8 if signal_data.get('side') == 'LONG' else 0.2
            else:  # Neutral - Permitir
                fng_score = 0.3
            scores.append(('Fear & Greed', fng_score))

            # 2. Volatilidad (menor volatilidad = más seguro)
            vol_level = sentiment_data.get('volatility', {}).get('level', 0.5)
            vol_score = min(vol_level * 1.5, 1.0)  # Alta volatilidad = mayor score de filtro
            scores.append(('Volatilidad', vol_score))

            # 3. Momentum técnico
            momentum_score = sentiment_data.get('momentum', {}).get('score', 0.5)
            side = signal_data.get('side', 'LONG')
            if side == 'LONG':
                momentum_filter = 1.0 - momentum_score  # Mayor momentum = menor filtro
            else:
                momentum_filter = momentum_score  # Mayor momentum bajista = menor filtro
            scores.append(('Momentum', momentum_filter))

            # 4. Análisis de IA híbrida (peso alto)
            ai_score = 0.5  # Default neutral
            if ai_analysis.get('available'):
                ai_score = 0.8 if ai_analysis.get('should_filter') else 0.2
            scores.append(('IA Híbrida', ai_score))

            # 5. 🎯 VALORACIÓN GPT-4o MINI (FACTOR MÁS IMPORTANTE - NUEVO)
            gpt_valuation_score = 0.5  # Default neutral
            if sentiment_data.get('ai_valuation', {}).get('available'):
                ai_val = sentiment_data['ai_valuation']
                side = signal_data.get('side', 'LONG')

                if side == 'LONG':
                    # Para señales LONG: usar short_signal como score de filtro
                    # Si short_signal > 0.6, hay riesgo de movimiento bajista
                    gpt_valuation_score = ai_val['short_signal']
                else:  # SHORT
                    # Para señales SHORT: usar long_signal como score de filtro
                    # Si long_signal > 0.6, hay riesgo de movimiento alcista
                    gpt_valuation_score = ai_val['long_signal']

                # Ajustar score: valores > 0.6 indican filtro, valores < 0.4 permiten
                if gpt_valuation_score > 0.6:
                    gpt_valuation_score = 0.8  # Fuerte filtro
                elif gpt_valuation_score > 0.5:
                    gpt_valuation_score = 0.6  # Filtro moderado
                elif gpt_valuation_score < 0.4:
                    gpt_valuation_score = 0.2  # Permitir
                else:
                    gpt_valuation_score = 0.4  # Neutral

            scores.append(('GPT-4o Mini', gpt_valuation_score))

            # Calcular score final (promedio ponderado)
            weights = {
                'Fear & Greed': 0.15,
                'Volatilidad': 0.15,
                'Momentum': 0.15,
                'IA Híbrida': 0.2,
                'GPT-4o Mini': 0.35  # 🎯 PESO MÁXIMO - Factor más importante
            }
            total_score = 0
            total_weight = 0

            for factor_name, score in scores:
                weight = weights.get(factor_name, 0.25)
                total_score += score * weight
                total_weight += weight

            final_score = total_score / total_weight if total_weight > 0 else 0.5

            # Decisión: filtrar si score > 0.7
            should_filter = final_score > 0.7

            # Crear razón detallada
            if should_filter:
                reasons = []
                for factor_name, score in scores:
                    if score > 0.7:
                        if factor_name == 'GPT-4o Mini':
                            ai_val = sentiment_data.get('ai_valuation', {})
                            side = signal_data.get('side', 'LONG')
                            if side == 'LONG':
                                reasons.append(f"GPT-4o Mini indica riesgo bajista ({ai_val.get('short_signal', 0):.3f})")
                            else:
                                reasons.append(f"GPT-4o Mini indica riesgo alcista ({ai_val.get('long_signal', 0):.3f})")
                        else:
                            reasons.append(f"{factor_name} adverso ({score:.1f})")
                reason = f"Señal filtrada: {', '.join(reasons[:2])}"
            else:
                reason = f"Señal permitida (score: {final_score:.2f})"
                # Agregar información positiva de GPT-4o Mini si está disponible
                if sentiment_data.get('ai_valuation', {}).get('available'):
                    ai_val = sentiment_data['ai_valuation']
                    side = signal_data.get('side', 'LONG')
                    if side == 'LONG' and ai_val.get('long_signal', 0) > 0.6:
                        reason += f" | GPT-4o Mini favorable: LONG {ai_val['long_signal']:.3f}"
                    elif side == 'SHORT' and ai_val.get('short_signal', 0) > 0.6:
                        reason += f" | GPT-4o Mini favorable: SHORT {ai_val['short_signal']:.3f}"

            return final_score, should_filter, reason

        except Exception as e:
            logger.error(f"❌ Error calculando decisión de filtro: {e}")
            return 0.5, False, f"Error en cálculo: {e}"

    def get_filter_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas del filtro."""
        return {
            'cache_size': len(self.cache),
            'cache_timeout': self.cache_timeout,
            'valuation_cache_size': len(self.valuation_cache),
            'valuation_cache_timeout': self.valuation_cache_timeout,
            'xai_available': self.xai_integration is not None,
            'gpt_valuation_available': self.valuation_system is not None,
            'primary_model': self.valuation_system.primary_model['name'] if self.valuation_system else None,
            'apis_integrated': {
                'coingecko': True,  # Siempre disponible en el sistema de valoración
                'cryptopanic': True,  # Siempre disponible en el sistema de valoración
                'yfinance': True  # Siempre disponible en el sistema de valoración
            },
            'last_updated': datetime.now().isoformat()
        }

    def clear_cache(self):
        """Limpiar cache de datos."""
        self.cache.clear()
        self.valuation_cache.clear()
        logger.info("🧹 AI Filter cache completo limpiado (incluyendo valoraciones GPT-4o Mini)")

# Instancia global
ai_filter_engine = AIFilterEngine()

# Funciones de conveniencia
async def initialize_ai_filter():
    """Inicializar el motor de filtrado."""
    await ai_filter_engine.initialize()

async def should_filter_signal(signal_data: Dict[str, Any], session_config: Dict[str, Any]) -> Tuple[bool, str, Dict[str, Any]]:
    """Verificar si una señal debe ser filtrada."""
    return await ai_filter_engine.should_filter_signal(signal_data, session_config)

def get_filter_stats() -> Dict[str, Any]:
    """Obtener estadísticas del filtro."""
    return ai_filter_engine.get_filter_stats()
