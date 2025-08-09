
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import asyncio
import nest_asyncio
from datetime import datetime

nest_asyncio.apply()

# Token y canal
TOKEN = "7868591681:AAGYeuSUwozg3xTi1zmxPx9gWRP2xsXP0Uc"
CANAL_ID = "-1002779367768"

# Variables globales
entradas = []
modo_espera = False
proteccion_activa = False
ganadas = 0
perdidas = 0
posible_entrada = False
entradas_hoy = 0
hora_inicio = datetime.now().strftime("%H:%M")

# Detectar tendencia alcista básica (últimos 3 valores)
def hay_tendencia():
    if len(entradas) < 3:
        return False
    return entradas[-3] < entradas[-2] < entradas[-1]

# Detectar posible entrada (primeros 2 de 3 valores ascendentes)
def hay_posible_tendencia():
    if len(entradas) < 2:
        return False
    return entradas[-2] < entradas[-1]

# Calcular efectividad
def calcular_efectividad():
    if ganadas + perdidas == 0:
        return 0
    return (ganadas / (ganadas + perdidas)) * 100

# Comandos
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Bot iniciado. Envíame resultados como '1.75'")

async def reiniciar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global entradas, modo_espera, proteccion_activa, ganadas, perdidas, posible_entrada, entradas_hoy, hora_inicio
    entradas = []
    modo_espera = False
    proteccion_activa = False
    ganadas = 0
    perdidas = 0
    posible_entrada = False
    entradas_hoy = 0
    hora_inicio = datetime.now().strftime("%H:%M")
    await update.message.reply_text("🔄 Contadores reiniciados")

# Lógica principal
async def recibir(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global modo_espera, proteccion_activa, ganadas, perdidas, posible_entrada, entradas_hoy

    try:
        valor = float(update.message.text.replace(",", "."))
        entradas.append(valor)

        # Verificar si se aborta posible entrada
        if posible_entrada and not hay_posible_tendencia():
            await update.message.reply_text("✖️ ABORTAR ENTRADA - Tendencia no confirmada")
            await context.bot.send_message(
                chat_id=CANAL_ID,
                text="✖️ ENTRADA ABORTADA - Tendencia no confirmada"
            )
            posible_entrada = False

        # Lógica cuando estamos en modo espera
        if modo_espera:
            if valor >= 1.80:
                ganadas += 1
                entradas_hoy += 1
                modo_espera = False
                proteccion_activa = False
                efectividad = calcular_efectividad()

                # Mensaje de ganada simplificado
                mensaje_ganada = f"""
🔥 Imparable! 🔥
Otro gran acierto al instante! 💸✨

🔥 La vela llegó a {valor:.2f}x
🏆 Entradas ganadas hoy: 🍀 {entradas_hoy} ❌ {perdidas}
📈 Nuestra efectividad: {efectividad:.2f}%

El único hack que necesitas para ganar siempre! 🔥💎
                """

                await update.message.reply_text(f"🟢 GANADA {valor:.2f}x! (G:{ganadas} P:{perdidas})")
                await context.bot.send_message(
                    chat_id=CANAL_ID,
                    text=mensaje_ganada
                )
            else:
                if not proteccion_activa:
                    proteccion_activa = True
                    await update.message.reply_text("🛡 PROTECCIÓN ACTIVADA (1 oportunidad)")
                    await context.bot.send_message(
                        chat_id=CANAL_ID,
                        text="🛡 PROTECCIÓN ACTIVADA (1 oportunidad)"
                    )
                else:
                    perdidas += 1
                    modo_espera = False
                    proteccion_activa = False
                    await update.message.reply_text(f"🔴 PERDIDA {valor:.2f}x (G:{ganadas} P:{perdidas})")
                    await context.bot.send_message(
                        chat_id=CANAL_ID,
                        text=f"❌ PERDIDA {valor:.2f}x\n📊 {ganadas}✅ {perdidas}❌"
                    )

        # Detección de posible entrada (2 de 3 valores ascendentes)
        elif hay_posible_tendencia() and len(entradas) >= 2 and not posible_entrada:
            posible_entrada = True
            mensaje_posible_entrada = f"""
⚠️ POSIBLE ENTRADA DETECTADA ⚠️

📈 Últimos valores: {entradas[-2]:.2f} → {entradas[-1]:.2f}
🔄 Esperando confirmación...
            """
            await update.message.reply_text(f"⚠️ POSIBLE ENTRADA\n🔹 Últimos: {entradas[-2]:.2f}-{entradas[-1]:.2f}\n🔄 Esperando confirmación...")
            await context.bot.send_message(
                chat_id=CANAL_ID,
                text=mensaje_posible_entrada
            )

        # Confirmación de entrada completa (3 valores ascendentes)
        elif hay_tendencia() and len(entradas) >= 3 and posible_entrada:
            modo_espera = True
            posible_entrada = False
            proteccion_activa = False

            mensaje_entrada = f"""
✅ ENTRADA CONFIRMADA ✅

📊 ENTRA DESPUÉS DE {entradas[-1]:.2f}x
💸 RETIRA EN 1.80x
🛡️ HAZ HASTA 1 PROTECCION

📈 Tendencia: {entradas[-3]:.2f} → {entradas[-2]:.2f} → {entradas[-1]:.2f}
⏳ Esperando resultado...
            """

            await update.message.reply_text(f"✅ ENTRADA CONFIRMADA\n🔹 Últimos: {entradas[-3]:.2f}-{entradas[-2]:.2f}-{entradas[-1]:.2f}\n🎯 CERRAR EN 1.80x")
            await context.bot.send_message(
                chat_id=CANAL_ID,
                text=mensaje_entrada
            )

    except ValueError:
        await update.message.reply_text("❌ Envía números como '1.75'")

# Configuración del bot
async def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("reiniciar", reiniciar))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, recibir))
    print("🤖 Bot en ejecución...")
    await app.run_polling()

await main()
