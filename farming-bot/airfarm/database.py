import os
import logging
import psycopg2
from psycopg2.extras import RealDictCursor

class Database:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.conn = None
        self._connect()

    def _connect(self):
        database_url = os.getenv('DATABASE_URL')
        if not database_url:
            raise ValueError("DATABASE_URL environment variable not set")
        self.conn = psycopg2.connect(database_url)
        self._init_db()

    def _init_db(self):
        with self.conn.cursor() as cur:
            cur.execute('''
                CREATE TABLE IF NOT EXISTS airdrops (
                    id SERIAL PRIMARY KEY,
                    url TEXT UNIQUE,
                    title TEXT,
                    participated INTEGER DEFAULT 0,
                    participated_at TIMESTAMP,
                    reward_amount REAL,
                    reward_token TEXT,
                    status TEXT DEFAULT 'pending'
                )
            ''')
            cur.execute('''
                CREATE TABLE IF NOT EXISTS balances (
                    id SERIAL PRIMARY KEY,
                    token TEXT,
                    amount REAL,
                    usd_value REAL,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            cur.execute('''
                CREATE TABLE IF NOT EXISTS transactions (
                    id SERIAL PRIMARY KEY,
                    airdrop_id INTEGER,
                    tx_hash TEXT,
                    amount REAL,
                    token TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
        self.conn.commit()

    def is_participated(self, url):
        with self.conn.cursor() as cur:
            cur.execute('SELECT participated FROM airdrops WHERE url = %s', (url,))
            result = cur.fetchone()
        return result and result[0] == 1

    def mark_participated(self, url, reward_amount=None, reward_token=None):
        with self.conn.cursor() as cur:
            cur.execute('''
                INSERT INTO airdrops (url, participated, participated_at, reward_amount, reward_token, status)
                VALUES (%s, 1, NOW(), %s, %s, 'completed')
                ON CONFLICT (url) DO UPDATE SET
                    participated = 1,
                    participated_at = NOW(),
                    reward_amount = EXCLUDED.reward_amount,
                    reward_token = EXCLUDED.reward_token,
                    status = 'completed'
            ''', (url, reward_amount, reward_token))
        self.conn.commit()

    def add_transaction(self, airdrop_url, tx_hash, amount, token):
        with self.conn.cursor() as cur:
            cur.execute('SELECT id FROM airdrops WHERE url = %s', (airdrop_url,))
            airdrop_id = cur.fetchone()
            if airdrop_id:
                cur.execute('''
                    INSERT INTO transactions (airdrop_id, tx_hash, amount, token)
                    VALUES (%s, %s, %s, %s)
                ''', (airdrop_id[0], tx_hash, amount, token))
        self.conn.commit()

    def update_balance(self, token, amount, usd_value=None):
        with self.conn.cursor() as cur:
            cur.execute('''
                INSERT INTO balances (token, amount, usd_value, last_updated)
                VALUES (%s, %s, %s, NOW())
                ON CONFLICT (token) DO UPDATE SET
                    amount = EXCLUDED.amount,
                    usd_value = EXCLUDED.usd_value,
                    last_updated = NOW()
            ''', (token, amount, usd_value))
        self.conn.commit()

    def get_balances(self):
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute('SELECT token, amount, usd_value FROM balances')
            return cur.fetchall()
