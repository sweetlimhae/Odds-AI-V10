from utils import safe_float, implied_probability, drop_rate

def clamp(value, low=0, high=100):
    return max(low, min(high, value))

def realistic_probability(score):
    score = safe_float(score)
    if score <= 0:
        return 0
    return min(0.74, max(0.42, score / 135))

def ev_percent_from_prob(probability, odds):
    odds = safe_float(odds)
    probability = safe_float(probability)
    if odds <= 1 or probability <= 0:
        return 0
    p = probability / 100
    return round((p * odds - 1) * 100, 2)

def kelly_percent_from_prob(probability, odds):
    odds = safe_float(odds)
    probability = safe_float(probability)
    if odds <= 1 or probability <= 0:
        return 0
    p = probability / 100
    b = odds - 1
    k = ((b * p) - (1 - p)) / b
    return round(clamp(k * 100, 0, 10), 2)

def value_gap_component(odds, market_avg):
    odds = safe_float(odds)
    market_avg = safe_float(market_avg)
    if odds <= 1 or market_avg <= 1:
        return 0
    gap = ((market_avg - odds) / odds) * 100
    if gap >= 6:
        return 100
    if gap >= 4:
        return 82
    if gap >= 2:
        return 65
    if gap >= 1:
        return 48
    if gap >= 0:
        return 35
    return 15

def calculate_ai_score(market):
    odds = safe_float(market.get("odds"))
    open_odds = safe_float(market.get("open_odds"))
    pinnacle_odds = safe_float(market.get("pinnacle_odds"))
    market_avg = safe_float(market.get("market_avg"))

    d = drop_rate(open_odds, odds)
    steam_score = safe_float(market.get("steam_score"))
    sharp_score = safe_float(market.get("sharp_score"))
    clv_score = safe_float(market.get("clv_score"))
    rlm_score = safe_float(market.get("rlm_score"))
    value_score = value_gap_component(odds, market_avg)
    consensus = safe_float(market.get("consensus_rate"))

    pinnacle_score = 72 if pinnacle_odds and market_avg and pinnacle_odds < market_avg else 45

    drop_score = 30
    if d >= 8:
        drop_score = 95
    elif d >= 5:
        drop_score = 80
    elif d >= 3:
        drop_score = 62
    elif d >= 1:
        drop_score = 45

    score = (
        sharp_score * 0.28 +
        steam_score * 0.19 +
        clv_score * 0.14 +
        value_score * 0.13 +
        pinnacle_score * 0.09 +
        drop_score * 0.08 +
        rlm_score * 0.06 +
        consensus * 0.03
    )

    if sharp_score < 55 and steam_score < 45:
        score = min(score, 74)
    elif sharp_score < 70 and steam_score < 60:
        score = min(score, 84)

    return int(clamp(round(score), 0, 99))

def risk_level(score, ev, kelly, ai_edge, sharp, steam):
    if score >= 88 and ev >= 5 and kelly >= 2 and ai_edge >= 3 and sharp >= 70 and steam >= 55:
        return "low"
    if score >= 76 and ev >= 0 and ai_edge >= 0 and sharp >= 45:
        return "medium"
    return "high"

def recommendation_decision(confidence, ev, kelly, ai_edge, risk, sharp, steam):
    if risk == "low" and confidence >= 88 and ev >= 5 and kelly >= 2 and sharp >= 70:
        return "BET"
    if confidence >= 76 and ev >= 0 and ai_edge >= 0 and sharp >= 45:
        return "WATCH"
    return "NO_BET"

def recommendation_grade(confidence, decision, sharp, steam):
    if decision == "NO_BET":
        return "No Bet"
    if confidence >= 92 and sharp >= 80 and steam >= 70:
        return "★★★★★ 강추천"
    if confidence >= 86 and sharp >= 65:
        return "★★★★ 추천"
    if confidence >= 76:
        return "★★★ 관찰"
    return "No Bet"

def reasons_for_pick(market, d, ev, sharp_score, steam_score, clv_score, value_score, risk, confidence, ai_edge, decision):
    reasons = []
    if decision == "NO_BET":
        if ev < 0:
            reasons.append("EV 부족")
        if ai_edge < 0:
            reasons.append("AI Edge 부족")
        if risk == "high":
            reasons.append("위험도 높음")
        if sharp_score < 50:
            reasons.append("Sharp 신호 약함")
        if steam_score < 40:
            reasons.append("Steam 신호 약함")
        return reasons or ["추천 근거 부족"]

    if d >= 5:
        reasons.append("초기배당 대비 강한 하락")
    elif d >= 2:
        reasons.append("배당 하락 감지")
    if sharp_score >= 80:
        reasons.append("Sharp Money 강함")
    elif sharp_score >= 60:
        reasons.append("Sharp Money 양호")
    if steam_score >= 75:
        reasons.append("Steam Move 강함")
    elif steam_score >= 55:
        reasons.append("Steam Move 감지")
    if clv_score >= 60:
        reasons.append("CLV 기대값 있음")
    if value_score >= 65:
        reasons.append("시장 평균 대비 가치 있음")
    if ev >= 10:
        reasons.append("EV 매우 우수")
    elif ev >= 5:
        reasons.append("EV 우수")
    elif ev > 0:
        reasons.append("EV 양호")
    if ai_edge >= 6:
        reasons.append("AI Edge 우수")
    if risk == "low":
        reasons.append("위험도 낮음")
    return reasons or ["관찰 필요"]

