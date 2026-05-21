import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from yt_dlp import YoutubeDL
import glob
import os

# --- BOT CONFIGURATION (PROFESSIONAL SETUP) ---
BOT_TOKEN = "8783503279:AAEFfkiy7slMS3_cWggmiiG0wiz15HNeigQ"
CHANNEL_USERNAME = "@SIGNAL_HUNTER_X"
DEVELOPER_NAME = "Ｍʀ 𓆩✘𓆪 ♱"
DEVELOPER_USERNAME = "@MrX_OfficiaI"

bot = telebot.TeleBot(BOT_TOKEN)
user_searches = {}

def is_user_subscribed(user_id):
    try:
        status = bot.get_chat_member(CHANNEL_USERNAME, user_id).status
        return status in ['member', 'administrator', 'creator']
    except Exception:
        # ሰርቨር ላይ ችግር ካጋጠመ ተጠቃሚው እንዲያልፍ ለማድረግ
        return True 

def send_force_join_msg(chat_id):
    markup = InlineKeyboardMarkup()
    btn_join = InlineKeyboardButton(text="📢 JOIN OFFICIAL CHANNEL", url=f"https://t.me/{CHANNEL_USERNAME.replace('@','')}")
    btn_verified = InlineKeyboardButton(text="🔄 VERIFY MEMBERSHIP", callback_data="check_sub")
    markup.add(btn_join)
    markup.add(btn_verified)
    
    msg_text = (
        "🛑 <b>ACCESS DENIED</b> 🛑\n\n"
        "You must be a member of our official network to utilize this service.\n"
        f"Please join <b>{CHANNEL_USERNAME}</b> and press the verification button below."
    )
    bot.send_message(chat_id, msg_text, reply_markup=markup, parse_mode="HTML")

# --- COMMON HEADERS FOR SOUNDCLOUD BYPASS ---
SC_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
}

# --- COMMANDS ---
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    if not is_user_subscribed(message.from_user.id):
        send_force_join_msg(message.chat.id)
        return
        
    welcome_text = (
        "⚡ <b>⚡ SOUNDCLOUD PREMIUM DOWNLOADER ⚡</b> ⚡\n\n"
        "Welcome to the ultimate audio extraction terminal. Send me any track title or artist name to begin.\n\n"
        f"💻 <b>Core Architecture:</b> {DEVELOPER_NAME}\n"
        f"🛠️ <b>Network Support:</b> {DEVELOPER_USERNAME}"
    )
    bot.reply_to(message, welcome_text, parse_mode="HTML")

# --- MUSIC SEARCH HANDLING (SOUNDCLOUD) ---
@bot.message_handler(func=lambda message: True)
def search_song(message):
    if not is_user_subscribed(message.from_user.id):
        send_force_join_msg(message.chat.id)
        return

    query = message.text
    status_msg = bot.reply_to(message, "🔍 <b>Querying SoundCloud Database... Please wait.</b>", parse_mode="HTML")
    
    ydl_opts = {
        'format': 'bestaudio/best',
        'default_search': 'scsearch3',
        'noplaylist': True,
        'quiet': True,
        'nocheckcertificate': True,
        'headers': SC_HEADERS
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
                    # የልብ ቅርፅ ኢሞጂ ሙሉ በሙሉ በ 🎧 ተቀይሯል
                    button = InlineKeyboardButton(text=f"🎧 {index+1}. {title}", callback_data=f"sc_{index}")
                    markup.add(button)
                    
                user_searches[message.chat.id] = search_results
                bot.delete_message(message.chat.id, status_msg.message_id)
                bot.send_message(message.chat.id, "🎵 <b>Select the exact index to initiate download:</b>", reply_markup=markup, parse_mode="HTML")
            else:
                bot.edit_message_text("❌ <b>Error:</b> No matches found on SoundCloud.", message.chat.id, status_msg.message_id, parse_mode="HTML")
    except Exception as e:
        print(f"SoundCloud Search Error: {e}")
        bot.edit_message_text("⚠️ <b>Network Timeout:</b> Connection to SoundCloud failed. Retrying...", message.chat.id, status_msg.message_id, parse_mode="HTML")

# --- CALLBACK QUERY HANDLERS (DOWNLOAD & SUBSCRIPTION CHECK) ---
@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    chat_id = call.message.chat.id
    user_id = call.from_user.id
    
    # ቻናል መቀላቀሉን ድጋሚ ማረጋገጫ በተን ሲጫን
    if call.data == "check_sub":
        if is_user_subscribed(user_id):
            bot.answer_callback_query(call.id, "✅ Verification Successful! Access Granted.")
            bot.delete_message(chat_id, call.message.message_id)
            bot.send_message(chat_id, "⚡ <b>System Initialized.</b> You can now send track names.", parse_mode="HTML")
        else:
            bot.answer_callback_query(call.id, "❌ Verification Failed. Please join the channel first.", show_alert=True)
        return

    # ዳውንሎድ ለማድረግ ሲመረጥ
    if call.data.startswith('sc_'):
        if not is_user_subscribed(user_id):
            send_force_join_msg(chat_id)
            return

        index = int(call.data.split('_')[1])
        if chat_id not in user_searches:
            bot.answer_callback_query(call.id, "❌ Session expired. Please search again.")
            return

        selected_song = user_searches[chat_id][index]
        bot.answer_callback_query(call.id, "📥 Fetching audio stream...")
        
        try:
            bot.edit_message_text(f"🚀 <b>Extracting:</b> <code>{selected_song['title']}</code>", chat_id, call.message.message_id, parse_mode="HTML")
        except Exception:
            pass

        unique_id = f"sc_{chat_id}_{index}"
        
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': f"{unique_id}.%(ext)s",
            'noplaylist': True,
            'quiet': True,
            'nocheckcertificate': True,
            'headers': SC_HEADERS,
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
            bot.send_message(chat_id, "⚠️ <b>Download Exception:</b> Failed to extract audio. The track may be restricted or private.")

print("SoundCloud Downloader Bot is running smoothly...")
bot.infinity_polling()
