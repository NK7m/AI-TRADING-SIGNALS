"""
Technical indicators calculator implementation.
"""

import numpy as np
from typing import List, Optional
from ..schemas import CandleData, IndicatorData


class IndicatorCalculator:
    """Calculates technical indicators from OHLCV data."""
    
    @staticmethod
    def calculate_ema(prices: List[float], period: int) -> List[Optional[float]]:
        """Calculate Exponential Moving Average."""
        if len(prices) < period:
            return [None] * len(prices)
        
        ema_values = [None] * (period - 1)
        multiplier = 2 / (period + 1)
        
        # First EMA value is SMA
        sma = sum(prices[:period]) / period
        ema_values.append(sma)
        
        # Calculate subsequent EMA values
        for i in range(period, len(prices)):
            ema = (prices[i] * multiplier) + (ema_values[-1] * (1 - multiplier))
            ema_values.append(ema)
        
        return ema_values
    
    @staticmethod
    def calculate_rsi(prices: List[float], period: int = 14) -> List[Optional[float]]:
        """Calculate Relative Strength Index."""
        if len(prices) < period + 1:
            return [None] * len(prices)
        
        rsi_values = [None] * period
        
        # Calculate price changes
        deltas = [prices[i] - prices[i-1] for i in range(1, len(prices))]
        
        # Separate gains and losses
        gains = [delta if delta > 0 else 0 for delta in deltas]
        losses = [-delta if delta < 0 else 0 for delta in deltas]
        
        # Calculate initial average gain and loss
        avg_gain = sum(gains[:period]) / period
        avg_loss = sum(losses[:period]) / period
        
        if avg_loss == 0:
            rsi_values.append(100)
        else:
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
            rsi_values.append(rsi)
        
        # Calculate subsequent RSI values
        for i in range(period, len(deltas)):
            avg_gain = ((avg_gain * (period - 1)) + gains[i]) / period
            avg_loss = ((avg_loss * (period - 1)) + losses[i]) / period
            
            if avg_loss == 0:
                rsi_values.append(100)
            else:
                rs = avg_gain / avg_loss
                rsi = 100 - (100 / (1 + rs))
                rsi_values.append(rsi)
        
        return rsi_values
    
    @staticmethod
    def calculate_macd(prices: List[float], fast_period: int = 12, slow_period: int = 26, signal_period: int = 9) -> tuple:
        """Calculate MACD (Moving Average Convergence Divergence)."""
        if len(prices) < slow_period:
            return [None] * len(prices), [None] * len(prices), [None] * len(prices)
        
        # Calculate EMAs
        ema_fast = IndicatorCalculator.calculate_ema(prices, fast_period)
        ema_slow = IndicatorCalculator.calculate_ema(prices, slow_period)
        
        # Calculate MACD line
        macd_line = []
        for i in range(len(prices)):
            if ema_fast[i] is not None and ema_slow[i] is not None:
                macd_line.append(ema_fast[i] - ema_slow[i])
            else:
                macd_line.append(None)
        
        # Calculate signal line (EMA of MACD)
        macd_values = [v for v in macd_line if v is not None]
        if len(macd_values) >= signal_period:
            signal_line = IndicatorCalculator.calculate_ema(macd_values, signal_period)
            # Pad with None values to match original length
            signal_line = [None] * (len(macd_line) - len(signal_line)) + signal_line
        else:
            signal_line = [None] * len(macd_line)
        
        # Calculate histogram
        histogram = []
        for i in range(len(macd_line)):
            if macd_line[i] is not None and signal_line[i] is not None:
                histogram.append(macd_line[i] - signal_line[i])
            else:
                histogram.append(None)
        
        return macd_line, signal_line, histogram
    
    @staticmethod
    def calculate_atr(candles: List[CandleData], period: int = 14) -> List[Optional[float]]:
        """Calculate Average True Range."""
        if len(candles) < period + 1:
            return [None] * len(candles)
        
        atr_values = [None] * period
        
        # Calculate True Range for each candle
        true_ranges = []
        for i in range(1, len(candles)):
            high = candles[i].high
            low = candles[i].low
            prev_close = candles[i-1].close
            
            tr1 = high - low
            tr2 = abs(high - prev_close)
            tr3 = abs(low - prev_close)
            
            true_ranges.append(max(tr1, tr2, tr3))
        
        # Calculate initial ATR (SMA of TR)
        atr = sum(true_ranges[:period]) / period
        atr_values.append(atr)
        
        # Calculate subsequent ATR values (smoothed)
        for i in range(period, len(true_ranges)):
            atr = ((atr * (period - 1)) + true_ranges[i]) / period
            atr_values.append(atr)
        
        return atr_values
    
    @classmethod
    def calculate_all_indicators(cls, candles: List[CandleData]) -> IndicatorData:
        """Calculate all technical indicators for the given candles."""
        if not candles:
            return IndicatorData()
        
        # Extract close prices
        close_prices = [candle.close for candle in candles]
        
        # Calculate indicators
        ema_20 = cls.calculate_ema(close_prices, 20)
        ema_50 = cls.calculate_ema(close_prices, 50)
        rsi = cls.calculate_rsi(close_prices, 14)
        macd_line, macd_signal, macd_histogram = cls.calculate_macd(close_prices)
        atr = cls.calculate_atr(candles, 14)
        
        # Get the latest values
        return IndicatorData(
            ema_20=ema_20[-1] if ema_20[-1] is not None else None,
            ema_50=ema_50[-1] if ema_50[-1] is not None else None,
            rsi=rsi[-1] if rsi[-1] is not None else None,
            macd=macd_line[-1] if macd_line[-1] is not None else None,
            macd_signal=macd_signal[-1] if macd_signal[-1] is not None else None,
            macd_histogram=macd_histogram[-1] if macd_histogram[-1] is not None else None,
            atr=atr[-1] if atr[-1] is not None else None
        )

