import os
import time
import random
import logging
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import WebDriverException, NoSuchElementException, TimeoutException
from utils import random_delay, safe_click, get_random_user_agent, load_env_bool, human_typing, human_scroll
from proxy_manager import ProxyManager
from captcha_solver import CaptchaSolver
from wallet_manager import WalletManager

class TaskAutomator:
    def __init__(self, wallet_manager=None):
        self.wallet_manager = wallet_manager or WalletManager()
        self.proxy_manager = ProxyManager()
        self.captcha_solver = CaptchaSolver()
        self.driver = None
        self.current_wallet = None
        self.logger = logging.getLogger(__name__)

    def set_wallet(self, wallet):
        self.current_wallet = wallet

    def setup_driver(self):
        if self.driver:
            return

        options = uc.ChromeOptions()
        if load_env_bool('HEADLESS', False):
            options.add_argument('--headless=new')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--disable-web-security')
        options.add_argument('--disable-features=IsolateOrigins,site-per-process')
        options.add_argument('--ignore-certificate-errors')
        options.add_argument('--disable-extensions')
        options.add_argument('--disable-infobars')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-gpu')
        options.add_argument('--enable-javascript')
        options.add_argument('--lang=en-US,en')
        options.add_argument('--window-size=1280,800')
        options.add_experimental_option('excludeSwitches', ['enable-automation'])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_experimental_option('prefs', {
            'credentials_enable_service': False,
            'profile.password_manager_enabled': False,
            'profile.default_content_setting_values.notifications': 2,
        })

        if load_env_bool('USER_AGENT_ROTATION', True):
            options.add_argument(f'--user-agent={get_random_user_agent()}')

        self.proxy_manager.set_proxy_options(options)

        self.driver = uc.Chrome(options=options)

        try:
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            self.driver.execute_script("window.navigator.chrome = {runtime: {}}")
            self.driver.execute_script("Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]})")
            self.driver.execute_script("Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']})")
        except WebDriverException:
            pass

    def participate(self, airdrop, wallet=None):
        if wallet:
            self.current_wallet = wallet

        self.setup_driver()

        try:
            title = airdrop.get('title', 'unknown airdrop')
            self.logger.info(f"Starting participation in {title}")
            self.driver.get(airdrop['url'])
            random_delay(4, 8)
            human_scroll(self.driver)

            completed = self._complete_tasks(airdrop['url'])
            if completed:
                self.logger.info(f"Completed {completed} tasks for {title}")
                return True

            self.logger.warning(f"No tasks completed for {title}")
            return False
        except Exception as e:
            self.logger.error(f"Error participating in {airdrop.get('title', airdrop.get('url'))}: {e}")
            return False
        finally:
            self.proxy_manager.rotate_proxy()
            self.cleanup()

    def _complete_tasks(self, url):
        tasks = [
            self._connect_wallet,
            self._solve_captcha,
            self._fill_form,
            self._submit_entry,
            self._follow_social_media,
            self._join_telegram,
        ]

        completed = 0
        for task in tasks:
            try:
                if task():
                    completed += 1
                    random_delay(2, 5)
                else:
                    self.logger.debug(f"Task {task.__name__} not applicable or failed")
            except Exception as e:
                self.logger.warning(f"Task {task.__name__} failed: {e}")
        return completed

    def _follow_social_media(self):
        try:
            social_buttons = self.driver.find_elements(By.XPATH, "//a[contains(@href, 'twitter.com') or contains(@href, 'x.com') or contains(@href, 'discord.gg')]")
            clicks = 0
            for button in social_buttons[:3]:
                try:
                    self._scroll_to_element(button)
                    safe_click(self.driver, button)
                    random_delay(2, 4)
                    clicks += 1
                except Exception:
                    continue
            return clicks > 0
        except Exception as e:
            self.logger.debug(f"Follow social media failed: {e}")
            return False

    def _join_telegram(self):
        try:
            telegram_links = self.driver.find_elements(By.XPATH, "//a[contains(@href, 't.me/') or contains(@href, 'telegram.me/')]")
            joined = 0
            for link in telegram_links[:2]:
                try:
                    self._scroll_to_element(link)
                    safe_click(self.driver, link)
                    random_delay(3, 5)
                    joined += 1
                except Exception:
                    continue
            return joined > 0
        except Exception as e:
            self.logger.debug(f"Join telegram failed: {e}")
            return False

    def _connect_wallet(self):
        try:
            connect_buttons = self.driver.find_elements(By.XPATH, "//button[contains(text(), 'Connect') or contains(text(), 'Wallet') or contains(@id, 'connect')]")
            for button in connect_buttons:
                try:
                    self._scroll_to_element(button)
                    safe_click(self.driver, button)
                    random_delay(3, 5)
                    return self.wallet_manager.connect_wallet(self.driver, wallet=self.current_wallet, dapp_url=self.driver.current_url)
                except Exception:
                    continue
            return False
        except Exception as e:
            self.logger.debug(f"Connect wallet failed: {e}")
            return False

    def _fill_form(self):
        try:
            email = os.getenv('USER_EMAIL', 'test@example.com')
            inputs = self.driver.find_elements(By.TAG_NAME, 'input')
            filled = 0
            for input_field in inputs:
                if not input_field.is_displayed():
                    continue
                input_type = input_field.get_attribute('type') or ''
                if input_type.lower() == 'email':
                    human_typing(input_field, email)
                    filled += 1
                elif input_type.lower() in ('text', 'search') and not input_field.get_attribute('value'):
                    human_typing(input_field, 'Airdrop Participant')
                    filled += 1
                random_delay(0.8, 1.5)
            return filled > 0
        except Exception as e:
            self.logger.debug(f"Form fill failed: {e}")
            return False

    def _solve_captcha(self):
        try:
            recaptcha = self.driver.find_elements(By.CLASS_NAME, 'g-recaptcha')
            if recaptcha:
                site_key = recaptcha[0].get_attribute('data-sitekey')
                if site_key:
                    code = self.captcha_solver.solve_recaptcha(self.driver, site_key, self.driver.current_url)
                    if code:
                        self.driver.execute_script("document.getElementById('g-recaptcha-response').innerHTML=arguments[0];", code)
                        return True

            hcaptcha = self.driver.find_elements(By.CLASS_NAME, 'h-captcha')
            if hcaptcha:
                site_key = hcaptcha[0].get_attribute('data-sitekey')
                if site_key:
                    code = self.captcha_solver.solve_hcaptcha(self.driver, site_key, self.driver.current_url)
                    if code:
                        self.driver.execute_script("document.querySelector('[name=\\\"h-captcha-response\\\"]').value=arguments[0];", code)
                        return True

            turnstile = self.driver.find_elements(By.CSS_SELECTOR, '[data-testid="cf-turnstile"]')
            if turnstile:
                site_key = turnstile[0].get_attribute('data-sitekey') or os.getenv('TURNSTILE_SITE_KEY')
                if site_key:
                    code = self.captcha_solver.solve_turnstile(site_key, self.driver.current_url)
                    return bool(code)

        except Exception as e:
            self.logger.error(f"CAPTCHA solving failed: {e}")
        return False

    def _submit_entry(self):
        try:
            submit_buttons = self.driver.find_elements(By.XPATH, "//button[contains(text(), 'Submit') or contains(text(), 'Enter') or contains(text(), 'Join') or contains(text(), 'Claim') or contains(text(), 'Continue')]")
            for button in submit_buttons:
                try:
                    self._scroll_to_element(button)
                    safe_click(self.driver, button)
                    random_delay(2, 4)
                    return True
                except Exception:
                    continue
            return False
        except Exception as e:
            self.logger.debug(f"Submit entry failed: {e}")
            return False

    def _scroll_to_element(self, element):
        try:
            self.driver.execute_script('arguments[0].scrollIntoView({behavior: "smooth", block: "center"});', element)
            human_scroll(self.driver, distance=250)
        except Exception:
            pass

    def cleanup(self):
        if self.driver:
            try:
                self.driver.quit()
            except Exception:
                pass
            self.driver = None
