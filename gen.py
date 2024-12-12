import logging
import asyncio
import nest_asyncio
import datetime
from random import *
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, _update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler
from supabase import create_client, Client
from cmds import *
import aiohttp, string


ADMIN_USER_ID = 1972505293

nest_asyncio.apply()

logging.basicConfig(level=logging.INFO)

SUPABASE_URL = 'https://navfofqbgudvnprspgsz.supabase.co'
SUPABASE_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im5hdmZvZnFiZ3Vkdm5wcnNwZ3N6Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3Mjg0MTQ1NDgsImV4cCI6MjA0Mzk5MDU0OH0.KN_NjH1wSkUzRgK2JG-r9uoF9FVsLPhIXyez2YcEDY4'
TOKEN = '7607388879:AAGxo7g7inudREcxfsWH6EnNPEJhjeQbURM'

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

REPORTS_ID = -1002432179007

async def is_registered(user_id):
    try:
        response = supabase.table('users').select('id').eq('id', user_id).execute()
        return len(response.data) > 0 
    except Exception as e:
        logging.error(f"Error: {e}")
        return False

async def validate_bin(bin_number):
    url = f"https://binlist.io/lookup/{bin_number}"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    # Verificar el scheme
                    scheme = data.get("scheme")
                    if scheme in ["VISA", "MASTERCARD"]:
                        if data.get("number", {}).get("length"):
                            return data["number"]["length"]
                    # Si el scheme no es uno de los permitidos, retornar None
                    return None
    except Exception as e:
        logging.error(f"Error al validar el BIN: {e}")
        return None

def cc_gen(bin_number, mes='x', ano='x', cvv='x', length=16):
    ccs = []
    while len(ccs) < 7:
        card = str(bin_number)
        while len(card) < length - 1:
            card += str(random.randint(0, 9))

        # Calcular el dígito verificador Luhn
        num = [int(d) for d in card]
        num.reverse()
        total = 0
        for i, digit in enumerate(num):
            if i % 2 == 0:
                digit *= 2
            if digit > 9:
                digit -= 9
            total += digit
        check_digit = (10 - (total % 10)) % 10

        card += str(check_digit)

        if mes == 'x':
            mes_gen = f"{random.randint(1, 12):02}"
        else:
            mes_gen = mes

        if ano == 'x':
            ano_gen = random.randint(2023, 2031)
        else:
            ano_gen = ano

        if cvv == 'x':
            cvv_gen = random.randint(100, 999) if card[0] != '3' else random.randint(1000, 9999)
        else:
            cvv_gen = cvv

        card_full = f"`{card}|{mes_gen}|{ano_gen}|{cvv_gen}`"
        ccs.append(card_full)

    return ccs

# Generar mensaje para el comando
def generate_message(username, bin_number, length, mes='x', ano='x', cvv='x'):
    tarjetas = cc_gen(bin_number, mes=mes, ano=ano, cvv=cvv, length=length)
    tarjetas_formateadas = "\n".join(tarjetas)
    return (
        f"VSXXBOT\n"
        "━━━━━━━━━━━━━━━━\n"
        f"[✯] BIN: `{bin_number[:6]}`\n"
        "━━━━━━━━━━━━━━━━\n"
        f"{tarjetas_formateadas}\n"
        "━━━━━━━━━━━━━━━━\n"
        f"Gen BY: `@{username}`\n"
    )

