from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import asyncio
import nest_asyncio

# Configuración
TOKEN = "7868591681:AAGYeuSUwozg3xTi1zmxPx9gWRP2xsXP0Uc"
CANAL_ID = "-1002701232762"

# Estado del bot
class BotState:
    def __init__(self):
        self.entradas = []
        self.modo_espera = False
        self.protegido = 0
        self.ganadas = 0
        self.perdidas = 0
        self.ultima_entrada = None

bot_state = BotState()

# Funciones auxiliares
def detectar_tendencia(entradas):
    if len(entradas) < 3:
        return False
    return entradas[-3] < entradas[-2] < entradas[-1]

# Handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "✅ Bot Aviator iniciado.\n"
        "Escribe resultados numéricos (ej: 2.35) para análisis.\n"
        "Usa /reiniciar para resetear historial."
    )

async def reiniciar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bot_state.__init__()  # Reinicia todos los valores
    await update.message.reply_text("🔄 Historial reiniciado.")
    await context.bot.send_message(
        chat_id=CANAL_ID,
        text="🔄 Historial reiniciado manualmente."
    )

async def recibir(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        valor = float(update.message.text.replace(",", "."))
        bot_state.entradas.append(valor)

        if bot_state.modo_espera:
            await procesar_resultado(valor, update, context)
        else:
            await analizar_tendencia(valor, update, context)

    except ValueError:
        await update.message.reply_text("❌ Ingresa un número válido. Ej: 2.35")

async def procesar_resultado(valor, update, context):
    if valor >= 2:
        bot_state.ganadas += 1
        bot_state.modo_espera = False
        bot_state.protegido = 0
        await update.message.reply_text("🟢 ¡GANADA!")
        await context.bot.send_message(
            chat_id=CANAL_ID,
            text=f"✅ Entrada GANADA con {valor}x\n"
                 f"📈 Total: {bot_state.ganadas} ganadas | {bot_state.perdidas} perdidas"
        )
    else:
        bot_state.protegido += 1
        if bot_state.protegido <= 2:
            await update.message.reply_text(f"🛡 Protección {bot_state.protegido} activa...")
            await context.bot.send_message(
                chat_id=CANAL_ID,
                text=f"🛡 Protección {bot_state.protegido} activa. "
                     f"{'Última oportunidad...' if bot_state.protegido == 2 else 'Esperando nuevo resultado...'}"
            )
        else:
            bot_state.perdidas += 1
            bot_state.modo_espera = False
            bot_state.protegido = 0
            await update.message.reply_text("🔴 ¡PERDIDA TOTAL!")
            await context.bot.send_message(
                chat_id=CANAL_ID,
                text=f"❌ Entrada PERDIDA tras 2 protecciones\n"
                     f"📉 Total: {bot_state.ganadas} ganadas | {bot_state.perdidas} perdidas"
            )

async def analizar_tendencia(valor, update, context):
    if detectar_tendencia(bot_state.entradas):
        bot_state.modo_espera = True
        bot_state.ultima_entrada = valor
        mensaje = (
            "✅ ENTRADA DETECTADA ✅\n\n"
            f"📊 ENTRA DESPUÉS DE {valor}x\n"
            "💸 RETIRA EN 2x\n"
            "🛡️ HAZ HASTA 2 PROTECCIONES"
        )
        await update.message.reply_text(mensaje)
        await context.bot.send_message(chat_id=CANAL_ID, text=mensaje)
    else:
        await update.message.reply_text(f"✔ Entrada registrada: {valor}")

# Configuración e inicio del bot
def main():
    # Configuración de nest_asyncio solo para entornos con bucle de eventos existente
    try:
        nest_asyncio.apply()
    except RuntimeError:
        pass

    app = ApplicationBuilder().token(TOKEN).build()
    
    # Handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("reiniciar", reiniciar))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, recibir))
    
    print("✅ Bot iniciado y escuchando...")
    app.run_polling()

if __name__ == "__main__":
    main()
