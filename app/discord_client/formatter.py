"""
Discord message formatter for trading signals.
"""

from datetime import datetime
from typing import Optional, Dict, Any
from ..schemas import Signal
from ..config import get_config


class DiscordFormatter:
    """Formats trading signals for Discord messages."""
    
    def __init__(self):
        self.config = get_config()
    
    def format_signal_embed(self, signal: Signal, last_signal: Optional[Signal] = None) -> Dict[str, Any]:
        """Format a trading signal as a Discord embed."""
        # Determine color based on signal type
        color_map = {
            "BUY": 0x00ff00,    # Green
            "SELL": 0xff0000,   # Red
            "NEUTRAL": 0x808080  # Gray
        }
        color = color_map.get(signal.signal, 0x808080)
        
        # Build title
        confidence_pct = int(signal.confidence * 100)
        title = f"{signal.signal} ({confidence_pct}%) — {signal.symbol} {signal.timeframe}"
        
        # Build fields
        fields = []
        
        # Reason field
        fields.append({
            "name": "Reason",
            "value": signal.reasoning[:1024],  # Discord field limit
            "inline": False
        })
        
        # Stop Loss and Take Profits
        if signal.validation.stop_loss is not None:
            fields.append({
                "name": "Stop Loss",
                "value": f"{signal.validation.stop_loss:.4f}",
                "inline": True
            })
        
        if signal.validation.take_profits:
            tp_text = ", ".join([f"{tp:.4f}" for tp in signal.validation.take_profits])
            fields.append({
                "name": "Take Profits",
                "value": tp_text,
                "inline": True
            })
        
        # Support and Resistance levels
        if signal.validation.support_levels:
            support_text = ", ".join([f"{level:.4f}" for level in signal.validation.support_levels])
            fields.append({
                "name": "Support Levels",
                "value": support_text,
                "inline": True
            })
        
        if signal.validation.resistance_levels:
            resistance_text = ", ".join([f"{level:.4f}" for level in signal.validation.resistance_levels])
            fields.append({
                "name": "Resistance Levels", 
                "value": resistance_text,
                "inline": True
            })
        
        # Model and Latency
        fields.append({
            "name": "Model / Latency",
            "value": f"{signal.metadata.model} ({signal.metadata.latency_ms}ms)",
            "inline": True
        })
        
        # Timestamp
        ist_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S IST")
        fields.append({
            "name": "Timestamp",
            "value": ist_timestamp,
            "inline": True
        })
        
        # Build embed
        embed = {
            "title": title,
            "color": color,
            "fields": fields,
            "timestamp": datetime.now().isoformat(),
            "footer": {
                "text": "AI Trading Signals Bot - Educational Only"
            }
        }
        
        return embed
    
    def format_heartbeat_message(self, symbol: str, timeframe: str, current_price: float, 
                                last_signal: Optional[Signal] = None) -> Dict[str, Any]:
        """Format a neutral heartbeat message."""
        # Build last signal info
        if last_signal:
            last_signal_info = f"{last_signal.signal} @ {last_signal.confidence:.2f}"
            last_signal_time = last_signal.metadata.latency_ms  # This would need to be actual timestamp
        else:
            last_signal_info = "None"
            last_signal_time = "N/A"
        
        # Build content
        content = f"NEUTRAL | {symbol} {timeframe} | price: {current_price:.4f} | Last signal: {last_signal_info} | Health OK ✅"
        
        # Build embed
        embed = {
            "title": f"NEUTRAL — {symbol} {timeframe}",
            "color": 0x808080,  # Gray
            "description": content,
            "timestamp": datetime.now().isoformat(),
            "footer": {
                "text": "AI Trading Signals Bot - Heartbeat"
            }
        }
        
        return embed
    
    def should_mention_traders(self, signal: Signal) -> bool:
        """Check if traders should be mentioned based on confidence."""
        return signal.confidence >= self.config.app.min_confidence_tag
    
    def get_traders_mention(self) -> str:
        """Get the traders mention string."""
        role_config = self.config.app.role_mention
        
        if role_config.mode == "id":
            return f"<@&{role_config.value}>"
        else:
            return role_config.value

