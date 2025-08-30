"""
Yahoo Finance data source implementation.
"""

import asyncio
from typing import List, Optional
from datetime import datetime, timedelta
import yfinance as yf
from loguru import logger
from .base import DataSource
from ..schemas import CandleData


class YFinanceSource(DataSource):
    """Yahoo Finance data source for stocks and ETFs."""
    
    def __init__(self, symbol: str, interval: str):
        super().__init__(symbol, interval)
        self.ticker = yf.Ticker(symbol)
    
    async def fetch_candles(self, limit: int = 300) -> List[CandleData]:
        """Fetch OHLCV candle data from Yahoo Finance."""
        try:
            # Convert interval to yfinance format
            yf_interval = self._convert_interval()
            
            # Calculate period based on interval and limit
            period = self._calculate_period(yf_interval, limit)
            
            # Fetch data in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            data = await loop.run_in_executor(
                None, 
                lambda: self.ticker.history(period=period, interval=yf_interval)
            )
            
            if data.empty:
                logger.warning(f"No data found for {self.symbol}")
                return []
            
            # Convert to CandleData objects
            candles = []
            for timestamp, row in data.iterrows():
                candle = CandleData(
                    timestamp=timestamp.to_pydatetime(),
                    open=float(row['Open']),
                    high=float(row['High']),
                    low=float(row['Low']),
                    close=float(row['Close']),
                    volume=float(row['Volume'])
                )
                candles.append(candle)
            
            # Limit to requested number of candles
            if len(candles) > limit:
                candles = candles[-limit:]
            
            logger.info(f"Fetched {len(candles)} candles for {self.symbol}")
            return candles
            
        except Exception as e:
            logger.error(f"Error fetching candles for {self.symbol}: {e}")
            return []
    
    async def get_current_price(self) -> float:
        """Get the current price from Yahoo Finance."""
        try:
            loop = asyncio.get_event_loop()
            info = await loop.run_in_executor(None, self.ticker.info)
            
            # Try different price fields
            price_fields = ['currentPrice', 'regularMarketPrice', 'previousClose']
            for field in price_fields:
                if field in info and info[field] is not None:
                    return float(info[field])
            
            # Fallback: get latest close from recent data
            data = await self.fetch_candles(1)
            if data:
                return data[-1].close
            
            logger.warning(f"Could not get current price for {self.symbol}")
            return 0.0
            
        except Exception as e:
            logger.error(f"Error getting current price for {self.symbol}: {e}")
            return 0.0
    
    def _convert_interval(self) -> str:
        """Convert interval to yfinance format."""
        interval_map = {
            "1m": "1m",
            "5m": "5m",
            "15m": "15m", 
            "30m": "30m",
            "1h": "1h",
            "4h": "4h",
            "1d": "1d"
        }
        return interval_map.get(self.interval, "1d")
    
    def _calculate_period(self, interval: str, limit: int) -> str:
        """Calculate the period string for yfinance based on interval and limit."""
        # yfinance period options: 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max
        interval_minutes = {
            "1m": 1,
            "5m": 5,
            "15m": 15,
            "30m": 30,
            "1h": 60,
            "4h": 240,
            "1d": 1440
        }
        
        minutes_per_candle = interval_minutes.get(interval, 1440)
        total_minutes = limit * minutes_per_candle
        
        if total_minutes <= 1440:  # 1 day
            return "1d"
        elif total_minutes <= 4320:  # 3 days
            return "5d"
        elif total_minutes <= 12960:  # 9 days
            return "1mo"
        elif total_minutes <= 25920:  # 18 days
            return "3mo"
        elif total_minutes <= 51840:  # 36 days
            return "6mo"
        else:
            return "1y"

