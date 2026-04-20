import os
import logging
import time
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from utils import random_delay, safe_click, wait_for_element, get_random_user_agent
from proxy_manager import ProxyManager
from captcha_solver import CaptchaSolver

class TaskAutomator:
    def __init__(self, wallet_manager=None):
        self.proxy_manager = ProxyManager()
        self.captcha_solver = CaptchaSolver()
        self.wallet_manager = wallet_manager
        self.wallet = None
        self.driver = None
        self.logger = logging.getLogger(__name__)

    def set_wallet(self, wallet):
        self.wallet = wallet

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

        driver_path = os.getenv('DRIVER_PATH')
        chrome_version = os.getenv('CHROME_VERSION')

        if driver_path:
            self.driver = uc.Chrome(options=options, driver_executable_path=driver_path)
        elif chrome_version:
            try:
                self.driver = uc.Chrome(options=options, version_main=int(chrome_version))
            except Exception:
                self.logger.warning("Chrome version detection failed for CHROME_VERSION=%s, falling back to default undetected_chromedriver behavior", chrome_version)
                self.driver = uc.Chrome(options=options)
        else:
            try:
                self.driver = uc.Chrome(options=options, version_main=None)
            except Exception:
                self.logger.warning("Automatic Chrome driver detection failed, retrying without version_main")
                self.driver = uc.Chrome(options=options)

        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

    def participate(self, airdrop):
        """Participate in an airdrop"""
        if not self.driver:
            self.setup_driver()

        try:
            self.logger.info(f"Navigating to airdrop: {airdrop['title']}")
            self.driver.get(airdrop['url'])
            random_delay(3, 7)

            claimed = self._claim_with_definition(airdrop.get('config'))
            if not claimed:
                claimed = self._claim_airdrop()

            if claimed:
                self.logger.info(f"Participated in airdrop: {airdrop['title']}")
                return True
            else:
                self.logger.warning(f"Participation failed for airdrop: {airdrop['title']}")
                return False
        except Exception as e:
            self.logger.error(f"Error participating in airdrop {airdrop['title']}: {e}")
            return False
        finally:
            self.proxy_manager.rotate_proxy()

    def _claim_with_definition(self, config):
        if not config:
            return False

        wallet_addresses = self.wallet_manager.get_wallet_addresses() if self.wallet_manager else []
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

    def _claim_airdrop(self):
        try:
            claim_texts = ['claim', 'apply', 'join', 'submit', 'participate', 'start']
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
            self.logger.error(f"Airdrop participation failed: {e}")
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
