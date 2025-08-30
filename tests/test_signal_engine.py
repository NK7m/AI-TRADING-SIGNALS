"""
Tests for signal engine.
"""

import pytest
import json
from unittest.mock import Mock, patch, AsyncMock
from app.signal_engine.gemini_engine import GeminiSignalEngine
from app.signal_engine.prompt_builder import PromptBuilder
from app.schemas import MarketData, CandleData, IndicatorData


class TestPromptBuilder:
    """Test prompt builder functionality."""
    
    def test_build_user_prompt(self, sample_market_data):
        """Test user prompt building."""
        prompt = PromptBuilder.build_user_prompt(sample_market_data)
        
        assert "BTCUSDT" in prompt
        assert "15m" in prompt
        assert "108.0000" in prompt  # current_price
        assert "EMA20" in prompt
        assert "RSI" in prompt
        assert "REQUIRED JSON SCHEMA" in prompt
    
    def test_compress_candles(self, sample_market_data):
        """Test candle compression."""
        compressed = PromptBuilder._compress_candles(sample_market_data.candles)
        
        assert "O:" in compressed
        assert "H:" in compressed
        assert "L:" in compressed
        assert "C:" in compressed
        assert "V:" in compressed
    
    def test_build_indicators_summary(self, sample_indicator_data):
        """Test indicators summary building."""
        summary = PromptBuilder._build_indicators_summary(sample_indicator_data)
        
        assert "EMA20: 105.5000" in summary
        assert "EMA50: 103.2000" in summary
        assert "RSI: 65.50" in summary
        assert "MACD: 0.8000" in summary
        assert "ATR: 2.5000" in summary
    
    def test_build_headlines_summary(self):
        """Test headlines summary building."""
        headlines = [
            "Bitcoin reaches new high",
            "Market volatility increases significantly",
            "Trading volume spikes"
        ]
        
        summary = PromptBuilder._build_headlines_summary(headlines)
        
        assert "Bitcoin reaches new high" in summary
        assert "Market volatility increases" in summary
        assert "Trading volume spikes" in summary
    
    def test_get_schema_text(self):
        """Test schema text generation."""
        schema_text = PromptBuilder._get_schema_text()
        
        # Should be valid JSON
        schema = json.loads(schema_text)
        
        assert "symbol" in schema
        assert "timeframe" in schema
        assert "signal" in schema
        assert "confidence" in schema
        assert "reasoning" in schema
        assert "validation" in schema
        assert "metadata" in schema


class TestGeminiSignalEngine:
    """Test Gemini signal engine."""
    
    @pytest.fixture
    def mock_gemini_response(self):
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
    
    @patch('app.signal_engine.gemini_engine.genai')
    def test_parse_response(self, mock_genai, mock_gemini_response):
        """Test response parsing."""
        engine = GeminiSignalEngine()
        
        # Test valid JSON response
        response_text = json.dumps(mock_gemini_response)
        signal = engine._parse_response(response_text, None, 0)
        
        assert signal is not None
        assert signal.symbol == "BTCUSDT"
        assert signal.timeframe == "15m"
        assert signal.signal == "BUY"
        assert signal.confidence == 0.85
        assert signal.reasoning == "Strong bullish momentum with RSI above 60 and MACD crossover"
        assert signal.validation.support_levels == [105.0, 100.0]
        assert signal.validation.resistance_levels == [110.0, 115.0]
        assert signal.validation.stop_loss == 102.0
        assert signal.validation.take_profits == [112.0, 118.0]
    
    @patch('app.signal_engine.gemini_engine.genai')
    def test_parse_invalid_json(self, mock_genai):
        """Test parsing invalid JSON response."""
        engine = GeminiSignalEngine()
        
        # Test invalid JSON
        response_text = "invalid json"
        signal = engine._parse_response(response_text, None, 0)
        
        assert signal is None
    
    @patch('app.signal_engine.gemini_engine.genai')
    def test_parse_missing_fields(self, mock_genai):
        """Test parsing response with missing fields."""
        engine = GeminiSignalEngine()
        
        # Test missing required fields
        response_text = json.dumps({"symbol": "BTCUSDT"})
        signal = engine._parse_response(response_text, None, 0)
        
        assert signal is None
    
    @patch('app.signal_engine.gemini_engine.genai')
    def test_parse_invalid_signal_type(self, mock_genai):
        """Test parsing response with invalid signal type."""
        engine = GeminiSignalEngine()
        
        # Test invalid signal type
        response_text = json.dumps({
            "symbol": "BTCUSDT",
            "timeframe": "15m",
            "signal": "INVALID",
            "confidence": 0.85,
            "reasoning": "Test"
        })
        signal = engine._parse_response(response_text, None, 0)
        
        assert signal is None
    
    @patch('app.signal_engine.gemini_engine.genai')
    def test_parse_invalid_confidence(self, mock_genai):
        """Test parsing response with invalid confidence."""
        engine = GeminiSignalEngine()
        
        # Test invalid confidence
        response_text = json.dumps({
            "symbol": "BTCUSDT",
            "timeframe": "15m",
            "signal": "BUY",
            "confidence": 1.5,  # Invalid: > 1.0
            "reasoning": "Test"
        })
        signal = engine._parse_response(response_text, None, 0)
        
        assert signal is None
    
    @patch('app.signal_engine.gemini_engine.genai')
    def test_parse_markdown_response(self, mock_genai, mock_gemini_response):
        """Test parsing response with markdown code blocks."""
        engine = GeminiSignalEngine()
        
        # Test response with markdown code blocks
        response_text = f"```json\n{json.dumps(mock_gemini_response)}\n```"
        signal = engine._parse_response(response_text, None, 0)
        
        assert signal is not None
        assert signal.symbol == "BTCUSDT"
        assert signal.signal == "BUY"

