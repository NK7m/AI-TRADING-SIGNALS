"""
CLI entry point for the AI Trading Signals Bot.
"""

import asyncio
import argparse
import sys
import uvicorn
from loguru import logger
from .config import get_config
from .server import get_server
from .scheduler import SignalScheduler


def setup_logging():
    """Setup logging configuration."""
    config = get_config()
    
    # Remove default logger
    logger.remove()
    
    # Add console logger
    logger.add(
        sys.stderr,
        level=config.app.log_level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
    )


async def run_server():
    """Run the FastAPI server."""
    setup_logging()
    logger.info("Starting AI Trading Signals Bot server...")
    
    try:
        config = get_config()
        server = get_server()
        
        # Start the server
        await server.start()
        
        # Run with uvicorn
        uvicorn.run(
            server.app,
            host=config.server.host,
            port=config.server.port,
            log_level=config.app.log_level.lower()
        )
        
    except KeyboardInterrupt:
        logger.info("Received interrupt signal, shutting down...")
    except Exception as e:
        logger.error(f"Server error: {e}")
        sys.exit(1)
    finally:
        server = get_server()
        await server.stop()


async def generate_signal_once(symbol: str, interval: str):
    """Generate a single signal for testing."""
    setup_logging()
    logger.info(f"Generating signal for {symbol} {interval}...")
    
    try:
        scheduler = SignalScheduler()
        signal = await scheduler.generate_signal_once(symbol, interval)
        
        if signal:
            print(f"\nSignal Generated:")
            print(f"Symbol: {signal.symbol}")
            print(f"Timeframe: {signal.timeframe}")
            print(f"Signal: {signal.signal}")
            print(f"Confidence: {signal.confidence:.2%}")
            print(f"Reasoning: {signal.reasoning}")
            
            if signal.validation.stop_loss:
                print(f"Stop Loss: {signal.validation.stop_loss:.4f}")
            
            if signal.validation.take_profits:
                print(f"Take Profits: {', '.join([f'{tp:.4f}' for tp in signal.validation.take_profits])}")
            
            if signal.validation.support_levels:
                print(f"Support: {', '.join([f'{s:.4f}' for s in signal.validation.support_levels])}")
            
            if signal.validation.resistance_levels:
                print(f"Resistance: {', '.join([f'{r:.4f}' for r in signal.validation.resistance_levels])}")
            
            print(f"Model: {signal.metadata.model}")
            print(f"Latency: {signal.metadata.latency_ms}ms")
            
        else:
            print("Failed to generate signal")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Error generating signal: {e}")
        sys.exit(1)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="AI Trading Signals Bot",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m app run                    # Start the server
  python -m app once --symbol BTCUSDT --interval 15m  # Generate one signal
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Run command
    run_parser = subparsers.add_parser("run", help="Start the trading bot server")
    
    # Once command
    once_parser = subparsers.add_parser("once", help="Generate a single signal")
    once_parser.add_argument("--symbol", required=True, help="Trading symbol (e.g., BTCUSDT)")
    once_parser.add_argument("--interval", required=True, help="Time interval (e.g., 15m)")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    if args.command == "run":
        asyncio.run(run_server())
    elif args.command == "once":
        asyncio.run(generate_signal_once(args.symbol, args.interval))
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()

