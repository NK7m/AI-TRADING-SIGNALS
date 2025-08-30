"""
Pydantic schemas for the AI Trading Signals Bot.
"""

from decimal import Decimal
from typing import List, Optional, Literal, Dict, Any
from pydantic import BaseModel, Field, validator, condecimal
from datetime import datetime


class ValidationData(BaseModel):
    """Validation data for trading signals."""
    support_levels: List[float] = Field(default_factory=list)
    resistance_levels: List[float] = Field(default_factory=list)
    stop_loss: Optional[float] = None
    take_profits: List[float] = Field(default_factory=list)


class SignalMetadata(BaseModel):
    """Metadata for signal processing."""
    latency_ms: int
    model: str
    version: str = "1.0.0"


class Signal(BaseModel):
    """Main signal schema for AI trading signals."""
    symbol: str
    timeframe: str
    signal: Literal["BUY", "SELL", "NEUTRAL"]
    confidence: condecimal(ge=0, le=1)
    reasoning: str = Field(..., max_length=400)
    validation: ValidationData
    metadata: SignalMetadata

    @validator('reasoning')
    def validate_reasoning(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('Reasoning cannot be empty')
        return v.strip()

    @validator('symbol')
    def validate_symbol(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('Symbol cannot be empty')
        return v.strip().upper()


class SignalRequest(BaseModel):
    """Request schema for generating signals."""
    symbol: str
    interval: str
    tradingview_link: Optional[str] = None


class ScheduleStatus(BaseModel):
    """Status of the scheduler."""
    running: bool
    next_runs: Dict[str, datetime]
    last_signals: Dict[str, Signal]


class HealthStatus(BaseModel):
    """Health check status."""
    status: str
    timestamp: datetime
    version: str
    uptime_seconds: float


class AssetConfig(BaseModel):
    """Configuration for an asset."""
    symbol: str
    kind: str  # "binance", "yfinance", etc.
    interval: str


class DataSourceConfig(BaseModel):
    """Configuration for data sources."""
    default_interval: str = "15m"
    bars: int = 300
    sources: List[AssetConfig]
    news: Dict[str, Any] = Field(default_factory=dict)


class LLMConfig(BaseModel):
    """Configuration for LLM provider."""
    provider: str = "gemini"
    model: str = "gemini-1.5-pro"
    api_key: str
    request_timeout_seconds: int = 30
    max_retries: int = 2


class DiscordConfig(BaseModel):
    """Configuration for Discord integration."""
    mode: str = "webhook"  # "webhook" or "bot"
    webhook_url: Optional[str] = None
    bot_token: Optional[str] = None
    channel_id: Optional[str] = None
    embeds: bool = True


class RoleMentionConfig(BaseModel):
    """Configuration for role mentions."""
    mode: str = "name"  # "name" or "id"
    value: str = "@traders"


class AppConfig(BaseModel):
    """Main application configuration."""
    timezone: str = "Asia/Kolkata"
    log_level: str = "INFO"
    neutral_heartbeat_minutes: int = 30
    min_confidence_tag: float = 0.75
    role_mention: RoleMentionConfig


class ServerConfig(BaseModel):
    """Server configuration."""
    host: str = "0.0.0.0"
    port: int = 8080


class MetricsConfig(BaseModel):
    """Metrics configuration."""
    enabled: bool = True
    path: str = "/metrics"


class TradingViewConfig(BaseModel):
    """TradingView configuration."""
    link: str = ""
    allow_webhook: bool = True


class Config(BaseModel):
    """Complete application configuration."""
    app: AppConfig
    discord: DiscordConfig
    llm: LLMConfig
    data: DataSourceConfig
    tradingview: TradingViewConfig
    server: ServerConfig
    metrics: MetricsConfig


class CandleData(BaseModel):
    """OHLCV candle data."""
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float


class IndicatorData(BaseModel):
    """Technical indicator data."""
    ema_20: Optional[float] = None
    ema_50: Optional[float] = None
    rsi: Optional[float] = None
    macd: Optional[float] = None
    macd_signal: Optional[float] = None
    macd_histogram: Optional[float] = None
    atr: Optional[float] = None


class MarketData(BaseModel):
    """Complete market data for analysis."""
    symbol: str
    timeframe: str
    candles: List[CandleData]
    indicators: IndicatorData
    current_price: float
    headlines: List[str] = Field(default_factory=list)

