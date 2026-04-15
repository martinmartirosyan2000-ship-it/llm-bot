# bot.py — Telegram բոտի ամբողջ логика

import telebot                          # pip install pyTelegramBotAPI
from telebot import types               # Կոճակների համար
from config import BOT_TOKEN, CHANNEL_ID
from llm_data import LLM_DATA


# ============================================================
# Բոտի ստեղծումը
# ============================================================
bot = telebot.TeleBot(BOT_TOKEN)


# ============================================================
# Օժանդակ ֆունկցիա — ստուգել արդյո՞ք user-ը subscribe է
# ============================================================
def is_subscribed(user_id: int) -> bool:
    """
    Ստուգում է՝ user-ը member է channel-ում, թե ոչ։
    get_chat_member վերադարձնում է status:
    'member', 'administrator', 'creator' — ok
    'left', 'kicked' — չի բաժանորդագրվել
    """
    try:
        member = bot.get_chat_member(CHANNEL_ID, user_id)
        return member.status in ("member", "administrator", "creator")
    except Exception:
        # Եթե bot-ը channel-ի admin չէ, կբռնի exception
        return False


# ============================================================
# /start հրաման
# ============================================================
@bot.message_handler(commands=["start"])
def start(message):
    user_id = message.from_user.id

    if not is_subscribed(user_id):
        # ----- Դեռ չի բաժանորդագրվել -----
        # Ստեղծում ենք inline կոճակներ
        markup = types.InlineKeyboardMarkup()

        # 1️⃣ Ալիքին անցնելու կոճակ
        btn_channel = types.InlineKeyboardButton(
            text="📢 Subscribe to Channel",
            url=f"https://t.me/{CHANNEL_ID.lstrip('@')}"
        )
        # 2️⃣ Ստուգելու կոճակ
        btn_check = types.InlineKeyboardButton(
            text="✅ I've Subscribed — Check",
            callback_data="check_subscription"   # callback-ի id
        )

        markup.add(btn_channel)
        markup.add(btn_check)

        bot.send_message(
            message.chat.id,
            "👋 Welcome!\n\n"
            "Before using this bot, please subscribe to our channel 👇\n"
            "After subscribing, press the ✅ button below.",
            reply_markup=markup
        )
    else:
        # ----- Արդեն բաժանորդ է -----
        show_categories(message.chat.id)


# ============================================================
# Callback handler — կոճակների սեղմումների handling
# ============================================================
@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    user_id = call.from_user.id
    chat_id = call.message.chat.id
    data = call.data   # callback_data-ն

    # ---- Subscription ստուգում ----
    if data == "check_subscription":
        if is_subscribed(user_id):
            # Ջնջում ենք հին message-ը, բերում category menu
            bot.delete_message(chat_id, call.message.message_id)
            show_categories(chat_id)
        else:
            bot.answer_callback_query(
                call.id,
                "❌ You haven't subscribed yet! Please subscribe first.",
                show_alert=True
            )

    # ---- Ոլորտ ընտրելու callback ----
    elif data.startswith("cat_"):
        category_key = data[4:]   # "cat_code" → "code"
        show_tools(chat_id, category_key, call.message.message_id)

    # ---- Հետ կոճակ ----
    elif data == "back_to_categories":
        bot.delete_message(chat_id, call.message.message_id)
        show_categories(chat_id)


# ============================================================
# Ֆունկցիա — ցույց տալ ոլորտների ցուցակը
# ============================================================
def show_categories(chat_id: int):
    markup = types.InlineKeyboardMarkup(row_width=2)  # 2 կոճակ մի շարքում

    buttons = []
    for key, value in LLM_DATA.items():
        btn = types.InlineKeyboardButton(
            text=value["name"],
            callback_data=f"cat_{key}"   # օրինակ՝ "cat_code"
        )
        buttons.append(btn)

    markup.add(*buttons)   # * — unpack անում ենք list-ը

    bot.send_message(
        chat_id,
        "🤖 *Choose a category to see the best AI tools:*",
        parse_mode="Markdown",
        reply_markup=markup
    )


# ============================================================
# Ֆունկցիա — ցույց տալ ոլորտի tools-ը
# ============================================================
def show_tools(chat_id: int, category_key: str, message_id: int):
    category = LLM_DATA.get(category_key)

    if not category:
        bot.send_message(chat_id, "❌ Category not found.")
        return

    # Կառուցում ենք text-ը
    text = f"*{category['name']}*\n\n"
    text += "Here are the best AI tools right now:\n\n"

    for i, tool in enumerate(category["tools"], start=1):
        text += f"{i}. *{tool['name']}*\n"
        text += f"   📌 {tool['desc']}\n"
        text += f"   🔗 [Open →]({tool['url']})\n\n"

    # Inline կոճակ — url-ներ + հետ կոճակ
    markup = types.InlineKeyboardMarkup()

    for tool in category["tools"]:
        btn = types.InlineKeyboardButton(
            text=f"🔗 {tool['name']}",
            url=tool["url"]
        )
        markup.add(btn)

    # Հետ կոճակ
    back_btn = types.InlineKeyboardButton(
        text="⬅️ Back to Categories",
        callback_data="back_to_categories"
    )
    markup.add(back_btn)

    # Ջնջում ենք հին message-ը, ուղարկում նորը
    bot.delete_message(chat_id, message_id)
    bot.send_message(
        chat_id,
        text,
        parse_mode="Markdown",
        reply_markup=markup,
        disable_web_page_preview=True
    )


# ============================================================
# Բոտի գործարկումը
# ============================================================
if __name__ == "__main__":
    print("🤖 Bot is running...")
    bot.infinity_polling()   # Անընդհատ «լսում» է հաղորդագրությունները