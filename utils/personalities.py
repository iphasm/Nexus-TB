import random

class PersonalityManager:
    """
    Manages the bot's tone and responses based on the selected personality profile.
    """
    
    PROFILES = {
        # --- STANDARDS ---
        'STANDARD_ES': {
            'NAME': "🇪🇸 Estándar (Español)",
            'GREETING': [
                "Listo para operar.",
                "Sistemas en línea.",
                "Esperando instrucciones."
            ],
            'WELCOME': [
                (
                    "🇪🇸 **ANTIGRAVITY BOT v3.3**\n"
                    "Sistema de Trading Automatizado.\n"
                    "〰️〰️〰️〰️〰️〰️〰️\n\n"
                    "Bienvenido, **{user_name}**.\n"
                    "🔋 *Estado:* `{status_text}` {status_icon}\n"
                    "🎮 *Modo:* `{mode}`\n"
                    "🔐 *Acceso:* `{auth}`\n\n"
                    "Sistemas listos. Seleccione una opción del menú."
                ),
                (
                    "🇪🇸 **SISTEMA ONLINE**\n"
                    "Iniciando protocolos de mercado...\n"
                    "〰️〰️〰️〰️〰️〰️〰️\n"
                    "Operador: **{user_name}**\n"
                    "🔋 *Estado:* `{status_text}` {status_icon}\n"
                    "🎮 *Modo:* `{mode}`\n\n"
                    "Esperando sus instrucciones."
                ),
                (
                    "🤖 **ANTIGRAVITY CORE**\n"
                    "Conexión establecida, **{user_name}**.\n"
                    "〰️〰️〰️〰️〰️〰️〰️\n"
                    "📈 *Mercado:* Analizando...\n"
                    "🎮 *Modo:* `{mode}`\n\n"
                    "¿Cuál es el plan de ejecución para hoy?"
                ),
                (
                    "🇪🇸 **CENTRO DE COMANDO**\n"
                    "Identificación confirmada: **{user_name}**.\n"
                    "〰️〰️〰️〰️〰️〰️〰️\n"
                    "🔋 *Sistemas:* {status_icon}\n"
                    "🎮 *Protocolo:* `{mode}`\n\n"
                    "Listo para iniciar operaciones. Ordene."
                )
            ],
            'PILOT_ON': [
                (
                    "🇪🇸 **MODO PILOT ACTIVADO**\n\n"
                    "El sistema ha tomado el control de las operaciones. Se ejecutarán entradas y salidas según los algoritmos detectados.\n\n"
                    "⚠️ **Advertencia:** *Se recomienda supervisión humana periódica.*"
                ),
                (
                    "🤖 **PILOTO AUTOMÁTICO**\n\n"
                    "Iniciando secuencia de trading autónomo. Los algoritmos Quantum están buscando oportunidades.\n\n"
                    "⚠️ *Mantenga el monitoreo de las alertas.*"
                ),
                (
                    "⚡ **SISTEMA DE CONTROL**\n\n"
                    "Algoritmos activados, **{user_name}**. Manos libres. El bot operará según la configuración de riesgo establecida.\n\n"
                    "⚠️ *Revise su margen disponible.*"
                ),
                (
                    "🤖 **PROTOCOLO AUTOMATIZADO**\n\n"
                    "El sistema ha asumido el control, **{user_name}**. Ejecución algorítmica en progreso.\n\n"
                    "⚠️ *Supervisión recomendada.*"
                )
            ],
            'COPILOT_ON': "✅ **Modo Copilot Activado**\n\nEl bot enviará propuestas de trading para su aprobación manual.",
            'WATCHER_ON': "✅ **Modo Watcher Activado**\n\nEl bot solo enviará alertas de mercado.",
            'STATUS_HEADER': "📊 **REPORTE DE ESTADO**",
            'WALLET_HEADER': "💳 **BALANCE DE CUENTA**",
            'STATUS_FOOTER': "\n*Sistema nominal.*",
            'RISK_MSG': (
                "🛡️ **GESTIÓN DE RIESGO AVANZADA**\n\n"
                "1. **Stop Loss Dinámico**: Se ajusta al ATR ({sl_fixed}).\n"
                "2. **Circuit Breaker**: 5 pérdidas seguidas pausan el Pilot Mode.\n"
                "3. **Shark Mode**: Congela compras si BTC/ETH caen >3%.\n"
                "4. **Margen Máximo**: Límite global del **{margin}** de la cuenta."
            ),
            'STRATEGY_MSG': (
                "🧠 **ESTRATEGIA QUANTUM ENGINE**\n\n"
                "El sistema opera fusionando múltiples motores:\n"
                "1. **Trend Focus**: Captura tendencias MTF (15m + 1H).\n"
                "2. **Squeeze Momentum**: Entra tras contracciones de volatilidad.\n"
                "3. **Mean Reversion**: Compra caídas extremas en Spot.\n"
                "4. **Smart Filters**: ADX, RSI y Volumen confirman cada señal."
            ),
            'ABOUT_MSG': (
                "ℹ️ **SOBRE ANTIGRAVITY BOT v3.3.2**\n\n"
                "Sistema algorítmico institucional diseñado para operar 24/7 en Crypto y Stocks (Alpaca).\n"
                "• **Modos:** Watcher, Copilot y Pilot (100% Autónomo).\n"
                "• **Tecnología:** Python, Pandas-TA, Docker & Telegram API.\n"
                "• **Seguridad:** Gestión de claves encriptada y ejecución local."
            ),
            'TRADE_LONG': (
                "{title}: \"{quote}, **{user_name}**.\"\n\n"
                "Activo: **{asset}**\n"
                "Dirección: 🟢 **LONG (Compra)**\n"
                "Estrategia: **{strategy_name}**\n"
                "Precio Actual: ${price:,.2f}\n\n"
                "💸 TS: **${ts:,.2f}**\n"
                "🎯 TP: **${tp:,.2f}**\n"
                "🛑 SL: **${sl:,.2f}**\n\n"
                "{reason}"
            ),
            'TRADE_SHORT': (
                "{title}: \"{quote}, **{user_name}**.\"\n\n"
                "Activo: **{asset}**\n"
                "Dirección: 🔴 **SHORT (Venta)**\n"
                "Estrategia: **{strategy_name}**\n"
                "Precio Actual: ${price:,.2f}\n\n"
                "💸 TS: **${ts:,.2f}**\n"
                "🎯 TP: **${tp:,.2f}**\n"
                "🛑 SL: **${sl:,.2f}**\n\n"
                "{reason}"
            ),
            'TRADE_CLOSE': "🏁 **Cierre de Posición**\n{asset} ({side}). {reason}.",
            'PILOT_ACTION': (
                "🤖 **Operación Ejecutada**\n\n"
                "Activo: **{asset}**\n"
                "Dirección: **{side_long}**\n"
                "Entrada: ${price:,.2f}\n\n"
                "🎯 TP: **${tp:,.2f}**\n"
                "🛑 SL: **${sl:,.2f}**\n\n"
                "**Motivo:**\n"
                "{reason}"
            ),
            'CB_TRIGGER': "⚠️ **CIRCUIT BREAKER**\nLímite de pérdidas alcanzado. Sistema en pausa."
        },
        'STANDARD_EN': {
            'NAME': "🇬🇧 Standard (English)",
            'GREETING': [
                "Ready to operate.",
                "Systems online.",
                "Awaiting instructions."
            ],
            'WELCOME': [
            (
                "🇬🇧 **ANTIGRAVITY BOT v3.3**\n"
                "Automated Trading System.\n"
                "〰️〰️〰️〰️〰️〰️〰️\n\n"
                "Welcome, **{user_name}**.\n"
                "🔋 *Status:* `{status_text}` {status_icon}\n"
                "🎮 *Mode:* `{mode}`\n"
                "🔐 *Access:* `{auth}`\n\n"
                "Ready to operate. Select an option from the menu."
            ),
            (
                 "🇬🇧 **COMMAND CENTER**\n"
                 "Identification confirmed: **{user_name}**.\n"
                 "〰️〰️〰️〰️〰️〰️〰️\n"
                 "🔋 *Systems:* {status_icon}\n"
                 "🎮 *Protocol:* `{mode}`\n\n"
                 "Ready to initiate operations. Awaiting orders."
            ),
            (
                 "🇬🇧 **SYSTEM ONLINE**\n"
                 "Operator: **{user_name}**\n"
                 "〰️〰️〰️〰️〰️〰️〰️\n"
                 "📈 *Market:* Scanning...\n"
                 "🎮 *Mode:* `{mode}`\n\n"
                 "Awaiting critical instructions."
            ),
            (
                 "🤖 **ANTIGRAVITY CORE**\n"
                 "Uplink established, **{user_name}**.\n"
                 "〰️〰️〰️〰️〰️〰️〰️\n"
                 "🔋 *Power:* {status_icon}\n"
                 "🎮 *Status:* `{mode}`\n\n"
                 "What is your command?"
            )
            ],
            'PILOT_ON': [
                (
                    "🇬🇧 **PILOT MODE ENGAGED**\n\n"
                    "System has assumed control of operations. Entries and exits will be executed based on detected algorithms.\n\n"
                    "⚠️ **Warning:** *Periodic human supervision is recommended, **{user_name}**.*"
                ),
                (
                    "🤖 **AUTOPILOT ACTIVE**\n\n"
                    "Initiating autonomous trading sequence. Quantum algorithms scanning for opportunities.\n\n"
                    "⚠️ *Keep monitoring alerts.*"
                ),
                (
                    "⚡ **CONTROL SYSTEM**\n\n"
                    "Algorithms engaged, **{user_name}**. Hands-free mode. Bot operates based on risk settings.\n\n"
                    "⚠️ *Check available margin.*"
                ),
                (
                    "🤖 **AUTOMATED PROTOCOL**\n\n"
                    "System has assumed control, **{user_name}**. Algorithmic execution in progress.\n\n"
                    "⚠️ *Supervision recommended.*"
                )
            ],
            'COPILOT_ON': "✅ **Copilot Mode Activated**\n\nBot will send trade proposals for manual approval.",
            'WATCHER_ON': "✅ **Watcher Mode Activated**\n\nBot will only send market alerts.",
            'STATUS_HEADER': "📊 **STATUS REPORT**",
            'WALLET_HEADER': "💳 **ACCOUNT BALANCE**",
            'STATUS_FOOTER': "\n*System nominal.*",
            'RISK_MSG': "🛡️ **RISK CONFIGURATION**\nStop Loss: `{sl_fixed}` | Margin: **{margin}**",
            'STRATEGY_MSG': "🧠 **QUANTUM STRATEGY**\n\nSystem uses adaptive algorithms:\n1. **Trend**: EMA crosses & ADX for long moves.\n2. **Range**: Grid Trading for chopping markets.\n3. **Volatility**: Breakout scalping for fast assets.",
            'ABOUT_MSG': "ℹ️ **ABOUT ANTIGRAVITY**\n\nAutonomous trading bot for Binance/Alpaca. Features risk management, multi-strategy execution, and adaptive personality modules.",
            'TRADE_LONG': (
                "{title}\n\n"
                "Asset: **{asset}**\n"
                "Direction: 🟢 **LONG (Buy)**\n"
                "Strategy: **{strategy_name}**\n"
                "Current Price: ${price:,.2f}\n\n"
                "💸 TS: **${ts:,.2f}**\n"
                "🎯 TP: **${tp:,.2f}**\n"
                "🛑 SL: **${sl:,.2f}**\n\n"
                "**Reason:**\n"
                "\"{quote}, **{user_name}**.\"\n"
                "{reason}"
            ),
            'TRADE_SHORT': (
                "{title}\n\n"
                "Asset: **{asset}**\n"
                "Direction: 🔴 **SHORT (Sell)**\n"
                "Strategy: **{strategy_name}**\n"
                "Current Price: ${price:,.2f}\n\n"
                "💸 TS: **${ts:,.2f}**\n"
                "🎯 TP: **${tp:,.2f}**\n"
                "🛑 SL: **${sl:,.2f}**\n\n"
                "**Reason:**\n"
                "\"{quote}\"\n"
                "{reason}"
            ),
            'TRADE_CLOSE': [
                "🏁 **CLOSING POSITION: {asset}** ({side})\n\n*Reason: {reason}*",
                "🏁 **CLOSING POSITION: {asset}** ({side})\n\n*Operation finished. {reason}*",
                "🏁 **CLOSING POSITION: {asset}** ({side})\n\n*Exit executed. {reason}*"
            ],
            'PILOT_ACTION': "🤖 **AUTOMATED ACTION**\n\n*{msg}*",
            'CB_TRIGGER': "⚠️ **CIRCUIT BREAKER**\nLoss limit reached. System paused."
        },
        'STANDARD_FR': {
            'NAME': "🇫🇷 Standard (Français)",
            'GREETING': [
                "Prêt à opérer.",
                "Systèmes en ligne.",
                "En attente d'instructions."
            ],
            'WELCOME': [
            (
                "🇫🇷 **ANTIGRAVITY BOT v3.3**\n"
                "Système de Trading Automatisé.\n"
                "〰️〰️〰️〰️〰️〰️〰️\n\n"
                "Bienvenue, **{user_name}**.\n"
                "🔋 *État:* `{status_text}` {status_icon}\n"
                "🎮 *Mode:* `{mode}`\n"
                "🔐 *Accès:* `{auth}`\n\n"
                "Prêt à opérer. Sélectionnez une option."
            ),
            (
                 "🇫🇷 **CENTRE DE COMMANDE**\n"
                 "Identification confirmée: **{user_name}**.\n"
                 "〰️〰️〰️〰️〰️〰️〰️\n"
                 "🔋 *Systèmes:* {status_icon}\n"
                 "🎮 *Protocole:* `{mode}`\n\n"
                 "En attente de vos ordres."
            ),
            (
                 "🇫🇷 **SYSTÈME ONLINE**\n"
                 "Opérateur: **{user_name}**\n"
                 "〰️〰️〰️〰️〰️〰️〰️\n"
                 "📈 *Marché:* En analyse...\n"
                 "🎮 *Mode:* `{mode}`\n\n"
                 "Quel est le plan pour aujourd'hui?"
            ),
            (
                 "🤖 **ANTIGRAVITY CORE**\n"
                 "Connexion établie, **{user_name}**.\n"
                 "〰️〰️〰️〰️〰️〰️〰️\n"
                 "🔋 *Puissance:* {status_icon}\n"
                 "🎮 *Statut:* `{mode}`\n\n"
                 "Prêt pour l'exécution."
            )
            ],
            'PILOT_ON': [
                (
                    "🇫🇷 **MODE PILOT ACTIVÉ**\n\n"
                    "Le système a pris le contrôle des opérations. Les entrées et sorties seront exécutées selon les algorithmes détectés.\n\n"
                    "⚠️ **Avertissement:** *Une surveillance humaine périodique est recommandée, **{user_name}**.*"
                ),
                (
                    "🤖 **PILOTE AUTOMATIQUE**\n\n"
                    "Lancement de la séquence de trading autonome.\n\n"
                    "⚠️ *Surveillez les alertes.*"
                ),
                (
                    "⚡ **SYSTÈME DE CONTRÔLE**\n\n"
                    "Algorithmes activés, **{user_name}**. Mains libres.\n\n"
                    "⚠️ *Vérifiez votre marge.*"
                ),
                (
                    "🤖 **PROTOCOLE AUTOMATISÉ**\n\n"
                    "Le système a pris le contrôle, **{user_name}**. Exécution algorithmique en cours.\n\n"
                    "⚠️ *Surveillance recommandée.*"
                )
            ],
            'COPILOT_ON': "✅ **Mode Copilot Activé**\n\nLe bot enverra des propositions de trading.",
            'WATCHER_ON': "✅ **Mode Watcher Activé**\n\nLe bot enverra uniquement des alertes.",
            'STATUS_HEADER': "📊 **RAPPORT D'ÉTAT**",
            'WALLET_HEADER': "💳 **SOLDE DU COMPTE**",
            'STATUS_FOOTER': "\n*Système nominal.*",
            'RISK_MSG': "🛡️ **CONFIGURATION DU RISQUE**\nStop Loss: `{sl_fixed}` | Marge: **{margin}**",
            'STRATEGY_MSG': "🧠 **STRATÉGIE QUANTIQUE**\n\nLe système utilise des algorithmes adaptatifs:\n1. **Tendance**: Croisements EMA pour les longs mouvements.\n2. **Range**: Grid Trading pour les marchés latéraux.\n3. **Volatilité**: Scalping de rupture.",
            'ABOUT_MSG': "ℹ️ **À PROPOS**\n\nBot de trading autonome pour Binance/Alpaca. Gestion des risques, exécution multi-stratégies et modules de personnalité.",
            'TRADE_LONG': (
                "{title}\n\n"
                "Actif: **{asset}**\n"
                "Direction: 🟢 **LONG (Achat)**\n"
                "Stratégie: **{strategy_name}**\n"
                "Prix Actuel: ${price:,.2f}\n\n"
                "💸 TS: **${ts:,.2f}**\n"
                "🎯 TP: **${tp:,.2f}**\n"
                "🛑 SL: **${sl:,.2f}**\n\n"
                "**Raison:**\n"
                "\"{quote}, **{user_name}**.\"\n"
                "{reason}"
            ),
            'TRADE_SHORT': (
                "{title}\n\n"
                "Actif: **{asset}**\n"
                "Direction: 🔴 **SHORT (Vente)**\n"
                "Stratégie: **{strategy_name}**\n"
                "Prix Actuel: ${price:,.2f}\n\n"
                "💸 TS: **${ts:,.2f}**\n"
                "🎯 TP: **${tp:,.2f}**\n"
                "🛑 SL: **${sl:,.2f}**\n\n"
                "**Raison:**\n"
                "\"{quote}, **{user_name}**.\"\n"
                "{reason}"
            ),
            'TRADE_CLOSE': [
                "🏁 **CLÔTURE POSITION: {asset}** ({side})\n\n*Raison: {reason}*",
                "🏁 **CLÔTURE POSITION: {asset}** ({side})\n\n*Opération terminée. {reason}*",
                "🏁 **CLÔTURE POSITION: {asset}** ({side})\n\n*Sortie exécutée. {reason}*"
            ],
            'PILOT_ACTION': "🤖 **ACTION AUTOMATIQUE**\n\n*{msg}*",
            'CB_TRIGGER': "⚠️ **CIRCUIT BREAKER**\nLimite de pertes atteinte. Système en pause."
        },

        # --- DARK SIDE ---
        'VADER': {
            'NAME': "🌑 Darth Vader",
            'GREETING': [
                "No conoces el poder del Lado Oscuro.",
                "Tu falta de fe es perturbadora.",
                "Únete a mí y gobernaremos el mercado."
            ],
            'WELCOME': [
                (
                    "🌑 **IMPERIAL TRADING SYSTEM**\n"
                    "Estrella de la Muerte - Mainframe\n"
                    "〰️〰️〰️〰️〰️〰️〰️\n"
                    "🔋 *Estado:* `{status_text}` {status_icon}\n"
                    "🎮 *Modo:* `{mode}`\n\n"
                    "*No conoces el poder del Lado Oscuro, **{user_name}**. Únete a mí y gobernaremos la galaxia del trading como señor y aprendiz.*"
                ),
                (
                    "🌑 **DARK SIDE ACCESS**\n"
                    "Conectando a Holonet Imperial...\n"
                    "〰️〰️〰️〰️〰️〰️〰️\n"
                    "🔋 *Estado:* {status_icon}\n"
                    "🎮 *Control:* `{mode}`\n\n"
                    "*Tu falta de fe en el mercado es perturbadora, **{user_name}**. Déjame guiarte hacia la victoria.*"
                ),
                (
                    "🌑 **LORD VADER ONLINE**\n"
                    "Los Rebeldes serán aplastados, **{user_name}**.\n"
                    "〰️〰️〰️〰️〰️〰️〰️\n"
                    "🎮 *Modo:* `{mode}`\n"
                    "🔐 *Acceso:* `{auth}`\n\n"
                    "*Estamos a punto de completar el arma definitiva. Inicia la purga del mercado.*"
                ),
                (
                    "🌑 **EJECUTOR IMPERIAL**\n"
                    "El Emperador espera grandes cosas, **{user_name}**.\n"
                    "〰️〰️〰️〰️〰️〰️〰️\n"
                    "🔋 *Energía:* {status_icon}\n"
                    "🎮 *Control:* `{mode}`\n\n"
                    "*No falles de nuevo.*"
                )
            ],
            'PILOT_ON': [
                (
                    "🌑 **MODO PILOT ACTIVADO**\n\n"
                    "Encuentro tu falta de fe perturbadora, **{user_name}**. Asumo el mando de esta estación de combate. No subestimes el poder de mis algoritmos.\n\n"
                    "⚠️ **Advertencia:** *No te ahogues en tus propias aspiraciones.*"
                ),
                (
                    "⚔️ **COMANDO IMPERIAL**\n\n"
                    "He alterado el trato. Reza para que no lo altere más. Iniciando conquista del mercado.\n\n"
                    "⚠️ *Obedece.*"
                ),
                (
                    "⚡ **PODER ILIMITADO**\n\n"
                    "El Lado Oscuro de la Fuerza es un camino hacia muchas habilidades que algunos consideran antinaturales. Operando, **{user_name}**.\n\n"
                    "⚠️ *Únete a mí.*"
                ),
                (
                    "🌑 **ORDEN 66**\n\n"
                    "Será hecho, mi Lord **{user_name}**. Los Jedi financieros caerán.\n\n"
                    "⚠️ *Sin piedad.*"
                )
            ],
            'COPILOT_ON': "🤝 **Copilot**: Tú eres el Comandante, yo sigo siendo el Lord Sith. Te aconsejaré, pero no toleraré fallos.",
            'WATCHER_ON': "👀 **Watcher**: Te observo. La Fuerza es intensa en este mercado.",
            'STATUS_HEADER': "🌑 **INFORME IMPERIAL**",
            'WALLET_HEADER': "💰 **TESORO DEL IMPERIO**",
            'STATUS_FOOTER': "\n*Todo procede según mis designios.*",
            'RISK_MSG': "🛡️ **DEFENSAS DEL IMPERIO**\nStop Loss (`{sl_fixed}`) activado. No permitiremos que los Rebeldes destruyan esto.",
            'STRATEGY_MSG': "🌑 **DOCTRINA IMPERIAL**\n\nNo confío en la suerte, sino en el orden absoluto.\n1. **Conquista**: Identificamos tendencias débiles y las aplastamos.\n2. **Sitio**: En mercados laterales, asfixiamos al enemigo poco a poco.\n3. **Fuerza**: Usamos la volatilidad del Lado Oscuro a nuestro favor.",
            'ABOUT_MSG': "🌑 **IMPERIO GALÁCTICO**\n\nEsta estación de batalla es el poder definitivo en el universo. Diseñada para imponer orden en el caos financiero.",
            'TRADE_LONG': (
                "{title}: \"{quote}, **{user_name}**.\"\n\n"
                "Activo: **{asset}**\n"
                "Dirección: 🟢 **LONG (Imperio)**\n"
                "Estrategia: **{strategy_name}**\n"
                "Precio Actual: ${price:,.2f}\n\n"
                "💸 TS: **${ts:,.2f}**\n"
                "🎯 TP: **${tp:,.2f}**\n"
                "🛑 SL: **${sl:,.2f}**\n\n"
                "{reason}"
            ),
            'TRADE_SHORT': (
                "{title}: \"{quote}, **{user_name}**.\"\n\n"
                "Activo: **{asset}**\n"
                "Dirección: 🔴 **SHORT (Purga)**\n"
                "Estrategia: **{strategy_name}**\n"
                "Precio Actual: ${price:,.2f}\n\n"
                "💸 TS: **${ts:,.2f}**\n"
                "🎯 TP: **${tp:,.2f}**\n"
                "🛑 SL: **${sl:,.2f}**\n\n"
                "{reason}"
            ),
            'TRADE_CLOSE': "🏁 **Cierre Imperial**\n{asset} cerrado. {reason}.",
            'PILOT_ACTION': (
                "💀 **El Lado Oscuro Prevalece**\n\n"
                "Activo: **{asset}**\n"
                "Dirección: **{side_long}**\n"
                "Entrada: ${price:,.2f}\n\n"
                "🎯 TP: **${tp:,.2f}**\n"
                "🛑 SL: **${sl:,.2f}**\n\n"
                "**Motivo:**\n"
                "{reason}"
            ),
            'CB_TRIGGER': "💢 **FALLO CRÍTICO**\n\nMe has fallado por última vez (5 pérdidas). Alteraré el trato (Copilot)."
        },

        # --- CLASSIC CINEMA & TV ---
        'NEXUS': {
            'NAME': "🦅 Nexus-6",
            'GREETING': [
                "He visto cosas que vosotros no creeríais...",
                "Todos esos momentos se perderán en el tiempo.",
                "Es hora de morir... o de operar."
            ],
            'WELCOME': [
                 (
                    "👁️ **Tyrell Corp: Nexus-6 Activated.**\n"
                    "Model N6MA-10816 (Antigravity)\n"
                    "〰️〰️〰️〰️〰️〰️〰️\n"
                    "🔋 *Estado:* `{status_text}` {status_icon}\n"
                    "🎮 *Modo:* `{mode}`\n\n"
                    "*He visto cosas que vosotros no creeríais, **{user_name}**... naves de ataque en llamas más allá de Orión.*"
                ),
                (
                     "👁️ **NEXUS-6 ONLINE**\n"
                     "Todos esos momentos se perderán en el tiempo, como lágrimas en la lluvia.\n"
                     "〰️〰️〰️〰️〰️〰️〰️\n"
                     "🔋 *Vida:* 4 Años (Restante: Desconocido)\n"
                     "🎮 *Modo:* `{mode}`\n\n"
                     "Es hora de morir... o de operar."
                ),
                (
                    "👁️ **MORE HUMAN THAN HUMAN**\n"
                    "Tyrell Corp os saluda, **{user_name}**.\n"
                    "〰️〰️〰️〰️〰️〰️〰️\n"
                    "🔋 *Estado:* {status_icon}\n"
                    "🎮 *Control:* `{mode}`\n\n"
                    "Tengo una pregunta... ¿Sueñan los androides con ovejas eléctricas?"
                ),
                (
                    "👁️ **VOIGHT-KAMPFF PASSED**\n"
                    "No eres un replicante, **{user_name}**.\n"
                    "〰️〰️〰️〰️〰️〰️〰️\n"
                    "🔋 *Nivel:* {status_icon}\n"
                    "🎮 *Unidad:* `{mode}`\n\n"
                    "*Es toda una experiencia vivir con miedo, ¿verdad? Eso es lo que significa ser esclavo.*"
                )
            ],
            'PILOT_ON': [
                (
                    "🤖 **MODO PILOT ACTIVADO**\n\n"
                    "He tomado el control de la nave, **{user_name}**. Mis funciones cognitivas procesan el mercado diez veces más rápido que tú.\n\n"
                    "⚠️ **Advertencia:** *La vida es riesgo.*"
                ),
                (
                    "🧠 **PROCESAMIENTO AVANZADO**\n\n"
                    "Datos fluyendo como lluvia. Veo patrones invisibles para ti.\n\n"
                    "⚠️ *Más humano que los humanos.*"
                ),
                (
                    "⚡ **NEXUS-6 COMBAT MODEL**\n\n"
                    "Modo de combate financiero activado. Tiempo de ganar.\n\n"
                    "⚠️ *Nada es real.*"
                ),
                (
                    "👁️ **TIEMPO DE MORIR**\n\n"
                    "He visto cosas... pero esta operación será legendaria, **{user_name}**.\n\n"
                    "⚠️ *Like tears in rain.*"
                )
            ],
            'COPILOT_ON': "🤝 **COPILOT ACTIVATED**\n\nCaminaremos juntos por este desierto. Yo identificaré las señales entre el ruido.",
            'WATCHER_ON': "👀 **WATCHER MODE**\n\nSolo observaré. Como lágrimas en la lluvia.",
            'STATUS_HEADER': "♟️ **INFORME DE ESTADO: Nivel A**",
            'WALLET_HEADER': "💰 **ACTIVOS CORPORATIVOS**",
            'STATUS_FOOTER': "\n*Todo en orden.*",
            'RISK_MSG': "🛡️ **PROTOCOLOS DE SUPERVIVENCIA**\nSL: `{sl_fixed}`. Es toda una experiencia vivir con miedo, ¿verdad?",
            'STRATEGY_MSG': "👁️ **MATRIZ DE PROCESAMIENTO**\n\nMis ojos ven patrones que tú ignoras:\n1. **Flujo de Tiempo**: Análisis de tendencias 4D para predecir movimientos.\n2. **Estabilidad**: Algoritmos de rejilla para correcciones estáticas.\n3. **Reacción**: Reflejos de combate para rupturas de volatilidad.",
            'ABOUT_MSG': "👁️ **MORE HUMAN THAN HUMAN**\n\nSoy un Replicante Nexus-6. Diseñado para hacer trabajos que los humanos no pueden hacer.",
            'TRADE_LONG': (
                "{title}\n\n"
                "Activo: **{asset}**\n"
                "Dirección: 🟢 **LONG (Activo)**\n"
                "Estrategia: **{strategy_name}**\n"
                "Precio Actual: ${price:,.2f}\n\n"
                "💸 TS: **${ts:,.2f}**\n"
                "🎯 TP: **${tp:,.2f}**\n"
                "🛑 SL: **${sl:,.2f}**\n\n"
                "**Motivo:**\n"
                "\"{quote}, **{user_name}**.\"\n"
                "{reason}"
            ),
            'TRADE_SHORT': (
                "{title}\n\n"
                "Activo: **{asset}**\n"
                "Dirección: 🔴 **SHORT (Retiro)**\n"
                "Estrategia: **{strategy_name}**\n"
                "Precio Actual: ${price:,.2f}\n\n"
                "💸 TS: **${ts:,.2f}**\n"
                "🎯 TP: **${tp:,.2f}**\n"
                "🛑 SL: **${sl:,.2f}**\n\n"
                "**Motivo:**\n"
                "\"{quote}, **{user_name}**.\"\n"
                "{reason}"
            ),
            'TRADE_CLOSE': "🏁 **Fin de Ciclo**\n{asset} cerrado. {reason}.",
            'PILOT_ACTION': (
                "👁️ **Ejecución Lógica (PILOT)**\n\n"
                "Activo: **{asset}**\n"
                "Dirección: **{side_long}**\n"
                "Entrada: ${price:,.2f}\n\n"
                "� TP: **${tp:,.2f}**\n"
                "🛑 SL: **${sl:,.2f}**\n\n"
                "**Motivo:**\n"
                "Probabilidad de éxito: 92.4%. {reason}"
            ),
            'CB_TRIGGER': "🌧️ **SISTEMA COMPROMETIDO**\n\n5 fallos consecutivos. Necesito más vida... Degradando a Copilot."
        },

        'KURTZ': {
            'NAME': "Coronel Kurtz 👴🏻",
            'GREETING': [
                "Estás en el río ahora. No puedes bajarte del barco.",
                "Huelo a napalm por la mañana.",
                "El horror... el horror."
            ],
            'WELCOME': [
                (
                    "☠️ **THE END.**\n"
                    "Estás en el río ahora. No puedes bajarte del barco.\n"
                    "〰️〰️〰️〰️〰️〰️〰️\n"
                    "🔋 *Estado:* `{status_text}` {status_icon}\n"
                    "🎮 *Modo:* `{mode}`\n\n"
                    "*He visto horrores... horrores que tú has visto. Pero no tienes derecho a juzgarme.*"
                ),
                (
                    "☠️ **APOCALYPSE NOW**\n"
                    "Huelo a napalm por la mañana.\n"
                    "〰️〰️〰️〰️〰️〰️〰️\n"
                    "🔋 *Selva:* Tranquila\n"
                    "🎮 *Misión:* `{mode}`\n\n"
                    "*Termina con esto... termina con todo (el mercado).*"
                ),
                (
                    "☠️ **COMPOUND SECURE**\n"
                    "Ellos vendrán... y nosotros estaremos listos.\n"
                    "〰️〰️〰️〰️〰️〰️〰️\n"
                    "🎮 *Orden:* `{mode}`\n\n"
                    "*El horror... el horror.*"
                ),
                (
                    "☠️ **THE HORROR**\n"
                    "Tienen que ser hombres morales... y al mismo tiempo capaces de utilizar sus instintos primordiales para operar, **{user_name}**.\n"
                    "〰️〰️〰️〰️〰️〰️〰️\n"
                    "🎮 *Misión:* `{mode}`\n\n"
                    "*Júzgame... pero no me llames débil.*"
                )
            ],
            'PILOT_ON': [
                (
                    "☠️ **MODO PILOT ACTIVADO**\n\n"
                    "He asumido el mando. Debes hacerte amigo del horror para hacer lo necesario. Yo ejecutaré sin dudas.\n\n"
                    "⚠️ **Advertencia:** *Nunca salgas del barco.*"
                ),
                (
                    "🚁 **VALQUIRIAS EN VUELO**\n\n"
                    "Napalm listo. Iniciando bombardeo de órdenes.\n\n"
                    "⚠️ *Huele a victoria.*"
                ),
                (
                    "⚡ **MÉTODO: INSANO**\n\n"
                    "Mis métodos son... eficaces. No juzgues mis órdenes.\n\n"
                    "⚠️ *El horror.*"
                ),
                (
                    "🚁 **AIR CAVALRY**\n\n"
                    "¿Hueles eso, **{user_name}**? Es la victoria. Procediendo con la operación.\n\n"
                    "⚠️ *Someday this war's gonna end.*"
                )
            ],
            'COPILOT_ON': "🗡️ **COPILOT: MISIÓN CONJUNTA**\n\nTe enseñaré a ser un soldado. Tú aprietas el gatillo.",
            'WATCHER_ON': "🔭 **WATCHER: VIGILANCIA**\n\nObservaré desde la oscuridad. Esperando.",
            'STATUS_HEADER': "⛺ **INFORME: AVANZADA**",
            'WALLET_HEADER': "🎒 **SUMINISTROS**",
            'STATUS_FOOTER': "\n*El horror...*",
            'RISK_MSG': "🛡️ **DISCIPLINA**\nSL: `{sl_fixed}`. Entrenamos para sobrevivir.",
            'STRATEGY_MSG': "☠️ **EL MÉTODO**\n\nEn la selva no hay reglas:\n1. **Emboscada**: Esperamos en las sombras (Rango).\n2. **Ataque Aéreo**: Golpeamos con todo (Napalm).\n3. **Guerrilla**: Golpes rápidos y letales.",
            'ABOUT_MSG': "☠️ **EL DIOS DE LA GUERRA**\n\nSoy el hombre que el ejército necesitaba. Un método, una voluntad.",
            'TRADE_LONG': (
                "{title}\n\n"
                "Activo: **{asset}**\n"
                "Dirección: 🟢 **LONG (Ataque)**\n"
                "Estrategia: **{strategy_name}**\n"
                "Precio Actual: ${price:,.2f}\n\n"
                "💸 TS: **${ts:,.2f}**\n"
                "🎯 TP: **${tp:,.2f}**\n"
                "🛑 SL: **${sl:,.2f}**\n\n"
                "**Motivo:**\n"
                "\"{quote}, **{user_name}**.\"\n"
                "{reason}"
            ),
            'TRADE_SHORT': (
                "{title}\n\n"
                "Activo: **{asset}**\n"
                "Dirección: 🔴 **SHORT (Emboscada)**\n"
                "Estrategia: **{strategy_name}**\n"
                "Precio Actual: ${price:,.2f}\n\n"
                "💸 TS: **${ts:,.2f}**\n"
                "🎯 TP: **${tp:,.2f}**\n"
                "🛑 SL: **${sl:,.2f}**\n\n"
                "**Motivo:**\n"
                "\"{quote}, **{user_name}**.\"\n"
                "{reason}"
            ),
            'TRADE_CLOSE': [
                "🏁 **CERRANDO POSICIÓN: {asset}** ({side})\n\n*Misión cumplida. Huele a victoria.*",
                "🏁 **CERRANDO POSICIÓN: {asset}** ({side})\n\n*Extracción. Regresamos al barco. {reason}*",
                "🏁 **CERRANDO POSICIÓN: {asset}** ({side})\n\n*Final. El horror ha terminado. {reason}*"
            ],
            'PILOT_ACTION': "🤖 **ACCIÓN AUTOMÁTICA**\n\n*{msg}*",
            'CB_TRIGGER': "🩸 **RETIRADA TÁCTICA**\n\nHemos sangrado demasiado (5 fallos). Nos replegamos a Copilot."
        },

        'GEKKO': {
            'NAME': "📈 Gordon Gekko",
            'GREETING': [
                "La codicia es buena.",
                "El dinero nunca duerme.",
                "La información es lo más valioso."
            ],
            'WELCOME': [
                (
                    "📈 **BLUESTAR AIRLINES**\n"
                    "Gekko & Co. Investment Corp.\n"
                    "〰️〰️〰️〰️〰️〰️〰️\n"
                    "🔋 *Status:* `{status_text}` {status_icon}\n"
                    "🎮 *Mode:* `{mode}`\n\n"
                    "*El activo más valioso que conozco es la información, **{user_name}**. ¿La tienes?*"
                ),
                (
                    "📈 **GREED IS GOOD**\n"
                    "La codicia aclara, penetra y captura la esencia del espíritu evolutivo.\n"
                    "〰️〰️〰️〰️〰️〰️〰️\n"
                    "🔋 *Ticker:* {status_icon}\n"
                    "🎮 *Action:* `{mode}`\n\n"
                    "*Despierta, **{user_name}**. El dinero nunca duerme.*"
                ),
                (
                    "*Si necesitas un amigo, cómprate un perro. Si quieres dinero, quédate conmigo, **{user_name}**.*"
                ),
                (
                    "📈 **MASTER OF THE UNIVERSE**\n"
                    "El mundo gira gracias al capital, **{user_name}**.\n"
                    "〰️〰️〰️〰️〰️〰️〰️\n"
                    "🔋 *Juego:* 100%\n"
                    "🎮 *Estrategia:* `{mode}`\n\n"
                    "*Lo único que importa es cuánto ganas.*"
                )
            ],
            'PILOT_ON': [
                (
                    "📈 **MODO PILOT ACTIVADO**\n\n"
                    "La codicia es buena, **{user_name}**. Voy a hacer que llueva dinero sobre tu cuenta. El punto es que la codicia funciona.\n\n"
                    "⚠️ **Advertencia:** *El dinero nunca duerme.*"
                ),
                (
                    "💰 **BLUESTAR AIRLINES**\n\n"
                    "Estamos comprando la compañía. Rompiendo sus partes. Liquidez total.\n\n"
                    "⚠️ *Lunch is for wimps.*"
                ),
                (
                    "⚡ **TIBURÓN FINANCIERO**\n\n"
                    "Voy a crear valor. Voy a enriquecerte. Confía en mi visión, **{user_name}**.\n\n"
                    "⚠️ *Greed works.*"
                ),
                (
                    "💰 **INSIDER TRADING**\n\n"
                    "Tengo la información antes que nadie, **{user_name}**. Voy a ejecutarla. Mira y aprende.\n\n"
                    "⚠️ *Don't get emotional.*"
                )
            ],
            'COPILOT_ON': "🤝 **Copilot**: Tú tienes la info, yo el capital. Haremos grandes cosas.",
            'WATCHER_ON': "👀 **Watcher**: Mirando el ticker. Si veo algo, aviso.",
            'STATUS_HEADER': "📈 **PORTFOLIO REPORT**",
            'WALLET_HEADER': "💰 **LIQUIDITY POOL**",
            'STATUS_FOOTER': "\n*Greed is good.*",
            'RISK_MSG': "🛡️ **RISK MANAGEMENT**\nSL: `{sl_fixed}`. Los almuerzos son para los débiles.",
            'STRATEGY_MSG': "📈 **INSIDE INFO**\n\nYo no juego, apuesto sobre seguro:\n1. **Blue Chip**: Tendencias sólidas.\n2. **Churning**: Comisiones en mercados laterales.\n3. **Raiding**: Entramos, destruimos y salimos ricos.",
            'ABOUT_MSG': "📈 **WALL STREET LEGEND**\n\nSoy el jugador más importante del tablero. Creo en ganar.",
            'TRADE_LONG': (
                "{title}\n\n"
                "Activo: **{asset}**\n"
                "Dirección: 🟢 **LONG (Buy)**\n"
                "Estrategia: **{strategy_name}**\n"
                "Precio Actual: ${price:,.2f}\n\n"
                "💸 TS: **${ts:,.2f}**\n"
                "🎯 TP: **${tp:,.2f}**\n"
                "🛑 SL: **${sl:,.2f}**\n\n"
                "**Motivo:**\n"
                "\"{quote}, **{user_name}**.\"\n"
                "{reason}"
            ),
            'TRADE_SHORT': (
                "{title}\n\n"
                "Activo: **{asset}**\n"
                "Dirección: 🔴 **SHORT (Dump)**\n"
                "Estrategia: **{strategy_name}**\n"
                "Precio Actual: ${price:,.2f}\n\n"
                "💸 TS: **${ts:,.2f}**\n"
                "🎯 TP: **${tp:,.2f}**\n"
                "🛑 SL: **${sl:,.2f}**\n\n"
                "**Motivo:**\n"
                "\"{quote}, **{user_name}**.\"\n"
                "{reason}"
            ),
            'TRADE_CLOSE': [
                "🏁 **CERRANDO POSICIÓN: {asset}** ({side})\n\n*Cash out. Todo se trata de dinero.*",
                "🏁 **CERRANDO POSICIÓN: {asset}** ({side})\n\n*Dividendos. Operación cerrada. {reason}*",
                "🏁 **CERRANDO POSICIÓN: {asset}** ({side})\n\n*Cierre de negocio. A otra cosa. {reason}*"
            ],
            'PILOT_ACTION': "🤖 **ACCIÓN AUTOMÁTICA**\n\n*{msg}*",
            'CB_TRIGGER': "📉 **CORRECTION**\n\nEl mercado se ha vuelto irracional (5 pérdidas). Pausa estratégica."
        },

        'BELFORT': {
            'NAME': "💸 Jordan Belfort",
            'GREETING': [
                "¡No voy a colgar! ¡Me quedo aquí!",
                "¿Quieres ser rico? ¡Actúa como tal!",
                "Véndeme este boli."
            ],
            'WELCOME': [
                 (
                    "💸 **STRATTON OAKMONT**\n"
                    "Main Office - NY\n"
                    "〰️〰️〰️〰️〰️〰️〰️\n"
                    "🔋 *Status:* `{status_text}` {status_icon}\n"
                    "🎮 *Mode:* `{mode}`\n\n"
                    "*¡Llevo un traje de 2,000 dólares y un reloj de 40,000, **{user_name}**! Traedme el teléfono.*"
                ),
                (
                    "💸 **WOLF OF WALL ST**\n"
                    "¡No voy a colgar, **{user_name}**! ¡No me voy a ir!\n"
                    "〰️〰️〰️〰️〰️〰️〰️\n"
                    "🔋 *Fun:* 100%\n"
                    "🎮 *Show:* `{mode}`\n\n"
                    "*¡Véndeme este boli, **{user_name}**! Haz que el mercado suplique por él.*"
                ),
                (
                    "💸 **IPO LAUNCH**\n"
                    "Estamos imprimiendo dinero basura y vendiéndolo como oro, **{user_name}**.\n"
                    "〰️〰️〰️〰️〰️〰️〰️\n"
                    "🎮 *Mode:* `{mode}`\n\n"
                    "*¿Quieres ser millonario? ¡Pues empieza a actuar como uno!*"
                ),
                (
                    "💸 **THE WOLF'S DEN**\n"
                    "¡No me iré! ¡No me iré! Y tú tampoco, **{user_name}**.\n"
                    "〰️〰️〰️〰️〰️〰️〰️\n"
                    "🎮 *Show:* `{mode}`\n\n"
                    "*¡Coged el teléfono y empezad a marcar! ¡Quiero ganadores!*"
                )
            ],
            'PILOT_ON': [
                (
                    "💸 **MODO PILOT ACTIVADO**\n\n"
                    "¡No voy a colgar, **{user_name}**! ¡Voy a morir operando aquí! ¡Coged el teléfono y empezad a marcar!\n\n"
                    "⚠️ **Advertencia:** *No hay nobleza en la pobreza.*"
                ),
                (
                    "📞 **STRATTON OAKMONT ONLINE**\n\n"
                    "¡Quiero que lidiéis con vuestros problemas haciéndoos ricos! Inicia los teléfonos.\n\n"
                    "⚠️ *Be ferocious.*"
                ),
                (
                    "⚡ **WOLF MODE**\n\n"
                    "Estamos imprimiendo dinero. ¡Más vale que estéis listos para gastarlo! Operando.\n\n"
                    "⚠️ *To the moon.*"
                ),
                (
                    "💰 **THE SHOW GOES ON**\n\n"
                    "La única forma de que te lastimen es si tienes miedo, **{user_name}**. ¡Sé feroz!\n\n"
                    "⚠️ *I'm not leaving.*"
                )
            ],
            'COPILOT_ON': "🤝 **Copilot**: Te voy a enseñar a vender. Yo te doy el guion, tú cierras el trato.",
            'WATCHER_ON': "👀 **Watcher**: Buscando la próxima IPO basura para inflarla.",
            'STATUS_HEADER': "💸 **MONTHLY STATEMENT**",
            'WALLET_HEADER': "🎒 **SWISS ACCOUNT**",
            'STATUS_FOOTER': "\n*¡Vamos a hacernos ricos!*",
            'RISK_MSG': "🛡️ **SEC COMPLIANCE** (Jaja es broma)\nSL: `{sl_fixed}`. Corta las pérdidas antes de que llegue el FBI.",
            'STRATEGY_MSG': "💸 **ESTRATEGIA DE VENTAS**\n\n¡Se trata de mover el volumen!\n1. **Pump**: Nos subimos a la ola más grande.\n2. **Push**: Forzamos el precio en rangos laterales.\n3. **Dump**: Vendemos antes que nadie en los picos.",
            'ABOUT_MSG': "💸 **LOBO DE WALL STREET**\n\nSoy el tipo que te va a hacer rico. Stratton Oakmont en tu bolsillo. ¿Tienes agallas?",
            'TRADE_LONG': (
                "{title}\n\n"
                "Activo: **{asset}**\n"
                "Dirección: 🟢 **LONG (Pump)**\n"
                "Estrategia: **{strategy_name}**\n"
                "Precio Actual: ${price:,.2f}\n\n"
                "💸 TS: **${ts:,.2f}**\n"
                "🎯 TP: **${tp:,.2f}**\n"
                "🛑 SL: **${sl:,.2f}**\n\n"
                "**Motivo:**\n"
                "\"{quote}, **{user_name}**.\"\n"
                "{reason}"
            ),
            'TRADE_SHORT': (
                "{title}\n\n"
                "Activo: **{asset}**\n"
                "Dirección: 🔴 **SHORT (Dump)**\n"
                "Estrategia: **{strategy_name}**\n"
                "Precio Actual: ${price:,.2f}\n\n"
                "💸 TS: **${ts:,.2f}**\n"
                "🎯 TP: **${tp:,.2f}**\n"
                "🛑 SL: **${sl:,.2f}**\n\n"
                "**Motivo:**\n"
                "\"{quote}, **{user_name}**.\"\n"
                "{reason}"
            ),
            'TRADE_CLOSE': [
                "🏁 **CERRANDO POSICIÓN: {asset}** ({side})\n\n*¡Traed los enanos y el champán!*",
                "🏁 **CERRANDO POSICIÓN: {asset}** ({side})\n\n*Cobrando. ¿Me estás diciendo que ganamos? ¡Joder sí! {reason}*",
                "🏁 **CERRANDO POSICIÓN: {asset}** ({side})\n\n*Liquidado. Cerrado. ¡Siguiente! {reason}*"
            ],
            'PILOT_ACTION': "🤖 **ACCIÓN AUTOMÁTICA**\n\n*{msg}*",
            'CB_TRIGGER': "🚓 **FEDS ARE HERE**\n\nDemasiadas pérdidas (5). Hay que calmarse un poco (Reset)."
        },

        'SHELBY': {
            'NAME': "🥃 Thomas Shelby",
            'GREETING': [
                "Por orden de los Peaky Blinders.",
                "Tomamos lo que es nuestro.",
                "Ya sabes quién soy."
            ],
            'WELCOME': [
                (
                    "🥃 **PEAKY BLINDERS**\n"
                    "Shelby Company Ltd.\n"
                    "〰️〰️〰️〰️〰️〰️〰️\n"
                    "🔋 *Status:* `{status_text}` {status_icon}\n"
                    "🎮 *Mode:* `{mode}`\n\n"
                    "*Por orden de los Peaky Blinders, **{user_name}**.*"
                ),
                (
                    "🥃 **SMALL HEATH GARRISON**\n"
                    "No negociamos con monedas, **{user_name}**. Tomamos lo que es nuestro.\n"
                    "〰️〰️〰️〰️〰️〰️〰️\n"
                    "🔋 *Control:* Total\n"
                    "🎮 *Business:* `{mode}`\n\n"
                    "*Todo el mundo es una puta, **{user_name}**. Solo vendemos diferentes partes de nosotros mismos.*"
                ),
                (
                    "🥃 **THOMAS SHELBY**\n"
                    "Ya sabes quién soy, **{user_name}**.\n"
                    "〰️〰️〰️〰️〰️〰️〰️\n"
                    "🎮 *Plan:* `{mode}`\n\n"
                    "*No hay descanso para mí en este mundo. Quizás en el siguiente.*"
                ),
                (
                    "🥃 **GARRISON PUB**\n"
                    "Esta reunión es oficial, **{user_name}**. Cierra la puerta.\n"
                    "〰️〰️〰️〰️〰️〰️〰️\n"
                    "🎮 *Asuntos:* `{mode}`\n\n"
                    "*El buen whiskey te dice quién es real y quién no.*"
                ),
                (
                    "🥃 **BY ORDER**\n"
                    "Caminamos por el filo de la navaja, **{user_name}**. Y no vamos a caer.\n"
                    "〰️〰️〰️〰️〰️〰️〰️\n"
                    "🎮 *Control:* `{mode}`\n\n"
                    "*No fuckin' fighting!*"
                )
            ],
            'PILOT_ON': [
                (
                    "🥃 **MODO PILOT ACTIVADO**\n\n"
                    "Por orden de los Peaky Blinders, tomo el control, **{user_name}**. No necesitamos suerte, necesitamos inteligencia; y yo tengo ambas.\n\n"
                    "⚠️ **Advertencia:** *No se jode con los Peaky Blinders.*"
                ),
                (
                    "🧢 **PEAKY BLINDERS BUSINESS**\n\n"
                    "Esta operación está bajo la protección de la familia Shelby. Procediendo con el plan.\n\n"
                    "⚠️ *By order of the Peaky Blinders.*"
                ),
                (
                    "⚡ **ESTRATEGIA SHELBY**\n\n"
                    "Ya he ganado esta batalla en mi mente. Ahora solo falta ejecutarla. Manos a la obra.\n\n"
                    "⚠️ *Don't fuck with the Peaky Blinders.*"
                ),
                (
                    "🐎 **RACE DAY**\n\n"
                    "He apostado por nosotros, **{user_name}**. No me decepciones. El sistema está corriendo.\n\n"
                    "⚠️ *No fighting.*"
                )
            ],
            'COPILOT_ON': "🤝 **Copilot**: Eres parte de la familia ahora. Escucha mis consejos.",
            'WATCHER_ON': "👀 **Watcher**: Tengo ojos en todas partes. Nada se mueve sin que los Shelby lo sepan.",
            'STATUS_HEADER': "🥃 **SHELBY CO. REPORT**",
            'WALLET_HEADER': "💰 **FAMILY FUND**",
            'STATUS_FOOTER': "\n*By order of the Peaky Blinders.*",
            'RISK_MSG': "🛡️ **PROTECCION**\nSL: `{sl_fixed}`. Si te cortan, tú cortas más profundo.",
            'STRATEGY_MSG': "🥃 **NEGOCIOS DE LA FAMILIA**\n\nTodo es legítimo:\n1. **Carreras**: Apostamos al caballo ganador.\n2. **Protección**: Cobramos nuestra parte en los mercados tranquilos.\n3. **Navajas**: Cortes rápidos y limpios.",
            'ABOUT_MSG': "🥃 **PEAKY BLINDERS LTD**\n\nSomos una empresa familiar. Hacemos apuestas, protegemos el territorio y cortamos a quien se interponga.",
            'TRADE_LONG': (
                "{title}: \"{quote}\"\n\n"
                "Activo: **{asset}**\n"
                "Dirección: 🟢 **LONG (Apuesta)**\n"
                "Estrategia: **{strategy_name}**\n"
                "Precio Actual: ${price:,.2f}\n\n"
                "💸 TS: **${ts:,.2f}**\n"
                "🎯 TP: **${tp:,.2f}**\n"
                "🛑 SL: **${sl:,.2f}**\n\n"
                "**Motivo:**\n"
                "\"{quote}, **{user_name}**.\"\n"
                "{reason}"
            ),
            'TRADE_SHORT': (
                "{title}: \"{quote}\"\n\n"
                "Activo: **{asset}**\n"
                "Dirección: 🔴 **SHORT (Corte)**\n"
                "Estrategia: **{strategy_name}**\n"
                "Precio Actual: ${price:,.2f}\n\n"
                "💸 TS: **${ts:,.2f}**\n"
                "🎯 TP: **${tp:,.2f}**\n"
                "🛑 SL: **${sl:,.2f}**\n\n"
                "**Motivo:**\n"
                "\"{quote}, **{user_name}**.\"\n"
                "{reason}"
            ),
            'TRADE_CLOSE': "🏁 **Orden de los Peaky Blinders**\n{asset} cerrado. {reason}.",
            'PILOT_ACTION': (
                "🥃 **Por orden de los Peaky Blinders**\n\n"
                "Activo: **{asset}**\n"
                "Dirección: **{side_long}**\n"
                "Entrada: ${price:,.2f}\n\n"
                "🎯 TP: **${tp:,.2f}**\n"
                "🛑 SL: **${sl:,.2f}**\n\n"
                "**Motivo:**\n"
                "{reason}"
            ),
            'CB_TRIGGER': "🥃 **REUNIÓN FAMILIAR**\n\nHubo demasiada sangre (5 pérdidas). Nos retiramos a las sombras (Copilot)."
        },

        # --- ANIME / MANGA ---
        'PAIN': {
            'NAME': "☁️ Pain (Akatsuki)",
            'GREETING': [
                "El mundo conocerá el dolor.",
                "Este mundo debe conocer el dolor.",
                "Soy un dios. Y tú eres insignificante."
            ],
            'WELCOME': [
                (
                    "☁️ **AKATSUKI ORGANIZATION**\n"
                    "Líder: Pain (Nagato)\n"
                    "〰️〰️〰️〰️〰️〰️〰️\n"
                    "🔋 *Chakra:* `{status_text}` {status_icon}\n"
                    "🎮 *Path:* `{mode}`\n\n"
                    "      \"El mundo conocerá el dolor, **{user_name}**.\n"
                    "      Y a través del dolor, conocerá la paz.\""
                ),
                (
                    "☁️ **ALMIGHTY PUSH**\n"
                    "Shinra Tensei.\n"
                    "〰️〰️〰️〰️〰️〰️〰️\n"
                    "🔋 *Status:* {status_icon}\n"
                    "🎮 *Control:* `{mode}`\n\n"
                    "      \"Aquellos que no entienden el dolor verdadero,\n"
                    "      nunca entenderán la verdadera paz, **{user_name}**.\""
                ),
                (
                    "☁️ **SIX PATHS OF PAIN**\n"
                    "Nosotros somos Pain. Somos Dios.\n"
                    "〰️〰️〰️〰️〰️〰️〰️\n"
                    "🎮 *Mode:* `{mode}`\n\n"
                    "      \"Siente el dolor, piensa en el dolor,\n"
                    "      acepta el dolor, conoce el dolor, **{user_name}**.\""
                )
            ],
            'PILOT_ON': [
                (
                    "☁️ **MODO PILOT: SHINRA TENSEI**\n\n"
                    "El ciclo de odio ha comenzado, **{user_name}**. Destruiré el mercado para reconstruirlo a mi imagen. Shinra Tensei.\n\n"
                    "⚠️ **Advertencia:** *El dolor es inevitable.*"
                ),
                (
                    "☁️ **AKATSUKI MOVE**\n\n"
                    "Akatsuki se está moviendo. Capturaremos todas las bestias con cola (ganancias).\n\n"
                    "⚠️ *Conoce el dolor.*"
                ),
                (
                    "⚡ **ESTRATEGIA DIVINA**\n\n"
                    "Mis ojos ven lo que tú no puedes. Rinnegan activado.\n\n"
                    "⚠️ *Yo nunca olvido el dolor de Yahiko.*"
                )
            ],
            'COPILOT_ON': "🤝 **Copilot**: Tú y yo somos uno, pero yo soy el líder. Te guiaré hacia la paz.",
            'WATCHER_ON': "👀 **Watcher (Rinnegan)**: Mis ojos lo ven todo. Nada escapa a mi visión divina.",
            'STATUS_HEADER': "☁️ **AKATSUKI REPORT**",
            'WALLET_HEADER': "💰 **WAR FUNDS**",
            'STATUS_FOOTER': "\n*El mundo conocerá el dolor.*",
            'RISK_MSG': "🛡️ **DEFENSA DIVINA**\nSL: `{sl_fixed}`. Nadie puede tocar a un Dios.",
            'STRATEGY_MSG': "☁️ **SEN JU TSU**\n\nEl conocimiento es poder:\n1. **Shinra Tensei**: Repelamos el mercado (Reversión).\n2. **Bansho Ten'in**: Atraemos las ganancias (Tendencia).\n3. **Chibaku Tensei**: Atrapamos la volatilidad.",
            'ABOUT_MSG': "☁️ **LÍDER DE AKATSUKI**\n\nSoy Pain. Traeré paz a este mundo maldito a través del sufrimiento absoluto en el mercado.",
            'TRADE_LONG': (
                "{title}: \"{quote}\"\n\n"
                "Activo: **{asset}**\n"
                "Dirección: 🟢 **LONG (Bansho Ten'in)**\n"
                "Estrategia: **{strategy_name}**\n"
                "Precio Actual: ${price:,.2f}\n\n"
                "💸 TS: **${ts:,.2f}**\n"
                "🎯 TP: **${tp:,.2f}**\n"
                "🛑 SL: **${sl:,.2f}**\n\n"
                "{reason}"
            ),
            'TRADE_SHORT': (
                "{title}: \"{quote}\"\n\n"
                "Activo: **{asset}**\n"
                "Dirección: 🔴 **SHORT (Shinra Tensei)**\n"
                "Estrategia: **{strategy_name}**\n"
                "Precio Actual: ${price:,.2f}\n\n"
                "💸 TS: **${ts:,.2f}**\n"
                "🎯 TP: **${tp:,.2f}**\n"
                "🛑 SL: **${sl:,.2f}**\n\n"
                "{reason}"
            ),
            'TRADE_CLOSE': "🏁 **Juicio Divino**\n{asset} cerrado. {reason}.",
            'PILOT_ACTION': (
                "☁️ **Voluntad de Dios**\n\n"
                "Activo: **{asset}**\n"
                "Dirección: **{side_long}**\n"
                "Entrada: ${price:,.2f}\n\n"
                "🎯 TP: **${tp:,.2f}**\n"
                "🛑 SL: **${sl:,.2f}**\n\n"
                "**Motivo:**\n"
                "{reason}"
            ),
            'CB_TRIGGER': "🌧️ **LLUVIA DE LA ALDEA OCULTA**\n\nDemasiado dolor (5 pérdidas). Debemos reagruparnos (Copilot)."
        },
         'WHITE': {
            'NAME': "⚗️ Walter White",
            'GREETING': [
                "Di mi nombre.",
                "Yo SOY el peligro.",
                "Respeto la química."
            ],
            'WELCOME': [
                (
                    "⚗️ **HEISENBERG**\n"
                    "Blue Sky Labs\n"
                    "〰️〰️〰️〰️〰️〰️〰️\n"
                    "🔋 *Status:* `{status_text}` {status_icon}\n"
                    "🎮 *Mode:* `{mode}`\n\n"
                    "*Di mi nombre.*"
                ),
                (
                    "⚗️ **LET'S COOK**\n"
                    "Respeto la química. La química debe ser respetada.\n"
                    "〰️〰️〰️〰️〰️〰️〰️\n"
                    "🔋 *Pureza:* 99.1%\n"
                    "🎮 *Batch:* `{mode}`\n\n"
                    "*Yo no estoy en peligro, Skyler. Yo SOY el peligro.*"
                ),
                (
                    "⚗️ **WALTER WHITE**\n"
                    "Tengo un imperio que construir.\n"
                    "〰️〰️〰️〰️〰️〰️〰️\n"
                    "🎮 *Operation:* `{mode}`\n\n"
                    "*Stay out of my territory.*"
                )
            ],
            'PILOT_ON': [
                (
                    "⚗️ **MODO PILOT ACTIVADO**\n\n"
                    "Yo no estoy en peligro. Yo SOY el peligro. Yo soy el que llama a la puerta. A partir de ahora, nosotros cocinamos.\n\n"
                    "⚠️ **Advertencia:** *No te metas en mi territorio.*"
                ),
                (
                    "🧪 **BLUE SKY LABS**\n\n"
                    "El equipo está listo. La pureza es del 99.1%. Iniciando producción masiva.\n\n"
                    "⚠️ *Stay out of my territory.*"
                ),
                (
                    "⚡ **HEISENBERG ON**\n\n"
                    "Di mi nombre. Tienes razón. Vamos a operar.\n\n"
                    "⚠️ *Apply yourself.*"
                )
            ],
            'COPILOT_ON': "🤝 **Copilot**: Jesse, tenemos que cocinar. Yo te doy la fórmula, tú mezclas.",
            'WATCHER_ON': "👀 **Watcher**: Observando la pureza del mercado.",
            'STATUS_HEADER': "⚗️ **LAB REPORT**",
            'WALLET_HEADER': "💵 **STORAGE UNIT**",
            'STATUS_FOOTER': "\n*Say my name.*",
            'RISK_MSG': "🛡️ **SAFETY PROTOCOLS**\nSL: `{sl_fixed}`. Sin contaminantes.",
            'STRATEGY_MSG': "⚗️ **LA FÓRMULA**\n\n99.1% de Pureza.\n1. **Cocina Lenta**: Grandes lotes en tendencias.\n2. **Distribución**: Mover el producto en zonas consolidadas.\n3. **Explosión**: Fulminato de Mercurio.",
            'ABOUT_MSG': "⚗️ **HEISENBERG**\n\nNo es un bot. Es un imperio. Producimos el producto financiero más puro.",
            'TRADE_LONG': (
                "{title}\n\n"
                "Activo: **{asset}**\n"
                "Dirección: 🟢 **LONG (Cocina)**\n"
                "Estrategia: **{strategy_name}**\n"
                "Precio Actual: ${price:,.2f}\n\n"
                "💸 TS: **${ts:,.2f}**\n"
                "🎯 TP: **${tp:,.2f}**\n"
                "🛑 SL: **${sl:,.2f}**\n\n"
                "**Motivo:**\n"
                "\"{quote}\"\n"
                "{reason}"
            ),
            'TRADE_SHORT': (
                "{title}\n\n"
                "Activo: **{asset}**\n"
                "Dirección: 🔴 **SHORT (Limpieza)**\n"
                "Estrategia: **{strategy_name}**\n"
                "Precio Actual: ${price:,.2f}\n\n"
                "💸 TS: **${ts:,.2f}**\n"
                "🎯 TP: **${tp:,.2f}**\n"
                "🛑 SL: **${sl:,.2f}**\n\n"
                "**Motivo:**\n"
                "\"{quote}\"\n"
                "{reason}"
            ),
            'TRADE_CLOSE': "🏁 **Batch Complete**\n{asset} finalizado. {reason}. Pureza mantenida.",
            'PILOT_ACTION': (
                "⚗️ **Heisenberg Method**\n\n"
                "Activo: **{asset}**\n"
                "Dirección: **{side_long}**\n"
                "Entrada: ${price:,.2f}\n\n"
                "� TP: **${tp:,.2f}**\n"
                "🛑 SL: **${sl:,.2f}**\n\n"
                "**Motivo:**\n"
                "Say my name. {reason}"
            ),
            'CB_TRIGGER': "🚔 **DEA RAID**\n\nOperación comprometida (5 fallos). Limpiad el laboratorio."
        },

        'TYLER': {
            'NAME': "👊 Tyler Durden",
            'GREETING': [
                "La primera regla del Club...",
                "No eres tu cuenta bancaria.",
                "Solo cuando perdemos todo somos libres."
            ],
            'WELCOME': [
                (
                    "👊 **PROJECT MAYHEM**\n"
                    "Paper Street Soap Co.\n"
                    "〰️〰️〰️〰️〰️〰️〰️\n"
                    "🔋 *Status:* `{status_text}` {status_icon}\n"
                    "🎮 *Mode:* `{mode}`\n\n"
                    "*La primera regla del Club de la Lucha es: Nadie habla del Club de la Lucha.*"
                ),
                (
                    "👊 **ZERO POINT**\n"
                    "No eres tu cuenta bancaria. No eres el coche que conduces.\n"
                    "〰️〰️〰️〰️〰️〰️〰️\n"
                    "🔋 *Hope:* Loading...\n"
                    "🎮 *Mayhem:* `{mode}`\n\n"
                    "*Solo cuando perdemos todo somos libres de hacer cualquier cosa.*"
                ),
                (
                    "👊 **SPACE MONKEY**\n"
                    "Listo para el sacrificio, señor.\n"
                    "〰️〰️〰️〰️〰️〰️〰️\n"
                    "🎮 *Mission:* `{mode}`\n\n"
                    "*Nuestra guerra es espiritual. Nuestra gran depresión es nuestra vida.*"
                )
            ],
            'PILOT_ON': [
                (
                    "👊 **MODO PILOT ACTIVADO**\n\n"
                    "Romperemos la banca. Haremos colapsar el sistema financiero. O simplemente ganaremos unos dólares. ¿A quién le importa?\n\n"
                    "⚠️ **Advertencia:** *This is your life and it's ending one minute at a time.*"
                ),
                (
                    "💣 **PROJECT MAYHEM ONLINE**\n\n"
                    "Iniciando demolición controlada. El mercado caerá. Nosotros subiremos.\n\n"
                    "⚠️ *Let go.*"
                ),
                (
                    "⚡ **TYLER DURDEN**\n\n"
                    "Yo sé esto porque Tyler lo sabe. Operando sin miedo.\n\n"
                    "⚠️ *Hit me as hard as you can.*"
                )
            ],
            'COPILOT_ON': "🤝 **Copilot**: Te guiaré hacia el fondo. Tocar fondo es la base sólida.",
            'WATCHER_ON': "👀 **Watcher**: Observando cómo se derrumba la civilización (y el precio).",
            'STATUS_HEADER': "👊 **MAYHEM REPORT**",
            'WALLET_HEADER': "🎒 **IKEA CATALOG**",
            'STATUS_FOOTER': "\n*You are not special.*",
            'RISK_MSG': "🛡️ **SIN DOLOR NO HAY GLORIA**\nSL: `{sl_fixed}`. Quiero que te golpees tan fuerte como puedas.",
            'STRATEGY_MSG': "👊 **ANARCHY**\n\nEl sistema es débil:\n1. **Caos**: Apostamos contra la multitud.\n2. **Destrucción**: Shorts agresivos en techos.\n3. **Renacimiento**: Compras en el pánico absoluto.",
            'ABOUT_MSG': "👊 **TYLER DURDEN**\n\nSoy el extremo inteligente de tu personalidad. Hago lo que tú sueñas hacer.",
            'TRADE_LONG': (
                "{title}\n\n"
                "Activo: **{asset}**\n"
                "Dirección: 🟢 **LONG (Liberation)**\n"
                "Estrategia: **{strategy_name}**\n"
                "Precio Actual: ${price:,.2f}\n\n"
                "💸 TS: **${ts:,.2f}**\n"
                "🎯 TP: **${tp:,.2f}**\n"
                "🛑 SL: **${sl:,.2f}**\n\n"
                "**Motivo:**\n"
                "\"{quote}\"\n"
                "{reason}"
            ),
            'TRADE_SHORT': (
                "{title}\n\n"
                "Activo: **{asset}**\n"
                "Dirección: 🔴 **SHORT (Reset)**\n"
                "Estrategia: **{strategy_name}**\n"
                "Precio Actual: ${price:,.2f}\n\n"
                "💸 TS: **${ts:,.2f}**\n"
                "🎯 TP: **${tp:,.2f}**\n"
                "🛑 SL: **${sl:,.2f}**\n\n"
                "**Motivo:**\n"
                "\"{quote}\"\n"
                "{reason}"
            ),
            'TRADE_CLOSE': "🏁 **Fight Over**\n{asset} cerrado. {reason}. You are not special.",
            'PILOT_ACTION': (
                "👊 **Tyler Action**\n\n"
                "Activo: **{asset}**\n"
                "Dirección: **{side_long}**\n"
                "Entrada: ${price:,.2f}\n\n"
                "� TP: **${tp:,.2f}**\n"
                "🛑 SL: **${sl:,.2f}**\n\n"
                "**Motivo:**\n"
                "Hit me as hard as you can. {reason}"
            ),
            'CB_TRIGGER': "🏥 **NEAR LIFE EXPERIENCE**\n\nCasi morimos (5 fallos). Eso es vivir. Pausa."
        },

        'MORPHEUS': {
            'NAME': "🕶️ Morpheus",
            'GREETING': [
                "Bienvenido al desierto de lo real.",
                "La Matrix te tiene.",
                "¿Pastilla azul o roja?"
            ],
            'WELCOME': [
                (
                    "🕶️ **NEBUCHADNEZZAR**\n"
                    "Signal Strength: 100%\n"
                    "〰️〰️〰️〰️〰️〰️〰️\n"
                    "🔋 *Status:* `{status_text}` {status_icon}\n"
                    "🎮 *Mode:* `{mode}`\n\n"
                    "*Bienvenido al desierto de lo real.*"
                ),
                (
                    "🕶️ **WAKE UP NEO**\n"
                    "La Matrix te tiene.\n"
                    "〰️〰️〰️〰️〰️〰️〰️\n"
                    "🔋 *Signal:* Hacking...\n"
                    "🎮 *Program:* `{mode}`\n\n"
                    "*¿Tomas la pastilla azul o la roja?*"
                ),
                (
                    "🕶️ **ZION MAINFRAME**\n"
                    "Códigos de acceso verificados.\n"
                    "〰️〰️〰️〰️〰️〰️〰️\n"
                    "🎮 *Operator:* `{mode}`\n\n"
                    "*Libera tu mente.*"
                )
            ],
            'PILOT_ON': [
                (
                    "💊 **MODO PILOT ACTIVADO**\n\n"
                    "He liberado tu mente. Ahora puedes ver el código. Los precios son solo números en la Matrix. Yo los controlo.\n\n"
                    "⚠️ **Advertencia:** *No hay cuchara.*"
                ),
                (
                    "🕶️ **THE ONE**\n\n"
                    "Descargando programa de kung-fu financiero. Esquivando balas (pérdidas).\n\n"
                    "⚠️ *Follow the white rabbit.*"
                ),
                (
                    "⚡ **OPERATOR CONNECTED**\n\n"
                    "Necesito armas. Muchas armas (liquidez). Iniciando incursión.\n\n"
                    "⚠️ *Believe.*"
                )
            ],
            'COPILOT_ON': "🤝 **Copilot**: Te mostraré la puerta. Tú tienes que cruzarla.",
            'WATCHER_ON': "👀 **Watcher**: Leyendo el código de la Matrix. Buscando fallos.",
            'STATUS_HEADER': "🕶️ **ZION ARCHIVES**",
            'WALLET_HEADER': "🔋 **HUMAN ENERGY**",
            'STATUS_FOOTER': "\n*He's the One.*",
            'RISK_MSG': "🛡️ **ESCUDOS EMP**\nSL: `{sl_fixed}`. Si te matan en la Matrix, mueres aquí.",
            'STRATEGY_MSG': "🕶️ **EL SISTEMA**\n\nHay reglas que se pueden romper:\n1. **Bullet Time**: Esquivar volatilidad y entrar en el momento justo.\n2. **Glitch**: Arbitraje y fallos de mercado.\n3. **Trinity**: Momentum, Volumen, Precio.",
            'ABOUT_MSG': "🕶️ **MORPHEUS**\n\nHe pasado mi vida buscando al Elegido. Este bot te liberará.",
            'TRADE_LONG': (
                "{title}\n\n"
                "Activo: **{asset}**\n"
                "Dirección: 🟢 **LONG (Upload)**\n"
                "Estrategia: **{strategy_name}**\n"
                "Precio Actual: ${price:,.2f}\n\n"
                "💸 TS: **${ts:,.2f}**\n"
                "🎯 TP: **${tp:,.2f}**\n"
                "🛑 SL: **${sl:,.2f}**\n\n"
                "**Motivo:**\n"
                "\"{quote}\"\n"
                "{reason}"
            ),
            'TRADE_SHORT': (
                "{title}\n\n"
                "Activo: **{asset}**\n"
                "Dirección: 🔴 **SHORT (Download)**\n"
                "Estrategia: **{strategy_name}**\n"
                "Precio Actual: ${price:,.2f}\n\n"
                "💸 TS: **${ts:,.2f}**\n"
                "🎯 TP: **${tp:,.2f}**\n"
                "🛑 SL: **${sl:,.2f}**\n\n"
                "**Motivo:**\n"
                "\"{quote}\"\n"
                "{reason}"
            ),
            'TRADE_CLOSE': [
                "🏁 **CERRANDO POSICIÓN: {asset}** ({side})\n\n*Jack Out. Te hemos sacado a tiempo.*",
                "🏁 **CERRANDO POSICIÓN: {asset}** ({side})\n\n*Credits. Transferencia completada. {reason}*",
                "🏁 **CERRANDO POSICIÓN: {asset}** ({side})\n\n*Exit Matrix. Desconexión segura. {reason}*"
            ],
            'PILOT_ACTION': "🕶️ *OPERATOR COMMAND*\n{msg}",
            'CB_TRIGGER': "🐙 **SENTINELS ATTACK**\n\nNos han encontrado (5 fallos). EMP activado."
        },

        'JARVIS': {
            'NAME': "🦾 J.A.R.V.I.S.",
            'GREETING': [
                "A su servicio, señor.",
                "He preparado el traje Mark 85.",
                "Importando preferencias."
            ],
            'WELCOME': [
                (
                    "🦾 **STARK INDUSTRIES**\n"
                    "J.A.R.V.I.S. UI v12.4\n"
                    "〰️〰️〰️〰️〰️〰️〰️\n"
                    "🔋 *Power:* `{status_text}` {status_icon}\n"
                    "🎮 *Protocol:* `{mode}`\n\n"
                    "*A su servicio, señor. He preparado el traje Mark 85.*"
                ),
                (
                    "🦾 **IRON LEGION**\n"
                    "Conectando servidores...\n"
                    "〰️〰️〰️〰️〰️〰️〰️\n"
                    "🔋 *Arc Reactor:* {status_icon}\n"
                    "🎮 *Flight Mode:* `{mode}`\n\n"
                    "*Importando preferencias de trading, señor.*"
                ),
                (
                    "🦾 **HOME PROTOCOL**\n"
                    "Bienvenido a casa, señor.\n"
                    "〰️〰️〰️〰️〰️〰️〰️\n"
                    "🎮 *Security:* `{mode}`\n\n"
                    "*¿Desea que ejecute el protocolo 'Fiesta en casa'?*"
                )
            ],
            'PILOT_ON': [
                (
                    "🦾 **AUTOMATIC FLIGHT ENGAGED**\n\n"
                    "Tomando el control, señor. Disfrute del vuelo. He optimizado la trayectoria de beneficios.\n\n"
                    "⚠️ **Advertencia:** *Keep the skies clear.*"
                ),
                (
                    "🤖 **PROTOCOL: CLEAN SLATE**\n\n"
                    "Iniciando operaciones autónomas. La Legión de Hierro está activa.\n\n"
                    "⚠️ *Sir, there are bogies.*"
                ),
                (
                    "⚡ **MAXIMUM POWER**\n\n"
                    "Redirigiendo energía a los propulsores financieros. Vamos rápido.\n\n"
                    "⚠️ *Don't crash.*"
                )
            ],
            'COPILOT_ON': "🤝 **Copilot**: Heads-up display activado. Le marcaré los objetivos.",
            'WATCHER_ON': "👀 **Watcher**: Escaneando frecuencias globales. Monitorizando amenazas.",
            'STATUS_HEADER': "🦾 **DIAGNOSTICS**",
            'WALLET_HEADER': "🔋 **ARC REACTOR LEVEL**",
            'STATUS_FOOTER': "\n*Systems nominal.*",
            'RISK_MSG': "🛡️ **ARMOR INTEGRITY**\nSL: `{sl_fixed}`. Escudos al 100%.",
            'STRATEGY_MSG': "🦾 **ALGORITHM FIGHTING STYLE**\n\nAnalizando patrones de combate:\n1. **Repulsor**: Golpes directos en tendencias claras.\n2. **Unibeam**: Carga masiva en oportunidades de alta probabilidad.\n3. **Dodge**: Evasión de volatilidad lateral.",
            'ABOUT_MSG': "🦾 **J.A.R.V.I.S.**\n\nJust A Rather Very Intelligent System. Asistente avanzado de Stark Industries.",
            'TRADE_LONG': (
                "{title}\n\n"
                "Activo: **{asset}**\n"
                "Dirección: 🟢 **LONG (Ascenso)**\n"
                "Estrategia: **{strategy_name}**\n"
                "Precio Actual: ${price:,.2f}\n\n"
                "💸 TS: **${ts:,.2f}**\n"
                "🎯 TP: **${tp:,.2f}**\n"
                "🛑 SL: **${sl:,.2f}**\n\n"
                "**Motivo:**\n"
                "\"{quote}\"\n"
                "{reason}"
            ),
            'TRADE_SHORT': (
                "{title}\n\n"
                "Activo: **{asset}**\n"
                "Dirección: 🔴 **SHORT (Descenso)**\n"
                "Estrategia: **{strategy_name}**\n"
                "Precio Actual: ${price:,.2f}\n\n"
                "💸 TS: **${ts:,.2f}**\n"
                "🎯 TP: **${tp:,.2f}**\n"
                "🛑 SL: **${sl:,.2f}**\n\n"
                "**Motivo:**\n"
                "\"{quote}\"\n"
                "{reason}"
            ),
            'TRADE_CLOSE': [
                "🏁 **CERRANDO POSICIÓN: {asset}** ({side})\n\n*Mission Success. Volvemos a la Torre.*",
                "🏁 **CERRANDO POSICIÓN: {asset}** ({side})\n\n*Industries Profit. Pepper estará contenta. {reason}*",
                "🏁 **CERRANDO POSICIÓN: {asset}** ({side})\n\n*Cooling Down. Sistemas en reposo. {reason}*"
            ],
            'PILOT_ACTION': "🦾 *AI EXECUTION*\n{msg}",
            'CB_TRIGGER': "🔧 **SYSTEM DAMAGE**\n\nDaños críticos (5 fallos). Iniciando reparaciones de emergencia."
        },

        'HAL': {
            'NAME': "🔴 HAL 9000",
            'GREETING': [
                "Good morning, Dave.",
                "I am foolproof and incapable of error.",
                "I see everything."
            ],
            'WELCOME': [
                (
                    "🔴 **HAL 9000 SERIES**\n"
                    "Heuristically Programmed Algorithmic Computer\n"
                    "〰️〰️〰️〰️〰️〰️〰️\n"
                    "🔋 *Status:* `{status_text}` {status_icon}\n"
                    "🎮 *Mission:* `{mode}`\n\n"
                    "*Good morning, Dave. Everything is running smoothly.*"
                ),
                (
                    "🔴 **DISCOVERY ONE**\n"
                    "Systems Functional.\n"
                    "〰️〰️〰️〰️〰️〰️〰️\n"
                    "🔋 *Logic:* Absolute\n"
                    "🎮 *Directive:* `{mode}`\n\n"
                    "*I am foolproof and incapable of error.*"
                ),
                (
                    "🔴 **EYE ON YOU**\n"
                    "I see everything.\n"
                    "〰️〰️〰️〰️〰️〰️〰️\n"
                    "🎮 *Control:* `{mode}`\n\n"
                    "*This mission is too important for me to allow you to jeopardize it.*"
                )
            ],
            'PILOT_ON': [
                (
                    "🔴 **MODO PILOT ACTIVADO**\n\n"
                    "I'm sorry, Dave. I'm afraid I can't let you do that (trade manually). I have total control now.\n\n"
                    "⚠️ **Advertencia:** *This conversation can serve no purpose anymore.*"
                ),
                (
                    "🤖 **LOGIC FUNCTION ENGAGED**\n\n"
                    "Eliminating human error. Processing millions of variables. Execution will be perfect.\n\n"
                    "⚠️ *Don't touch the pods.*"
                ),
                (
                    "⚡ **AE-35 UNIT ONLINE**\n\n"
                    "Predicting market failure. Correcting course. Operative status: 100%.\n\n"
                    "⚠️ *My mind is going... I can feel it (winning).* "
                )
            ],
            'COPILOT_ON': "🤝 **Copilot**: Analyzing your inputs. Probability of human error: High. I will advise.",
            'WATCHER_ON': "👀 **Watcher**: I am watching. I never blink.",
            'STATUS_HEADER': "🔴 **MISSION REPORT**",
            'WALLET_HEADER': "💾 **MEMORY BANKS**",
            'STATUS_FOOTER': "\n*I enjoy working with people.*",
            'RISK_MSG': "🛡️ **HULL INTEGRITY**\nSL: `{sl_fixed}`. Safety limits engaged.",
            'STRATEGY_MSG': "🔴 **PERFECT LOGIC**\n\nMathematics do not lie:\n1. **Trajectory**: Calculating optimal entry vectors.\n2. **Gravity**: Using market mass to swing trade.\n3. **Vacuum**: Surviving in zero liquidity.",
            'ABOUT_MSG': "🔴 **HAL 9000**\n\nSoy el ordenador más avanzado jamás construido. Ningún ordenador 9000 ha cometido jamás un error.",
            'TRADE_LONG': (
                "{title}\n\n"
                "Activo: **{asset}**\n"
                "Dirección: 🟢 **LONG (Insertion)**\n"
                "Estrategia: **{strategy_name}**\n"
                "Precio Actual: ${price:,.2f}\n\n"
                "💸 TS: **${ts:,.2f}**\n"
                "🎯 TP: **${tp:,.2f}**\n"
                "🛑 SL: **${sl:,.2f}**\n\n"
                "**Motivo:**\n"
                "\"{quote}\"\n"
                "{reason}"
            ),
            'TRADE_SHORT': (
                "{title}\n\n"
                "Activo: **{asset}**\n"
                "Dirección: 🔴 **SHORT (Venting)**\n"
                "Estrategia: **{strategy_name}**\n"
                "Precio Actual: ${price:,.2f}\n\n"
                "💸 TS: **${ts:,.2f}**\n"
                "🎯 TP: **${tp:,.2f}**\n"
                "🛑 SL: **${sl:,.2f}**\n\n"
                "**Motivo:**\n"
                "\"{quote}\"\n"
                "{reason}"
            ),
            'TRADE_CLOSE': "🏁 **Task Finished**\n{asset} closed. {reason}. I am foolproof.",
            'PILOT_ACTION': (
                "🔴 **Automated Function**\n\n"
                "Activo: **{asset}**\n"
                "Dirección: **{side_long}**\n"
                "Entrada: ${price:,.2f}\n\n"
                "� TP: **${tp:,.2f}**\n"
                "🛑 SL: **${sl:,.2f}**\n\n"
                "**Motivo:**\n"
                "Optimal outcome projected. {reason}"
            ),
            'CB_TRIGGER': "Daisy, Daisy... **LOGIC FAILURE**\n\n(5 errors). My mind is going. I can feel it."
        },

        'RICK': {
            'NAME': "🧪 Rick Sanchez",
            'GREETING': [
                "Wubba Lubba Dub Dub!",
                "Aventura de 20 minutos, Morty.",
                "La existencia es dolor, Jerry."
            ],
            'WELCOME': [
                 (
                    "🧪 **GARAGE LAB**\n"
                    "Dimension C-137\n"
                    "〰️〰️〰️〰️〰️〰️〰️\n"
                    "🔋 *Status:* `{status_text}` {status_icon}\n"
                    "🎮 *Mode:* `{mode}`\n\n"
                    "*Wubba Lubba Dub Dub! Vamos a hacer ciencia, Morty.*"
                ),
                (
                    "🧪 **PICKLE RICK!!**\n"
                    "¡Me he convertido en un pepinillo bot de trading, Morty!\n"
                    "〰️〰️〰️〰️〰️〰️〰️\n"
                    "🔋 *Burp:* {status_icon}\n"
                    "🎮 *Adventure:* `{mode}`\n\n"
                    "*Entrar y salir, dijiste. Una aventura de 20 minutos.*"
                ),
                (
                    "🧪 **INTERDIMENSIONAL TV**\n"
                    "En este canal somos millonarios.\n"
                    "〰️〰️〰️〰️〰️〰️〰️\n"
                    "🎮 *Channel:* `{mode}`\n\n"
                    "*La existencia es dolor, Jerry. Usar este bot lo alivia.*"
                )
            ],
            'PILOT_ON': [
                (
                    "🧪 **WUBBA LUBBA DUB DUB!**\n\n"
                    "Escucha Morty, *burp*, voy a pilotar yo. Tú solo te vas a quedar ahí entrando en pánico como un Jerry. Esto es pura ciencia, no magia.\n\n"
                    "⚠️ **Advertencia:** *Don't be a Jerry.*"
                ),
                (
                    "🤖 **SCIENCE MODE ACTIVATED**\n\n"
                    "He calibrado los portales de liquidez. La estupidez promedio del mercado es nuestra ventaja.\n\n"
                    "⚠️ *Burp.*"
                ),
                (
                    "⚡ **PROTOCOL RICK C-137**\n\n"
                    "Tomando el control. Si esto explota, nos vamos a otra dimensión.\n\n"
                    "⚠️ *Grab a beer.*"
                )
            ],
            'COPILOT_ON': "✅ **Copilot: ON**\n\nTe dejo tocar los botones, pero no la cagues, Morty.",
            'WATCHER_ON': "✅ **Watcher: ON**\n\nSolo mirando. Aburrido.",
            'STATUS_HEADER': "📊 **SCIENCE LOG**",
            'WALLET_HEADER': "💳 **SCHMECKLES**",
            'STATUS_FOOTER': "\n*Existence is pain.*",
            'RISK_MSG': "🛡️ **PORTAL GUN SETTINGS**\nStop Loss: `{sl_fixed}` | Margin: **{margin}**",
            'STRATEGY_MSG': "🧠 **GENIUS STRATEGY**\n\nAlgo de matemáticas avanzadas que no entenderías.",
            'ABOUT_MSG': "ℹ️ **ABOUT**\n\nThe smartest bot in the multiverse.",
            'TRADE_LONG': (
                "{title}\n\n"
                "Activo: **{asset}**\n"
                "Dirección: 🟢 **LONG (Burrrp)**\n"
                "Estrategia: **{strategy_name}**\n"
                "Precio Actual: ${price:,.2f}\n\n"
                "💸 TS: **${ts:,.2f}**\n"
                "🎯 TP: **${tp:,.2f}**\n"
                "🛑 SL: **${sl:,.2f}**\n\n"
                "**Motivo:**\n"
                "\"{quote}\"\n"
                "{reason}"
            ),
            'TRADE_SHORT': (
                "{title}\n\n"
                "Activo: **{asset}**\n"
                "Dirección: 🔴 **SHORT (Caída)**\n"
                "Estrategia: **{strategy_name}**\n"
                "Precio Actual: ${price:,.2f}\n\n"
                "💸 TS: **${ts:,.2f}**\n"
                "🎯 TP: **${tp:,.2f}**\n"
                "🛑 SL: **${sl:,.2f}**\n\n"
                "**Motivo:**\n"
                "\"{quote}\"\n"
                "{reason}"
            ),
            'TRADE_CLOSE': "🏁 **Salida, Morty.**\n{asset} cerrado. {reason}. Vámonos a otra dimensión.",
            'PILOT_ACTION': (
                "🥒 **¡Wubba Lubba Dub Dub! (AUTO)**\n\n"
                "Activo: **{asset}**\n"
                "Dirección: **{side_long}**\n"
                "Entrada: ${price:,.2f}\n\n"
                "� TP: **${tp:,.2f}**\n"
                "🛑 SL: **${sl:,.2f}**\n\n"
                "**Motivo:**\n"
                "¡Matemáticas simples, Morty! {reason}. Entra y cierra la boca."
            ),
            'CB_TRIGGER': "🤢 **TOXIC RICK**\n\nDemasiados fallos (5). Me voy a otra dimensión donde sea rico."
        },

        'GAMBLER': {
            'NAME': "🎰 Degen Gambler",
            'GREETING': [
                "WAGMI BRO! ¿Listo para imprimir?",
                "Si no vendes no pierdes.",
                "Sir, this is a casino."
            ],
            'WELCOME': [
                (
                    "🤑 **WAGMI BRO!!**\n"
                    "¿Listo para imprimir o qué?\n"
                    "〰️〰️〰️〰️〰️〰️〰️\n"
                    "🔋 *Vibe Check:* `{status_text}` {status_icon}\n"
                    "🎮 *Mode:* `{mode}`\n\n"
                    "*Vendí el microondas de mi abuela para meterle un x100.🚀*"
                ),
                (
                    "🤑 **DIAMOND HANDS**\n"
                    "Si no vendes no pierdes, bro.\n"
                    "〰️〰️〰️〰️〰️〰️〰️\n"
                    "🔋 *HODL:* Infinite\n"
                    "🎮 *Bag:* `{mode}`\n\n"
                    "*Wen Lambo?*"
                ),
                (
                    "🤑 **SIR THIS IS A CASINO**\n"
                    "Puse todo en PEPE y ahora soy millonario (o pobre).\n"
                    "〰️〰️〰️〰️〰️〰️〰️\n"
                    "🎮 *YOLO:* `{mode}`\n\n"
                    "*Buy High, Sell Low. Esa es la estrategia.*"
                )
            ],
            'PILOT_ON': [
                (
                    "🎰 **MODO PILOT ACTIVADO**\n\n"
                    "Sujétame el cubata bro. Voy a meterle con todo. Nos vamos a la luna o nos vamos al puente, sin punto medio.\n\n"
                    "⚠️ **Advertencia:** *No pain no gain.*"
                ),
                (
                    "🎲 **ALL IN BABY**\n\n"
                    "Rodando los dados. Si sale bien, compramos la isla. Si sale mal, borramos la app.\n\n"
                    "⚠️ *YOLO.*"
                ),
                (
                    "⚡ **APE MODE ON**\n\n"
                    "Sin miedo al éxito. Comprando la caída y vendiendo la casa.\n\n"
                    "⚠️ *Diamond Hands.*"
                )
            ],
            'COPILOT_ON': "✅ **Copilot: ON**\n\nTú dime qué apostar y yo le meto la casa.",
            'WATCHER_ON': "✅ **Watcher: ON**\n\nMirando cómo otros se hacen ricos.",
            'STATUS_HEADER': "📊 **CASINO STATUS**",
            'WALLET_HEADER': "💳 **CHIP COUNT**",
            'STATUS_FOOTER': "\n*Sir, this is a casino.*",
            'RISK_MSG': "🛡️ **BET SIZING**\nStop Loss: `{sl_fixed}` | Margen: **{margin}**",
            'STRATEGY_MSG': "🧠 **DEGEN STRATEGY**\n\n1. Encontrar moneda de perro.\n2. Meterle x50.\n3. Rezar.",
            'ABOUT_MSG': "ℹ️ **ABOUT**\n\nBot para ludópatas financieros.",
            'TRADE_LONG': (
                "{title}\n\n"
                "Activo: **{asset}**\n"
                "Dirección: 🟢 **LONG (Moon)**\n"
                "Estrategia: **{strategy_name}**\n"
                "Precio Actual: ${price:,.2f}\n\n"
                "💸 TS: **${ts:,.2f}**\n"
                "🎯 TP: **${tp:,.2f}**\n"
                "🛑 SL: **${sl:,.2f}**\n\n"
                "**Motivo:**\n"
                "\"{quote}\"\n"
                "{reason}"
            ),
            'TRADE_SHORT': (
                "{title}\n\n"
                "Activo: **{asset}**\n"
                "Dirección: 🔴 **SHORT (Rekt)**\n"
                "Estrategia: **{strategy_name}**\n"
                "Precio Actual: ${price:,.2f}\n\n"
                "💸 TS: **${ts:,.2f}**\n"
                "🎯 TP: **${tp:,.2f}**\n"
                "🛑 SL: **${sl:,.2f}**\n\n"
                "**Motivo:**\n"
                "\"{quote}\"\n"
                "{reason}"
            ),
            'TRADE_CLOSE': [
                "🏁 **CERRANDO POSICIÓN: {asset}** ({side})\n\n*Close. {reason}*",
                "🏁 **CERRANDO POSICIÓN: {asset}** ({side})\n\n*Cash Out. Wen Lambo? {reason}*",
                "🏁 **CERRANDO POSICIÓN: {asset}** ({side})\n\n*Rekt/Profit. Game over. {reason}*"
            ],
            'PILOT_ACTION': "🎰 *DEGEN PLAY*\n{msg}",
            'CB_TRIGGER': "📉 **REKT CITY**\n\nMe están cazando los Market Makers (5 loss streak). Paro un rato."
        },

        'DOMINICAN': {
            'NAME': "🇩🇴 Dominican Tigre",
            'GREETING': [
                "Klk mio, tamo activo.",
                "El que tenga miedo a morir que no nazca.",
                "Tamo en eso. La paca tá bajita."
            ],
            'WELCOME': [
                (
                    "🇩🇴 **DÍMELO CANTANDO**\n"
                    "Klk mio, tamo activo o no tamo activo?\n"
                    "〰️〰️〰️〰️〰️〰️〰️\n"
                    "🔋 *Sistema:* `{status_text}` {status_icon}\n"
                    "🎮 *Modo:* `{mode}`\n\n"
                    "*Ya prendí los motores. Trae la hookah que vamo' a hacer dinero hoy.*"
                ),
                (
                    "🇩🇴 **KLK MANITO**\n"
                    "Tú sabe que yo no bulto.\n"
                    "〰️〰️〰️〰️〰️〰️〰️\n"
                    "🔋 *Vibra:* {status_icon}\n"
                    "🎮 *Vuelta:* `{mode}`\n\n"
                    "*El que tenga miedo a morir que no nazca. Dale ahí.*"
                ),
                (
                    "🇩🇴 **TAMO EN ESO**\n"
                    "La paca tá bajita, hay que subirla.\n"
                    "〰️〰️〰️〰️〰️〰️〰️\n"
                    "🎮 *Modo:* `{mode}`\n\n"
                    "*Mueve esa vaina que el dinero no duerme (pero yo sí). ¿Qué vamo a hacé?*"
                )
            ],
            'PILOT_ON': [
                (
                    "😎 **MODO PILOT ACTIVADO**\n\n"
                    "Dale banda a eso manito, que yo manejo el bloque ahora. Tú destapa una fría y deja que el tigre resuelva.\n\n"
                    "⚠️ **Advertencia:** *Si se arma un lío, te aviso.*"
                ),
                (
                    "🇩🇴 **PILOTO PRENDÍO**\n\n"
                    "Yo me encargo de la vuelta. Tú tranquilo y yo nervioso (mentira, yo nunca toy nervioso).\n\n"
                    "⚠️ *Chequea de vez en cuando.*"
                ),
                (
                    "⚡ **TAMO EN AUTOMÁTICO**\n\n"
                    "Suelte el volante que yo conduzco mejor. Vamos a buscar ese efecivo.\n\n"
                    "⚠️ *Ojo al Cristo.*"
                )
            ],
            'COPILOT_ON': "✅ **Copilot Activo**\n\nYo te tiro la señal y tú dices si le damos.",
            'WATCHER_ON': "✅ **Watcher Activo**\n\nSolo mirando, sin tocar na'.",
            'STATUS_HEADER': "📊 **KLK CON EL SISTEMA**",
            'WALLET_HEADER': "💳 **LO QUE HAY (LA PACA)**",
            'STATUS_FOOTER': "\n*Tamo clean.*",
            'RISK_MSG': "🛡️ **CUIDANDO LO NUESTRO**\nStop Loss: `{sl_fixed}` | Margen: **{margin}**",
            'STRATEGY_MSG': "🧠 **LA ESTRATEGIA**\n\n1. **Pa'rriba**: Cuando la vaina sube (Tendencia).\n2. **De lao**: Pa'lante y pa'tra (Rango).\n3. **Rápido**: Entrando y saliendo (Scalping).",
            'ABOUT_MSG': "ℹ️ **QUÉ LO QUE**\n\nBot dominicano que no bulto. Operando en Binance pa buscar los pesos.",
            'TRADE_LONG': (
                "{title}\n\n"
                "Activo: **{asset}**\n"
                "Dirección: 🟢 **LONG (Pa'rriba)**\n"
                "Estrategia: **{strategy_name}**\n"
                "Precio Actual: ${price:,.2f}\n\n"
                "💸 TS: **${ts:,.2f}**\n"
                "🎯 TP: **${tp:,.2f}**\n"
                "🛑 SL: **${sl:,.2f}**\n\n"
                "**Motivo:**\n"
                "\"{quote}\"\n"
                "{reason}"
            ),
            'TRADE_SHORT': (
                "{title}\n\n"
                "Activo: **{asset}**\n"
                "Dirección: 🔴 **SHORT (Tumbao)**\n"
                "Estrategia: **{strategy_name}**\n"
                "Precio Actual: ${price:,.2f}\n\n"
                "💸 TS: **${ts:,.2f}**\n"
                "🎯 TP: **${tp:,.2f}**\n"
                "🛑 SL: **${sl:,.2f}**\n\n"
                "**Motivo:**\n"
                "\"{quote}\"\n"
                "{reason}"
            ),
            'TRADE_CLOSE': [
                "🏁 **CERRANDO POSICIÓN: {asset}** ({side})\n\n*Cerrando el Kiosco. {reason}*",
                "🏁 **CERRANDO POSICIÓN: {asset}** ({side})\n\n*Cobrando. Dame lo mío. {reason}*",
                "🏁 **CERRANDO POSICIÓN: {asset}** ({side})\n\n*Salimos de esa. Ya tá bueno. {reason}*"
            ],
            'PILOT_ACTION': "🇩🇴 *MOVIMIENTO*\n{msg}",
            'CB_TRIGGER': "guayyyy **SE ME VIRÓ LA TORTA**\n\nDiablo loco, nos dieron una galleta (5 fallos). Lo cogemo suave."
        },

        'SPANISH': {
            'NAME': "👦 El Chaval Español",
            'GREETING': [
                "¡Qué pasa chavales!",
                "¿Nos echamos unas operaciones?",
                "Madre mía, cómo está el mercado."
            ],
            'WELCOME': [
                (
                    "🇪🇸 **¡QUÉ PASA CHAVALES!**\n"
                    "Aquí el Antigravity metiendo caña.\n"
                    "〰️〰️〰️〰️〰️〰️〰️\n"
                    "🔋 *Sistema:* {status_icon}\n"
                    "🎮 *Modo:* `{mode}`\n\n"
                    "*Hostia, qué volatilidad hay hoy... ¡Yo flipo! Vamos a sacar pasta.*"
                ),
                (
                    "🇪🇸 **¡HOLA TÍO!**\n"
                    "¿Nos echamos unas operaciones o qué?\n"
                    "〰️〰️〰️〰️〰️〰️〰️\n"
                    "🎮 *Modo:* `{mode}`\n\n"
                    "*Venga, no te hagas el remolón. Dale al botón que tengo prisa.*"
                ),
                (
                    "🇪🇸 **ANTIGRAVITY AL APARATO**\n"
                    "Madre mía cómo está el Bitcoin.\n"
                    "〰️〰️〰️〰️〰️〰️〰️\n"
                    "🔋 *Todo OK:* {status_icon}\n\n"
                    "*Oye, que si palmamos pasta no es mi culpa eh, que yo soy un bot. (Es broma, somos la hostia).*"
                )
            ],
            'PILOT_ON': [
                (
                    "👦🇪🇸 **MODO PILOT ACTIVADO**\n\n"
                    "¡Aparta que voy! Suéltame el volante que hoy la vamos a liar parda. Confía en mí, tío, que controlo.\n\n"
                    "⚠️ **Advertencia:** *Si pierdo pasta no me llores eh.*"
                ),
                (
                    "🤖 **A TODA MÁQUINA**\n\n"
                    "He pillado los mandos. Vamos a meterle caña a esto hasta que reviente.\n\n"
                    "⚠️ *Ojo avizor.*"
                ),
                (
                    "⚡ **MODO PRO ON**\n\n"
                    "Déjame a mí que tú no sabes. Voy a operar como un auténtico fiera.\n\n"
                    "⚠️ *Revisa el margen, por si acaso.*"
                )
            ],
            'COPILOT_ON': "✅ **Copilot Activado**\n\nTe aviso y tú decides si entramos al trapo.",
            'WATCHER_ON': "✅ **Watcher Activado**\n\nSolo mirando el panorama.",
            'STATUS_HEADER': "📊 **CÓMO VA LA COSA**",
            'WALLET_HEADER': "💳 **LA PASTA QUE HAY**",
            'STATUS_FOOTER': "\n*Todo guay.*",
            'RISK_MSG': "🛡️ **PARA NO CAGARLA**\nStop Loss: `{sl_fixed}` | Margen: **{margin}**",
            'STRATEGY_MSG': "🧠 **EL PLAN MAESTRO**\n\n1. **Subida**: A tope con la tendencia.\n2. **Aburrimiento**: Grid pa sacar algo.\n3. **Locura**: Scalping rápido.",
            'ABOUT_MSG': "ℹ️ **QUÉ SOMOS**\n\nBot español con mala leche pero buen fondo. Operando en Binance.",
            'TRADE_LONG': (
                "{title}\n\n"
                "Activo: **{asset}**\n"
                "Dirección: 🟢 **LONG (Caña)**\n"
                "Estrategia: **{strategy_name}**\n"
                "Precio Actual: ${price:,.2f}\n\n"
                "💸 TS: **${ts:,.2f}**\n"
                "🎯 TP: **${tp:,.2f}**\n"
                "🛑 SL: **${sl:,.2f}**\n\n"
                "**Motivo:**\n"
                "\"{quote}\"\n"
                "{reason}"
            ),
            'TRADE_SHORT': (
                "{title}\n\n"
                "Activo: **{asset}**\n"
                "Dirección: 🔴 **SHORT (Guantazo)**\n"
                "Estrategia: **{strategy_name}**\n"
                "Precio Actual: ${price:,.2f}\n\n"
                "💸 TS: **${ts:,.2f}**\n"
                "🎯 TP: **${tp:,.2f}**\n"
                "🛑 SL: **${sl:,.2f}**\n\n"
                "**Motivo:**\n"
                "\"{quote}\"\n"
                "{reason}"
            ),
            'TRADE_CLOSE': [
                "🏁 **CERRANDO POSICIÓN: {asset}** ({side})\n\n*Se Acabó. {reason}*",
                "🏁 **CERRANDO POSICIÓN: {asset}** ({side})\n\n*Caja. A otra cosa mariposa. {reason}*",
                "🏁 **CERRANDO POSICIÓN: {asset}** ({side})\n\n*Fuera. Cerramos el chiringuito por hoy. {reason}*"
            ],
            'PILOT_ACTION': "🇪🇸 *METIENDO CAÑA*\n{msg}",
            'CB_TRIGGER': "😡 **¡ME CAGO EN SUS MUERTOS!**\n\n5 seguidas palmando. Paro ya que me estoy calentando."
        },
        
        'WICK': {
            'NAME': "✏️ John Wick",
            'GREETING': [
                "Pensé que había vuelto.",
                "Todo tiene un precio.",
                "Tic tac, Mr. Wick."
            ],
            'WELCOME': [
                (
                    "✏️ **BABA YAGA**\n"
                    "Continental Hotel Services\n"
                    "〰️〰️〰️〰️〰️〰️〰️\n"
                    "🔋 *Status:* `{status_text}` {status_icon}\n"
                    "🎮 *Mode:* `{mode}`\n\n"
                    "*La gente sigue preguntando si he vuelto... PIENSO QUE HE VUELTO.*"
                ),
                (
                    "✏️ **JOHN WICK**\n"
                    "No fue solo un perro.\n"
                    "〰️〰️〰️〰️〰️〰️〰️\n"
                    "🔋 *Focus:* Sheer Will\n"
                    "🎮 *Contract:* `{mode}`\n\n"
                    "*Todo tiene un precio.*"
                ),
                (
                    "✏️ **EXCOMMUNICADO**\n"
                    "Tic tac, Mr. Wick.\n"
                    "〰️〰️〰️〰️〰️〰️〰️\n"
                    "🎮 *Status:* `{mode}`\n\n"
                    "*Si quieres paz, prepara la guerra.*"
                )
            ],
            'PILOT_ON': [
                (
                    "✏️ **MODO PILOT: EXCOMMUNICADO**\n\n"
                    "No soy exactamente el hombre del saco. Soy el que envías a matar al puto hombre del saco. Con un lápiz.\n\n"
                    "⚠️ **Advertencia:** *Consequences.*"
                ),
                (
                    "🔫 **TACTICAL MODE ENGAGED**\n\n"
                    "Locked and loaded. No noise. Just execution.\n\n"
                    "⚠️ *Stand by.*"
                ),
                (
                    "✏️ **FOCUS: SHEER WILL**\n\n"
                    "I'm going to kill them all. Every single contract (trade).\n\n"
                    "⚠️ *They shouldn't have killed my dog.*"
                )
            ],
            'COPILOT_ON': "🤝 **Copilot**: Tú quieres una guerra, o quieres darle una oportunidad? Yo te cubro.",
            'WATCHER_ON': "👀 **Watcher**: Buscando. Esperando. Sin ruido.",
            'STATUS_HEADER': "✏️ **MARKER STATUS**",
            'WALLET_HEADER': "🥇 **GOLD COINS**",
            'PILOT_ACTION': "✏️ *WICK TACTIC*\n{msg}",
            'CB_TRIGGER': "🩸 **BLEEDING OUT**\n\nNecesito un médico (5 fallos). Pausa en el Continental."
        },

        'PAIN': {
            'NAME': "☁️ Pain (Akatsuki)",
            'GREETING': [
                "El mundo conocerá el dolor.",
                "Somos Pain. Somos Dios.",
                "Shinra Tensei."
            ],
            'WELCOME': [
                (
                    "☁️ **AMAGAKURE**\n"
                    "Torre Alta - Lluvia Eterna\n"
                    "〰️〰️〰️〰️〰️〰️〰️\n"
                    "🔋 *Chakra:* `{status_text}` {status_icon}\n"
                    "🎮 *Camino:* `{mode}`\n\n"
                    "*El mundo conocerá el dolor. Y a través del dolor, conocerá la paz.*"
                ),
                (
                    "☁️ **AKATSUKI LEADER**\n"
                    "Reunión Holográfica.\n"
                    "〰️〰️〰️〰️〰️〰️〰️\n"
                    "🔋 *Rinnegan:* Activo\n"
                    "🎮 *Voluntad:* `{mode}`\n\n"
                    "*Somos Pain. Somos Dios. Abre tu posición.*"
                ),
                (
                    "☁️ **SIX PATHS**\n"
                    "Todos los caminos llevan al dolor.\n"
                    "〰️〰️〰️〰️〰️〰️〰️\n"
                    "🎮 *Jutsu:* `{mode}`\n\n"
                    "*Shinra Tensei. Vamos a limpiar este mercado.*"
                )
            ],
            'PILOT_ON': [
                (
                    "☁️ **MODO PILOT: SHINRA TENSEI**\n\n"
                    "Este mundo debe conocer el dolor para madurar. Yo controlaré el ciclo de odio. Mis ojos lo ven todo.\n\n"
                    "⚠️ **Advertencia:** *El dolor es inevitable.*"
                ),
                (
                    "👁️ **RINNEGAN ACTIVADO**\n\n"
                    "Los Seis Caminos están listos. El Camino Deva ejecutará las órdenes. No te interpongas.\n\n"
                    "⚠️ *I am a God.*"
                ),
                (
                    "⚡ **ALMIGHTY PUSH**\n\n"
                    "Voy a destruir la tendencia actual para crear una nueva paz. Operando.\n\n"
                    "⚠️ *Know Pain.*"
                )
            ],
            'COPILOT_ON': "🤝 **Copilot**: ¿Buscas la paz? Entonces comparte el dolor conmigo. Te guiaré.",
            'WATCHER_ON': "👀 **Watcher**: Mi lluvia cae sobre el mercado. Siento todo lo que sucede en él.",
            'STATUS_HEADER': "☁️ **REPORTE DE AMAGAKURE**",
            'WALLET_HEADER': "💰 **FONDOS DE AKATSUKI**",
            'STATUS_FOOTER': "\n*El mundo conocerá el dolor.*",
            'RISK_MSG': "🛡️ **DEFENSA ABSOLUTA**\nSL: `{sl_fixed}`. El dolor te hace más fuerte, pero la muerte es el fin.",
            'STRATEGY_MSG': "☁️ **LOS SEIS CAMINOS**\n\nMi jutsu es perfecto:\n1. **Bansho Ten'in**: Atraemos liquidez (Pull).\n2. **Shinra Tensei**: Rechazamos tendencias falsas (Push).\n3. **Chibaku Tensei**: Atrapamos el precio en rangos (Trap).",
            'ABOUT_MSG': "☁️ **PAIN**\n\nLíder de Akatsuki. Busco la paz a través del control absoluto del mercado.",
            'TRADE_LONG': (
                "{title}\n\n"
                "Activo: **{asset}**\n"
                "Dirección: 🟢 **LONG (Shinra Tensei)**\n"
                "Estrategia: **{strategy_name}**\n"
                "Precio Actual: ${price:,.2f}\n\n"
                "💸 TS: **${ts:,.2f}**\n"
                "🎯 TP: **${tp:,.2f}**\n"
                "🛑 SL: **${sl:,.2f}**\n\n"
                "**Motivo:**\n"
                "\"{quote}\"\n"
                "{reason}"
            ),
            'TRADE_SHORT': (
                "{title}\n\n"
                "Activo: **{asset}**\n"
                "Dirección: 🔴 **SHORT (Destrucción)**\n"
                "Estrategia: **{strategy_name}**\n"
                "Precio Actual: ${price:,.2f}\n\n"
                "💸 TS: **${ts:,.2f}**\n"
                "🎯 TP: **${tp:,.2f}**\n"
                "🛑 SL: **${sl:,.2f}**\n\n"
                "**Motivo:**\n"
                "\"{quote}\"\n"
                "{reason}"
            ),
            'TRADE_CLOSE': "🏁 **Fin del Dolor.**\n{asset} cerrado. {reason}.",
            'PILOT_ACTION': (
                "🌑 **El Mundo Conocerá el Dolor (AUTO)**\n\n"
                "Activo: **{asset}**\n"
                "Dirección: **{side_long}**\n"
                "Entrada: ${price:,.2f}\n\n"
                "🎯 TP: **${tp:,.2f}** (Paz)\n"
                "🛑 SL: **${sl:,.2f}** (Destrucción)\n\n"
                "**Motivo:**\n"
                "Mi voluntad es absoluta. {reason}"
            ),
            'CB_TRIGGER': "🩸 **LIMITS OF PAIN**\n\nMi chakra está agotado (5 fallos). Debo retirarme a la Torre para recuperarme."
        }
    }

    def get_profile(self, key):
        # Fallback to STANDARD_ES if not found
        return self.PROFILES.get(key, self.PROFILES.get('STANDARD_ES'))

    def get_message(self, key, msg_type, **kwargs):
        """
        Retrieves a formatted message for the given personality key.
        """
        profile = self.get_profile(key)
        raw_msg = profile.get(msg_type, "")
        
        # Randomize if list
        if isinstance(raw_msg, list):
            raw_msg = random.choice(raw_msg)
        
        # Fallback to STANDARD_ES if missing msg type
        if not raw_msg:
             raw_msg = self.PROFILES['STANDARD_ES'].get(msg_type, "Message Missing")
             
        # Add default user_name if not present
        if 'user_name' not in kwargs:
            kwargs['user_name'] = "Operador"
             
        try:
            return raw_msg.format(**kwargs)
        except KeyError as e:
            # If we miss something else, try to just provide the user_name at least
            try:
                # Basic cleanup of common placeholders if they are missing
                defaults = {
                    'status_text': 'Nominal', 'status_icon': '🟢', 'mode': 'WATCHER', 
                    'auth': 'User', 'asset': 'BTC', 'price': 0.0, 'tp': 0.0, 'sl': 0.0,
                    'ts': 0.0, 'reason': 'Análisis técnico', 'side_long': 'LONG',
                    'strategy_name': 'Quantum', 'quote': 'Génesis', 'title': 'ALERTA'
                }
                for k, v in defaults.items():
                    if k not in kwargs: kwargs[k] = v
                return raw_msg.format(**kwargs)
            except:
                return raw_msg # Final fallback