# Handler del comando /gen
async def gen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_id = update.effective_user.id
    
        if not await is_registered(user_id):
            await update.message.reply_text("Please register first using /register.")
            return 
    
        username = update.effective_user.username or "N/A"
        user_data = context.user_data
        user_id = update.effective_user.id

        if not user_data.get('user_info'):
            result = supabase.table('users').select('*').eq('id', user_id).execute()
            if not result.data:
                await update.callback_query.message.reply_text(
                    "You don't have permission to use this button. Send the /start command to initiate the bot."
                )
                return
            user_data['user_info'] = result.data[0]  


        # Obtener el BIN del mensaje del usuario
        args = context.args
        if not args or len(args[0]) < 6 or not args[0][:6].isdigit():
            await update.message.reply_text("Por favor, proporciona un BIN válido de al menos 6 dígitos. Ejemplo: /gen 123456")
            return

        # Extraer los primeros 6 dígitos como BIN
        bin_input = args[0]
        bin_number = bin_input[:6]

        # Validar BIN con binlist.io
        length = await validate_bin(bin_number)
        if not length:
            await update.message.reply_text("El BIN proporcionado no es válido o no se pudo validar. Solo se permiten BINs de VISA y MASTERCARD.")
            return

        # Separar parámetros adicionales (mes, año, cvv)
        mes = 'x'
        ano = 'x'
        cvv = 'x'
        if '|' in bin_input:
            parts = bin_input.split('|')
            if len(parts) > 1 and parts[1] != 'rnd':
                mes = parts[1]
            if len(parts) > 2 and parts[2] != 'rnd':
                ano = parts[2]
            if len(parts) > 3 and parts[3] != 'rnd':
                cvv = parts[3]

        # Generar el mensaje con las tarjetas
        gen_message = generate_message(username, bin_number, length, mes, ano, cvv)

        # Crear botón de Re-Gen
        keyboard = [
            [InlineKeyboardButton("Re-Gen", callback_data=f"regen|{bin_number}|{mes}|{ano}|{cvv}|0")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        context.user_data['user_message_id'] = update.effective_user.id

        # Responder con el mensaje generado
        await update.message.reply_text(
            gen_message,
            parse_mode="Markdown",
            reply_markup=reply_markup,
            disable_web_page_preview=True
        )
    except Exception as e:
        logging.error(f"Error en el comando /gen: {e}")
        await update.message.reply_text("Error")

async def regen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        query = update.callback_query
        await query.answer()

        # Verificar que el usuario que presiona el botón es el que generó el mensaje
        user_id = update.effective_user.id
        if context.user_data.get('user_message_id') != user_id:
            username = update.effective_user.username or "N/A"
            await query.message.reply_text(
                f"@{username}, no puedes usar este botón porque no fuiste quien lo generó."
            )
            return

        # Extraer datos del callback_data
        data = query.data.split('|')
        if len(data) != 6:
            await query.message.reply_text("Datos inválidos en el callback. Por favor, intenta nuevamente.")
            return

        bin_number, mes, ano, cvv, attempt = data[1], data[2], data[3], data[4], int(data[5])

        # Verificar que no se exceda el límite de intentos
        if attempt >= 3:
            await query.edit_message_text("Límite de intentos alcanzado. No se pueden generar más tarjetas.")
            return

        # Generar nuevas tarjetas con el mismo BIN
        username = query.from_user.username or "N/A"
        gen_message = generate_message(username, bin_number, 16, mes, ano, cvv)

        # Crear botón actualizado con el intento incrementado
        keyboard = [
            [InlineKeyboardButton("Re-Gen", callback_data=f"regen|{bin_number}|{mes}|{ano}|{cvv}|{attempt + 1}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        # Editar el mensaje con nuevas tarjetas
        await query.edit_message_text(
            gen_message,
            parse_mode="Markdown",
            reply_markup=reply_markup,
            disable_web_page_preview=True
        )
    except Exception as e:
        logging.error(f"Error en el botón Re-Gen: {e}")
        await update.callback_query.message.reply_text("Ocurrió un error al regenerar las tarjetas. Inténtalo nuevamente.")


# Configurar la aplicación
async def main():
    app = ApplicationBuilder().token(TOKEN).build()

    # Agregar el comando /gen
    app.add_handler(CommandHandler("gen", gen))

    # Agregar el handler para el botón Re-Gen
    app.add_handler(CallbackQueryHandler(regen, pattern='regen'))

    await app.run_polling()

if __name__ == '__main__':
    asyncio.run(main())
