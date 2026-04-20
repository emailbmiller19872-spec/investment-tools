import os
import random
import logging
from selenium.webdriver.chrome.options import Options

class ProxyManager:
    def __init__(self):
        raw_proxies = os.getenv('PROXIES', '')
        self.proxies = [p.strip() for p in raw_proxies.split(',') if p.strip()]
        self.current_proxy = None
        self.logger = logging.getLogger(__name__)

    def get_random_proxy(self):
        return random.choice(self.proxies) if self.proxies else None

    def set_proxy_options(self, options: Options):
        proxy = self.get_random_proxy()
        if proxy:
            if '://' not in proxy:
                proxy = f'http://{proxy}'
            options.add_argument(f'--proxy-server={proxy}')
            self.current_proxy = proxy
            self.logger.info(f"Using proxy: {proxy}")

    def rotate_proxy(self):
        new = self.get_random_proxy()
        if new and new != self.current_proxy:
            self.current_proxy = new
            self.logger.info(f"Rotated to proxy: {new}")
        return new
