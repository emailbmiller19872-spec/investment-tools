import sqlite3
import os
import logging

class Database:
    def __init__(self, db_path='data/airdrop_bot.db'):
        self.db_path = db_path
        self.init_db()
        self.logger = logging.getLogger(__name__)

    def init_db(self):
        """Initialize database tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Airdrops table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS airdrops (
                id INTEGER PRIMARY KEY,
                url TEXT UNIQUE,
                title TEXT,
                participated INTEGER DEFAULT 0,
                participated_at TIMESTAMP,
                reward_amount REAL,
                reward_token TEXT,
                status TEXT DEFAULT 'pending'
            )
        ''')
        
        # Balances table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS balances (
                id INTEGER PRIMARY KEY,
                token TEXT,
                amount REAL,
                usd_value REAL,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Transactions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY,
                airdrop_id INTEGER,
                tx_hash TEXT,
                amount REAL,
                token TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (airdrop_id) REFERENCES airdrops (id)
            )
        ''')
        
        conn.commit()
        conn.close()

    def is_participated(self, url):
        """Check if already participated in airdrop"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT participated FROM airdrops WHERE url = ?', (url,))
        result = cursor.fetchone()
        conn.close()
        return result and result[0] == 1

    def mark_participated(self, url, reward_amount=None, reward_token=None):
        """Mark airdrop as participated"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO airdrops (url, participated, participated_at, reward_amount, reward_token, status)
            VALUES (?, 1, datetime('now'), ?, ?, 'completed')
        ''', (url, reward_amount, reward_token))
        conn.commit()
        conn.close()

    def add_transaction(self, airdrop_url, tx_hash, amount, token):
        """Add transaction record"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM airdrops WHERE url = ?', (airdrop_url,))
        airdrop_id = cursor.fetchone()
        if airdrop_id:
            cursor.execute('''
                INSERT INTO transactions (airdrop_id, tx_hash, amount, token)
                VALUES (?, ?, ?, ?)
            ''', (airdrop_id[0], tx_hash, amount, token))
        conn.commit()
        conn.close()

    def update_balance(self, token, amount, usd_value=None):
        """Update token balance"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO balances (token, amount, usd_value, last_updated)
            VALUES (?, ?, ?, datetime('now'))
        ''', (token, amount, usd_value))
        conn.commit()
        conn.close()

    def get_balances(self):
        """Get all balances"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT token, amount, usd_value FROM balances')
        balances = cursor.fetchall()
        conn.close()
        return balances