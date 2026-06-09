import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
import time
from threading import Thread
from flask import Flask
import os
import sqlite3
import json

# =====================================================================
# 🌐 FLASK SERVER FOR RENDER (Render ပေါ်တွင် Bot မအိပ်ဘဲ အမြဲနိုးနေစေရန်)
# =====================================================================
app = Flask('')

@app.route('/')
def home():
    return "Bot Is Alive!"

def run():
    # Render သည် Dynamic Port သုံးသဖြင့် Port ပတ်ဝန်းကျင်ကို ဖတ်ခိုင်းခြင်း
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.start()

# =====================================================================
# 🗄️ SQLITE DATABASE SETUP (ဒေတာများ မပျောက်ပျက်စေရန် သိမ်းဆည်းသည့်စနစ်)
# =====================================================================
DB_FILE = "vpn_bot.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    # Users Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            chat_id INTEGER PRIMARY KEY,
            name TEXT,
            username TEXT,
            coins INTEGER DEFAULT 0,
            purchased_vpns TEXT DEFAULT '[]',
            used_gb_total INTEGER DEFAULT 0,
            referred_users INTEGER DEFAULT 0
        )
    ''')
    # VPN Links Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS vpn_links (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            gb_key TEXT,
            link TEXT,
            used INTEGER DEFAULT 0,
            buyer_id INTEGER DEFAULT NULL
        )
    ''')
    # Settings Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# ดေတာဘေ့စ် အကူလုပ်ဆောင်ချက်များ
def db_get_user(chat_id):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT name, username, coins, purchased_vpns, used_gb_total, referred_users FROM users WHERE chat_id = ?", (chat_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return {
            "name": row[0],
            "username": row[1],
            "coins": row[2],
            "purchased_vpns": json.loads(row[3]),
            "used_gb_total": row[4],
            "referred_users": row[5]
        }
    return None

def db_create_or_update_user(chat_id, name="Unknown", username="None"):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    user = db_get_user(chat_id)
    if not user:
        cursor.execute("INSERT INTO users (chat_id, name, username) VALUES (?, ?, ?)", (chat_id, name, username))
    else:
        cursor.execute("UPDATE users SET name = ?, username = ? WHERE chat_id = ?", (name, username, chat_id))
    conn.commit()
    conn.close()

def db_update_user_field(chat_id, field, value):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    if field == "purchased_vpns":
        value = json.dumps(value)
    cursor.execute(f"UPDATE users SET {field} = ? WHERE chat_id = ?", (value, chat_id))
    conn.commit()
    conn.close()

def db_get_all_users():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT chat_id, name, username, coins, referred_users, used_gb_total FROM users")
    rows = cursor.fetchall()
    conn.close()
    return rows

def db_get_packages():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM settings WHERE key = 'packages'")
    row = cursor.fetchone()
    conn.close()
    if row:
        return json.loads(row[0])
    return {"5gb": 10, "10gb": 20, "50gb": 50, "100gb": 90} # Default Packages

def db_save_packages(packages):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('packages', ?)", (json.dumps(packages),))
    conn.commit()
    conn.close()

# =====================================================================
# 🤖 BOT INITIALIZATION
# =====================================================================
# လုံခြုံရေးအတွက် Token ကို Render Environment Variable မှ ဖတ်ခိုင်းထားပါသည်
TOKEN = os.environ.get("BOT_TOKEN", "8724005419:AAH2HPdjlJ2ZcdzkLdMpcJWEaDuQhWg4ls4")
bot = telebot.TeleBot(TOKEN)

ADMIN_LIST = [7592705124]  
BOT_USERNAME = None

# သင်ပြုလုပ်ထားသော မူလ Design Keyboard အတိုင်း တစ်ပုံစံတည်း ထိန်းသိမ်းထားပါသည်
def get_main_inline_keyboard():
    inline_markup = InlineKeyboardMarkup(row_width=2)
    btn_user_info = InlineKeyboardButton('👤 User Info', callback_data='user_info')
    btn_refer = InlineKeyboardButton('🔗 Refer', callback_data='refer')
    btn_gen_key = InlineKeyboardButton('🔑 Generate Key', callback_data='gen_key')
    btn_buy_credits = InlineKeyboardButton('💰 Buy Credits', callback_data='buy_credits')
    btn_channel = InlineKeyboardButton('📢 Channel ↗', url='https://t.me/starlinkfreezone')
    
    inline_markup.add(btn_user_info, btn_refer)      
    inline_markup.add(btn_gen_key, btn_buy_credits)
    inline_markup.add(btn_channel)   
    return inline_markup

