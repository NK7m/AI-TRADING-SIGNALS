class BotDelivery:
    def __init__(self, config):
        self.config = config
        # Initialize Discord/Telegram bot here

    def send_signal(self, signal, confidence, stop_loss, take_profit, asset):
        signal_map = {0: "Hold", 1: "Buy", 2: "Sell"}
        msg = (
            f"Signal for {asset}: {signal_map[signal]}\n"
            f"Confidence: {confidence:.2f}%\n"
            f"Stop Loss: {stop_loss:.2f}\n"
            f"Take Profit: {take_profit:.2f}"
        )
        # Send to Discord/Telegram
        print(msg)  # Replace with actual bot send