import logging
import asyncio
import nest_asyncio
import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler
from supabase import create_client, Client

nest_asyncio.apply()

logging.basicConfig(level=logging.INFO)

SUPABASE_URL = 'https://navfofqbgudvnprspgsz.supabase.co'
SUPABASE_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im5hdmZvZnFiZ3Vkdm5wcnNwZ3N6Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3Mjg0MTQ1NDgsImV4cCI6MjA0Mzk5MDU0OH0.KN_NjH1wSkUzRgK2JG-r9uoF9FVsLPhIXyez2YcEDY4'
TOKEN = '7607388879:AAGxo7g7inudREcxfsWH6EnNPEJhjeQbURM'

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

ADMIN_USER_ID = 1972505293

welcome_message = "Hello and Welcome to Rei Ayanami Checker, touch the buttons below for more info."

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    username = update.effective_user.username

    result = supabase.table('users').select('*').eq('id', user_id).execute()
    if result.data:
        await update.message.reply_text(f'¡Bienvenido! Utiliza /cmds para ver los comandos.')
    else:
        await update.message.reply_text('¡Bienvenido! Utiliza /register para registrarte.')

async def register(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    username = update.effective_user.username

    try:
        result = supabase.table('users').select('*').eq('id', user_id).execute()
        if result.data:
            await update.message.reply_text('Tranquilo Vaquero, ya estás registrado!')
            return  

        now = datetime.datetime.now()
        registered_date = now.date().isoformat()  
        registered_time = now.time().isoformat()  

        supabase.table('users').insert({
            'id': user_id,
            'username': username,
            'registered_date': registered_date,
            'registered_time': registered_time,
            'credits': 15  
        }).execute()

        await update.message.reply_text('Usuario registrado con éxito!')
        await asyncio.sleep(2)
        await update.message.reply_text("Utiliza /cmds para ver los comandos.")

    except Exception as e:
        await context.bot.send_message(chat_id=ADMIN_USER_ID, text=f'Error registrando usuario: {str(e)}')

async def send_commands_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    username = update.effective_user.username

    result = supabase.table('users').select('*').eq('id', user_id).execute()
    if result.data:
        keyboard = [
            [InlineKeyboardButton("Tools", callback_data='tools'), InlineKeyboardButton("Info", callback_data='info')],
            [InlineKeyboardButton("Gates", callback_data='gates'), InlineKeyboardButton("Exit", callback_data='exit')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await context.bot.send_photo(
            chat_id=chat_id,
            photo='https://github.com/ROBMO-CLOUD/Code/blob/main/cmds.jpg?raw=true',  
            caption=welcome_message.replace('@user', f'@{username}'),
            reply_markup=reply_markup
        )
    else:
        await update.message.reply_text('¡Bienvenido! Utiliza /register para registrarte.')

async def cmds(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_commands_message(update, context)

async def info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id

    try:
        user_info = supabase.table('users').select('*').eq('id', user_id).execute()
        
        if user_info.data:
            user_data = user_info.data[0]  

            username = user_data['username']
            registered_date = user_data['registered_date']
            registered_time = user_data['registered_time']
            credits = user_data['credits']
            
            info_message = "𝐕𝐒𝐗𝐗 𝐁𝐎𝐓 / @𝐑𝟎𝐁𝐌𝟎\n" \
                           "━━━━❪ 么 ❫━━━━\n\n" \
                           f"『 亗 』  𝐈𝐃: {user_id}\n\n" \
                           f"『 亗 』  𝐔𝐬𝐞𝐫: @{username}\n\n" \
                           f"『 亗 』  𝐃𝐚𝐭𝐞: {registered_date}\n\n" \
                           f"『 亗 』  𝐇𝐨𝐮𝐫: {registered_time}\n\n" \
                           f"『 亗 』  𝐂𝐫𝐞𝐝𝐢𝐭𝐬: {credits}\n\n"\
                           "━━━━❪ 么 ❫━━━━\n" \

            await context.bot.delete_message(chat_id=chat_id, message_id=update.callback_query.message.message_id)

            keyboard = [[InlineKeyboardButton("Back", callback_data='back')]]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await context.bot.send_message(chat_id=chat_id, text=info_message, reply_markup=reply_markup)
        else:
            await update.callback_query.message.reply_text("No se encontró información para este usuario.")

    except Exception as e:
        await context.bot.send_message(chat_id=ADMIN_USER_ID, text=f'Error obteniendo información: {str(e)}')

async def back(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    await context.bot.delete_message(chat_id=chat_id, message_id=update.callback_query.message.message_id)

    await send_commands_message(update, context)

async def tools(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    keyboard = [
        [InlineKeyboardButton("Back", callback_data='back'), InlineKeyboardButton("Next", callback_data='next')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    tools_message = "𝐕𝐒𝐗𝐗 𝐁𝐎𝐓 / @𝐑𝟎𝐁𝐌𝟎\n" \
        "━━━━❪ ϟ ❫━━━━\n\n" \
        "『 亗 』  𝐄𝐱𝐭𝐫𝐚𝐩𝐨𝐥𝐚𝐭𝐨𝐫 𝐛𝐢𝐧: /ext xxxxxx\n\n" \
        "『 亗 』  𝐈𝐧𝐟𝐨 𝐛𝐢𝐧: /bin xxxxxx\n\n" \
        "『 亗 』  𝐆𝐞𝐧: /gen xxxxxx\n\n" \
        "『 亗 』  𝐑𝐧𝐝 𝐋𝐨𝐜𝐚𝐭𝐢𝐨𝐧: /rnd US, CO, PE, EC\n\n" \
        "『 亗 』  𝐈𝐏 𝐈𝐧𝐟𝐨: /ip xxxxxx\n\n" \
        "━━━━❪ ϟ ❫━━━━\n" 
   
    await context.bot.delete_message(chat_id=chat_id, message_id=update.callback_query.message.message_id)
    await context.bot.send_message(chat_id=chat_id, text=tools_message, reply_markup=reply_markup)

async def main():
    application = ApplicationBuilder().token(TOKEN).build()

    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('register', register))
    application.add_handler(CommandHandler('cmds', cmds))  
    application.add_handler(CallbackQueryHandler(info, pattern='info'))
    application.add_handler(CallbackQueryHandler(back, pattern='back'))
    application.add_handler(CallbackQueryHandler(tools, pattern='tools'))


    await application.run_polling()

if __name__ == '__main__':
    asyncio.run(main())
