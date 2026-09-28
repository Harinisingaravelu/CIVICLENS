from .history import latest_comparison, state_history

def historical_result(question: str):
    q = question.strip().lower()
    if not any(word in q for word in ("historical", "history", "previous", "changed", "change since", "trend")):
        return None
    for state in ("Tamil Nadu", "Uttar Pradesh", "West Bengal"):
        if state.lower() in q:
            result = state_history(state)
            if result["status"] != "ok":
                return {"intent":"historical_state_unavailable","result":result}
            return {"intent":"historical_state_change","result":result}
    result = latest_comparison()
    return {"intent":"historical_comparison" if result["status"] == "ok" else "historical_comparison_unavailable","result":result}
