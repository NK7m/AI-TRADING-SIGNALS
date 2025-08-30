"""
Base data source interface for the AI Trading Signals Bot.
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import datetime
from ..schemas import CandleData, MarketData


class DataSource(ABC):
    """Abstract base class for data sources."""
    
    def __init__(self, symbol: str, interval: str):
        self.symbol = symbol
        self.interval = interval
    
    @abstractmethod
    async def fetch_candles(self, limit: int = 300) -> List[CandleData]:
        """Fetch OHLCV candle data."""
        pass
    
    @abstractmethod
    async def get_current_price(self) -> float:
        """Get the current price of the symbol."""
        pass
    
    async def fetch_market_data(self, limit: int = 300) -> MarketData:
        """Fetch complete market data including candles and current price."""
        candles = await self.fetch_candles(limit)
        current_price = await self.get_current_price()
        
        return MarketData(
            symbol=self.symbol,
            timeframe=self.interval,
            candles=candles,
            indicators=None,  # Will be calculated separately
            current_price=current_price,
            headlines=[]  # Will be populated by news source if available
        )
    
    def _parse_interval(self, interval: str) -> str:
        """Parse interval string to data source specific format."""
        interval_map = {
            "1m": "1m",
            "5m": "5m", 
            "15m": "15m",
            "30m": "30m",
            "1h": "1h",
            "4h": "4h",
            "1d": "1d"
        }
        return interval_map.get(interval, interval)

