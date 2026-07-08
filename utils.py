def safe_float(value, default=0.0):
    try:
        if value is None:
            return default
        return float(str(value).replace(",", "."))
    except Exception:
        return default

def implied_probability(odds):
    odds = safe_float(odds)
    if odds <= 1:
        return 0
    return round((1 / odds) * 100, 2)

def drop_rate(open_odds, current_odds):
    open_odds = safe_float(open_odds)
    current_odds = safe_float(current_odds)
    if open_odds <= 1 or current_odds <= 1:
        return 0
    return round(((open_odds - current_odds) / open_odds) * 100, 2)
