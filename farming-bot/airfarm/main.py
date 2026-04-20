import os
from dotenv import load_dotenv
from .orchestrator import AirdropOrchestrator
from .utils import setup_logging

if __name__ == "__main__":
    load_dotenv()
    setup_logging()
    bot = AirdropOrchestrator()
    bot.start()
