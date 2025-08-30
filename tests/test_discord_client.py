"""
Tests for Discord client.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from app.discord_client.client import DiscordClient
from app.discord_client.formatter import DiscordFormatter
from app.schemas import Signal, ValidationData, SignalMetadata


class TestDiscordFormatter:
    """Test Discord message formatting."""
    
    def test_format_signal_embed(self, sample_signal):
        """Test signal embed formatting."""
        formatter = DiscordFormatter()
        embed = formatter.format_signal_embed(sample_signal)
        
        assert embed["title"] == "BUY (85%) — BTCUSDT 15m"
        assert embed["color"] == 0x00ff00  # Green for BUY
        assert "Reason" in [field["name"] for field in embed["fields"]]
        assert "Stop Loss" in [field["name"] for field in embed["fields"]]
        assert "Take Profits" in [field["name"] for field in embed["fields"]]
        assert "Support Levels" in [field["name"] for field in embed["fields"]]
        assert "Resistance Levels" in [field["name"] for field in embed["fields"]]
        assert "Model / Latency" in [field["name"] for field in embed["fields"]]
        assert "Timestamp" in [field["name"] for field in embed["fields"]]
    
    def test_format_sell_signal_embed(self):
        """Test SELL signal embed formatting."""
        signal = Signal(
            symbol="BTCUSDT",
            timeframe="15m",
            signal="SELL",
            confidence=0.75,
            reasoning="Bearish momentum detected",
            validation=ValidationData(),
            metadata=SignalMetadata(
                latency_ms=1200,
                model="gemini-1.5-pro",
                version="1.0.0"
            )
        )
        
        formatter = DiscordFormatter()
        embed = formatter.format_signal_embed(signal)
        
        assert embed["title"] == "SELL (75%) — BTCUSDT 15m"
        assert embed["color"] == 0xff0000  # Red for SELL
    
    def test_format_neutral_signal_embed(self):
        """Test NEUTRAL signal embed formatting."""
        signal = Signal(
            symbol="BTCUSDT",
            timeframe="15m",
            signal="NEUTRAL",
            confidence=0.5,
            reasoning="No clear direction",
            validation=ValidationData(),
            metadata=SignalMetadata(
                latency_ms=1000,
                model="gemini-1.5-pro",
                version="1.0.0"
            )
        )
        
        formatter = DiscordFormatter()
        embed = formatter.format_signal_embed(signal)
        
        assert embed["title"] == "NEUTRAL (50%) — BTCUSDT 15m"
        assert embed["color"] == 0x808080  # Gray for NEUTRAL
    
    def test_format_heartbeat_message(self):
        """Test heartbeat message formatting."""
        formatter = DiscordFormatter()
        embed = formatter.format_heartbeat_message("BTCUSDT", "15m", 108.5)
        
        assert embed["title"] == "NEUTRAL — BTCUSDT 15m"
        assert embed["color"] == 0x808080
        assert "NEUTRAL | BTCUSDT 15m" in embed["description"]
        assert "price: 108.5000" in embed["description"]
        assert "Health OK ✅" in embed["description"]
    
    def test_should_mention_traders(self):
        """Test traders mention logic."""
        formatter = DiscordFormatter()
        
        # High confidence signal
        high_confidence_signal = Signal(
            symbol="BTCUSDT",
            timeframe="15m",
            signal="BUY",
            confidence=0.85,  # Above threshold
            reasoning="Strong signal",
            validation=ValidationData(),
            metadata=SignalMetadata(
                latency_ms=1000,
                model="gemini-1.5-pro",
                version="1.0.0"
            )
        )
        
        assert formatter.should_mention_traders(high_confidence_signal) is True
        
        # Low confidence signal
        low_confidence_signal = Signal(
            symbol="BTCUSDT",
            timeframe="15m",
            signal="BUY",
            confidence=0.65,  # Below threshold
            reasoning="Weak signal",
            validation=ValidationData(),
            metadata=SignalMetadata(
                latency_ms=1000,
                model="gemini-1.5-pro",
                version="1.0.0"
            )
        )
        
        assert formatter.should_mention_traders(low_confidence_signal) is False
    
    def test_get_traders_mention(self):
        """Test traders mention string generation."""
        formatter = DiscordFormatter()
        
        # Test name mode
        formatter.config.app.role_mention.mode = "name"
        formatter.config.app.role_mention.value = "@traders"
        assert formatter.get_traders_mention() == "@traders"
        
        # Test ID mode
        formatter.config.app.role_mention.mode = "id"
        formatter.config.app.role_mention.value = "123456789012345678"
        assert formatter.get_traders_mention() == "<@&123456789012345678>"


class TestDiscordClient:
    """Test Discord client functionality."""
    
    @pytest.fixture
    def mock_config(self):
        """Mock configuration for testing."""
        config = Mock()
        config.discord.mode = "webhook"
        config.discord.webhook_url = "https://discord.com/api/webhooks/test"
        config.discord.embeds = True
        config.app.role_mention.mode = "name"
        config.app.role_mention.value = "@traders"
        config.app.min_confidence_tag = 0.75
        return config
    
    @patch('app.discord_client.client.get_config')
    @patch('aiohttp.ClientSession.post')
    async def test_send_webhook_signal_success(self, mock_post, mock_get_config, sample_signal, mock_config):
        """Test successful webhook signal sending."""
        mock_get_config.return_value = mock_config
        
        # Mock successful response
        mock_response = AsyncMock()
        mock_response.status = 204
        mock_post.return_value.__aenter__.return_value = mock_response
        
        client = DiscordClient()
        success = await client._send_webhook_signal(sample_signal)
        
        assert success is True
        mock_post.assert_called_once()
    
    @patch('app.discord_client.client.get_config')
    @patch('aiohttp.ClientSession.post')
    async def test_send_webhook_signal_failure(self, mock_post, mock_get_config, sample_signal, mock_config):
        """Test failed webhook signal sending."""
        mock_get_config.return_value = mock_config
        
        # Mock failed response
        mock_response = AsyncMock()
        mock_response.status = 400
        mock_post.return_value.__aenter__.return_value = mock_response
        
        client = DiscordClient()
        success = await client._send_webhook_signal(sample_signal)
        
        assert success is False
    
    @patch('app.discord_client.client.get_config')
    async def test_send_webhook_no_url(self, mock_get_config, sample_signal):
        """Test webhook sending with no URL configured."""
        config = Mock()
        config.discord.mode = "webhook"
        config.discord.webhook_url = None
        mock_get_config.return_value = config
        
        client = DiscordClient()
        success = await client._send_webhook_signal(sample_signal)
        
        assert success is False
    
    @patch('app.discord_client.client.get_config')
    @patch('aiohttp.ClientSession.post')
    async def test_send_webhook_heartbeat_success(self, mock_post, mock_get_config, mock_config):
        """Test successful webhook heartbeat sending."""
        mock_get_config.return_value = mock_config
        
        # Mock successful response
        mock_response = AsyncMock()
        mock_response.status = 204
        mock_post.return_value.__aenter__.return_value = mock_response
        
        client = DiscordClient()
        success = await client._send_webhook_heartbeat("BTCUSDT", "15m", 108.5)
        
        assert success is True
        mock_post.assert_called_once()
    
    @patch('app.discord_client.client.get_config')
    async def test_send_signal_webhook_mode(self, mock_get_config, sample_signal, mock_config):
        """Test send_signal in webhook mode."""
        mock_get_config.return_value = mock_config
        
        with patch.object(DiscordClient, '_send_webhook_signal', return_value=True) as mock_webhook:
            client = DiscordClient()
            success = await client.send_signal(sample_signal)
            
            assert success is True
            mock_webhook.assert_called_once_with(sample_signal, None)
    
    @patch('app.discord_client.client.get_config')
    async def test_send_heartbeat_webhook_mode(self, mock_get_config, mock_config):
        """Test send_heartbeat in webhook mode."""
        mock_get_config.return_value = mock_config
        
        with patch.object(DiscordClient, '_send_webhook_heartbeat', return_value=True) as mock_webhook:
            client = DiscordClient()
            success = await client.send_heartbeat("BTCUSDT", "15m", 108.5)
            
            assert success is True
            mock_webhook.assert_called_once_with("BTCUSDT", "15m", 108.5, None)

