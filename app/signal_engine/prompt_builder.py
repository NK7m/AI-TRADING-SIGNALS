"""
Prompt builder for the Gemini signal engine.
"""

import json
from datetime import datetime
from typing import Dict, Any
from ..schemas import MarketData, Signal, ValidationData, SignalMetadata


class PromptBuilder:
    """Builds prompts for the Gemini signal engine."""
    
    SYSTEM_PROMPT = """You are an objective market signal engine. You analyze candles and indicators to output one of BUY|SELL|NEUTRAL with a numeric confidence in [0,1], never exceeding 1.0. Keep reasoning concise (≤ 400 chars) and produce valid JSON only that matches the provided schema. Do not include any extra text."""

    @staticmethod
    def build_user_prompt(market_data: MarketData, timezone: str = "Asia/Kolkata") -> str:
        """Build the user prompt for signal generation."""
        now_ist = datetime.now().strftime("%Y-%m-%d %H:%M:%S %Z")
        
        # Compress candle data for prompt
        candles_summary = PromptBuilder._compress_candles(market_data.candles)
        
        # Build indicators summary
        indicators_summary = PromptBuilder._build_indicators_summary(market_data.indicators)
        
        # Build headlines summary
        headlines_summary = PromptBuilder._build_headlines_summary(market_data.headlines)
        
        # Get schema as text
        schema_text = PromptBuilder._get_schema_text()
        
        prompt = f"""Current time ({timezone}): {now_ist}
Symbol: {market_data.symbol}
Timeframe: {market_data.timeframe}
Latest price: {market_data.current_price:.4f}
Indicators (last 300 bars summarized): {indicators_summary}
Headlines (optional): {headlines_summary}

REQUIRED JSON SCHEMA:
{schema_text}

Return ONLY valid JSON."""
        
        return prompt
    
    @staticmethod
    def _compress_candles(candles) -> str:
        """Compress candle data for the prompt."""
        if not candles:
            return "No candle data available"
        
        # Take first 5, middle 5, and last 5 candles
        total = len(candles)
        if total <= 15:
            selected = candles
        else:
            selected = (
                candles[:5] + 
                candles[total//2-2:total//2+3] + 
                candles[-5:]
            )
        
        summary = []
        for candle in selected:
            summary.append(
                f"{candle.timestamp.strftime('%m-%d %H:%M')}: "
                f"O:{candle.open:.4f} H:{candle.high:.4f} "
                f"L:{candle.low:.4f} C:{candle.close:.4f} V:{candle.volume:.0f}"
            )
        
        return " | ".join(summary)
    
    @staticmethod
    def _build_indicators_summary(indicators) -> str:
        """Build indicators summary for the prompt."""
        if not indicators:
            return "No indicators available"
        
        summary_parts = []
        
        if indicators.ema_20 is not None:
            summary_parts.append(f"EMA20: {indicators.ema_20:.4f}")
        if indicators.ema_50 is not None:
            summary_parts.append(f"EMA50: {indicators.ema_50:.4f}")
        if indicators.rsi is not None:
            summary_parts.append(f"RSI: {indicators.rsi:.2f}")
        if indicators.macd is not None:
            summary_parts.append(f"MACD: {indicators.macd:.4f}")
        if indicators.macd_signal is not None:
            summary_parts.append(f"MACD_Signal: {indicators.macd_signal:.4f}")
        if indicators.macd_histogram is not None:
            summary_parts.append(f"MACD_Hist: {indicators.macd_histogram:.4f}")
        if indicators.atr is not None:
            summary_parts.append(f"ATR: {indicators.atr:.4f}")
        
        return " | ".join(summary_parts) if summary_parts else "No indicators available"
    
    @staticmethod
    def _build_headlines_summary(headlines) -> str:
        """Build headlines summary for the prompt."""
        if not headlines:
            return "No recent headlines"
        
        # Limit to first 3 headlines, max 100 chars each
        limited_headlines = headlines[:3]
        summary_parts = []
        
        for headline in limited_headlines:
            if len(headline) > 100:
                headline = headline[:97] + "..."
            summary_parts.append(headline)
        
        return " | ".join(summary_parts)
    
    @staticmethod
    def _get_schema_text() -> str:
        """Get the JSON schema as text."""
        schema = {
            "symbol": "string",
            "timeframe": "string", 
            "signal": "BUY|SELL|NEUTRAL",
            "confidence": "number (0.0 to 1.0)",
            "reasoning": "string (max 400 chars, concise analysis)",
            "validation": {
                "support_levels": "array of numbers",
                "resistance_levels": "array of numbers", 
                "stop_loss": "number or null",
                "take_profits": "array of numbers"
            },
            "metadata": {
                "latency_ms": "number",
                "model": "string",
                "version": "string"
            }
        }
        
        return json.dumps(schema, indent=2)

