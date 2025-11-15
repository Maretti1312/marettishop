import sqlite3
from datetime import datetime
from typing import Optional, List, Dict
import config

class Database:
    def __init__(self, db_file=config.DATABASE_FILE):
        self.db_file = db_file
        self.init_database()
    
    def get_connection(self):
        return sqlite3.connect(self.db_file)
    
    def init_database(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                telegram_username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                approved INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS pending_accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_user_id INTEGER,
                telegram_username TEXT,
                password TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                telegram_username TEXT,
                product_name TEXT,
                quantity REAL,
                unit_price REAL,
                total_price REAL,
                payment_method TEXT,
                status TEXT DEFAULT 'pending',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS special_offers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                product_name TEXT,
                description TEXT,
                price REAL,
                active INTEGER DEFAULT 1,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS help_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_user_id INTEGER,
                telegram_username TEXT,
                request_type TEXT,
                message TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def create_pending_account(self, telegram_user_id: int, username: str, password: str):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO pending_accounts (telegram_user_id, telegram_username, password) VALUES (?, ?, ?)',
            (telegram_user_id, username, password)
        )
        request_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return request_id
    
    def get_pending_accounts(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT id, telegram_user_id, telegram_username, password, created_at FROM pending_accounts')
        accounts = cursor.fetchall()
        conn.close()
        return accounts
    
    def approve_account(self, request_id: int):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT telegram_user_id, telegram_username, password FROM pending_accounts WHERE id = ?', (request_id,))
        result = cursor.fetchone()
        
        if result:
            telegram_user_id, username, password = result
            cursor.execute(
                'INSERT INTO users (user_id, telegram_username, password, approved) VALUES (?, ?, ?, 1)',
                (telegram_user_id, username, password)
            )
            cursor.execute('DELETE FROM pending_accounts WHERE id = ?', (request_id,))
            conn.commit()
            conn.close()
            return True
        
        conn.close()
        return False
    
    def reject_account(self, request_id: int):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM pending_accounts WHERE id = ?', (request_id,))
        conn.commit()
        conn.close()
    
    def get_user(self, telegram_user_id: int):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE user_id = ? AND approved = 1', (telegram_user_id,))
        user = cursor.fetchone()
        conn.close()
        return user
    
    def get_user_by_username(self, username: str):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE telegram_username = ? AND approved = 1', (username,))
        user = cursor.fetchone()
        conn.close()
        return user
    
    def create_order(self, user_id: Optional[int], username: str, product_name: str, 
                     quantity: float, unit_price: float, total_price: float, payment_method: str):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            '''INSERT INTO orders (user_id, telegram_username, product_name, quantity, 
               unit_price, total_price, payment_method) 
               VALUES (?, ?, ?, ?, ?, ?, ?)''',
            (user_id, username, product_name, quantity, unit_price, total_price, payment_method)
        )
        order_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return order_id
    
    def get_user_orders(self, user_id: int):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            'SELECT * FROM orders WHERE user_id = ? ORDER BY created_at DESC',
            (user_id,)
        )
        orders = cursor.fetchall()
        conn.close()
        return orders
    
    def get_all_orders(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM orders ORDER BY created_at DESC')
        orders = cursor.fetchall()
        conn.close()
        return orders
    
    def create_special_offer(self, user_id: int, product_name: str, description: str, price: float):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO special_offers (user_id, product_name, description, price) VALUES (?, ?, ?, ?)',
            (user_id, product_name, description, price)
        )
        offer_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return offer_id
    
    def get_special_offers(self, user_id: int):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            'SELECT * FROM special_offers WHERE user_id = ? AND active = 1',
            (user_id,)
        )
        offers = cursor.fetchall()
        conn.close()
        return offers
    
    def deactivate_offer(self, offer_id: int):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE special_offers SET active = 0 WHERE id = ?', (offer_id,))
        conn.commit()
        conn.close()
    
    def create_help_request(self, telegram_user_id: int, username: str, request_type: str, message: str):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO help_requests (telegram_user_id, telegram_username, request_type, message) VALUES (?, ?, ?, ?)',
            (telegram_user_id, username, request_type, message)
        )
        request_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return request_id
    
    def get_all_users(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE approved = 1')
        users = cursor.fetchall()
        conn.close()
        return users