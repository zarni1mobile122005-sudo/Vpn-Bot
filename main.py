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

# --- 📁 DATABASE HELPER FUNCTIONS (JSON စနစ်) ---
def load_config():
    if not os.path.exists('config.json'):
        default_config = {
            "TOKEN": "8724005419:AAH2HPdjlJ2ZcdzkLdMpcJWEaDuQhWg4ls4",
            "ADMIN_LIST": [7592705124],
            "CHANNEL_ID": "@starlinkfreezone",  # စစ်ဆေးမည့် Channel ၏ Username (သို့) ID
            "CHANNEL_URL": "https://t.me/starlinkfreezone" # Channel Link
        }
        with open('config.json', 'w') as f:
            json.dump(default_config, f, indent=4)
        return default_config
    with open('config.json', 'r') as f:
        return json.load(f)

def save_config():
    with open('config.json', 'w') as f:
        json.dump({"TOKEN": TOKEN, "ADMIN_LIST": ADMIN_LIST, "CHANNEL_ID": CHANNEL_ID, "CHANNEL_URL": CHANNEL_URL}, f, indent=4)

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
CHANNEL_ID = config.get("CHANNEL_ID", "@starlinkfreezone")
CHANNEL_URL = config.get("CHANNEL_URL", "https://t.me/starlinkfreezone")

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

# --- 🔒 FORCE JOIN CHECK FUNCTION ---
def is_user_joined(user_id):
    """ အသုံးပြုသူက Channel ထဲမှာ ရှိမရှိ စစ်ဆေးပေးမည့် Function """
    if user_id in ADMIN_LIST: 
        return True # Admin ဖြစ်ပါက စစ်ဆေးရန်မလိုဘဲ အလိုအလျောက် သုံးခွင့်ပေးမည်
    try:
        member = bot.get_chat_member(CHANNEL_ID, user_id)
        # အကယ်၍ အခြေအနေက အဖွဲ့ဝင် ဖြစ်နေရင် True ပေးမယ်
        if member.status in ['member', 'administrator', 'creator']:
            return True
        return False
    except Exception as e:
        # Bot က Channel ထဲမှာ Admin မဖြစ်သေးရင် သို့မဟုတ် ID မှားနေရင် လူတိုင်းကို ပေးသုံးလိုက်မည်
        print(f"Force Join Error: {e}")
        return True

def send_force_join_message(chat_id):
    """ Channel မဝင်ရသေးပါက ပြသမည့် စာသားနှင့် ခလုတ် """
    markup = InlineKeyboardMarkup()
    btn_join = InlineKeyboardButton("📢 Join Our Channel", url=CHANNEL_URL)
    btn_check = InlineKeyboardButton("🔄 Joined (စစ်ဆေးမည်)", callback_data="check_join")
    markup.add(btn_join)
    markup.add(btn_check)
    
    text = (
        "🚀 **ဤ Bot ကို အသုံးပြုနိုင်ရန်အတွက် ကျွန်တော်တို့၏ Channel ကို အရင် Join ပေးရပါမည်။**\n\n"
        "အောက်ပါခလုတ်ကို နှိပ်ပြီး Channel ထဲဝင်ရောက်ပေးပါဗျာ။ ပြီးပါက 'Joined (စစ်ဆေးမည်)' ခလုတ်ကို နှိပ်ပါ။"
    )
    bot.send_message(chat_id, text, reply_markup=markup, parse_mode='Markdown')

