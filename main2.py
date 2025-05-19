from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
from typing import Final
import logging

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

TOKEN: Final = '7584856650:AAFu6rcuKBu225xCmpoCVOKUX90alFYOv8Q'
GROUP_CHAT_ID: Final = '-1002634716157'

afitsiantlar = ["Aziz", "Laziz", "Samir", "Bexruz"]
taomlar = [
    "Balaza", "Frikadelki", "Dumg'oza", "Baranina lapatka", "Jiz gavyajiy",
    "bon vagu'riy", "Yazik", "Baranina", "Mangale mangale", "Kuriniy bedro na mangale",
    "Kuskavoy gavyajiy", "Kuskavoy baraniy", "Ko'fta", "Qaburg'a shshalik", "file shashlik","Marvarid", "Rulet", "Napaleion"
]

# Stol turlari va ularning soni
stol_turlari = {
    "Zal": list(range(1, 13)),  # 1-12 gacha
    "Ulitsa": list(range(1, 9)),  # 1-8 gacha
    "Saboy": []  # Stol yo'q
}

user_data = {}

def is_valid_phone(phone: str) -> bool:
    if phone.startswith("+"):
        phone = phone[1:]
    return phone.isdigit() and 9 <= len(phone) <= 15

def is_valid_name(name: str) -> bool:
    return name.isalpha() and 3 <= len(name) <= 20

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    user_data[user_id] = {}
    await update.message.reply_text("Ismingizni kiriting:")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text.strip()
    user_id = update.message.from_user.id

    if user_id not in user_data:
        user_data[user_id] = {}

    if 'ismi' not in user_data[user_id]:
        if is_valid_name(user_text):
            user_data[user_id]['ismi'] = user_text

            # Telefon tugmasini faqat shu yerda ko‘rsatamiz:
            keyboard = [[KeyboardButton("📞 Telefon raqam yuborish", request_contact=True)]]
            await update.message.reply_text(
                "Telefon raqamingizni kiriting yoki tugmani bosing:",
                reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
            )
        else:
            await update.message.reply_text("Iltimos, ismingizni to‘g‘ri kiriting (3-20 harf).")
        return  # shu blokdan keyin boshqa kodga o‘tmaymiz

    # 2) TELEFON RAQAM QO‘LDA KIRITILGAN BO‘LIM
    if 'telefon' not in user_data[user_id] and update.message.text:
        if is_valid_phone(user_text):
            user_data[user_id]['telefon'] = user_text

            # Telefon tugmasini darhol olib tashlaymiz
            await update.message.reply_text(
                "Rahmat, telefon qabul qilindi.",
                reply_markup=ReplyKeyboardRemove()
            )

            # Inline stollar tugmalari bosqichiga o‘tamiz
            await show_stol_turlari(update, context)
        else:
            await update.message.reply_text("Iltimos, faqat raqam kiriting (9-15 ta raqam).")
        return 

    elif 'stol_turi' in user_data[user_id] and 'stol' not in user_data[user_id]:
        if user_text.isdigit():
            selected_type = user_data[user_id]['stol_turi']
            stol_raqami = int(user_text)
            if stol_raqami in stol_turlari[selected_type]:
                user_data[user_id]['stol'] = stol_raqami
                await show_rating_options(update, context)
            else:
                await update.message.reply_text(f"Noto'g'ri stol raqami. {selected_type} uchun quyidagi stollar mavjud: {', '.join(map(str, stol_turlari[selected_type]))}")
        else:
            await update.message.reply_text("Iltimos, faqat raqam kiriting.")

    elif 'rating' in user_data[user_id] and 'izoh' not in user_data[user_id]:
        user_data[user_id]['izoh'] = user_text
        await send_final_review(update, context, user_id)

