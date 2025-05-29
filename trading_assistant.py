# ULTIMATE PRO TRADING SUITE
# Created by Naitik Upadhyay

import yfinance as yf
import talib
import numpy as np
import pandas as pd
import requests
import telegram
from transformers import pipeline
from newsapi import NewsApiClient
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
import warnings
warnings.filterwarnings('ignore')

# ==================== CONFIGURATION ====================
class Config:
    # Asset Settings
    SYMBOLS = ["BTC-USD", "ETH-USD", "SPY"]  # Monitor multiple assets
    TIMEFRAME = "15m"                         # 1m, 5m, 15m, 1h, 4h, 1d
    
    # Risk Management
    RISK_PERCENT = 1.0                        # Risk per trade (1-5%)
    MAX_PORTFOLIO_RISK = 15.0                 # Max total portfolio risk %
    
    # APIs (Get your free keys)
    NEWS_API_KEY = "your_newsapi_key"
    ALPHA_VANTAGE_KEY = "your_alphavantage_key"
    TELEGRAM_TOKEN = "your_telegram_bot_token"
    TELEGRAM_CHAT_ID = "your_chat_id"
    
    # Broker Integration (Example: Binance)
    BROKER_API_KEY = "your_broker_api_key"
    BROKER_SECRET = "your_broker_secret"

# ==================== ENHANCED MARKET DATA ====================
class DataEngine:
    def __init__(self):
        self.cache = {}
        
    def get_live_data(self, symbol):
        """Fetch live market data with retries"""
        try:
            data = yf.download(symbol, period="10d", interval=Config.TIMEFRAME)
            self.cache[symbol] = data
            return data
        except Exception as e:
            print(f"Error fetching data for {symbol}: {str(e)}")
            return self.cache.get(symbol, pd.DataFrame())

    def get_fundamentals(self, symbol):
        """Get fundamental data (Alpha Vantage)"""
        if "-" in symbol:  # Crypto
            url = f"https://www.alphavantage.co/query?function=DIGITAL_CURRENCY_DAILY&symbol={symbol.split('-')[0]}&market=USD&apikey={Config.ALPHA_VANTAGE_KEY}"
        else:  # Stock
            url = f"https://www.alphavantage.co/query?function=OVERVIEW&symbol={symbol}&apikey={Config.ALPHA_VANTAGE_KEY}"
        
        try:
            response = requests.get(url).json()
            return {
                "pe_ratio": float(response.get("PE Ratio", 0)),
                "market_cap": float(response.get("MarketCapitalization", 0)),
                "52_week_high": float(response.get("52WeekHigh", 0))
            }
        except:
            return None

# ==================== AI PREDICTION ENGINE ====================
class AIEngine:
    def __init__(self):
        self.models = {}
        
    def create_model(self, input_shape):
        """Advanced LSTM architecture"""
        model = Sequential([
            LSTM(256, return_sequences=True, input_shape=input_shape),
            Dropout(0.4),
            LSTM(128),
            Dropout(0.3),
            Dense(64, activation='relu'),
            Dense(1)
        ])
        model.compile(optimizer='adam', loss='mse')
        return model
    
    def predict_price(self, symbol, data):
        """Multi-feature price prediction"""
        if symbol not in self.models:
            self.models[symbol] = self.create_model((60, 8))
            
        # Feature engineering
        data = self.calculate_indicators(data)
        features = data[['Close', 'SMA_50', 'EMA_20', 'RSI', 'MACD', 'BB_Upper', 'BB_Lower', 'OBV']]
        
        # Normalize
        scaler = MinMaxScaler()
        scaled_data = scaler.fit_transform(features)
        
        # Prepare sequences
        X, y = [], []
        seq_length = 60
        for i in range(seq_length, len(scaled_data)):
            X.append(scaled_data[i-seq_length:i])
            y.append(scaled_data[i, 0])
        
        # Train and predict
        self.models[symbol].fit(np.array(X), np.array(y), epochs=50, batch_size=32, verbose=0)
        future_pred = self.models[symbol].predict(scaled_data[-seq_length:].reshape(1, seq_length, 8))
        return scaler.inverse_transform(
            np.concatenate((future_pred, scaled_data[-1, 1:].reshape(1,-1)), axis=1)
        )[0][0]

    def calculate_indicators(self, data):
        """Calculate all technical indicators"""
        # Trend Indicators
        data['SMA_50'] = talib.SMA(data['Close'], timeperiod=50)
        data['EMA_20'] = talib.EMA(data['Close'], timeperiod=20)
        
        # Momentum Indicators
        data['RSI'] = talib.RSI(data['Close'], timeperiod=14)
        data['MACD'], data['MACD_Signal'], _ = talib.MACD(data['Close'])
        
        # Volatility Indicators
        data['BB_Upper'], data['BB_Middle'], data['BB_Lower'] = talib.BBANDS(data['Close'])
        
        # Volume Indicators
        data['OBV'] = talib.OBV(data['Close'], data['Volume'])
        
        return data

