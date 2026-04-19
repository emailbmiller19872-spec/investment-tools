import os
import time
import logging
from dotenv import load_dotenv
import schedule
from coinbot.scraper import FaucetScraper
from coinbot.task_automator import TaskAutomator
from coinbot.wallet_manager import WalletManager
from coinbot.proxy_manager import ProxyManager
from coinbot.captcha_solver import CaptchaSolver
from coinbot.consolidation import ConsolidationEngine
from coinbot.database import Database
from coinbot.utils import setup_logging, random_delay

load_dotenv()
setup_logging()

class AutonomousFaucetBot:
    def __init__(self):
        self.scraper = FaucetScraper()
        self.automator = TaskAutomator()
        self.wallet = WalletManager()
        self.consolidator = ConsolidationEngine(self.wallet)
        self.proxy_manager = ProxyManager()
        self.captcha_solver = CaptchaSolver()
        self.db = Database()
        self.logger = logging.getLogger(__name__)

    def run_cycle(self):
        """Main cycle: discover, claim, and track faucets"""
        try:
            self.logger.info("Starting faucet claim cycle")
            faucets = self.scraper.discover_faucets()
            
            for faucet in faucets:
                if self.db.is_participated(faucet['url']):
                    continue
                
                self.logger.info(f"Processing faucet: {faucet['title']}")
                success = self.automator.participate(faucet)
                
                if success:
                    self.db.mark_participated(faucet['url'])
                    self.logger.info(f"Successfully claimed faucet: {faucet['title']}")
                else:
                    self.logger.warning(f"Failed to claim faucet: {faucet['title']}")
                
                random_delay(30, 60)  # Delay between faucet claims
            
            self.wallet.update_balances()
            self.consolidator.run_consolidation_cycle()
            self.logger.info("Cycle completed")
            
        except Exception as e:
            self.logger.error(f"Error in run_cycle: {e}")
            time.sleep(300)

    def start(self):
        """Start the autonomous faucet collector"""
        self.logger.info("Starting Autonomous Faucet Collector")
        
        self.run_cycle()
        
        interval_hours = int(os.getenv('CLAIM_INTERVAL_HOURS', 1))
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
    bot = AutonomousFaucetBot()
    bot.start()