# --- ⌨️ KEYBOARDS ---
def get_main_inline_keyboard():
    inline_markup = InlineKeyboardMarkup(row_width=2)
    btn_user_info = InlineKeyboardButton('👤 User Info', callback_data='user_info')
    btn_refer = InlineKeyboardButton('🔗 ဖိတ်ခေါ် link ', callback_data='refer')
    btn_gen_key = InlineKeyboardButton('🔑 Vpn Key ဝယ်ရန်', callback_data='gen_key')
    btn_buy_credits = InlineKeyboardButton('💰 Coin ဝယ်ရန်', callback_data='buy_credits')
    btn_channel = InlineKeyboardButton('📢 Channel ↗', url=CHANNEL_URL)
    
    inline_markup.add(btn_user_info, btn_refer)      
    inline_markup.add(btn_gen_key, btn_buy_credits)
    inline_markup.add(btn_channel)   
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

    # Channel Join ထားခြင်း ရှိမရှိ စစ်ဆေးခြင်း
    if not is_user_joined(chat_id):
        send_force_join_message(chat_id)
        return

    reply_markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    btn_how_to_use = KeyboardButton('📖 VPN အသုံးပြုနည်း')
    reply_markup.add(btn_how_to_use)
    
    welcome_text = "✨ Premium VPN Bot မှ ကြိုဆိုပါတယ်ဗျာ။\nအောက်ပါ ခလုတ်များကို အသုံးပြုနိုင်ပါတယ်-"
    bot.send_message(message.chat.id, welcome_text, reply_markup=reply_markup)
    bot.send_message(message.chat.id, "👉 လိုအပ်ရာ လုပ်ဆောင်ချက်ကို နှိပ်ပါ -", reply_markup=get_main_inline_keyboard())

@bot.message_handler(func=lambda message: message.text == '📖 VPN အသုံးပြုနည်း')
def how_to_use_handler(message):
    if not is_user_joined(message.chat.id):
        send_force_join_message(message.chat.id)
        return
    link_markup = InlineKeyboardMarkup()
    btn_link = InlineKeyboardButton('🔗 ဒီနေရာကို နှိပ်ပြီး အသုံးပြုနည်းကြည့်ရန်', url='https://t.me/starlinkfreezone/7')
    link_markup.add(btn_link)
    bot.send_message(message.chat.id, "💡 VPN အသုံးပြုနည်းကို လေ့လာရန် အောက်ပါ ခလုတ် သို့မဟုတ် Link ကို နှိပ်ပါဗျာ။\n\n👉 https://t.me/starlinkfreezone/7", reply_markup=link_markup)

# --- 👑 ADMIN COMMANDS SECTION ---
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
        "🔗 `/5gb <link>` , `/10gb <link>` စသဖြင့် VPN Link အသစ်ထည့်ရန်။\n"
        "🔥 `/deletelink <gb> <link>` - Stock ထဲမှ VPN Link အား ရှာဖွေဖျက်ထုတ်ရန်။\n"
        "➕ `/addadmin <chat_id>` - Admin အသစ် ထပ်တိုးထည့်သွင်းရန်။\n"
        "📊 `/gbl` - လက်ရှိ VPN Links လက်ကျန်စာရင်း ကြည့်ရန်။\n"
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
        if amount <= 0:
            bot.send_message(message.chat.id, "❌ တိုးပေးမည့် Coin ပမာဏသည် 0 ထက် ကြီးရပါမည်။")
            return
        if target_id not in USER_DATABASE: check_and_create_user(target_id)
        USER_DATABASE[target_id]["coins"] += amount
        save_users() 
        current_coins = USER_DATABASE[target_id]["coins"]
        bot.send_message(message.chat.id, f"✅ Chat ID: `{target_id}` ထံသို့ **+{amount} Coins** အောင်မြင်စွာ ဖြည့်သွင်းပေးပြီးပါပြီ။\n📊 လက်ရှိ စုစုပေါင်း Coin: {current_coins} Coins", parse_mode='Markdown')
        try:
            bot.send_message(target_id, f"🎁 **Coin ရရှိမှုသတိပေးချက်**\n\nAdmin မှ သင့်အကောင့်ထဲသို့ **+{amount} Coins** ထည့်သွင်းပေးလိုက်ပါပြီ။\n💰 သင့်ရဲ့ လက်ရှိ Coin လက်ကျန်: **{current_coins} Coins** ဖြစ်သွားပါပြီဗျာ။", parse_mode='Markdown')
        except: pass
    except ValueError:
        bot.send_message(message.chat.id, "❌ Chat ID နှင့် Coin ပမာဏသည် ကိန်းဂဏန်း (Number) သာ ဖြစ်ရပါမည်။")

