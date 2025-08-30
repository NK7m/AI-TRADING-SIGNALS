"""
FastAPI server for the AI Trading Signals Bot.
"""

import time
from datetime import datetime
from typing import Optional
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from loguru import logger
from .config import get_config
from .schemas import SignalRequest, Signal, HealthStatus, ScheduleStatus
from .scheduler import SignalScheduler


class TradingBotServer:
    """FastAPI server for the trading signals bot."""
    
    def __init__(self):
        self.config = get_config()
        self.app = FastAPI(
            title="AI Trading Signals Bot",
            description="Production-ready AI trading signals bot using Gemini",
            version="1.0.0"
        )
        self.scheduler = SignalScheduler()
        self.start_time = time.time()
        self._setup_routes()
    
    def _setup_routes(self):
        """Setup FastAPI routes."""
        
        @self.app.get("/healthz", response_model=HealthStatus)
        async def health_check():
            """Health check endpoint."""
            uptime = time.time() - self.start_time
            return HealthStatus(
                status="healthy",
                timestamp=datetime.now(),
                version="1.0.0",
                uptime_seconds=uptime
            )
        
        @self.app.get("/readyz")
        async def readiness_check():
            """Readiness check endpoint."""
            # Check if scheduler is running
            if not self.scheduler.running:
                raise HTTPException(status_code=503, detail="Scheduler not running")
            
            return {"status": "ready"}
        
        @self.app.get("/metrics")
        async def metrics():
            """Basic metrics endpoint."""
            uptime = time.time() - self.start_time
            status = self.scheduler.get_status()
            
            return {
                "uptime_seconds": uptime,
                "scheduler_running": status["running"],
                "active_jobs": len(status["next_runs"]),
                "last_signals_count": len(status["last_signals"])
            }
        
        @self.app.post("/signal/once", response_model=Signal)
        async def generate_signal_once(request: SignalRequest):
            """Generate a single trading signal."""
            try:
                signal = await self.scheduler.generate_signal_once(
                    request.symbol, 
                    request.interval
                )
                
                if not signal:
                    raise HTTPException(
                        status_code=500, 
                        detail="Failed to generate signal"
                    )
                
                return signal
                
            except Exception as e:
                logger.error(f"Error generating signal: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/schedule/start")
        async def start_scheduler():
            """Start the signal scheduler."""
            try:
                if self.scheduler.running:
                    return {"message": "Scheduler is already running"}
                
                await self.scheduler.start()
                return {"message": "Scheduler started successfully"}
                
            except Exception as e:
                logger.error(f"Error starting scheduler: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/schedule/stop")
        async def stop_scheduler():
            """Stop the signal scheduler."""
            try:
                if not self.scheduler.running:
                    return {"message": "Scheduler is not running"}
                
                await self.scheduler.stop()
                return {"message": "Scheduler stopped successfully"}
                
            except Exception as e:
                logger.error(f"Error stopping scheduler: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/status", response_model=ScheduleStatus)
        async def get_status():
            """Get scheduler status."""
            try:
                status = self.scheduler.get_status()
                return ScheduleStatus(**status)
                
            except Exception as e:
                logger.error(f"Error getting status: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/")
        async def root():
            """Root endpoint with basic info."""
            return {
                "name": "AI Trading Signals Bot",
                "version": "1.0.0",
                "status": "running",
                "endpoints": {
                    "health": "/healthz",
                    "ready": "/readyz", 
                    "metrics": "/metrics",
                    "signal": "/signal/once",
                    "schedule_start": "/schedule/start",
                    "schedule_stop": "/schedule/stop",
                    "status": "/status"
                },
                "disclaimer": "Educational purposes only - not financial advice"
            }
    
    async def start(self):
        """Start the server."""
        logger.info("Starting FastAPI server...")
        
        # Start scheduler automatically
        await self.scheduler.start()
        
        logger.info(f"Server will start on {self.config.server.host}:{self.config.server.port}")
    
    async def stop(self):
        """Stop the server."""
        logger.info("Stopping FastAPI server...")
        await self.scheduler.stop()
        logger.info("Server stopped")


# Global server instance
server_instance = None


def get_server() -> TradingBotServer:
    """Get the global server instance."""
    global server_instance
    if server_instance is None:
        server_instance = TradingBotServer()
    return server_instance


def get_app() -> FastAPI:
    """Get the FastAPI app instance."""
    return get_server().app

