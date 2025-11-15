import logging
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler, CallbackQueryHandler
import config
from database import Database

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

db = Database()

CHOOSING_ACTION, OFFER_USER_ID, OFFER_PRODUCT, OFFER_DESCRIPTION, OFFER_PRICE = range(5)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if str(user_id) != config.ADMIN_ID:
        await update.message.reply_text("Nie masz uprawnień do tego bota.")
        return ConversationHandler.END
    
    keyboard = [
        ['📋 Oczekujące konta', '📦 Wszystkie zamówienia'],
        ['👥 Wszyscy użytkownicy', '🎁 Dodaj ofertę specjalną'],
        ['📊 Statystyki']
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    await update.message.reply_text(
        "🔧 PANEL ADMINA\n\nWybierz akcję:",
        reply_markup=reply_markup
    )
    return CHOOSING_ACTION

async def handle_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    
    if text == '📋 Oczekujące konta':
        return await show_pending_accounts(update, context)
    elif text == '📦 Wszystkie zamówienia':
        return await show_all_orders(update, context)
    elif text == '👥 Wszyscy użytkownicy':
        return await show_all_users(update, context)
    elif text == '🎁 Dodaj ofertę specjalną':
        return await start_special_offer(update, context)
    elif text == '📊 Statystyki':
        return await show_statistics(update, context)
    
    return CHOOSING_ACTION

async def show_pending_accounts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pending = db.get_pending_accounts()
    
    if not pending:
        await update.message.reply_text("Brak oczekujących wniosków o konto.")
        return CHOOSING_ACTION
    
    text = f"📋 OCZEKUJĄCE WNIOSKI ({len(pending)}):\n\n"
    
    for acc in pending:
        text += f"#{acc[0]}\n"
        text += f"Telegram ID: {acc[1]}\n"
        text += f"Username: {acc[2]}\n"
        text += f"Hasło: {acc[3]}\n"
        text += f"Data: {acc[4]}\n"
        
        keyboard = [
            [
                InlineKeyboardButton("✅ Zatwierdź", callback_data=f"approve_{acc[0]}"),
                InlineKeyboardButton("❌ Odrzuć", callback_data=f"reject_{acc[0]}")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(text, reply_markup=reply_markup)
        text = ""
    
    return CHOOSING_ACTION

async def show_all_orders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    orders = db.get_all_orders()
    
    if not orders:
        await update.message.reply_text("Brak zamówień.")
        return CHOOSING_ACTION
    
    text = f"📦 WSZYSTKIE ZAMÓWIENIA ({len(orders)}):\n\n"
    
    for order in orders[:20]:
        text += f"#{order[0]} - {order[2]}\n"
        text += f"Produkt: {order[3]} ({order[4]}g)\n"
        text += f"Kwota: {order[6]} zł\n"
        text += f"Płatność: {order[7]}\n"
        text += f"Data: {order[9]}\n\n"
    
    if len(orders) > 20:
        text += f"... i {len(orders) - 20} więcej"
    
    await update.message.reply_text(text)
    return CHOOSING_ACTION

async def show_all_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    users = db.get_all_users()
    
    if not users:
        await update.message.reply_text("Brak zarejestrowanych użytkowników.")
        return CHOOSING_ACTION
    
    text = f"👥 WSZYSCY UŻYTKOWNICY ({len(users)}):\n\n"
    
    for user in users:
        text += f"ID: {user[0]}\n"
        text += f"Username: {user[1]}\n"
        text += f"Data: {user[4]}\n\n"
    
    await update.message.reply_text(text)
    return CHOOSING_ACTION

async def start_special_offer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎁 NOWA OFERTA SPECJALNA\n\n"
        "Podaj Telegram ID użytkownika:"
    )
    return OFFER_USER_ID

async def handle_offer_user_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    
    try:
        user_id = int(text)
        user = db.get_user(user_id)
        
        if not user:
            await update.message.reply_text(
                "Użytkownik o tym ID nie istnieje lub nie ma zatwierdzonego konta.\n"
                "Podaj prawidłowe ID:"
            )
            return OFFER_USER_ID
        
        context.user_data['offer_user_id'] = user_id
        context.user_data['offer_username'] = user[1]
        
        await update.message.reply_text(
            f"Użytkownik: {user[1]}\n\n"
            "Podaj nazwę produktu (np. 'Diament Premium'):"
        )
        return OFFER_PRODUCT
        
    except ValueError:
        await update.message.reply_text("Podaj prawidłowy numer ID:")
        return OFFER_USER_ID

async def handle_offer_product(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['offer_product'] = update.message.text
    
    await update.message.reply_text("Podaj opis oferty:")
    return OFFER_DESCRIPTION

async def handle_offer_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['offer_description'] = update.message.text
    
    await update.message.reply_text("Podaj cenę (zł/g):")
    return OFFER_PRICE

async def handle_offer_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    
    try:
        price = float(text)
        
        user_id = context.user_data['offer_user_id']
        product = context.user_data['offer_product']
        description = context.user_data['offer_description']
        username = context.user_data['offer_username']
        
        offer_id = db.create_special_offer(user_id, product, description, price)
        
        await update.message.reply_text(
            f"✅ Oferta specjalna utworzona!\n\n"
            f"ID oferty: #{offer_id}\n"
            f"Dla: {username}\n"
            f"Produkt: {product}\n"
            f"Cena: {price} zł/g"
        )
        
        try:
            notification = f"🎁 NOWA OFERTA SPECJALNA DLA CIEBIE!\n\n"
            notification += f"Produkt: {product}\n"
            notification += f"{description}\n"
            notification += f"Cena: {price} zł/g\n\n"
            notification += "Sprawdź sekcję ZAKUP aby zobaczyć!"
            
            await context.bot.send_message(chat_id=user_id, text=notification)
        except Exception as e:
            logger.error(f"Nie można wysłać powiadomienia do użytkownika: {e}")
        
        context.user_data.clear()
        return await start(update, context)
        
    except ValueError:
        await update.message.reply_text("Podaj prawidłową cenę:")
        return OFFER_PRICE

async def show_statistics(update: Update, context: ContextTypes.DEFAULT_TYPE):
    users = db.get_all_users()
    orders = db.get_all_orders()
    pending = db.get_pending_accounts()
    
    total_revenue = sum(order[6] for order in orders)
    
    text = "📊 STATYSTYKI\n\n"
    text += f"👥 Użytkownicy: {len(users)}\n"
    text += f"📦 Zamówienia: {len(orders)}\n"
    text += f"💰 Całkowity przychód: {total_revenue} zł\n"
    text += f"⏳ Oczekujące konta: {len(pending)}\n"
    
    await update.message.reply_text(text)
    return CHOOSING_ACTION

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data.startswith('approve_'):
        request_id = int(data.split('_')[1])
        
        if db.approve_account(request_id):
            await query.edit_message_text(
                text=query.message.text + "\n\n✅ ZATWIERDZONO"
            )
            
            pending = db.get_pending_accounts()
            for acc in pending:
                if acc[0] == request_id:
                    try:
                        await context.bot.send_message(
                            chat_id=acc[1],
                            text="✅ Twoje konto zostało zatwierdzone!\n\nMożesz teraz korzystać ze wszystkich funkcji."
                        )
                    except:
                        pass
                    break
        else:
            await query.edit_message_text(
                text=query.message.text + "\n\n❌ BŁĄD"
            )
    
    elif data.startswith('reject_'):
        request_id = int(data.split('_')[1])
        db.reject_account(request_id)
        
        await query.edit_message_text(
            text=query.message.text + "\n\n❌ ODRZUCONO"
        )

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    return await start(update, context)

def main():
    if not config.ADMIN_BOT_TOKEN:
        logger.error("ADMIN_BOT_TOKEN nie jest ustawiony!")
        return
    
    if not config.ADMIN_ID:
        logger.error("ADMIN_ID nie jest ustawiony!")
        return
    
    application = Application.builder().token(config.ADMIN_BOT_TOKEN).build()
    
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            CHOOSING_ACTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_action)],
            OFFER_USER_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_offer_user_id)],
            OFFER_PRODUCT: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_offer_product)],
            OFFER_DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_offer_description)],
            OFFER_PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_offer_price)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )
    
    application.add_handler(conv_handler)
    application.add_handler(CallbackQueryHandler(handle_callback))
    
    logger.info("Bot admina uruchomiony!")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()