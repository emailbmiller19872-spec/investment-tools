import os
import random
import logging
import tempfile
import zipfile
import urllib.parse
from selenium.webdriver.chrome.options import Options

try:
    from selenium_authenticated_proxy import authenticated_proxy
except ImportError:
    authenticated_proxy = None

class ProxyManager:
    def __init__(self):
        raw_proxies = os.getenv('PROXIES', '')
        self.proxies = [proxy.strip() for proxy in raw_proxies.split(',') if proxy.strip()]
        self.current_proxy = None
        self.logger = logging.getLogger(__name__)

    def get_random_proxy(self):
        if not self.proxies:
            self.logger.warning("No proxies configured")
            return None
        return random.choice(self.proxies)

    def set_proxy_options(self, options: Options):
        proxy = self.get_random_proxy()
        if not proxy:
            return None

        proxy = self._normalize_proxy_string(proxy)
        self.current_proxy = proxy

        if authenticated_proxy and '@' in proxy:
            try:
                authenticated_proxy(options, proxy)
                self.logger.info(f"Using authenticated proxy via selenium_authenticated_proxy: {proxy}")
                return proxy
            except Exception as e:
                self.logger.warning(f"Authenticated proxy helper failed: {e}")

        if '@' in proxy:
            try:
                extension_path = self._create_proxy_auth_extension(proxy)
                options.add_extension(extension_path)
                self.logger.info(f"Using proxy auth extension for: {proxy}")
            except Exception as e:
                self.logger.warning(f"Proxy auth extension failed: {e}")
                options.add_argument(f'--proxy-server={proxy}')
                self.logger.info(f"Falling back to proxy-server argument for: {proxy}")
        else:
            options.add_argument(f'--proxy-server={proxy}')
            self.logger.info(f"Using proxy: {proxy}")

        return proxy

    def rotate_proxy(self):
        new_proxy = self.get_random_proxy()
        if new_proxy != self.current_proxy:
            self.current_proxy = new_proxy
            self.logger.info(f"Rotated to proxy: {new_proxy}")
        return new_proxy

    def _normalize_proxy_string(self, proxy):
        if '://' not in proxy:
            proxy = f'http://{proxy}'
        return proxy

    def _create_proxy_auth_extension(self, proxy):
        parsed = urllib.parse.urlparse(proxy)
        scheme = parsed.scheme or 'http'
        username = urllib.parse.unquote(parsed.username or '')
        password = urllib.parse.unquote(parsed.password or '')
        host = parsed.hostname
        port = parsed.port

        if not host or not port or not username or not password:
            raise ValueError('Authenticated proxy must include user, pass, host, and port')

        manifest = {
            'version': '1.0.0',
            'manifest_version': 2,
            'name': 'Proxy Auth Extension',
            'permissions': [
                'proxy',
                'tabs',
                'webRequest',
                'webRequestBlocking',
                'storage',
                '<all_urls>'
            ],
            'background': {
                'scripts': ['background.js']
            }
        }

        background = f"""
chrome.proxy.settings.set({{
  value: {{
    mode: 'fixed_servers',
    rules: {{
      singleProxy: {{
        scheme: '{scheme}',
        host: '{host}',
        port: {port}
      }}
    }}
  }},
  scope: 'regular'
}}, function() {{}});

chrome.webRequest.onAuthRequired.addListener(
  function(details, callback) {{
    callback({{authCredentials: {{username: '{username}', password: '{password}'}}}});
  }},
  {{urls: ['<all_urls>']}},
  ['blocking']
);
"""

        tmpdir = tempfile.mkdtemp(prefix='proxy_auth_ext_')
        manifest_path = os.path.join(tmpdir, 'manifest.json')
        background_path = os.path.join(tmpdir, 'background.js')

        with open(manifest_path, 'w', encoding='utf-8') as f:
            json.dump(manifest, f)
        with open(background_path, 'w', encoding='utf-8') as f:
            f.write(background)

        archive_path = os.path.join(tmpdir, 'proxy_auth_extension.zip')
        with zipfile.ZipFile(archive_path, 'w') as z:
            z.write(manifest_path, 'manifest.json')
            z.write(background_path, 'background.js')

        return archive_path

    def test_proxy(self, proxy):
        """Test if proxy is working"""
        try:
            import requests
            response = requests.get('https://httpbin.org/ip', proxies={'http': proxy, 'https': proxy}, timeout=10)
            return response.status_code == 200
        except:
            return False