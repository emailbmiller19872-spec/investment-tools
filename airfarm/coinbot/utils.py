import os
import logging
import random
import time
from fake_useragent import UserAgent


def setup_logging():
    """Setup logging configuration"""
    log_dir = 'logs'
    if not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)

    logging.basicConfig(
        filename=os.path.join(log_dir, 'airdrop_bot.log'),
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    formatter = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
    console.setFormatter(formatter)
    logging.getLogger('').addHandler(console)


def safe_mkdir(path):
    """Create directory if it does not exist"""
    if not path:
        return
    os.makedirs(path, exist_ok=True)


def load_env_int(name, default=0):
    try:
        return int(os.getenv(name, default))
    except (TypeError, ValueError):
        return default


def load_env_bool(name, default=False):
    value = os.getenv(name, str(default))
    return str(value).strip().lower() in ('1', 'true', 'yes', 'on')


def random_delay(min_seconds=1, max_seconds=5):
    """Add random delay to mimic human behavior"""
    delay = random.uniform(min_seconds, max_seconds)
    time.sleep(delay)


def get_random_user_agent():
    """Get a random user agent"""
    try:
        ua = UserAgent()
        return ua.random
    except Exception:
        return 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36'


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
            driver.execute_script('arguments[0].click();', element)
            return True
        except Exception:
            return False


def wait_for_element(driver, by, value, timeout=10):
    """Wait for element to be present"""
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC

    try:
        return WebDriverWait(driver, timeout).until(EC.presence_of_element_located((by, value)))
    except Exception:
        return None


def human_typing(element, text, min_delay=0.05, max_delay=0.18):
    """Type text with human-like delays"""
    for character in text:
        element.send_keys(character)
        time.sleep(random.uniform(min_delay, max_delay))


def human_scroll(driver, distance=None, duration=2.5):
    """Scroll the page in human-like steps"""
    if distance is None:
        distance = random.randint(200, 900)
    steps = random.randint(10, 18)
    step_size = int(distance / steps)
    for _ in range(steps):
        driver.execute_script(f'window.scrollBy(0, {step_size});')
        time.sleep(duration / steps)
