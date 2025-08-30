"""
Pytest configuration and fixtures for the AI Trading Signals Bot.
"""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import Mock, AsyncMock
from app.schemas import Signal, ValidationData, SignalMetadata, CandleData, IndicatorData, MarketData


@pytest.fixture
def sample_candle_data():
    """Sample candle data for testing."""
    return [
        CandleData(
            timestamp=datetime.now(),
            open=100.0,
            high=105.0,
            low=95.0,
            close=102.0,
            volume=1000.0
        ),
        CandleData(
            timestamp=datetime.now(),
            open=102.0,
            high=108.0,
            low=98.0,
            close=106.0,
            volume=1200.0
        ),
        CandleData(
            timestamp=datetime.now(),
            open=106.0,
            high=110.0,
            low=104.0,
            close=108.0,
            volume=1100.0
        )
    ]


@pytest.fixture
def sample_indicator_data():
    """Sample indicator data for testing."""
    return IndicatorData(
        ema_20=105.5,
        ema_50=103.2,
        rsi=65.5,
        macd=0.8,
        macd_signal=0.6,
        macd_histogram=0.2,
        atr=2.5
    )


@pytest.fixture
def sample_market_data(sample_candle_data, sample_indicator_data):
    """Sample market data for testing."""
    return MarketData(
        symbol="BTCUSDT",
        timeframe="15m",
        candles=sample_candle_data,
        indicators=sample_indicator_data,
        current_price=108.0,
        headlines=["Bitcoin reaches new high", "Market volatility increases"]
    )


@pytest.fixture
def sample_signal():
    """Sample trading signal for testing."""
    return Signal(
        symbol="BTCUSDT",
        timeframe="15m",
        signal="BUY",
        confidence=0.85,
        reasoning="Strong bullish momentum with RSI above 60 and MACD crossover",
        validation=ValidationData(
            support_levels=[105.0, 100.0],
            resistance_levels=[110.0, 115.0],
            stop_loss=102.0,
            take_profits=[112.0, 118.0]
        ),
        metadata=SignalMetadata(
            latency_ms=1500,
            model="gemini-1.5-pro",
            version="1.0.0"
        )
    )


@pytest.fixture
def mock_gemini_response():
    """Mock Gemini API response."""
    return {
        "symbol": "BTCUSDT",
        "timeframe": "15m",
        "signal": "BUY",
        "confidence": 0.85,
        "reasoning": "Strong bullish momentum with RSI above 60 and MACD crossover",
        "validation": {
            "support_levels": [105.0, 100.0],
            "resistance_levels": [110.0, 115.0],
            "stop_loss": 102.0,
            "take_profits": [112.0, 118.0]
        },
        "metadata": {
            "latency_ms": 1500,
            "model": "gemini-1.5-pro",
            "version": "1.0.0"
        }
    }


@pytest.fixture
def mock_config():
    """Mock configuration for testing."""
    config = Mock()
    config.app.timezone = "Asia/Kolkata"
    config.app.log_level = "INFO"
    config.app.neutral_heartbeat_minutes = 30
    config.app.min_confidence_tag = 0.75
    config.app.role_mention.mode = "name"
    config.app.role_mention.value = "@traders"
    
    config.discord.mode = "webhook"
    config.discord.webhook_url = "https://discord.com/api/webhooks/test"
    config.discord.embeds = True
    
    config.llm.provider = "gemini"
    config.llm.model = "gemini-1.5-pro"
    config.llm.api_key = "test-api-key"
    config.llm.request_timeout_seconds = 30
    config.llm.max_retries = 2
    
    config.data.default_interval = "15m"
    config.data.bars = 300
    config.data.sources = []
    
    config.server.host = "0.0.0.0"
    config.server.port = 8080
    
    config.metrics.enabled = True
    config.metrics.path = "/metrics"
    
    return config


@pytest.fixture
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