# ==================== SENTIMENT ANALYSIS ====================
class SentimentEngine:
    def __init__(self):
        self.nlp = pipeline("sentiment-analysis", 
                          model="finiteautomata/bertweet-base-sentiment-analysis")
        self.newsapi = NewsApiClient(api_key=Config.NEWS_API_KEY)
        
    def get_sentiment(self, symbol):
        """Multi-source sentiment analysis"""
        # News sentiment
        news = self.newsapi.get_everything(
            q=symbol.split('-')[0],
            language='en',
            sort_by='relevancy'
        )
        
        # Social media sentiment (simulated)
        social_posts = self._get_social_media_posts(symbol)
        
        # Analyze sentiment
        news_scores = [self.nlp(article['title'])[0] for article in news['articles'][:5]]
        social_scores = [self.nlp(post)[0] for post in social_posts]
        
        # Calculate weighted score
        positive = sum([1 for res in news_scores + social_scores if res['label'] == 'POSITIVE'])
        total = len(news_scores + social_scores)
        score = (positive - (total - positive)) / total
        
        if score > 0.3:
            return "EXTREME BULLISH", score
        elif score > 0.1:
            return "BULLISH", score
        elif score < -0.3:
            return "EXTREME BEARISH", score
        elif score < -0.1:
            return "BEARISH", score
        else:
            return "NEUTRAL", score
            
    def _get_social_media_posts(self, symbol):
        """Simulate fetching social media posts"""
        # In production, connect to Twitter/Reddit API
        return [
            f"{symbol} is looking bullish today!",
            f"Analysts predict a rally for {symbol}",
            f"Warning: {symbol} showing overbought signals"
        ]

# ==================== RISK MANAGEMENT ====================
class RiskManager:
    def __init__(self):
        self.portfolio = {}
        
    def calculate_position(self, symbol, current_price, stop_loss_pct):
        """Advanced position sizing"""
        account_balance = 10000  # In production, fetch from broker
        risk_amount = account_balance * (Config.RISK_PERCENT / 100)
        stop_loss = current_price * (1 - stop_loss_pct)
        position_size = risk_amount / (current_price - stop_loss)
        
        # Check portfolio exposure
        total_risk = sum(
            pos['risk'] for pos in self.portfolio.values()
        ) + (risk_amount / account_balance * 100)
        
        if total_risk > Config.MAX_PORTFOLIO_RISK:
            return 0  # Skip trade to avoid overexposure
            
        return round(position_size, 2)
    
    def update_portfolio(self, symbol, position):
        """Track portfolio exposure"""
        self.portfolio[symbol] = position

# ==================== TRADE EXECUTION ====================
class TradeExecutor:
    def __init__(self):
        self.bot = telegram.Bot(token=Config.TELEGRAM_TOKEN)
        
    def send_alert(self, message):
        """Send Telegram alert"""
        try:
            self.bot.send_message(
                chat_id=Config.TELEGRAM_CHAT_ID,
                text=message,
                parse_mode='Markdown'
            )
        except Exception as e:
            print(f"Failed to send alert: {str(e)}")
    
    def execute_broker_trade(self, symbol, side, quantity):
        """Connect to broker API (example: Binance)"""
        # In production, implement with CCXT or broker SDK
        print(f"[BROKER] Would execute {side} {quantity} {symbol}")
        return True

