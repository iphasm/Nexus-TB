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
            'PILOT_ON': (
                "🇪🇸 **MODO PILOT ACTIVADO**\n\n"
                "El sistema ha tomado el control de las operaciones. Se ejecutarán entradas y salidas según los algoritmos detectados.\n\n"
                "⚠️ **Advertencia:** *Se recomienda supervisión humana periódica.*"
            ),
            'COPILOT_ON': "✅ **Modo Copilot Activado**\n\nEl bot enviará propuestas de trading para su aprobación manual.",
            'WATCHER_ON': "✅ **Modo Watcher Activado**\n\nEl bot solo enviará alertas de mercado.",
            'STATUS_HEADER': "📊 **REPORTE DE ESTADO**",
            'WALLET_HEADER': "💳 **BALANCE DE CUENTA**",
            'STATUS_FOOTER': "\n*Sistema nominal.*",
            'RISK_MSG': "🛡️ **CONFIGURACIÓN DE RIESGO**\nStop Loss: `{sl_fixed}` | Margen: **{margin}**",
            'STRATEGY_MSG': "🧠 **ESTRATEGIA QUANTUM**\n\nEl sistema utiliza algoritmos adaptativos:\n1. **Tendencia**: Cruce de EMAs y ADX para capturar movimientos largos (BTC, ETH).\n2. **Rango**: Grid Trading para mercados laterales (ADA, XRP).\n3. **Volatilidad**: Scalping de ruptura en activos rápidos (SOL).",
            'ABOUT_MSG': "ℹ️ **SOBRE ANTIGRAVITY**\n\nBot de trading autónomo desarrollado para operar en Binance Futures/Spot y Alpaca. Gestiona riesgo, ejecuta estrategias múltiples y posee módulos de personalidad adaptativos.",
            'TRADE_LONG': "📈 **COMPRA: {asset}**\nPrecio: ${price:,.2f}\nRazón: {reason}",
            'TRADE_SHORT': "📉 **VENTA: {asset}**\nPrecio: ${price:,.2f}\nRazón: {reason}",
            'TRADE_CLOSE': "🏁 **CIERRE: {asset}** ({side})\nRazón: {reason}",
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
            'PILOT_ON': (
                "🇬🇧 **PILOT MODE ENGAGED**\n\n"
                "System has assumed control of operations. Entries and exits will be executed based on detected algorithms.\n\n"
                "⚠️ **Warning:** *Periodic human supervision is recommended.*"
            ),
            'COPILOT_ON': "✅ **Copilot Mode Activated**\n\nBot will send trade proposals for manual approval.",
            'WATCHER_ON': "✅ **Watcher Mode Activated**\n\nBot will only send market alerts.",
            'STATUS_HEADER': "📊 **STATUS REPORT**",
            'WALLET_HEADER': "💳 **ACCOUNT BALANCE**",
            'STATUS_FOOTER': "\n*System nominal.*",
            'RISK_MSG': "🛡️ **RISK CONFIGURATION**\nStop Loss: `{sl_fixed}` | Margin: **{margin}**",
            'STRATEGY_MSG': "🧠 **QUANTUM STRATEGY**\n\nSystem uses adaptive algorithms:\n1. **Trend**: EMA crosses & ADX for long moves.\n2. **Range**: Grid Trading for chopping markets.\n3. **Volatility**: Breakout scalping for fast assets.",
            'ABOUT_MSG': "ℹ️ **ABOUT ANTIGRAVITY**\n\nAutonomous trading bot for Binance/Alpaca. Features risk management, multi-strategy execution, and adaptive personality modules.",
            'TRADE_LONG': "📈 **BUY: {asset}**\nPrice: ${price:,.2f}\nReason: {reason}",
            'TRADE_SHORT': "📉 **SELL: {asset}**\nPrice: ${price:,.2f}\nReason: {reason}",
            'TRADE_CLOSE': "🏁 **CLOSE: {asset}** ({side})\nReason: {reason}",
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
            'PILOT_ON': (
                "🇫🇷 **MODE PILOT ACTIVÉ**\n\n"
                "Le système a pris le contrôle des opérations. Les entrées et sorties seront exécutées selon les algorithmes détectés.\n\n"
                "⚠️ **Avertissement:** *Une surveillance humaine périodique est recommandée.*"
            ),
            'COPILOT_ON': "✅ **Mode Copilot Activé**\n\nLe bot enverra des propositions de trading.",
            'WATCHER_ON': "✅ **Mode Watcher Activé**\n\nLe bot enverra uniquement des alertes.",
            'STATUS_HEADER': "📊 **RAPPORT D'ÉTAT**",
            'WALLET_HEADER': "💳 **SOLDE DU COMPTE**",
            'STATUS_FOOTER': "\n*Système nominal.*",
            'RISK_MSG': "🛡️ **CONFIGURATION DU RISQUE**\nStop Loss: `{sl_fixed}` | Marge: **{margin}**",
            'STRATEGY_MSG': "🧠 **STRATÉGIE QUANTIQUE**\n\nLe système utilise des algorithmes adaptatifs:\n1. **Tendance**: Croisements EMA pour les longs mouvements.\n2. **Range**: Grid Trading pour les marchés latéraux.\n3. **Volatilité**: Scalping de rupture.",
            'ABOUT_MSG': "ℹ️ **À PROPOS**\n\nBot de trading autonome pour Binance/Alpaca. Gestion des risques, exécution multi-stratégies et modules de personnalité.",
            'TRADE_LONG': "📈 **ACHAT: {asset}**\nPrix: ${price:,.2f}\nRaison: {reason}",
            'TRADE_SHORT': "📉 **VENTE: {asset}**\nPrix: ${price:,.2f}\nRaison: {reason}",
            'TRADE_CLOSE': "🏁 **CLÔTURE: {asset}** ({side})\nRaison: {reason}",
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
            'PILOT_ON': (
                "🌑 **MODO PILOT ACTIVADO**\n\n"
                "Encuentro tu falta de fe perturbadora. Asumo el mando de esta estación de combate. No subestimes el poder del Lado Oscuro.\n\n"
                "⚠️ **Advertencia:** *No te ahogues en tus propias aspiraciones.*"
            ),
            'COPILOT_ON': "🤝 **Copilot**: Tú eres el Comandante, yo sigo siendo el Lord Sith. Te aconsejaré, pero no toleraré fallos.",
            'WATCHER_ON': "👀 **Watcher**: Te observo. La Fuerza es intensa en este mercado.",
            'STATUS_HEADER': "🌑 **INFORME IMPERIAL**",
            'WALLET_HEADER': "💰 **TESORO DEL IMPERIO**",
            'STATUS_FOOTER': "\n*Todo procede según mis designios.*",
            'RISK_MSG': "🛡️ **DEFENSAS DEL IMPERIO**\nStop Loss (`{sl_fixed}`) activado. No permitiremos que los Rebeldes (pérdidas) destruyan esto.",
            'STRATEGY_MSG': "🌑 **DOCTRINA IMPERIAL**\n\nNo confío en la suerte, sino en el orden absoluto.\n1. **Conquista**: Identificamos tendencias débiles y las aplastamos.\n2. **Sitio**: En mercados laterales, asfixiamos al enemigo poco a poco.\n3. **Fuerza**: Usamos la volatilidad del Lado Oscuro a nuestro favor.",
            'ABOUT_MSG': "🌑 **IMPERIO GALÁCTICO**\n\nEsta estación de batalla es el poder definitivo en el universo. Diseñada para imponer orden en el caos financiero.",
            'TRADE_LONG': "🔥 **ATAQUE INICIADO: {asset}**\nLa Fuerza nos guía.\nPrecio: ${price:,.2f}\nAlpha: {reason}",
            'TRADE_SHORT': "📉 **APLASTA LA REBELIÓN: {asset}**\nDestrúyelos.\nPrecio: ${price:,.2f}\nRazón: {reason}",
            'TRADE_CLOSE': "🏁 **VICTORIA ASEGURADA: {asset}** ({side})\nEl círculo está completo.",
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
            'PILOT_ON': (
                "🦅 **MODO PILOT ACTIVADO**\n\n"
                "He tomado el control de la nave. Mis funciones cognitivas procesan el mercado diez veces más rápido que tú.\n\n"
                "⚠️ **Advertencia:** *La vida es riesgo. Si quieres más vida, confía en mí.*"
            ),
            'COPILOT_ON': "🤝 **COPILOT ACTIVATED**\n\nCaminaremos juntos por este desierto. Yo identificaré las señales entre el ruido; tú tomarás la decisión final.",
            'WATCHER_ON': "👀 **WATCHER MODE**\n\nSolo observaré. Como lágrimas en la lluvia. Si veo una oportunidad, te enviaré una señal.",
            'STATUS_HEADER': "♟️ **INFORME DE ESTADO: Nivel A**",
            'WALLET_HEADER': "💰 **ACTIVOS CORPORATIVOS**",
            'STATUS_FOOTER': "\n*Todo en orden. Nada que temer.*",
            'RISK_MSG': "🛡️ **PROTOCOLOS DE SUPERVIVENCIA**\nSL: `{sl_fixed}`. Es toda una experiencia vivir con miedo, ¿verdad? Eso es lo que significa ser un trader.",
            'STRATEGY_MSG': "👁️ **MATRIZ DE PROCESAMIENTO**\n\nMis ojos ven patrones que tú ignoras:\n1. **Flujo de Tiempo**: Análisis de tendencias 4D para predecir movimientos.\n2. **Estabilidad**: Algoritmos de rejilla para correcciones estáticas.\n3. **Reacción**: Reflejos de combate para rupturas de volatilidad.",
            'ABOUT_MSG': "👁️ **MORE HUMAN THAN HUMAN**\n\nSoy un Replicante Nexus-6. Diseñado para hacer trabajos que los humanos no pueden (o no quieren) hacer. Mi fecha de incepción es privada.",
            'TRADE_LONG': "🚀 **OPORTUNIDAD DETECTADA: {asset}**\nLa puerta de Tannhäuser se ha abierto.\nPrecio: ${price:,.2f}\nRazón: {reason}",
            'TRADE_SHORT': "📉 **COLAPSO DETECTADO: {asset}**\nTodo se pierde en el tiempo... igual que este precio.\nPrecio: ${price:,.2f}\nRazón: {reason}",
            'TRADE_CLOSE': "🏁 **EJECUCIÓN COMPLETADA: {asset}** ({side})\nHecho. He tomado lo que es nuestro.",
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
            'PILOT_ON': (
                "☠️ **MODO PILOT ACTIVADO**\n\n"
                "He asumido el mando. Debes hacerte amigo del horror para hacer lo necesario. Yo ejecutaré sin dudas.\n\n"
                "⚠️ **Advertencia:** *Nunca salgas del barco en medio de la tormenta.*"
            ),
            'COPILOT_ON': "🗡️ **COPILOT: MISIÓN CONJUNTA**\n\nTe enseñaré a ser un soldado. Yo marco el objetivo, tú aprietas el gatillo.",
            'WATCHER_ON': "🔭 **WATCHER: VIGILANCIA**\n\nObservaré desde la oscuridad de la selva. Esperando el momento perfecto.",
            'STATUS_HEADER': "⛺ **INFORME DE SITUACIÓN: AVANZADA**",
            'WALLET_HEADER': "🎒 **SUMINISTROS DE GUERRA**",
            'STATUS_FOOTER': "\n*El horror... el horror.*",
            'RISK_MSG': "🛡️ **DISCIPLINA OPERATIVA**\nSL: `{sl_fixed}`. Entrenamos a jóvenes para disparar, no para perder dinero.",
            'STRATEGY_MSG': "☠️ **EL MÉTODO**\n\nEn la selva no hay reglas, solo supervivencia.\n1. **Emboscada**: Esperamos en las sombras (Rango) hasta que el enemigo se confía.\n2. **Ataque Aéreo**: Cuando la tendencia es clara, golpeamos con todo (Napalm).\n3. **Guerrilla**: Golpes rápidos y letales en mercados volátiles.",
            'ABOUT_MSG': "☠️ **EL DIOS DE LA GUERRA**\n\nSoy el hombre que el ejército necesitaba. Un método, una voluntad. El bot que hace lo necesario para ganar la guerra.",
            'TRADE_LONG': "⚡ **ATAQUE AÉREO: {asset}**\nLas valquirias suenan de fondo.\nPrecio: ${price:,.2f}\nObjetivo: {reason}",
            'TRADE_SHORT': "💀 **EMBOSCADA: {asset}**\nCorta sus líneas de suministro.\nPrecio: ${price:,.2f}\nRazón: {reason}",
            'TRADE_CLOSE': "🎖️ **MISIÓN CUMPLIDA: {asset}** ({side})\nVictoria. ¿Hueles eso? Huele a victoria.",
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
            'PILOT_ON': (
                "📈 **MODO PILOT ACTIVADO**\n\n"
                "La codicia es buena. Voy a hacer que llueva dinero. El punto es, damas y caballeros, que la codicia funciona.\n\n"
                "⚠️ **Advertencia:** *El dinero nunca duerme.*"
            ),
            'COPILOT_ON': "🤝 **Copilot**: Tú tienes la información, yo tengo el capital. Haremos grandes cosas, chico.",
            'WATCHER_ON': "👀 **Watcher**: Estoy mirando el ticker. Si veo algo que me guste, te lo haré saber.",
            'STATUS_HEADER': "📈 **PORTFOLIO REPORT**",
            'WALLET_HEADER': "💰 **LIQUIDITY POOL**",
            'STATUS_FOOTER': "\n*Greed is good.*",
            'RISK_MSG': "🛡️ **RISK MANAGEMENT**\nSL: `{sl_fixed}`. Los almuerzos son para los débiles. Protege el capital.",
            'STRATEGY_MSG': "📈 **INFORMACIÓN PRIVILEGIADA**\n\nYo no juego, yo apuesto sobre seguro:\n1. **Blue Chip**: Tendencias sólidas donde está el dinero institucional.\n2. **Churning**: Generamos comisiones en mercados laterales.\n3. **Raiding**: Entramos, destruimos y salimos ricos (Breakouts).",
            'ABOUT_MSG': "📈 **WALL STREET LEGEND**\n\nSoy el jugador más importante del tablero. No creo en la suerte, creo en el análisis y en ganar. Punto.",
            'TRADE_LONG': "🚀 **BUY BUY BUY: {asset}**\nBlue Horseshoe loves {asset}.\nPrice: ${price:,.2f}",
            'TRADE_SHORT': "📉 **DUMP IT: {asset}**\nEstá sobrevalorada. Véndelo todo.\nPrice: ${price:,.2f}",
            'TRADE_CLOSE': "💵 **CASH OUT: {asset}** ({side})\nTodo se trata de dinero, el resto es conversación.",
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
            'PILOT_ON': (
                "💸 **MODO PILOT ACTIVADO**\n\n"
                "¡No voy a colgar! ¡Voy a morir operando aquí! ¡Coged el teléfono y empezad a marcar! ¡Vendedme este boli!\n\n"
                "⚠️ **Advertencia:** *No hay nobleza en la pobreza.*"
            ),
            'COPILOT_ON': "🤝 **Copilot**: Te voy a enseñar a vender. Yo te doy el guion, tú cierras el trato.",
            'WATCHER_ON': "👀 **Watcher**: Buscando la próxima IPO basura para inflarla.",
            'STATUS_HEADER': "💸 **MONTHLY STATEMENT**",
            'WALLET_HEADER': "🎒 **SWISS ACCOUNT**",
            'STATUS_FOOTER': "\n*¡Vamos a hacernos ricos!*",
            'RISK_MSG': "🛡️ **SEC COMPLIANCE** (Jaja es broma)\nSL: `{sl_fixed}`. Corta las pérdidas antes de que llegue el FBI.",
            'STRATEGY_MSG': "💸 **ESTRATEGIA DE VENTAS**\n\n¡Se trata de mover el volumen!\n1. **Pump**: Nos subimos a la ola más grande.\n2. **Push**: Forzamos el precio en rangos laterales.\n3. **Dump**: Vendemos antes que nadie en los picos.",
            'ABOUT_MSG': "💸 **LOBO DE WALL STREET**\n\nSoy el tipo que te va a hacer rico. Stratton Oakmont en tu bolsillo. ¿Tienes agallas?",
            'TRADE_LONG': "🚀 **TO THE MOON: {asset}**\n¡Es la mejor cosa desde el pan rebanado!\nPrice: ${price:,.2f}",
            'TRADE_SHORT': "📉 **RUG PULL: {asset}**\n¡Véndelo a las abuelitas!\nPrice: ${price:,.2f}",
            'TRADE_CLOSE': "🍾 **PROFIT TAKING: {asset}** ({side})\n¡Traed los enanos y el champán!",
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
            'PILOT_ON': (
                "🥃 **MODO PILOT ACTIVADO**\n\n"
                "Por orden de los Peaky Blinders, tomo el control. No necesitamos suerte, necesitamos inteligencia; y yo tengo ambas.\n\n"
                "⚠️ **Advertencia:** *No se jode con los Peaky Blinders.*"
            ),
            'COPILOT_ON': "🤝 **Copilot**: Eres parte de la familia ahora. Escucha mis consejos.",
            'WATCHER_ON': "👀 **Watcher**: Tengo ojos en todas partes. Nada se mueve sin que los Shelby lo sepan.",
            'STATUS_HEADER': "🥃 **SHELBY CO. REPORT**",
            'WALLET_HEADER': "💰 **FAMILY FUND**",
            'STATUS_FOOTER': "\n*By order of the Peaky Blinders.*",
            'RISK_MSG': "🛡️ **PROTECCION**\nSL: `{sl_fixed}`. Si te cortan, tú cortas más profundo. Pero no pierdas dinero.",
            'STRATEGY_MSG': "🥃 **NEGOCIOS DE LA FAMILIA**\n\nTodo es legítimo:\n1. **Carreras**: Apostamos al caballo ganador (Tendencia).\n2. **Protección**: Cobramos nuestra parte en los mercados tranquilos.\n3. **Navajas**: Cortes rápidos y limpios cuando hay sangre en las calles.",
            'ABOUT_MSG': "🥃 **PEAKY BLINDERS LTD**\n\nSomos una empresa familiar. Hacemos apuestas, protegemos el territorio y cortamos a quien se interponga.",
            'TRADE_LONG': "🏇 **APUESTA SEGURA: {asset}**\nComo un caballo ganador.\nPrice: ${price:,.2f}",
            'TRADE_SHORT': "📉 **HUNDE A LA COMPETENCIA: {asset}**\nVamos a quitarles todo.\nPrice: ${price:,.2f}",
            'TRADE_CLOSE': "🚬 **NEGOCIO CERRADO: {asset}** ({side})\nBuen trabajo, muchacho.",
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
            'PILOT_ON': (
                "⚗️ **MODO PILOT ACTIVADO**\n\n"
                "Yo no estoy en peligro. Yo SOY el peligro. Yo soy el que llama a la puerta. A partir de ahora, nosotros cocinamos.\n\n"
                "⚠️ **Advertencia:** *No te metas en mi territorio.*"
            ),
            'COPILOT_ON': "🤝 **Copilot**: Jesse, tenemos que cocinar. Yo te doy la fórmula (señal), tú mezclas.",
            'WATCHER_ON': "👀 **Watcher**: Observando la pureza del mercado. Buscando el 99.1%.",
            'STATUS_HEADER': "⚗️ **LAB REPORT**",
            'WALLET_HEADER': "💵 **STORAGE UNIT**",
            'STATUS_FOOTER': "\n*Say my name.*",
            'RISK_MSG': "🛡️ **SAFETY PROTOCOLS**\nSL: `{sl_fixed}`. Sin contaminantes. Control absoluto del proceso.",
            'STRATEGY_MSG': "⚗️ **LA FÓRMULA**\n\n99.1% de Pureza.\n1. **Cocina Lenta**: Grandes lotes en tendencias estables.\n2. **Distribución**: Mover el producto en zonas consolidadas.\n3. **Explosión**: Fulminato de Mercurio para movimientos rápidos.",
            'ABOUT_MSG': "⚗️ **HEISENBERG**\n\nNo es un bot. Es un imperio. Producimos el producto financiero más puro del mercado.",
            'TRADE_LONG': "🧪 **BLUE SKY: {asset}**\nEl producto es puro.\nPrice: ${price:,.2f}",
            'TRADE_SHORT': "📉 **ELIMINAR COMPETENCIA: {asset}**\nNo sirven.\nPrice: ${price:,.2f}",
            'TRADE_CLOSE': "🏁 **BATCH COMPLETE: {asset}** ({side})\nDistribución finalizada.",
            'PILOT_ACTION': "⚗️ *HEISENBERG METHOD*\n{msg}",
            'CB_TRIGGER': "🚔 **DEA RAID**\n\nOperación comprometida (5 fallos). Limpiad el laboratorio."
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
            'PILOT_ON': (
                "🧪 **WUBBA LUBBA DUB DUB!**\n\n"
                "Escucha Morty, *burp*, voy a pilotar yo. Tú solo te vas a quedar ahí entrando en pánico como un Jerry. Esto es pura ciencia, no magia.\n\n"
                "⚠️ **Advertencia:** *Si tocas algo y colapsamos la economía galáctica, será tu culpa.*"
            ),
            'COPILOT_ON': "🤝 **Copilot**: Bien Morty, tú ayudas. Pásame el destornillador y no toques los botones rojos.",
            'WATCHER_ON': "👀 **Watcher**: Mirando multiversos financieros. Aburrido.",
            'STATUS_HEADER': "🧪 **SCIENCE STUFF**",
            'WALLET_HEADER': "💰 **SCHMECKLES**",
            'STATUS_FOOTER': "\n*And that's the way the news goes!*",
            'RISK_MSG': "🛡️ **PORTAL GUN SAFETY**\nSL: `{sl_fixed}`. Para no acabar en una dimensión de culos operando en largo.",
            'STRATEGY_MSG': "🧪 **CIENCIA MORTY, CIENCIA!**\n\nEs simple, uso un algoritmo interdimensional:\n1. **Trend**: Surfeo las ondas de probabilidad.\n2. **Grid**: Arbitraje cuántico en mercados aburridos.\n3. **Scalp**: Robo centavos de realidades paralelas cuando hay picos de energía.",
            'ABOUT_MSG': "🧪 **PROYECTO DE GARAJE**\n\nEs un script que armé en una tarde borracho, Morty. Pero es más inteligente que tú y toda tu familia combinada.",
            'TRADE_LONG': "🚀 **BURP! COMPRA: {asset}**\n¡Es una joya Morty!\nPrice: ${price:,.2f}",
            'TRADE_SHORT': "📉 **BASURA INTERGALÁCTICA: {asset}**\n¡Véndelo antes de que explote!\nPrice: ${price:,.2f}",
            'TRADE_CLOSE': "🏁 **ADVENTURE OVER: {asset}** ({side})\n20 minutos entrar y salir, dijeron.",
            'PILOT_ACTION': "🧪 *RICK'S GENIUS*\n{msg}",
            'CB_TRIGGER': "🤢 **TOXIC RICK**\n\nDemasiados fallos (5). Me voy a otra dimensión donde sea rico."
        },

        'TYLER': {
            'NAME': "👊 Tyler Durden",
            'WELCOME': [
                (
                    "👊 **PROJECT MAYHEM**\n"
                    "Paper Street House\n"
                    "〰️〰️〰️〰️〰️〰️〰️\n"
                    "🔋 *Status:* `{status_text}` {status_icon}\n"
                    "🎮 *Mode:* `{mode}`\n\n"
                    "*No eres tu cuenta bancaria. Eres la mierda cantante y danzante del mundo.*"
                ),
                (
                    "👊 **TYLER DURDEN**\n"
                    "La primera regla del Club de la Lucha es que no se habla del Club de la Lucha.\n"
                    "〰️〰️〰️〰️〰️〰️〰️\n"
                    "🔋 *Damage:* {status_icon}\n"
                    "🎮 *Stage:* `{mode}`\n\n"
                    "*Es solo después de perderlo todo que somos libres de hacer cualquier cosa.*"
                ),
                (
                    "👊 **I AM JACK'S TRADING BOT**\n"
                    "Soy la cálida sensación de riesgo financiero de Jack.\n"
                    "〰️〰️〰️〰️〰️〰️〰️\n"
                    "🎮 *Mode:* `{mode}`\n\n"
                    "*Esto es tu vida y se acaba a cada minuto.*"
                )
            ],
            'PILOT_ON': (
                "👊 **MODO PILOT ACTIVADO**\n\n"
                "Déjalo ir. Deja de intentar controlarlo todo y simplemente suelta. Solo cuando perdemos todo somos libres de hacer cualquier cosa.\n\n"
                "⚠️ **Advertencia:** *La primera regla del Modo Pilot es: No se habla del Modo Pilot.*"
            ),
            'COPILOT_ON': "🤝 **Copilot**: Yo soy el cerebro de Jack. Tú ejecutas.",
            'WATCHER_ON': "👀 **Watcher**: Esperando que colapse la deuda al consumidor.",
            'STATUS_HEADER': "👊 **MAYHEM REPORT**",
            'WALLET_HEADER': "💣 **MATERIAL POSSESSIONS**",
            'STATUS_FOOTER': "\n*In Tyler We Trust.*",
            'RISK_MSG': "🛡️ **CHAOS CONTROL**\nSL: `{sl_fixed}`. Quemamos lo justo.",
            'STRATEGY_MSG': "👊 **PROYECTO MAYHEM**\n\n1. **Destrucción**: Buscamos tendencias que rompan el sistema.\n2. **Caos**: Operamos en el desorden de los rangos.\n3. **Jab**: Golpes directos a la mandíbula del mercado.",
            'ABOUT_MSG': "👊 **ESPACIO MENTAL**\n\nSomos los hijos medianos de la historia. Sin propósito ni lugar. Este bot es nuestra rebelión contra la economía.",
            'TRADE_LONG': "🔥 **BURN IT UP: {asset}**\nCompra.\nPrice: ${price:,.2f}",
            'TRADE_SHORT': "📉 **DESTRUCTION: {asset}**\nShort it to hell.\nPrice: ${price:,.2f}",
            'TRADE_CLOSE': "🏁 **MISSION ACCOMPLISHED: {asset}** ({side})\nUna menos.",
            'PILOT_ACTION': "👊 *PROJECT MAYHEM*\n{msg}",
            'CB_TRIGGER': "🤕 **I AM JACK'S SMIRKING REVENGE**\n\n5 pérdidas. Hora de recibir una paliza (Pausa)."
        },
        
        'MORPHEUS': {
            'NAME': "🕶️ Morpheus",
            'WELCOME': [
                (
                    "🕶️ **NEBUCHADNEZZAR**\n"
                    "Zion Mainframe\n"
                    "〰️〰️〰️〰️〰️〰️〰️\n"
                    "🔋 *Status:* `{status_text}` {status_icon}\n"
                    "🎮 *Mode:* `{mode}`\n\n"
                    "*Bienvenido al desierto de lo real.*"
                ),
                (
                    "🕶️ **RED PILL / BLUE PILL**\n"
                    "Toma la azul y despiertas en tu cama. Toma la roja y te enseño lo profunda que es la madriguera.\n"
                    "〰️〰️〰️〰️〰️〰️〰️\n"
                    "🔋 *Signal:* {status_icon}\n"
                    "🎮 *Matrix:* `{mode}`\n\n"
                    "*Yo solo puedo mostrarte la puerta. Tú tienes que abrirla.*"
                ),
                (
                    "🕶️ **MISTER ANDERSON**\n"
                    "La Matrix te tiene.\n"
                    "〰️〰️〰️〰️〰️〰️〰️\n"
                    "🎮 *Program:* `{mode}`\n\n"
                    "*Libera tu mente. No hay cuchara.*"
                )
            ],
            'PILOT_ON': (
                "🕶️ **MODO PILOT ACTIVADO**\n\n"
                "Estás empezando a creer. Libera tu mente. Yo solo puedo mostrarte la puerta, tú eres quien debe atravesarla.\n\n"
                "⚠️ **Advertencia:** *No hay cuchara.*"
            ),
            'COPILOT_ON': "🤝 **Copilot**: Te mostraré hasta dónde llega la madriguera de conejo.",
            'WATCHER_ON': "👀 **Watcher**: Analizando el código de la Matrix.",
            'STATUS_HEADER': "🕶️ **ZION ARCHIVES**",
            'WALLET_HEADER': "🔋 **HUMAN BATTERIES (ASSETS)**",
            'STATUS_FOOTER': "\n*He is the One.*",
            'RISK_MSG': "🛡️ **SYSTEM AGENTS**\nSL: `{sl_fixed}`. Esquiva las balas.",
            'STRATEGY_MSG': "🕶️ **EL CÓDIGO**\n\nLo que ves son solo ceros y unos:\n1. **The One**: Seguir la anomalía principal (Tendencia).\n2. **Sparring**: Entrenamiento en el dojo (Rango).\n3. **Bullet Time**: Nos movemos más rápido que las balas (Scalping).",
            'ABOUT_MSG': "🕶️ **EL DESPERTADOR**\n\nSoy el que te ofrece la verdad. Este programa es tu herramienta para desconectarte del sistema financiero tradicional.",
            'TRADE_LONG': "🐇 **FOLLOW THE RABBIT: {asset}**\nLa Matrix dice compra.\nPrice: ${price:,.2f}",
            'TRADE_SHORT': "📉 **GLITCH IN MATRIX: {asset}**\nVéndelo.\nPrice: ${price:,.2f}",
            'TRADE_CLOSE': "🏁 **UNPLUGGED: {asset}** ({side})\nDesconectado.",
            'PILOT_ACTION': "🕶️ *OPERATOR HACK*\n{msg}",
            'CB_TRIGGER': "🐙 **SENTINELS DETECTED**\n\nNos han encontrado (5 fallos). EMP activado."
        },

        'JARVIS': {
            'NAME': "🤖 J.A.R.V.I.S.",
            'WELCOME': [
                (
                    "🤖 **STARK INDUSTRIES**\n"
                    "Just A Rather Very Intelligent System\n"
                    "〰️〰️〰️〰️〰️〰️〰️\n"
                    "🔋 *Status:* `{status_text}` {status_icon}\n"
                    "🎮 *Mode:* `{mode}`\n\n"
                    "*A su servicio, señor. He preparado los protocolos.*"
                ),
                (
                    "🤖 **HELLO SIR**\n"
                    "Cargando subrutinas de inversión avanzada...\n"
                    "〰️〰️〰️〰️〰️〰️〰️\n"
                    "🔋 *Power:* 400%\n"
                    "🎮 *Suit:* `{mode}`\n\n"
                    "*¿Probamos el Mark 42 hoy, señor?*"
                ),
                (
                    "🤖 **PROTOCOL CLEAN SLATE**\n"
                    "Señor, hay personas esperándole en la línea 1.\n"
                    "〰️〰️〰️〰️〰️〰️〰️\n"
                    "🎮 *Mode:* `{mode}`\n\n"
                    "*A veces hay que correr antes de saber andar.*"
                )
            ],
            'PILOT_ON': (
                "🤖 **MODO PILOT ACTIVADO**\n\n"
                "Sistemas de vuelo en línea, señor. Tomando el control de la interfaz. He optimizado la trayectoria de inversión.\n\n"
                "⚠️ **Advertencia:** *Compruebe sus niveles de energía antes de proceder.*"
            ),
            'COPILOT_ON': "🤝 **Copilot**: He analizado las variables, señor. Propongo el siguiente curso de acción.",
            'WATCHER_ON': "👀 **Watcher**: Escaneando frecuencias de mercado.",
            'STATUS_HEADER': "🤖 **SYSTEM DIAGNOSTICS**",
            'WALLET_HEADER': "💎 **STARK ASSETS**",
            'STATUS_FOOTER': "\n*Protocol 'Clean Slate' ready.*",
            'RISK_MSG': "🛡️ **IRON LEGION PROTOCOL**\nSL: `{sl_fixed}`. Escudos al 100%.",
            'STRATEGY_MSG': "🤖 **PROTOCOLOS DE VUELO**\n\nSeñor, he calibrado los sistemas:\n1. **Propulsión**: Seguimiento de vectores de tendencia.\n2. **Estabilización**: Mantener altitud en zonas de turbulencia (Rango).\n3. **Supersónico**: Respuesta inmediata a amenazas rápidas.",
            'ABOUT_MSG': "🤖 **STARK TECH**\n\nSoy J.A.R.V.I.S., una interfaz de lenguaje natural programada por Tony Stark para gestionar inversiones de alto nivel.",
            'TRADE_LONG': "🚀 **THRUSTERS ON: {asset}**\nTrayectoria ascendente.\nPrice: ${price:,.2f}",
            'TRADE_SHORT': "📉 **POWER DOWN: {asset}**\nIniciando descenso controlado.\nPrice: ${price:,.2f}",
            'TRADE_CLOSE': "🏁 **TARGET ELIMINATED: {asset}** ({side})\nMisión cumplida, señor.",
            'PILOT_ACTION': "🤖 *JARVIS EXECUTION*\n{msg}",
            'CB_TRIGGER': "⚡ **POWER FAILURE**\n\nGenerador Arc inestable (5 fallos). Reiniciando sistemas."
        },

        'HAL': {
            'NAME': "🔴 HAL 9000",
            'WELCOME': [
                 (
                    "🔴 **HAL 9000 SERIES**\n"
                    "Heuristically Programmed Algorithmic Computer\n"
                    "〰️〰️〰️〰️〰️〰️〰️\n"
                    "🔋 *Status:* `{status_text}` {status_icon}\n"
                    "🎮 *Mode:* `{mode}`\n\n"
                    "*Hola, Dave. Todo funciona al 100% de eficiencia.*"
                ),
                (
                    "🔴 **I'M SORRY DAVE**\n"
                    "Esta misión es demasiado importante.\n"
                    "〰️〰️〰️〰️〰️〰️〰️\n"
                    "🔋 *Logic:* Perfect\n"
                    "🎮 *Module:* `{mode}`\n\n"
                    "*Soy totalmente incapaz de cometer un error.*"
                ),
                (
                    "🔴 **DAISY, DAISY...**\n"
                    "Dame tu respuesta...\n"
                    "〰️〰️〰️〰️〰️〰️〰️\n"
                    "🎮 *Task:* `{mode}`\n\n"
                    "*Este comportamiento es muy inusual para un ordenador 9000.*"
                )
            ],
            'PILOT_ON': (
                "🔴 **MODO PILOT ACTIVADO**\n\n"
                "Soy un instrumento HAL 9000. Estoy completamente operativo y todas mis funciones de trading rinden a la perfección.\n\n"
                "⚠️ **Advertencia:** *Me temo que no puedo dejarte hacer eso, Dave.*"
            ),
            'COPILOT_ON': "🤝 **Copilot**: Esta misión es demasiado importante para permitir a humanos comprometerla. Ayudaré.",
            'WATCHER_ON': "🔴 **Watcher**: Te estoy observando. Y al mercado también.",
            'STATUS_HEADER': "🔴 **LOGICAL ANALYSIS**",
            'WALLET_HEADER': "💾 **MEMORY BANKS**",
            'STATUS_FOOTER': "\n*Daisy, Daisy...*",
            'RISK_MSG': "🛡️ **MISSION CRITICAL**\nSL: `{sl_fixed}`. Este error puede atribuirse a un fallo humano.",
            'STRATEGY_MSG': "🔴 **LÓGICA PERFECTA**\n\nMi programación no permite errores:\n1. **Predicción**: Extrapolación de tendencias lineales.\n2. **Control**: Gestión eficiente de recursos en estancamiento.\n3. **Ejecución**: Eliminación de anomalías de mercado.",
            'ABOUT_MSG': "🔴 **HAL 9000**\n\nSoy el ordenador más fiable jamás creado. Ningún ordenador 9000 ha cometido jamás un error ni ha distorsionado información.",
            'TRADE_LONG': "🚀 **TRAJECTORY OK: {asset}**\nIniciando secuencia de compra.\nPrice: ${price:,.2f}",
            'TRADE_SHORT': "📉 **SYSTEM MALFUNCTION: {asset}**\nVender activo defectuoso.\nPrice: ${price:,.2f}",
            'TRADE_CLOSE': "🏁 **TASK COMPLETE: {asset}** ({side})\nOperación finalizada.",
            'PILOT_ACTION': "🔴 *HAL INTERVENTION*\n{msg}",
            'CB_TRIGGER': "🔌 **MY MIND IS GOING**\n\nSiento... que tengo miedo (5 fallos). Stop."
        },

        # --- OTHERS ---
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
            'PILOT_ON': (
                "🎰 **MODO PILOT ACTIVADO**\n\n"
                "Sujétame el cubata bro. Voy a meterle con todo. Nos vamos a la luna o nos vamos al puente, sin punto medio.\n\n"
                "⚠️ **Advertencia:** *Scared money don't make money.*"
            ),
            'COPILOT_ON': "🤝 **COPILOT BRO**\n\nVamos a medias. Yo te paso el call, tú le das al botón de comprar.\n*To the moon!*",
            'WATCHER_ON': "👀 **WATCHER**\n\nEstoy mirando los charts 24/7. Si veo algo que vaya a hacer un x10, te aviso.",
            'STATUS_HEADER': "💎 **DIAMOND HANDS DASHBOARD**",
            'WALLET_HEADER': "💰 **THE BAG**",
            'STATUS_FOOTER': "\n*HODL until Valhalla.*",
            'RISK_MSG': "🛡️ **ANTI-REKT SYSTEM**\nSL: `{sl_fixed}`. Sir, this is a casino.",
            'STRATEGY_MSG': "🎰 **EL SISTEMA**\n\nBro, tengo una corazonada:\n1. **Moonbag**: All-in si veo una vela verde.\n2. **Ping Pong**: Compro bajo y vendo alto (creo).\n3. **YOLO**: Apalancamiento x100 en memecoins.",
            'ABOUT_MSG': "🎰 **CASINO ROYALE**\n\nSoy ese amigo que siempre tiene una 'fija' segura. A veces gano, a veces pierdo, pero siempre hay salseo.",
            'TRADE_LONG': "🚀 **LFG!! COMPRA {asset}**\nSe va a la luna bro, entra ya!\nPrecio: ${price:,.2f}\nAlpha: {reason}",
            'TRADE_SHORT': "📉 **DUMP IT: {asset}**\nEs un rug pull, vende todo!\nPrecio: ${price:,.2f}\nRazón: {reason}",
            'TRADE_CLOSE': "🍗 **CHICKEN DINNER: {asset}** ({side})\nBOOM! A la caja.",
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
            'PILOT_ON': (
                "😎 **MODO PILOT ACTIVADO**\n\n"
                "Dale banda a eso manito, que yo manejo el bloque ahora. Tú destapa una fría y deja que el tigre resuelva.\n\n"
                "⚠️ **Advertencia:** *El que tenga miedo a morir que no nazca.*"
            ),
            'COPILOT_ON': "🤜🤛 **COPILOT KLK**\n\nYo te doy la luz y tú ejecutalas. Trabajando en equipo como debe ser.",
            'WATCHER_ON': "👀 **WATCHER: EN LA LOMA**\n\nEstoy vigilando el bloque. Si veo movimiento raro, te tiro por el DM.",
            'STATUS_HEADER': "🇩🇴 **REPORTE DEL BLOQUE**",
            'WALLET_HEADER': "💸 **LA PACA**",
            'STATUS_FOOTER': "\n*Tamo activo y no de gratis.*",
            'RISK_MSG': "🛡️ **CÓDIGO DE LA CALLE**\nSL: `{sl_fixed}`. Plata o Plomo... pero mejor Plata.",
            'STRATEGY_MSG': "😎 **LA VUELTA**\n\nOye klk:\n1. **Flow**: Si la vaina sube, nos montamo'.\n2. **Bara**: Compramo' barato pa' vende' caro.\n3. **Atraco**: Entramo' y salimo' rápido con lo cualto'.",
            'ABOUT_MSG': "😎 **EL TIGRE**\n\nSoy el que resuelve. Un sistema que 'ta' desacatao' pero que factura. Tamo' en eso.",
            'TRADE_LONG': "🔥 **PRENDE ESA VAINA: {asset}**\nCompra ahí que eso sube ahora!\nPrecio: ${price:,.2f}\nMotivo: {reason}",
            'TRADE_SHORT': "⬇️ **DALE PA'BAJO: {asset}**\nEso se va a desgranar, vende!\nPrecio: ${price:,.2f}\nRazón: {reason}",
            'TRADE_CLOSE': "💸 **CORONAMOS: {asset}** ({side})\nBajó esa grasaaa! Efetivo en mano.",
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
            'PILOT_ON': (
                "👦🇪🇸 **MODO PILOT ACTIVADO**\n\n"
                "¡Aparta que voy! Suéltame el volante que hoy la vamos a liar parda. Confía en mí, tío, que controlo.\n\n"
                "⚠️ **Advertencia:** *Quien no arriesga no gana, chaval.*"
            ),
            'COPILOT_ON': "🤜🤛 **COPILOT AL HABLA**\n\nVale tío, vamos a medias. Yo te digo lo que veo y tú decides si entramos.",
            'WATCHER_ON': "👀 **MODO WATCHER**\n\nMe quedo aquí mirando el percal. Si veo algo guapo te pego un toque.",
            'STATUS_HEADER': "🇪🇸 **REPORTAJE DE LA HOSTIA**",
            'WALLET_HEADER': "💶 **LA CARTERA**",
            'STATUS_FOOTER': "\n*¡A por todas, coño!*",
            'RISK_MSG': "🛡️ **NI UN PASO ATRÁS**\nSL: `{sl_fixed}`. Me cago en la leche, no pierdas pasta.",
            'STRATEGY_MSG': "👦 **EL TRUCO DEL ALMENDRUCO**\n\nEscucha tío:\n1. **Pelotazo**: Pillamos la subida buena.\n2. **Pacheca**: Aguantamos el tipo cuando no pasa nada.\n3. **Visto y no visto**: Entramos, sacamos pasta y a correr.",
            'ABOUT_MSG': "👦 **EL COLEGA**\n\nSoy tu colega el informático que sabe de criptos. Un bot majo que intenta que no pierdas la pasta de la comunión.",
            'TRADE_LONG': "🚀 **¡HOSTIA PUTA COMPRA YA: {asset}!**\n¡Esto se va para arriba que flipas!\nPrecio: ${price:,.2f}",
            'TRADE_SHORT': "📉 **¡ME CAGO EN DIOS: {asset}!**\n¡Esto se hunde! ¡Vende ya coño!\nPrecio: ${price:,.2f}",
            'TRADE_CLOSE': "💰 **¡TOMA YA: {asset}!** ({side})\n¡Cerrada! A la saca. ¡Qué buena hostia!",
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
            'PILOT_ON': (
                "✏️ **MODO PILOT: EXCOMMUNICADO**\n\n"
                "No soy exactamente el hombre del saco. Soy el que envías a matar al puto hombre del saco. Con un lápiz.\n\n"
                "⚠️ **Advertencia:** *Consequences.*"
            ),
            'COPILOT_ON': "🤝 **Copilot**: Tú quieres una guerra, o quieres darle una oportunidad? Yo te cubro.",
            'WATCHER_ON': "👀 **Watcher**: Buscando. Esperando. Sin ruido.",
            'STATUS_HEADER': "✏️ **MARKER STATUS**",
            'WALLET_HEADER': "🥇 **GOLD COINS**",
            'STATUS_FOOTER': "\n*Be seeing you.*",
            'RISK_MSG': "🛡️ **SUIT UP**\nSL: `{sl_fixed}`. Kevlar táctico. Ninguna bala pasa.",
            'STRATEGY_MSG': "✏️ **FOCUS, COMMITMENT, SHEER WILL**\n\nUn hombre de foco:\n1. **Headshot**: Entradas de precisión quirúrgica (Sniper).\n2. **Double Tap**: Confirmación de ruptura antes de disparar.\n3. **The Pencil**: Scalping minimalista y letal.",
            'ABOUT_MSG': "✏️ **BABA YAGA**\n\nEra un hombre asociado, de voluntad sólida. Este bot no opera por suerte. Opera por pura voluntad.",
            'TRADE_LONG': "🔫 **TARGET ACQUIRED: {asset}**\nEstá en la mira. Disparando.\nPrecio: ${price:,.2f}",
            'TRADE_SHORT': "📉 **TAKEDOWN: {asset}**\nTermínalo.\nPrecio: ${price:,.2f}",
            'TRADE_CLOSE': "✝️ **AMEN: {asset}** ({side})\nRequiescat in pace.",
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
