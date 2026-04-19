import os
import sys
import time
import logging
from dotenv import load_dotenv
import schedule

load_dotenv()

# Determine which bot to run based on BOT_TYPE environment variable
BOT_TYPE = os.getenv('BOT_TYPE', 'coinbot').lower()

if BOT_TYPE == 'coinbot':
    from coinbot.scraper import FaucetScraper
    from coinbot.task_automator import TaskAutomator
    from coinbot.wallet_manager import WalletManager
    from coinbot.proxy_manager import ProxyManager
    from coinbot.captcha_solver import CaptchaSolver
    from coinbot.consolidation import ConsolidationEngine
    from coinbot.database import Database
    from coinbot.utils import setup_logging, random_delay
elif BOT_TYPE == 'airfarm':
    from airfarm.scraper import AirdropScraper
    from airfarm.task_automator import TaskAutomator
    from airfarm.wallet_manager import WalletManager
    from airfarm.proxy_manager import ProxyManager
    from airfarm.captcha_solver import CaptchaSolver
    from airfarm.consolidation import ConsolidationEngine
    from airfarm.database import Database
    from airfarm.utils import setup_logging, random_delay
else:
    print(f"Error: Invalid BOT_TYPE '{BOT_TYPE}'. Must be 'coinbot' or 'airfarm'")
    sys.exit(1)

setup_logging()

class AutonomousBot:
    def __init__(self):
        if BOT_TYPE == 'coinbot':
            self.scraper = FaucetScraper()
            self.bot_name = "Faucet Collector"
        else:
            self.scraper = AirdropScraper()
            self.bot_name = "Airdrop Farmer"
        
        self.automator = TaskAutomator()
        self.wallet = WalletManager()
        self.consolidator = ConsolidationEngine(self.wallet)
        self.proxy_manager = ProxyManager()
        self.captcha_solver = CaptchaSolver()
        self.db = Database()
        self.logger = logging.getLogger(__name__)

    def run_cycle(self):
        """Main cycle: discover, participate, and track"""
        try:
            self.logger.info(f"Starting {self.bot_name} cycle")
            
            if BOT_TYPE == 'coinbot':
                items = self.scraper.discover_faucets()
                item_type = "faucet"
            else:
                items = self.scraper.discover_airdrops()
                item_type = "airdrop"
            
            for item in items:
                if self.db.is_participated(item['url']):
                    continue
                
                self.logger.info(f"Processing {item_type}: {item['title']}")
                success = self.automator.participate(item)
                
                if success:
                    self.db.mark_participated(item['url'])
                    self.logger.info(f"Successfully participated in {item['title']}")
                else:
                    self.logger.warning(f"Failed to participate in {item['title']}")
                
                random_delay(30, 60)
            
            self.wallet.update_balances()
            self.consolidator.run_consolidation_cycle()
            self.logger.info("Cycle completed")
            
        except Exception as e:
            self.logger.error(f"Error in run_cycle: {e}")
            time.sleep(300)

    def start(self):
        """Start the autonomous bot"""
        self.logger.info(f"Starting Autonomous {self.bot_name}")
        
        self.run_cycle()
        
        if BOT_TYPE == 'coinbot':
            interval_hours = int(os.getenv('CLAIM_INTERVAL_HOURS', 1))
        else:
            interval_hours = int(os.getenv('CHECK_INTERVAL_HOURS', 6))
        
        schedule.every(interval_hours).hours.do(self.run_cycle)

        consolidation_interval_minutes = int(os.getenv('CONSOLIDATION_INTERVAL_MINUTES', '0'))
        if consolidation_interval_minutes > 0:
            schedule.every(consolidation_interval_minutes).minutes.do(self.consolidator.run_consolidation_cycle)

        try:
            while True:
                schedule.run_pending()
                time.sleep(60)
        except KeyboardInterrupt:
            self.logger.info("Shutting down gracefully")

if __name__ == "__main__":
    bot = AutonomousBot()
    bot.start()