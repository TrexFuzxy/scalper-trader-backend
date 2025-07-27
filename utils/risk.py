def calculate_position_size(account_size, stop_loss, risk_pct):
    risk_amount = account_size * (risk_pct / 100)
    position_size = risk_amount / abs(stop_loss)
    return round(position_size, 2) 