@bot.message_handler(commands=['coindelete', 'cd'])
def admin_coin_delete(message):
    if message.chat.id not in ADMIN_LIST: return
    args = message.text.split()
    if len(args) < 3:
        bot.send_message(message.chat.id, "❌ ပုံစံမမှန်ပါ။ စာရိုက်နည်း - `/coindelete <chat_id> <amount>`", parse_mode='Markdown')
        return
    try:
        target_id = int(args[1])
        amount = int(args[2])
        if amount <= 0:
            bot.send_message(message.chat.id, "❌ နှုတ်ယူမည့် Coin ပမာဏသည် 0 ထက် ကြီးရပါမည်။")
            return
        if target_id not in USER_DATABASE:
            bot.send_message(message.chat.id, "❌ ၎င်း Chat ID အား Bot ဒေတာဘေ့စ်တွင် ရှာမတွေ့ပါ။")
            return
        if USER_DATABASE[target_id]["coins"] < amount:
            USER_DATABASE[target_id]["coins"] = 0
        else:
            USER_DATABASE[target_id]["coins"] -= amount
        save_users() 
        current_coins = USER_DATABASE[target_id]["coins"]
        bot.send_message(message.chat.id, f"✅ Chat ID: `{target_id}` ထံမှ **-{amount} Coins** နှုတ်ယူပြီးပါပြီ။\n📊 လက်ရှိ ကျန်ရှိ Coin: {current_coins} Coins", parse_mode='Markdown')
        try:
            bot.send_message(target_id, f"📉 **အကောင့်ပြင်ဆင်မှု သတိပေးချက်**\n\nAdmin မှ သင့်အကောင့်ထဲမှ **-{amount} Coins** လျှော့ချ/နှုတ်ယူ လိုက်ပါပြီ။\n💰 သင့်ရဲ့ လက်ကျန် Coin: **{current_coins} Coins** ဖြစ်ပါသည်။", parse_mode='Markdown')
        except: pass
    except ValueError:
        bot.send_message(message.chat.id, "❌ Chat ID နှင့် Coin ပမာဏသည် ကိန်းဂဏန်း (Number) သာ ဖြစ်ရပါမည်။")

@bot.message_handler(commands=['addadmin', 'aa'])
def admin_add_new_admin(message):
    if message.chat.id not in ADMIN_LIST: return
    args = message.text.split()
    if len(args) < 2:
        bot.send_message(message.chat.id, "❌ ပုံစံမမှန်ပါ။ စာရိုက်နည်း - `/addadmin <chat_id>`", parse_mode='Markdown')
        return
    try:
        new_admin_id = int(args[1])
        if new_admin_id in ADMIN_LIST:
            bot.send_message(message.chat.id, "💡 ထို Chat ID သည် Admin စာရင်းထဲတွင် ရှိပြီးသားဖြစ်ပါသည်။")
        else:
            ADMIN_LIST.append(new_admin_id)
            save_config() 
            bot.send_message(message.chat.id, f"✅ Chat ID: `{new_admin_id}` အား Admin အဖြစ် အောင်မြင်စွာ ခန့်အပ်ပြီးပါပြီ။", parse_mode='Markdown')
            try:
                bot.send_message(new_admin_id, "🎉 သင့်အား ဤ VPN Bot ၏ **Admin** အဖြစ် ခန့်အပ်လိုက်ပြီဖြစ်သဖြင့် ယခုမှစ၍ `/ac` Command အား အသုံးပြုနိုင်ပါပြီဗျာ။")
            except: pass
    except ValueError:
        bot.send_message(message.chat.id, "❌ Chat ID သည် ကိန်းဂဏန်းသက်သက် (Number) သာ ဖြစ်ရပါမည်။")