def get_v2box_inline_keyboard():
    gb_markup = InlineKeyboardMarkup(row_width=2)
    buttons = []
    packages = db_get_packages()
    for gb, coin in packages.items():
        buttons.append(InlineKeyboardButton(f"📦 {gb.upper()} ({coin} Coins)", callback_data=f"buy_v2box_{gb}"))
    
    gb_markup.add(*buttons)
    gb_markup.add(InlineKeyboardButton('🔙 Back', callback_data='back_to_vpn_types'))
    return gb_markup

def check_and_create_user(message_or_id):
    if isinstance(message_or_id, int):
        db_create_or_update_user(message_or_id)
    else:
        chat_id = message_or_id.chat.id
        name = message_or_id.from_user.first_name
        username = message_or_id.from_user.username if message_or_id.from_user.username else "None"
        db_create_or_update_user(chat_id, name, username)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    chat_id = message.chat.id
    command_args = message.text.split()
    is_new_user = (db_get_user(chat_id) is None)
    
    check_and_create_user(message)
    
    if len(command_args) > 1 and is_new_user:
        referrer_id = command_args[1]
        try:
            referrer_id = int(referrer_id)
            if referrer_id != chat_id:
                ref_user = db_get_user(referrer_id)
                if ref_user:
                    db_update_user_field(referrer_id, "coins", ref_user["coins"] + 1)
                    db_update_user_field(referrer_id, "referred_users", ref_user["referred_users"] + 1)
                    try:
                        bot.send_message(referrer_id, f"🎉 အဖွဲ့ဝင်သစ်တစ်ဦး သင့် Link မှတစ်ဆင့် ဆက်သွယ်ဝင်ရောက်လာသဖြင့် သင့်ထံ **+1 Coin** ထည့်သွင်းပေးလိုက်ပါပြီ။", parse_mode='Markdown')
                    except: pass
        except ValueError: pass

    reply_markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    btn_how_to_use = KeyboardButton('📖 VPN အသုံးပြုနည်း')
    reply_markup.add(btn_how_to_use)
    
    welcome_text = "✨ Premium VPN Bot မှ ကြိုဆိုပါတယ်ဗျာ။\nအောက်ပါ ခလုတ်များကို အသုံးပြုနိုင်ပါတယ်-"
    bot.send_message(message.chat.id, welcome_text, reply_markup=reply_markup)
    bot.send_message(message.chat.id, "👉 လိုအပ်ရာ လုပ်ဆောင်ချက်ကို နှိပ်ပါ -", reply_markup=get_main_inline_keyboard())

@bot.message_handler(func=lambda message: message.text == '📖 VPN အသုံးပြုနည်း')
def how_to_use_handler(message):
    link_markup = InlineKeyboardMarkup()
    btn_link = InlineKeyboardButton('🔗 ဒီနေရာကို နှိပ်ပြီး အသုံးပြုနည်းကြည့်ရန်', url='https://t.me/starlinkfreezone/7')
    link_markup.add(btn_link)
    bot.send_message(message.chat.id, "💡 VPN အသုံးပြုနည်းကို လေ့လာရန် အောက်ပါ ခလုတ် သို့မဟုတ် Link ကို နှိပ်ပါဗျာ။\n\n👉 https://t.me/starlinkfreezone/7", reply_markup=link_markup)

