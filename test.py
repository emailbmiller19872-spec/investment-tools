#!/usr/bin/env python3
"""
Test script for Autonomous Airdrop Capital Builder
Run this to test individual components before full deployment
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

def test_scraper():
    """Test airdrop discovery"""
    from scraper import AirdropScraper
    scraper = AirdropScraper()
    airdrops = scraper.discover_airdrops()
    print(f"Discovered {len(airdrops)} airdrops")
    for airdrop in airdrops[:3]:
        print(f"- {airdrop['title']}: {airdrop['url']}")

def test_database():
    """Test database operations"""
    from database import Database
    db = Database()
    db.update_balance('ETH', 1.5)
    balances = db.get_balances()
    print("Current balances:")
    for token, amount, usd in balances:
        print(f"- {token}: {amount}")

def test_wallet():
    """Test wallet connection (without real keys)"""
    from wallet_manager import WalletManager
    wm = WalletManager()
    if wm.address:
        print(f"Wallet address: {wm.address}")
        # Note: Balance check requires real provider
    else:
        print("Wallet not configured")

def test_proxy():
    """Test proxy rotation"""
    from proxy_manager import ProxyManager
    pm = ProxyManager()
    proxy = pm.get_random_proxy()
    if proxy:
        print(f"Using proxy: {proxy}")
        working = pm.test_proxy(proxy)
        print(f"Proxy working: {working}")
    else:
        print("No proxies configured")

def main():
    print("Testing Autonomous Airdrop Capital Builder components...\n")
    
    print("1. Testing scraper...")
    try:
        test_scraper()
    except Exception as e:
        print(f"Scraper test failed: {e}")
    
    print("\n2. Testing database...")
    try:
        test_database()
    except Exception as e:
        print(f"Database test failed: {e}")
    
    print("\n3. Testing wallet...")
    try:
        test_wallet()
    except Exception as e:
        print(f"Wallet test failed: {e}")
    
    print("\n4. Testing proxy...")
    try:
        test_proxy()
    except Exception as e:
        print(f"Proxy test failed: {e}")
    
    print("\nTest complete. Check logs for detailed information.")

if __name__ == "__main__":
    main()