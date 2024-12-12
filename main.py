import telebot
import os
import time
from telebot import types
import subprocess
from url_uploader import url_uploader_module
from bulk_uploader import bulk_uploader_module

# Telegram bot token
TOKEN = '7978926514:AAEttfF3CSqVULf8xs0Oqshx-vuCOxI0cwE'
bot = telebot.TeleBot(TOKEN)

print("ðŸš€ Bot start ho gya GuRu ðŸš€")

temp_data = {}
authorized_users = {'5443679321': float('inf')}  # Permanent authorization for the owner

def is_authorized(user_id):
    return user_id in authorized_users and time.time() < authorized_users[user_id]

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = str(message.from_user.id)
    if not is_authorized(user_id):
        bot.send_message(message.chat.id, "ðŸš« Unauthorized access.")
        return

    username = message.from_user.username or "User"
    welcome_text = f"ðŸš€ Welcome, @{username}! Choose an option below to get started:"
    markup = types.InlineKeyboardMarkup(row_width=2)
    owner_btn = types.InlineKeyboardButton("ðŸ‘¤ Owner", url="https://t.me/SDV_bots")
    developer_btn = types.InlineKeyboardButton("ðŸ’» Developer", url="https://t.me/unknownkiller7777")
    functions_btn = types.InlineKeyboardButton("âš™ï¸ Functions", callback_data="show_functions")
    markup.add(owner_btn, developer_btn, functions_btn)
    bot.send_message(message.chat.id, welcome_text, reply_markup=markup)

@bot.message_handler(commands=['addid'])
def add_user(message):
    user_id = str(message.from_user.id)
    if user_id != '5443679321':
        bot.send_message(message.chat.id, "ðŸš« Only the owner can use this command.")
        return

    msg = bot.send_message(message.chat.id, "Please send the user ID to authorize.")
    bot.register_next_step_handler(msg, ask_for_duration)

def ask_for_duration(message):
    user_to_add = message.text.strip()
    temp_data["user_to_add"] = user_to_add
    markup = types.InlineKeyboardMarkup()
    durations = {"1 month": 30 * 24 * 3600, "2 months": 2 * 30 * 24 * 3600, "5 months": 5 * 30 * 24 * 3600}
    for label, seconds in durations.items():
        markup.add(types.InlineKeyboardButton(label, callback_data=f"authorize_{seconds}"))
    bot.send_message(message.chat.id, "Kitne time ke liye authorization dena chahte hain?", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("authorize_"))
def authorize_user(call):
    user_id = temp_data.get("user_to_add")
    if not user_id:
        bot.send_message(call.message.chat.id, "ðŸš« User ID not found.")
        return
    duration = int(call.data.split("_")[1])
    authorized_users[user_id] = time.time() + duration
    bot.answer_callback_query(call.id, "âœ… User authorized successfully!")
    bot.delete_message(call.message.chat.id, call.message.message_id)

@bot.callback_query_handler(func=lambda call: call.data == "show_functions")
def show_functions(call):
    delete_message(call)
    markup = types.InlineKeyboardMarkup()
    url_uploader_btn = types.InlineKeyboardButton("URL Uploader ðŸ“¤", callback_data="url_uploader")
    bulk_uploader_btn = types.InlineKeyboardButton("Bulk Uploader ðŸ“¥", callback_data="bulk_uploader")
    markup.add(url_uploader_btn, bulk_uploader_btn)
    bot.send_message(call.message.chat.id, "Choose an option:", reply_markup=markup)

def delete_message(call):
    bot.delete_message(call.message.chat.id, call.message.message_id)

# URL Uploader and Bulk Uploader functions now imported from their respective modules
@bot.callback_query_handler(func=lambda call: call.data == "url_uploader")
def url_uploader_start(call):
    delete_message(call)
    url_uploader_module.start_url_uploader(bot, call)

@bot.callback_query_handler(func=lambda call: call.data in ["custom_name", "default_name"])
def url_uploader_download_file(call):
    url_uploader_module.download_file_callback_handler(bot, call)

@bot.callback_query_handler(func=lambda call: call.data == "bulk_uploader")
def bulk_uploader_start(call):
    bulk_uploader_module.start_bulk_uploader(bot, call)

@bot.callback_query_handler(func=lambda call: call.data in ["dl_videos", "dl_pdfs", "dl_both"])
def bulk_download_handler(call):
    bulk_uploader_module.bulk_download_handler(bot, call)
# Start the bot
bot.polling()