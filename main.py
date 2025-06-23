from utils.config import load_config
from signals.signal_engine import SignalEngine
from indicators.indicator_engine import IndicatorEngine
from sentiment.sentiment_analyzer import SentimentAnalyzer
from risk.risk_manager import RiskManager
from delivery.bot_delivery import BotDelivery

def main():
    config = load_config()
    indicator_engine = IndicatorEngine()
    sentiment_analyzer = SentimentAnalyzer()
    signal_engine = SignalEngine(model_path='models/signal_model.pkl')
    risk_manager = RiskManager()
    bot_delivery = BotDelivery(config)

    # Example: Fetch data, compute indicators, analyze sentiment, generate signal
    data = indicator_engine.fetch_data(config['asset'], config['interval'])
    features = indicator_engine.compute_features(data)
    sentiment = sentiment_analyzer.analyze_latest_news(config['asset'])
    signal, confidence = signal_engine.predict_signal(features + [sentiment])
    stop_loss, take_profit = risk_manager.suggest_levels(data, signal)
    bot_delivery.send_signal(signal, confidence, stop_loss, take_profit, config['asset'])

if __name__ == "__main__":
    main()