@bot.message_handler(commands=['deletelink', 'dl'])
def admin_delete_vpn_link(message):
    if message.chat.id not in ADMIN_LIST: return
    args = message.text.split()
    if len(args) < 3:
        bot.send_message(message.chat.id, "❌ ပုံစံမမှန်ပါ။ စာရိုက်နည်း - `/deletelink <gb> <ဖျက်မည့်လင့်ခ်>`", parse_mode='Markdown')
        return
    gb_key = args[1].lower()
    target_link = message.text.split(None, 2)[2].strip()
    if gb_key not in VPN_LINKS:
        bot.send_message(message.chat.id, f"❌ {gb_key.upper()} ဟူသော သိုလှောင်ခန်းစာရင်း မရှိပါ။")
        return
    links_list = VPN_LINKS[gb_key]
    found = False
    for item in links_list:
        if item['link'] == target_link:
            links_list.remove(item)
            found = True
            break
    if found:
        save_links()
        bot.send_message(message.chat.id, f"✅ {gb_key.upper()} Stock စာရင်းထဲမှ သတ်မှတ်ထားသော VPN Link ကို အောင်မြင်စွာ ဖျက်ထုတ်ပြီးပါပြီ။")
    else:
        bot.send_message(message.chat.id, "❌ ပေးထားသော VPN Link သည် Stock စာရင်းထဲတွင် မရှိပါ သို့မဟုတ် စာရိုက်မှားနေပါသည်။")

@bot.message_handler(commands=['ul'])
def admin_user_list(message):
    if message.chat.id not in ADMIN_LIST: return
    if not USER_DATABASE:
        bot.send_message(message.chat.id, "❌ Bot တွင် ယခုထိ User မရှိသေးပါ။")
        return
    ul_text = "👥 **Bot Users List & Details**\n━━━━━━━━━━━━━━━━━━━━\n"
    for uid, udata in USER_DATABASE.items():
        ul_text += (
            f"👤 **Name:** {udata['name']}\n"
            f" Username: @{udata['username']}\n"
            f"🆔 Chat ID: `{uid}`\n"
            f"💰 Coins: {udata['coins']} | 👥 Ref: {udata['referred_users']} ယောက်\n"
            f"📊 သုံးစွဲခဲ့ပြီးသောပမာဏ: {udata['used_gb_total']} GB\n"
            "------------------------------------\n"
        )
    ul_text += "━━━━━━━━━━━━━━━━━━━━"
    bot.send_message(message.chat.id, ul_text, parse_mode='Markdown')

@bot.message_handler(commands=['pu'])
def admin_package_update(message):
    if message.chat.id not in ADMIN_LIST: return
    args = message.text.split()
    if len(args) < 3:
        bot.send_message(message.chat.id, "❌ ပုံစံမမှန်ပါ။ စာရိုက်နည်း - `/pu <gb> <coins>` သို့မဟုတ် `/pu <gb> delete`", parse_mode='Markdown')
        return
    gb_input = args[1].lower()
    action_or_coin = args[2].lower()
    
    if action_or_coin == 'delete':
        if gb_input in V2BOX_PACKAGES:
            del V2BOX_PACKAGES[gb_input]
            if gb_input in VPN_LINKS: del VPN_LINKS[gb_input]
            save_links()
            bot.send_message(message.chat.id, f"✅ V2BOX **{gb_input.upper()}** Package အား အောင်မြင်စွာ ဖြုတ်ချပြီးပါပြီ။", parse_mode='Markdown')
        else:
            bot.send_message(message.chat.id, "❌ ဖျက်ရန် ထို Package စာရင်း ရှာမတွေ့ပါ။")
    else:
        try:
            coin_price = int(action_or_coin)
            is_edit = gb_input in V2BOX_PACKAGES
            V2BOX_PACKAGES[gb_input] = coin_price
            if gb_input not in VPN_LINKS: VPN_LINKS[gb_input] = []
            save_links()
            status_msg = "ပြင်ဆင်ခြင်း" if is_edit else "အသစ်ထည့်သွင်းခြင်း"
            bot.send_message(message.chat.id, f"✅ V2BOX **{gb_input.upper()}** ကို {coin_price} Coins အဖြစ် {status_msg} အောင်မြင်ပါသည်။", parse_mode='Markdown')
        except ValueError:
            bot.send_message(message.chat.id, "❌ Coin ဈေးနှုန်းသည် ကိန်းဂဏန်း (Number) သာ ဖြစ်ရပါမည်။")

