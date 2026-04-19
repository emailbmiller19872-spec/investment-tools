import json
import logging
import os

class FaucetScraper:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.definition_path = os.path.join(os.path.dirname(__file__), 'faucets.json')

    def discover_faucets(self):
        """Load faucet definitions from faucets.json"""
        if not os.path.exists(self.definition_path):
            self.logger.error(f"Faucet definition file not found: {self.definition_path}")
            return []

        try:
            with open(self.definition_path, 'r', encoding='utf-8') as f:
                definitions = json.load(f)
        except Exception as e:
            self.logger.error(f"Failed to load faucet definitions: {e}")
            return []

        faucets = []
        for name, config in definitions.items():
            faucet = {
                'name': name,
                'title': config.get('title', name.replace('_', ' ').title()),
                'url': config.get('url'),
                'config': config
            }
            if faucet['url']:
                faucets.append(faucet)
            else:
                self.logger.warning(f"Skipping faucet definition without URL: {name}")

        self.logger.info(f"Loaded {len(faucets)} faucet definitions")
        return faucets
