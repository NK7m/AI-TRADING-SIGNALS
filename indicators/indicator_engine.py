import yfinance as yf
import pandas_ta as ta

class IndicatorEngine:
    def fetch_data(self, ticker, interval):
        data = yf.download(ticker, period='1mo', interval=interval)
        return data

    def compute_features(self, data):
        data['rsi'] = ta.rsi(data['Close'])
        data['macd'] = ta.macd(data['Close'])['MACD_12_26_9']
        data['ema'] = ta.ema(data['Close'])
        data['sma'] = ta.sma(data['Close'])
        data['bb_upper'] = ta.bbands(data['Close'])['BBU_20_2.0']
        data['bb_lower'] = ta.bbands(data['Close'])['BBL_20_2.0']
        # Add more features as needed
        latest = data.iloc[-1]
        return [
            latest['rsi'], latest['macd'], latest['ema'],
            latest['sma'], latest['bb_upper'], latest['bb_lower']
        ]