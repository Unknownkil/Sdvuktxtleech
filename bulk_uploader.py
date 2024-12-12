import telebot
import os
import subprocess
import time
from telebot import types

class BulkUploaderModule:
    def __init__(self):
        self.temp_data = {}

    def start_bulk_uploader(self, bot, call):
        msg = bot.send_message(call.message.chat.id, "Please send the TXT file containing the URLs 📄")
        bot.register_next_step_handler(msg, lambda message: self.process_txt_file(bot, message))

    def process_txt_file(self, bot, message):
        try:
            if not message.document:
                bot.send_message(message.chat.id, "❌ Please upload a valid TXT file.")
                return
            
            file_info = bot.get_file(message.document.file_id)
            downloaded_file = bot.download_file(file_info.file_path)
            file_path = f"{message.document.file_name}"
            
            with open(file_path, "wb") as f:
                f.write(downloaded_file)
            
            video_links, pdf_links = [], []
            with open(file_path, "r") as f:
                for line in f:
                    name, url = line.split(":", 1)
                    if ".pdf" in url.strip():
                        pdf_links.append((name.strip(), url.strip()))
                    else:
                        video_links.append((name.strip(), url.strip()))
            
            os.remove(file_path)
            self.temp_data["video_links"] = video_links
            self.temp_data["pdf_links"] = pdf_links

            markup = types.InlineKeyboardMarkup()
            videos_btn = types.InlineKeyboardButton(f"DL Only Videos 🎥 ({len(video_links)})", callback_data="dl_videos")
            pdfs_btn = types.InlineKeyboardButton(f"DL Only PDFs 📄 ({len(pdf_links)})", callback_data="dl_pdfs")
            both_btn = types.InlineKeyboardButton("DL Both 📥", callback_data="dl_both")
            markup.add(videos_btn, pdfs_btn, both_btn)
            
            bot.send_message(message.chat.id, "Choose download option:", reply_markup=markup)
        except Exception as e:
            bot.send_message(message.chat.id, f"❌ Error processing TXT file: {e}")

    def download_with_progress(self, bot, chat_id, file_name, command):
        sent_message = bot.send_message(chat_id, f"📥 Starting download...\n𝘿𝙤𝙬𝙣𝙡𝙤𝙖𝙙 》0%\n𝙎𝙥𝙚𝙚𝙙 》Calculating...\n𝙉𝙖𝙢𝙚 》{file_name}")
        markup = types.InlineKeyboardMarkup()
        refresh_btn = types.InlineKeyboardButton("🔄 Refresh Progress", callback_data=f"refresh_{sent_message.message_id}")
        markup.add(refresh_btn)

        bot.edit_message_reply_markup(chat_id, sent_message.message_id, reply_markup=markup)
        
        start_time = time.time()

        process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
        for line in process.stdout:
            if "%" in line:  # Parse progress from yt-dlp output
                try:
                    progress = line.split("%")[0].split()[-1]
                    elapsed_time = time.time() - start_time
                    speed = f"{(int(progress) / elapsed_time):.2f} KB/s"

                    bot.edit_message_text(
                        chat_id=chat_id,
                        message_id=sent_message.message_id,
                        text=f"📥 Downloading...\n𝘿𝙤𝙬𝙣𝙡𝙤𝙖𝙙 》{progress}%\n𝙎𝙋𝙚𝙚𝙙 》{speed}\n𝙉𝙖𝙢𝙚 》{file_name}"
                    )
                except:
                    pass
        process.wait()
        return sent_message.message_id

    def upload_with_progress(self, bot, chat_id, file_path):
        sent_message = bot.send_message(chat_id, f"📤 Starting upload...\n𝙐𝙥𝙡𝙤𝙖𝙙𝙞𝙣𝙜 》0%\n𝙎𝙋𝙚𝙚𝙙 》Calculating...\n𝙉𝙖𝙢𝙚 》{os.path.basename(file_path)}")
        markup = types.InlineKeyboardMarkup()
        refresh_btn = types.InlineKeyboardButton("🔄 Refresh Progress", callback_data=f"refresh_{sent_message.message_id}")
        markup.add(refresh_btn)

        bot.edit_message_reply_markup(chat_id, sent_message.message_id, reply_markup=markup)
        
        file_size = os.path.getsize(file_path)
        uploaded_size = 0
        chunk_size = 1024 * 1024  # 1 MB chunks
        start_time = time.time()

        with open(file_path, "rb") as f:
            while chunk := f.read(chunk_size):
                uploaded_size += len(chunk)
                progress = (uploaded_size / file_size) * 100
                elapsed_time = time.time() - start_time
                speed = f"{(uploaded_size / elapsed_time) / 1024:.2f} KB/s"

                bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=sent_message.message_id,
                    text=f"📤 Uploading...\n𝙐𝙥𝙡𝙤𝙖𝙙𝙞𝙣𝙜 》{progress:.2f}%\n𝙎𝙋𝙚𝙚𝙙 》{speed}\n𝙉𝙖𝙢𝙚 》{os.path.basename(file_path)}"
                )
                time.sleep(0.5)  # Simulate delay for progress visibility

        bot.send_message(chat_id, "✅ Upload complete!")
        bot.delete_message(chat_id, sent_message.message_id)  # Delete progress message

    def bulk_download_handler(self, bot, call):
        video_links = self.temp_data.get("video_links", [])
        pdf_links = self.temp_data.get("pdf_links", [])
        if call.data == "dl_videos":
            files = video_links
        elif call.data == "dl_pdfs":
            files = pdf_links
        else:
            files = video_links + pdf_links

        bot.send_message(call.message.chat.id, "Starting bulk download...")

        for name, url in files:
            try:
                extension = ".pdf" if ".pdf" in url else ".mp4"
                file_name = f"{name}{extension}"
                download_command = f"yt-dlp -o '{file_name}' '{url}'"

                message_id = self.download_with_progress(bot, call.message.chat.id, file_name, download_command)
                self.upload_with_progress(bot, call.message.chat.id, file_name)
                bot.send_document(call.message.chat.id, open(file_name, "rb"))
                os.remove(file_name)  # Clean up after upload
                bot.delete_message(call.message.chat.id, message_id)  # Delete download progress message
                bot.send_message(call.message.chat.id, f"✅ File `{file_name}` uploaded successfully.")
            except Exception as e:
                bot.send_message(call.message.chat.id, f"❌ Error processing `{name}`: {e}")

        bot.send_message(call.message.chat.id, "All downloads completed.")

bulk_uploader_module = BulkUploaderModule()