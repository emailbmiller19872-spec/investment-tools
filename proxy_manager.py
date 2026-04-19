import os
import random
import logging
from selenium.webdriver.chrome.options import Options

class ProxyManager:
    def __init__(self):
        self.proxies = os.getenv('PROXIES', '').split(',') if os.getenv('PROXIES') else []
        self.current_proxy = None
        self.logger = logging.getLogger(__name__)

    def get_random_proxy(self):
        """Get a random proxy from the list"""
        if not self.proxies:
            return None
        return random.choice(self.proxies).strip()

    def set_proxy_options(self, options: Options):
        """Set proxy options for Selenium"""
        proxy = self.get_random_proxy()
        if proxy:
            options.add_argument(f'--proxy-server={proxy}')
            self.current_proxy = proxy
            self.logger.info(f"Using proxy: {proxy}")
        else:
            self.logger.warning("No proxies configured")

    def rotate_proxy(self):
        """Rotate to a new proxy"""
        new_proxy = self.get_random_proxy()
        if new_proxy != self.current_proxy:
            self.current_proxy = new_proxy
            self.logger.info(f"Rotated to proxy: {new_proxy}")
        return new_proxy

    def test_proxy(self, proxy):
        """Test if proxy is working"""
        try:
            import requests
            response = requests.get('https://httpbin.org/ip', proxies={'http': proxy, 'https': proxy}, timeout=10)
            return response.status_code == 200
        except:
            return False