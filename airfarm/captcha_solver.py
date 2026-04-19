import os
import time
import logging
import requests
from free_captcha_solver import FreeCaptchaSolver

class TwoCaptchaClient:
    BASE_URL = 'http://2captcha.com'

    def __init__(self, api_key):
        self.api_key = api_key
        self.session = requests.Session()

    def solve(self, method, site_key, url):
        payload = {
            'key': self.api_key,
            'method': method,
            'googlekey': site_key,
            'pageurl': url,
            'json': 1
        }
        response = self.session.post(f'{self.BASE_URL}/in.php', data=payload, timeout=30)
        response.raise_for_status()
        data = response.json()
        if data.get('status') != 1:
            raise ValueError(data)
        return self._poll_result(data['request'])

    def _poll_result(self, request_id, retries=20, interval=5):
        for _ in range(retries):
            time.sleep(interval)
            response = self.session.get(f'{self.BASE_URL}/res.php', params={
                'key': self.api_key,
                'action': 'get',
                'id': request_id,
                'json': 1
            }, timeout=30)
            response.raise_for_status()
            data = response.json()
            if data.get('status') == 1:
                return data.get('request')
            if data.get('request') != 'CAPCHA_NOT_READY':
                raise ValueError(data)
        raise TimeoutError('2Captcha solve timed out')

class CapSolverClient:
    BASE_URL = os.getenv('CAPSOLVER_ENDPOINT', 'https://api.capsolver.com')

    def __init__(self, api_key):
        self.api_key = api_key
        self.session = requests.Session()

    def create_task(self, task_type, website_url, website_key):
        payload = {
            'clientKey': self.api_key,
            'task': {
                'type': task_type,
                'websiteURL': website_url,
                'websiteKey': website_key
            }
        }
        response = self.session.post(f'{self.BASE_URL}/createTask', json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()
        if data.get('errorId') != 0:
            raise ValueError(data)
        return data['taskId']

    def get_result(self, task_id, retries=20, interval=5):
        payload = {'clientKey': self.api_key, 'taskId': task_id}
        for _ in range(retries):
            time.sleep(interval)
            response = self.session.post(f'{self.BASE_URL}/getTaskResult', json=payload, timeout=30)
            response.raise_for_status()
            data = response.json()
            if data.get('errorId') != 0:
                raise ValueError(data)
            if data.get('status') == 'ready':
                return data['solution'].get('gRecaptchaResponse') or data['solution'].get('token')
        raise TimeoutError('CapSolver solve timed out')

    def solve(self, task_type, site_key, url):
        task_id = self.create_task(task_type, url, site_key)
        return self.get_result(task_id)

class FlareSolverrClient:
    def __init__(self, endpoint):
        self.endpoint = endpoint.rstrip('/')
        self.session = requests.Session()

    def fetch_content(self, url, max_wait=60):
        payload = {
            'cmd': 'request.get',
            'url': url,
            'maxTimeout': max_wait * 1000,
            'returnOnlyCookies': False
        }
        response = self.session.post(f'{self.endpoint}/v1', json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()
        if data.get('status') != 'ok':
            raise ValueError(data)
        return data.get('solution', {}).get('response')

class CaptchaSolver:
    def __init__(self):
        self.free_solver = FreeCaptchaSolver()
        self.twocaptcha_key = os.getenv('TWOCAPTCHA_API_KEY')
        self.capsolver_key = os.getenv('CAPSOLVER_API_KEY')
        self.flaresolverr_url = os.getenv('FLARESOLVERR_URL')
        self.logger = logging.getLogger(__name__)

        self.paid_solver = None
        if self.capsolver_key:
            self.paid_solver = CapSolverClient(self.capsolver_key)
            self.logger.info('CapSolver configured as paid CAPTCHA provider')
        elif self.twocaptcha_key:
            self.paid_solver = TwoCaptchaClient(self.twocaptcha_key)
            self.logger.info('2Captcha configured as paid CAPTCHA provider')

    def solve_recaptcha(self, driver, site_key, url):
        self.logger.info('Attempting reCAPTCHA solution with fallback chain')
        result = self.free_solver.solve_recaptcha_v2(driver, site_key, url)
        if result:
            return result

        if self.paid_solver:
            self.logger.info('Using paid CAPTCHA provider for reCAPTCHA')
            if isinstance(self.paid_solver, CapSolverClient):
                return self.paid_solver.solve('RecaptchaV2TaskProxyless', site_key, url)
            return self.paid_solver.solve('userrecaptcha', site_key, url)
        return None

    def solve_hcaptcha(self, driver, site_key, url):
        self.logger.info('Attempting hCaptcha solution with fallback chain')
        result = self.free_solver.solve_hcaptcha(driver, site_key, url)
        if result:
            return result

        if self.paid_solver:
            self.logger.info('Using paid CAPTCHA provider for hCaptcha')
            if isinstance(self.paid_solver, CapSolverClient):
                return self.paid_solver.solve('HCaptchaTaskProxyless', site_key, url)
            return self.paid_solver.solve('hcaptcha', site_key, url)
        return None

    def solve_turnstile(self, site_key, url):
        self.logger.info('Attempting Turnstile solution with paid provider')
        if self.paid_solver and isinstance(self.paid_solver, CapSolverClient):
            return self.paid_solver.solve('TurnstileTaskProxyless', site_key, url)
        if self.paid_solver:
            return self.paid_solver.solve('turnstile', site_key, url)
        return None

    def solve_flare_solverr(self, url):
        if not self.flaresolverr_url:
            self.logger.warning('FlareSolverr URL not configured')
            return None
        try:
            self.logger.info('Fetching page content through FlareSolverr')
            client = FlareSolverrClient(self.flaresolverr_url)
            return client.fetch_content(url)
        except Exception as e:
            self.logger.error(f'FlareSolverr request failed: {e}')
            return None

    def solve_image_captcha(self, image_path):
        self.logger.info('Attempting image CAPTCHA solve with free methods')
        return self.free_solver.solve_image_captcha(image_path)
