class RiskManager:
    def suggest_levels(self, data, signal):
        last_close = data['Close'].iloc[-1]
        atr = data['High'].rolling(14).max() - data['Low'].rolling(14).min()
        atr = atr.iloc[-1] if not atr.empty else 0.01 * last_close
        if signal == 1:  # Buy
            stop_loss = last_close - atr
            take_profit = last_close + 2 * atr
        elif signal == 2:  # Sell
            stop_loss = last_close + atr
            take_profit = last_close - 2 * atr
        else:
            stop_loss = take_profit = last_close
        return stop_loss, take_profit