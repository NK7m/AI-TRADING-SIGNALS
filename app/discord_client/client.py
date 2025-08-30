"""
Discord client for sending trading signals.
"""

import asyncio
import aiohttp
from typing import Optional, Dict, Any
from loguru import logger
from ..schemas import Signal
from ..config import get_config
from .formatter import DiscordFormatter


class DiscordClient:
    """Discord client for sending trading signals."""
    
    def __init__(self):
        self.config = get_config()
        self.formatter = DiscordFormatter()
        self._session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        """Async context manager entry."""
        self._session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self._session:
            await self._session.close()
    
    async def send_signal(self, signal: Signal, last_signal: Optional[Signal] = None) -> bool:
        """Send a trading signal to Discord."""
        try:
            if self.config.discord.mode == "webhook":
                return await self._send_webhook_signal(signal, last_signal)
            elif self.config.discord.mode == "bot":
                return await self._send_bot_signal(signal, last_signal)
            else:
                logger.error(f"Unknown Discord mode: {self.config.discord.mode}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending signal to Discord: {e}")
            return False
    
    async def send_heartbeat(self, symbol: str, timeframe: str, current_price: float, 
                           last_signal: Optional[Signal] = None) -> bool:
        """Send a neutral heartbeat message."""
        try:
            if self.config.discord.mode == "webhook":
                return await self._send_webhook_heartbeat(symbol, timeframe, current_price, last_signal)
            elif self.config.discord.mode == "bot":
                return await self._send_bot_heartbeat(symbol, timeframe, current_price, last_signal)
            else:
                logger.error(f"Unknown Discord mode: {self.config.discord.mode}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending heartbeat to Discord: {e}")
            return False
    
    async def _send_webhook_signal(self, signal: Signal, last_signal: Optional[Signal] = None) -> bool:
        """Send signal via webhook."""
        if not self.config.discord.webhook_url:
            logger.error("Discord webhook URL not configured")
            return False
        
        # Format the message
        embed = self.formatter.format_signal_embed(signal, last_signal)
        
        # Build payload
        payload = {
            "embeds": [embed]
        }
        
        # Add traders mention if confidence is high enough
        if self.formatter.should_mention_traders(signal):
            payload["content"] = self.formatter.get_traders_mention()
        
        # Send webhook
        if not self._session:
            self._session = aiohttp.ClientSession()
        
        async with self._session.post(self.config.discord.webhook_url, json=payload) as response:
            if response.status == 204:
                logger.info(f"Signal sent to Discord: {signal.signal} for {signal.symbol}")
                return True
            else:
                logger.error(f"Discord webhook error: {response.status}")
                return False
    
    async def _send_webhook_heartbeat(self, symbol: str, timeframe: str, current_price: float,
                                    last_signal: Optional[Signal] = None) -> bool:
        """Send heartbeat via webhook."""
        if not self.config.discord.webhook_url:
            logger.error("Discord webhook URL not configured")
            return False
        
        # Format the message
        embed = self.formatter.format_heartbeat_message(symbol, timeframe, current_price, last_signal)
        
        # Build payload
        payload = {
            "embeds": [embed]
        }
        
        # Send webhook
        if not self._session:
            self._session = aiohttp.ClientSession()
        
        async with self._session.post(self.config.discord.webhook_url, json=payload) as response:
            if response.status == 204:
                logger.info(f"Heartbeat sent to Discord: {symbol} {timeframe}")
                return True
            else:
                logger.error(f"Discord webhook error: {response.status}")
                return False
    
    async def _send_bot_signal(self, signal: Signal, last_signal: Optional[Signal] = None) -> bool:
        """Send signal via bot (placeholder for future implementation)."""
        logger.warning("Bot mode not implemented yet, falling back to webhook")
        return await self._send_webhook_signal(signal, last_signal)
    
    async def _send_bot_heartbeat(self, symbol: str, timeframe: str, current_price: float,
                                last_signal: Optional[Signal] = None) -> bool:
        """Send heartbeat via bot (placeholder for future implementation)."""
        logger.warning("Bot mode not implemented yet, falling back to webhook")
        return await self._send_webhook_heartbeat(symbol, timeframe, current_price, last_signal)

