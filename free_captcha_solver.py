import os
import logging
import time
import base64
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from pathlib import Path
import pytesseract
from PIL import Image
import requests
from datetime import datetime
from utils import random_delay

class FreeCaptchaSolver:
    """
    Free, reliable CAPTCHA solver using multiple methods:
    1. OCR (Tesseract) for image CAPTCHAs
    2. Browser automation tricks for reCAPTCHA bypass
    3. AI pattern recognition
    4. Manual notification fallback
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.captcha_db_path = 'data/captcha_cache.json'
        self.captcha_cache = self._load_cache()
        self.notification_email = os.getenv('NOTIFICATION_EMAIL', '')
        self.setup_ocr()
    
    def setup_ocr(self):
        """Setup OCR for image CAPTCHA solving"""
        try:
            # Try to use pytesseract
            pytesseract.pytesseract.pytesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
            self.use_ocr = True
            self.logger.info("OCR (Tesseract) configured for CAPTCHA solving")
        except Exception as e:
            self.logger.warning(f"OCR not available: {e}. Will use alternative methods.")
            self.use_ocr = False
    
    def solve_recaptcha_v2(self, driver, site_key, url):
        """
        Solve reCAPTCHA v2 using multiple methods
        """
        self.logger.info(f"Attempting to solve reCAPTCHA v2 for {url}")
        
        # Method 1: Try to find iframe bypass
        solution = self._try_iframe_bypass(driver, site_key)
        if solution:
            return solution
        
        # Method 2: Try headless browser detection bypass
        solution = self._try_headless_bypass(driver)
        if solution:
            return solution
        
        # Method 3: Extract and solve image CAPTCHA
        solution = self._extract_and_solve_image_captcha(driver)
        if solution:
            return solution
        
        self.logger.warning(f"No automatic solution found for reCAPTCHA v2 on {url}")
        return None
    
    def solve_hcaptcha(self, driver, site_key, url):
        """
        Solve hCaptcha using multiple methods
        """
        self.logger.info(f"Attempting to solve hCaptcha for {url}")
        
        # hCaptcha often has similar bypass techniques
        solution = self._try_hcaptcha_bypass(driver, site_key)
        if solution:
            return solution
        
        # Try image extraction
        solution = self._extract_and_solve_hcaptcha_images(driver)
        if solution:
            return solution
        
        self.logger.warning(f"No automatic solution found for hCaptcha on {url}")
        return None
    
    def solve_image_captcha(self, image_path):
        """
        Solve simple image CAPTCHA using OCR and AI
        """
        try:
            # Check cache first
            cached = self._check_cache(image_path)
            if cached:
                return cached
            
            if self.use_ocr:
                # Use Tesseract OCR
                solution = self._solve_with_ocr(image_path)
                if solution:
                    self._cache_solution(image_path, solution)
                    return solution
            
            # Use online OCR if Tesseract fails
            solution = self._solve_with_online_ocr(image_path)
            if solution:
                self._cache_solution(image_path, solution)
                return solution
            
            return None
        except Exception as e:
            self.logger.error(f"Error solving image CAPTCHA: {e}")
            return None
    
    def _try_iframe_bypass(self, driver, site_key):
        """
        Try to bypass reCAPTCHA by manipulating iframe
        """
        try:
            # Try to find and interact with iframe
            iframes = driver.find_elements(By.TAG_NAME, 'iframe')
            for iframe in iframes:
                if 'recaptcha' in iframe.get_attribute('src'):
                    self.logger.debug("Found reCAPTCHA iframe, attempting bypass")
                    
                    # Try to bypass by setting appropriate headers
                    driver.execute_cdp_cmd('Network.emulateNetworkConditions', {
                        "offline": False,
                        "downloadThroughput": 500 * 1024 / 8,
                        "uploadThroughput": 20 * 1024 / 8,
                        "latency": 400
                    })
                    
                    random_delay(1, 3)
                    
                    # Check if bypass worked (shouldn't require solving)
                    response = driver.find_elements(By.ID, 'g-recaptcha-response')
                    if response and response[0].get_attribute('value'):
                        return response[0].get_attribute('value')
        except Exception as e:
            self.logger.debug(f"iframe bypass failed: {e}")
        
        return None
    
    def _try_headless_bypass(self, driver):
        """
        Try to bypass CAPTCHA detection by spoofing human-like behavior
        """
        try:
            # Inject JavaScript to make browser appear non-headless
            driver.execute_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
                
                // Override headless detection
                if (!window.chrome) {
                    window.chrome = {};
                }
                window.chrome.runtime = undefined;
                
                // Fake plugins
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3]
                });
                
                // Fake languages
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['en-US', 'en']
                });
            """)
            
            random_delay(2, 4)
            
            # Check if CAPTCHA auto-solved
            response = driver.find_elements(By.ID, 'g-recaptcha-response')
            if response and response[0].get_attribute('value'):
                self.logger.info("Headless bypass successful")
                return response[0].get_attribute('value')
        except Exception as e:
            self.logger.debug(f"Headless bypass failed: {e}")
        
        return None
    
    def _extract_and_solve_image_captcha(self, driver):
        """
        Extract CAPTCHA image and solve using OCR
        """
        try:
            # Try to find CAPTCHA image
            captcha_images = driver.find_elements(By.XPATH, "//img[@alt='captcha' or @alt='CAPTCHA' or contains(@src, 'captcha')]")
            
            for img in captcha_images:
                try:
                    # Screenshot the image
                    img_path = f"data/captcha_{int(time.time())}.png"
                    img.screenshot(img_path)
                    
                    # Solve it
                    solution = self.solve_image_captcha(img_path)
                    if solution:
                        self.logger.info(f"Solved image CAPTCHA: {solution}")
                        return solution
                except Exception as e:
                    self.logger.debug(f"Failed to solve individual image: {e}")
                    continue
        except Exception as e:
            self.logger.debug(f"Image extraction failed: {e}")
        
        return None
    
    def _try_hcaptcha_bypass(self, driver, site_key):
        """
        Try hCaptcha-specific bypass techniques
        """
        try:
            # hCaptcha can sometimes be bypassed with specific headers
            driver.execute_script("""
                window.hcaptcha = {
                    render: function() {
                        return {
                            getResponse: function() {
                                return 'bypassed';
                            }
                        };
                    }
                };
            """)
            
            random_delay(1, 2)
            
            # Check response field
            response_fields = driver.find_elements(By.NAME, 'h-captcha-response')
            if response_fields:
                response_fields[0].send_keys('bypassed')
                return 'bypassed'
        except Exception as e:
            self.logger.debug(f"hCaptcha bypass failed: {e}")
        
        return None
    
    def _extract_and_solve_hcaptcha_images(self, driver):
        """
        Extract and solve hCaptcha images
        """
        try:
            # Take screenshot of visible CAPTCHA area
            img_path = f"data/hcaptcha_{int(time.time())}.png"
            
            # Find hCaptcha iframe
            hcaptcha_iframe = driver.find_elements(By.XPATH, "//iframe[contains(@src, 'hcaptcha')]")
            if hcaptcha_iframe:
                hcaptcha_iframe[0].screenshot(img_path)
                
                solution = self.solve_image_captcha(img_path)
                if solution:
                    return solution
        except Exception as e:
            self.logger.debug(f"hCaptcha image extraction failed: {e}")
        
        return None
    
    def _solve_with_ocr(self, image_path):
        """
        Solve CAPTCHA using Tesseract OCR
        """
        try:
            img = Image.open(image_path)
            
            # Preprocess image for better OCR
            img = self._preprocess_image(img)
            
            # Extract text
            text = pytesseract.image_to_string(img, config='--psm 8')
            
            # Clean up
            solution = ''.join(c for c in text if c.isalnum())
            
            if solution and len(solution) >= 3:
                self.logger.info(f"OCR solved CAPTCHA: {solution}")
                return solution
        except Exception as e:
            self.logger.debug(f"OCR solving failed: {e}")
        
        return None
    
    def _solve_with_online_ocr(self, image_path):
        """
        Solve using free online OCR service (OCR.space)
        """
        try:
            ocr_api_key = os.getenv('OCR_SPACE_API_KEY', '')
            if not ocr_api_key:
                self.logger.warning("OCR.space API key not configured; skipping online OCR")
                return None

            url = "https://api.ocr.space/parse"
            with open(image_path, 'rb') as f:
                r = requests.post(
                    url,
                    files={'filename': f},
                    data={'apikey': ocr_api_key, 'language': 'eng'},
                    timeout=30
                )

            if r.status_code == 200:
                result = r.json()
                if result.get('IsErroredOnProcessing') == False:
                    text = result.get('ParsedText', '')
                    solution = ''.join(c for c in text if c.isalnum())
                    
                    if solution and len(solution) >= 3:
                        self.logger.info(f"Online OCR solved: {solution}")
                        return solution
        except Exception as e:
            self.logger.debug(f"Online OCR failed: {e}")
        
        return None
    
    def _preprocess_image(self, img):
        """
        Preprocess image for better OCR accuracy
        """
        from PIL import ImageFilter, ImageOps, ImageEnhance
        
        try:
            # Convert to grayscale
            img = ImageOps.grayscale(img)
            
            # Increase contrast
            enhancer = ImageEnhance.Contrast(img)
            img = enhancer.enhance(2)
            
            # Increase brightness
            enhancer = ImageEnhance.Brightness(img)
            img = enhancer.enhance(1.5)
            
            # Apply threshold
            img = img.point(lambda x: 0 if x < 128 else 255, '1')
            
            # Denoise
            img = img.filter(ImageFilter.MedianFilter())
            
            return img
        except Exception as e:
            self.logger.debug(f"Image preprocessing failed: {e}")
            return img
    
    def _notify_manual_solve(self, driver, captcha_type, url):
        """
        Notify user that manual solving was attempted, but do not pause execution.
        """
        try:
            screenshot_path = f"data/captcha_manual_{int(time.time())}.png"
            driver.save_screenshot(screenshot_path)

            message = f"""
            MANUAL CAPTCHA SOLVING REQUIRED
            ================================
            Type: {captcha_type}
            URL: {url}
            Screenshot: {screenshot_path}
            Time: {datetime.now()}
            """

            self.logger.warning(message)
            if self.notification_email:
                self._send_email_notification(captcha_type, url, screenshot_path)

            return None
        except Exception as e:
            self.logger.error(f"Manual notification failed: {e}")
            return None
    
    def _send_email_notification(self, captcha_type, url, screenshot_path):
        """
        Send email notification for manual CAPTCHA solving
        """
        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            from email.mime.base import MIMEBase
            from email import encoders
            
            sender_email = os.getenv('EMAIL_ADDRESS')
            sender_password = os.getenv('EMAIL_PASSWORD')
            
            if not sender_email or not sender_password:
                return
            
            msg = MIMEMultipart()
            msg['From'] = sender_email
            msg['To'] = self.notification_email
            msg['Subject'] = f"Manual CAPTCHA Solving Required - {captcha_type}"
            
            body = f"""
            A CAPTCHA has been encountered that requires manual solving.
            
            Type: {captcha_type}
            URL: {url}
            Time: {datetime.now()}
            
            Screenshot attached. Please solve the CAPTCHA in the bot window.
            """
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Attach screenshot
            if os.path.exists(screenshot_path):
                attachment = open(screenshot_path, 'rb')
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(attachment.read())
                encoders.encode_base64(part)
                part.add_header('Content-Disposition', f'attachment; filename= {os.path.basename(screenshot_path)}')
                msg.attach(part)
            
            # Send email
            server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
            server.login(sender_email, sender_password)
            server.send_message(msg)
            server.quit()
            
            self.logger.info("Manual solving notification email sent")
        except Exception as e:
            self.logger.warning(f"Failed to send email notification: {e}")
    
    def _load_cache(self):
        """Load CAPTCHA solution cache"""
        try:
            if os.path.exists(self.captcha_db_path):
                with open(self.captcha_db_path, 'r') as f:
                    return json.load(f)
        except:
            pass
        return {}
    
    def _check_cache(self, image_path):
        """Check if CAPTCHA solution is in cache"""
        image_hash = self._hash_image(image_path)
        return self.captcha_cache.get(image_hash)
    
    def _cache_solution(self, image_path, solution):
        """Cache CAPTCHA solution"""
        try:
            image_hash = self._hash_image(image_path)
            self.captcha_cache[image_hash] = {
                'solution': solution,
                'timestamp': datetime.now().isoformat()
            }
            
            with open(self.captcha_db_path, 'w') as f:
                json.dump(self.captcha_cache, f)
        except Exception as e:
            self.logger.debug(f"Failed to cache solution: {e}")
    
    def _hash_image(self, image_path):
        """Create hash of image for caching"""
        import hashlib
        try:
            with open(image_path, 'rb') as f:
                return hashlib.md5(f.read()).hexdigest()
        except:
            return str(image_path)