def ai_analysis_text(p):
    if p["decision"] == "BET":
        return f"{p['pick']}은 AI 예상승률 {p['ai_probability']}%, 시장확률 {p['market_probability']}%, Edge {p['ai_edge']}%입니다. Sharp {p['sharp_score']}점, Steam {p['steam_score']}점, CLV {p['clv_score']}점으로 실전 후보입니다."
    if p["decision"] == "WATCH":
        return f"{p['pick']}은 조건은 나쁘지 않지만 강한 확신은 부족합니다. Sharp {p['sharp_score']}점, Steam {p['steam_score']}점, EV {p['ev']}%라 관찰 구간입니다."
    return f"{p['pick']}은 현재 No Bet입니다. EV {p['ev']}%, AI Edge {p['ai_edge']}%, Sharp {p['sharp_score']}점 기준에서 추천 근거가 부족합니다."

def analyze_market(game, market):
    odds = safe_float(market.get("odds"))
    open_odds = safe_float(market.get("open_odds"))
    pinnacle_odds = safe_float(market.get("pinnacle_odds"))
    market_avg = safe_float(market.get("market_avg"))

    d = drop_rate(open_odds, odds)
    score = calculate_ai_score(market)
    ai_prob = round(realistic_probability(score) * 100, 2)
    market_prob = implied_probability(odds)
    ai_edge = round(ai_prob - market_prob, 2)
    ev = ev_percent_from_prob(ai_prob, odds)
    kelly = kelly_percent_from_prob(ai_prob, odds)

    sharp_score = safe_float(market.get("sharp_score"))
    steam_score = safe_float(market.get("steam_score"))
    clv_score = safe_float(market.get("clv_score"))
    rlm_score = safe_float(market.get("rlm_score"))
    value_score = value_gap_component(odds, market_avg)

    risk = risk_level(score, ev, kelly, ai_edge, sharp_score, steam_score)
    confidence = int(clamp(score + (ai_edge * 0.25) + (ev * 0.15), 0, 99))

    if sharp_score < 60 or steam_score < 45:
        confidence = min(confidence, 84)

    decision = recommendation_decision(confidence, ev, kelly, ai_edge, risk, sharp_score, steam_score)
    grade = recommendation_grade(confidence, decision, sharp_score, steam_score)

    item = {
        "sport": game.get("sport"),
        "league": game.get("league"),
        "game": f"{game.get('league')} {game.get('home')} vs {game.get('away')}",
        "home": game.get("home"),
        "away": game.get("away"),
        "starts_at": game.get("starts_at"),
        "start_in_minutes": game.get("start_in_minutes"),
        "type": market.get("type"),
        "pick": market.get("pick"),
        "bookmaker": market.get("bookmaker"),
        "is_pinnacle": market.get("is_pinnacle", False),
        "odds": odds,
        "open_odds": open_odds,
        "pinnacle_odds": pinnacle_odds,
        "market_avg": market_avg,
        "best_odds": market.get("best_odds"),
        "drop_rate": d,
        "market_probability": market_prob,
        "implied_probability": market_prob,
        "ai_probability": ai_prob,
        "ai_edge": ai_edge,
        "score": score,
        "confidence": confidence,
        "ev": ev,
        "kelly": kelly,
        "sharp_score": sharp_score,
        "steam_score": steam_score,
        "clv_score": clv_score,
        "rlm_score": rlm_score,
        "value_score": value_score,
        "risk": risk,
        "decision": decision,
        "grade": grade,
        "bookmakers": market.get("bookmakers", []),
        "movement": market.get("movement", "-"),
        "market_count": market.get("market_count", 0),
        "consensus_rate": market.get("consensus_rate", 0),
        "closing_prediction": market.get("closing_prediction"),
        "history": market.get("history", []),
    }

    item["reasons"] = reasons_for_pick(market, d, ev, sharp_score, steam_score, clv_score, value_score, risk, confidence, ai_edge, decision)
    item["ai_analysis"] = ai_analysis_text(item)
    return item