async def show_stol_turlari(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🏢 Zal ", callback_data="stol_Zal")],
        [InlineKeyboardButton("🌳 Ulitsa", callback_data="stol_Ulitsa")],
        [InlineKeyboardButton("🚗 Saboy ", callback_data="stol_Saboy")]
    ]
    
    if hasattr(update, 'message'):
        await update.message.reply_text(
            "Stol turini tanlang:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            reply_to_message_id=update.message.message_id
        )
    else:
        await update.callback_query.edit_message_text(
            "Stol turini tanlang:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

async def show_stol_raqamlari(update: Update, context: ContextTypes.DEFAULT_TYPE, stol_turi: str):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    
    user_data[user_id]['stol_turi'] = stol_turi
    
    if stol_turi == "Saboy":
        user_data[user_id]['stol'] = 0  # Saboyda stol yo'q
        await show_rating_options(query, context)  # Bu yerda query ni yuboramiz
        return
    
    stollar = stol_turlari[stol_turi]
    keyboard = []
    
    for i in range(0, len(stollar), 2):
        row = []
        if i < len(stollar):
            row.append(InlineKeyboardButton(str(stollar[i]), callback_data=f"stolnum_{stollar[i]}"))
        if i+1 < len(stollar):
            row.append(InlineKeyboardButton(str(stollar[i+1]), callback_data=f"stolnum_{stollar[i+1]}"))
        keyboard.append(row)
    
    keyboard.append([InlineKeyboardButton("🔙 Orqaga", callback_data="back_to_stol_types")])
    
    await query.edit_message_text(
        f"{stol_turi} stolini tanlang:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def show_rating_options(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if hasattr(update, 'message'):
        user_id = update.message.from_user.id
        chat_id = update.message.chat_id
    else:
        query = update.callback_query
        await query.answer()
        user_id = query.from_user.id
        chat_id = query.message.chat_id if query.message else None

    # Clear previous messages
    if 'message_ids' in context.user_data:
        for msg_id in context.user_data['message_ids']:
            try:
                await context.bot.delete_message(chat_id=chat_id, message_id=msg_id)
            except Exception as e:
                logger.error(f"Failed to delete message: {e}")
        context.user_data['message_ids'] = []

    if user_id in user_data and 'rating_type' in user_data[user_id]:
        if user_data[user_id]['rating_type'] == 'taom':
            keyboard = [
                [InlineKeyboardButton("🍽 Taomlarga baho berish (tanlangan)", callback_data="rate_dishes", disabled=True)],
                [InlineKeyboardButton("👨‍🍳 Afitsiantlarga baho berish", callback_data="rate_waiters")]
            ]
            message = await context.bot.send_message(
                chat_id=chat_id,
                text="Siz allaqachon taomlarga baho berishni tanlagansiz. Afitsiantlarga ham baho bermoqchimisiz?",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        else:
            keyboard = [
                [InlineKeyboardButton("🍽 Taomlarga baho berish", callback_data="rate_dishes")],
                [InlineKeyboardButton("👨‍🍳 Afitsiantlarga baho berish (tanlangan)", callback_data="rate_waiters", disabled=True)]
            ]
            message = await context.bot.send_message(
                chat_id=chat_id,
                text="Siz allaqachon afitsiantlarga baho berishni tanlagansiz. Taomlarga ham baho bermoqchimisiz?",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
    else:
        keyboard = [
            [InlineKeyboardButton("🍽 Taomlarga baho berish", callback_data="rate_dishes")],
            [InlineKeyboardButton("👨‍🍳 Afitsiantlarga baho berish", callback_data="rate_waiters")]
        ]
        message = await context.bot.send_message(
            chat_id=chat_id,
            text="Nimaga baho bermoqchisiz?",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    # Store the new message ID
    if 'message_ids' not in context.user_data:
        context.user_data['message_ids'] = []
    context.user_data['message_ids'].append(message.message_id)

async def ask_for_taom(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if hasattr(update, 'message'):
        chat_id = update.message.chat_id
    else:
        chat_id = update.message.chat_id if hasattr(update, 'message') else None

    # Clear previous messages
    if 'message_ids' in context.user_data:
        for msg_id in context.user_data['message_ids']:
            try:
                await context.bot.delete_message(chat_id=chat_id, message_id=msg_id)
            except Exception as e:
                logger.error(f"Failed to delete message: {e}")
        context.user_data['message_ids'] = []

    keyboard = []
    for i in range(0, len(taomlar), 2):
        row = []
        if i < len(taomlar):
            row.append(InlineKeyboardButton(taomlar[i], callback_data=f"taom_{i}"))
        if i+1 < len(taomlar):
            row.append(InlineKeyboardButton(taomlar[i+1], callback_data=f"taom_{i+1}"))
        if row:
            keyboard.append(row)
    
    keyboard.append([InlineKeyboardButton("🔙 Orqaga", callback_data="back_to_rating_options")])
    
    message = await context.bot.send_message(
        chat_id=chat_id,
        text="Quyidagi taomlardan birini tanlang:",
        reply_markup=InlineKeyboardMarkup(keyboard))
    
    # Store the new message ID
    if 'message_ids' not in context.user_data:
        context.user_data['message_ids'] = []
    context.user_data['message_ids'].append(message.message_id)

async def ask_for_afitsiant(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if hasattr(update, 'message'):
        chat_id = update.message.chat_id
    else:
        chat_id = update.message.chat_id if hasattr(update, 'message') else None

    # Clear previous messages
    if 'message_ids' in context.user_data:
        for msg_id in context.user_data['message_ids']:
            try:
                await context.bot.delete_message(chat_id=chat_id, message_id=msg_id)
            except Exception as e:
                logger.error(f"Failed to delete message: {e}")
        context.user_data['message_ids'] = []

    keyboard = [[InlineKeyboardButton(name, callback_data=f"af_{i}")] 
            for i, name in enumerate(afitsiantlar)]
    
    keyboard.append([InlineKeyboardButton("🔙 Orqaga", callback_data="back_to_rating_options")])
    
    message = await context.bot.send_message(
        chat_id=chat_id,
        text="Quyidagi afitsiantlardan birini tanlang:",
        reply_markup=InlineKeyboardMarkup(keyboard))
    
    # Store the new message ID
    if 'message_ids' not in context.user_data:
        context.user_data['message_ids'] = []
    context.user_data['message_ids'].append(message.message_id)

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if user_id not in user_data:
        user_data[user_id] = {}

    if query.data.startswith("stol_"):
        stol_turi = query.data.split("_")[1]
        await show_stol_raqamlari(update, context, stol_turi)
    
    elif query.data.startswith("stolnum_"):
        stol_raqami = int(query.data.split("_")[1])
        user_data[user_id]['stol'] = stol_raqami

        # ← Shu yerga qo‘shing:
        await query.edit_message_reply_markup(reply_markup=None)

        # Keyin baholash oynasini ko‘rsatamiz:
        await show_rating_options(query, context)
    
    elif query.data == "back_to_stol_types":
        await show_stol_turlari(query, context)
    
    elif query.data == "back_to_rating_options":
        try:
            # Delete current message
            await context.bot.delete_message(chat_id=query.message.chat_id, message_id=query.message.message_id)
            
            # Clear any stored message IDs
            if 'message_ids' in context.user_data:
                context.user_data['message_ids'] = []
            
            # Reset rating type
            if 'rating_type' in user_data[user_id]:
                del user_data[user_id]['rating_type']
            
            # Show rating options
            await show_rating_options(query, context)
        except Exception as e:
            logger.error(f"Error handling back button: {e}")
            await query.message.reply_text("Xatolik yuz berdi. Iltimos, /start buyrug'i bilan qaytadan boshlang.")
        return
        
    elif query.data == "rate_dishes":
        user_data[user_id]['rating_type'] = 'taom'
        await ask_for_taom(query, context)
        
    elif query.data == "rate_waiters":
        user_data[user_id]['rating_type'] = 'afitsiant'
        await ask_for_afitsiant(query, context)

    elif query.data.startswith("af_"):
        afitsiant_index = int(query.data.split("_")[1])
        afitsiant_name = afitsiantlar[afitsiant_index]
        user_data[user_id]['afitsiant'] = afitsiant_name
        await show_rating_scale(query, context, f"Siz {afitsiant_name}ni tanladingiz. Iltimos, baho bering:")

    elif query.data.startswith("taom_"):
        taom_index = int(query.data.split("_")[1])
        taom_name = taomlar[taom_index]
        user_data[user_id]['taom'] = taom_name
        await show_rating_scale(query, context, f"Siz {taom_name}ni tanladingiz. Iltimos, baho bering:")

    elif query.data.startswith("rate_"):
        rating = int(query.data.split("_")[1])
        user_data[user_id]['rating'] = rating
        await query.edit_message_text("Izohingizni kiriting:")

async def show_rating_scale(query, context, message_text):
    rating_labels = ["Juda yomon", "Yomon", "O'rtacha", "Yaxshi", "Ajoyib"]
    keyboard = [
        [InlineKeyboardButton(f"{i} ⭐ - {rating_labels[i-1]}", callback_data=f"rate_{i}")] 
        for i in range(1, 6)
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(message_text, reply_markup=reply_markup)

async def send_final_review(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int):
    try:
        user_info = user_data[user_id]
        rating_labels = ["Juda yomon", "Yomon", "O'rtacha", "Yaxshi", "Ajoyib"]
        rating = user_info["rating"]
        username = update.message.from_user.username or "Yo'q"

        if user_info['rating_type'] == 'afitsiant':
            item_name = user_info['afitsiant']
            item_type = "Afitsiant"
            emoji = "👨‍🍳"
        else:
            item_name = user_info['taom']
            item_type = "Taom"
            emoji = "🍽"

        phone = user_info['telefon']
        if not phone.startswith("+"):
            phone = "+" + phone

        review_message = (
            f"✅ Yangi {item_type.lower()} bahosi!\n\n"
            f"👤 Mijoz ismi: {user_info['ismi']}\n"
            f"📞 Telefon: {phone}\n"
            f"📍 Stol turi: {user_info.get('stol_turi',)}\n"
            f"🪑 Stol raqami: {user_info.get('stol',)}\n"
            f"{emoji} {item_type}: {item_name}\n"
            f"⭐ Baho: {rating} - {rating_labels[rating-1]}\n"
            f"📝 Izoh: {user_info.get('izoh', 'Yoq')}\n"
            f"🔗 Foydalanuvchi: @{username}"
        )

        user_response = (
            "✅ Rahmat! Bahoyingiz qabul qilindi.\n\n"
            "📊 Baholash natijalari:\n"
            f"{emoji} {item_type}: {item_name}\n"
            f"⭐ Baho: {rating} ⭐\n"
            f"📝 Izoh: {user_info.get('izoh', 'Yoq')}\n"
            f"📍 Stol turi: {user_info.get('stol_turi',)}\n"
            f"🪑 Stol raqami: {user_info.get('stol', )}\n\n"
            "Yana baho bermoqchimisiz? /start buyrug'ini bosing."
        )
        
        try:
            await context.bot.send_message(chat_id=GROUP_CHAT_ID, text=review_message)
        except Exception as e:
            logger.error(f"Guruhga xabar yuborishda xato: {e}")
        
        await update.message.reply_text(user_response)
        
    except Exception as e:
        logger.error(f"Xatolik yuz berdi: {e}")
        await update.message.reply_text("Kechirasiz, xatolik yuz berdi. Iltimos, /start buyrug'i orqali qaytadan urinib ko'ring")
    finally:
        if user_id in user_data:
            del user_data[user_id]
        if 'message_ids' in context.user_data:
            del context.user_data['message_ids']

async def contact_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if update.message.contact: 
        await update.message.reply_text(
            "Rahmat, telefon qabul qilindi.",
            reply_markup=ReplyKeyboardRemove()
        )

        user_data[user_id]['telefon'] = update.message.contact.phone_number
        await show_stol_turlari(update, context)
    else:
        await update.message.reply_text("Iltimos, kontaktingizni tugma orqali yuboring yoki raqamni qo'lda kiriting.")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "🆘 Yordam menyusi:\n\n"
        "Bot orqali afitsiantlar va taomlarga baho bera olasiz.\n"
        "Boshlash uchun /start buyrug'ini bosing.\n\n"
        "📞 Aloqa uchun: +998946831459\n"
        "📩 Telegram: @Z_Muhammadabdullo"
    )
    await update.message.reply_text(help_text)

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Xatolik yuz berdi: {context.error}", exc_info=True)
    if isinstance(update, Update) and update.message:
        await update.message.reply_text(
            "⚠️ Kechirasiz, xatolik yuz berdi. Iltimos, /start buyrug'i orqali qaytadan urinib ko'ring."
        )

def main():
    app = Application.builder().token(TOKEN).build()
    
    app.add_error_handler(error_handler)
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(MessageHandler(filters.CONTACT, contact_handler))
    app.add_handler(CallbackQueryHandler(button))
    
    app.run_polling()

if __name__ == "__main__":
    main() 