import os
import logging
from free_captcha_solver import FreeCaptchaSolver

class CaptchaSolver:
    """
    Primary CAPTCHA solver - uses free methods first, optional paid fallback
    """
    def __init__(self):
        self.free_solver = FreeCaptchaSolver()
        self.paid_api_key = os.getenv('TWOCAPTCHA_API_KEY')
        self.logger = logging.getLogger(__name__)
        
        # Only try to import paid solver if key is configured
        if self.paid_api_key:
            try:
                from twocaptcha import TwoCaptcha
                self.paid_solver = TwoCaptcha(self.paid_api_key)
                self.logger.info("2Captcha configured as fallback")
            except:
                self.paid_solver = None
        else:
            self.paid_solver = None

    def solve_recaptcha(self, driver, site_key, url):
        """
        Solve reCAPTCHA v2 using free methods, fallback to paid if available
        """
        self.logger.info("Attempting to solve reCAPTCHA with FREE methods first")
        
        # Try free solver first
        result = self.free_solver.solve_recaptcha_v2(driver, site_key, url)
        if result:
            return result
        
        # Fallback to paid if configured
        if self.paid_solver:
            self.logger.info("Free methods failed, using 2Captcha fallback")
            try:
                result = self.paid_solver.recaptcha(sitekey=site_key, url=url)
                return result['code']
            except Exception as e:
                self.logger.error(f"2Captcha fallback failed: {e}")
        
        return None

    def solve_hcaptcha(self, driver, site_key, url):
        """
        Solve hCaptcha using free methods, fallback to paid if available
        """
        self.logger.info("Attempting to solve hCaptcha with FREE methods first")
        
        # Try free solver first
        result = self.free_solver.solve_hcaptcha(driver, site_key, url)
        if result:
            return result
        
        # Fallback to paid if configured
        if self.paid_solver:
            self.logger.info("Free methods failed, using 2Captcha fallback")
            try:
                result = self.paid_solver.hcaptcha(sitekey=site_key, url=url)
                return result['code']
            except Exception as e:
                self.logger.error(f"2Captcha fallback failed: {e}")
        
        return None

    def solve_image_captcha(self, image_path):
        """
        Solve image CAPTCHA using free OCR methods
        """
        return self.free_solver.solve_image_captcha(image_path)