# AI Trading Signals Bot

A production-ready AI trading signals bot that uses Google's Gemini AI to analyze market data and post trading signals to Discord channels.

## ⚠️ Disclaimer

**This software is for educational purposes only and is not financial advice. Trading involves substantial risk of loss and is not suitable for all investors. Past performance is not indicative of future results. Always do your own research and consider consulting with a financial advisor before making investment decisions.**

## Features

- 🤖 **AI-Powered Analysis**: Uses Google Gemini AI for market signal generation
- 📊 **Multiple Data Sources**: Supports Binance (crypto), Yahoo Finance (stocks/ETFs)
- 🔄 **Automated Scheduling**: Configurable intervals with heartbeat monitoring
- 💬 **Discord Integration**: Rich embeds with role mentions for high-confidence signals
- 🏥 **Health Monitoring**: Built-in health checks and metrics
- 🐳 **Docker Ready**: Complete containerization with docker-compose
- 🧪 **Well Tested**: Comprehensive test suite with >90% coverage
- ⚡ **Async Performance**: High-performance async I/O throughout

## Quick Start

### Prerequisites

- Python 3.11+
- Docker & Docker Compose (optional)
- Gemini API key
- Discord webhook URL

### 1. Clone and Setup

```bash
git clone <repository-url>
cd ai-trading
```

### 2. Configure Environment

```bash
# Copy environment template
cp env.template .env

# Edit .env with your credentials
nano .env
```

Required environment variables:
```bash
GEMINI_API_KEY=your_gemini_api_key_here
DISCORD_WEBHOOK_URL=your_discord_webhook_url_here
```

### 3. Run with Docker (Recommended)

```bash
# Start the bot
docker compose up --build

# View logs
docker compose logs -f

# Stop the bot
docker compose down
```

### 4. Run Locally

```bash
# Install dependencies
pip install -r requirements.txt

# Start the bot
python -m app run

# Generate a test signal
python -m app once --symbol BTCUSDT --interval 15m
```

## Configuration

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GEMINI_API_KEY` | Yes | Google Gemini API key |
| `DISCORD_WEBHOOK_URL` | Yes | Discord webhook URL |
| `DISCORD_BOT_TOKEN` | No | Discord bot token (if using bot mode) |
| `DISCORD_CHANNEL_ID` | No | Discord channel ID (if using bot mode) |

### Config File (`config/config.yaml`)

```yaml
app:
  timezone: "Asia/Kolkata"
  log_level: "INFO"
  neutral_heartbeat_minutes: 30
  min_confidence_tag: 0.75
  role_mention:
    mode: "name"   # "name" or "id"
    value: "@traders"

discord:
  mode: "webhook"  # or "bot"
  webhook_url: "${DISCORD_WEBHOOK_URL}"
  embeds: true

llm:
  provider: "gemini"
  model: "gemini-1.5-pro"
  api_key: "${GEMINI_API_KEY}"
  request_timeout_seconds: 30
  max_retries: 2

data:
  default_interval: "15m"
  bars: 300
  sources:
    - symbol: "BTCUSDT"
      kind: "binance"
      interval: "15m"
    - symbol: "AAPL"
      kind: "yfinance"
      interval: "15m"

server:
  host: "0.0.0.0"
  port: 8080
