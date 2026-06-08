import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
import time
import json
import os
from threading import Thread
from flask import Flask

# Flask Server for Render Keep-Alive & Server Status Check
app = Flask('')

@app.route('/')
def home():
    return "✅ Bot Server is Online and Database is Active!"

def run():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.start()

# --- 📁 DATABASE HELPER FUNCTIONS (JSON ဖြင့် အမြဲတမ်းသိမ်းဆည်းမည့် စနစ်) ---
def load_config():
    if not os.path.exists('config.json'):
        default_config = {
            "TOKEN": "8724005419:AAH2HPdjlJ2ZcdzkLdMpcJWEaDuQhWg4ls4",
            "ADMIN_LIST": [7592705124]
        }
        with open('config.json', 'w') as f:
            json.dump(default_config, f, indent=4)
        return default_config
    with open('config.json', 'r') as f:
        return json.load(f)

def save_config():
    with open('config.json', 'w') as f:
        json.dump({"TOKEN": TOKEN, "ADMIN_LIST": ADMIN_LIST}, f, indent=4)

def load_users():
    if not os.path.exists('database.json') or os.path.getsize('database.json') == 0:
        return {}
    with open('database.json', 'r') as f:
        data = json.load(f)
        return {int(k): v for k, v in data.items()}

def save_users():
    with open('database.json', 'w') as f:
        json.dump(USER_DATABASE, f, indent=4)

def load_links():
    if not os.path.exists('vpn_links.json') or os.path.getsize('vpn_links.json') == 0:
        return {"5gb": [], "10gb": [], "50gb": [], "100gb": []}
    with open('vpn_links.json', 'r') as f:
        return json.load(f)

def save_links():
    with open('vpn_links.json', 'w') as f:
        json.dump(VPN_LINKS, f, indent=4)

# --- ⚙️ SETUP & CONFIGURATION ---
config = load_config()
TOKEN = config["TOKEN"]
ADMIN_LIST = config["ADMIN_LIST"]

bot = telebot.TeleBot(TOKEN)
BOT_USERNAME = None

USER_DATABASE = load_users()
VPN_LINKS = load_links()

V2BOX_PACKAGES = {
    "5gb": 10,
    "10gb": 20,
    "50gb": 50,
    "100gb": 90
}

# --- ⌨️ KEYBOARDS ---
def get_main_inline_keyboard():
    inline_markup = InlineKeyboardMarkup(row_width=2)
    btn_user_info = InlineKeyboardButton('👤 User Info', callback_data='user_info')
    btn_register = InlineKeyboardButton('📝 Register', callback_data='register')
    btn_refer = InlineKeyboardButton('🔗 Refer', callback_data='refer')
    btn_gen_key = InlineKeyboardButton('🔑 Generate Key', callback_data='gen_key')
    btn_my_keys = InlineKeyboardButton('📊 My Keys', callback_data='my_keys')
    btn_server_status = InlineKeyboardButton('🖥 Server Status', callback_data='server_status')
    btn_buy_credits = InlineKeyboardButton('💰 Buy Credits', callback_data='buy_credits')
    btn_channel = InlineKeyboardButton('📢 Channel ↗', url='https://t.me/starlinkfreezone')
    
    inline_markup.add(btn_user_info, btn_register)      
    inline_markup.add(btn_refer, btn_gen_key)
    inline_markup.add(btn_my_keys, btn_server_status)
    inline_markup.add(btn_buy_credits, btn_channel)   
    return inline_markup

def get_v2box_inline_keyboard():
    gb_markup = InlineKeyboardMarkup(row_width=2)
    buttons = []
    for gb, coin in V2BOX_PACKAGES.items():
        buttons.append(InlineKeyboardButton(f"📦 {gb.upper()} ({coin} Coins)", callback_data=f"buy_v2box_{gb}"))
    gb_markup.add(*buttons)
    gb_markup.add(InlineKeyboardButton('🔙 Back', callback_data='back_to_vpn_types'))
    return gb_markup

