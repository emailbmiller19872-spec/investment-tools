import os
import logging

class ScoringEngine:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.min_score_threshold = int(os.getenv('MIN_SCORE_THRESHOLD', 50))

    def score_batch(self, airdrops):
        for a in airdrops:
            a['score'] = 100 if 'testnet' in a['url'] else 50
        return sorted(airdrops, key=lambda x: x.get('score', 0), reverse=True)

    def should_farm(self, airdrop):
        return airdrop.get('score', 0) >= self.min_score_threshold
