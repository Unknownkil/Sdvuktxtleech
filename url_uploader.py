import telebot
import os
import subprocess
from telebot import types

class URLUploaderModule:
    def __init__(self):
        self.temp_data = {}

    def start_url_uploader(self, bot, call):
        msg = bot.send_message(call.message.chat.id, "Please send the download link ðŸ”—")
        bot.register_next_step_handler(msg, lambda message: self.process_download_link(bot, message))

    def process_download_link(self, bot, message):
        url = message.text
        markup = types.InlineKeyboardMarkup()
        yes_btn = types.InlineKeyboardButton("Yes", callback_data="custom_name")
        no_btn = types.InlineKeyboardButton("No", callback_data="default_name")
        markup.add(yes_btn, no_btn)
        self.temp_data["url"] = url
        self.temp_data["chat_id"] = message.chat.id
        bot.send_message(message.chat.id, "Do you want to give it a name?", reply_markup=markup)

    def download_file_callback_handler(self, bot, call):
        if call.data == "custom_name":
            self.delete_message(bot, call)
            msg = bot.send_message(call.message.chat.id, "Please send the name:")
            bot.register_next_step_handler(msg, lambda m: self.download_file(bot, m, custom_name=True))
        elif call.data == "default_name":
            self.delete_message(bot, call)
            self.download_file(bot, call.message, custom_name=False)

    def download_file(self, bot, message, custom_name=False):
        chat_id = message.chat.id
        url = self.temp_data.get("url", "")
        name = message.text if custom_name else "default_file"
        extension = ".pdf" if ".pdf" in url else ".mp4"
        
        download_msg = bot.send_message(chat_id, f"Starting download for {name}... 0%")

        try:
            download_command_yt_dlp = f"yt-dlp -o '{name}{extension}' '{url}'"
            download_command_ffmpeg = f"ffmpeg -i '{url}' -c copy '{name}{extension}'"
            
            result = subprocess.run(download_command_yt_dlp, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if result.returncode != 0:
                result = subprocess.run(download_command_ffmpeg, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            if result.returncode == 0:
                with open(name + extension, "rb") as file:
                    bot.send_document(chat_id, file)
                os.remove(name + extension)
                bot.edit_message_text(f"Download complete for {name}.", chat_id, download_msg.message_id)
            else:
                bot.edit_message_text("ðŸš« Error downloading file. Try again later.", chat_id, download_msg.message_id)
        except Exception as e:
            bot.edit_message_text(f"ðŸš« Error: {e}", chat_id, download_msg.message_id)

    def delete_message(self, bot, call):
        bot.delete_message(call.message.chat.id, call.message.message_id)

url_uploader_module = URLUploaderModule()