# =====================================================================
# 👑 ADMIN COMMANDS SECTION (မူလအတိုင်း မပြောင်းလဲပါ)
# =====================================================================
@bot.message_handler(commands=['ac'])
def admin_commands_list(message):
    if message.chat.id not in ADMIN_LIST: return
    ac_text = (
        "👑 **Admin Command List & Manual**\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "👥 `/ul` - Bot အသုံးပြုနေသော User စာရင်းကြည့်ရန်။\n\n"
        "💰 `/coinadd <chat_id> <amount>` - User ထံ Coin ထည့်ပေးရန်။\n"
        "📉 `/coindelete <chat_id> <amount>` - User ထံမှ Coin နှုတ်ယူရန်။\n"
        "💰 `/pu <gb> <coins>` - Package ဈေးနှုန်း သတ်မှတ်/ပြင်ဆင်ရန်။\n"
        "❌ `/pu <gb> delete` - Package ကို ပြန်ဖျက်ရန်။\n\n"
        "🔗 `/5gb <link>` , `/10gb <link>` စသဖြင့် VPN Link အသစ်ထည့်ရန်။\n\n"
        "🔥 `/deletelink <gb> <link>` - Stock ထဲမှ VPN Link အား ရှာဖွေဖျက်ထုတ်ရန်။\n"
        "➕ `/addadmin <chat_id>` - Admin အသစ် ထပ်တိုးထည့်သွင်းရန်။\n"
        "📊 `/gbl` - လက်ရှိ VPN Links လက်ကျန်စာရင်း ကြည့်ရန်။\n\n"
        "📢 `/am <စာသား>` - User အားလုံးထံ စာတစ်ပြိုင်နက် ပို့ရန် (Broadcast)။\n"
        "━━━━━━━━━━━━━━━━━━━━"
    )
    bot.send_message(message.chat.id, ac_text, parse_mode='Markdown')

@bot.message_handler(commands=['coinadd', 'ca'])
def admin_coin_add(message):
    if message.chat.id not in ADMIN_LIST: return
    args = message.text.split()
    if len(args) < 3: return
    try:
        target_id = int(args[1])
        amount = int(args[2])
        check_and_create_user(target_id)
        user = db_get_user(target_id)
        new_coins = user["coins"] + amount
        db_update_user_field(target_id, "coins", new_coins)
        bot.send_message(message.chat.id, f"✅ Chat ID: `{target_id}` ထံသို့ **+{amount} Coins** ထည့်ပြီးပါပြီ။")
        try:
            bot.send_message(target_id, f"🎁 Admin မှ သင့်ထံသို့ **+{amount} Coins** ထည့်သွင်းပေးလိုက်ပါပြီ။\nလက်ကျန်: **{new_coins} Coins**")
        except: pass
    except ValueError: pass

@bot.message_handler(commands=['coindelete', 'cd'])
def admin_coin_delete(message):
    if message.chat.id not in ADMIN_LIST: return
    args = message.text.split()
    if len(args) < 3: return
    try:
        target_id = int(args[1])
        amount = int(args[2])
        user = db_get_user(target_id)
        if not user: return
        new_coins = max(0, user["coins"] - amount)
        db_update_user_field(target_id, "coins", new_coins)
        bot.send_message(message.chat.id, f"✅ Chat ID: `{target_id}` ထံမှ **-{amount} Coins** နှုတ်ပြီးပါပြီ။")
    except ValueError: pass

@bot.message_handler(commands=['addadmin', 'aa'])
def admin_add_new_admin(message):
    if message.chat.id not in ADMIN_LIST: return
    args = message.text.split()
    if len(args) < 2: return
    try:
        new_admin_id = int(args[1])
        if new_admin_id not in ADMIN_LIST:
            ADMIN_LIST.append(new_admin_id)
            bot.send_message(message.chat.id, f"✅ Chat ID: `{new_admin_id}` အား Admin အဖြစ် ခန့်အပ်ပြီးပါပြီ။")
    except ValueError: pass

@bot.message_handler(commands=['deletelink', 'dl'])
def admin_delete_vpn_link(message):
    if message.chat.id not in ADMIN_LIST: return
    args = message.text.split()
    if len(args) < 3: return
    gb_key = args[1].lower()
    target_link = message.text.split(None, 2)[2].strip()
    
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM vpn_links WHERE gb_key = ? AND link = ?", (gb_key, target_link))
    if cursor.rowcount > 0:
        bot.send_message(message.chat.id, "✅ VPN Link ကို ဖျက်ပြီးပါပြီ။")
    conn.commit()
    conn.close()

@bot.message_handler(commands=['ul'])
def admin_user_list(message):
    if message.chat.id not in ADMIN_LIST: return
    users = db_get_all_users()
    if not users: return
    ul_text = "👥 **Bot Users List**\n━━━━━━━━━━━━━━━━━━━━\n"
    for uid, name, username, coins, ref, used_gb in users:
        ul_text += f" Xian: {name} | @{username}\n🆔 ID: `{uid}` | Coins: {coins} | Ref: {ref}\n📊 Used: {used_gb} GB\n-----------\n"
    bot.send_message(message.chat.id, ul_text, parse_mode='Markdown')

