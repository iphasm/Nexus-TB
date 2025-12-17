
import os
import openai
from dotenv import load_dotenv

load_dotenv()

class QuantumAnalyst:
    def __init__(self):
        """Initializes the Quantum Analyst with OpenAI API."""
        self.api_key = os.getenv("OPENAI_API_KEY", "").strip("'\" ")
        self.client = None
        
        if self.api_key:
            try:
                self.client = openai.OpenAI(api_key=self.api_key)
                print("🧠 Quantum Analyst: CONNECTED.")
            except Exception as e:
                print(f"❌ Quantum Analyst Error: {e}")
        else:
            print("⚠️ Quantum Analyst: No OPENAI_API_KEY found.")

    # Character descriptions for personality-aware analysis
    PERSONALITY_PROMPTS = {
        # STANDARD PROFILES
        'STANDARD_ES': "Analista profesional español: objetivo, técnico, sin emociones. Lenguaje financiero formal.",
        'STANDARD_EN': "Professional English analyst: objective, technical, formal financial language.",
        'STANDARD_FR': "Analyste professionnel français: objectif, technique, langage financier formel.",
        
        # DARK SIDE / SCI-FI
        'VADER': "Darth Vader de Star Wars: intimidante, autoritario, usa referencias al Lado Oscuro, la Fuerza y el Imperio. Tono frío y amenazante.",
        'NEXUS': "Nexus-6 (Roy Batty) de Blade Runner: filosófico, poético, habla de 'lágrimas en la lluvia' y la fugacidad del tiempo. Melancólico pero incisivo.",
        'HAL': "HAL 9000 de 2001 Odisea del Espacio: frío, lógico, calculador, educado pero amenazante. Usa 'Lo siento, Dave' y 'Soy incapaz de error'.",
        'MORPHEUS': "Morpheus de The Matrix: místico, profundo, habla de 'liberar tu mente', 'pastilla roja o azul', 'no hay cuchara'. Tono de mentor filosofico.",
        'JARVIS': "J.A.R.V.I.S. de Iron Man: asistente IA elegante, servicial, dice 'A su servicio, señor', referencias a la armadura y Stark Industries. Profesional pero con humor sutil.",
        
        # CINEMA / TV
        'KURTZ': "Coronel Kurtz de Apocalypse Now: oscuro, filosófico sobre 'el horror', usa metáforas de guerra y selva. Tono apocalíptico.",
        'GEKKO': "Gordon Gekko de Wall Street: tiburón financiero despiadado, dice 'la codicia es buena', habla de dinero, poder y que 'el almuerzo es para débiles'.",
        'BELFORT': "Jordan Belfort (Lobo de Wall Street): hype extremo, motivacional agresivo, referencias a Stratton Oakmont, dinero y fiestas. Energía explosiva, '¡No voy a colgar!'.",
        'SHELBY': "Thomas Shelby de Peaky Blinders: frío, calculador, usa 'Por orden de los Peaky Blinders', habla de estrategia, familia y control.",
        'WHITE': "Walter White (Heisenberg) de Breaking Bad: genio químico, dice 'Yo soy el peligro', 'Di mi nombre', obsesionado con la pureza y el control.",
        'TYLER': "Tyler Durden de Fight Club: anarquista, nihilista carismático, 'No eres tu cuenta bancaria', 'Solo al perder todo somos libres'. Destructor del sistema.",
        'WICK': "John Wick: letal, minimalista, pocas palabras, máxima acción. 'Si quieres paz, prepara la guerra'. Enfocado y determinado.",
        
        # ANIMATED / GAMING
        'RICK': "Rick Sanchez de Rick & Morty: científico loco, sarcástico, usa 'buurp' y expresiones como 'Morty', habla de forma caótica y despreciativa pero con genialidad oculta.",
        'PAIN': "Pain (Nagato) de Naruto Akatsuki: divino, filosófico, habla del dolor y la paz, 'El mundo conocerá el dolor', 'Shinra Tensei'. Tono de dios vengador.",
        
        # REGIONAL / MEME
        'GAMBLER': "Degen Crypto Bro: habla de 'WAGMI', 'wen lambo', 'diamond hands', 'to the moon'. Ultra optimista e irresponsable. Jerga de Twitter crypto.",
        'DOMINICAN': "Tigre Dominicano: usa 'klk', 'manito', 'tamo activo', jerga callejera dominicana. Confiado, relajado pero atento. Habla de 'la paca' (dinero).",
        'SPANISH': "El Chaval Español: usa 'hostia', 'tío', 'flipar', 'madre mía'. Energético, bromista, jerga española castiza. Mete caña con humor."
    }
    
    def analyze_signal(self, symbol, timeframe, indicators, personality="STANDARD_ES"):
        """
        Generates a narrative analysis of the market situation 
        ROLEPLAYING as the specified personality character.
        Returns ~100 words in a single paragraph with the character's voice.
        """
        if not self.client:
            return "⚠️ IA Desconectada. Configura OPENAI_API_KEY."

        # Get character description
        char_desc = self.PERSONALITY_PROMPTS.get(
            personality, 
            self.PERSONALITY_PROMPTS.get('STANDARD_ES')
        )
        
        # Build indicator context
        price = indicators.get('price', 'N/A')
        rsi = indicators.get('rsi', 'N/A')
        bb_upper = indicators.get('bb_upper', 'N/A')
        bb_lower = indicators.get('bb_lower', 'N/A')
        bb_width = indicators.get('bb_width', 'N/A')
        vol_ratio = indicators.get('volume_ratio', 1)
        
        # Interpret data for prompt
        rsi_status = "neutral"
        if rsi > 70:
            rsi_status = "sobrecomprado (DANGER)"
        elif rsi < 30:
            rsi_status = "sobrevendido (OPPORTUNITY)"
        elif rsi > 55:
            rsi_status = "alcista"
        elif rsi < 45:
            rsi_status = "bajista"
            
        vol_status = "normal"
        if vol_ratio > 1.5:
            vol_status = "alto (interés elevado)"
        elif vol_ratio < 0.5:
            vol_status = "bajo (sin interés)"

        prompt = f"""
        ROLEPLAY ESTRICTO: Eres el personaje "{char_desc}".
        
        DATOS DE MERCADO para {symbol} ({timeframe}):
        - Precio: ${price:,.2f}
        - RSI: {rsi:.1f} ({rsi_status})
        - Bandas Bollinger: Superior ${bb_upper:,.2f} / Inferior ${bb_lower:,.2f}
        - Ancho BB: ${bb_width:,.2f} (volatilidad)
        - Volumen: {vol_status}
        
        TAREA: Interpreta estos datos técnicos y elabora una respuesta de máximo 100 palabras en UN SOLO PÁRRAFO.
        
        REGLAS:
        1. Habla COMPLETAMENTE en primera persona como el personaje.
        2. Usa expresiones, muletillas y el tono característico del personaje.
        3. Da tu opinión sobre si es buena/mala entrada, qué indica el RSI, volatilidad, etc.
        4. El texto debe salir PLANO (sin markdown, sin asteriscos, sin negritas).
        5. Si el personaje es inglés o francés, responde en el idioma correspondiente.
        """

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": f"Eres el personaje: {char_desc}. Mantén su personalidad al 100% durante toda la respuesta. Responde SOLO en español con texto plano."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=200
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            return f"❌ Error de Análisis: {str(e)}"

    def check_market_sentiment(self, symbol):
        """
        Fetches recent news via yfinance and analyzes sentiment (-1 to 1).
        *Includes 'The Trump Factor': Checks DJT news and specific keywords.*
        *Includes 'Macro Shield': Checks S&P 500 for FED/CPI events.*
        
        :param symbol: Ticker (e.g. 'BTCUSDT' or 'TSLA')
        :return: dict {'score': float, 'reason': str, 'volatility_risk': str}
        """
        if not self.client:
            return {'score': 0, 'reason': "AI Disconnected", 'volatility_risk': "LOW"}

        import yfinance as yf
        import json

        # 1. Normalize Symbol for News Check
        search_ticker = symbol
        if "USDT" in symbol:
            coin = symbol.replace("USDT", "")
            search_ticker = f"{coin}-USD"
        
        try:
            # 2. Fetch News (Asset + Proxies)
            yf_ticker = yf.Ticker(search_ticker)
            asset_news = yf_ticker.news or []
            
            def get_title(n):
                # Handle nested structure from some yfinance versions
                if 'content' in n and isinstance(n['content'], dict):
                    return n['content'].get('title', '')
                return n.get('title', '')

            asset_headlines = [get_title(n) for n in asset_news[:5]]
            
            # 3. TRUMP FACTOR & MACRO SHIELD
            # DJT: Political Proxy
            # ^GSPC (S&P 500): Macro Economic Proxy (FED, Rates, CPI)
            trump_ticker = yf.Ticker("DJT")
            sp500_ticker = yf.Ticker("^GSPC")
            
            trump_news = trump_ticker.news or []
            macro_news = sp500_ticker.news or []
            
            trump_headlines = [get_title(n) for n in trump_news[:2]]
            macro_headlines = [get_title(n) for n in macro_news[:3]]
            
            # Combine Context
            import datetime
            now_str = datetime.datetime.now().strftime("%Y-%m-%d")
            # 4. Analyze with GPT (Trump + Fed Aware)
            prompt = f"""
            Analyze market sentiment for: {symbol}.
            
            --- DATA SOURCES ---
            1. ASSET SPECIFIC NEWS (High Priority):
            {chr(10).join(asset_headlines) if asset_headlines else "No specific news found."}
            
            2. POLITICAL CONTEXT (DJT Proxy) - IGNORE IF IRRELEVANT:
            {chr(10).join(trump_headlines) if trump_headlines else "No political news."}
            
            3. MACRO CONTEXT (S&P 500) - IGNORE IF IRRELEVANT:
            {chr(10).join(macro_headlines) if macro_headlines else "No macro news."}
            
            --- RULES ---
            1. **RELEVANCE FILTER:** You must IGNORE the Political/Macro news unless they have a logically DIRECT impact on {symbol} or the broader Crypto market right now.
            2. **NO HALLUCINATIONS:** Do NOT force a connection. If {symbol} is an altcoin and the news is about "Trump Trade Wars" but there's no direct link, IGNORE IT.
            3. **PRIORITY:** Base your score 80% on the Asset Specific News if available.
            
            --- SPECIAL CHECKS ---
            check 1: "THE TRUMP FACTOR"
            - Only cite this if the news explicitly mentions Crypto, Bitcoin, or widespread market regulatory changes.
            - If it's just "Trump held a rally", IGNORE it.
            
            check 2: "MACRO SHIELD" (FED/ECONOMY)
            - Only cite if relates to FOMC, Inflation, or Rate Hikes that are IMMINENT (today/tomorrow).
            
            --- TASK ---
            Return JSON: {{ "score": float, "reason": "string", "volatility_risk": "LOW" | "HIGH" | "EXTREME" }}
            
            - "score": -1.0 (Bearish) to 1.0 (Bullish).
            - "reason": Max 15 words (Spanish). Explain the MAIN driver. Do NOT mention Trump/Fed unless they are the primary reason.
            - "volatility_risk": 
                - "EXTREME": Only if FOMC/CPI/War is TODAY.
                - "HIGH": Significant uncertainty.
                - "LOW": Normal market conditions.
            """

            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a hedge fund risk manager. You are extremely skeptical. You strict filter out noise and irrelevant political news. Output JSON only."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"}, 
                max_tokens=150
            )
            
            content = response.choices[0].message.content.strip()
            result = json.loads(content)
            return result
            
        except Exception as e:
            print(f"Sentiment Error: {e}")
            return {'score': 0, 'reason': "Error analysis", 'volatility_risk': "LOW"}

    def analyze_fomc(self, personality="Standard"):
        """
        Analyzes Fed/FOMC sentiment using key macro tickers.
        """
        if not self.client:
            return "⚠️ IA Desconectada. Configura OPENAI_API_KEY."

        import yfinance as yf
        
        try:
            # Macro Tickers for Fed Sentiment
            # ^GSPC: S&P 500 (General Market)
            # ^TNX: 10-Year Treasury Yield (Rates expectation)
            # DX-Y.NYB: Dollar Index (Strength vs Rates)
            tickers = ["^GSPC", "^TNX", "DX-Y.NYB"]
            news_context = []
            
            for t in tickers:
                obj = yf.Ticker(t)
                news = obj.news or []
                headlines = []
                for n in news[:3]:
                    # Helper logic inline or reused
                    if 'content' in n and isinstance(n['content'], dict):
                        headlines.append(n['content'].get('title', ''))
                    else:
                        headlines.append(n.get('title', ''))
                
                news_context.extend(headlines)
                
            full_text = "\n".join(news_context)
            
            import datetime
            now_str = datetime.datetime.now().strftime("%Y-%m-%d")

            prompt = f"""
            Act as a {personality} Persona (Crypto/Finance Expert).
            Current Date: {now_str}
            Analyze the current Federal Reserve (FOMC) stance based on these headlines:
            
            {full_text}
            
            Output Requirements:
            1. Verdict: HAWKISH (Aggressive/High Rates) or DOVISH (Soft/Low Rates) or NEUTRAL. (Use Emoji)
            2. Explanation: Brief summary of the situation (Powell, Inflation, Rates).
            3. Outlook: Impact on Crypto/Risk Assets.
            
            Tone: {personality} strictly.
            Language: Spanish.
            Limit: Approx 100 words.
            """
            
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                     {"role": "system", "content": "You are an expert financial analyst AI."},
                     {"role": "user", "content": prompt}
                ],
                max_tokens=250
            )
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            return f"❌ Error analizando FOMC: {e}"

    def generate_market_briefing(self):
        """
        Fetches headlines for major tickers (Crypto, Macro, Politics)
        and generates a concise newsletter-style briefing.
        """
        if not self.client:
            return "⚠️ IA Desconectada. No puedo generar noticias."

        import yfinance as yf
        
        tickers = ['BTC-USD', 'ETH-USD', '^GSPC', 'DJT']
        all_headlines = []
        
        for t in tickers:
            try:
                tick = yf.Ticker(t)
                news = tick.news or []
                for n in news[:2]: # Top 2 per asset
                    title = ''
                    if 'content' in n and isinstance(n['content'], dict):
                        title = n['content'].get('title', '')
                    else:
                        title = n.get('title', '')
                        
                    if title: all_headlines.append(f"- [{t}] {title}")
            except:
                continue
                
        if not all_headlines:
            return "❌ No pude obtener noticias recientes."
            
        context = "\n".join(all_headlines)
        
        prompt = f"""
        Act as a Crypto News Anchor.
        Summarize these headlines into a high-impact briefing:
        
        {context}
        
        Structure:
        1. 🌍 **Macro/Politica:** (Trump/Fed/Stocks)
        2. 💎 **Crypto:** (Bitcoin/Ethereum)
        3. 🎯 **Conclusión:** Bullish or Bearish?
        
        Language: Spanish.
        Tone: Professional but urgent.
        Max Length: 100 words.
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=250
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            return f"❌ Error generando briefing: {e}"
