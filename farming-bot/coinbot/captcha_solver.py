import os
import logging
import time
import requests
from free_captcha_solver import FreeCaptchaSolver

class CaptchaSolver:
    def __init__(self):
        self.free_solver = FreeCaptchaSolver()
        self.capsolver_key = os.getenv('CAPSOLVER_API_KEY')
        self.twocaptcha_key = os.getenv('TWOCAPTCHA_API_KEY')
        self.logger = logging.getLogger(__name__)

    def solve_recaptcha(self, driver, site_key, url):
        if self.capsolver_key:
            code = self._solve_capsolver('ReCaptchaV2TaskProxyless', site_key, url)
            if code:
                return code
        if self.twocaptcha_key:
            code = self._solve_2captcha('userrecaptcha', site_key, url)
            if code:
                return code
        return self.free_solver.solve_recaptcha_v2(driver, site_key, url)

    def solve_hcaptcha(self, driver, site_key, url):
        if self.capsolver_key:
            code = self._solve_capsolver('HCaptchaTaskProxyless', site_key, url)
            if code:
                return code
        if self.twocaptcha_key:
            code = self._solve_2captcha('hcaptcha', site_key, url)
            if code:
                return code
        return self.free_solver.solve_hcaptcha(driver, site_key, url)

    def _solve_capsolver(self, task_type, site_key, url):
        try:
            payload = {
                'clientKey': self.capsolver_key,
                'task': {'type': task_type, 'websiteURL': url, 'websiteKey': site_key}
            }
            r = requests.post('https://api.capsolver.com/createTask', json=payload, timeout=30).json()
            if r.get('errorId') != 0:
                return None
            task_id = r['taskId']
            for _ in range(30):
                time.sleep(5)
                res = requests.post('https://api.capsolver.com/getTaskResult', json={'clientKey': self.capsolver_key, 'taskId': task_id}).json()
                if res.get('status') == 'ready':
                    return res['solution'].get('gRecaptchaResponse') or res['solution'].get('token')
            return None
        except Exception:
            return None

    def _solve_2captcha(self, method, site_key, url):
        try:
            payload = {'key': self.twocaptcha_key, 'method': method, 'googlekey': site_key, 'pageurl': url, 'json': 1}
            r = requests.post('http://2captcha.com/in.php', data=payload, timeout=30).json()
            if r.get('status') != 1:
                return None
            request_id = r['request']
            for _ in range(30):
                time.sleep(5)
                res = requests.get('http://2captcha.com/res.php', params={'key': self.twocaptcha_key, 'action': 'get', 'id': request_id, 'json': 1}).json()
                if res.get('status') == 1:
                    return res['request']
            return None
        except Exception:
            return None
