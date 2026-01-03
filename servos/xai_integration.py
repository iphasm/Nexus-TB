#!/usr/bin/env python3
"""
Módulo de integración híbrida xAI + OpenAI para Nexus Core.
Implementa sistema de fallback inteligente y uso estratégico de recursos.
"""

import os
import json
import time
import logging
from typing import Dict, Any, Optional, Tuple
import requests

logger = logging.getLogger(__name__)

class NexusXAIIntegration:
    """
    Integración híbrida de xAI y OpenAI para optimizar costos y rendimiento.
    xAI para tareas rápidas y básicas, OpenAI para análisis complejos.
    """

    def __init__(self):
        # Configuración de xAI desde variables de entorno (sin valores por defecto sensibles)
        self.xai_api_key = os.getenv("XAI_API_KEY", "").strip()
        self.xai_base_url = os.getenv("XAI_BASE_URL", "https://api.x.ai/v1")
        self.xai_model = os.getenv("XAI_MODEL", "grok-3")  # Modelo balanceado por defecto
        self.xai_timeout = int(os.getenv("XAI_TIMEOUT", "10"))  # Timeout en segundos
        self.xai_max_tokens = int(os.getenv("XAI_MAX_TOKENS", "500"))
        self.xai_cost_per_token = float(os.getenv("XAI_COST_PER_TOKEN", "0.00002"))  # Costo estimado

        # Configuración de costos y límites
        # Estadísticas de uso
        self.usage_stats = {
            "xai_queries": 0,
            "xai_success": 0,
            "xai_failed": 0,
            "fallback_to_openai": 0,
            "total_cost": 0.0,
            "avg_response_time": 0.0
        }

        # Verificar configuración
        if not self.xai_api_key:
            logger.warning("XAI_API_KEY no configurada - xAI estará deshabilitado")
            self.xai_available = False
        else:
            self.xai_available = True
            logger.info("xAI integration inicializada correctamente")

    def query_xai(self, prompt: str, context: str = "trading",
                  max_retries: int = 2, fallback: bool = True) -> Dict[str, Any]:
        """
        Consulta a xAI con sistema de fallback a OpenAI.

        Args:
            prompt: Consulta a realizar
            context: Contexto (trading, analysis, education, alert)
            max_retries: Número máximo de reintentos
            fallback: Si debe hacer fallback a OpenAI en caso de error

        Returns:
            Dict con resultado de la consulta
        """
        self.usage_stats["xai_queries"] += 1

        if not self.xai_available:
            if fallback:
                logger.info("xAI no disponible, usando fallback a OpenAI")
                return self._fallback_to_openai(prompt, context)
            else:
                return {
                    "success": False,
                    "error": "xAI no configurado",
                    "fallback_used": False
                }

        # Preparar contexto específico
        context_prompts = {
            "trading": "Eres un analista de trading experimentado. Responde de forma concisa y técnica.",
            "analysis": "Eres un analista técnico especializado en criptomonedas. Sé preciso y data-driven.",
            "education": "Explica conceptos de trading de forma clara y educativa.",
            "alert": "Eres un sistema de alertas de trading. Responde con formato claro y actionable.",
            "calculation": "Eres un calculador financiero. Proporciona resultados precisos con fórmulas."
        }

        full_prompt = f"{context_prompts.get(context, context_prompts['trading'])}\n\n{prompt}"

        # Intentar consulta con reintentos
        for attempt in range(max_retries + 1):
            try:
                start_time = time.time()

                headers = {
                    "Authorization": f"Bearer {self.xai_api_key}",
                    "Content-Type": "application/json"
                }

                payload = {
                    "model": self.xai_model,
                    "messages": [{"role": "user", "content": full_prompt}],
                    "max_tokens": self.xai_max_tokens,
                    "temperature": 0.3  # Bajo para respuestas consistentes
                }

                response = requests.post(
                    f"{self.xai_base_url}/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=self.xai_timeout
                )

                end_time = time.time()
                response_time = end_time - start_time

                if response.status_code == 200:
                    result = response.json()
                    answer = result["choices"][0]["message"]["content"]

                    # Actualizar estadísticas
                    self.usage_stats["xai_success"] += 1
                    self._update_response_time(response_time)

                    tokens_used = result.get("usage", {}).get("total_tokens", 0)
                    cost = tokens_used * self.xai_cost_per_token
                    self.usage_stats["total_cost"] += cost

                    return {
                        "success": True,
                        "response": answer,
                        "model": self.xai_model,
                        "response_time": round(response_time, 2),
                        "tokens_used": tokens_used,
                        "cost": cost,
                        "fallback_used": False,
                        "provider": "xai"
                    }

                elif response.status_code in [429, 500, 502, 503, 504]:
                    # Errores temporales, reintentar
                    if attempt < max_retries:
                        logger.warning(f"xAI error {response.status_code}, reintento {attempt + 1}")
                        time.sleep(2 ** attempt)  # Exponential backoff
                        continue

                else:
                    # Error permanente
                    logger.error(f"xAI error permanente {response.status_code}: {response.text}")
                    break

            except requests.exceptions.Timeout:
                logger.warning(f"xAI timeout en intento {attempt + 1}")
                if attempt < max_retries:
                    continue
            except Exception as e:
                logger.error(f"Error en xAI consulta: {e}")
                break

        # Si llegamos aquí, todos los intentos fallaron
        self.usage_stats["xai_failed"] += 1

        if fallback:
            logger.info("xAI falló, usando fallback a OpenAI")
            self.usage_stats["fallback_to_openai"] += 1
            return self._fallback_to_openai(prompt, context)
        else:
            return {
                "success": False,
                "error": f"xAI falló después de {max_retries + 1} intentos",
                "fallback_used": False
            }

    def _fallback_to_openai(self, prompt: str, context: str) -> Dict[str, Any]:
        """
        Fallback a OpenAI cuando xAI falla.
        Importa dinámicamente para evitar dependencias circulares.
        """
        try:
            # Importar aquí para evitar dependencias circulares
            from servos.ai_analyst import NexusAnalyst

            analyst = NexusAnalyst()

            # Mapear contextos de xAI a tipos de análisis de OpenAI
            context_mapping = {
                "trading": "signal_analysis",
                "analysis": "technical_analysis",
                "education": "educational",
                "alert": "alert_system",
                "calculation": "calculation"
            }

            analysis_type = context_mapping.get(context, "general_analysis")

            # Usar OpenAI para el análisis
            result = analyst.analyze_market_data(
                market_data={"query": prompt, "context": context},
                analysis_type=analysis_type
            )

            if result and "analysis" in result:
                return {
                    "success": True,
                    "response": result["analysis"],
                    "model": "gpt-4o",  # Asumiendo configuración actual
                    "response_time": result.get("processing_time", 0),
                    "tokens_used": 0,  # No disponible en OpenAI response
                    "cost": 0.0,  # Costo ya manejado por OpenAI
                    "fallback_used": True,
                    "provider": "openai"
                }
            else:
                return {
                    "success": False,
                    "error": "Fallback a OpenAI falló",
                    "fallback_used": True
                }

        except Exception as e:
            logger.error(f"Error en fallback a OpenAI: {e}")
            return {
                "success": False,
                "error": f"Fallback error: {str(e)}",
                "fallback_used": True
            }

    def _update_response_time(self, response_time: float):
        """Actualizar promedio de tiempo de respuesta."""
        current_avg = self.usage_stats["avg_response_time"]
        total_queries = self.usage_stats["xai_success"]

        if total_queries == 1:
            self.usage_stats["avg_response_time"] = response_time
        else:
            self.usage_stats["avg_response_time"] = (
                (current_avg * (total_queries - 1)) + response_time
            ) / total_queries

    # ========== FUNCIONES DE USO ESPECÍFICO ==========

    def analyze_candlestick_pattern(self, symbol: str, current_price: float,
                                  recent_candles: list) -> Dict[str, Any]:
        """
        Análisis rápido de patrones de velas usando xAI.

        Args:
            symbol: Par de trading (ej: "BTC/USDT")
            current_price: Precio actual
            recent_candles: Lista de precios recientes [open, high, low, close]

        Returns:
            Dict con análisis del patrón
        """
        if len(recent_candles) < 4:
            return {"success": False, "error": "Se necesitan al menos 4 velas"}

        prompt = f"""Analiza el patrón de velas para {symbol}:
Precio actual: ${current_price:.2f}
Últimas 4 velas (OHLC): {recent_candles}

Identifica el patrón técnico y su implicación (alcista/bajista/neutral).
Responde en formato conciso."""

        result = self.query_xai(prompt, context="analysis", max_retries=1)

        if result["success"]:
            return {
                "success": True,
                "pattern_analysis": result["response"],
                "symbol": symbol,
                "current_price": current_price,
                "provider": result["provider"]
            }
        else:
            return {"success": False, "error": result.get("error", "Análisis falló")}

    def calculate_position_size(self, capital: float, entry_price: float,
                               stop_loss_price: float, risk_percent: float = 1.0) -> Dict[str, Any]:
        """
        Cálculo de tamaño de posición usando xAI.

        Args:
            capital: Capital total disponible
            entry_price: Precio de entrada
            stop_loss_price: Precio de stop loss
            risk_percent: Porcentaje de riesgo (1% por defecto)

        Returns:
            Dict con cálculos de position sizing
        """
        prompt = f"""Calcula el tamaño óptimo de posición:

Capital total: ${capital:.2f}
Precio de entrada: ${entry_price:.2f}
Stop Loss: ${stop_loss_price:.2f}
Riesgo máximo: {risk_percent}%

Fórmula: Position Size = (Capital × Risk%) / |Entry - Stop Loss|

Proporciona:
1. Tamaño de posición en USD
2. Tamaño de posición en unidades
3. Riesgo total en USD
4. Ratio riesgo/recompensa sugerido"""

        result = self.query_xai(prompt, context="calculation", max_retries=1)

        if result["success"]:
            return {
                "success": True,
                "calculations": result["response"],
                "parameters": {
                    "capital": capital,
                    "entry_price": entry_price,
                    "stop_loss": stop_loss_price,
                    "risk_percent": risk_percent
                },
                "provider": result["provider"]
            }
        else:
            return {"success": False, "error": result.get("error", "Cálculo falló")}

    def explain_trading_concept(self, concept: str, user_level: str = "intermediate") -> Dict[str, Any]:
        """
        Explicación educativa de conceptos de trading usando xAI.

        Args:
            concept: Concepto a explicar (ej: "RSI", "fibonacci", "support/resistance")
            user_level: Nivel del usuario (beginner, intermediate, advanced)

        Returns:
            Dict con explicación educativa
        """
        prompt = f"""Explica el concepto de trading: "{concept}"

Nivel del usuario: {user_level}

Proporciona:
1. Definición clara y concisa
2. Cómo se calcula/identifica
3. Interpretación práctica
4. Ejemplo simple
5. Errores comunes a evitar

Mantén la explicación educativa y actionable."""

        result = self.query_xai(prompt, context="education", max_retries=1)

        if result["success"]:
            return {
                "success": True,
                "explanation": result["response"],
                "concept": concept,
                "user_level": user_level,
                "provider": result["provider"]
            }
        else:
            return {"success": False, "error": result.get("error", "Explicación falló")}

    def validate_trading_signal(self, signal_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validación rápida de señales de trading usando xAI.

        Args:
            signal_data: Datos de la señal (symbol, side, entry, sl, tp, etc.)

        Returns:
            Dict con validación de la señal
        """
        prompt = f"""Valida esta señal de trading:

Símbolo: {signal_data.get('symbol', 'N/A')}
Dirección: {signal_data.get('side', 'N/A')}
Precio entrada: ${signal_data.get('entry_price', 0):.2f}
Stop Loss: ${signal_data.get('stop_loss', 0):.2f}
Take Profit: ${signal_data.get('take_profit', 0):.2f}
Razón: {signal_data.get('reason', 'N/A')}

Evalúa:
1. ¿Es la señal técnica válida?
2. ¿Está bien configurado el risk management?
3. ¿Qué factores adicionales confirmarían la entrada?
4. Nivel de confianza (Alto/Medio/Bajo)

Responde de forma concisa y actionable."""

        result = self.query_xai(prompt, context="alert", max_retries=1)

        if result["success"]:
            return {
                "success": True,
                "validation": result["response"],
                "signal_data": signal_data,
                "provider": result["provider"]
            }
        else:
            return {"success": False, "error": result.get("error", "Validación falló")}

    def get_usage_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas de uso del sistema híbrido."""
        stats = self.usage_stats.copy()
        stats["xai_available"] = self.xai_available
        stats["xai_model"] = self.xai_model
        stats["success_rate"] = (
            (stats["xai_success"] / stats["xai_queries"] * 100)
            if stats["xai_queries"] > 0 else 0
        )
        stats["fallback_rate"] = (
            (stats["fallback_to_openai"] / stats["xai_queries"] * 100)
            if stats["xai_queries"] > 0 else 0
        )
        return stats

    def reset_stats(self):
        """Reiniciar estadísticas de uso."""
        self.usage_stats = {
            "xai_queries": 0,
            "xai_success": 0,
            "xai_failed": 0,
            "fallback_to_openai": 0,
            "total_cost": 0.0,
            "avg_response_time": 0.0
        }

# Instancia global para uso en toda la aplicación
xai_integration = NexusXAIIntegration()

# Funciones de conveniencia para uso directo
def query_xai_fast(prompt: str, context: str = "trading") -> str:
    """
    Función de conveniencia para consultas rápidas a xAI.

    Returns:
        String con la respuesta o mensaje de error
    """
    result = xai_integration.query_xai(prompt, context, max_retries=1)
    return result["response"] if result["success"] else f"Error: {result.get('error', 'Consulta falló')}"

def analyze_pattern(symbol: str, current_price: float, candles: list) -> str:
    """Análisis rápido de patrones de velas."""
    result = xai_integration.analyze_candlestick_pattern(symbol, current_price, candles)
    return result.get("pattern_analysis", "Error en análisis") if result["success"] else result.get("error", "Análisis falló")

def calculate_position(capital: float, entry: float, sl: float, risk_pct: float = 1.0) -> str:
    """Cálculo rápido de position sizing."""
    result = xai_integration.calculate_position_size(capital, entry, sl, risk_pct)
    return result.get("calculations", "Error en cálculo") if result["success"] else result.get("error", "Cálculo falló")

def explain_concept(concept: str, level: str = "intermediate") -> str:
    """Explicación educativa de conceptos."""
    result = xai_integration.explain_trading_concept(concept, level)
    return result.get("explanation", "Error en explicación") if result["success"] else result.get("error", "Explicación falló")