@bot.message_handler(commands=['pu'])
def admin_package_update(message):
    if message.chat.id not in ADMIN_LIST: return
    args = message.text.split()
    if len(args) < 3: return
    gb_input = args[1].lower()
    action_or_coin = args[2].lower()
    
    packages = db_get_packages()
    if action_or_coin == 'delete':
        if gb_input in packages: 
            del packages[gb_input]
            db_save_packages(packages)
            bot.send_message(message.chat.id, f"❌ Package {gb_input.upper()} ကို ဖျက်လိုက်ပါပြီ။")
    else:
        try:
            packages[gb_input] = int(action_or_coin)
            db_save_packages(packages)
            bot.send_message(message.chat.id, f"✅ Package {gb_input.upper()} ပြင်ဆင်မှု အောင်မြင်သည်။")
        except ValueError: pass

@bot.message_handler(func=lambda message: message.text.split()[0].lower() in ['/5gb', '/10gb', '/50gb', '/100gb'])
def admin_add_vpn_links(message):
    if message.chat.id not in ADMIN_LIST: return
    cmd = message.text.split()[0].lower()
    gb_key = cmd.replace('/', '')
    link_data = message.text[len(cmd):].strip()
    if not link_data: return
    incoming_links = [l.strip() for l in link_data.split('\n') if l.strip()]
    
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    for l in incoming_links:
        cursor.execute("INSERT INTO vpn_links (gb_key, link) VALUES (?, ?)", (gb_key, l))
    conn.commit()
    conn.close()
    bot.send_message(message.chat.id, f"✅ {gb_key.upper()} သို့ လင့်ခ် {len(incoming_links)} ခု ထည့်ပြီးပါပြီ။")

@bot.message_handler(commands=['gbl'])
def admin_view_links_status(message):
    if message.chat.id not in ADMIN_LIST: return
    gbl_text = "📊 **VPN Links Stock**\n"
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    packages = db_get_packages()
    for gb in packages.keys():
        cursor.execute("SELECT COUNT(*) FROM vpn_links WHERE gb_key = ? AND used = 0", (gb,))
        avail = cursor.fetchone()[0]
        gbl_text += f"📂 **{gb.upper()}:** လက်ကျန် {avail} ခု\n"
    conn.close()
    bot.send_message(message.chat.id, gbl_text, parse_mode='Markdown')

@bot.message_handler(commands=['am'])
def admin_broadcast_message(message):
    if message.chat.id not in ADMIN_LIST: return
    broadcast_msg = message.text[4:].strip()
    if not broadcast_msg: return
    users = db_get_all_users()
    for row in users:
        try: bot.send_message(row[0], broadcast_msg)
        except: pass
    bot.send_message(message.chat.id, "✅ Broadcast ပို့ဆောင်ပြီးပါပြီ။")

