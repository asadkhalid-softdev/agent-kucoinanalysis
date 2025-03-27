# KuCoin Analysis Bot

A sophisticated cryptocurrency analysis bot that provides real-time technical analysis and trading signals using the KuCoin API. The bot combines multiple technical indicators and strategies to generate comprehensive market insights.

## Features

- **Multi-Strategy Analysis**
  - Momentum Strategy
  - Mean Reversion Strategy
  - Breakout Strategy
  - Configurable strategy selection via environment variables

- **Technical Indicators**
  - RSI (Relative Strength Index)
  - MACD (Moving Average Convergence Divergence)
  - Bollinger Bands
  - Moving Averages (SMA, EMA)
  - Stochastic Oscillator
  - ADX (Average Directional Index)
  - Fibonacci Retracement
  - OBV (On-Balance Volume)
  - Candlestick Patterns
    - Doji (neutral)
    - Hammer (bullish)
    - Shooting Star (bearish)
    - Bullish/Bearish Engulfing

- **Multi-Timeframe Analysis**
  - Support for multiple timeframes (1min to 1week)
  - Configurable primary and secondary timeframes
  - Adaptive data collection based on timeframe

- **Real-time Monitoring**
  - Live dashboard for monitoring analysis results
  - Performance metrics and system status
  - Historical data visualization

- **Telegram Integration**
  - Real-time trading signals via Telegram
  - Configurable notification filters
  - Customizable alert conditions

## Prerequisites

- Python 3.10 or higher
- KuCoin API credentials (for enhanced functionality)
- Internet connection

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/agent-kucoinanalysis.git
cd agent-kucoinanalysis
```

2. Create and activate a virtual environment using uv:
```bash
uv venv --python 3.10
.venv\Scripts\activate  # On Windows
source .venv/bin/activate  # On Unix/MacOS
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure environment variables:
Create a `.env` file with the following settings:

```env
# KuCoin API Credentials
KUCOIN_API_KEY=your_api_key
KUCOIN_API_SECRET=your_api_secret
KUCOIN_API_PASSPHRASE=your_api_passphrase

# API Authentication
API_USERNAME=admin
API_PASSWORD=your_password
SECRET_KEY=your_jwt_secret_key

# Telegram Settings
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id
TELEGRAM_NOTIFICATIONS_ENABLED=true
TELEGRAM_NOTIFY_ON_VOLUME=0
TELEGRAM_NOTIFY_ON_RSI_BUY=70

# Strategy-specific filters
MOMENTUM_SCORE_THRESHOLD=0.5
MOMENTUM_CONFIDENCE_THRESHOLD=0.6
MEAN_REVERSION_SCORE_THRESHOLD=0.5
MEAN_REVERSION_CONFIDENCE_THRESHOLD=0.6
BREAKOUT_SCORE_THRESHOLD=0.5
BREAKOUT_CONFIDENCE_THRESHOLD=0.6

# Strategy Filters
ENABLE_MOMENTUM_STRATEGY=true
ENABLE_MEAN_REVERSION_STRATEGY=true
ENABLE_BREAKOUT_STRATEGY=true
```

## Usage

1. Start the application:
```bash
python main.py
```

2. Access the interfaces:
- API Documentation: http://localhost:8000/docs
- Monitoring Dashboard: http://localhost:8050

## Configuration

### Analysis Settings
Configure analysis parameters in `config/user_config.json`:
```json
{
  "analysis": {
    "interval": 1,
    "main_timeframe": "15min",
    "timeframes": ["15min"],
    "indicators": [
      "RSI", "MACD", "BBANDS", "SMA", "EMA", 
      "STOCH", "ADX", "FIBONACCI", "OBV", "CANDLESTICK"
    ]
  }
}
```

### Strategy Settings
Enable/disable strategies and adjust thresholds in `.env`:
```env
ENABLE_MOMENTUM_STRATEGY=true
MOMENTUM_SCORE_THRESHOLD=0.5
MOMENTUM_CONFIDENCE_THRESHOLD=0.6
```

### Candlestick Pattern Analysis
The bot includes sophisticated candlestick pattern analysis that:
- Detects common patterns (Doji, Hammer, Shooting Star, Engulfing)
- Provides pattern-specific signals and strengths
- Integrates with multiple trading strategies:
  - Momentum: 0.6 weight (confirms trend direction)
  - Mean Reversion: 0.4 weight (helps identify potential reversals)
  - Breakout: 0.5 weight (confirms breakout signals)

## API Endpoints

### Authentication
```
POST /token
Content-Type: application/x-www-form-urlencoded
username=admin&password=your_password
```

### Symbol Management
- `GET /api/symbols` - List all tracked symbols
- `POST /api/symbols` - Add a new symbol
- `DELETE /api/symbols/{symbol}` - Remove a symbol

### Analysis
- `GET /api/analysis` - Get analysis for all symbols
- `GET /api/analysis/{symbol}` - Get detailed analysis for a specific symbol
- `GET /api/analysis/sentiment` - Get sentiment summary for all symbols

## Monitoring Dashboard

The dashboard provides:
- Real-time analysis results
- System performance metrics
- Historical data visualization
- Strategy performance tracking
- Candlestick pattern visualization

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
