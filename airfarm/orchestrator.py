import os
import time
import json
import random
import logging
import schedule
import concurrent.futures
from dotenv import load_dotenv
from scraper import AirdropScraper
from task_automator import TaskAutomator
from wallet_manager import WalletManager
from database import Database
from utils import random_delay, load_env_int, load_env_bool
from decision_engine import ScoringEngine

load_dotenv()

class AirdropOrchestrator:
    def __init__(self, config_path='config/airdrop_tasks.json'):
        self.logger = logging.getLogger(__name__)
        self.db = Database()
        self.scraper = AirdropScraper()
        self.wallet_manager = WalletManager()
        self.scorer = ScoringEngine()
        self.config = self.load_config(config_path)
        self.max_workers = max(load_env_int('MAX_WORKERS', 2), 1)
        self.concurrent = load_env_bool('CONCURRENT_WALLETS', True)
        self.consolidation_min_minutes = max(load_env_int('CONSOLIDATION_MIN_MINUTES', 15), 1)
        self.consolidation_max_minutes = max(load_env_int('CONSOLIDATION_MAX_MINUTES', 360), self.consolidation_min_minutes)
        self.next_consolidation_time = None

    def load_config(self, config_path):
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                self.logger.warning(f"Failed to parse config {config_path}: {e}")
        return {
            'targets': [],
            'max_airdrops_per_cycle': int(os.getenv('MAX_AIRDROPS_PER_CYCLE', 10))
        }

    def _process_airdrop(self, airdrop):
        wallet = self.wallet_manager.rotate_wallet()
        if wallet is None:
            self.logger.error('No wallet available for airdrop processing')
            return False, airdrop

        self.logger.info(f"Using wallet {wallet['address']} for {airdrop['title']}")
        automator = TaskAutomator(self.wallet_manager)
        automator.set_wallet(wallet)
        success = automator.participate(airdrop)
        automator.cleanup()
        return success, airdrop

    def _schedule_next_consolidation(self):
        delay_minutes = random.randint(self.consolidation_min_minutes, self.consolidation_max_minutes)
        self.next_consolidation_time = time.time() + delay_minutes * 60
        self.logger.info(f'Scheduled next consolidation in {delay_minutes} minutes')

    def run_consolidation(self):
        if not self.wallet_manager.has_consolidation_config():
            self.logger.info('Consolidation not configured or disabled')
            return

        self.logger.info('Starting wallet consolidation cycle')
        result = self.wallet_manager.consolidate_all_wallets()
        self.logger.info(f'Consolidation result: {result}')

    def run_cycle(self):
        try:
            self.logger.info('Starting airdrop discovery cycle')
            airdrops = self.scraper.discover_airdrops()
            
            # Score and rank airdrops
            scored_airdrops = self.scorer.score_batch(airdrops)
            self.logger.info(f'Scored {len(scored_airdrops)} airdrops')
            
            # Filter to high-potential opportunities
            high_potential = [a for a in scored_airdrops if self.scorer.should_farm(a)]
            self.logger.info(f'Found {len(high_potential)} high-potential airdrops to farm')
            
            max_per_cycle = int(os.getenv('MAX_AIRDROPS_PER_CYCLE', 10))
            selected = high_potential[:max_per_cycle]

            if self.concurrent and selected:
                with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                    futures = [executor.submit(self._process_airdrop, airdrop) for airdrop in selected]
                    for future in concurrent.futures.as_completed(futures):
                        success, airdrop = future.result()
                        if success:
                            self.db.mark_participated(airdrop['url'])
                            self.logger.info(f"Successfully participated in {airdrop['title']} (Score: {airdrop.get('score', 0)})")
                        else:
                            self.logger.warning(f"Failed to participate in {airdrop['title']} (Score: {airdrop.get('score', 0)})")
                        random_delay(20, 40)
            else:
                for airdrop in selected:
                    success, _ = self._process_airdrop(airdrop)
                    if success:
                        self.db.mark_participated(airdrop['url'])
                        self.logger.info(f"Successfully participated in {airdrop['title']} (Score: {airdrop.get('score', 0)})")
                    else:
                        self.logger.warning(f"Failed to participate in {airdrop['title']} (Score: {airdrop.get('score', 0)})")
                    random_delay(20, 40)

            self.wallet_manager.update_balances()
            self.logger.info('Cycle completed')
        except Exception as e:
            self.logger.error(f'Cycle error: {e}')
            time.sleep(300)

    def start(self):
        self.logger.info('Starting Airdrop Orchestrator')
        self.run_cycle()
        self._schedule_next_consolidation()
        interval = load_env_int('CHECK_INTERVAL_HOURS', 6)
        schedule.every(interval).hours.do(self.run_cycle)
        try:
            while True:
                schedule.run_pending()
                if self.next_consolidation_time and time.time() >= self.next_consolidation_time:
                    self.run_consolidation()
                    self._schedule_next_consolidation()
                time.sleep(60)
        except KeyboardInterrupt:
            self.logger.info('Shutting down orchestrator')
