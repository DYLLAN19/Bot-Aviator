
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import asyncio
import nest_asyncio

nest_asyncio.apply()

# Token de tu bot y el chat_id de tu canal
TOKEN = "7868591681:AAGYeuSUwozg3xTi1zmxPx9gWRP2xsXP0Uc"
CANAL_ID = "-1002701232762"  # ejemplo: @aviator_signales

# Historial de entradas
entradas = []
modo_espera = False
protegido = 0
ganadas = 0
perdidas = 0
ultima_entrada = None

# Función para detectar tendencia alcista
def detectar_tendencia():
    if len(entradas) < 3:
        return False
    return entradas[-3] < entradas[-2] < entradas[-1]

# Comando /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Bot Aviator iniciado.\nSolo escribe el resultado (ej: 2.35) y yo me encargo del análisis.\nUsa /reiniciar para resetear historial.")

# Comando /reiniciar
async def reiniciar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global entradas, modo_espera, protegido, ganadas, perdidas, ultima_entrada
    entradas = []
    modo_espera = False
    protegido = 0
    ganadas = 0
    perdidas = 0
    ultima_entrada = None
    await update.message.reply_text("🔄 Historial reiniciado.")
    await context.bot.send_message(chat_id=CANAL_ID, text="🔄 Historial reiniciado manualmente.")

# Manejo de mensajes (números)
async def recibir(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global modo_espera, protegido, ganadas, perdidas, ultima_entrada

    try:
        valor = float(update.message.text.replace(",", "."))
        entradas.append(valor)

        # Si estamos en espera de un resultado tras una entrada
        if modo_espera:
            if valor >= 2:
                ganadas += 1
                await update.message.reply_text("🟢 ¡GANADA!")
                await context.bot.send_message(chat_id=CANAL_ID, text=f"✅ Entrada GANADA con {valor}x\n📈 Total: {ganadas} ganadas | {perdidas} perdidas")
                modo_espera = False
                protegido = 0
            else:
                protegido += 1
                if protegido == 1:
                    await update.message.reply_text("🛡 Primera protección activa...")
                    await context.bot.send_message(chat_id=CANAL_ID, text="🛡 Primera protección activa. Esperando nuevo resultado...")
                elif protegido == 2:
                    await update.message.reply_text("🛡 Segunda protección activa...")
                    await context.bot.send_message(chat_id=CANAL_ID, text="🛡 Segunda protección activa. Última oportunidad...")
                else:
                    perdidas += 1
                    modo_espera = False
                    protegido = 0
                    await update.message.reply_text("🔴 ¡PERDIDA TOTAL!")
                    await context.bot.send_message(chat_id=CANAL_ID, text=f"❌ Entrada PERDIDA tras 2 protecciones\n📉 Total: {ganadas} ganadas | {perdidas} perdidas")

        else:
            # Detectar tendencia
            if detectar_tendencia():
                modo_espera = True
                ultima_entrada = valor
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

    except ValueError:
        await update.message.reply_text("❌ Por favor ingresa un número válido. Ej: 2.35")

# Iniciar el bot
async def main():
    app = ApplicationBuilder().token(TOKEN).build()
    # ... (tus handlers aquí)
    print("Bot iniciado...")
    await app.run_polling()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
