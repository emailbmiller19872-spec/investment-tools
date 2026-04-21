import os
import sqlite3
import json
from datetime import datetime
from database import Database

def show_status():
    """Display current bot status and statistics"""
    print("\n" + "="*60)
    print("       COINBOT FAUCET COLLECTOR STATUS")
    print("="*60)

    # Check if log file exists and show recent activity
    log_file = 'logs/airdrop_bot.log'
    if os.path.exists(log_file):
        print("\n📋 RECENT ACTIVITY (last 10 lines):")
        with open(log_file, 'r') as f:
            lines = f.readlines()
            for line in lines[-10:]:
                print("   " + line.strip())
    else:
        print("\n⚠️  No log file found. Bot may not have run yet.")

    # Check database for claimed faucets
    print("\n💰 CLAIMED FAUCETS:")
    try:
        db = Database()
        conn = sqlite3.connect(db.db_file)
        cursor = conn.cursor()
        cursor.execute("SELECT url, title, timestamp FROM participated ORDER BY timestamp DESC LIMIT 10")
        rows = cursor.fetchall()
        if rows:
            for url, title, timestamp in rows:
                print(f"   ✓ {title} - {timestamp}")
        else:
            print("   No faucets claimed yet")
        conn.close()
    except Exception as e:
        print(f"   Could not read database: {e}")

    # Check wallets
    print("\n👛 WALLETS:")
    wallet_file = 'data/wallets.json'
    if os.path.exists(wallet_file):
        try:
            with open(wallet_file, 'r') as f:
                wallets = json.load(f)
                print(f"   Total wallets: {len(wallets)}")
                for addr, data in list(wallets.items())[:3]:
                    balance = data.get('balance', 'unknown')
                    print(f"   {addr[:20]}... Balance: {balance}")
        except Exception as e:
            print(f"   Error reading wallets: {e}")
    else:
        print("   No wallets configured")

    # Show faucet definitions
    print("\n🚰 FAUCET SOURCES:")
    faucets_file = 'faucets.json'
    if os.path.exists(faucets_file):
        try:
            with open(faucets_file, 'r') as f:
                faucets = json.load(f)
                print(f"   Total faucet definitions: {len(faucets)}")
                for faucet in faucets:
                    print(f"   • {faucet.get('title', 'Unknown')}")
        except Exception as e:
            print(f"   Error reading faucets: {e}")

    print("\n" + "="*60)
    print(f"Status checked at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60 + "\n")

if __name__ == "__main__":
    show_status()
