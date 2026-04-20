import os
import logging
import random
import time
from fake_useragent import UserAgent

def setup_logging():
    """Setup logging configuration"""
    log_dir = 'logs'
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    logging.basicConfig(
        filename=os.path.join(log_dir, 'airdrop_bot.log'),
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Also log to console
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    formatter = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
    console.setFormatter(formatter)
    logging.getLogger('').addHandler(console)

def random_delay(min_seconds=1, max_seconds=5):
    """Add random delay to mimic human behavior"""
    delay = random.uniform(min_seconds, max_seconds)
    time.sleep(delay)

def get_random_user_agent():
    """Get a random user agent"""
    ua = UserAgent()
    return ua.random

def safe_click(driver, element, timeout=10):
    """Safely click an element with retry"""
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import TimeoutException, ElementClickInterceptedException
    
    try:
        WebDriverWait(driver, timeout).until(EC.element_to_be_clickable(element))
        element.click()
        return True
    except (TimeoutException, ElementClickInterceptedException):
        try:
            driver.execute_script("arguments[0].click();", element)
            return True
        except Exception:
            return False

def wait_for_element(driver, by, value, timeout=10):
    """Wait for element to be present"""
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    
    try:
        return WebDriverWait(driver, timeout).until(EC.presence_of_element_located((by, value)))
    except:
        return None