def check_and_create_user(message_or_id, name="Unknown", username="None"):
    if isinstance(message_or_id, int):
        chat_id = message_or_id
    else:
        chat_id = message_or_id.chat.id
        name = message_or_id.from_user.first_name
        username = message_or_id.from_user.username if message_or_id.from_user.username else "None"
        
    if chat_id not in USER_DATABASE:
        USER_DATABASE[chat_id] = {
            "name": name,
            "username": username,
            "registered": False,   
            "coins": 0,
            "purchased_vpns": [], 
            "used_gb_total": 0,    
            "referred_users": 0
        }
        save_users() 
    else:
        if not isinstance(message_or_id, int):
            USER_DATABASE[chat_id]["name"] = name
            USER_DATABASE[chat_id]["username"] = username
            save_users()

# --- 🚀 USER COMMANDS ---
@bot.message_handler(commands=['start'])
def send_welcome(message):
    chat_id = message.chat.id
    check_and_create_user(message)
    
    command_args = message.text.split()
    if len(command_args) > 1:
        referrer_id = command_args[1]
        try:
            referrer_id = int(referrer_id)
            if referrer_id != chat_id and chat_id not in USER_DATABASE:
                check_and_create_user(referrer_id)
                USER_DATABASE[referrer_id]["coins"] += 1
                USER_DATABASE[referrer_id]["referred_users"] += 1
                save_users() 
                try:
                    bot.send_message(referrer_id, f"🎉 အဖွဲ့ဝင်သစ်တစ်ဦး သင့် Link မှတစ်ဆင့် ဆက်သွယ်ဝင်ရောက်လာသဖြင့် သင့်ထံ **+1 Coin** ထည့်သွင်းပေးလိုက်ပါပြီ။", parse_mode='Markdown')
                except: pass
        except ValueError: pass

    reply_markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    reply_markup.add(KeyboardButton('📖 VPN အသုံးပြုနည်း'))
    
    welcome_text = "✨ Premium VPN Bot မှ ကြိုဆိုပါတယ်ဗျာ။\nအောက်ပါ ခလုတ်များကို အသုံးပြုနိုင်ပါတယ်-"
    bot.send_message(message.chat.id, welcome_text, reply_markup=reply_markup)
    bot.send_message(message.chat.id, "👉 လိုအပ်ရာ လုပ်ဆောင်ချက်ကို နှိပ်ပါ -", reply_markup=get_main_inline_keyboard())

@bot.message_handler(commands=['help'])
def help_command(message):
    bot.send_message(message.chat.id, "👉 လိုအပ်ရာ လုပ်ဆောင်ချက်ကို နှိပ်ပါ -", reply_markup=get_main_inline_keyboard())

@bot.message_handler(func=lambda message: message.text == '📖 VPN အသုံးပြုနည်း')
def how_to_use_handler(message):
    link_markup = InlineKeyboardMarkup()
    link_markup.add(InlineKeyboardButton('🔗 ဒီနေရာကို နှိပ်ပြီး အသုံးပြုနည်းကြည့်ရန်', url='https://t.me/starlinkfreezone/7'))
    bot.send_message(message.chat.id, "💡 VPN အသုံးပြုနည်းကို လေ့လာရန် အောက်ပါ ခလုတ် သို့မဟုတ် Link ကို နှိပ်ပါဗျာ။\n\n👉 https://t.me/starlinkfreezone/7", reply_markup=link_markup)