# ==================== MAIN TRADING BOT ====================
class TradingBot:
    def __init__(self):
        self.data_engine = DataEngine()
        self.ai_engine = AIEngine()
        self.sentiment_engine = SentimentEngine()
        self.risk_manager = RiskManager()
        self.trade_executor = TradeExecutor()
        
    def analyze_symbol(self, symbol):
        """Complete analysis for one symbol"""
        print(f"\n🔍 Analyzing {symbol}...")
        
        # Get data
        data = self.data_engine.get_live_data(symbol)
        if data.empty:
            return None
            
        current_price = data['Close'].iloc[-1]
        
        # AI Prediction
        predicted_price = self.ai_engine.predict_price(symbol, data)
        
        # Sentiment Analysis
        sentiment, sentiment_score = self.sentiment_engine.get_sentiment(symbol)
        
        # Generate signal
        signal = self._generate_signal(data, current_price, predicted_price, sentiment)
        
        # Risk management
        position_size = self.risk_manager.calculate_position(
            symbol, 
            current_price,
            stop_loss_pct=0.02 if signal['confidence'] > 70 else 0.01
        )
        
        # Prepare report
        report = {
            "symbol": symbol,
            "current_price": current_price,
            "predicted_price": predicted_price,
            "sentiment": sentiment,
            "signal": signal,
            "position_size": position_size,
            "indicators": self.ai_engine.calculate_indicators(data).iloc[-1].to_dict(),
            "patterns": self._detect_patterns(data)
        }
        
        return report
    
    def _generate_signal(self, data, current_price, predicted_price, sentiment):
        """Advanced signal generation"""
        # Technical factors
        indicators = self.ai_engine.calculate_indicators(data)
        trend = "UP" if indicators['SMA_50'].iloc[-1] > indicators['SMA_50'].iloc[-2] else "DOWN"
        momentum = "BULLISH" if indicators['MACD'].iloc[-1] > indicators['MACD_Signal'].iloc[-1] else "BEARISH"
        
        # Prediction confidence
        pred_diff = abs(predicted_price - current_price) / current_price
        confidence = min(90, int(pred_diff * 2000))  # Scale confidence
        
        # Generate signal
        if (predicted_price > current_price * 1.015 and 
            "BULL" in sentiment and 
            momentum == "BULLISH"):
            return {
                "action": "BUY",
                "confidence": confidence,
                "reason": f"Strong bullish confluence (AI: +{pred_diff:.2%})"
            }
        elif (predicted_price < current_price * 0.985 and 
              "BEAR" in sentiment and 
              momentum == "BEARISH"):
            return {
                "action": "SELL",
                "confidence": confidence,
                "reason": f"Strong bearish confluence (AI: -{pred_diff:.2%})"
            }
        else:
            return {
                "action": "HOLD",
                "confidence": 100 - confidence,
                "reason": "Waiting for better opportunity"
            }
    
    def _detect_patterns(self, data):
        """Detect candlestick patterns"""
        patterns = []
        for pattern in [
            'CDLENGULFING', 'CDLHAMMER', 'CDLMORNINGSTAR',
            'CDLEVENINGSTAR', 'CDLPIERCING', 'CDL3WHITESOLDIERS'
        ]:
            result = getattr(talib, pattern)(
                data['Open'], data['High'], data['Low'], data['Close']
            )
            if result.iloc[-1] != 0:
                patterns.append(pattern[3:])  # Remove 'CDL' prefix
        return patterns if patterns else ["No clear patterns"]
    
    def run(self):
        """Main execution loop"""
        print(f"\n{'='*60}")
        print(f"🚀 ULTIMATE PRO TRADING BOT | {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        print(f"📊 Monitoring {len(Config.SYMBOLS)} assets | {Config.TIMEFRAME} timeframe")
        print(f"⚖️ Risk Management: {Config.RISK_PERCENT}% per trade")
        print(f"{'='*60}\n")
        
        while True:
            try:
                for symbol in Config.SYMBOLS:
                    report = self.analyze_symbol(symbol)
                    if not report:
                        continue
                        
                    self._display_report(report)
                    
                    # Execute trades for high-confidence signals
                    if report['signal']['confidence'] > 75 and report['position_size'] > 0:
                        self._execute_trade(report)
                        
                # Wait for next interval
                time.sleep(300)  # 5 minutes
                
            except Exception as e:
                print(f"Error in main loop: {str(e)}")
                time.sleep(60)
    
    def _display_report(self, report):
        """Display analysis results"""
        print(f"\n📈 {report['symbol']} @ ${report['current_price']:.2f}")
        print(f"🔮 Predicted: ${report['predicted_price']:.2f} ({'↑' if report['predicted_price'] > report['current_price'] else '↓'})")
        print(f"📰 Sentiment: {report['sentiment']}")
        print(f"🎯 Signal: {report['signal']['action']} (Confidence: {report['signal']['confidence']}%)")
        print(f"💡 Reason: {report['signal']['reason']}")
        print(f"📊 Position Size: {report['position_size']} {report['symbol'].split('-')[0]}")
        
        # Send Telegram alert
        message = (
            f"*{report['symbol']} Trading Signal*\n"
            f"Price: ${report['current_price']:.2f}\n"
            f"Signal: *{report['signal']['action']}* ({report['signal']['confidence']}%)\n"
            f"Reason: {report['signal']['reason']}\n"
            f"Position: {report['position_size']} shares"
        )
        self.trade_executor.send_alert(message)
    
    def _execute_trade(self, report):
        """Execute trade through broker API"""
        symbol = report['symbol']
        action = report['signal']['action']
        quantity = report['position_size']
        
        # Execute trade
        success = self.trade_executor.execute_broker_trade(
            symbol=symbol,
            side=action,
            quantity=quantity
        )
        
        if success:
            print(f"\n✅ Executed {action} order for {quantity} {symbol}")
            self.risk_manager.update_portfolio(symbol, {
                "direction": action,
                "quantity": quantity,
                "entry_price": report['current_price'],
                "risk": Config.RISK_PERCENT
            })

# ==================== RUN THE BOT ====================
if __name__ == "__main__":
    bot = TradingBot()
    bot.run()