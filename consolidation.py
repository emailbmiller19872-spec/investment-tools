import os
import random
import time
import logging
from decimal import Decimal

from wallet_manager import WalletManager


def str_to_bool(value, default=False):
    if value is None:
        return default
    return str(value).strip().lower() in ('1', 'true', 'yes', 'on')


class FundingEngine:
    def __init__(self, wallet_manager: WalletManager):
        self.wallet_manager = wallet_manager
        self.enabled = str_to_bool(os.getenv('AIRFARM_FUNDING_ENABLED', 'true'), True)
        self.min_balance = Decimal(os.getenv('AIRFARM_MIN_FUND_BALANCE_ETH', '0.03'))
        self.fund_amount = Decimal(os.getenv('AIRFARM_FUND_AMOUNT_ETH', '0.06'))
        self.delay_min = int(os.getenv('AIRFARM_FUNDING_DELAY_MIN_SECONDS', '10'))
        self.delay_max = int(os.getenv('AIRFARM_FUNDING_DELAY_MAX_SECONDS', '25'))
        self.logger = logging.getLogger(__name__)

    def ensure_airfarm_funded(self):
        if not self.enabled:
            self.logger.info('Airfarm funding is disabled')
            return

        source = self.wallet_manager.get_default_wallet()
        targets = self.wallet_manager.get_airfarm_wallets()

        if not source:
            self.logger.warning('No coinbot funding wallet configured; skipping airfarm funding')
            return

        if not targets:
            self.logger.warning('No airfarm wallet addresses configured; skipping airfarm funding')
            return

        self.logger.info('Checking airfarm wallet funding levels')
        for wallet in targets:
            balance = Decimal(str(self.wallet_manager.get_balance(wallet=wallet)))
            self.logger.debug(f"Airfarm wallet {wallet['address']} balance: {balance} ETH")

            if balance < self.min_balance:
                transfer_amount = self.fund_amount
                if transfer_amount <= 0:
                    self.logger.warning('No valid AIRFARM_FUND_AMOUNT_ETH configured; skipping fund transfer')
                    continue

                self.logger.info(
                    f"Funding airfarm wallet {wallet['address']} with {transfer_amount} ETH from {source['address']}"
                )
                tx_hash = self.wallet_manager.send_transaction(
                    wallet['address'], float(transfer_amount), wallet=source
                )

                if tx_hash:
                    self.logger.info(f"Airfarm funding tx sent: {tx_hash}")
                else:
                    self.logger.error(f"Failed to fund airfarm wallet {wallet['address']}")

                time.sleep(random.uniform(self.delay_min, self.delay_max))
            else:
                self.logger.debug(f"Airfarm wallet {wallet['address']} is already funded")


class ConsolidationEngine:
    def __init__(self, wallet_manager: WalletManager):
        self.wallet_manager = wallet_manager
        self.enabled = str_to_bool(os.getenv('CONSOLIDATION_ENABLED', 'true'), True)
        self.min_balance = Decimal(os.getenv('CONSOLIDATION_MIN_BALANCE_ETH', '0.02'))
        self.gas_buffer = Decimal(os.getenv('CONSOLIDATION_GAS_BUFFER_ETH', '0.002'))
        self.delay_min = int(os.getenv('CONSOLIDATION_DELAY_MIN_SECONDS', '10'))
        self.delay_max = int(os.getenv('CONSOLIDATION_DELAY_MAX_SECONDS', '30'))
        self.final_sweep_enabled = str_to_bool(os.getenv('AIRFARM_FINAL_SWEEP_ENABLED', 'false'), False)
        self.logger = logging.getLogger(__name__)

    def _should_sweep(self, balance_eth: Decimal) -> bool:
        return balance_eth > (self.min_balance + self.gas_buffer)

    def _get_send_amount(self, balance_eth: Decimal) -> Decimal:
        return balance_eth - self.gas_buffer

    def _sweep_to_target(self, source_wallets, target_wallet, label):
        if not target_wallet:
            self.logger.warning(f"No {label} target wallet configured; skipping sweep")
            return 0

        if not source_wallets:
            self.logger.warning(f"No {label} source wallets configured; skipping sweep")
            return 0

        self.logger.info(f"Running {label} sweep")
        sweep_count = 0

        for wallet in source_wallets:
            if not wallet.get('private_key'):
                self.logger.warning(f"Skipping {wallet['address']}: missing private key")
                continue

            balance = Decimal(str(self.wallet_manager.get_balance(wallet=wallet)))
            self.logger.debug(f"{label.capitalize()} source {wallet['address']} balance = {balance} ETH")

            if not self._should_sweep(balance):
                self.logger.info(f"Skipping {wallet['address']}: below threshold")
                continue

            send_amount = self._get_send_amount(balance)
            if send_amount <= 0:
                self.logger.warning(f"No funds available after gas buffer for {wallet['address']}")
                continue

            self.logger.info(
                f"Sweeping {float(send_amount):.6f} ETH from {wallet['address']} to {target_wallet['address']}"
            )
            tx_hash = self.wallet_manager.send_transaction(
                target_wallet['address'], float(send_amount), wallet=wallet
            )
            if tx_hash:
                self.logger.info(f"Sweep tx sent: {tx_hash}")
                sweep_count += 1
            else:
                self.logger.error(f"Failed sweep from {wallet['address']}")

            time.sleep(random.uniform(self.delay_min, self.delay_max))

        self.logger.info(f"{label.capitalize()} sweep complete: {sweep_count} tx(s)")
        return sweep_count

    def run_consolidation_cycle(self):
        if not self.enabled:
            self.logger.info('Consolidation is disabled')
            return

        master_wallet = self.wallet_manager.get_master_wallet()
        
        if not master_wallet:
            self.logger.warning('No master wallet configured; skipping consolidation')
            return

        # Sweep coinbot wallets to master
        self._sweep_to_target(
            self.wallet_manager.get_coinbot_wallets(),
            master_wallet,
            'coinbot to master'
        )

        # Sweep airfarm wallets to master (optional - for collecting rewards)
        self._sweep_to_target(
            self.wallet_manager.get_airfarm_wallets(),
            master_wallet,
            'airfarm to master'
        )
