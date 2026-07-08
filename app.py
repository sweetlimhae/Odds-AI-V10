from flask import Flask, jsonify, render_template, request
from config import ODDS_API_KEY, MIN_START_MINUTES, MAX_START_MINUTES
from odds import get_games
from analyzer import build_recommendations, build_summary

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/live-games")
def live_games():
    sport = request.args.get("sport", "all")
    minutes = int(request.args.get("minutes", 1440))
    games, mode, notice = get_games(sport, minutes)
    return jsonify({"mode": mode, "sport": sport, "minutes": minutes, "count": len(games), "games": games, "notice": notice, "time_filter": {"min_minutes": 0, "max_minutes": minutes}})

@app.route("/api/recommendations")
def recommendations():
    sport = request.args.get("sport", "all")
    minutes = int(request.args.get("minutes", 1440))
    games, mode, notice = get_games(sport, minutes)
    combos, picks, no_bet = build_recommendations(games)
    summary = build_summary(picks, combos, no_bet)
    excluded = [{"game": p["game"], "pick": p["pick"], "score": p["score"], "confidence": p["confidence"], "ev": p["ev"], "ai_edge": p["ai_edge"], "risk": p["risk"], "decision": p["decision"], "reason": "AI 기준 미달 또는 No Bet"} for p in picks if p["decision"] == "NO_BET"]
    return jsonify({"mode": mode, "sport": sport, "minutes": minutes, "combos": combos, "top_picks": picks[:10], "excluded": excluded, "summary": summary, "no_bet": no_bet, "notice": notice})

@app.route("/api/health")
def health():
    return jsonify({"status": "ok", "version": "Odds-AI-V10-practical", "odds_api_key": bool(ODDS_API_KEY), "time_filter": {"min_minutes": MIN_START_MINUTES, "max_minutes": MAX_START_MINUTES}, "source": "liveman_soccer_plus_practical_combo"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
