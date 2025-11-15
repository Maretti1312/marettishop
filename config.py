import os

# Tokeny botów
CUSTOMER_BOT_TOKEN = '8208677217:AAF9dPQhG8R55bo3LtpzKJ8_pDIa9NkV8rI'
ADMIN_BOT_TOKEN = '7996266811:AAEU_xB_7BI3YLR0w8xk9R3D72uRNrgmiJQ'
ADMIN_ID = '6292620803'

# Produkty
PRODUCTS = {
    '💎': {
        'name': 'Diament',
        'base_price': 60,
        'emoji': '💎'
    },
    '🥦': {
        'name': 'Brokuł',
        'base_price': 50,
        'emoji': '🥦'
    }
}

# Rabaty
DISCOUNTS = [
    {'min_grams': 30, 'discount': 20},
    {'min_grams': 20, 'discount': 15},
    {'min_grams': 10, 'discount': 10},
]

# Metody płatności
PAYMENT_METHODS = ['Gotówka', 'Przelew BLIK']

# Baza danych
DATABASE_FILE = 'shop_database.db'