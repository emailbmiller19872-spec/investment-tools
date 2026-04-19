import os
import logging
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from utils import random_delay, safe_click, wait_for_element, get_random_user_agent
from proxy_manager import ProxyManager
from captcha_solver import CaptchaSolver
from wallet_manager import WalletManager

class TaskAutomator:
    def __init__(self):
        self.proxy_manager = ProxyManager()
        self.captcha_solver = CaptchaSolver()
        self.wallet_manager = WalletManager()
        self.driver = None
        self.logger = logging.getLogger(__name__)

    def setup_driver(self):
        """Setup Selenium driver with anti-detection measures"""
        options = Options()
        options.add_argument("--headless") if os.getenv('HEADLESS', 'true').lower() == 'true' else None
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_argument(f'--user-agent={get_random_user_agent()}')
        
        self.proxy_manager.set_proxy_options(options)
        
        self.driver = webdriver.Chrome(options=options)
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

    def participate(self, airdrop):
        """Participate in airdrop"""
        if not self.driver:
            self.setup_driver()
        
        try:
            self.logger.info(f"Starting participation in {airdrop['title']}")
            self.driver.get(airdrop['url'])
            random_delay(3, 7)
            
            # Analyze page and complete tasks
            tasks_completed = self._complete_tasks(airdrop['url'])
            
            if tasks_completed:
                self.logger.info(f"All tasks completed for {airdrop['title']}")
                return True
            else:
                self.logger.warning(f"Some tasks failed for {airdrop['title']}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error participating in {airdrop['title']}: {e}")
            return False
        finally:
            # Rotate proxy after each airdrop
            self.proxy_manager.rotate_proxy()

    def _complete_tasks(self, url):
        """Complete common airdrop tasks"""
        tasks = [
            self._follow_social_media,
            self._join_telegram,
            self._connect_wallet,
            self._fill_form,
            self._solve_captcha,
            self._submit_entry
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
        
        return completed > 0  # At least one task completed

    def _follow_social_media(self):
        """Follow social media accounts"""
        social_buttons = self.driver.find_elements(By.XPATH, "//a[contains(@href, 'twitter.com') or contains(@href, 'x.com') or contains(@href, 'discord.gg')]")
        followed = 0
        for button in social_buttons[:3]:  # Limit to 3
            try:
                button.click()
                time.sleep(1)
                # Handle popups, but this is simplified
                followed += 1
                random_delay(1, 3)
            except:
                continue
        return followed > 0

    def _join_telegram(self):
        """Join Telegram channels"""
        telegram_links = self.driver.find_elements(By.XPATH, "//a[contains(@href, 't.me/')]")
        joined = 0
        for link in telegram_links[:2]:  # Limit to 2
            try:
                link.click()
                time.sleep(2)
                # In practice, would need Telegram API integration
                joined += 1
            except:
                continue
        return joined > 0

    def _connect_wallet(self):
        """Connect wallet to dApp"""
        connect_buttons = self.driver.find_elements(By.XPATH, "//button[contains(text(), 'Connect') or contains(text(), 'Wallet')]")
        for button in connect_buttons:
            try:
                safe_click(self.driver, button)
                time.sleep(3)
                # Handle wallet popup - this is very site-specific
                # For MetaMask, would need to interact with extension
                return self.wallet_manager.connect_wallet(self.driver, self.driver.current_url)
            except:
                continue
        return False

    def _fill_form(self):
        """Fill out forms"""
        try:
            inputs = self.driver.find_elements(By.TAG_NAME, 'input')
            for input_field in inputs:
                if input_field.is_displayed():
                    input_type = input_field.get_attribute('type')
                    if input_type == 'email':
                        input_field.send_keys('your-email@example.com')  # Use a real email service
                    elif input_type == 'text':
                        input_field.send_keys('Airdrop Participant')
                    random_delay(0.5, 1)
            return True
        except:
            return False

    def _solve_captcha(self):
        """Solve CAPTCHA if present"""
        try:
            # Check for reCAPTCHA
            recaptcha = self.driver.find_elements(By.CLASS_NAME, 'g-recaptcha')
            if recaptcha:
                site_key = recaptcha[0].get_attribute('data-sitekey')
                if site_key:
                    code = self.captcha_solver.solve_recaptcha(
                        self.driver, site_key, self.driver.current_url
                    )
                    if code:
                        # Inject the response
                        self.driver.execute_script(f"document.getElementById('g-recaptcha-response').innerHTML='{code}';")
                        return True
            
            # Check for hCaptcha
            hcaptcha = self.driver.find_elements(By.CLASS_NAME, 'h-captcha')
            if hcaptcha:
                site_key = hcaptcha[0].get_attribute('data-sitekey')
                if site_key:
                    code = self.captcha_solver.solve_hcaptcha(
                        self.driver, site_key, self.driver.current_url
                    )
                    if code:
                        self.driver.execute_script(f"document.querySelector('[name=\"h-captcha-response\"]').value='{code}';")
                        return True
                        
        except Exception as e:
            self.logger.error(f"CAPTCHA solving failed: {e}")
        return False

    def _submit_entry(self):
        """Submit the entry"""
        submit_buttons = self.driver.find_elements(By.XPATH, "//button[contains(text(), 'Submit') or contains(text(), 'Enter') or contains(text(), 'Join')]")
        for button in submit_buttons:
            try:
                safe_click(self.driver, button)
                time.sleep(2)
                return True
            except:
                continue
        return False

    def cleanup(self):
        """Clean up driver"""
        if self.driver:
            self.driver.quit()
            self.driver = None