"""
Gemini-based signal engine implementation.
"""

import json
import time
import asyncio
from typing import Optional, Dict, Any
import google.generativeai as genai
from loguru import logger
from ..schemas import MarketData, Signal, ValidationData, SignalMetadata
from ..config import get_config
from .prompt_builder import PromptBuilder


class GeminiSignalEngine:
    """Gemini-based signal generation engine."""
    
    def __init__(self):
        self.config = get_config()
        self._setup_gemini()
        self.model = genai.GenerativeModel(self.config.llm.model)
    
    def _setup_gemini(self):
        """Setup Gemini API configuration."""
        if not self.config.llm.api_key:
            raise ValueError("Gemini API key not configured")
        
        genai.configure(api_key=self.config.llm.api_key)
    
    async def generate_signal(self, market_data: MarketData) -> Optional[Signal]:
        """Generate a trading signal from market data."""
        start_time = time.time()
        
        try:
            # Build prompts
            system_prompt = PromptBuilder.SYSTEM_PROMPT
            user_prompt = PromptBuilder.build_user_prompt(
                market_data, 
                self.config.app.timezone
            )
            
            # Generate response with retries
            response_text = await self._generate_with_retries(system_prompt, user_prompt)
            
            if not response_text:
                logger.error("Failed to get response from Gemini")
                return None
            
            # Parse and validate response
            signal = self._parse_response(response_text, market_data, start_time)
            
            if signal:
                logger.info(f"Generated {signal.signal} signal for {signal.symbol} "
                          f"with confidence {signal.confidence}")
            
            return signal
            
        except Exception as e:
            logger.error(f"Error generating signal: {e}")
            return None
    
    async def _generate_with_retries(self, system_prompt: str, user_prompt: str) -> Optional[str]:
        """Generate response with retry logic."""
        for attempt in range(self.config.llm.max_retries + 1):
            try:
                # Run Gemini generation in thread pool to avoid blocking
                loop = asyncio.get_event_loop()
                response = await loop.run_in_executor(
                    None,
                    lambda: self.model.generate_content(
                        f"{system_prompt}\n\n{user_prompt}",
                        generation_config=genai.types.GenerationConfig(
                            temperature=0.1,
                            max_output_tokens=1000,
                        )
                    )
                )
                
                if response and response.text:
                    return response.text.strip()
                
                logger.warning(f"Empty response from Gemini (attempt {attempt + 1})")
                
            except Exception as e:
                logger.warning(f"Gemini API error (attempt {attempt + 1}): {e}")
                
                if attempt < self.config.llm.max_retries:
                    wait_time = 2 ** attempt  # Exponential backoff
                    await asyncio.sleep(wait_time)
                else:
                    logger.error("Max retries exceeded for Gemini API")
        
        return None
    
    def _parse_response(self, response_text: str, market_data: MarketData, start_time: float) -> Optional[Signal]:
        """Parse and validate the Gemini response."""
        try:
            # Clean the response text
            response_text = response_text.strip()
            
            # Remove any markdown code blocks
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.startswith("```"):
                response_text = response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            
            response_text = response_text.strip()
            
            # Parse JSON
            try:
                data = json.loads(response_text)
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON response: {e}")
                logger.debug(f"Response text: {response_text}")
                return None
            
            # Validate required fields
            required_fields = ["symbol", "timeframe", "signal", "confidence", "reasoning"]
            for field in required_fields:
                if field not in data:
                    logger.error(f"Missing required field: {field}")
                    return None
            
            # Validate signal type
            if data["signal"] not in ["BUY", "SELL", "NEUTRAL"]:
                logger.error(f"Invalid signal type: {data['signal']}")
                return None
            
            # Validate confidence
            confidence = float(data["confidence"])
            if not (0.0 <= confidence <= 1.0):
                logger.error(f"Invalid confidence value: {confidence}")
                return None
            
            # Build validation data
            validation_data = ValidationData()
            if "validation" in data and isinstance(data["validation"], dict):
                validation = data["validation"]
                validation_data.support_levels = validation.get("support_levels", [])
                validation_data.resistance_levels = validation.get("resistance_levels", [])
                validation_data.stop_loss = validation.get("stop_loss")
                validation_data.take_profits = validation.get("take_profits", [])
            
            # Build metadata
            latency_ms = int((time.time() - start_time) * 1000)
            metadata = SignalMetadata(
                latency_ms=latency_ms,
                model=self.config.llm.model,
                version="1.0.0"
            )
            
            # Create signal object
            signal = Signal(
                symbol=data["symbol"],
                timeframe=data["timeframe"],
                signal=data["signal"],
                confidence=confidence,
                reasoning=data["reasoning"],
                validation=validation_data,
                metadata=metadata
            )
            
            return signal
            
        except Exception as e:
            logger.error(f"Error parsing response: {e}")
            logger.debug(f"Response text: {response_text}")
            return None