@bot.message_handler(func=lambda message: message.text.split()[0].lower() in ['/5gb', '/10gb', '/50gb', '/100gb'])
def admin_add_vpn_links(message):
    if message.chat.id not in ADMIN_LIST: return
    cmd = message.text.split()[0].lower()
    gb_key = cmd.replace('/', '')
    
    if gb_key not in V2BOX_PACKAGES:
        bot.send_message(message.chat.id, f"❌ ၎င်း {gb_key.upper()} Package အား မီနူးထဲတွင် သတ်မှတ်ထားခြင်း မရှိသေးပါ။ ဦးစွာ `/pu` ဖြင့် ထည့်ပေးပါ။")
        return
    link_data = message.text[len(cmd):].strip()
    if not link_data:
        bot.send_message(message.chat.id, f"❌ ပုံစံမမှန်ပါ။ ဥပမာ - `{cmd} vless://...` ဟု ရိုက်ထည့်ပါ။", parse_mode='Markdown')
        return
    incoming_links = [l.strip() for l in link_data.split('\n') if l.strip()]
    for l in incoming_links:
        VPN_LINKS[gb_key].append({"link": l, "used": False, "buyer_id": None})
    save_links()
    bot.send_message(message.chat.id, f"✅ {gb_key.upper()} အတွက် VPN Link စုစုပေါင်း (+{len(incoming_links)} ခု) အား Storage ထဲသို့ ထည့်သွင်းပြီးပါပြီ။")

@bot.message_handler(commands=['gbl'])
def admin_view_links_status(message):
    if message.chat.id not in ADMIN_LIST: return
    gbl_text = "📊 **VPN Links Stock & History**\n━━━━━━━━━━━━━━━━━━━━\n"
    for gb, links_list in VPN_LINKS.items():
        gbl_text += f"📂 **{gb.upper()} Package:**\n"
        if not links_list:
            gbl_text += "  ❌ Link တစ်ခုမှ မရှိသေးပါ။\n\n"
            continue
        for idx, item in enumerate(links_list, 1):
            status = f"🔴 သုံးပြီးသား (User ID: `{item['buyer_id']}`)" if item['used'] else "🟢 အသုံးမပြုရသေး (Available)"
            short_link = item['link'][:30] + "..." if len(item['link']) > 30 else item['link']
            gbl_text += f"  {idx}. `{short_link}`\n     ➔ အခြေအနေ: {status}\n"
        gbl_text += "\n"
    gbl_text += "━━━━━━━━━━━━━━━━━━━━"
    bot.send_message(message.chat.id, gbl_text, parse_mode='Markdown')

@bot.message_handler(commands=['am'])
def admin_broadcast_message(message):
    if message.chat.id not in ADMIN_LIST: return
    broadcast_msg = message.text[4:].strip()
    if not broadcast_msg:
        bot.send_message(message.chat.id, "❌ ပုံစံမမှန်ပါ။ ဥပမာ - `/am ယနေ့ည VPN Server ပြုပြင်ပါမည်။` ဟု ရိုက်ထည့်ပါ။")
        return
    if not USER_DATABASE:
        bot.send_message(message.chat.id, "❌ ပို့ရန် User တစ်ဦးမျှ မရှိသေးပါ။")
        return
    success_count = 0
    fail_count = 0
    bot.send_message(message.chat.id, f"📢 User အားလုံးထံသို့ စာသား ပို့ဆောင်နေပါပြီ...")
    for user_id in USER_DATABASE.keys():
        try:
            bot.send_message(user_id, broadcast_msg)
            success_count += 1
            time.sleep(0.1)
        except:
            fail_count += 1
    bot.send_message(message.chat.id, f"✅ ပို့ဆောင်မှု ပြီးဆုံးပါပြီ။\n\n🟢 အောင်မြင်: {success_count} ဦး\n🔴 ကျရှုံး (Block ထားသူ): {fail_count} ဦး")

