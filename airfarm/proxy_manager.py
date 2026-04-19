import os
import random
import logging
from selenium.webdriver.chrome.options import Options

class ProxyManager:
    def __init__(self):
        self.proxies = self._parse_proxy_sources()
        self.current_proxy = None
        self.logger = logging.getLogger(__name__)
        self.proxy_type = os.getenv('PROXY_TYPE', 'any').lower()

    def _parse_proxy_sources(self):
        proxies = []
        raw_proxies = os.getenv('PROXIES', '')
        raw_residential = os.getenv('RESIDENTIAL_PROXIES', '')
        raw_mobile = os.getenv('MOBILE_PROXIES', '')

        for proxy in raw_proxies.split(','):
            proxy = proxy.strip()
            if proxy:
                proxies.append({'proxy': proxy, 'type': 'any'})

        for proxy in raw_residential.split(','):
            proxy = proxy.strip()
            if proxy:
                proxies.append({'proxy': proxy, 'type': 'residential'})

        for proxy in raw_mobile.split(','):
            proxy = proxy.strip()
            if proxy:
                proxies.append({'proxy': proxy, 'type': 'mobile'})

        return proxies

    def normalize_proxy(self, proxy):
        if proxy.startswith(('http://', 'https://', 'socks5://', 'socks4://')):
            return proxy
        return f'http://{proxy}'

    def get_candidates(self):
        if self.proxy_type == 'residential':
            residential = [p for p in self.proxies if p['type'] == 'residential']
            return residential or self.proxies
        if self.proxy_type == 'mobile':
            mobile = [p for p in self.proxies if p['type'] == 'mobile']
            return mobile or self.proxies
        return self.proxies

    def get_random_proxy(self):
        candidates = self.get_candidates()
        if not candidates:
            return None
        return self.normalize_proxy(random.choice(candidates)['proxy'])

    def set_proxy_options(self, options: Options):
        proxy = self.get_random_proxy()
        if proxy:
            options.add_argument(f'--proxy-server={proxy}')
            self.current_proxy = proxy
            self.logger.info(f"Using proxy: {proxy}")
        else:
            self.logger.warning('No proxies configured')

    def rotate_proxy(self):
        candidates = [self.normalize_proxy(p['proxy']) for p in self.get_candidates() if self.normalize_proxy(p['proxy']) != self.current_proxy]
        if not candidates:
            return self.current_proxy
        self.current_proxy = random.choice(candidates)
        self.logger.info(f"Rotated to proxy: {self.current_proxy}")
        return self.current_proxy

    def test_proxy(self, proxy):
        try:
            import requests
            normalized = self.normalize_proxy(proxy)
            response = requests.get('https://httpbin.org/ip', proxies={'http': normalized, 'https': normalized}, timeout=10)
            return response.status_code == 200
        except Exception:
            return False
