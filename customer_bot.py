import logging
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler, CallbackQueryHandler
import config
from database import Database

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

db = Database()

CHOOSING_SECTION, CHOOSING_PRODUCT, CHOOSING_QUANTITY, CHOOSING_PAYMENT = range(4)
ACCOUNT_USERNAME, ACCOUNT_PASSWORD = range(4, 6)
HELP_TYPE, HELP_BULK_AMOUNT, HELP_COMPLAINT = range(6, 9)

def calculate_price(base_price: float, quantity: float) -> tuple:
    discount = 0
    for disc in config.DISCOUNTS:
        if quantity >= disc['min_grams']:
            discount = disc['discount']
            break
    
    unit_price = base_price - discount
    total_price = unit_price * quantity
    return unit_price, total_price, discount

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    keyboard = [
        ['🛒 ZAKUP'],
        ['👤 KONTO'],
        ['❓ POMOC']
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    welcome_text = f"Witaj {user.first_name}! 👋\n\n"
    welcome_text += "Wybierz jedną z opcji poniżej:"
    
    await update.message.reply_text(welcome_text, reply_markup=reply_markup)
    return CHOOSING_SECTION

async def handle_section(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    
    if text == '🛒 ZAKUP':
        return await show_products(update, context)
    elif text == '👤 KONTO':
        return await show_account(update, context)
    elif text == '❓ POMOC':
        return await show_help(update, context)
    else:
        await update.message.reply_text("Wybierz jedną z opcji z menu.")
        return CHOOSING_SECTION

async def show_products(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_db = db.get_user(user_id)
    
    text = "📦 NASZE PRODUKTY:\n\n"
    
    if user_db:
        special_offers = db.get_special_offers(user_id)
        if special_offers:
            text += "🌟 TWOJE SPECJALNE OFERTY:\n"
            for offer in special_offers:
                text += f"• {offer[2]} - {offer[3]}\n  Cena: {offer[4]} zł/g\n\n"
    
    text += "💎 Diament - 60 zł/g\n"
    text += "🥦 Brokuł - 50 zł/g\n\n"
    text += "📊 RABATY:\n"
    text += "• Od 10g: -10 zł/g\n"
    text += "• Od 20g: -15 zł/g\n"
    text += "• Od 30g: -20 zł/g\n\n"
    text += "Wybierz produkt:"
    
    keyboard = [
        ['💎 Diament', '🥦 Brokuł'],
        ['⬅️ Powrót']
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    await update.message.reply_text(text, reply_markup=reply_markup)
    return CHOOSING_PRODUCT

async def handle_product_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    
    if text == '⬅️ Powrót':
        return await start(update, context)
    
    product = None
    if '💎' in text:
        product = '💎'
    elif '🥦' in text:
        product = '🥦'
    
    if product:
        context.user_data['product'] = product
        keyboard = [['⬅️ Powrót']]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        
        await update.message.reply_text(
            f"Wybrałeś: {config.PRODUCTS[product]['name']} {product}\n\n"
            "Ile gramów chcesz kupić? (wpisz liczbę)",
            reply_markup=reply_markup
        )
        return CHOOSING_QUANTITY
    
    await update.message.reply_text("Wybierz produkt z menu.")
    return CHOOSING_PRODUCT

async def handle_quantity(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    
    if text == '⬅️ Powrót':
        return await show_products(update, context)
    
    try:
        quantity = float(text)
        if quantity <= 0:
            await update.message.reply_text("Podaj prawidłową ilość (większą od 0).")
            return CHOOSING_QUANTITY
        
        product = context.user_data['product']
        base_price = config.PRODUCTS[product]['base_price']
        unit_price, total_price, discount = calculate_price(base_price, quantity)
        
        context.user_data['quantity'] = quantity
        context.user_data['unit_price'] = unit_price
        context.user_data['total_price'] = total_price
        
        summary = f"📝 PODSUMOWANIE:\n\n"
        summary += f"Produkt: {config.PRODUCTS[product]['name']} {product}\n"
        summary += f"Ilość: {quantity}g\n"
        summary += f"Cena bazowa: {base_price} zł/g\n"
        if discount > 0:
            summary += f"Rabat: -{discount} zł/g 🎉\n"
        summary += f"Cena jednostkowa: {unit_price} zł/g\n"
        summary += f"RAZEM: {total_price} zł\n\n"
        summary += "Wybierz metodę płatności:"
        
        keyboard = [
            ['💵 Gotówka', '💳 Przelew BLIK'],
            ['⬅️ Powrót']
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        
        await update.message.reply_text(summary, reply_markup=reply_markup)
        return CHOOSING_PAYMENT
        
    except ValueError:
        await update.message.reply_text("Podaj liczbę (np. 5 lub 10.5)")
        return CHOOSING_QUANTITY

async def handle_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    
    if text == '⬅️ Powrót':
        return await handle_product_choice(update, context)
    
    payment_method = None
    if 'Gotówka' in text:
        payment_method = 'Gotówka'
    elif 'BLIK' in text:
        payment_method = 'Przelew BLIK'
    
    if payment_method:
        user = update.effective_user
        user_id = user.id
        username = user.username if user.username else user.first_name
        
        product = context.user_data['product']
        quantity = context.user_data['quantity']
        unit_price = context.user_data['unit_price']
        total_price = context.user_data['total_price']
        
        user_db = db.get_user(user_id)
        db_user_id = user_id if user_db else None
        
        order_id = db.create_order(
            db_user_id, 
            f"@{username}" if user.username else username,
            config.PRODUCTS[product]['name'],
            quantity,
            unit_price,
            total_price,
            payment_method
        )
        
        admin_message = f"🔔 NOWE ZAMÓWIENIE #{order_id}\n\n"
        admin_message += f"Klient: @{username if user.username else username}\n"
        admin_message += f"Telegram ID: {user_id}\n"
        admin_message += f"Produkt: {config.PRODUCTS[product]['name']} {product}\n"
        admin_message += f"Ilość: {quantity}g\n"
        admin_message += f"Cena: {total_price} zł\n"
        admin_message += f"Płatność: {payment_method}\n"
        
        try:
            await context.bot.send_message(
                chat_id=config.ADMIN_ID,
                text=admin_message
            )
        except Exception as e:
            logger.error(f"Nie można wysłać wiadomości do admina: {e}")
        
        confirmation = f"✅ Zamówienie złożone!\n\n"
        confirmation += f"Numer zamówienia: #{order_id}\n"
        confirmation += f"Kwota do zapłaty: {total_price} zł\n"
        confirmation += f"Metoda płatności: {payment_method}\n\n"
        confirmation += "Skontaktujemy się z Tobą wkrótce! 📞"
        
        await update.message.reply_text(confirmation)
        
        context.user_data.clear()
        return await start(update, context)
    
    await update.message.reply_text("Wybierz metodę płatności z menu.")
    return CHOOSING_PAYMENT

async def show_account(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user = db.get_user(user_id)
    
    if user:
        text = f"👤 TWOJE KONTO\n\n"
        text += f"Nazwa użytkownika: {user[1]}\n"
        text += f"Status: Zatwierdzone ✅\n\n"
        
        orders = db.get_user_orders(user_id)
        text += f"📦 Historia zakupów ({len(orders)} zamówień):\n\n"
        
        for order in orders[:5]:
            text += f"#{order[0]} - {order[3]} ({order[4]}g)\n"
            text += f"   {order[6]} zł - {order[7]}\n"
            text += f"   {order[9]}\n\n"
        
        if len(orders) > 5:
            text += f"... i {len(orders) - 5} więcej\n"
        
        keyboard = [['⬅️ Powrót']]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        
        await update.message.reply_text(text, reply_markup=reply_markup)
        return CHOOSING_SECTION
    else:
        text = "👤 UTWÓRZ KONTO\n\n"
        text += "Aby utworzyć konto, będziesz potrzebować:\n"
        text += "1. Nazwy użytkownika Telegram (zaczynającej się od @)\n"
        text += "2. Hasła (max 8 znaków)\n\n"
        text += "Wniosek zostanie wysłany do zatwierdzenia.\n\n"
        text += "Podaj swoją nazwę użytkownika Telegram (np. @twojnick):"
        
        keyboard = [['⬅️ Anuluj']]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        
        await update.message.reply_text(text, reply_markup=reply_markup)
        return ACCOUNT_USERNAME

async def handle_account_username(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    
    if text == '⬅️ Anuluj':
        return await start(update, context)
    
    if not text.startswith('@'):
        await update.message.reply_text("Nazwa użytkownika musi zaczynać się od @\nSpróbuj ponownie:")
        return ACCOUNT_USERNAME
    
    context.user_data['account_username'] = text
    
    await update.message.reply_text("Teraz podaj hasło (max 8 znaków):")
    return ACCOUNT_PASSWORD

async def handle_account_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    
    if text == '⬅️ Anuluj':
        return await start(update, context)
    
    if len(text) > 8:
        await update.message.reply_text("Hasło może mieć maksymalnie 8 znaków.\nPodaj hasło ponownie:")
        return ACCOUNT_PASSWORD
    
    username = context.user_data['account_username']
    password = text
    user = update.effective_user
    
    request_id = db.create_pending_account(user.id, username, password)
    
    admin_message = f"🆕 WNIOSEK O KONTO #{request_id}\n\n"
    admin_message += f"Telegram ID: {user.id}\n"
    admin_message += f"Nazwa: {user.first_name}\n"
    admin_message += f"Username: {username}\n"
    admin_message += f"Hasło: {password}\n"
    
    keyboard = [
        [
            InlineKeyboardButton("✅ Zatwierdź", callback_data=f"approve_{request_id}"),
            InlineKeyboardButton("❌ Odrzuć", callback_data=f"reject_{request_id}")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    try:
        await context.bot.send_message(
            chat_id=config.ADMIN_ID,
            text=admin_message,
            reply_markup=reply_markup
        )
    except Exception as e:
        logger.error(f"Nie można wysłać wiadomości do admina: {e}")
    
    await update.message.reply_text(
        "✅ Wniosek o utworzenie konta został wysłany!\n\n"
        "Poczekaj na zatwierdzenie przez administratora."
    )
    
    context.user_data.clear()
    return await start(update, context)

async def show_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = "❓ POMOC\n\n"
    text += "W czym mogę pomóc?"
    
    keyboard = [
        ['📦 Zakup większej ilości'],
        ['⚠️ Reklamacja'],
        ['⬅️ Powrót']
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    await update.message.reply_text(text, reply_markup=reply_markup)
    return HELP_TYPE

async def handle_help_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    
    if text == '⬅️ Powrót':
        return await start(update, context)
    
    if 'większej ilości' in text:
        context.user_data['help_type'] = 'bulk'
        keyboard = [['⬅️ Anuluj']]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        
        await update.message.reply_text(
            "📦 ZAKUP WIĘKSZEJ ILOŚCI\n\n"
            "Jaką kwotę szacujesz na zakup? (wpisz kwotę w zł)",
            reply_markup=reply_markup
        )
        return HELP_BULK_AMOUNT
    
    elif 'Reklamacja' in text:
        context.user_data['help_type'] = 'complaint'
        keyboard = [['⬅️ Anuluj']]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        
        await update.message.reply_text(
            "⚠️ REKLAMACJA\n\n"
            "Opisz problem, z którym się spotkałeś:",
            reply_markup=reply_markup
        )
        return HELP_COMPLAINT
    
    return HELP_TYPE

async def handle_bulk_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    
    if text == '⬅️ Anuluj':
        return await start(update, context)
    
    user = update.effective_user
    username = user.username if user.username else user.first_name
    
    message = f"Szacowana kwota: {text} zł"
    db.create_help_request(user.id, f"@{username}" if user.username else username, 'Zakup większej ilości', message)
    
    admin_message = f"📦 ZAPYTANIE O WIĘKSZĄ ILOŚĆ\n\n"
    admin_message += f"Klient: @{username if user.username else username}\n"
    admin_message += f"Telegram ID: {user.id}\n"
    admin_message += f"Szacowana kwota: {text} zł\n"
    
    try:
        await context.bot.send_message(chat_id=config.ADMIN_ID, text=admin_message)
    except Exception as e:
        logger.error(f"Nie można wysłać wiadomości do admina: {e}")
    
    await update.message.reply_text(
        "✅ Zapytanie zostało wysłane!\n\n"
        "Skontaktujemy się z Tobą wkrótce."
    )
    
    context.user_data.clear()
    return await start(update, context)

async def handle_complaint(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    
    if text == '⬅️ Anuluj':
        return await start(update, context)
    
    user = update.effective_user
    username = user.username if user.username else user.first_name
    
    db.create_help_request(user.id, f"@{username}" if user.username else username, 'Reklamacja', text)
    
    admin_message = f"⚠️ REKLAMACJA\n\n"
    admin_message += f"Klient: @{username if user.username else username}\n"
    admin_message += f"Telegram ID: {user.id}\n"
    admin_message += f"Treść:\n{text}\n"
    
    try:
        await context.bot.send_message(chat_id=config.ADMIN_ID, text=admin_message)
    except Exception as e:
        logger.error(f"Nie można wysłać wiadomości do admina: {e}")
    
    await update.message.reply_text(
        "✅ Reklamacja została zgłoszona!\n\n"
        "Przepraszamy za niedogodności. Skontaktujemy się wkrótce."
    )
    
    context.user_data.clear()
    return await start(update, context)

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text(
        "Anulowano.",
        reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END

def main():
    if not config.CUSTOMER_BOT_TOKEN:
        logger.error("CUSTOMER_BOT_TOKEN nie jest ustawiony!")
        return
    
    application = Application.builder().token(config.CUSTOMER_BOT_TOKEN).build()
    
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            CHOOSING_SECTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_section)],
            CHOOSING_PRODUCT: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_product_choice)],
            CHOOSING_QUANTITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_quantity)],
            CHOOSING_PAYMENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_payment)],
            ACCOUNT_USERNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_account_username)],
            ACCOUNT_PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_account_password)],
            HELP_TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_help_type)],
            HELP_BULK_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_bulk_amount)],
            HELP_COMPLAINT: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_complaint)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )
    
    application.add_handler(conv_handler)
    
    logger.info("Bot klienta uruchomiony!")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()