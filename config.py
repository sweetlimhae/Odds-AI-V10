import os
ODDS_API_KEY = os.getenv("ODDS_API_KEY", "")
MIN_START_MINUTES = int(os.getenv("MIN_START_MINUTES", "0"))
MAX_START_MINUTES = int(os.getenv("MAX_START_MINUTES", "1440"))
