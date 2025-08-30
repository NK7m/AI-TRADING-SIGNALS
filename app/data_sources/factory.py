"""
Data source factory for creating appropriate data sources.
"""

from typing import Dict, Type
from .base import DataSource
from .yfinance_source import YFinanceSource
from .binance_source import BinanceSource


class DataSourceFactory:
    """Factory for creating data sources based on asset type."""
    
    _sources: Dict[str, Type[DataSource]] = {
        "yfinance": YFinanceSource,
        "binance": BinanceSource,
    }
    
    @classmethod
    def create_source(cls, kind: str, symbol: str, interval: str) -> DataSource:
        """Create a data source instance."""
        if kind not in cls._sources:
            raise ValueError(f"Unknown data source kind: {kind}")
        
        source_class = cls._sources[kind]
        return source_class(symbol, interval)
    
    @classmethod
    def register_source(cls, kind: str, source_class: Type[DataSource]):
        """Register a new data source type."""
        cls._sources[kind] = source_class
    
    @classmethod
    def get_available_sources(cls) -> list:
        """Get list of available data source kinds."""
        return list(cls._sources.keys())

