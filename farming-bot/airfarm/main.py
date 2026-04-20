import os
import time
import logging
from dotenv import load_dotenv
import schedule
from scraper import AirdropScraper
from task_automator import TaskAutomator
from wallet_manager import WalletManager
from consolidation import ConsolidationEngine
from database import Database
from utils import setup_logging, random_delay

load_dotenv()
setup_logging()

class AutonomousAirdropBot:
    def __init__(self):
        self.scraper = AirdropScraper()
        self.automator = TaskAutomator()
        self.wallet = WalletManager()
        self.consolidator = ConsolidationEngine(self.wallet)
        self.db = Database()
        self.logger = logging.getLogger(__name__)

    def run_cycle(self):
        try:
            self.logger.info("Starting airdrop discovery cycle")
            airdrops = self.scraper.discover_airdrops()
            for airdrop in airdrops:
                if self.db.is_participated(airdrop['url']):
                    continue
                self.logger.info(f"Processing airdrop: {airdrop['title']}")
                success = self.automator.participate(airdrop)
                if success:
                    self.db.mark_participated(airdrop['url'])
                    self.logger.info(f"Successfully participated in {airdrop['title']}")
                else:
                    self.logger.warning(f"Failed to participate in {airdrop['title']}")
                random_delay(30, 60)
            self.wallet.update_balances()
            self.consolidator.run_consolidation_cycle()
            self.logger.info("Cycle completed")
        except Exception as e:
            self.logger.error(f"Error in run_cycle: {e}")
            time.sleep(300)

    def start(self):
        self.logger.info("Starting Autonomous Airdrop Farmer")
        self.run_cycle()
        interval_hours = int(os.getenv('CHECK_INTERVAL_HOURS', 6))
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
    bot = AutonomousAirdropBot()
    bot.start()
