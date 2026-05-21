import os
import glob
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from yt_dlp import YoutubeDL

# --- CONFIGURATION ---
BOT_TOKEN = "8783503279:AAEFfkiy7slMS3_cWggmiiG0wiz15HNeigQ"
CHANNEL_USERNAME = "@SIGNAL_HUNTER_X"  
DEVELOPER_NAME = "Ｍʀ 𓆩✘𓆪 ♱"
DEVELOPER_USERNAME = "@MrX_OfficiaI"

bot = telebot.TeleBot(BOT_TOKEN)
user_searches = {}

# --- FUNCTION TO CHECK CHANNEL MEMBERSHIP ---
def is_user_subscribed(user_id):
    try:
        member = bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in ['member', 'administrator', 'creator']
    except Exception as e:
        print(f"Subscription Check Error: {e}")
        return False

# --- FORCE JOIN MESSAGE SYSTEM ---
def send_force_join_msg(chat_id):
    markup = InlineKeyboardMarkup()
    btn_join = InlineKeyboardButton(text="📢 Join Channel", url=f"https://t.me/{CHANNEL_USERNAME.replace('@', '')}")
    btn_verified = InlineKeyboardButton(text="🔄 Verified / Check Again", callback_data="check_sub")
    markup.add(btn_join, btn_verified)
    
    msg_text = (
        "⚠️ <b>Access Denied!</b>\n\n"
        f"You must join our official channel to use this bot.\n"
        f"Please join {CHANNEL_USERNAME} and click the verified button below."
    )
    bot.send_message(chat_id, msg_text, reply_markup=markup, parse_mode="HTML")

# --- COMMANDS ---
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    if not is_user_subscribed(message.from_user.id):
        send_force_join_msg(message.chat.id)
        return
        
    welcome_text = (
        "🎵 <b>Welcome to Premium SoundCloud Downloader Bot!</b>\n\n"
        "Send me any song title or artist name to download directly from SoundCloud.\n\n"
        f"👤 <b>Developer:</b> {DEVELOPER_NAME}\n"
        f"💬 <b>Support:</b> {DEVELOPER_USERNAME}"
    )
    bot.reply_to(message, welcome_text, parse_mode="HTML")

# --- MUSIC SEARCH HANDLING (SOUNDCLOUD) ---
@bot.message_handler(func=lambda message: True)
def search_song(message):
    if not is_user_subscribed(message.from_user.id):
        send_force_join_msg(message.chat.id)
        return
        
    query = message.text
    status_msg = bot.reply_to(message, "🔍 <b>Searching SoundCloud...</b> Please wait.", parse_mode="HTML")
    
    # 🔥 ለሳውንድክላውድ የተስተካከለ አምራጭ (ምንም ኩኪስ አይፈልግም)
    ydl_opts = {
        'format': 'bestaudio/best',
        'default_search': 'scsearch3', # 3 ምርጥ የሳውንድክላውድ ውጤቶችን ይፈልጋል
        'noplaylist': True,
        'quiet': True,
    }
    
    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(query, download=False)
            if 'entries' in info and len(info['entries']) > 0:
                markup = InlineKeyboardMarkup()
                search_results = []
                
                for index, entry in enumerate(info['entries']):
                    title = entry.get('title', 'Unknown Track')[:35]
                    search_results.append({'title': entry.get('title'), 'url': entry.get('webpage_url')})
                    button = InlineKeyboardButton(text=f"🧡 {index+1}. {title}", callback_data=f"sc_{index}")
                    markup.add(button)
                
                user_searches[message.chat.id] = search_results
                bot.delete_message(message.chat.id, status_msg.message_id)
                bot.send_message(message.chat.id, "🎵 <b>Select a track to download from SoundCloud:</b>", reply_markup=markup, parse_mode="HTML")
            else:
                bot.edit_message_text("❌ No results found on SoundCloud. Please try another name.", message.chat.id, status_msg.message_id)
    except Exception as e:
        print(f"SoundCloud Search Error: {e}")
        bot.edit_message_text("⚠️ Connection error with SoundCloud. Please try again.", message.chat.id, status_msg.message_id)

# --- CALLBACK QUERY HANDLERS ---
@bot.callback_query_handler(func=lambda call: True)
def handle_callbacks(call):
    chat_id = call.message.chat.id
    user_id = call.from_user.id
    
    if call.data == "check_sub":
        if is_user_subscribed(user_id):
            bot.answer_callback_query(call.id, "✅ Verification Successful! Enjoy.", show_alert=True)
            bot.delete_message(chat_id, call.message.message_id)
            bot.send_message(chat_id, "🎉 <b>Access Granted!</b> Send me a song name now.", parse_mode="HTML")
        else:
            bot.answer_callback_query(call.id, "❌ You haven't joined the channel yet!", show_alert=True)
        return

    if call.data.startswith('sc_'):
        if not is_user_subscribed(user_id):
            bot.answer_callback_query(call.id, "⚠️ Channel membership required!", show_alert=True)
            send_force_join_msg(chat_id)
            return
            
        index = int(call.data.split('_')[1])
        if chat_id not in user_searches:
            return
        
        selected_song = user_searches[chat_id][index]
        bot.answer_callback_query(call.id, "📥 Downloading track from SoundCloud...")
        
        try:
            bot.edit_message_text(f"🚀 Downloading: <b>{selected_song['title']}</b>...", chat_id, call.message.message_id, parse_mode="HTML")
        except Exception:
            pass
            
        unique_id = f"sc_{chat_id}_{index}"
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': f"{unique_id}.%(ext)s",
            'noplaylist': True,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        }
            
        try:
            with YoutubeDL(ydl_opts) as ydl:
                ydl.download([selected_song['url']])
                
            downloaded_files = glob.glob(f"{unique_id}.*")
            if downloaded_files:
                actual_filename = downloaded_files[0]
                with open(actual_filename, 'rb') as audio:
                    bot.send_audio(chat_id, audio, title=selected_song['title'])
                os.remove(actual_filename)
                try:
                    bot.delete_message(chat_id, call.message.message_id)
                except Exception:
                    pass
        except Exception as e:
            print(f"SoundCloud Download Error: {e}")
            bot.send_message(chat_id, "⚠️ Download failed. Please try again.", parse_mode="HTML")

print("SoundCloud Downloader Bot is running smoothly...")
bot.infinity_polling()





