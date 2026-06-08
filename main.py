import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
import time
from threading import Thread
from flask import Flask

# Flask Server တည်ဆောက်ခြင်း (Render ပေါ်တွင် ပေါက်နေစေရန်)
app = Flask('')

@app.route('/')
def home():
    return "Bot Is Alive!"

def run():
    # Render သည် Free Plan တွင် Port 10000 သို့မဟုတ် Dynamic Port ကို သုံးသည်
    import os
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.start()

# သင့်ရဲ့ Bot Token
TOKEN = '8724005419:AAH2HPdjlJ2ZcdzkLdMpcJWEaDuQhWg4ls4'
bot = telebot.TeleBot(TOKEN)

# ADMIN LIST
ADMIN_LIST = [7592705124]  

# ဒေတာဘေ့စ်များ
USER_DATABASE = {}
BOT_USERNAME = None

# V2BOX Package ဈေးနှုန်းများ
V2BOX_PACKAGES = {
    "5gb": 10,
    "10gb": 20,
    "50gb": 50,
    "100gb": 90
}

# VPN Link များ သိုလှောင်ခန်း
VPN_LINKS = {
    "5gb": [],   
    "10gb": [],
    "50gb": [],
    "100gb": []
}

# ပင်မ Menu Inline Keyboard
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

# Dynamic Package Keyboard
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
            "coins": 0,
            "purchased_vpns": [], 
            "used_gb_total": 0,    
            "referred_users": 0
        }
    else:
        if not isinstance(message_or_id, int):
            USER_DATABASE[chat_id]["name"] = name
            USER_DATABASE[chat_id]["username"] = username

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
                try:
                    bot.send_message(referrer_id, f"🎉 အဖွဲ့ဝင်သစ်တစ်ဦး သင့် Link မှတစ်ဆင့် ဆက်သွယ်ဝင်ရောက်လာသဖြင့် သင့်ထံ **+1 Coin** ထည့်သွင်းပေးလိုက်ပါပြီ။", parse_mode='Markdown')
                except Exception:
                    pass
        except ValueError:
            pass

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
# 👑 ADMIN COMMANDS SECTION
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
    if len(args) < 3:
        bot.send_message(message.chat.id, "❌ ပုံစံမမှန်ပါ။ စာရိုက်နည်း - `/coinadd <chat_id> <amount>`", parse_mode='Markdown')
        return
    try:
        target_id = int(args[1])
        amount = int(args[2])
        if amount <= 0: return
        if target_id not in USER_DATABASE: check_and_create_user(target_id)
        USER_DATABASE[target_id]["coins"] += amount
        current_coins = USER_DATABASE[target_id]["coins"]
        bot.send_message(message.chat.id, f"✅ Chat ID: `{target_id}` ထံသို့ **+{amount} Coins** ထည့်ပြီးပါပြီ။")
        try:
            bot.send_message(target_id, f"🎁 Admin မှ သင့်ထံသို့ **+{amount} Coins** ထည့်သွင်းပေးလိုက်ပါပြီ။\nလက်ကျန်: **{current_coins} Coins**")
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
        current_coins = USER_DATABASE[target_id]["coins"]
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
    if gb_key in VPN_LINKS:
        for item in VPN_LINKS[gb_key]:
            if item['link'] == target_link:
                VPN_LINKS[gb_key].remove(item)
                bot.send_message(message.chat.id, "✅ VPN Link ကို ဖျက်ပြီးပါပြီ။")
                return

@bot.message_handler(commands=['ul'])
def admin_user_list(message):
    if message.chat.id not in ADMIN_LIST: return
    if not USER_DATABASE: return
    ul_text = "👥 **Bot Users List**\n━━━━━━━━━━━━━━━━━━━━\n"
    for uid, udata in USER_DATABASE.items():
        ul_text += f"👤 **Name:** {udata['name']} | ID: `{uid}` | Coins: {udata['coins']}\n"
    bot.send_message(message.chat.id, ul_text, parse_mode='Markdown')

@bot.message_handler(commands=['pu'])
def admin_package_update(message):
    if message.chat.id not in ADMIN_LIST: return
    args = message.text.split()
    if len(args) < 3: return
    gb_input = args[1].lower()
    action_or_coin = args[2].lower()
    if action_or_coin == 'delete':
        if gb_input in V2BOX_PACKAGES: del V2BOX_PACKAGES[gb_input]
    else:
        try:
            V2BOX_PACKAGES[gb_input] = int(action_or_coin)
            if gb_input not in VPN_LINKS: VPN_LINKS[gb_input] = []
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
    for l in incoming_links:
        VPN_LINKS[gb_key].append({"link": l, "used": False, "buyer_id": None})
    bot.send_message(message.chat.id, f"✅ {gb_key.upper()} သို့ လင့်ခ် {len(incoming_links)} ခု ထည့်ပြီးပါပြီ။")

