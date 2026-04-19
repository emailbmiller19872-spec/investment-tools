import os
import logging
from web3 import Web3
from web3.middleware import geth_poa_middleware
from eth_account import Account
import requests

class WalletManager:
    def __init__(self):
        self.address = os.getenv('WALLET_ADDRESS')
        self.private_key = os.getenv('PRIVATE_KEY')
        self.w3 = Web3(Web3.HTTPProvider('https://mainnet.infura.io/v3/YOUR_INFURA_KEY'))  # Replace with your provider
        self.w3.middleware_onion.inject(geth_poa_middleware, layer=0)
        self.account = Account.from_key(self.private_key) if self.private_key else None
        self.logger = logging.getLogger(__name__)
        self.balances = {}

    def connect_wallet(self, driver, dapp_url):
        """Attempt to connect wallet to dApp (simplified)"""
        try:
            driver.get(dapp_url)
            # This is highly dependent on the dApp's UI
            # For MetaMask, it would require extension interaction
            # This is a placeholder for actual implementation
            self.logger.info(f"Attempting wallet connection to {dapp_url}")
            # In practice, this would involve clicking "Connect Wallet" and handling MetaMask popup
            return True
        except Exception as e:
            self.logger.error(f"Wallet connection failed: {e}")
            return False

    def get_balance(self, token_address=None):
        """Get wallet balance"""
        try:
            if token_address:
                # ERC20 token balance
                contract = self.w3.eth.contract(address=token_address, abi=self._get_erc20_abi())
                balance = contract.functions.balanceOf(self.address).call()
                decimals = contract.functions.decimals().call()
                return balance / (10 ** decimals)
            else:
                # ETH balance
                balance = self.w3.eth.get_balance(self.address)
                return self.w3.from_wei(balance, 'ether')
        except Exception as e:
            self.logger.error(f"Error getting balance: {e}")
            return 0

    def update_balances(self):
        """Update all tracked balances"""
        from database import Database
        db = Database()
        
        # Update ETH
        eth_balance = self.get_balance()
        db.update_balance('ETH', eth_balance)
        
        # Add other tokens as needed
        # This would require a list of token addresses
        
        balances = db.get_balances()
        total_value = 0
        for token, amount, usd_value in balances:
            if usd_value:
                total_value += amount * usd_value
        
        self.logger.info(f"Total portfolio value: ${total_value:.2f}")

    def send_transaction(self, to_address, amount, token_address=None):
        """Send transaction"""
        try:
            if token_address:
                # ERC20 transfer
                contract = self.w3.eth.contract(address=token_address, abi=self._get_erc20_abi())
                tx = contract.functions.transfer(to_address, amount).build_transaction({
                    'from': self.address,
                    'nonce': self.w3.eth.get_transaction_count(self.address),
                    'gas': 200000,
                    'gasPrice': self.w3.eth.gas_price
                })
            else:
                # ETH transfer
                tx = {
                    'to': to_address,
                    'value': self.w3.to_wei(amount, 'ether'),
                    'gas': 21000,
                    'gasPrice': self.w3.eth.gas_price,
                    'nonce': self.w3.eth.get_transaction_count(self.address)
                }
            
            signed_tx = self.w3.eth.account.sign_transaction(tx, self.private_key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            self.logger.info(f"Transaction sent: {tx_hash.hex()}")
            return tx_hash.hex()
        except Exception as e:
            self.logger.error(f"Transaction failed: {e}")
            return None

    def _get_erc20_abi(self):
        """Get ERC20 ABI"""
        return [
            {"constant": True, "inputs": [{"name": "_owner", "type": "address"}], "name": "balanceOf", "outputs": [{"name": "balance", "type": "uint256"}], "type": "function"},
            {"constant": True, "inputs": [], "name": "decimals", "outputs": [{"name": "", "type": "uint8"}], "type": "function"},
            {"constant": False, "inputs": [{"name": "_to", "type": "address"}, {"name": "_value", "type": "uint256"}], "name": "transfer", "outputs": [{"name": "", "type": "bool"}], "type": "function"}
        ]