"""
Tests for Pydantic schemas.
"""

import pytest
from decimal import Decimal
from datetime import datetime
from app.schemas import Signal, ValidationData, SignalMetadata, CandleData, IndicatorData


class TestSignal:
    """Test Signal schema validation."""
    
    def test_valid_signal(self):
        """Test valid signal creation."""
        signal = Signal(
            symbol="BTCUSDT",
            timeframe="15m",
            signal="BUY",
            confidence=Decimal("0.85"),
            reasoning="Strong bullish momentum",
            validation=ValidationData(),
            metadata=SignalMetadata(
                latency_ms=1500,
                model="gemini-1.5-pro",
                version="1.0.0"
            )
        )
        
        assert signal.symbol == "BTCUSDT"
        assert signal.timeframe == "15m"
        assert signal.signal == "BUY"
        assert signal.confidence == Decimal("0.85")
        assert signal.reasoning == "Strong bullish momentum"
    
    def test_invalid_signal_type(self):
        """Test invalid signal type."""
        with pytest.raises(ValueError):
            Signal(
                symbol="BTCUSDT",
                timeframe="15m",
                signal="INVALID",
                confidence=Decimal("0.85"),
                reasoning="Test",
                validation=ValidationData(),
                metadata=SignalMetadata(
                    latency_ms=1500,
                    model="gemini-1.5-pro",
                    version="1.0.0"
                )
            )
    
    def test_invalid_confidence_range(self):
        """Test confidence outside valid range."""
        with pytest.raises(ValueError):
            Signal(
                symbol="BTCUSDT",
                timeframe="15m",
                signal="BUY",
                confidence=Decimal("1.5"),  # Invalid: > 1.0
                reasoning="Test",
                validation=ValidationData(),
                metadata=SignalMetadata(
                    latency_ms=1500,
                    model="gemini-1.5-pro",
                    version="1.0.0"
                )
            )
    
    def test_empty_reasoning(self):
        """Test empty reasoning validation."""
        with pytest.raises(ValueError):
            Signal(
                symbol="BTCUSDT",
                timeframe="15m",
                signal="BUY",
                confidence=Decimal("0.85"),
                reasoning="",  # Empty reasoning
                validation=ValidationData(),
                metadata=SignalMetadata(
                    latency_ms=1500,
                    model="gemini-1.5-pro",
                    version="1.0.0"
                )
            )
    
    def test_symbol_normalization(self):
        """Test symbol normalization to uppercase."""
        signal = Signal(
            symbol="btcusdt",  # Lowercase
            timeframe="15m",
            signal="BUY",
            confidence=Decimal("0.85"),
            reasoning="Test",
            validation=ValidationData(),
            metadata=SignalMetadata(
                latency_ms=1500,
                model="gemini-1.5-pro",
                version="1.0.0"
            )
        )
        
        assert signal.symbol == "BTCUSDT"


class TestCandleData:
    """Test CandleData schema."""
    
    def test_valid_candle(self):
        """Test valid candle data creation."""
        candle = CandleData(
            timestamp=datetime.now(),
            open=100.0,
            high=105.0,
            low=95.0,
            close=102.0,
            volume=1000.0
        )
        
        assert candle.open == 100.0
        assert candle.high == 105.0
        assert candle.low == 95.0
        assert candle.close == 102.0
        assert candle.volume == 1000.0


class TestIndicatorData:
    """Test IndicatorData schema."""
    
    def test_valid_indicators(self):
        """Test valid indicator data creation."""
        indicators = IndicatorData(
            ema_20=105.5,
            ema_50=103.2,
            rsi=65.5,
            macd=0.8,
            macd_signal=0.6,
            macd_histogram=0.2,
            atr=2.5
        )
        
        assert indicators.ema_20 == 105.5
        assert indicators.ema_50 == 103.2
        assert indicators.rsi == 65.5
        assert indicators.macd == 0.8
        assert indicators.macd_signal == 0.6
        assert indicators.macd_histogram == 0.2
        assert indicators.atr == 2.5
    
    def test_optional_indicators(self):
        """Test indicators with optional values."""
        indicators = IndicatorData()
        
        assert indicators.ema_20 is None
        assert indicators.ema_50 is None
        assert indicators.rsi is None
        assert indicators.macd is None
        assert indicators.macd_signal is None
        assert indicators.macd_histogram is None
        assert indicators.atr is None

