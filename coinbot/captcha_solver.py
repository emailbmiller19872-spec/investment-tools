import os
import logging
import time
import requests
from free_captcha_solver import FreeCaptchaSolver

class CaptchaSolver:
    """Primary CAPTCHA solver with paid solver fallback and safe request handling."""
    def __init__(self):
        self.free_solver = FreeCaptchaSolver()
        self.twocaptcha_api_key = os.getenv('TWOCAPTCHA_API_KEY')
        self.capsolver_api_key = os.getenv('CAPSOLVER_API_KEY')
        self.logger = logging.getLogger(__name__)

        if self.capsolver_api_key:
            self.logger.info("Capsolver configured for paid CAPTCHA solving")
        elif self.twocaptcha_api_key:
            self.logger.info("2Captcha configured for paid CAPTCHA solving")
        else:
            self.logger.info("No paid CAPTCHA solver configured; using free fallback")

    def solve_recaptcha(self, driver, site_key, url):
        if self.capsolver_api_key:
            code = self._solve_recaptcha_capsolver(site_key, url)
            if code:
                return code

        if self.twocaptcha_api_key:
            code = self._solve_recaptcha_2captcha(site_key, url)
            if code:
                return code

        return self.free_solver.solve_recaptcha_v2(driver, site_key, url)

    def solve_hcaptcha(self, driver, site_key, url):
        if self.capsolver_api_key:
            code = self._solve_hcaptcha_capsolver(site_key, url)
            if code:
                return code

        if self.twocaptcha_api_key:
            code = self._solve_hcaptcha_2captcha(site_key, url)
            if code:
                return code

        return self.free_solver.solve_hcaptcha(driver, site_key, url)

    def solve_image_captcha(self, image_path):
        """Solve image CAPTCHA using free OCR methods."""
        return self.free_solver.solve_image_captcha(image_path)

    def _solve_recaptcha_2captcha(self, site_key, url):
        try:
            payload = {
                'key': self.twocaptcha_api_key,
                'method': 'userrecaptcha',
                'googlekey': site_key,
                'pageurl': url,
                'json': 1
            }
            session = requests.Session()
            session.trust_env = False
            submit = session.post('http://2captcha.com/in.php', data=payload, timeout=30)
            data = submit.json()
            if data.get('status') != 1:
                self.logger.error(f"2Captcha submit failed: {data}")
                return None
            return self._poll_2captcha(data['request'])
        except Exception as e:
            self.logger.error(f"2Captcha recaptcha request failed: {e}")
            return None

    def _solve_hcaptcha_2captcha(self, site_key, url):
        try:
            payload = {
                'key': self.twocaptcha_api_key,
                'method': 'hcaptcha',
                'sitekey': site_key,
                'pageurl': url,
                'json': 1
            }
            session = requests.Session()
            session.trust_env = False
            submit = session.post('http://2captcha.com/in.php', data=payload, timeout=30)
            data = submit.json()
            if data.get('status') != 1:
                self.logger.error(f"2Captcha submit failed: {data}")
                return None
            return self._poll_2captcha(data['request'])
        except Exception as e:
            self.logger.error(f"2Captcha hcaptcha request failed: {e}")
            return None

    def _poll_2captcha(self, request_id):
        for _ in range(30):
            time.sleep(5)
            try:
                session = requests.Session()
                session.trust_env = False
                response = session.get(
                    'http://2captcha.com/res.php',
                    params={
                        'key': self.twocaptcha_api_key,
                        'action': 'get',
                        'id': request_id,
                        'json': 1
                    },
                    timeout=30
                )
                data = response.json()
                if data.get('status') == 1:
                    return data.get('request')
                if data.get('request') == 'CAPCHA_NOT_READY':
                    continue
                self.logger.error(f"2Captcha polling failed: {data}")
                return None
            except Exception as e:
                self.logger.debug(f"2Captcha polling error: {e}")
                continue
        self.logger.error("2Captcha timeout reached")
        return None

    def _solve_recaptcha_capsolver(self, site_key, url):
        try:
            payload = {
                'clientKey': self.capsolver_api_key,
                'task': {
                    'type': 'ReCaptchaV2TaskProxyless',
                    'websiteURL': url,
                    'websiteKey': site_key
                }
            }
            session = requests.Session()
            session.trust_env = False
            response = session.post('https://api.capsolver.com/createTask', json=payload, timeout=30).json()
            if response.get('errorId') != 0:
                self.logger.error(f"Capsolver submit failed: {response}")
                return None
            task_id = response.get('taskId')
            return self._poll_capsolver(task_id)
        except Exception as e:
            self.logger.error(f"Capsolver recaptcha request failed: {e}")
            return None

    def _solve_hcaptcha_capsolver(self, site_key, url):
        try:
            payload = {
                'clientKey': self.capsolver_api_key,
                'task': {
                    'type': 'HCaptchaTaskProxyless',
                    'websiteURL': url,
                    'websiteKey': site_key
                }
            }
            session = requests.Session()
            session.trust_env = False
            response = session.post('https://api.capsolver.com/createTask', json=payload, timeout=30).json()
            if response.get('errorId') != 0:
                self.logger.error(f"Capsolver submit failed: {response}")
                return None
            task_id = response.get('taskId')
            return self._poll_capsolver(task_id)
        except Exception as e:
            self.logger.error(f"Capsolver hcaptcha request failed: {e}")
            return None

    def _poll_capsolver(self, task_id):
        for _ in range(30):
            time.sleep(5)
            try:
                session = requests.Session()
                session.trust_env = False
                response = session.post(
                    'https://api.capsolver.com/getTaskResult',
                    json={'clientKey': self.capsolver_api_key, 'taskId': task_id},
                    timeout=30
                ).json()
                if response.get('errorId') != 0:
                    self.logger.error(f"Capsolver polling failed: {response}")
                    return None
                status = response.get('status')
                if status == 'processing':
                    continue
                if status == 'ready':
                    solution = response.get('solution', {})
                    return solution.get('gRecaptchaResponse') or solution.get('hCaptchaResponse') or solution.get('token')
            except Exception as e:
                self.logger.debug(f"Capsolver polling error: {e}")
                continue
        self.logger.error("Capsolver timeout reached")
        return None
