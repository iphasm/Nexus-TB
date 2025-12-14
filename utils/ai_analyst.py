
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

    def analyze_signal(self, symbol, timeframe, indicators, personality="Standard"):
        """
        Generates a narrative analysis of the market situation.
        """
        if not self.client:
            return "⚠️ IA Desconectada. Configura OPENAI_API_KEY."

        # Construct the context
        prompt = f"""
        Act as a Professional Crypto Trader ({personality} Persona).
        Analyze this setup for {symbol} on {timeframe} timeframe:
        
        Price: {indicators.get('price', 'N/A')}
        RSI: {indicators.get('rsi', 'N/A')}
        Bollinger Gap: {indicators.get('gap', 'N/A')}%
        Recent Volume: {indicators.get('vol', 'Normal')}
        
        Task: Explain specifically WHY this is a good/bad entry or what the market is doing.
        Tone: {personality} (Sarcastic/Professional/Mystic depending on name).
        Length: MAX 2 SENTENCES. Concise.
        Language: Spanish.
        """

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a seasoned high-frequency trading algorithm with a personality."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=100
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
            full_context = f"Date: {now_str}\n--- ASSET NEWS ---\n" + "\n".join(asset_headlines)
            full_context += "\n\n--- POLITICAL (DJT) ---\n" + "\n".join(trump_headlines)
            full_context += "\n\n--- MACRO (S&P 500) ---\n" + "\n".join(macro_headlines)

            if not asset_headlines and not trump_headlines and not macro_headlines:
                return {'score': 0, 'reason': "No recent news found.", 'volatility_risk': "LOW"}
            
            # 4. Analyze with GPT (Trump + Fed Aware)
            prompt = f"""
            Analyze market sentiment for: {symbol}.
            
            Context Data:
            {full_context}
            
            check 1: "THE TRUMP FACTOR"
            - Keywords: "Trump", "Election", "Regulations", "Tariff", "Trade War".
            - Tariff/Trade War = Negative for Risk Assets (usually).
            - Deregulation/Pro-Crypto = Positive.
            
            check 2: "MACRO SHIELD" (FED/ECONOMY)
            - Keywords: "FOMC", "Powell", "Fed", "CPI", "Inflation", "Rate Hike", "Job Data", "NFP".
            - If these are TODAY or IMMINENT, risk is EXTREME.
            
            Task: Return JSON {{ "score": float, "reason": "string", "volatility_risk": "LOW" | "HIGH" | "EXTREME" }}.
            - "score": -1.0 to 1.0.
            - "reason": Max 10 words (Spanish). Mention Fed/Trump if relevant.
            - "volatility_risk": 
                - "EXTREME" if FOMC/CPI/Powell/War is happening NOW or TODAY.
                - "HIGH" if Trump Tariffs or uncertain political noise.
                - "LOW" otherwise.
            """

            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a hedge fund risk manager. Detect Fed Events and Political Volatility. Output JSON only."},
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
