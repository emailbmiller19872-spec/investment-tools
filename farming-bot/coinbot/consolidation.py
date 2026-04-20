import os
import random
import time
import logging
from decimal import Decimal


def str_to_bool(value, default=False):
    if value is None:
        return default
    return str(value).strip().lower() in ('1', 'true', 'yes', 'on')


class ConsolidationEngine:
    def __init__(self, wallet_manager):
        self.wallet_manager = wallet_manager
        self.master_address = os.getenv('MASTER_WALLET_ADDRESS')
        self.enabled = str_to_bool(os.getenv('CONSOLIDATION_ENABLED'), True)
        self.min_balance = Decimal(os.getenv('MIN_CONSOLIDATION_BALANCE_ETH', '0.01'))
        self.gas_buffer = Decimal(os.getenv('CONSOLIDATION_GAS_BUFFER_ETH', '0.002'))
        self.delay_min = int(os.getenv('CONSOLIDATION_DELAY_MIN_SECONDS', '10'))
        self.delay_max = int(os.getenv('CONSOLIDATION_DELAY_MAX_SECONDS', '30'))
        self.logger = logging.getLogger(__name__)

        if not self.master_address:
            self.logger.warning('MASTER_WALLET_ADDRESS is not configured; consolidation disabled.')
            self.enabled = False

    def _should_sweep(self, balance_eth: Decimal) -> bool:
        return balance_eth > (self.min_balance + self.gas_buffer)

    def _balance_to_wei(self, balance_eth: Decimal):
        return int(balance_eth * Decimal(10**18))

    def _sweep_wallet(self, wallet):
        address = wallet.get('address')
        if not address:
            return False
        if not wallet.get('private_key'):
            self.logger.warning(f"Skipping consolidation for {address}: missing private key.")
            return False

        balance = Decimal(str(self.wallet_manager.get_balance(wallet=wallet)))
        self.logger.debug(f"Checking wallet {address} balance: {balance} ETH")

        if not self._should_sweep(balance):
            self.logger.info(f"Skipping sweep for {address}: balance below threshold.")
            return False

        send_amount = balance - self.gas_buffer
        if send_amount <= 0:
            self.logger.warning(f"No available amount to sweep after buffer for {address}.")
            return False

        self.logger.info(f"Sweeping {send_amount:.6f} ETH from {address} to {self.master_address}")
        tx_hash = self.wallet_manager.send_transaction(self.master_address, float(send_amount), wallet=wallet)
        if tx_hash:
            self.logger.info(f"Sweep transaction successful for {address}: {tx_hash}")
            return True

        self.logger.warning(f"Sweep transaction failed for {address}")
        return False

    def run_consolidation_cycle(self):
        if not self.enabled:
            self.logger.info('Consolidation is disabled')
            return 0

        farm_wallets = self.wallet_manager.get_farm_wallets()
        if not farm_wallets:
            self.logger.warning('No farm wallets defined for consolidation')
            return 0

        self.logger.info('Starting consolidation cycle')
        sweep_count = 0

        for wallet in farm_wallets:
            if self._sweep_wallet(wallet):
                sweep_count += 1
                delay = random.uniform(self.delay_min, self.delay_max)
                self.logger.debug(f"Waiting {delay:.1f}s before next sweep")
                time.sleep(delay)

        self.logger.info(f'Consolidation cycle complete, sweeps executed: {sweep_count}')
        return sweep_count
