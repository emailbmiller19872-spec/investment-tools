import os
import logging
import pytesseract
from PIL import Image
from utils import random_delay

class FreeCaptchaSolver:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.use_ocr = False
        try:
            pytesseract.pytesseract.tesseract_cmd = os.getenv('TESSERACT_PATH', 'tesseract')
            pytesseract.get_tesseract_version()
            self.use_ocr = True
        except Exception:
            pass

    def solve_recaptcha_v2(self, driver, site_key, url):
        self.logger.info("Free reCAPTCHA solving not implemented, returning None")
        return None

    def solve_hcaptcha(self, driver, site_key, url):
        self.logger.info("Free hCaptcha solving not implemented, returning None")
        return None