# --- 🔄 CALLBACK QUERY LISTENERS ---
@bot.callback_query_handler(func=lambda call: True)
def callback_listener(call):
    chat_id = call.message.chat.id
    check_and_create_user(call.message)

    # 🔄 'Joined' စစ်ဆေးသည့်ခလုတ်အားနှိပ်ပါက စစ်ဆေးပေးခြင်း
    if call.data == "check_join":
        if is_user_joined(chat_id):
            bot.answer_callback_query(call.id, "✅ ကျေးဇူးတင်ပါသည်! Channel ဝင်ရောက်မှု အောင်မြင်ပါသည်။")
            bot.delete_message(chat_id, call.message.message_id)
            
            reply_markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
            btn_how_to_use = KeyboardButton('📖 VPN အသုံးပြုနည်း')
            reply_markup.add(btn_how_to_use)
            
            bot.send_message(chat_id, "✨ Premium VPN Bot မှ ကြိုဆိုပါတယ်ဗျာ။\nအောက်ပါ ခလုတ်များကို အသုံးပြုနိုင်ပါတယ်-", reply_markup=reply_markup)
            bot.send_message(chat_id, "👉 လိုအပ်ရာ လုပ်ဆောင်ချက်ကို နှိပ်ပါ -", reply_markup=get_main_inline_keyboard())
        else:
            bot.answer_callback_query(call.id, "❌ သင် Channel ထဲမဝင်ရသေးပါဗျာ။ အရင် Join ပေးပါ။", show_alert=True)
        return

    # တခြား ခလုတ်များကို မနှိပ်ခင် Channel Join မJoin အရင်စစ်မည်
    if not is_user_joined(chat_id):
        bot.answer_callback_query(call.id, "❌ Bot ကို သုံးနိုင်ရန် Channel ကို အရင် Join ပေးပါ။", show_alert=True)
        send_force_join_message(chat_id)
        return

    bot.answer_callback_query(call.id)
    
    # 1. 👤 USER INFO
    if call.data == 'user_info':
        user_data = USER_DATABASE[chat_id]
        coins = user_data["coins"]
        vpns = user_data["purchased_vpns"]
        referred = user_data.get("referred_users", 0)
        vpn_count = len(vpns)
        
        vpn_history_text = ""
        if vpn_count > 0:
            for idx, vpn in enumerate(vpns, 1):
                vpn_history_text += f"   {idx}. {vpn['type'].upper()} - ({vpn['date']})\n"
        else:
            vpn_history_text = "   ❌ ဝယ်ယူမှု စာရင်းမရှိသေးပါ။\n"
            
        info_text = (
            "👤 **User Information**\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            f"🆔 **Chat ID:** `{chat_id}`\n"
            f"💰 **Coin လက်ကျန်:** {coins} Coins\n"
            f"👥 **ဖိတ်ခေါ်ထားသော လူဦးရေ:** {referred} ယောက်\n"
            f"📦 **ဝယ်ယူပြီးသော VPN အရေအတွက်:** {vpn_count} ခု\n\n"
            f"📋 **ဝယ်ယူခဲ့ဖူးသည့် အမျိုးအစားနှင့် နေ့စွဲများ:**\n{vpn_history_text}"
            "━━━━━━━━━━━━━━━━━━━━"
        )
        back_markup = InlineKeyboardMarkup()
        back_markup.add(InlineKeyboardButton('🔙 Back', callback_data='back_to_main'))
        bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id, text=info_text, parse_mode='Markdown', reply_markup=back_markup)
        
    # 2. 🔗 REFER
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

    # 3. 🔑 GENERATE KEY
    elif call.data == 'gen_key':
        vpn_type_markup = InlineKeyboardMarkup(row_width=1)
        vpn_type_markup.add(InlineKeyboardButton('🚀 V2BOX VPN', callback_data='v2box_menu'), InlineKeyboardButton('🔙 Back', callback_data='back_to_main'))
        bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id, text="🔑 **Generate Key (Key ထုတ်ယူခြင်း)**\n\nအသုံးပြုလိုသော VPN Type ကို ရွေးချယ်ပေးပါ-", parse_mode='Markdown', reply_markup=vpn_type_markup)

    # 4. 🚀 V2BOX MENU
    elif call.data == 'v2box_menu':
        v2box_text = (
            "🚀 **V2BOX VPN Packages**\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "သင်ဝယ်ယူလိုသော GB ပမာဏကို ရွေးချယ်ပေးပါဗျာ။\n"
            "သင့်အကောင့်ထဲတွင် လုံလောက်သော Coin ရှိရန် လိုအပ်ပါသည်။\n"
            "━━━━━━━━━━━━━━━━━━━━"
        )
        bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id, text=v2box_text, parse_mode='Markdown', reply_markup=get_v2box_inline_keyboard())

    # 5. 🔙 BACK TO VPN TYPES
    elif call.data == 'back_to_vpn_types':
        vpn_type_markup = InlineKeyboardMarkup(row_width=1)
        vpn_type_markup.add(InlineKeyboardButton('🚀 V2BOX VPN', callback_data='v2box_menu'), InlineKeyboardButton('🔙 Back', callback_data='back_to_main'))
        bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id, text="🔑 **Generate Key (Key ထုတ်ယူခြင်း)**\n\nအသုံးပြုလိုသော VPN Type ကို ရွေးချယ်ပေးပါ-", parse_mode='Markdown', reply_markup=vpn_type_markup)

    # 6. 💰 BUY CREDITS
    elif call.data == 'buy_credits':
        buy_text = (
            "💰 **Coin ဝယ်ယူရန် နည်းလမ်းများ**\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "Coin ဝယ်ယူလိုပါက အောက်ဖော်ပြပါ တာဝန်ခံ Admin များထံသို့ "
            "တိုက်ရိုက် ဆက်သွယ်စုံစမ်း ဝယ်ယူနိုင်ပါတယ်ဗျာ။\n"
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
            return
            
        available_links = [l for l in VPN_LINKS.get(selected_package, []) if not l['used']]
        if not available_links:
            bot.send_message(chat_id, f"❌ စိတ်မကောင်းပါဘူးဗျာ၊ လောလောဆယ် {selected_package.upper()} အတွက် အသင့်သုံး VPN Link လက်ကျန် ပြတ်လပ်နေပါသည်။ ကျေးဇူးပြု၍ ခေတ္တစောင့်ဆိုင်းပြီးမှ ပြန်ဝယ်ယူပါ။")
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
            "date": current_date
        })
        
        save_users()
        save_links()
        
        success_text = (
            f"🎉 **ဝယ်ယူမှု အောင်မြင်ပါသည်!**\n\n"
            f"📦 **အမျိုးအစား:** V2BOX {selected_package.upper()}\n"
            f"📉 **နှုတ်ယူပြီး Coin:** -{coin_needed} Coins\n"
            f"💰 **လက်ကျန် Coin:** {user_data['coins']} Coins\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"👇 **သင့်ရဲ့ VPN Link (အောက်ပါစာသားကို ကော်ပီကူးယူပါ) :**\n"
            f"`{chosen_item['link']}`\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"💡 ၎င်း Link ကို ကော်ပီယူ၍ V2BOX Application ထဲတွင် ထည့်သွင်းအသုံးပြုနိုင်ပါပြီ။"
        )
        bot.send_message(chat_id, success_text, parse_mode='Markdown')
        
        for admin_id in ADMIN_LIST:
            try:
                bot.send_message(admin_id, f"🔔 **Notification:** User `{user_data['name']}` (ID: `{chat_id}`) သည် V2BOX {selected_package.upper()} အား ဝယ်ယူသွားခဲ့ပြီး Stock မှ လင့်ခ်တစ်ခု လျော့နည်းသွားပါပြီ။")
            except: pass

# --- START BOT ENGINE ---
print("Starting Flask Keep-Alive Server...")
keep_alive()

print("Checking Bot details from Telegram...")
try:
    BOT_USERNAME = bot.get_me().username
    print(f"✅ Bot is Live as @{BOT_USERNAME}")
    print("Bot စတင် အလုပ်လုပ်နေပါပြီ...")
    bot.infinity_polling()
except Exception as e:
    print(f"❌ Error starting bot: {e}")