@bot.message_handler(commands=['gbl'])
def admin_view_links_status(message):
    if message.chat.id not in ADMIN_LIST: return
    gbl_text = "📊 **VPN Links Stock**\n"
    for gb, links_list in VPN_LINKS.items():
        avail = sum(1 for l in links_list if not l['used'])
        gbl_text += f"📂 **{gb.upper()}:** လက်ကျန် {avail} ခု\n"
    bot.send_message(message.chat.id, gbl_text, parse_mode='Markdown')

@bot.message_handler(commands=['am'])
def admin_broadcast_message(message):
    if message.chat.id not in ADMIN_LIST: return
    broadcast_msg = message.text[4:].strip()
    if not broadcast_msg: return
    for user_id in USER_DATABASE.keys():
        try: bot.send_message(user_id, broadcast_msg)
        except: pass
    bot.send_message(message.chat.id, "✅ Broadcast ပို့ဆောင်ပြီးပါပြီ။")

# =====================================================================
# CALLBACK QUERY LISTENERS
# =====================================================================

@bot.callback_query_handler(func=lambda call: True)
def callback_listener(call):
    bot.answer_callback_query(call.id)
    chat_id = call.message.chat.id
    check_and_create_user(call.message)
    
    if call.data == 'user_info':
        user_data = USER_DATABASE[chat_id]
        info_text = f"👤 **User Information**\n🆔 ID: `{chat_id}`\n💰 Coins: {user_data['coins']} Coins"
        back_markup = InlineKeyboardMarkup()
        back_markup.add(InlineKeyboardButton('🔙 Back', callback_data='back_to_main'))
        bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id, text=info_text, parse_mode='Markdown', reply_markup=back_markup)
        
    elif call.data == 'refer':
        referral_link = f"https://t.me/{BOT_USERNAME}?start={chat_id}"
        refer_text = f"🔗 **Referral Link:**\n`{referral_link}`"
        back_markup = InlineKeyboardMarkup()
        back_markup.add(InlineKeyboardButton('🔙 Back', callback_data='back_to_main'))
        bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id, text=refer_text, parse_mode='Markdown', reply_markup=back_markup)

    elif call.data == 'gen_key':
        vpn_type_markup = InlineKeyboardMarkup(row_width=1)
        vpn_type_markup.add(InlineKeyboardButton('🚀 V2BOX VPN', callback_data='v2box_menu'), InlineKeyboardButton('🔙 Back', callback_data='back_to_main'))
        bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id, text="🔑 Select VPN Type:", reply_markup=vpn_type_markup)

    elif call.data == 'v2box_menu':
        bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id, text="🚀 Select GB Package:", reply_markup=get_v2box_inline_keyboard())

    elif call.data == 'back_to_vpn_types':
        vpn_type_markup = InlineKeyboardMarkup(row_width=1)
        vpn_type_markup.add(InlineKeyboardButton('🚀 V2BOX VPN', callback_data='v2box_menu'), InlineKeyboardButton('🔙 Back', callback_data='back_to_main'))
        bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id, text="🔑 Select VPN Type:", reply_markup=vpn_type_markup)

    elif call.data == 'buy_credits':
        buy_markup = InlineKeyboardMarkup()
        buy_markup.add(InlineKeyboardButton('🔙 Back', callback_data='back_to_main'))
        bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id, text="💰 Admin ထံ ဆက်သွယ်၍ ဝယ်ယူပါ။", reply_markup=buy_markup)

    elif call.data == 'back_to_main':
        bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id, text="👉 လိုအပ်ရာ လုပ်ဆောင်ချက်ကို နှိပ်ပါ -", reply_markup=get_main_inline_keyboard())
        
    elif call.data.startswith('buy_v2box_'):
        selected_package = call.data.split('_')[2]
        coin_needed = V2BOX_PACKAGES.get(selected_package, 99999)
        user_data = USER_DATABASE[chat_id]
        
        if user_data["coins"] < coin_needed:
            bot.send_message(chat_id, f"❌ Coin မလုံလောက်ပါ။")
            return
            
        available_links = [l for l in VPN_LINKS.get(selected_package, []) if not l['used']]
        if not available_links:
            bot.send_message(chat_id, f"❌ လက်ကျန်ပြတ်လပ်နေပါသည်။")
            return
            
        chosen_item = available_links[0]
        chosen_item['used'] = True
        chosen_item['buyer_id'] = chat_id
        user_data["coins"] -= coin_needed
        
        bot.send_message(chat_id, f"🎉 ဝယ်ယူမှုအောင်မြင်သည်။\nLink: `{chosen_item['link']}`", parse_mode='Markdown')

# Bot စတင်ခြင်းမပြုမီ Flask ကို အရင်နှိုးထားမည်
print("Starting Web Server for Cron-Job...")
keep_alive()

print("Checking Bot details...")
BOT_USERNAME = bot.get_me().username
print(f"Bot Username: @{BOT_USERNAME}")
bot.infinity_polling()
