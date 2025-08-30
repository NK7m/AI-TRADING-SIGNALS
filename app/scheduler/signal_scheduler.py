"""
Signal scheduler for automated trading signal generation.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, Optional, List
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from loguru import logger
from ..config import get_config
from ..schemas import Signal, AssetConfig
from ..data_sources import DataSourceFactory
from ..indicators import IndicatorCalculator
from ..signal_engine import GeminiSignalEngine
from ..discord_client import DiscordClient


class SignalScheduler:
    """Scheduler for automated signal generation and Discord posting."""
    
    def __init__(self):
        self.config = get_config()
        self.scheduler = AsyncIOScheduler(timezone=self.config.app.timezone)
        self.signal_engine = GeminiSignalEngine()
        self.last_signals: Dict[str, Signal] = {}
        self.last_heartbeats: Dict[str, datetime] = {}
        self.running = False
    
    async def start(self):
        """Start the scheduler."""
        if self.running:
            logger.warning("Scheduler is already running")
            return
        
        logger.info("Starting signal scheduler...")
        
        # Schedule heartbeat for each asset
        for asset in self.config.data.sources:
            asset_key = f"{asset.symbol}_{asset.interval}"
            
            # Schedule heartbeat every 30 minutes
            self.scheduler.add_job(
                self._send_heartbeat,
                trigger=IntervalTrigger(minutes=self.config.app.neutral_heartbeat_minutes),
                args=[asset],
                id=f"heartbeat_{asset_key}",
                replace_existing=True
            )
            
            # Schedule signal generation based on interval
            self._schedule_signal_generation(asset)
        
        self.scheduler.start()
        self.running = True
        logger.info("Signal scheduler started successfully")
    
    async def stop(self):
        """Stop the scheduler."""
        if not self.running:
            logger.warning("Scheduler is not running")
            return
        
        logger.info("Stopping signal scheduler...")
        self.scheduler.shutdown()
        self.running = False
        logger.info("Signal scheduler stopped")
    
    def _schedule_signal_generation(self, asset: AssetConfig):
        """Schedule signal generation for an asset."""
        asset_key = f"{asset.symbol}_{asset.interval}"
        
        # Convert interval to minutes for scheduling
        interval_minutes = self._interval_to_minutes(asset.interval)
        
        # Schedule signal generation
        self.scheduler.add_job(
            self._generate_and_send_signal,
            trigger=IntervalTrigger(minutes=interval_minutes),
            args=[asset],
            id=f"signal_{asset_key}",
            replace_existing=True
        )
        
        logger.info(f"Scheduled signal generation for {asset.symbol} every {asset.interval}")
    
    def _interval_to_minutes(self, interval: str) -> int:
        """Convert interval string to minutes."""
        interval_map = {
            "1m": 1,
            "5m": 5,
            "15m": 15,
            "30m": 30,
            "1h": 60,
            "4h": 240,
            "1d": 1440
        }
        return interval_map.get(interval, 15)
    
    async def _generate_and_send_signal(self, asset: AssetConfig):
        """Generate and send a trading signal for an asset."""
        asset_key = f"{asset.symbol}_{asset.interval}"
        
        try:
            logger.info(f"Generating signal for {asset.symbol} {asset.interval}")
            
            # Fetch market data
            data_source = DataSourceFactory.create_source(asset.kind, asset.symbol, asset.interval)
            market_data = await data_source.fetch_market_data(self.config.data.bars)
            
            if not market_data.candles:
                logger.warning(f"No candle data available for {asset.symbol}")
                return
            
            # Calculate indicators
            market_data.indicators = IndicatorCalculator.calculate_all_indicators(market_data.candles)
            
            # Generate signal
            signal = await self.signal_engine.generate_signal(market_data)
            
            if not signal:
                logger.warning(f"Failed to generate signal for {asset.symbol}")
                return
            
            # Send to Discord
            async with DiscordClient() as discord_client:
                success = await discord_client.send_signal(signal, self.last_signals.get(asset_key))
                
                if success:
                    self.last_signals[asset_key] = signal
                    logger.info(f"Signal sent successfully: {signal.signal} for {signal.symbol}")
                else:
                    logger.error(f"Failed to send signal to Discord for {asset.symbol}")
            
        except Exception as e:
            logger.error(f"Error generating signal for {asset.symbol}: {e}")
    
    async def _send_heartbeat(self, asset: AssetConfig):
        """Send a neutral heartbeat for an asset."""
        asset_key = f"{asset.symbol}_{asset.interval}"
        
        try:
            logger.info(f"Sending heartbeat for {asset.symbol} {asset.interval}")
            
            # Get current price
            data_source = DataSourceFactory.create_source(asset.kind, asset.symbol, asset.interval)
            current_price = await data_source.get_current_price()
            
            if current_price == 0:
                logger.warning(f"Could not get current price for {asset.symbol}")
                return
            
            # Send heartbeat to Discord
            async with DiscordClient() as discord_client:
                success = await discord_client.send_heartbeat(
                    asset.symbol, 
                    asset.interval, 
                    current_price,
                    self.last_signals.get(asset_key)
                )
                
                if success:
                    self.last_heartbeats[asset_key] = datetime.now()
                    logger.info(f"Heartbeat sent successfully for {asset.symbol}")
                else:
                    logger.error(f"Failed to send heartbeat to Discord for {asset.symbol}")
            
        except Exception as e:
            logger.error(f"Error sending heartbeat for {asset.symbol}: {e}")
    
    def get_status(self) -> Dict:
        """Get scheduler status."""
        if not self.running:
            return {
                "running": False,
                "next_runs": {},
                "last_signals": {}
            }
        
        # Get next run times
        next_runs = {}
        for job in self.scheduler.get_jobs():
            if job.next_run_time:
                next_runs[job.id] = job.next_run_time
        
        # Get last signals
        last_signals = {}
        for asset_key, signal in self.last_signals.items():
            last_signals[asset_key] = {
                "symbol": signal.symbol,
                "timeframe": signal.timeframe,
                "signal": signal.signal,
                "confidence": float(signal.confidence),
                "timestamp": signal.metadata.latency_ms  # This should be actual timestamp
            }
        
        return {
            "running": self.running,
            "next_runs": next_runs,
            "last_signals": last_signals
        }
    
    async def generate_signal_once(self, symbol: str, interval: str) -> Optional[Signal]:
        """Generate a signal once for testing purposes."""
        try:
            # Find the asset configuration
            asset = None
            for config_asset in self.config.data.sources:
                if config_asset.symbol == symbol and config_asset.interval == interval:
                    asset = config_asset
                    break
            
            if not asset:
                # Create a temporary asset config
                asset = AssetConfig(symbol=symbol, kind="binance", interval=interval)
            
            # Fetch market data
            data_source = DataSourceFactory.create_source(asset.kind, asset.symbol, asset.interval)
            market_data = await data_source.fetch_market_data(self.config.data.bars)
            
            if not market_data.candles:
                logger.warning(f"No candle data available for {asset.symbol}")
                return None
            
            # Calculate indicators
            market_data.indicators = IndicatorCalculator.calculate_all_indicators(market_data.candles)
            
            # Generate signal
            signal = await self.signal_engine.generate_signal(market_data)
            
            return signal
            
        except Exception as e:
            logger.error(f"Error generating signal for {symbol}: {e}")
            return None

