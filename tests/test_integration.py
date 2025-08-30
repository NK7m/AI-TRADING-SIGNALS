"""
Integration tests for the AI Trading Signals Bot.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from app.scheduler import SignalScheduler
from app.schemas import AssetConfig


class TestIntegration:
    """Integration tests for the trading bot."""
    
    @pytest.fixture
    def mock_config(self):
        """Mock configuration for integration tests."""
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
        config.data.sources = [
            AssetConfig(symbol="BTCUSDT", kind="binance", interval="15m")
        ]
        
        config.server.host = "0.0.0.0"
        config.server.port = 8080
        
        config.metrics.enabled = True
        config.metrics.path = "/metrics"
        
        return config
    
    @patch('app.scheduler.signal_scheduler.get_config')
    @patch('app.scheduler.signal_scheduler.DataSourceFactory')
    @patch('app.scheduler.signal_scheduler.IndicatorCalculator')
    @patch('app.scheduler.signal_scheduler.GeminiSignalEngine')
    @patch('app.scheduler.signal_scheduler.DiscordClient')
    async def test_signal_generation_flow(self, mock_discord, mock_gemini, mock_indicators, 
                                        mock_data_factory, mock_get_config, mock_config):
        """Test the complete signal generation flow."""
        mock_get_config.return_value = mock_config
        
        # Mock data source
        mock_data_source = AsyncMock()
        mock_data_source.fetch_market_data.return_value = Mock(
            symbol="BTCUSDT",
            timeframe="15m",
            candles=[Mock()],
            indicators=None,
            current_price=108.0,
            headlines=[]
        )
        mock_data_factory.create_source.return_value = mock_data_source
        
        # Mock indicators
        mock_indicators.calculate_all_indicators.return_value = Mock()
        
        # Mock signal engine
        mock_signal = Mock()
        mock_signal.symbol = "BTCUSDT"
        mock_signal.timeframe = "15m"
        mock_signal.signal = "BUY"
        mock_signal.confidence = 0.85
        mock_gemini.return_value.generate_signal.return_value = mock_signal
        
        # Mock Discord client
        mock_discord_instance = AsyncMock()
        mock_discord_instance.send_signal.return_value = True
        mock_discord.return_value.__aenter__.return_value = mock_discord_instance
        
        # Create scheduler and test
        scheduler = SignalScheduler()
        signal = await scheduler.generate_signal_once("BTCUSDT", "15m")
        
        assert signal is not None
        assert signal.symbol == "BTCUSDT"
        assert signal.signal == "BUY"
        assert signal.confidence == 0.85
    
    @patch('app.scheduler.signal_scheduler.get_config')
    async def test_scheduler_status(self, mock_get_config, mock_config):
        """Test scheduler status functionality."""
        mock_get_config.return_value = mock_config
        
        scheduler = SignalScheduler()
        
        # Test initial status
        status = scheduler.get_status()
        assert status["running"] is False
        assert status["next_runs"] == {}
        assert status["last_signals"] == {}
        
        # Test after starting (mocked)
        scheduler.running = True
        scheduler.last_signals["BTCUSDT_15m"] = Mock()
        
        status = scheduler.get_status()
        assert status["running"] is True
        assert "BTCUSDT_15m" in status["last_signals"]
    
    @patch('app.scheduler.signal_scheduler.get_config')
    @patch('app.scheduler.signal_scheduler.DataSourceFactory')
    async def test_signal_generation_no_data(self, mock_data_factory, mock_get_config, mock_config):
        """Test signal generation with no market data."""
        mock_get_config.return_value = mock_config
        
        # Mock data source with no data
        mock_data_source = AsyncMock()
        mock_data_source.fetch_market_data.return_value = Mock(
            symbol="BTCUSDT",
            timeframe="15m",
            candles=[],  # No candles
            indicators=None,
            current_price=0.0,
            headlines=[]
        )
        mock_data_factory.create_source.return_value = mock_data_source
        
        scheduler = SignalScheduler()
        signal = await scheduler.generate_signal_once("BTCUSDT", "15m")
        
        assert signal is None
    
    @patch('app.scheduler.signal_scheduler.get_config')
    @patch('app.scheduler.signal_scheduler.DataSourceFactory')
    @patch('app.scheduler.signal_scheduler.IndicatorCalculator')
    @patch('app.scheduler.signal_scheduler.GeminiSignalEngine')
    async def test_signal_generation_engine_failure(self, mock_gemini, mock_indicators, 
                                                  mock_data_factory, mock_get_config, mock_config):
        """Test signal generation when engine fails."""
        mock_get_config.return_value = mock_config
        
        # Mock data source
        mock_data_source = AsyncMock()
        mock_data_source.fetch_market_data.return_value = Mock(
            symbol="BTCUSDT",
            timeframe="15m",
            candles=[Mock()],
            indicators=None,
            current_price=108.0,
            headlines=[]
        )
        mock_data_factory.create_source.return_value = mock_data_source
        
        # Mock indicators
        mock_indicators.calculate_all_indicators.return_value = Mock()
        
        # Mock signal engine failure
        mock_gemini.return_value.generate_signal.return_value = None
        
        scheduler = SignalScheduler()
        signal = await scheduler.generate_signal_once("BTCUSDT", "15m")
        
        assert signal is None

