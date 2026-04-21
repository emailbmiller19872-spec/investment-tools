import os
import time
import logging
import threading
from datetime import datetime
from dotenv import load_dotenv
import schedule
from flask import Flask, jsonify
from scraper import FaucetScraper
from task_automator import TaskAutomator
from wallet_manager import WalletManager
from consolidation import ConsolidationEngine
from database import Database
from utils import setup_logging, random_delay

load_dotenv()
setup_logging()

# Flask app for health checks (keeps Render service alive)
app = Flask(__name__)

class BotState:
    def __init__(self):
        self.last_run = None
        self.claims_today = 0
        self.total_claims = 0
        self.status = "starting"
        self.errors = []

bot_state = BotState()

@app.route('/healthz')
def health_check():
    """Render health check endpoint"""
    return jsonify({
        "status": "healthy",
        "bot_status": bot_state.status,
        "last_run": bot_state.last_run,
        "claims_today": bot_state.claims_today,
        "total_claims": bot_state.total_claims,
        "timestamp": datetime.now().isoformat()
    }), 200

@app.route('/')
def root():
    """Root endpoint with bot status"""
    return jsonify({
        "service": "Coinbot Faucet Collector",
        "status": bot_state.status,
        "version": "1.0.0",
        "endpoints": {
            "health": "/healthz",
            "status": "/status"
        }
    })

@app.route('/status')
def status():
    """Detailed status endpoint"""
    return jsonify({
        "status": bot_state.status,
        "last_run": bot_state.last_run,
        "claims_today": bot_state.claims_today,
        "total_claims": bot_state.total_claims,
        "recent_errors": bot_state.errors[-5:] if bot_state.errors else []
    })

def run_flask():
    """Run Flask in background thread"""
    port = int(os.getenv('PORT', 8080))
    app.run(host='0.0.0.0', port=port, threaded=True)

class AutonomousFaucetBot:
    def __init__(self):
        self.scraper = FaucetScraper()
        self.automator = TaskAutomator()
        self.wallet = WalletManager()
        self.consolidator = ConsolidationEngine(self.wallet)
        self.db = Database()
        self.logger = logging.getLogger(__name__)
        self.claims_today = 0
        self.last_date = datetime.now().date()

    def reset_daily_counter(self):
        """Reset daily claim counter"""
        today = datetime.now().date()
        if today != self.last_date:
            self.claims_today = 0
            self.last_date = today
            bot_state.claims_today = 0

    def run_cycle(self):
        bot_state.status = "running"
        bot_state.last_run = datetime.now().isoformat()
        self.reset_daily_counter()

        try:
            self.logger.info("Starting faucet claim cycle")
            faucets = self.scraper.discover_faucets()
            cycle_claims = 0

            for faucet in faucets:
                if self.db.is_participated(faucet['url']):
                    continue
                self.logger.info(f"Processing faucet: {faucet['title']}")
                success = self.automator.participate(faucet)
                if success:
                    self.db.mark_participated(faucet['url'])
                    self.claims_today += 1
                    cycle_claims += 1
                    bot_state.claims_today = self.claims_today
                    bot_state.total_claims += 1
                    self.logger.info(f"Successfully claimed faucet: {faucet['title']}")
                else:
                    self.logger.warning(f"Failed to claim faucet: {faucet['title']}")
                random_delay(30, 60)

            self.wallet.update_balances()
            self.consolidator.run_consolidation_cycle()
            self.logger.info(f"Cycle completed. Claims this cycle: {cycle_claims}")
            bot_state.status = "idle"

        except Exception as e:
            error_msg = f"Error in run_cycle: {e}"
            self.logger.error(error_msg)
            bot_state.errors.append(f"{datetime.now().isoformat()}: {error_msg}")
            bot_state.status = "error"
            time.sleep(300)

    def start(self):
        self.logger.info("Starting Autonomous Faucet Collector")
        bot_state.status = "starting"

        # Run first cycle immediately
        self.run_cycle()

        # Schedule regular cycles
        interval_hours = int(os.getenv('CLAIM_INTERVAL_HOURS', 1))
        schedule.every(interval_hours).hours.do(self.run_cycle)
        self.logger.info(f"Scheduled cycles every {interval_hours} hours")

        consolidation_interval = int(os.getenv('CONSOLIDATION_INTERVAL_MINUTES', 0))
        if consolidation_interval > 0:
            schedule.every(consolidation_interval).minutes.do(self.consolidator.run_consolidation_cycle)
            self.logger.info(f"Scheduled consolidation every {consolidation_interval} minutes")

        bot_state.status = "idle"

        try:
            while True:
                schedule.run_pending()
                time.sleep(60)
        except KeyboardInterrupt:
            self.logger.info("Shutting down")
            bot_state.status = "stopped"

if __name__ == "__main__":
    # Start Flask health check server in background thread
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    logging.getLogger(__name__).info(f"Health check server started on port {os.getenv('PORT', 8080)}")

    # Start the bot
    bot = AutonomousFaucetBot()
    bot.start()
