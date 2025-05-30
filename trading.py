import yfinance as yf
import numpy as np
import pandas as pd
import time
from datetime import datetime
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
import requests
import warnings
warnings.filterwarnings('ignore')

# ==================== CONFIGURATION ====================
class Config:
    # Available markets
    CRYPTO_PAIRS = ["BTC-USD", "ETH-USD", "SOL-USD"]
    FOREX_PAIRS = ["EURUSD=X", "GBPUSD=X", "USDJPY=X"]
    STOCKS = ["TSLA", "AAPL", "NVDA"]
    
    # Available timeframes
    TIMEFRAMES = {
        '1': '1m', 
        '2': '5m', 
        '3': '15m',
        '4': '1h',
        '5': '4h',
        '6': '1d'
    }
    
    # Telegram
    TELEGRAM_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"
    TELEGRAM_CHAT_ID = "YOUR_CHAT_ID"

# ==================== USER INTERFACE ====================
def get_user_input():
    print("\n" + "="*50)
    print("🚀 AI Trading Bot - Configuration")
    print("="*50)
    
    # 1. Asset Selection
    print("\n🛒 Select Asset Category:")
    print("1. Cryptocurrencies")
    print("2. Forex Pairs")
    print("3. Stocks")
    print("4. Custom Symbol")
    
    while True:
        asset_choice = input("Your choice (1-4): ")
        if asset_choice == "1":
            print("\nAvailable Crypto Pairs:")
            for i, pair in enumerate(Config.CRYPTO_PAIRS, 1):
                print(f"{i}. {pair}")
            selection = input(f"Select pair (1-{len(Config.CRYPTO_PAIRS)}): ")
            try:
                symbol = Config.CRYPTO_PAIRS[int(selection)-1]
                break
            except:
                print("Invalid selection, try again")
                
        elif asset_choice == "2":
            print("\nAvailable Forex Pairs:")
            for i, pair in enumerate(Config.FOREX_PAIRS, 1):
                print(f"{i}. {pair.replace('=X','')}")
            selection = input(f"Select pair (1-{len(Config.FOREX_PAIRS)}): ")
            try:
                symbol = Config.FOREX_PAIRS[int(selection)-1]
                break
            except:
                print("Invalid selection, try again")
                
        elif asset_choice == "3":
            print("\nAvailable Stocks:")
            for i, stock in enumerate(Config.STOCKS, 1):
                print(f"{i}. {stock}")
            selection = input(f"Select stock (1-{len(Config.STOCKS)}): ")
            try:
                symbol = Config.STOCKS[int(selection)-1]
                break
            except:
                print("Invalid selection, try again")
                
        elif asset_choice == "4":
            symbol = input("Enter custom symbol (e.g. BTC-USD, TSLA, EURUSD=X): ").strip().upper()
            if not (("-" in symbol) or ("=X" in symbol)):
                print("⚠️ Format as: BTC-USD (crypto) or EURUSD=X (forex)")
                continue
            break
            
        else:
            print("Invalid choice, try again")

    # 2. Timeframe Selection
    print("\n⏰ Select Timeframe:")
    for key, value in Config.TIMEFRAMES.items():
        print(f"{key}. {value}")
    
    while True:
        tf_choice = input("Your choice (1-6): ")
        if tf_choice in Config.TIMEFRAMES:
            timeframe = Config.TIMEFRAMES[tf_choice]
            break
        print("Invalid choice, try again")

    # 3. Signal Interval
    print("\n🔔 Signal Check Interval (minutes)")
    while True:
        try:
            interval = int(input("How often to check for signals (1-60 mins): "))
            if 1 <= interval <= 60:
                break
            print("Please enter between 1-60")
        except:
            print("Invalid input, enter a number")

    return symbol, timeframe, interval * 60  # Convert minutes to seconds

# ==================== TECHNICAL INDICATORS ====================
class TechnicalIndicators:
    @staticmethod
    def rsi(close, window=14):
        delta = close.diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        avg_gain = gain.rolling(window).mean()
        avg_loss = loss.rolling(window).mean()
        rs = avg_gain / avg_loss
        return 100 - (100 / (1 + rs))

    @staticmethod
    def macd(close, fast=12, slow=26, signal=9):
        ema_fast = close.ewm(span=fast).mean()
        ema_slow = close.ewm(span=slow).mean()
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal).mean()
        return macd_line, signal_line

    @staticmethod
    def engulfing_pattern(open, high, low, close):
        bullish = (close > open) & (close.shift(1) < open.shift(1)) & (close > open.shift(1)) & (open < close.shift(1))
        bearish = (close < open) & (close.shift(1) > open.shift(1)) & (close < open.shift(1)) & (open > close.shift(1))
        return bullish, bearish

# ==================== TELEGRAM NOTIFIER ====================
class TelegramNotifier:
    @staticmethod
    def send_message(message):
        url = f"https://api.telegram.org/bot{Config.TELEGRAM_TOKEN}/sendMessage"
        params = {
            'chat_id': Config.TELEGRAM_CHAT_ID,
            'text': message,
            'parse_mode': 'Markdown'
        }
        try:
            requests.post(url, params=params, timeout=10)
        except Exception as e:
            print(f"⚠️ Telegram send failed: {str(e)}")

