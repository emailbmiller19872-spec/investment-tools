import os
import time
import logging
from dotenv import load_dotenv
import schedule
from scraper import FaucetScraper
from task_automator import TaskAutomator
from wallet_manager import WalletManager
from consolidation import ConsolidationEngine
from database import Database
from utils import setup_logging, random_delay

load_dotenv()
setup_logging()

class AutonomousFaucetBot:
    def __init__(self):
        self.scraper = FaucetScraper()
        self.automator = TaskAutomator()
        self.wallet = WalletManager()
        self.consolidator = ConsolidationEngine(self.wallet)
        self.db = Database()
        self.logger = logging.getLogger(__name__)

    def run_cycle(self):
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
                random_delay(30, 60)
            self.wallet.update_balances()
            self.consolidator.run_consolidation_cycle()
            self.logger.info("Cycle completed")
        except Exception as e:
            self.logger.error(f"Error in run_cycle: {e}")
            time.sleep(300)

    def start(self):
        self.logger.info("Starting Autonomous Faucet Collector")
        self.run_cycle()
        interval_hours = int(os.getenv('CLAIM_INTERVAL_HOURS', 1))
        schedule.every(interval_hours).hours.do(self.run_cycle)
        consolidation_interval = int(os.getenv('CONSOLIDATION_INTERVAL_MINUTES', 0))
        if consolidation_interval > 0:
            schedule.every(consolidation_interval).minutes.do(self.consolidator.run_consolidation_cycle)
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)
        except KeyboardInterrupt:
            self.logger.info("Shutting down")

if __name__ == "__main__":
    bot = AutonomousFaucetBot()
    bot.start()
