"""
Tests for technical indicators calculation.
"""

import pytest
import numpy as np
from datetime import datetime
from app.indicators.calculator import IndicatorCalculator
from app.schemas import CandleData


class TestIndicatorCalculator:
    """Test technical indicators calculation."""
    
    def test_ema_calculation(self):
        """Test EMA calculation."""
        prices = [100, 102, 101, 103, 105, 104, 106, 108, 107, 109]
        ema_values = IndicatorCalculator.calculate_ema(prices, 5)
        
        # First 4 values should be None (insufficient data)
        assert ema_values[0] is None
        assert ema_values[1] is None
        assert ema_values[2] is None
        assert ema_values[3] is None
        
        # 5th value should be SMA
        expected_sma = sum(prices[:5]) / 5
        assert abs(ema_values[4] - expected_sma) < 0.01
        
        # Subsequent values should be EMA
        assert ema_values[5] is not None
        assert ema_values[6] is not None
    
    def test_rsi_calculation(self):
        """Test RSI calculation."""
        prices = [100, 102, 101, 103, 105, 104, 106, 108, 107, 109, 111, 110, 112, 114, 113]
        rsi_values = IndicatorCalculator.calculate_rsi(prices, 14)
        
        # First 14 values should be None (insufficient data)
        for i in range(14):
            assert rsi_values[i] is None
        
        # 15th value should be calculated
        assert rsi_values[14] is not None
        assert 0 <= rsi_values[14] <= 100
    
    def test_macd_calculation(self):
        """Test MACD calculation."""
        prices = [100, 102, 101, 103, 105, 104, 106, 108, 107, 109, 111, 110, 112, 114, 113, 115, 117, 116, 118, 120, 119, 121, 123, 122, 124, 126, 125, 127, 129, 128]
        macd_line, signal_line, histogram = IndicatorCalculator.calculate_macd(prices)
        
        # First 25 values should be None (insufficient data for slow EMA)
        for i in range(25):
            assert macd_line[i] is None
            assert signal_line[i] is None
            assert histogram[i] is None
        
        # Subsequent values should be calculated
        assert macd_line[25] is not None
        assert signal_line[25] is not None
        assert histogram[25] is not None
    
    def test_atr_calculation(self):
        """Test ATR calculation."""
        candles = [
            CandleData(timestamp=datetime.now(), open=100, high=105, low=95, close=102, volume=1000),
            CandleData(timestamp=datetime.now(), open=102, high=108, low=98, close=106, volume=1200),
            CandleData(timestamp=datetime.now(), open=106, high=110, low=104, close=108, volume=1100),
            CandleData(timestamp=datetime.now(), open=108, high=112, low=106, close=110, volume=1300),
            CandleData(timestamp=datetime.now(), open=110, high=115, low=108, close=113, volume=1400),
            CandleData(timestamp=datetime.now(), open=113, high=118, low=111, close=116, volume=1500),
            CandleData(timestamp=datetime.now(), open=116, high=120, low=114, close=118, volume=1600),
            CandleData(timestamp=datetime.now(), open=118, high=122, low=116, close=120, volume=1700),
            CandleData(timestamp=datetime.now(), open=120, high=125, low=118, close=123, volume=1800),
            CandleData(timestamp=datetime.now(), open=123, high=127, low=121, close=125, volume=1900),
            CandleData(timestamp=datetime.now(), open=125, high=130, low=123, close=128, volume=2000),
            CandleData(timestamp=datetime.now(), open=128, high=132, low=126, close=130, volume=2100),
            CandleData(timestamp=datetime.now(), open=130, high=135, low=128, close=133, volume=2200),
            CandleData(timestamp=datetime.now(), open=133, high=137, low=131, close=135, volume=2300),
            CandleData(timestamp=datetime.now(), open=135, high=140, low=133, close=138, volume=2400)
        ]
        
        atr_values = IndicatorCalculator.calculate_atr(candles, 14)
        
        # First 14 values should be None (insufficient data)
        for i in range(14):
            assert atr_values[i] is None
        
        # 15th value should be calculated
        assert atr_values[14] is not None
        assert atr_values[14] > 0
    
    def test_calculate_all_indicators(self):
        """Test calculation of all indicators."""
        candles = [
            CandleData(timestamp=datetime.now(), open=100, high=105, low=95, close=102, volume=1000),
            CandleData(timestamp=datetime.now(), open=102, high=108, low=98, close=106, volume=1200),
            CandleData(timestamp=datetime.now(), open=106, high=110, low=104, close=108, volume=1100),
            CandleData(timestamp=datetime.now(), open=108, high=112, low=106, close=110, volume=1300),
            CandleData(timestamp=datetime.now(), open=110, high=115, low=108, close=113, volume=1400),
            CandleData(timestamp=datetime.now(), open=113, high=118, low=111, close=116, volume=1500),
            CandleData(timestamp=datetime.now(), open=116, high=120, low=114, close=118, volume=1600),
            CandleData(timestamp=datetime.now(), open=118, high=122, low=116, close=120, volume=1700),
            CandleData(timestamp=datetime.now(), open=120, high=125, low=118, close=123, volume=1800),
            CandleData(timestamp=datetime.now(), open=123, high=127, low=121, close=125, volume=1900),
            CandleData(timestamp=datetime.now(), open=125, high=130, low=123, close=128, volume=2000),
            CandleData(timestamp=datetime.now(), open=128, high=132, low=126, close=130, volume=2100),
            CandleData(timestamp=datetime.now(), open=130, high=135, low=128, close=133, volume=2200),
            CandleData(timestamp=datetime.now(), open=133, high=137, low=131, close=135, volume=2300),
            CandleData(timestamp=datetime.now(), open=135, high=140, low=133, close=138, volume=2400),
            CandleData(timestamp=datetime.now(), open=138, high=142, low=136, close=140, volume=2500),
            CandleData(timestamp=datetime.now(), open=140, high=145, low=138, close=143, volume=2600),
            CandleData(timestamp=datetime.now(), open=143, high=147, low=141, close=145, volume=2700),
            CandleData(timestamp=datetime.now(), open=145, high=150, low=143, close=148, volume=2800),
            CandleData(timestamp=datetime.now(), open=148, high=152, low=146, close=150, volume=2900),
            CandleData(timestamp=datetime.now(), open=150, high=155, low=148, close=153, volume=3000),
            CandleData(timestamp=datetime.now(), open=153, high=157, low=151, close=155, volume=3100),
            CandleData(timestamp=datetime.now(), open=155, high=160, low=153, close=158, volume=3200),
            CandleData(timestamp=datetime.now(), open=158, high=162, low=156, close=160, volume=3300),
        ]
        
        indicators = IndicatorCalculator.calculate_all_indicators(candles)
        
        # All indicators should be calculated (some may be None due to insufficient data)
        assert indicators is not None
        # At least some indicators should have values
        assert any([
            indicators.ema_20 is not None,
            indicators.ema_50 is not None,
            indicators.rsi is not None,
            indicators.macd is not None,
            indicators.atr is not None
        ])
    
    def test_empty_candles(self):
        """Test with empty candle list."""
        indicators = IndicatorCalculator.calculate_all_indicators([])
        
        assert indicators is not None
        assert indicators.ema_20 is None
        assert indicators.ema_50 is None
        assert indicators.rsi is None
        assert indicators.macd is None
        assert indicators.atr is None

