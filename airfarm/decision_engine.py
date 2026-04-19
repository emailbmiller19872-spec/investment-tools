import os
import logging
import requests
from datetime import datetime
from bs4 import BeautifulSoup

class ScoringEngine:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.weights = {
            'protocol_fundamentals': 25,
            'tokenomics_community': 20,
            'team_backers': 20,
            'eligibility_sybil': 15,
            'community_sentiment': 10,
            'onchain_difficulty': 10
        }
        self.min_score_threshold = int(os.getenv('MIN_SCORE_THRESHOLD', 50))

    def score_batch(self, airdrops):
        """Score a batch of airdrops and return sorted list"""
        scored = []
        for airdrop in airdrops:
            try:
                score_data = self._calculate_score(airdrop)
                airdrop['score'] = score_data['total_score']
                airdrop['score_breakdown'] = score_data
                scored.append(airdrop)
            except Exception as e:
                self.logger.warning(f"Failed to score airdrop {airdrop.get('title')}: {e}")
                airdrop['score'] = 0
                scored.append(airdrop)
        return sorted(scored, key=lambda x: x.get('score', 0), reverse=True)

    def _calculate_score(self, airdrop):
        """Calculate comprehensive score for an airdrop"""
        url = airdrop.get('url', '').lower()
        title = airdrop.get('title', '').lower()
        description = airdrop.get('description', '').lower()

        scores = {
            'protocol_fundamentals': self._score_protocol_fundamentals(url, title, description),
            'tokenomics_community': self._score_tokenomics_community(url, title, description),
            'team_backers': self._score_team_backers(url, title, description),
            'eligibility_sybil': self._score_eligibility_sybil(url, title, description),
            'community_sentiment': self._score_community_sentiment(url, title, description),
            'onchain_difficulty': self._score_onchain_difficulty(url, title, description)
        }

        total_score = sum(scores.values())
        scores['total_score'] = total_score

        return scores

    def _score_protocol_fundamentals(self, url, title, description):
        """Score based on protocol fundamentals and narrative"""
        score = 0
        trending_sectors = ['depin', 'rwa', 'modular', 'layer2', 'defi', 'ai', 'privacy']
        for sector in trending_sectors:
            if sector in title or sector in description or sector in url:
                score += 10
                break

        # Category leaders bonus
        leaders = ['scroll', 'zksync', 'polygon', 'arbitrum', 'optimism']
        for leader in leaders:
            if leader in url:
                score += 15
                break

        return min(score, self.weights['protocol_fundamentals'])

    def _score_tokenomics_community(self, url, title, description):
        """Score based on tokenomics and community allocation"""
        score = 0
        # Look for community allocation indicators
        community_keywords = ['community', 'airdrop', 'allocation', '10%', '15%', '20%']
        for keyword in community_keywords:
            if keyword in description:
                score += 10
                break

        # Testnet bonus (often indicates fair distribution)
        if 'testnet' in url or 'testnet' in title:
            score += 10

        return min(score, self.weights['tokenomics_community'])

    def _score_team_backers(self, url, title, description):
        """Score based on team, backers and ecosystem"""
        score = 0
        # Known VCs and backers
        vc_keywords = ['a16z', 'paradigm', 'sequoia', 'andreessen', 'horowitz', 'binance', 'coinbase']
        for vc in vc_keywords:
            if vc in description:
                score += 15
                break

        # Team doxxing indicators
        team_keywords = ['team', 'founder', 'linkedin', 'github']
        for keyword in team_keywords:
            if keyword in description:
                score += 5

        return min(score, self.weights['team_backers'])

    def _score_eligibility_sybil(self, url, title, description):
        """Score based on eligibility criteria and sybil resistance"""
        score = 0
        # Fair eligibility indicators
        fair_keywords = ['no kyc', 'fair', 'equal', 'everyone', 'participate']
        for keyword in fair_keywords:
            if keyword in description:
                score += 10

        # Sybil resistance (good sign)
        sybil_keywords = ['sybil', 'resistance', 'unique', 'one per']
        for keyword in sybil_keywords:
            if keyword in description:
                score += 5

        return min(score, self.weights['eligibility_sybil'])

    def _score_community_sentiment(self, url, title, description):
        """Score based on community sentiment and market demand"""
        score = 0
        # Social media presence
        social_keywords = ['twitter', 'discord', 'telegram', 'community']
        for keyword in social_keywords:
            if keyword in description:
                score += 5

        # Engagement indicators
        engagement_keywords = ['active', 'growing', 'popular', 'trending']
        for keyword in engagement_keywords:
            if keyword in description:
                score += 5

        return min(score, self.weights['community_sentiment'])

    def _score_onchain_difficulty(self, url, title, description):
        """Score based on on-chain activity and task difficulty"""
        score = 0
        # Easy tasks (higher score for accessibility)
        easy_keywords = ['connect wallet', 'follow', 'join', 'simple']
        for keyword in easy_keywords:
            if keyword in description:
                score += 8

        # Moderate complexity (good balance)
        moderate_keywords = ['bridge', 'swap', 'stake', 'lend']
        for keyword in moderate_keywords:
            if keyword in description:
                score += 5

        # High difficulty penalty (lower score)
        hard_keywords = ['complex', 'advanced', 'expert', 'capital required']
        for keyword in hard_keywords:
            if keyword in description:
                score -= 5

        return max(0, min(score, self.weights['onchain_difficulty']))

    def should_farm(self, airdrop):
        """Determine if an airdrop should be farmed based on score"""
        return airdrop.get('score', 0) >= self.min_score_threshold

    def get_high_potential_targets(self):
        """Return list of known high-potential testnets for 2026"""
        return [
            {
                'name': 'Canopy Network',
                'symbol': 'CNPY',
                'url': 'https://canopynetwork.com',
                'description': 'Appchain testnet with confirmed token airdrop and rewards hub'
            },
            {
                'name': 'Settlr',
                'symbol': 'STLR',
                'url': 'https://settlr.io',
                'description': 'Risk-free paper trading on Hyperliquid testnet, 900M tokens allocated'
            },
            {
                'name': 'Pharos Network',
                'symbol': 'PHRS',
                'url': 'https://pharos.network',
                'description': 'On-chain quests testnet with DEX swaps and RWA lending'
            },
            {
                'name': 'DataHaven',
                'symbol': 'HAVE',
                'url': 'https://datahaven.io',
                'description': 'Confirmed tokenomics and airdrop, simple testnet activities'
            },
            {
                'name': 'Zama',
                'symbol': 'ZAMA',
                'url': 'https://zama.ai',
                'description': 'FHE testnet for privacy-preserving AI and machine intelligence'
            }
        ]