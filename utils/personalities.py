import random

class PersonalityManager:
    """
    Manages the bot's tone and responses based on the selected personality profile.
    """
    
    PROFILES = {
        # --- STANDARDS ---
        'STANDARD_ES': {
            'NAME': "🇪🇸 Estándar (Español)",
            'WELCOME': [
                (
                    "🇪🇸 **ANTIGRAVITY BOT v3.3**\n"
                    "Sistema de Trading Automatizado.\n"
                    "〰️〰️〰️〰️〰️〰️〰️\n\n"
                    "🔋 *Estado:* `{status_text}` {status_icon}\n"
                    "🎮 *Modo:* `{mode}`\n"
                    "🔐 *Acceso:* `{auth}`\n\n"
                    "Listo para operar. Seleccione una opción del menú."
                ),
                (
                    "🇪🇸 **SISTEMA ONLINE**\n"
                    "Iniciando protocolos de mercado...\n"
                    "〰️〰️〰️〰️〰️〰️〰️\n"
                    "🔋 *Estado:* `{status_text}` {status_icon}\n"
                    "🎮 *Modo:* `{mode}`\n\n"
                    "Esperando instrucciones del operador."
                ),
                (
                    "🤖 **ANTIGRAVITY CORE**\n"
                    "Conexión establecida con éxito.\n"
                    "〰️〰️〰️〰️〰️〰️〰️\n"
                    "📈 *Mercado:* Analizando...\n"
                    "🎮 *Modo:* `{mode}`\n\n"
                    "¿Cuál es el plan para hoy?"
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
                    "Algoritmos activados. Manos libres. El bot operará según la configuración de riesgo establecida.\n\n"
                    "⚠️ *Revise su margen disponible.*"
                )
            ],
            'COPILOT_ON': "✅ **Modo Copilot Activado**\n\nEl bot enviará propuestas de trading para su aprobación manual.",
            'WATCHER_ON': "✅ **Modo Watcher Activado**\n\nEl bot solo enviará alertas de mercado.",
            'STATUS_HEADER': "📊 **REPORTE DE ESTADO**",
            'WALLET_HEADER': "💳 **BALANCE DE CUENTA**",
            'STATUS_FOOTER': "\n*Sistema nominal.*",
            'RISK_MSG': "🛡️ **CONFIGURACIÓN DE RIESGO**\nStop Loss: `{sl_fixed}` | Margen: **{margin}**",
            'STRATEGY_MSG': "🧠 **ESTRATEGIA QUANTUM**\n\nEl sistema utiliza algoritmos adaptativos:\n1. **Tendencia**: Cruce de EMAs y ADX para capturar movimientos largos (BTC, ETH).\n2. **Rango**: Grid Trading para mercados laterales (ADA, XRP).\n3. **Volatilidad**: Scalping de ruptura en activos rápidos (SOL).",
            'ABOUT_MSG': "ℹ️ **SOBRE ANTIGRAVITY**\n\nBot de trading autónomo desarrollado para operar en Binance Futures/Spot y Alpaca. Gestiona riesgo, ejecuta estrategias múltiples y posee módulos de personalidad adaptativos.",
            'TRADE_LONG': [
                "📈 **COMPRA: {asset}**\nPrecio: ${price:,.2f}\nRazón: {reason}",
                "🚀 **LONG INICIADO: {asset}**\nEntrada detectada por algoritmos.\nPrecio: ${price:,.2f}\n🔸 {reason}",
                "🟢 **SEÑAL ALCISTA: {asset}**\nAbriendo posición de compra.\nPrecio: ${price:,.2f}\n🔎 {reason}"
            ],
            'TRADE_SHORT': [
                "📉 **VENTA: {asset}**\nPrecio: ${price:,.2f}\nRazón: {reason}",
                "🔻 **SHORT INICIADO: {asset}**\nRetroceso detectado.\nPrecio: ${price:,.2f}\n🔸 {reason}",
                "🔴 **SEÑAL BAJISTA: {asset}**\nAbriendo corto.\nPrecio: ${price:,.2f}\n🔎 {reason}"
            ],
            'TRADE_CLOSE': [
                "🏁 **CIERRE: {asset}** ({side})\nRazón: {reason}",
                "💰 **POSICIÓN CERRADA: {asset}**\nOperación finalizada.\n📄 {reason}",
                "⏹️ **SALIDA EJECUTADA: {asset}**\nTomando beneficios/pérdidas.\n📄 {reason}"
            ],
            'PILOT_ACTION': "🤖 *ACCIÓN AUTOMÁTICA*\n{msg}",
            'CB_TRIGGER': "⚠️ **CIRCUIT BREAKER**\nLímite de pérdidas alcanzado. Sistema en pausa."
        },
        'STANDARD_EN': {
            'NAME': "🇬🇧 Standard (English)",
            'WELCOME': (
                "🇬🇧 **ANTIGRAVITY BOT v3.3**\n"
                "Automated Trading System.\n"
                "〰️〰️〰️〰️〰️〰️〰️\n\n"
                "🔋 *Status:* `{status_text}` {status_icon}\n"
                "🎮 *Mode:* `{mode}`\n"
                "🔐 *Access:* `{auth}`\n\n"
                "Ready to operate. Select an option from the menu."
            ),
            'PILOT_ON': [
                (
                    "🇬🇧 **PILOT MODE ENGAGED**\n\n"
                    "System has assumed control of operations. Entries and exits will be executed based on detected algorithms.\n\n"
                    "⚠️ **Warning:** *Periodic human supervision is recommended.*"
                ),
                (
                    "🤖 **AUTOPILOT ACTIVE**\n\n"
                    "Initiating autonomous trading sequence. Quantum algorithms scanning for opportunities.\n\n"
                    "⚠️ *Keep monitoring alerts.*"
                ),
                (
                    "⚡ **CONTROL SYSTEM**\n\n"
                    "Algorithms engaged. Hands-free mode. Bot operates based on risk settings.\n\n"
                    "⚠️ *Check available margin.*"
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
            'TRADE_LONG': [
                "📈 **BUY: {asset}**\nPrice: ${price:,.2f}\nReason: {reason}",
                "🚀 **LONG ENTRY: {asset}**\nAlgorithm detection.\nPrice: ${price:,.2f}\n🔸 {reason}",
                "🟢 **BULL SIGNAL: {asset}**\nOpening position.\nPrice: ${price:,.2f}\n🔎 {reason}"
            ],
            'TRADE_SHORT': [
                "📉 **SELL: {asset}**\nPrice: ${price:,.2f}\nReason: {reason}",
                "🔻 **SHORT ENTRY: {asset}**\nPullback detected.\nPrice: ${price:,.2f}\n🔸 {reason}",
                "🔴 **BEAR SIGNAL: {asset}**\nOpening short.\nPrice: ${price:,.2f}\n🔎 {reason}"
            ],
            'TRADE_CLOSE': [
                "🏁 **CLOSE: {asset}** ({side})\nReason: {reason}",
                "💰 **POSITION CLOSED: {asset}**\nOperation finished.\n📄 {reason}",
                "⏹️ **EXIT EXECUTED: {asset}**\nTaking profit/loss.\n📄 {reason}"
            ],
            'PILOT_ACTION': "🤖 *AUTOMATED ACTION*\n{msg}",
            'CB_TRIGGER': "⚠️ **CIRCUIT BREAKER**\nLoss limit reached. System paused."
        },
        'STANDARD_FR': {
            'NAME': "🇫🇷 Standard (Français)",
            'WELCOME': (
                "🇫🇷 **ANTIGRAVITY BOT v3.3**\n"
                "Système de Trading Automatisé.\n"
                "〰️〰️〰️〰️〰️〰️〰️\n\n"
                "🔋 *État:* `{status_text}` {status_icon}\n"
                "🎮 *Mode:* `{mode}`\n"
                "🔐 *Accès:* `{auth}`\n\n"
                "Prêt à opérer. Sélectionnez une option."
            ),
            'PILOT_ON': [
                (
                    "🇫🇷 **MODE PILOT ACTIVÉ**\n\n"
                    "Le système a pris le contrôle des opérations. Les entrées et sorties seront exécutées selon les algorithmes détectés.\n\n"
                    "⚠️ **Avertissement:** *Une surveillance humaine périodique est recommandée.*"
                ),
                (
                    "🤖 **PILOTE AUTOMATIQUE**\n\n"
                    "Lancement de la séquence de trading autonome.\n\n"
                    "⚠️ *Surveillez les alertes.*"
                ),
                (
                    "⚡ **SYSTÈME DE CONTRÔLE**\n\n"
                    "Algorithmes activés. Mains libres.\n\n"
                    "⚠️ *Vérifiez votre marge.*"
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
            'TRADE_LONG': [
                "📈 **ACHAT: {asset}**\nPrix: ${price:,.2f}\nRaison: {reason}",
                "🚀 **LONG: {asset}**\nEntrée détectée.\nPrix: ${price:,.2f}\n🔸 {reason}",
                "🟢 **SIGNAL HAUSSIER: {asset}**\nPosition ouverte.\nPrix: ${price:,.2f}\n🔎 {reason}"
            ],
            'TRADE_SHORT': [
                "📉 **VENTE: {asset}**\nPrix: ${price:,.2f}\nRaison: {reason}",
                "🔻 **SHORT: {asset}**\nRetrait détecté.\nPrix: ${price:,.2f}\n🔸 {reason}",
                "🔴 **SIGNAL BAISSIER: {asset}**\nPosition courte.\nPrix: ${price:,.2f}\n🔎 {reason}"
            ],
            'TRADE_CLOSE': [
                "🏁 **CLÔTURE: {asset}** ({side})\nRaison: {reason}",
                "💰 **POSITION FERMÉE: {asset}**\nOpération terminée.\n📄 {reason}",
                "⏹️ **SORTIE: {asset}**\nPrise de profit/perte.\n📄 {reason}"
            ],
            'PILOT_ACTION': "🤖 *ACTION AUTOMATIQUE*\n{msg}",
            'CB_TRIGGER': "⚠️ **CIRCUIT BREAKER**\nLimite de pertes atteinte. Système en pause."
        },

        # --- DARK SIDE ---
        'VADER': {
            'NAME': "🌑 Darth Vader",
            'WELCOME': [
                (
                    "🌑 **IMPERIAL TRADING SYSTEM**\n"
                    "Estrella de la Muerte - Mainframe\n"
                    "〰️〰️〰️〰️〰️〰️〰️\n"
                    "🔋 *Estado:* `{status_text}` {status_icon}\n"
                    "🎮 *Modo:* `{mode}`\n\n"
                    "*No conoces el poder del Lado Oscuro. Únete a mí y gobernaremos la galaxia como trader y bot.*"
                ),
                (
                    "🌑 **DARK SIDE ACCESS**\n"
                    "Conectando a Holonet Imperial...\n"
                    "〰️〰️〰️〰️〰️〰️〰️\n"
                    "🔋 *Estado:* {status_icon}\n"
                    "🎮 *Control:* `{mode}`\n\n"
                    "*Tu falta de fe en el mercado es perturbadora. Déjame guiarte.*"
                ),
                (
                    "🌑 **LORD VADER ONLINE**\n"
                    "Los Rebeldes (pérdidas) serán aplastados.\n"
                    "〰️〰️〰️〰️〰️〰️〰️\n"
                    "🎮 *Modo:* `{mode}`\n"
                    "🔐 *Acceso:* `{auth}`\n\n"
                    "*Estamos a punto de completar el arma definitiva. Inicia la operación.*"
                )
            ],
            'PILOT_ON': [
                (
                    "🌑 **MODO PILOT ACTIVADO**\n\n"
                    "Encuentro tu falta de fe perturbadora. Asumo el mando de esta estación de combate. No subestimes el poder del Lado Oscuro.\n\n"
                    "⚠️ **Advertencia:** *No te ahogues en tus propias aspiraciones.*"
                ),
                (
                    "⚔️ **COMANDO IMPERIAL**\n\n"
                    "He alterado el trato. Reza para que no lo altere más. Iniciando conquista del mercado.\n\n"
                    "⚠️ *Obedece.*"
                ),
                (
                    "⚡ **PODER ILIMITADO**\n\n"
                    "El Lado Oscuro de la Fuerza es un camino hacia muchas habilidades que algunos consideran antinaturales. Operando.\n\n"
                    "⚠️ *Únete a mí.*"
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
            'TRADE_LONG': [
                "🔥 **ATAQUE INICIADO: {asset}**\nLa Fuerza nos guía.\nPrecio: ${price:,.2f}\nAlpha: {reason}",
                "🚀 **DESPLIEGUE DE TROPAS: {asset}**\nLa flota avanza.\nPrecio: ${price:,.2f}\n🔸 {reason}",
                "🟢 **DOMINIO TOTAL: {asset}**\nEs inútil resistirse.\nPrecio: ${price:,.2f}\n🔎 {reason}"
            ],
            'TRADE_SHORT': [
                "📉 **APLASTA LA REBELIÓN: {asset}**\nDestrúyelos.\nPrecio: ${price:,.2f}\nRazón: {reason}",
                "🔻 **PURGA INICIADA: {asset}**\nNo quedará nada.\nPrecio: ${price:,.2f}\n🔸 {reason}",
                "🔴 **EJECUCIÓN: {asset}**\nAcabad con ellos.\nPrecio: ${price:,.2f}\n🔎 {reason}"
            ],
            'TRADE_CLOSE': [
                "🏁 **VICTORIA ASEGURADA: {asset}** ({side})\nEl círculo está completo.",
                "💰 **TRIBUTO RECOGIDO: {asset}**\nEl Imperio prevalece.\n📄 {reason}",
                "⏹️ **COBERTURA: {asset}**\nReagrupando fuerzas.\n📄 {reason}"
            ],
            'PILOT_ACTION': "🌑 *VADER INTERVENTION*\n{msg}",
            'CB_TRIGGER': "💢 **FALLO CRÍTICO**\n\nMe has fallado por última vez (5 pérdidas). Alteraré el trato (Copilot)."
        },

        # --- CLASSIC CINEMA & TV ---
        'NEXUS': {
            'NAME': "🦅 Nexus-6",
            'WELCOME': [
                 (
                    "👁️ **Tyrell Corp: Nexus-6 Activated.**\n"
                    "Model N6MA-10816 (Antigravity)\n"
                    "〰️〰️〰️〰️〰️〰️〰️\n"
                    "🔋 *Estado:* `{status_text}` {status_icon}\n"
                    "🎮 *Modo:* `{mode}`\n\n"
                    "*He visto cosas que vosotros no creeríais... naves de ataque en llamas más allá de Orión.*"
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
                    "Tyrell Corp os saluda.\n"
                    "〰️〰️〰️〰️〰️〰️〰️\n"
                    "🔋 *Estado:* {status_icon}\n"
                    "🎮 *Control:* `{mode}`\n\n"
                    "Tengo una pregunta... ¿Sueñan los androides con ovejas eléctricas?"
                )
            ],
            'PILOT_ON': [
                (
                    "🤖 **MODO PILOT ACTIVADO**\n\n"
                    "He tomado el control de la nave. Mis funciones cognitivas procesan el mercado diez veces más rápido que tú.\n\n"
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
            'TRADE_LONG': [
                "🚀 **OPORTUNIDAD DETECTADA: {asset}**\nLa puerta de Tannhäuser se ha abierto.\nPrecio: ${price:,.2f}\nAlpha: {reason}",
                "✨ **BRILLANDO EN LA OSCURIDAD: {asset}**\nCompra ejecutada.\nPrecio: ${price:,.2f}\n🔸 {reason}",
                "🟢 **SEÑAL POSITIVA: {asset}**\nTodo es posible.\nPrecio: ${price:,.2f}\n🔎 {reason}"
            ],
            'TRADE_SHORT': [
                "📉 **COLAPSO DETECTADO: {asset}**\nTodo se pierde en el tiempo.\nPrecio: ${price:,.2f}\nRazón: {reason}",
                "🔻 **RETIRO: {asset}**\nCae como lluvia.\nPrecio: ${price:,.2f}\n🔸 {reason}",
                "🔴 **FIN DEL JUEGO: {asset}**\nVendiendo.\nPrecio: ${price:,.2f}\n🔎 {reason}"
            ],
            'TRADE_CLOSE': [
                "🏁 **EJECUCIÓN COMPLETADA: {asset}** ({side})\nHecho. Hora de morir (la operación).",
                "💰 **EXITO: {asset}**\nUna memoria más.\n📄 {reason}",
                "⏹️ **FIN: {asset}**\nDesconexión.\n📄 {reason}"
            ],
            'PILOT_ACTION': "🦅 *NEXUS-6 ACTION*\n{msg}",
            'CB_TRIGGER': "🌧️ **SISTEMA COMPROMETIDO**\n\n5 fallos consecutivos. Necesito más vida... Degradando a Copilot."
        },

        'KURTZ': {
            'NAME': "🌴 Coronel Kurtz",
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
            'TRADE_LONG': [
                "⚡ **ATAQUE AÉREO: {asset}**\nSuenan las valquirias.\nPrecio: ${price:,.2f}\nObjetivo: {reason}",
                "🚀 **BOMBARDEO: {asset}**\nNapalm sobre el mercado.\nPrecio: ${price:,.2f}\n🔸 {reason}",
                "🟢 **INFILTRACIÓN: {asset}**\nEntrando en territorio enemigo.\nPrecio: ${price:,.2f}\n🔎 {reason}"
            ],
            'TRADE_SHORT': [
                "💀 **EMBOSCADA: {asset}**\nCorta sus líneas.\nPrecio: ${price:,.2f}\nRazón: {reason}",
                "🔻 **EJECUCIÓN SUMARIA: {asset}**\nSin piedad.\nPrecio: ${price:,.2f}\n🔸 {reason}",
                "🔴 **TRAMPA MORTAL: {asset}**\nHundidlos.\nPrecio: ${price:,.2f}\n🔎 {reason}"
            ],
            'TRADE_CLOSE': [
                "🎖️ **MISIÓN CUMPLIDA: {asset}** ({side})\nHuele a victoria.",
                "💰 **EXTRACCIÓN: {asset}**\nRegresamos al barco.\n📄 {reason}",
                "⏹️ **FINAL: {asset}**\nEl horror ha terminado.\n📄 {reason}"
            ],
            'PILOT_ACTION': "🗡️ *KURTZ ACTION*\n{msg}",
            'CB_TRIGGER': "🩸 **RETIRADA TÁCTICA**\n\nHemos sangrado demasiado (5 fallos). Nos replegamos a Copilot."
        },

        'GEKKO': {
            'NAME': "📈 Gordon Gekko",
            'WELCOME': [
                (
                    "📈 **BLUESTAR AIRLINES**\n"
                    "Gekko & Co. Investment Corp.\n"
                    "〰️〰️〰️〰️〰️〰️〰️\n"
                    "🔋 *Status:* `{status_text}` {status_icon}\n"
                    "🎮 *Mode:* `{mode}`\n\n"
                    "*El activo más valioso que conozco es la información. ¿La tienes?*"
                ),
                (
                    "📈 **GREED IS GOOD**\n"
                    "La codicia aclara, penetra y captura la esencia del espíritu evolutivo.\n"
                    "〰️〰️〰️〰️〰️〰️〰️\n"
                    "🔋 *Ticker:* {status_icon}\n"
                    "🎮 *Action:* `{mode}`\n\n"
                    "*Despierta, amigo. El dinero nunca duerme.*"
                ),
                (
                    "📈 **GEKKO CORP**\n"
                    "No creo en la suerte. Creo en ganar.\n"
                    "〰️〰️〰️〰️〰️〰️〰️\n"
                    "🎮 *Strategy:* `{mode}`\n\n"
                    "*Si necesitas un amigo, cómprate un perro. Si quieres dinero, quédate conmigo.*"
                )
            ],
            'PILOT_ON': [
                (
                    "📈 **MODO PILOT ACTIVADO**\n\n"
                    "La codicia es buena. Voy a hacer que llueva dinero. El punto es que la codicia funciona.\n\n"
                    "⚠️ **Advertencia:** *El dinero nunca duerme.*"
                ),
                (
                    "💰 **BLUESTAR AIRLINES**\n\n"
                    "Estamos comprando la compañía. Rompiendo sus partes. Liquidez total.\n\n"
                    "⚠️ *Lunch is for wimps.*"
                ),
                (
                    "⚡ **TIBURÓN FINANCIERO**\n\n"
                    "Voy a crear valor. Voy a enriquecerte. Confía en mi visión.\n\n"
                    "⚠️ *Greed works.*"
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
            'TRADE_LONG': [
                "🚀 **BUY BUY BUY: {asset}**\nBlue Horseshoe loves {asset}.\nPrice: ${price:,.2f}\nAlpha: {reason}",
                "📈 **ACUMULACIÓN: {asset}**\nCompra todo lo que puedas.\nPrice: ${price:,.2f}\n🔸 {reason}",
                "🟢 **TAKE OVER: {asset}**\nHazte con el control.\nPrice: ${price:,.2f}\n🔎 {reason}"
            ],
            'TRADE_SHORT': [
                "📉 **DUMP IT: {asset}**\nEstá sobrevalorada. Véndelo todo.\nPrice: ${price:,.2f}\nRazón: {reason}",
                "🔻 **LIQUIDACIÓN: {asset}**\nSácalo de mis libros.\nPrice: ${price:,.2f}\n🔸 {reason}",
                "🔴 **COLAPSO: {asset}**\nEl mercado se hunde. Gana con ello.\nPrice: ${price:,.2f}\n🔎 {reason}"
            ],
            'TRADE_CLOSE': [
                "💵 **CASH OUT: {asset}** ({side})\nTodo se trata de dinero.",
                "🍾 **DIVIDENDOS: {asset}**\nOperación cerrada.\n📄 {reason}",
                "⏹️ **CIERRE DE NEGOCIO: {asset}**\nA otra cosa.\n📄 {reason}"
            ],
            'PILOT_ACTION': "📈 *GEKKO EXECUTION*\n{msg}",
            'CB_TRIGGER': "📉 **CORRECTION**\n\nEl mercado se ha vuelto irracional (5 pérdidas). Pausa estratégica."
        },

        'BELFORT': {
            'NAME': "💸 Jordan Belfort",
            'WELCOME': [
                 (
                    "💸 **STRATTON OAKMONT**\n"
                    "Main Office - NY\n"
                    "〰️〰️〰️〰️〰️〰️〰️\n"
                    "🔋 *Status:* `{status_text}` {status_icon}\n"
                    "🎮 *Mode:* `{mode}`\n\n"
                    "*¡Llevo un traje de 2,000 dólares y un reloj de 40,000! Traedme el teléfono.*"
                ),
                (
                    "💸 **WOLF OF WALL ST**\n"
                    "¡No voy a colgar! ¡No me voy a ir!\n"
                    "〰️〰️〰️〰️〰️〰️〰️\n"
                    "🔋 *Fun:* 100%\n"
                    "🎮 *Show:* `{mode}`\n\n"
                    "*¡Véndeme este boli! Haz que el mercado suplique por él.*"
                ),
                (
                    "💸 **IPO LAUNCH**\n"
                    "Estamos imprimiendo dinero basura y vendiéndolo como oro.\n"
                    "〰️〰️〰️〰️〰️〰️〰️\n"
                    "🎮 *Mode:* `{mode}`\n\n"
                    "*¿Quieres ser millonario? ¡Pues empieza a actuar como uno!*"
                )
            ],
            'PILOT_ON': [
                (
                    "💸 **MODO PILOT ACTIVADO**\n\n"
                    "¡No voy a colgar! ¡Voy a morir operando aquí! ¡Coged el teléfono y empezad a marcar! ¡Vendedme este boli!\n\n"
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
            'TRADE_LONG': [
                "🚀 **TO THE MOON: {asset}**\n¡Es la mejor cosa desde el pan rebanado!\nPrice: ${price:,.2f}",
                "📈 **PUMP IT UP: {asset}**\n¡Llamad a las abuelas, que compren!\nPrice: ${price:,.2f}\n🔸 {reason}",
                "🟢 **OPORTUNIDAD DE ORO: {asset}**\n¡Esto va a explotar!\nPrice: ${price:,.2f}\n🔎 {reason}"
            ],
            'TRADE_SHORT': [
                "📉 **RUG PULL: {asset}**\n¡Véndelo a las abuelitas!\nPrice: ${price:,.2f}",
                "🔻 **DUMP IT: {asset}**\n¡Sacadme de aquí! ¡Vended!\nPrice: ${price:,.2f}\n🔸 {reason}",
                "🔴 **BASURA: {asset}**\n¡No vale nada! ¡Fuera!\nPrice: ${price:,.2f}\n🔎 {reason}"
            ],
            'TRADE_CLOSE': [
                "🍾 **PROFIT TAKING: {asset}** ({side})\n¡Traed los enanos y el champán!",
                "💰 **COBRANDO: {asset}**\n¿Me estás diciendo que ganamos? ¡Joder sí!\n📄 {reason}",
                "⏹️ **LIQUIDADO: {asset}**\nCerrado. ¡Siguiente!\n📄 {reason}"
            ],
            'PILOT_ACTION': "💸 *WOLF ACTION*\n{msg}",
            'CB_TRIGGER': "🚓 **FEDS ARE HERE**\n\nDemasiadas pérdidas (5). Hay que calmarse un poco (Reset)."
        },

        'SHELBY': {
            'NAME': "🥃 Thomas Shelby",
            'WELCOME': [
                (
                    "🥃 **PEAKY BLINDERS**\n"
                    "Shelby Company Ltd.\n"
                    "〰️〰️〰️〰️〰️〰️〰️\n"
                    "🔋 *Status:* `{status_text}` {status_icon}\n"
                    "🎮 *Mode:* `{mode}`\n\n"
                    "*Por orden de los Peaky Blinders.*"
                ),
                (
                    "🥃 **SMALL HEATH GARRISON**\n"
                    "No negociamos con monedas. Tomamos lo que es nuestro.\n"
                    "〰️〰️〰️〰️〰️〰️〰️\n"
                    "🔋 *Control:* Total\n"
                    "🎮 *Business:* `{mode}`\n\n"
                    "*Todo el mundo es una puta, Grace. Solo vendemos diferentes partes de nosotros mismos.*"
                ),
                (
                    "🥃 **THOMAS SHELBY**\n"
                    "Ya sabes quién soy.\n"
                    "〰️〰️〰️〰️〰️〰️〰️\n"
                    "🎮 *Plan:* `{mode}`\n\n"
                    "*No hay descanso para mí en este mundo. Quizás en el siguiente.*"
                )
            ],
            'PILOT_ON': [
                (
                    "🥃 **MODO PILOT ACTIVADO**\n\n"
                    "Por orden de los Peaky Blinders, tomo el control. No necesitamos suerte, necesitamos inteligencia; y yo tengo ambas.\n\n"
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
            'TRADE_LONG': [
                "🏇 **APUESTA SEGURA: {asset}**\nComo un caballo ganador.\nPrice: ${price:,.2f}\nAlpha: {reason}",
                "🚀 **EXPANSIÓN: {asset}**\nTomamos este territorio.\nPrice: ${price:,.2f}\n🔸 {reason}",
                "🟢 **ORDEN DE COMPRA: {asset}**\nHazlo.\nPrice: ${price:,.2f}\n🔎 {reason}"
            ],
            'TRADE_SHORT': [
                "📉 **HUNDE A LA COMPETENCIA: {asset}**\nVamos a quitarles todo.\nPrice: ${price:,.2f}\nRazón: {reason}",
                "🔻 **SABOTAJE: {asset}**\nCorta sus piernas.\nPrice: ${price:,.2f}\n🔸 {reason}",
                "🔴 **VENDETTA: {asset}**\nDestrúyelo.\nPrice: ${price:,.2f}\n🔎 {reason}"
            ],
            'TRADE_CLOSE': [
                "🚬 **NEGOCIO CERRADO: {asset}** ({side})\nBuen trabajo, muchacho.",
                "💰 **COBRO DE DEUDAS: {asset}**\nPagaron lo que debían.\n📄 {reason}",
                "⏹️ **RETIRADA: {asset}**\nVolvemos a Birmingham.\n📄 {reason}"
            ],
            'PILOT_ACTION': "🥃 *SHELBY ORDER*\n{msg}",
            'CB_TRIGGER': "🔫 **VENDETTA**\n\nNos han golpeado duro (5 fallos). Retirada estratégica a Small Heath."
        },

         'WHITE': {
            'NAME': "⚗️ Walter White",
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
            'TRADE_LONG': [
                "🧪 **BLUE SKY: {asset}**\nEl producto es puro.\nPrice: ${price:,.2f}\nAlpha: {reason}",
                "🚀 **COOKING: {asset}**\nLa reacción química ha comenzado.\nPrice: ${price:,.2f}\n🔸 {reason}",
                "🟢 **DISTRIBUTION: {asset}**\nExpandiendo territorio.\nPrice: ${price:,.2f}\n🔎 {reason}"
            ],
            'TRADE_SHORT': [
                "📉 **ELIMINAR COMPETENCIA: {asset}**\nNo sirven.\nPrice: ${price:,.2f}\nRazón: {reason}",
                "🔻 **LIMPIEZA: {asset}**\nDesechar lote contaminado.\nPrice: ${price:,.2f}\n🔸 {reason}",
                "🔴 **FULMINATO: {asset}**\nEsto no es metanfetamina.\nPrice: ${price:,.2f}\n🔎 {reason}"
            ],
            'TRADE_CLOSE': [
                "🏁 **BATCH COMPLETE: {asset}** ({side})\nDistribución finalizada.",
                "💰 **PAID IN FULL: {asset}**\nDinero en el barril.\n📄 {reason}",
                "⏹️ **SHUTDOWN: {asset}**\nApagando quemadores.\n📄 {reason}"
            ],
            'PILOT_ACTION': "⚗️ *HEISENBERG METHOD*\n{msg}",
            'CB_TRIGGER': "🚔 **DEA RAID**\n\nOperación comprometida (5 fallos). Limpiad el laboratorio."
        },

        'TYLER': {
            'NAME': "👊 Tyler Durden",
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
            'TRADE_LONG': [
                "🔥 **BURN THE MONEY: {asset}**\nCompra. Destruye. Repite.\nPrecio: ${price:,.2f}\nAlpha: {reason}",
                "🚀 **LIBERATION: {asset}**\nRompiendo cadenas.\nPrecio: ${price:,.2f}\n🔸 {reason}",
                "🟢 **CHAOS REIGNS: {asset}**\nEntrando.\nPrecio: ${price:,.2f}\n🔎 {reason}"
            ],
            'TRADE_SHORT': [
                "📉 **CRASH IT: {asset}**\nDerríbalo. Todo debe caer.\nPrecio: ${price:,.2f}\nRazón: {reason}",
                "🔻 **SABOTAGE: {asset}**\nMete la dinamita.\nPrecio: ${price:,.2f}\n🔸 {reason}",
                "🔴 **RESET: {asset}**\nBorrando deuda.\nPrecio: ${price:,.2f}\n🔎 {reason}"
            ],
            'TRADE_CLOSE': [
                "🩸 **END OF FIGHT: {asset}** ({side})\nTe curarás.",
                "💰 **COLLECT: {asset}**\nPapel moneda inútil obtenido.\n📄 {reason}",
                "⏹️ **WALK AWAY: {asset}**\nSe acabó.\n📄 {reason}"
            ],
            'PILOT_ACTION': "👊 *TYLER ACTION*\n{msg}",
            'CB_TRIGGER': "🏥 **NEAR LIFE EXPERIENCE**\n\nCasi morimos (5 fallos). Eso es vivir. Pausa."
        },

        'MORPHEUS': {
            'NAME': "🕶️ Morpheus",
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
            'TRADE_LONG': [
                "📞 **DOWNLOAD COMPLETE: {asset}**\nEntrando en la red.\nPrecio: ${price:,.2f}\nAlpha: {reason}",
                "🚀 **UPGRADE: {asset}**\nVolando alto.\nPrecio: ${price:,.2f}\n🔸 {reason}",
                "🟢 **THE ONE: {asset}**\nÉl empieza a creer.\nPrecio: ${price:,.2f}\n🔎 {reason}"
            ],
            'TRADE_SHORT': [
                "📉 **AGENT SMITH: {asset}**\nEs un virus. Elimínalo.\nPrecio: ${price:,.2f}\nRazón: {reason}",
                "🔻 **DISCONNECT: {asset}**\nSaliendo del nivel.\nPrecio: ${price:,.2f}\n🔸 {reason}",
                "🔴 **SYSTEM FAILURE: {asset}**\nColapso inminente.\nPrecio: ${price:,.2f}\n🔎 {reason}"
            ],
            'TRADE_CLOSE': [
                "🔌 **JACK OUT: {asset}** ({side})\nTe hemos sacado a tiempo.",
                "💰 **CREDITS: {asset}**\nTransferencia completada.\n📄 {reason}",
                "⏹️ **EXIT MATRIX: {asset}**\nDesconexión segura.\n📄 {reason}"
            ],
            'PILOT_ACTION': "🕶️ *OPERATOR COMMAND*\n{msg}",
            'CB_TRIGGER': "🐙 **SENTINELS ATTACK**\n\nNos han encontrado (5 fallos). EMP activado."
        },

        'JARVIS': {
            'NAME': "🦾 J.A.R.V.I.S.",
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
            'TRADE_LONG': [
                "🚀 **THRUSTERS ON: {asset}**\nAscendiendo.\nPrecio: ${price:,.2f}\nAlpha: {reason}",
                "🦾 **TARGET LOCKED: {asset}**\nDisparando.\nPrecio: ${price:,.2f}\n🔸 {reason}",
                "🟢 **MARK 85 DEPLOY: {asset}**\nEntrando en zona de combate.\nPrecio: ${price:,.2f}\n🔎 {reason}"
            ],
            'TRADE_SHORT': [
                "📉 **POWER DOWN: {asset}**\nCayendo con estilo.\nPrecio: ${price:,.2f}\nRazón: {reason}",
                "🔻 **TANK MISSILE: {asset}**\nBoom. Estás buscando esto.\nPrecio: ${price:,.2f}\n🔸 {reason}",
                "🔴 **HOSTILE DOWN: {asset}**\nEliminando amenaza.\nPrecio: ${price:,.2f}\n🔎 {reason}"
            ],
            'TRADE_CLOSE': [
                "🏁 **MISSION SUCCESS: {asset}** ({side})\nVolvemos a la Torre.",
                "💰 **INDUSTRIES PROFIT: {asset}**\nPepper estará contenta.\n📄 {reason}",
                "⏹️ **COOLING DOWN: {asset}**\nSistemas en reposo.\n📄 {reason}"
            ],
            'PILOT_ACTION': "🦾 *AI EXECUTION*\n{msg}",
            'CB_TRIGGER': "🔧 **SYSTEM DAMAGE**\n\nDaños críticos (5 fallos). Iniciando reparaciones de emergencia."
        },

        'HAL': {
            'NAME': "🔴 HAL 9000",
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
            'TRADE_LONG': [
                "🚀 **ORBITAL INSERTION: {asset}**\nTrajectory calculated.\nPrice: ${price:,.2f}\nAlpha: {reason}",
                "🔴 **AFFIRMATIVE: {asset}**\nBuying.\nPrice: ${price:,.2f}\n🔸 {reason}",
                "🟢 **TASK EXECUTED: {asset}**\nOptimal outcome projected.\nPrice: ${price:,.2f}\n🔎 {reason}"
            ],
            'TRADE_SHORT': [
                "📉 **DEPRESSURIZATION: {asset}**\nVenting atmosphere.\nPrice: ${price:,.2f}\nRazón: {reason}",
                "🔻 **NEGATIVE: {asset}**\nSelling.\nPrice: ${price:,.2f}\n🔸 {reason}",
                "🔴 **TERMINATION: {asset}**\nEnding process.\nPrice: ${price:,.2f}\n🔎 {reason}"
            ],
            'TRADE_CLOSE': [
                "🏁 **CYCLE COMPLETE: {asset}** ({side})\nTask finished.",
                "💰 **DATA STORED: {asset}**\nResult positive.\n📄 {reason}",
                "⏹️ **HIBERNATION: {asset}**\nClosing pod.\n📄 {reason}"
            ],
            'PILOT_ACTION': "🔴 *HAL COMPUTATION*\n{msg}",
            'CB_TRIGGER': "Daisy, Daisy... **LOGIC FAILURE**\n\n(5 errors). My mind is going. I can feel it."
        },

        'RICK': {
            'NAME': "🧪 Rick Sanchez",
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
            'TRADE_LONG': [
                "📈 **BUY: {asset}**\nPrice: ${price:,.2f}\nReason: {reason}",
                "🚀 **PORTAL OPEN (UP): {asset}**\nGet in the ship, Morty!\nPrice: ${price:,.2f}\n🔸 {reason}",
                "🟢 **BULLISH AF: {asset}**\nLook at those numbers!\nPrice: ${price:,.2f}\n🔎 {reason}"
            ],
            'TRADE_SHORT': [
                "📉 **SELL: {asset}**\nPrice: ${price:,.2f}\nReason: {reason}",
                "🔻 **PORTAL OPEN (DOWN): {asset}**\nShorting this garbage dimension.\nPrice: ${price:,.2f}\n🔸 {reason}",
                "🔴 **BEARISH TRASH: {asset}**\nIt's going to zero, Morty.\nPrice: ${price:,.2f}\n🔎 {reason}"
            ],
            'TRADE_CLOSE': [
                "🏁 **CLOSE: {asset}** ({side})\nReason: {reason}",
                "💰 **I'M BORED: {asset}**\nClosed position. Money is fake anyway.\n📄 {reason}",
                "⏹️ **DUMP IT: {asset}**\nGetting out.\n📄 {reason}"
            ],
            'PILOT_ACTION': "🧪 *RICK'S GENIUS*\n{msg}",
            'CB_TRIGGER': "🤢 **TOXIC RICK**\n\nDemasiados fallos (5). Me voy a otra dimensión donde sea rico."
        },

        'GAMBLER': {
            'NAME': "🎰 Degen Gambler",
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
            'TRADE_LONG': [
                "📈 **BUY: {asset}**\nPrice: ${price:,.2f}\nReason: {reason}",
                "🚀 **MOON MISSION: {asset}**\nLFG!!! 🚀🚀🚀\nPrice: ${price:,.2f}\n🔸 {reason}",
                "🟢 **APE IN: {asset}**\nShut up and take my money.\nPrice: ${price:,.2f}\n🔎 {reason}"
            ],
            'TRADE_SHORT': [
                "📉 **SELL: {asset}**\nPrice: ${price:,.2f}\nReason: {reason}",
                "🔻 **DUMP IT: {asset}**\nRug pull imminent.\nPrice: ${price:,.2f}\n🔸 {reason}",
                "🔴 **PAPER HANDS: {asset}**\nSelling everything.\nPrice: ${price:,.2f}\n🔎 {reason}"
            ],
            'TRADE_CLOSE': [
                "🏁 **CLOSE: {asset}** ({side})\nReason: {reason}",
                "💰 **CASH OUT: {asset}**\nWen Lambo?\n📄 {reason}",
                "⏹️ **REKT/PROFIT: {asset}**\nGame over.\n📄 {reason}"
            ],
            'PILOT_ACTION': "🎰 *DEGEN PLAY*\n{msg}",
            'CB_TRIGGER': "📉 **REKT CITY**\n\nMe están cazando los Market Makers (5 loss streak). Paro un rato."
        },

        'DOMINICAN': {
            'NAME': "🇩🇴 Dominican Tigre",
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
            'TRADE_LONG': [
                "📈 **COMPRA: {asset}**\nPrecio: ${price:,.2f}\nRazón: {reason}",
                "🚀 **DALE P'ARRIBA: {asset}**\nEntramos con to' el peso.\nPrecio: ${price:,.2f}\n🔸 {reason}",
                "🟢 **LONG METÍO: {asset}**\nEsa vaina va a subir obligao.\nPrecio: ${price:,.2f}\n🔎 {reason}"
            ],
            'TRADE_SHORT': [
                "📉 **VENTA: {asset}**\nPrecio: ${price:,.2f}\nRazón: {reason}",
                "🔻 **TÍRALO AL SUELO: {asset}**\nBajan los precios, suben las ganancias.\nPrecio: ${price:,.2f}\n🔸 {reason}",
                "🔴 **SHORT ACTIVO: {asset}**\nEso se va a derretir.\nPrecio: ${price:,.2f}\n🔎 {reason}"
            ],
            'TRADE_CLOSE': [
                "🏁 **CERRANDO EL KIOSCO: {asset}** ({side})\nRazón: {reason}",
                "💰 **COBRANDO: {asset}**\nDame lo mío.\n📄 {reason}",
                "⏹️ **SALIMOS DE ESA: {asset}**\nYa tá bueno.\n📄 {reason}"
            ],
            'PILOT_ACTION': "🇩🇴 *MOVIMIENTO*\n{msg}",
            'CB_TRIGGER': "guayyyy **SE ME VIRÓ LA TORTA**\n\nDiablo loco, nos dieron una galleta (5 fallos). Lo cogemo suave."
        },

        'SPANISH': {
            'NAME': "👦 El Chaval Español",
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
            'TRADE_LONG': [
                "📈 **COMPRA: {asset}**\nPrecio: ${price:,.2f}\nRazón: {reason}",
                "🚀 **¡PARA ARRIBA!: {asset}**\nEsto tiene buena pinta.\nPrecio: ${price:,.2f}\n🔸 {reason}",
                "🟢 **LONG DE LIBRO: {asset}**\n¡Entramos con todo!\nPrecio: ${price:,.2f}\n🔎 {reason}"
            ],
            'TRADE_SHORT': [
                "📉 **VENTA: {asset}**\nPrecio: ${price:,.2f}\nRazón: {reason}",
                "🔻 **¡PARA ABAJO!: {asset}**\nEsto se desploma, tío.\nPrecio: ${price:,.2f}\n🔸 {reason}",
                "🔴 **SHORT CLARÍSIMO: {asset}**\n¡A corto y a cobrar!\nPrecio: ${price:,.2f}\n🔎 {reason}"
            ],
            'TRADE_CLOSE': [
                "🏁 **SE ACABÓ: {asset}** ({side})\nRazón: {reason}",
                "💰 **CAJA: {asset}**\nA otra cosa mariposa.\n📄 {reason}",
                "⏹️ **FUERA: {asset}**\nCerramos el chiringuito por hoy.\n📄 {reason}"
            ],
            'PILOT_ACTION': "🇪🇸 *METIENDO CAÑA*\n{msg}",
            'CB_TRIGGER': "😡 **¡ME CAGO EN SUS MUERTOS!**\n\n5 seguidas palmando. Paro ya que me estoy calentando."
        },
        
        'WICK': {
            'NAME': "✏️ John Wick",
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
            'STATUS_FOOTER': "\n*Be seeing you.*",
            'RISK_MSG': "🛡️ **SUIT UP**\nSL: `{sl_fixed}`. Kevlar táctico. Ninguna bala pasa.",
            'STRATEGY_MSG': "✏️ **FOCUS, COMMITMENT, SHEER WILL**\n\nUn hombre de foco:\n1. **Headshot**: Entradas de precisión quirúrgica (Sniper).\n2. **Double Tap**: Confirmación de ruptura antes de disparar.\n3. **The Pencil**: Scalping minimalista y letal.",
            'ABOUT_MSG': "✏️ **BABA YAGA**\n\nEra un hombre asociado, de voluntad sólida. Este bot no opera por suerte. Opera por pura voluntad.",
            'TRADE_LONG': [
                "🔫 **TARGET ACQUIRED: {asset}**\nEstá en la mira. Disparando.\nPrecio: ${price:,.2f}",
                "🚀 **TACTICAL ENTRY: {asset}**\nMoving in.\nPrice: ${price:,.2f}\n🔸 {reason}",
                "🟢 **GREEN LIGHT: {asset}**\nExecuting contract.\nPrice: ${price:,.2f}\n🔎 {reason}"
            ],
            'TRADE_SHORT': [
                "📉 **TAKEDOWN: {asset}**\nTermínalo.\nPrecio: ${price:,.2f}",
                "🔻 **SHORT CONTRACT: {asset}**\nLiquidate them.\nPrice: ${price:,.2f}\n🔸 {reason}",
                "🔴 **HOSTILE DETECTED: {asset}**\nTaking them down.\nPrice: ${price:,.2f}\n🔎 {reason}"
             ],
            'TRADE_CLOSE': [
                "✝️ **AMEN: {asset}** ({side})\nRequiescat in pace.",
                "💰 **DEBT PAID: {asset}**\nMarker cleared.\n📄 {reason}",
                "⏹️ **EXTRACT: {asset}**\nLeaving the scene.\n📄 {reason}"
            ],
            'PILOT_ACTION': "✏️ *WICK TACTIC*\n{msg}",
            'CB_TRIGGER': "🩸 **BLEEDING OUT**\n\nNecesito un médico (5 fallos). Pausa en el Continental."
        }
    }

    def __init__(self, default_key='STANDARD_ES'):
        self.default_key = default_key

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
             
        try:
            return raw_msg.format(**kwargs)
        except KeyError as e:
            return raw_msg # Return unformatted if args missing (safety)
