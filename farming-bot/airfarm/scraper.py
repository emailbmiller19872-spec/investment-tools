import requests
from bs4 import BeautifulSoup
import logging
from utils import random_delay, get_random_user_agent

class AirdropScraper:
    def __init__(self):
        self.sources = ['https://airdropalert.com/', 'https://airdrops.io/']
        self.logger = logging.getLogger(__name__)

    def discover_airdrops(self):
        airdrops = []
        for source in self.sources:
            try:
                headers = {'User-Agent': get_random_user_agent()}
                r = requests.get(source, headers=headers, timeout=30)
                soup = BeautifulSoup(r.content, 'html.parser')
                if 'airdropalert.com' in source:
                    for item in soup.find_all('div', class_='airdrop-item'):
                        link = item.find('a')
                        if link:
                            url = link.get('href')
                            if not url.startswith('http'):
                                url = f"https://airdropalert.com{url}"
                            airdrops.append({'title': link.get_text(strip=True), 'url': url, 'source': source})
                elif 'airdrops.io' in source:
                    for item in soup.find_all('div', class_='airdrop'):
                        link = item.find('a', class_='airdrop-link')
                        if link:
                            title = item.find('h3').get_text(strip=True) if item.find('h3') else 'Airdrop'
                            airdrops.append({'title': title, 'url': link['href'], 'source': source})
                random_delay(5, 10)
            except Exception as e:
                self.logger.error(f"Error scraping {source}: {e}")
        unique = []
        seen = set()
        for a in airdrops:
            if a['url'] not in seen:
                seen.add(a['url'])
                unique.append(a)
        return unique
