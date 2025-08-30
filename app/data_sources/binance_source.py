"""
Binance data source implementation.
"""

import asyncio
import aiohttp
from typing import List, Optional
from datetime import datetime
from loguru import logger
from .base import DataSource
from ..schemas import CandleData


class BinanceSource(DataSource):
    """Binance data source for cryptocurrency data."""
    
    BASE_URL = "https://api.binance.com"
    
    def __init__(self, symbol: str, interval: str):
        super().__init__(symbol, interval)
        self.symbol = symbol.replace("USDT", "").replace("BUSD", "") + "USDT"
    
    async def fetch_candles(self, limit: int = 300) -> List[CandleData]:
        """Fetch OHLCV candle data from Binance."""
        try:
            url = f"{self.BASE_URL}/api/v3/klines"
            params = {
                "symbol": self.symbol,
                "interval": self._convert_interval(),
                "limit": min(limit, 1000)  # Binance max limit is 1000
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status != 200:
                        logger.error(f"Binance API error: {response.status}")
                        return []
                    
                    data = await response.json()
            
            candles = []
            for kline in data:
                candle = CandleData(
                    timestamp=datetime.fromtimestamp(kline[0] / 1000),
                    open=float(kline[1]),
                    high=float(kline[2]),
                    low=float(kline[3]),
                    close=float(kline[4]),
                    volume=float(kline[5])
                )
                candles.append(candle)
            
            logger.info(f"Fetched {len(candles)} candles for {self.symbol}")
            return candles
            
        except Exception as e:
            logger.error(f"Error fetching candles for {self.symbol}: {e}")
            return []
    
    async def get_current_price(self) -> float:
        """Get the current price from Binance."""
        try:
            url = f"{self.BASE_URL}/api/v3/ticker/price"
            params = {"symbol": self.symbol}
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status != 200:
                        logger.error(f"Binance price API error: {response.status}")
                        return 0.0
                    
                    data = await response.json()
            
            return float(data["price"])
            
        except Exception as e:
            logger.error(f"Error getting current price for {self.symbol}: {e}")
            return 0.0
    
    def _convert_interval(self) -> str:
        """Convert interval to Binance format."""
        interval_map = {
            "1m": "1m",
            "5m": "5m",
            "15m": "15m",
            "30m": "30m",
            "1h": "1h",
            "4h": "4h",
            "1d": "1d"
        }
        return interval_map.get(self.interval, "1h")

