from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import numpy as np
import os

# Configuración (usa variables de entorno en producción)
TOKEN = os.getenv("7868591681:AAGYeuSUwozg3xTi1zmxPx9gWRP2xsXP0Uc", "TU_TOKEN_AQUÍ")
CANAL_ID = os.getenv("-1002701232762", "-1001234567890")

class AdvancedBotState:
    def __init__(self):
        self.entradas = []
        self.modo_espera = False
        self.posible_entrada = False
        self.protegido = 0
        self.ganadas = 0
        self.perdidas = 0
        self.ultima_entrada = None
        self.historico_riesgo = []

bot_state = AdvancedBotState()

# ---- Análisis Avanzado ----
def calcular_riesgo(entradas):
    """Clasifica el riesgo usando volatilidad y tendencia"""
    if len(entradas) < 5:
        return "moderado"
    
    cambios = np.diff(entradas[-5:])
    volatilidad = np.std(cambios)
    pendiente = np.polyfit(range(5), entradas[-5:], 1)[0]

    if volatilidad < 0.3 and pendiente > 0:
        return "bajo"
    elif volatilidad < 0.7 and pendiente > 0:
        return "moderado"
    else:
        return "alto"

def generar_recomendacion(entradas):
    """Evalúa patrones para sugerir estrategia óptima"""
    if len(entradas) < 4:
        return "ESPERAR", "Datos insuficientes"
    
    # Patrón de confirmación fuerte (3+ subidas)
    if all(x < y for x, y in zip(entradas[-4:-1], entradas[-3:])):
        return "ENTRAR_CON_PROTECCION", "Tendencia alcista fuerte detectada"
    
    # Patrón moderado (2/3 subidas)
    if sum(x < y for x, y in zip(entradas[-4:-1], entradas[-3:])) >= 2:
        return "ENTRAR_PARCIAL", "Tendencia moderada"
    
    return "ESPERAR", "Señal débil o riesgo alto"

# ---- Handlers ----
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 Aviator ProBot\n\n"
        "Sistema inteligente de trading con:\n"
        "✅ Detección de patrones\n"
        "🛡 Protección adaptativa\n"
        "📊 Análisis de riesgo en tiempo real\n\n"
        "Envía resultados numéricos (ej: 1.85, 2.40)"
    )

async def reiniciar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bot_state.__init__()
    await update.message.reply_text("🔄 Sistema reiniciado")
    await context.bot.send_message(chat_id=CANAL_ID, text="⚙️ Historial y configuraciones reseteadas")

async def recibir(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        valor = float(update.message.text.replace(",", "."))
        bot_state.entradas.append(valor)
        riesgo = calcular_riesgo(bot_state.entradas)
        bot_state.historico_riesgo.append(riesgo)

        # ---- Fase de Detección ----
        if not bot_state.modo_espera:
            recomendacion, razon = generar_recomendacion(bot_state.entradas)
            
            if recomendacion != "ESPERAR":
                mensaje_alerta = (
                    f"⚠️ {riesgo.upper()} - {recomendacion.replace('_', ' ')}\n"
                    f"📈 Últimos: {', '.join(map(str, bot_state.entos[-3:]))}\n"
                    f"🔍 Razon: {razon}\n"
                )
                
                if recomendacion == "ENTRAR_CON_PROTECCION":
                    mensaje_alerta += "✅ Recomendado: Entrada completa (2 protecciones)"
                elif recomendacion == "ENTRAR_PARCIAL":
                    mensaje_alerta += "🟡 Considerar: Entrada parcial (1 protección)"
                
                await context.bot.send_message(chat_id=CANAL_ID, text=mensaje_alerta)

                if recomendacion == "ENTRAR_CON_PROTECCION":
                    bot_state.modo_espera = True
                    bot_state.ultima_entrada = valor
                    await confirmar_entrada(valor, update, context)

        # ---- Fase de Protección ----
        if bot_state.modo_espera:
            await manejar_proteccion(valor, update, context)

    except ValueError:
        await update.message.reply_text("❌ Error: Formato inválido. Ejemplo: 1.85 o 2.40")

async def confirmar_entrada(valor, update, context):
    """Envía confirmación detallada de entrada"""
    mensaje = (
        "✅ ENTRADA CONFIRMADA\n\n"
        f"📊 Patrón: {' → '.join(map(str, bot_state.entradas[-3:]))}\n"
        f"🛡 Estrategia: {'2 protecciones' if calcular_riesgo(bot_state.entradas) == 'bajo' else '1 protección'}\n"
        f"📌 Multiplicador objetivo: 2.0x\n"
        "⚠️ Gestiona riesgo según tu capital"
    )
    await context.bot.send_message(chat_id=CANAL_ID, text=mensaje)

async def manejar_proteccion(valor, update, context):
    """Lógica avanzada de gestión de protecciones"""
    riesgo = calcular_riesgo(bot_state.entradas)
    
    if valor >= 2.0:
        bot_state.ganadas += 1
        bot_state.modo_espera = False
        await context.bot.send_message(
            chat_id=CANAL_ID,
            text=f"💰 GANADA ({valor}x)\n"
                 f"🎯 Balance: {bot_state.ganadas}✅ {bot_state.perdidas}❌"
        )
    else:
        bot_state.protegido += 1
        
        if riesgo == "alto" and bot_state.protegido >= 1:
            await context.bot.send_message(
                chat_id=CANAL_ID,
                text=f"⛔ ALTO RIESGO\n"
                     f"✋ Evitar 2da protección (Valor actual: {valor}x)\n"
                     f"💡 Esperar nueva señal"
            )
            bot_state.modo_espera = False
            bot_state.perdidas += 1
        elif bot_state.protegido <= 2:
            await context.bot.send_message(
                chat_id=CANAL_ID,
                text=f"🛡 Protección {bot_state.protegido}/2\n"
                     f"📉 Valor actual: {valor}x\n"
                     f"📊 Riesgo: {riesgo.upper()}"
            )

# ---- Configuración ----
def main():
    app = ApplicationBuilder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("reiniciar", reiniciar))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, recibir))
    
    print("🚀 Bot Aviator Pro iniciado - Análisis activo")
    app.run_polling()

if __name__ == "__main__":
    main()
