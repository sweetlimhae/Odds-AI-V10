from itertools import combinations
import math
from utils import safe_float
from ai import analyze_market

def flatten_picks(games):
    picks = []
    for game in games or []:
        for market in game.get("markets", []):
            if safe_float(market.get("odds")) > 1:
                picks.append(analyze_market(game, market))
    return sorted(
        picks,
        key=lambda p: (p["decision"] == "BET", p["confidence"], p["sharp_score"], p["ev"]),
        reverse=True
    )

def unique_by_game(picks):
    seen = set()
    result = []
    for p in picks:
        key = p.get("game")
        if key in seen:
            continue
        seen.add(key)
        result.append(p)
    return result

def hit_rate_from_picks(picks):
    if not picks:
        return 0
    probs = [safe_float(p.get("ai_probability")) / 100 for p in picks]
    hit = math.prod(probs) * 100
    return round(hit, 1)

def combo_item(name, picks, profile):
    if not picks:
        return None

    total_odds = math.prod([safe_float(p["odds"], 1) for p in picks])
    size = len(picks)
    hit_rate = hit_rate_from_picks(picks)

    if profile == "safe":
        stake = "시드 1~2%"
        memo = "안정 우선. 배당보다 신뢰도와 위험도 우선."
    elif profile == "normal":
        stake = "시드 0.7~1.5%"
        memo = "밸런스형. 신뢰도와 배당 균형."
    else:
        stake = "시드 0.3~0.8%"
        memo = "도전형. 배당은 높지만 변동성 큼."

    return {
        "type": name,
        "folder_size": size,
        "total_odds": round(total_odds, 2),
        "estimated_hit_rate": hit_rate,
        "stake_guide": stake,
        "profile_memo": memo,
        "avg_score": round(sum(p["score"] for p in picks) / size, 1),
        "avg_confidence": round(sum(p["confidence"] for p in picks) / size, 1),
        "avg_ev": round(sum(p["ev"] for p in picks) / size, 2),
        "avg_kelly": round(sum(p["kelly"] for p in picks) / size, 2),
        "avg_edge": round(sum(p["ai_edge"] for p in picks) / size, 2),
        "picks": picks,
    }

def best_combo(name, pool, profile, size=3):
    pool = unique_by_game(pool)

    if len(pool) < size:
        return combo_item(name, pool, profile) if pool else None

    best = None
    for combo in combinations(pool[:14], size):
        item = combo_item(name, list(combo), profile)

        if profile == "safe":
            rank = (item["estimated_hit_rate"], item["avg_confidence"], -item["total_odds"])
        elif profile == "normal":
            distance = abs(item["total_odds"] - 6.5)
            rank = (item["avg_confidence"], item["estimated_hit_rate"], -distance)
        else:
            rank = (item["avg_edge"], item["avg_ev"], item["total_odds"], item["avg_confidence"])

        if best is None:
            best = item
            continue

        if profile == "safe":
            old = (best["estimated_hit_rate"], best["avg_confidence"], -best["total_odds"])
        elif profile == "normal":
            old_distance = abs(best["total_odds"] - 6.5)
            old = (best["avg_confidence"], best["estimated_hit_rate"], -old_distance)
        else:
            old = (best["avg_edge"], best["avg_ev"], best["total_odds"], best["avg_confidence"])

        if rank > old:
            best = item

    return best

def build_recommendations(games):
    picks = flatten_picks(games)

    safe_pool = [
        p for p in picks
        if p["decision"] in ["BET", "WATCH"]
        and p["risk"] in ["low", "medium"]
        and p["confidence"] >= 76
        and p["sharp_score"] >= 45
        and p["ev"] >= -1
    ]

    normal_pool = [
        p for p in picks
        if p["decision"] in ["BET", "WATCH"]
        and p["confidence"] >= 70
        and p["ev"] >= -2
    ]

    challenge_pool = [
        p for p in picks
        if p["confidence"] >= 62
        and p["ai_edge"] >= -3
        and p["ev"] >= -5
    ]

    combos = [
        best_combo("안전형 3폴더", safe_pool, "safe", 3),
        best_combo("평균형 3폴더", normal_pool, "normal", 3),
        best_combo("도전형 3폴더", challenge_pool, "challenge", 3),
    ]

    combos = [c for c in combos if c and c.get("picks")]
    return combos, picks, len(combos) == 0

def build_summary(picks, combos, no_bet):
    if not picks:
        return {
            "total_picks": 0,
            "top_score": 0,
            "top_confidence": 0,
            "avg_ev": 0,
            "avg_edge": 0,
            "recommendation_count": 0,
            "bet_count": 0,
            "watch_count": 0,
            "no_bet_count": 0,
            "no_bet": True,
            "message": "분석 가능한 경기가 없습니다.",
        }

    bet_count = len([p for p in picks if p["decision"] == "BET"])
    watch_count = len([p for p in picks if p["decision"] == "WATCH"])
    no_bet_count = len([p for p in picks if p["decision"] == "NO_BET"])

    return {
        "total_picks": len(picks),
        "bet_count": bet_count,
        "watch_count": watch_count,
        "no_bet_count": no_bet_count,
        "top_score": max(p["score"] for p in picks),
        "top_confidence": max(p["confidence"] for p in picks),
        "avg_ev": round(sum(p["ev"] for p in picks) / len(picks), 2),
        "avg_edge": round(sum(p["ai_edge"] for p in picks) / len(picks), 2),
        "recommendation_count": len(combos),
        "no_bet": no_bet,
        "message": "안전형/평균형/도전형 3폴더 추천 생성" if not no_bet else "오늘은 관망 추천",
    }
