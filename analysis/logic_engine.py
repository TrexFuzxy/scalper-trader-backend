def generate_signal(analysis):
    # Dummy: Combine patterns and indicators for a signal
    signal = {
        "action": "buy" if "doji" in analysis.get("patterns", []) else "sell",
        "entry": 100.0,
        "stop_loss": 98.0,
        "take_profit": 105.0,
        "confidence": 0.85,
        "details": analysis
    }
    return signal 