# =====================================================================
# CALLBACK QUERY LISTENERS (USER INTERFACES - မူလ Design အတိုင်း)
# =====================================================================
@bot.callback_query_handler(func=lambda call: True)
def callback_listener(call):
    bot.answer_callback_query(call.id)
    chat_id = call.message.chat.id
    check_and_create_user(call.message)
    
    if call.data == 'user_info':
        user_data = db_get_user(chat_id)
        vpns = user_data["purchased_vpns"]
        vpn_history_text = ""
        if len(vpns) > 0:
            for idx, vpn in enumerate(vpns, 1):
                vpn_history_text += f"   {idx}. {vpn['type'].upper()} - ({vpn['date']})\n"
        else:
            vpn_history_text = "   ❌ ဝယ်ယူမှု စာရင်းမရှိသေးပါ။\n"
            
        info_text = (
            "👤 **User Information**\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            f"🆔 **Chat ID:** `{chat_id}`\n"
            f"💰 **Coin လက်ကျန်:** {user_data['coins']} Coins\n"
            f"👥 **ဖိတ်ခေါ်ထားသော လူဦးရေ:** {user_data['referred_users']} ယောက်\n"
            f"📦 **ဝယ်ယူပြီးသော VPN အရေအတွက်:** {len(vpns)} ခု\n\n"
            f"📋 **ဝယ်ယူခဲ့ဖူးသည့် အမျိုးအစားနှင့် နေ့စွဲများ:**\n{vpn_history_text}"
            "━━━━━━━━━━━━━━━━━━━━"
        )
        back_markup = InlineKeyboardMarkup()
        back_markup.add(InlineKeyboardButton('🔙 Back', callback_data='back_to_main'))
        bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id, text=info_text, parse_mode='Markdown', reply_markup=back_markup)
        
    elif call.data == 'refer':
        user_data = db_get_user(chat_id)
        referral_link = f"https://t.me/{BOT_USERNAME}?start={chat_id}"
        refer_text = (
            "🔗 **Referral System (မိတ်ဆက်ခြင်း စနစ်)**\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "သင့်ရဲ့ Referral Link ကို အသုံးပြုပြီး သူငယ်ချင်းများကို ဖိတ်ခေါ်ပါ။\n"
            "လူသစ်တစ်ယောက် ဝင်လာတိုင်း **1 Coin Free** ရရှိပါမည်။ 🎁\n\n"
            f"👥 **ဖိတ်ခေါ်ပြီးသမျှ လူဦးရေ:** {user_data['referred_users']} ယောက်\n\n"
            f"👇 **သင့်ရဲ့ ဖိတ်ခေါ်ရန် Link:**\n`{referral_link}`\n"
            "━━━━━━━━━━━━━━━━━━━━"
        )
        back_markup = InlineKeyboardMarkup()
        back_markup.add(InlineKeyboardButton('🔙 Back', callback_data='back_to_main'))
        bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id, text=refer_text, parse_mode='Markdown', reply_markup=back_markup)

    elif call.data == 'gen_key':
        vpn_type_markup = InlineKeyboardMarkup(row_width=1)
        vpn_type_markup.add(InlineKeyboardButton('🚀 V2BOX VPN', callback_data='v2box_menu'), InlineKeyboardButton('🔙 Back', callback_data='back_to_main'))
        bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id, text="🔑 **Generate Key (Key ထုတ်ယူခြင်း)**\n\nအသုံးပြုလိုသော VPN Type ကို ရွေးချယ်ပေးပါ-", parse_mode='Markdown', reply_markup=vpn_type_markup)

    elif call.data == 'v2box_menu':
        v2box_text = "🚀 **V2BOX VPN Packages**\n━━━━━━━━━━━━━━━━━━━━\nသင်ဝယ်ယူလိုသော GB ပမာဏကို ရွေးချယ်ပေးပါဗျာ。\nသင့်အကောင့်ထဲတွင် လုံလောက်သော Coin ရှိရန် လိုအပ်ပါသည်။\n━━━━━━━━━━━━━━━━━━━━"
        bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id, text=v2box_text, parse_mode='Markdown', reply_markup=get_v2box_inline_keyboard())

    elif call.data == 'back_to_vpn_types':
        vpn_type_markup = InlineKeyboardMarkup(row_width=1)
        vpn_type_markup.add(InlineKeyboardButton('🚀 V2BOX VPN', callback_data='v2box_menu'), InlineKeyboardButton('🔙 Back', callback_data='back_to_main'))
        bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id, text="🔑 **Generate Key (Key ထုတ်ယူခြင်း)**\n\nအသုံးပြုလိုသော VPN Type ကို ရွေးချယ်ပေးပါ-", parse_mode='Markdown', reply_markup=vpn_type_markup)

    elif call.data == 'buy_credits':
        buy_text = "💰 **Coin ဝယ်ယူရန် နည်းလမ်းများ**\n━━━━━━━━━━━━━━━━━━━━\nCoin ဝယ်ယူလိုပါက အောက်ဖော်ပြပါ တာဝန်ခံ Admin များထံသို့ တိုက်ရိုက် ဆက်သွယ်စုံစမ်း ဝယ်ယူနိုင်ပါတယ်ဗျာ။\n━━━━━━━━━━━━━━━━━━━━"
        buy_markup = InlineKeyboardMarkup(row_width=1)
        buy_markup.add(InlineKeyboardButton('👨‍💻 Admin Elonmusk', url='https://t.me/Elonmusk20606'), InlineKeyboardButton('👨‍💻 Admin mgzan', url='https://t.me/mgzan201'), InlineKeyboardButton('🔙 Back', callback_data='back_to_main'))
        bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id, text=buy_text, parse_mode='Markdown', reply_markup=buy_markup)

    elif call.data == 'back_to_main':
        bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id, text="👉 လိုအပ်ရာ လုပ်ဆောင်ချက်ကို နှိပ်ပါ -", reply_markup=get_main_inline_keyboard())
        
    elif call.data.startswith('buy_v2box_'):
        selected_package = call.data.split('_')[2]
        packages = db_get_packages()
        coin_needed = packages.get(selected_package, 99999)
        user_data = db_get_user(chat_id)
        
        if user_data["coins"] < coin_needed:
            bot.send_message(chat_id, f"❌ ဝယ်ယူရန် Coin မလုံလောက်ပါ။ {selected_package.upper()} အတွက် {coin_needed} Coins လိုအပ်သော်လည်း သင့်တွင် {user_data['coins']} Coins သာ ရှိပါသည်။")
            return
            
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT id, link FROM vpn_links WHERE gb_key = ? AND used = 0 LIMIT 1", (selected_package,))
        row = cursor.fetchone()
        
        if not row:
            bot.send_message(chat_id, f"❌ စိတ်မကောင်းပါဘူးဗျာ၊ လောလောဆယ် {selected_package.upper()} အတွက် အသင့်သုံး VPN Link လက်ကျန် ပြတ်လပ်နေပါသည်။ ကျေးဇူးပြု၍ ခေတ္တစောင့်ဆိုင်းပြီးမှ ပြန်ဝယ်ယူပါ။")
            conn.close()
            return
            
        link_id, vpn_link = row
        cursor.execute("UPDATE vpn_links SET used = 1, buyer_id = ? WHERE id = ?", (chat_id, link_id))
        conn.commit()
        conn.close()
        
        # Update User data
        db_update_user_field(chat_id, "coins", user_data["coins"] - coin_needed)
        try:
            gb_amount = int(selected_package.replace('gb', ''))
            db_update_user_field(chat_id, "used_gb_total", user_data["used_gb_total"] + gb_amount)
        except ValueError: pass
            
        current_date = time.strftime("%Y-%m-%d %H:%M:%S")
        user_data["purchased_vpns"].append({"type": f"V2BOX {selected_package.upper()}", "date": current_date})
        db_update_user_field(chat_id, "purchased_vpns", user_data["purchased_vpns"])
        
        success_text = (
            f"🎉 **ဝယ်ယူမှု အောင်မြင်ပါသည်!**\n\n"
            f"📦 **အမျိုးအစား:** V2BOX {selected_package.upper()}\n"
            f"📉 **နှုတ်ယူပြီး Coin:** -{coin_needed} Coins\n"
            f"💰 **လက်ကျန် Coin:** {user_data['coins'] - coin_needed} Coins\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"👇 **သင့်ရဲ့ VPN Link (အောက်ပါစာသားကို ကော်ပီကူးယူပါ) :**\n"
            f"`{vpn_link}`\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"💡 ၎င်း Link ကို ကော်ပီယူ၍ V2BOX Application ထဲတွင် ထည့်သွင်းအသုံးပြုနိုင်ပါပြီ။"
        )
        bot.send_message(chat_id, success_text, parse_mode='Markdown')
        
        for admin_id in ADMIN_LIST:
            try: bot.send_message(admin_id, f"🔔 **Notification:** User `{user_data['name']}` (ID: `{chat_id}`) သည် V2BOX {selected_package.upper()} အား ဝယ်ယူသွားခဲ့ပြီး Stock မှ လင့်ခ်တစ်ခု လျော့နည်းသွားပါပြီ။")
            except: pass

# Flask Web Server ကို နောက်ကွယ်တွင် အရင်နိုးမည်
print("Starting Web Server for Render...")
keep_alive()

print("Bot အချက်အလက်များ စစ်ဆေးနေပါပြီ...")
BOT_USERNAME = bot.get_me().username
print(f"Bot Username: @{BOT_USERNAME}")
print("Bot စတင် အလုပ်လုပ်နေပါပြီ...")
bot.infinity_polling()
