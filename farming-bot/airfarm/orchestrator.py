import os
import time
import logging
import schedule
from scraper import AirdropScraper
from task_automator import TaskAutomator
from wallet_manager import WalletManager
from consolidation import ConsolidationEngine
from decision_engine import ScoringEngine
from database import Database
from utils import random_delay

class AirdropOrchestrator:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.db = Database()
        self.scraper = AirdropScraper()
        self.wallet_manager = WalletManager()
        self.scorer = ScoringEngine()
        self.automator = TaskAutomator(self.wallet_manager)
        self.consolidator = ConsolidationEngine(self.wallet_manager)

    def run_cycle(self):
        try:
            self.logger.info("Starting airdrop discovery cycle")
            airdrops = self.scraper.discover_airdrops()
            scored = self.scorer.score_batch(airdrops)
            high_potential = [a for a in scored if self.scorer.should_farm(a)]
            for airdrop in high_potential[:int(os.getenv('MAX_AIRDROPS_PER_CYCLE', 10))]:
                if self.db.is_participated(airdrop['url']):
                    continue
                wallet = self.wallet_manager.rotate_wallet()
                if not wallet:
                    break
                self.automator.set_wallet(wallet)
                success = self.automator.participate(airdrop)
                if success:
                    self.db.mark_participated(airdrop['url'])
                random_delay(30, 60)
            self.consolidator.run_consolidation_cycle()
        except Exception as e:
            self.logger.error(f"Cycle error: {e}")
            time.sleep(300)

    def start(self):
        self.logger.info("Starting Airdrop Orchestrator")
        self.run_cycle()
        interval = int(os.getenv('CHECK_INTERVAL_HOURS', 6))
        schedule.every(interval).hours.do(self.run_cycle)
        while True:
            schedule.run_pending()
            time.sleep(60)
