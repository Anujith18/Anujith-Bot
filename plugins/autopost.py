import re
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from info import MAIN_CHANNEL_ID, FILE_STORE_CHANNEL, AUTO_POST, CUSTOM_CAPTION, BOT_USERNAME

# ഫയൽ നെയിമിൽ നിന്ന് എപ്പിസോഡും ക്വാളിറ്റിയും വേർതിരിച്ചെടുക്കാനുള്ള ഫങ്ക്ഷൻ
def get_file_details(file_name):
    ep_match = re.search(r'(?:E|Ep|Episode)\s*(\d+)', file_name, re.IGNORECASE)
    episode = ep_match.group(1) if ep_match else "Unknown"
    
    if "480p" in file_name: quality = "480p"
    elif "720p" in file_name: quality = "720p"
    elif "1080p" in file_name: quality = "1080p"
    else: quality = "HD"
    
    return episode, quality

@Client.on_message(filters.document & filters.chat(FILE_STORE_CHANNEL))
async def auto_post_handler(bot, message):
    if AUTO_POST:
        file_name = message.document.file_name
        file_id = message.document.file_id
        
        episode, quality = get_file_details(file_name)
        season = "01" 
        
        caption = CUSTOM_CAPTION.format(
            file_name=file_name,
            season=season,
            episode=episode,
            quality=quality
        )
        
        share_link = f"https://t.me/{BOT_USERNAME}?start=file_{file_id}"
        reply_markup = InlineKeyboardMarkup([
            [InlineKeyboardButton("📩 Get File", url=share_link)]
        ])
        
        await bot.send_message(
            chat_id=MAIN_CHANNEL_ID,
            text=caption,
            reply_markup=reply_markup
        )
        
