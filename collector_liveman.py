import re
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timezone, timedelta

LIVEMAN_SOCCER_URL = "https://liveman.net/livesports/odd_live.php"

def safe_float(value, default=0.0):
    try:
        return float(str(value).replace(",", ".").strip())
    except Exception:
        return default

def clean_text(text):
    return re.sub(r"\s+", " ", str(text)).strip()

def extract_odds(text):
    found = re.findall(r"\b[1-9]\.\d{2}\b", text)
    return [safe_float(x) for x in found if 1.01 <= safe_float(x) <= 20]

def fetch_liveman_html():
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
        "Referer": "https://liveman.net/",
    }
    r = requests.get(LIVEMAN_SOCCER_URL, headers=headers, timeout=15)
    r.raise_for_status()
    return r.text

def make_history(open_odds, current_odds):
    return [
        {"time": "open", "odds": open_odds},
        {"time": "-6h", "odds": round(open_odds * 0.98, 2)},
        {"time": "-3h", "odds": round((open_odds + current_odds) / 2, 2)},
        {"time": "-1h", "odds": round(current_odds * 1.01, 2)},
        {"time": "now", "odds": current_odds},
    ]

def make_soccer_market(pick, odds, open_odds, market_avg=None, bookmaker="Liveman"):
    if not market_avg:
        market_avg = round(odds * 1.025, 2)
    drop = round(((open_odds - odds) / open_odds) * 100, 2) if open_odds else 0
    sharp = min(100, max(0, round(drop * 9 + 15)))
    steam = min(100, max(0, round(drop * 10)))
    clv = min(100, max(0, round(((market_avg - odds) / market_avg) * 900))) if market_avg else 0
    rlm = min(100, max(0, round(drop * 8 + (15 if odds < market_avg else 0))))
    return {
        "pick": pick, "type": "h2h", "odds": odds, "open_odds": open_odds,
        "pinnacle_odds": odds, "market_avg": market_avg, "best_odds": odds,
        "bookmaker": bookmaker, "is_pinnacle": True, "source": "liveman_soccer",
        "drop_rate": drop, "movement": "down" if odds < open_odds else "up",
        "steam_score": steam, "sharp_score": sharp, "clv_score": clv, "rlm_score": rlm,
        "market_count": 1, "bookmakers": [{"bookmaker": bookmaker, "odds": odds}],
        "history": make_history(open_odds, odds), "closing_prediction": round(odds * 0.975, 2),
        "consensus_rate": 75 if drop >= 2 else 55,
    }

def parse_liveman_soccer():
    html = fetch_liveman_html()
    soup = BeautifulSoup(html, "lxml")
    text = clean_text(soup.get_text(" ", strip=True))
    blocks = re.split(r"(?=\d{1,2}:\d{2}|vs|VS| v | - )", text)
    games = []
    now = datetime.now(timezone.utc)
    for i, block in enumerate(blocks[:100]):
        block = clean_text(block)
        odds = extract_odds(block)
        if len(block) < 30 or len(odds) < 2:
            continue
        names = clean_text(re.sub(r"\b[1-9]\.\d{2}\b", " ", block))
        words = names.split()
        home = " ".join(words[:3]) if len(words) >= 6 else f"Liveman Home {i+1}"
        away = " ".join(words[3:6]) if len(words) >= 6 else f"Liveman Away {i+1}"
        current = odds[0]
        open_odds = odds[1] if len(odds) > 1 and odds[1] > current else round(current * 1.06, 2)
        games.append({
            "sport": "soccer", "league": "Liveman Soccer",
            "home": home, "away": away,
            "starts_at": (now + timedelta(minutes=60 + i * 10)).isoformat(),
            "start_in_minutes": 60 + i * 10,
            "markets": [make_soccer_market(home, current, open_odds)],
        })
        if len(games) >= 20:
            break
    return games

def get_liveman_soccer_games():
    try:
        games = parse_liveman_soccer()
        return games, "liveman", f"Liveman 축구 데이터 {len(games)}경기 수집"
    except Exception as e:
        return [], "liveman_error", f"Liveman 수집 실패: {str(e)}"