# ==================== AI TRADING BOT ====================
class AITradingBot:
    def __init__(self, symbol, timeframe):
        self.symbol = symbol
        self.timeframe = timeframe
        self.indicators = TechnicalIndicators()
        self.last_signal = None
        
    def get_data(self):
        data = yf.download(self.symbol, period="10d", interval=self.timeframe)
        if data.empty:
            raise ValueError(f"No data found for {self.symbol}")
        return self._calculate_indicators(data)
    
    def _calculate_indicators(self, data):
        data['SMA_50'] = data['Close'].rolling(50).mean()
        data['EMA_20'] = data['Close'].ewm(span=20).mean()
        data['RSI'] = self.indicators.rsi(data['Close'])
        data['MACD'], data['MACD_Signal'] = self.indicators.macd(data['Close'])
        data['Bullish_Engulfing'], data['Bearish_Engulfing'] = self.indicators.engulfing_pattern(
            data['Open'], data['High'], data['Low'], data['Close']
        )
        return data.dropna()
    
    def predict_price(self, data):
        scaler = MinMaxScaler()
        features = data[['Close', 'SMA_50', 'EMA_20', 'RSI', 'MACD']]
        scaled_data = scaler.fit_transform(features)
        
        X, y = [], []
        seq_length = 60
        for i in range(seq_length, len(scaled_data)):
            X.append(scaled_data[i-seq_length:i])
            y.append(scaled_data[i, 0])
        
        model = Sequential([
            LSTM(64, return_sequences=True, input_shape=(seq_length, scaled_data.shape[1])),
            Dropout(0.2),
            LSTM(32),
            Dense(1)
        ])
        model.compile(optimizer='adam', loss='mse')
        model.fit(np.array(X), np.array(y), epochs=10, batch_size=16, verbose=0)
        
        future_pred = model.predict(scaled_data[-seq_length:].reshape(1, seq_length, scaled_data.shape[1]))
        return float(scaler.inverse_transform(
            np.concatenate((future_pred, scaled_data[-1, 1:].reshape(1,-1)), axis=1)
        )[0][0])
    
    def analyze(self):
        try:
            data = self.get_data()
            current_price = float(data['Close'].iloc[-1])
            predicted_price = self.predict_price(data)
            
            signal = self._generate_signal(
                data,
                current_price,
                predicted_price
            )
            
            if signal != self.last_signal:
                self._send_notification(data, current_price, predicted_price, signal)
                self.last_signal = signal
            
        except Exception as e:
            print(f"⚠️ Error during analysis: {str(e)}")
            TelegramNotifier.send_message(f"❌ Error analyzing {self.symbol}:\n{str(e)}")
    
    def _generate_signal(self, data, current_price, predicted_price):
        last_rsi = float(data['RSI'].iloc[-1])
        macd_cross = bool(data['MACD'].iloc[-1] > data['MACD_Signal'].iloc[-1])
        bullish_engulf = bool(data['Bullish_Engulfing'].iloc[-1])
        bearish_engulf = bool(data['Bearish_Engulfing'].iloc[-1])
        
        conditions = {
            "🟢 STRONG BUY": (
                predicted_price > current_price * 1.02,
                last_rsi < 70,
                macd_cross,
                bullish_engulf
            ),
            "🔴 STRONG SELL": (
                predicted_price < current_price * 0.98,
                last_rsi > 30,
                not macd_cross,
                bearish_engulf
            )
        }
        
        for signal, conds in conditions.items():
            if all(conds):
                return signal
        return "🟡 NEUTRAL"
    
    def _send_notification(self, data, current_price, predicted_price, signal):
        message = (
            f"📊 *{self.symbol} Signal* ({self.timeframe})\n"
            f"💰 Price: ${current_price:.2f}\n"
            f"🔮 Predicted: ${predicted_price:.2f}\n"
            f"📈 RSI: {float(data['RSI'].iloc[-1]):.1f}\n"
            f"🎯 *Signal: {signal}*\n"
            f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        )
        print("\n" + message.replace("*", ""))
        TelegramNotifier.send_message(message)

# ==================== MAIN EXECUTION ====================
if __name__ == "__main__":
    symbol, timeframe, check_interval = get_user_input()
    bot = AITradingBot(symbol, timeframe)
    
    print(f"\n{'='*50}")
    print(f"🚀 Starting AI Trading Bot")
    print(f"📈 Asset: {symbol}")
    print(f"⏰ Timeframe: {timeframe}")
    print(f"🔔 Checking every: {check_interval//60} minutes")
    print(f"💬 Telegram alerts: Enabled")
    print(f"{'='*50}\n")
    print("🔄 Bot is running... Press Ctrl+C to stop\n")
    
    try:
        while True:
            bot.analyze()
            time.sleep(check_interval)
    except KeyboardInterrupt:
        print("\n🛑 Bot stopped by user")
        TelegramNotifier.send_message(f"🤖 *Bot Stopped*\n{symbol} monitoring ended")