```

## API Endpoints

The bot exposes a FastAPI server with the following endpoints:

### Health & Status
- `GET /healthz` - Health check
- `GET /readyz` - Readiness check
- `GET /metrics` - Basic metrics
- `GET /status` - Scheduler status

### Signal Generation
- `POST /signal/once` - Generate a single signal
  ```json
  {
    "symbol": "BTCUSDT",
    "interval": "15m",
    "tradingview_link": "https://tradingview.com/chart/..." // optional
  }
  ```

### Scheduler Control
- `POST /schedule/start` - Start the scheduler
- `POST /schedule/stop` - Stop the scheduler

## Discord Integration

### Webhook Setup

1. Go to your Discord server settings
2. Navigate to Integrations → Webhooks
3. Create a new webhook
4. Copy the webhook URL to your `.env` file

### Message Format

**Trading Signals:**
- Rich embeds with color coding (Green=Buy, Red=Sell, Gray=Neutral)
- Confidence percentage in title
- Support/resistance levels
- Stop loss and take profit targets
- Model information and latency

**Heartbeat Messages:**
- Sent every 30 minutes per asset
- Shows current price and last signal info
- Confirms system health

**Role Mentions:**
- High-confidence signals (≥75%) automatically mention `@traders`
- Configurable role name or ID

## TradingView Integration

### Webhook Alerts

1. Create a TradingView alert for your symbol
2. Set the webhook URL to: `http://your-bot-url:8080/signal/once`
3. Configure the alert to send JSON payload:
   ```json
   {
     "symbol": "BTCUSDT",
     "interval": "15m"
   }
   ```

### Chart Links

You can also paste TradingView chart URLs in the config or API requests. The bot will attempt to parse the symbol and interval from the URL.

## Data Sources

### Supported Sources

- **Binance**: Cryptocurrency data (BTCUSDT, ETHUSDT, etc.)
- **Yahoo Finance**: Stocks and ETFs (AAPL, TSLA, SPY, etc.)

### Technical Indicators

The bot calculates the following indicators:
- EMA (20, 50 periods)
- RSI (14 periods)
- MACD (12, 26, 9)
- ATR (14 periods)

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_schemas.py

# Run integration tests
pytest tests/test_integration.py
```

## Development

### Project Structure

```
ai-trading/
├── app/
│   ├── __init__.py
│   ├── __main__.py          # CLI entry point
│   ├── config.py            # Configuration management
│   ├── schemas.py           # Pydantic schemas
│   ├── server.py            # FastAPI server
│   ├── data_sources/        # Market data sources
│   ├── indicators/          # Technical indicators
│   ├── signal_engine/       # AI signal generation
│   ├── discord_client/      # Discord integration
│   └── scheduler/           # Task scheduling
├── config/
│   └── config.yaml          # Main configuration
├── tests/                   # Test suite
├── docker-compose.yml       # Docker setup
├── Dockerfile              # Container definition
├── requirements.txt        # Python dependencies
└── README.md              # This file
```

### Adding New Data Sources

1. Create a new class inheriting from `DataSource`
2. Implement `fetch_candles()` and `get_current_price()` methods
3. Register the source in `DataSourceFactory`

### Adding New Indicators

1. Add calculation method to `IndicatorCalculator`
2. Update `IndicatorData` schema if needed
3. Include in `calculate_all_indicators()` method

## Monitoring & Observability

### Health Checks

- `/healthz` - Basic health status
- `/readyz` - Readiness for traffic
- `/metrics` - Prometheus-style metrics

### Logging

Structured logging with configurable levels:
- `DEBUG` - Detailed debugging info
- `INFO` - General information
- `WARNING` - Warning messages
- `ERROR` - Error conditions

### Metrics

Basic metrics exposed at `/metrics`:
- Uptime
- Scheduler status
- Active jobs count
- Last signals count

## Troubleshooting

### Common Issues

1. **"Gemini API key not configured"**
   - Ensure `GEMINI_API_KEY` is set in `.env`
   - Verify the API key is valid

2. **"Discord webhook URL not configured"**
   - Check `DISCORD_WEBHOOK_URL` in `.env`
   - Verify the webhook URL is correct

3. **"No data found for symbol"**
   - Check if the symbol is supported by the data source
   - Verify the symbol format (e.g., BTCUSDT for Binance)

4. **"Failed to generate signal"**
   - Check Gemini API quota and limits
   - Verify network connectivity
   - Check logs for detailed error messages

### Debug Mode

```bash
# Run with debug logging
LOG_LEVEL=DEBUG python -m app run

# Or edit config.yaml
app:
  log_level: "DEBUG"
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review the logs for error messages
3. Open an issue on GitHub
4. Provide relevant configuration and error details

---

**Remember: This is educational software. Always do your own research and never risk more than you can afford to lose.**

