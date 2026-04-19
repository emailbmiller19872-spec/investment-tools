import requests
from bs4 import BeautifulSoup
import logging
import time
from utils import random_delay, get_random_user_agent

class AirdropScraper:
    def __init__(self):
        self.sources = [
            'https://airdropalert.com/',
            'https://airdrops.io/',
            'https://airdropbob.com/',
            'https://www.airdropshunter.com/',
            'https://www.cryptomoonshots.com/airdrops'
        ]
        self.logger = logging.getLogger(__name__)

    def discover_airdrops(self):
        """Scrape airdrop listings from multiple sources"""
        airdrops = []
        
        for source in self.sources:
            try:
                self.logger.info(f"Scraping {source}")
                headers = {'User-Agent': get_random_user_agent()}
                response = requests.get(source, headers=headers, timeout=30)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.content, 'html.parser')
                source_airdrops = self._parse_source(source, soup)
                airdrops.extend(source_airdrops)
                
                random_delay(5, 10)  # Delay between sources
                
            except Exception as e:
                self.logger.error(f"Error scraping {source}: {e}")
                continue
        
        # Remove duplicates
        unique_airdrops = []
        seen_urls = set()
        for airdrop in airdrops:
            if airdrop['url'] not in seen_urls:
                unique_airdrops.append(airdrop)
                seen_urls.add(airdrop['url'])
        
        self.logger.info(f"Discovered {len(unique_airdrops)} unique airdrops")
        return unique_airdrops

    def _parse_source(self, source, soup):
        """Parse airdrops from specific source"""
        airdrops = []
        
        if 'airdropalert.com' in source:
            items = soup.find_all('div', class_='airdrop-item')
            for item in items:
                link = item.find('a')
                if link:
                    title = link.get_text(strip=True)
                    url = link['href']
                    if not url.startswith('http'):
                        url = f"https://airdropalert.com{url}"
                    airdrops.append({
                        'title': title,
                        'url': url,
                        'source': source,
                        'reward': self._extract_reward(item)
                    })
        
        elif 'airdrops.io' in source:
            items = soup.find_all('div', class_='airdrop')
            for item in items:
                link = item.find('a', class_='airdrop-link')
                if link:
                    title = item.find('h3').get_text(strip=True) if item.find('h3') else 'Unknown'
                    url = link['href']
                    airdrops.append({
                        'title': title,
                        'url': url,
                        'source': source,
                        'reward': self._extract_reward(item)
                    })
        
        # Add more parsing for other sources as needed
        else:
            # Generic parsing
            links = soup.find_all('a', href=True)
            for link in links:
                href = link['href']
                if 'airdrop' in href.lower() or 'airdrop' in link.get_text().lower():
                    title = link.get_text(strip=True) or 'Airdrop'
                    if not href.startswith('http'):
                        href = f"{source.rstrip('/')}{href}"
                    airdrops.append({
                        'title': title,
                        'url': href,
                        'source': source,
                        'reward': 'Unknown'
                    })
        
        return airdrops

    def _extract_reward(self, element):
        """Extract reward information from airdrop item"""
        reward_text = ''
        reward_elements = element.find_all(text=lambda text: '$' in text or 'token' in text.lower())
        if reward_elements:
            reward_text = ' '.join(reward_elements).strip()
        return reward_text or 'Unknown'