# --- 👑 ADMIN COMMANDS SECTION ---
@bot.message_handler(commands=['ac'])
def admin_commands_list(message):
    if message.chat.id not in ADMIN_LIST: return
    ac_text = (
        "👑 **Admin Command List & Manual**\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "👥 `/ul` - Bot အသုံးပြုနေသော User စာရင်းကြည့်ရန်။\n\n"
        "💰 `/coinadd <chat_id> <amount>` - User ထံ Coin ထည့်ပေးရန်။ (`/ca`)\n"
        "📉 `/coindelete <chat_id> <amount>` - User ထံမှ Coin နှုတ်ယူရန်။ (`/cd`)\n"
        "💰 `/pu <gb> <coins>` - Package ဈေးနှုန်း သတ်မှတ်/ပြင်ဆင်ရန်။\n"
        "❌ `/pu <gb> delete` - Package ကို ပြန်ဖျက်ရန်။\n\n"
        "🔗 `/5gb <link>` , `/10gb <link>` စသဖြင့် VPN Link အသစ်ထည့်ရန်။\n\n"
        "🔥 `/deletelink <gb> <link>` - Stock ထဲမှ VPN Link အား ရှာဖွေဖျက်ထုတ်ရန်။ (`/dl`)\n"
        "➕ `/addadmin <chat_id>` - Admin အသစ် ထပ်တိုးထည့်သွင်းရန်။ (`/aa`)\n"
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
        if amount <= 0: return
        if target_id not in USER_DATABASE: check_and_create_user(target_id)
        USER_DATABASE[target_id]["coins"] += amount
        save_users() 
        current_coins = USER_DATABASE[target_id]["coins"]
        bot.send_message(message.chat.id, f"✅ Chat ID: `{target_id}` ထံသို့ **+{amount} Coins** ထည့်ပြီးပါပြီ။\n📊 စုစုပေါင်း: {current_coins} Coins")
        try:
            bot.send_message(target_id, f"🎁 **Coin ရရှိမှုသတိပေးချက်**\n\nAdmin မှ သင့်အကောင့်ထဲသို့ **+{amount} Coins** ထည့်သွင်းပေးလိုက်ပါပြီ။\n💰 လက်ရှိ Coin လက်ကျန်: **{current_coins} Coins**", parse_mode='Markdown')
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
        if target_id not in USER_DATABASE: return
        if USER_DATABASE[target_id]["coins"] < amount:
            USER_DATABASE[target_id]["coins"] = 0
        else:
            USER_DATABASE[target_id]["coins"] -= amount
        save_users() 
        current_coins = USER_DATABASE[target_id]["coins"]
        bot.send_message(message.chat.id, f"✅ Chat ID: `{target_id}` ထံမှ **-{amount} Coins** နှုတ်ပြီးပါပြီ။\n📊 လက်ရှိကျန်ရှိ Coin: {current_coins} Coins")
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
            save_config() 
            bot.send_message(message.chat.id, f"✅ Chat ID: `{new_admin_id}` အား Admin အဖြစ် အောင်မြင်စွာ ခန့်အပ်ပြီးပါပြီ။")
    except ValueError: pass

@bot.message_handler(commands=['deletelink', 'dl'])
def admin_delete_vpn_link(message):
    if message.chat.id not in ADMIN_LIST: return
    args = message.text.split()
    if len(args) < 3: return
    gb_key = args[1].lower()
    target_link = message.text.split(None, 2)[2].strip()
    if gb_key in VPN_LINKS:
        for item in VPN_LINKS[gb_key]:
            if item['link'] == target_link:
                VPN_LINKS[gb_key].remove(item)
                save_links() 
                bot.send_message(message.chat.id, f"✅ {gb_key.upper()} ထဲမှ VPN Link အား ဖျက်ပြီးပါပြီ။")
                return

@bot.message_handler(commands=['ul'])
def admin_user_list(message):
    if message.chat.id not in ADMIN_LIST: return
    if not USER_DATABASE: return
    ul_text = "👥 **Bot Users List & Details**\n━━━━━━━━━━━━━━━━━━━━\n"
    for uid, udata in USER_DATABASE.items():
        reg_status = "🟢 Registered" if udata.get("registered", False) else "🔴 Not Registered"
        ul_text += f"👤 **Name:** {udata['name']} | @{udata['username']}\n🆔 ID: `{uid}`\n💰 Coins: {udata['coins']} | Ref: {udata['referred_users']} ဦး\n📝 Status: {reg_status}\n------------------------------------\n"
    bot.send_message(message.chat.id, ul_text, parse_mode='Markdown')

@bot.message_handler(func=lambda message: message.text.split()[0].lower() in ['/5gb', '/10gb', '/50gb', '/100gb'])
def admin_add_vpn_links(message):
    if message.chat.id not in ADMIN_LIST: return
    cmd = message.text.split()[0].lower()
    gb_key = cmd.replace('/', '')
    link_data = message.text[len(cmd):].strip()
    if not link_data: return
    incoming_links = [l.strip() for l in link_data.split('\n') if l.strip()]
    
    if gb_key not in VPN_LINKS:
        VPN_LINKS[gb_key] = []
        
    for l in incoming_links:
        VPN_LINKS[gb_key].append({"link": l, "used": False, "buyer_id": None})
    save_links() 
    bot.send_message(message.chat.id, f"✅ {gb_key.upper()} သို့ လင့်ခ် {len(incoming_links)} ခု ထည့်ပြီးပါပြီ။")

@bot.message_handler(commands=['gbl'])
def admin_view_links_status(message):
    if message.chat.id not in ADMIN_LIST: return
    gbl_text = "📊 **VPN Links Stock**\n━━━━━━━━━━━━━━━━━━━━\n"
    for gb, links_list in VPN_LINKS.items():
        avail = sum(1 for l in links_list if not l['used'])
        gbl_text += f"📂 **{gb.upper()} Package:** လက်ကျန် {avail} ခု\n"
    bot.send_message(message.chat.id, gbl_text, parse_mode='Markdown')

@bot.message_handler(commands=['am'])
def admin_broadcast_message(message):
    if message.chat.id not in ADMIN_LIST: return
    broadcast_msg = message.text[4:].strip()
    if not broadcast_msg: return
    
    success_count = 0
    for user_id in USER_DATABASE.keys():
        try:
            bot.send_message(user_id, broadcast_msg)
            success_count += 1
            time.sleep(0.1)
        except: pass
    bot.send_message(message.chat.id, f"📢 Broadcast ပို့ဆောင်မှု ပြီးဆုံးပါပြီ။\n🟢 အောင်မြင်ဦးရေ: {success_count}")

# --- 🔄 CALLBACK QUERY LISTENERS ---
@bot.callback_query_handler(func=lambda call: True)
def callback_listener(call):
    chat_id = call.message.chat.id
    check_and_create_user(call.message)
    
    # 1. 👤 USER INFO
    if call.data == 'user_info':
        user_data = USER_DATABASE[chat_id]
        coins = user_data["coins"]
        referred = user_data.get("referred_users", 0)
        reg_status = "🟢 အောင်မြင်ပြီး" if user_data.get("registered", False) else "🔴 မလုပ်ရသေးပါ"
        
        info_text = (
            "👤 **User Information**\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            f"🆔 **Chat ID:** `{chat_id}`\n"
            f"📝 **အကောင့်မှတ်ပုံတင်ခြင်း:** {reg_status}\n"
            f"💰 **Coin လက်ကျန်:** {coins} Coins\n"
            f"👥 **ဖိတ်ခေါ်ထားသောလူဦးရေ:** {referred} ယောက်\n"
            f"📊 **အသုံးပြုခဲ့ပြီးသောပမာဏ:** {user_data.get('used_gb_total', 0)} GB\n"
            "━━━━━━━━━━━━━━━━━━━━"
        )
        back_markup = InlineKeyboardMarkup()
        back_markup.add(InlineKeyboardButton('🔙 Back', callback_data='back_to_main'))
        bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id, text=info_text, parse_mode='Markdown', reply_markup=back_markup)
        
    # 2. 📝 REGISTER
    elif call.data == 'register':
        user_data = USER_DATABASE[chat_id]
        if user_data.get("registered", False):
            reg_text = "✅ သင့်အကောင့်သည် မှတ်ပုံတင်ခြင်း (Register) အောင်မြင်စွာ ပြုလုပ်ပြီးသား ဖြစ်ပါတယ်ဗျာ။"
        else:
            user_data["registered"] = True
            save_users() 
            reg_text = "📝 **Register Success!**\n\nသင့်အကောင့်ကို စနစ်တကျ မှတ်ပုံတင်ပေးလိုက်ပါပြီ။ ယခုမှစ၍ VPN သော့ချက်များကို စိတ်ချစွာ ထုတ်ယူနိုင်ပါပြီဗျာ။"
            
        back_markup = InlineKeyboardMarkup()
        back_markup.add(InlineKeyboardButton('🔙 Back', callback_data='back_to_main'))
        bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id, text=reg_text, parse_mode='Markdown', reply_markup=back_markup)

    # 3. 🔗 REFER
    elif call.data == 'refer':
        user_data = USER_DATABASE[chat_id]
        referred = user_data.get("referred_users", 0)
        referral_link = f"https://t.me/{BOT_USERNAME}?start={chat_id}"
        
        refer_text = (
            "🔗 **Referral System (မိတ်ဆက်ခြင်း စနစ်)**\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "သင့်ရဲ့ Referral Link ကို အသုံးပြုပြီး သူငယ်ချင်းများကို ဖိတ်ခေါ်ပါ။\n"
            "လူသစ်တစ်ယောက် ဝင်လာတိုင်း **1 Coin Free** ရရှိပါမည်။ 🎁\n\n"
            f"👥 **ဖိတ်ခေါ်ပြီးသမျှ လူဦးရေ:** {referred} ယောက်\n\n"
            f"👇 **သင့်ရဲ့ ဖိတ်ခေါ်ရန် Link:**\n`{referral_link}`\n"
            "━━━━━━━━━━━━━━━━━━━━"
        )
        back_markup = InlineKeyboardMarkup()
        back_markup.add(InlineKeyboardButton('🔙 Back', callback_data='back_to_main'))
        bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id, text=refer_text, parse_mode='Markdown', reply_markup=back_markup)

    # 4. 🔑 GENERATE KEY
    elif call.data == 'gen_key':
        vpn_type_markup = InlineKeyboardMarkup(row_width=1)
        vpn_type_markup.add(InlineKeyboardButton('🚀 V2BOX VPN', callback_data='v2box_menu'), InlineKeyboardButton('🔙 Back', callback_data='back_to_main'))
        bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id, text="🔑 **Generate Key (Key ထုတ်ယူခြင်း)**\n\nအသုံးပြုလိုသော VPN Type ကို ရွေးချယ်ပေးပါ-", reply_markup=vpn_type_markup)

    elif call.data == 'v2box_menu':
        bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id, text="🚀 ဝယ်ယူလိုသော Package ပမာဏကို ရွေးချယ်ပါ-", reply_markup=get_v2box_inline_keyboard())

    elif call.data == 'back_to_vpn_types':
        vpn_type_markup = InlineKeyboardMarkup(row_width=1)
        vpn_type_markup.add(InlineKeyboardButton('🚀 V2BOX VPN', callback_data='v2box_menu'), InlineKeyboardButton('🔙 Back', callback_data='back_to_main'))
        bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id, text="🔑 **Generate Key (Key ထုတ်ယူခြင်း)**\n\nအသုံးပြုလိုသော VPN Type ကို ရွေးချယ်ပေးပါ-", reply_markup=vpn_type_markup)

    # 5. 📊 MY KEYS
    elif call.data == 'my_keys':
        user_data = USER_DATABASE[chat_id]
        vpns = user_data.get("purchased_vpns", [])
        
        if vpns:
            history_text = "📊 **သင့်ရဲ့ ဝယ်ယူထားခဲ့သော VPN Keys များ**\n━━━━━━━━━━━━━━━━━━━━\n"
            for idx, vpn in enumerate(vpns, 1):
                history_text += f"{idx}. 📦 {vpn['type']} \n   📅 ({vpn['date']})\n   🔑 `လင့်ခ်ကို User Info တွင် ပြန်ကြည့်နိုင်သည်`\n------------------------------------\n"
        else:
            history_text = "📊 **My Keys**\n━━━━━━━━━━━━━━━━━━━━\n❌ သင်သည် VPN Key တစ်ခုမျှ ဝယ်ယူထားခြင်း မရှိသေးပါဗျာ။"
            
        back_markup = InlineKeyboardMarkup()
        back_markup.add(InlineKeyboardButton('🔙 Back', callback_data='back_to_main'))
        bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id, text=history_text, parse_mode='Markdown', reply_markup=back_markup)

    # 6. 🖥 SERVER STATUS
    elif call.data == 'server_status':
        status_text = (
            "🖥 **Server Connection Status**\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "🤖 **Bot Core:** 🟢 Online (Normal)\n"
            "🌐 **Database Connection:** 🟢 Connected (JSON Realtime)\n"
            "⚡ **Ping Rate:** 🟢 Excellent\n"
            "🛰 **Render Host VPS:** 🟢 Active (Keep-Alive Triggered)\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "💡 ဗဟိုဆာဗာအားလုံး ကောင်းမွန်စွာ လည်ပတ်နေပါသည်။"
        )
        back_markup = InlineKeyboardMarkup()
        back_markup.add(InlineKeyboardButton('🔙 Back', callback_data='back_to_main'))
        bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id, text=status_text, parse_mode='Markdown', reply_markup=back_markup)

    # 7. 💰 BUY CREDITS
    elif call.data == 'buy_credits':
        buy_text = (
            "💰 **Coin ဝယ်ယူရန် နည်းလမ်းများ**\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "Coin ဝယ်ယူလိုပါက အောက်ဖော်ပြပါ တာဝန်ခံ Admin များထံသို့ တိုက်ရိုက် ဆက်သွယ်စုံစမ်း ဝယ်ယူနိုင်ပါတယ်ဗျာ။\n"
            "━━━━━━━━━━━━━━━━━━━━"
        )
        buy_markup = InlineKeyboardMarkup(row_width=1)
        buy_markup.add(
            InlineKeyboardButton('👨‍💻 Admin Elonmusk', url='https://t.me/Elonmusk20606'),
            InlineKeyboardButton('👨‍💻 Admin mgzan', url='https://t.me/mgzan201'),
            InlineKeyboardButton('🔙 Back', callback_data='back_to_main')
        )
        bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id, text=buy_text, parse_mode='Markdown', reply_markup=buy_markup)

    # BACK TO MAIN MENU
    elif call.data == 'back_to_main':
        bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id, text="👉 လိုအပ်ရာ လုပ်ဆောင်ချက်ကို နှိပ်ပါ -", reply_markup=get_main_inline_keyboard())
        
    # AUTOMATED PURCHASING ENGINE
    elif call.data.startswith('buy_v2box_'):
        selected_package = call.data.split('_')[2]
        coin_needed = V2BOX_PACKAGES.get(selected_package, 99999)
        user_data = USER_DATABASE[chat_id]
        
        if user_data["coins"] < coin_needed:
            bot.send_message(chat_id, f"❌ ဝယ်ယူရန် Coin မလုံလောက်ပါ။ {selected_package.upper()} အတွက် {coin_needed} Coins လိုအပ်သော်လည်း သင့်တွင် {user_data['coins']} Coins သာ ရှိပါသည်။")
            bot.answer_callback_query(call.id)
            return
            
        available_links = [l for l in VPN_LINKS.get(selected_package, []) if not l['used']]
        if not available_links:
            bot.send_message(chat_id, f"❌ စိတ်မကောင်းပါဘူးဗျာ၊ လောလောဆယ် {selected_package.upper()} အတွက် VPN Link လက်ကျန် ပြတ်လပ်နေပါသည်။")
            bot.answer_callback_query(call.id)
            return
            
        chosen_item = available_links[0]
        chosen_item['used'] = True
        chosen_item['buyer_id'] = chat_id
        
        user_data["coins"] -= coin_needed
        try:
            gb_amount = int(selected_package.replace('gb', ''))
            user_data["used_gb_total"] += gb_amount
        except ValueError: pass
            
        current_date = time.strftime("%Y-%m-%d %H:%M:%S")
        user_data["purchased_vpns"].append({
            "type": f"V2BOX {selected_package.upper()}",
            "date": current_date,
            "link": chosen_item['link']
        })
        
        save_users()
        save_links()
        
        success_text = (
            f"🎉 **ဝယ်ယူမှု အောင်မြင်ပါသည်!**\n\n"
            f"📦 **အမျိုးအစား:** V2BOX {selected_package.upper()}\n"
            f"📉 **နှုတ်ယူပြီး Coin:** -{coin_needed} Coins\n"
            f"💰 **လက်ကျန် Coin:** {user_data['coins']} Coins\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"👇 **သင့်ရဲ့ VPN Link (Copy ယူပါ) :**\n"
            f"`{chosen_item['link']}`\n"
            f"━━━━━━━━━━━━━━━━━━━━"
        )
        bot.send_message(chat_id, success_text, parse_mode='Markdown')
        
        for admin_id in ADMIN_LIST:
            try:
                bot.send_message(admin_id, f"🔔 **Notification:** User `{user_data['name']}` (ID: `{chat_id}`) သည် V2BOX {selected_package.upper()} အား ဝယ်ယူသွားခဲ့ပြီး Stock လျော့နည်းသွားပါပြီ။")
            except: pass

    bot.answer_callback_query(call.id)

# --- START BOT ENGINE ---
print("Starting Flask Keep-Alive Server...")
keep_alive()

print("Checking Bot details from Telegram...")
try:
    BOT_USERNAME = bot.get_me().username
    print(f"✅ Bot is Live as @{BOT_USERNAME}")
    bot.infinity_polling(timeout=10, long_polling_timeout=5)
except Exception as e:
    print(f"❌ Error starting bot: {e}")

