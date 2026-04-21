import os
import logging
import time
import subprocess
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from .utils import random_delay, safe_click, wait_for_element, get_random_user_agent
from .proxy_manager import ProxyManager
from .captcha_solver import CaptchaSolver
from .wallet_manager import WalletManager


def find_chrome_binary():
    """Find Chrome binary location on Windows"""
    possible_paths = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
        os.path.expandvars(r"%PROGRAMFILES%\Google\Chrome\Application\chrome.exe"),
        os.path.expandvars(r"%PROGRAMFILES(x86)%\Google\Chrome\Application\chrome.exe"),
    ]

    for path in possible_paths:
        if os.path.exists(path):
            return path

    try:
        result = subprocess.run(
            ['reg', 'query', r'HKLM\Software\Google\Chrome\BLBeacon', '/v', 'version'],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            for path in possible_paths:
                if os.path.exists(path):
                    return path
    except Exception:
        pass

    return None

class TaskAutomator:
    def __init__(self):
        self.proxy_manager = ProxyManager()
        self.captcha_solver = CaptchaSolver()
        self.wallet_manager = WalletManager()
        self.driver = None
        self.logger = logging.getLogger(__name__)

    def setup_driver(self):
        """Setup undetected Chrome driver with auto-managed WebDriver."""
        options = Options()
        if os.getenv('HEADLESS', 'true').lower() == 'true':
            options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_argument(f'--user-agent={get_random_user_agent()}')

        browser_data_dir = os.getenv('BROWSER_DATA_DIR')
        browser_profile = os.getenv('BROWSER_PROFILE')
        if browser_data_dir:
            options.add_argument(f"--user-data-dir={browser_data_dir}")
        if browser_profile:
            options.add_argument(f"--profile-directory={browser_profile}")

        self.proxy_manager.set_proxy_options(options)

        chrome_binary = find_chrome_binary()
        if chrome_binary:
            options.binary_location = chrome_binary
            self.logger.info(f"Using Chrome binary: {chrome_binary}")
        else:
            self.logger.warning("Could not find Chrome binary, using default detection")

        driver_path = os.getenv('DRIVER_PATH')
        chrome_version = os.getenv('CHROME_VERSION')

        try:
            if driver_path and os.path.exists(driver_path):
                service = Service(driver_path)
                self.driver = uc.Chrome(options=options, service=service)
            elif chrome_version:
                self.driver = uc.Chrome(options=options, version_main=int(chrome_version))
            else:
                self.driver = uc.Chrome(options=options)
        except Exception as e:
            self.logger.error(f"Failed to initialize Chrome driver: {e}")
            raise

        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

    def participate(self, faucet):
        """Claim a faucet reward"""
        if not self.driver:
            self.setup_driver()

        try:
            self.logger.info(f"Navigating to faucet: {faucet['title']}")
            self.driver.get(faucet['url'])
            random_delay(3, 7)

            claimed = self._claim_with_definition(faucet.get('config'))
            if not claimed:
                claimed = self._claim_faucet()

            if claimed:
                self.logger.info(f"Claimed faucet: {faucet['title']}")
                return True
            else:
                self.logger.warning(f"Claim failed for faucet: {faucet['title']}")
                return False
        except Exception as e:
            self.logger.error(f"Error claiming faucet {faucet['title']}: {e}")
            return False
        finally:
            self.proxy_manager.rotate_proxy()

    def _claim_with_definition(self, config):
        if not config:
            return False

        wallet_addresses = self.wallet_manager.get_wallet_addresses()
        wallet_address = wallet_addresses[0] if wallet_addresses else None

        if config.get('wallet_address_field') and wallet_address:
            if not self._fill_wallet_field(config['wallet_address_field'], wallet_address):
                return False

        if config.get('checkbox'):
            self._click_selector(config['checkbox'])

        if config.get('connect_wallet_button'):
            self._click_selector(config['connect_wallet_button'])
            random_delay(2, 4)

        if self._solve_captcha():
            random_delay(1, 3)

        if config.get('submit_button'):
            if not self._click_selector(config['submit_button']):
                return False

        self._close_ads(config.get('close_ad_button'))

        if config.get('success_message_html'):
            element = self._find_element(config['success_message_html'])
            return element is not None

        return True

    def _fill_wallet_field(self, selector, address):
        element = self._find_element(selector)
        if not element:
            self.logger.warning(f"Wallet field not found for selector {selector}")
            return False
        try:
            element.clear()
            element.send_keys(address)
            return True
        except Exception as e:
            self.logger.error(f"Failed to fill wallet field: {e}")
            return False

    def _find_element(self, selector):
        if not selector:
            return None
        try:
            if selector.startswith('xpath:'):
                return self.driver.find_element(By.XPATH, selector.split('xpath:', 1)[1])
            return self.driver.find_element(By.CSS_SELECTOR, selector)
        except NoSuchElementException:
            return None
        except Exception as e:
            self.logger.debug(f"Element lookup failed for {selector}: {e}")
            return None

    def _click_selector(self, selector):
        element = self._find_element(selector)
        if not element:
            self.logger.debug(f"Click selector not found: {selector}")
            return False
        return safe_click(self.driver, element)

    def _close_ads(self, selector):
        if not selector:
            return False
        for _ in range(int(os.getenv('CLOSE_AD_ATTEMPTS', 1))):
            if self._click_selector(selector):
                return True
            time.sleep(int(os.getenv('CLOSE_AD_RETRY_DELAY', 5)))
        return False

    def _claim_faucet(self):
        try:
            claim_texts = ['claim', 'roll', 'get reward', 'collect', 'submit', 'tap to claim']
            buttons = []
            for text in claim_texts:
                buttons.extend(self.driver.find_elements(By.XPATH, f"//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{text}')]") )
                buttons.extend(self.driver.find_elements(By.XPATH, f"//a[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{text}')]") )

            for button in buttons:
                try:
                    if safe_click(self.driver, button):
                        random_delay(2, 5)
                        self._solve_captcha()
                        return True
                except Exception:
                    continue

            forms = self.driver.find_elements(By.TAG_NAME, 'form')
            for form in forms:
                try:
                    form.submit()
                    random_delay(2, 4)
                    return True
                except Exception:
                    continue
        except Exception as e:
            self.logger.error(f"Claim faucet failed: {e}")
        return False

    def _solve_captcha(self):
        try:
            recaptcha = self.driver.find_elements(By.CLASS_NAME, 'g-recaptcha')
            if recaptcha:
                site_key = recaptcha[0].get_attribute('data-sitekey')
                if site_key:
                    code = self.captcha_solver.solve_recaptcha(self.driver, site_key, self.driver.current_url)
                    if code:
                        self.driver.execute_script(f"document.getElementById('g-recaptcha-response').innerHTML='{code}';")
                        return True

            hcaptcha = self.driver.find_elements(By.CLASS_NAME, 'h-captcha')
            if hcaptcha:
                site_key = hcaptcha[0].get_attribute('data-sitekey')
                if site_key:
                    code = self.captcha_solver.solve_hcaptcha(self.driver, site_key, self.driver.current_url)
                    if code:
                        self.driver.execute_script(f"document.querySelector('[name=\"h-captcha-response\"]').value='{code}';")
                        return True
        except Exception as e:
            self.logger.error(f"CAPTCHA solving failed: {e}")
        return False

    def cleanup(self):
        if self.driver:
            self.driver.quit()
            self.driver = None
