# KuCoin Spot Analysis Bot

An AI-powered technical analysis bot for cryptocurrency markets using the KuCoin API. This bot analyzes popular technical indicators to provide trading insights without executing trades.

## Features

- Real-time technical analysis of cryptocurrency markets
- Multi-timeframe analysis for comprehensive market insights
- Sentiment analysis combining multiple technical indicators
- RESTful API for easy integration with other systems
- Configurable analysis parameters and indicators
- Performance monitoring and optimization

## Getting Started

### Prerequisites

- Python 3.8 or higher
- KuCoin API credentials (optional for public endpoints)
- Internet connection

### Installation

1. Clone the repository:

```
git clone https://github.com/yourusername/kucoin-analysis-bot.git
cd kucoin-analysis-bot
```


2. Create a virtual environment:

```
python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate
```


3. Install dependencies:

```
pip install -r requirements.txt
```


4. Create a `.env` file with your configuration:

```
KUCOIN_API_KEY=your_api_key
KUCOIN_API_SECRET=your_api_secret
KUCOIN_API_PASSPHRASE=your_api_passphrase
API_USERNAME=admin
API_PASSWORD=secure_password
SECRET_KEY=your_jwt_secret_key
```


5. Start the application:

```
python main.py
```


## API Documentation

The bot provides a RESTful API for managing symbols and accessing analysis results.

### Authentication

All API endpoints (except `/docs` and `/redoc`) require authentication using JWT tokens.

To get a token:

POST /token
Content-Type: application/x-www-form-urlencoded

username=admin&password=secure_password

```
Response:
{
"access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
"token_type": "bearer"
}
```


Use this token in subsequent requests:

GET /api/symbols
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...


### Symbol Management

#### Get all tracked symbols

GET /api/symbols

```
Response:
[
"BTC-USDT",
"ETH-USDT",
"SOL-USDT"
]
```


#### Add a symbol

POST /api/symbols
Content-Type: application/json

{
"symbol": "BTC-USDT"
}

```
Response:
{
"symbol": "BTC-USDT",
"status": "added"
}
```


#### Remove a symbol

DELETE /api/symbols/BTC-USDT

```
Response:
{
"symbol": "BTC-USDT",
"status": "removed"
}
```


### Analysis Results

#### Get analysis for all symbols

GET /api/analysis

```
Response:
[
{
"symbol": "BTC-USDT",
"timestamp": "2023-07-15T14:30:00Z",
"price": 29876.45,
"sentiment": {
"overall": "buy",
"strength": "moderate",
"confidence": 0.72,
"score": 0.45
},
"analysis_summary": "BTC-USDT shows bullish momentum with RSI in neutral territory. Price is trading above key moving averages with positive MACD histogram."
},
{
"symbol": "ETH-USDT",
"timestamp": "2023-07-15T14:30:00Z",
"price": 1876.23,
"sentiment": {
"overall": "neutral",
"strength": "none",
"confidence": 0.65,
"score": 0.05
},
"analysis_summary": "ETH-USDT is consolidating in a range with mixed signals. RSI is neutral at 52.3 and price is near the middle Bollinger Band."
}
]
```


#### Get detailed analysis for a specific symbol

GET /api/analysis/BTC-USDT

```
Response:
{
"symbol": "BTC-USDT",
"timestamp": "2023-07-15T14:30:00Z",
"price": 29876.45,
"indicators": {
"RSI_14": {
"indicator": "RSI_14",
"value": 58.34,
"signal": "neutral",
"strength": 0.0
},
"MACD_12_26_9": {
"indicator": "MACD_12_26_9",
"value": {
"macd": 12.5,
"signal": 9.8,
"histogram": 2.7
},
"signal": "bullish",
"strength": 0.54
},
"BBANDS_20_2": {
"indicator": "BBANDS_20_2",
"value": {
"upper": 30120.45,
"middle": 29850.30,
"lower": 29580.15,
"bandwidth": 0.018,
"percent_b": 0.65
},
"signal": "neutral",
"strength": 0.0
}
},
"sentiment": {
"overall": "buy",
"strength": "moderate",
"confidence": 0.72,
"score": 0.45
},
"analysis_summary": "BTC-USDT shows bullish momentum with RSI in neutral territory. Price is trading above key moving averages with positive MACD histogram."
}
```


#### Get sentiment summary for all symbols

GET /api/analysis/sentiment

```
Response:
{
"BTC-USDT": {
"overall": "buy",
"strength": "moderate",
"confidence": 0.72,
"score": 0.45
},
"ETH-USDT": {
"overall": "neutral",
"strength": "none",
"confidence": 0.65,
"score": 0.05
}
}
```


### Configuration

#### Get current configuration

GET /api/config

```
Response:
{
"analysis": {
"interval": 60,
"timeframes": ["15min", "1hour", "4hour", "1day"],
"indicators": [
"RSI", "MACD", "BBANDS", "SMA", "EMA",
"OBV", "STOCH", "ADX", "FIBONACCI"
]
},
"display": {
"theme": "dark",
"decimal_places": 2,
"show_all_indicators": true
},
"notifications": {
"enabled": false,
"email": "",
"strong_signals_only": true
}
}
```


#### Update configuration

PUT /api/config
Content-Type: application/json

{
"analysis": {
"interval": 30,
"indicators": ["RSI", "MACD", "BBANDS", "SMA", "EMA"]
}
}

```
Response:
{
"status": "success",
"message": "Configuration updated"
}
```


#### Reset configuration to defaults

POST /api/config/reset

```
Response:
{
"status": "success",
"message": "Configuration reset to defaults"
}
```


## For more details, see the [API Documentation](http://localhost:8000/docs) when the server is running.

## Telegram Integration

The KuCoin Spot Analysis Bot includes Telegram integration to send real-time notifications for significant trading signals and allow interaction with the bot through commands.

### Setup Instructions

1. **Create a Telegram Bot**:
    - Open Telegram and search for "BotFather" (@BotFather)
    - Start a chat and send the command `/newbot`
    - Follow the prompts to name your bot and create a username
    - Save the API token provided by BotFather
2. **Configure Your Bot**:
    - Add the following to your `.env` file:

```
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=
TELEGRAM_NOTIFICATIONS_ENABLED=true
```

3. **Get Your Chat ID**:
    - Run the utility script:

```
python -m utils.get_telegram_chat_id
```

    - Send a message to your bot in Telegram
    - The script will display your chat ID
    - Add this ID to your `.env` file:

```
TELEGRAM_CHAT_ID=your_chat_id_here
```

4. **Test the Integration**:
    - Run the test script:

```
python -m utils.test_telegram
```

    - You should receive a test notification in Telegram

### Notification Features

The bot will automatically send you alerts when:

- A symbol develops a strong buy signal
- A symbol develops a strong sell signal
- Any critical system errors occur

Notifications include:

- Current price
- Sentiment strength and direction
- Confidence level
- Key indicator values
- Analysis summary

### Customizing Notifications

You can customize which sentiment levels trigger notifications by modifying the `telegram_notify_on_sentiment` setting in your configuration:

```python
# Default setting (in config/settings.py)
telegram_notify_on_sentiment: list = ["strong buy", "strong sell"]

# To add more notification triggers, modify to include additional sentiments:
telegram_notify_on_sentiment: list = ["strong buy", "strong sell", "moderate buy"]
```


### Security Considerations

- Never share your bot token publicly
- Regenerate your bot token if you suspect it has been compromised
- Consider using a private Telegram group for notifications if multiple people need access


### Troubleshooting

If you're not receiving notifications:

1. Ensure `TELEGRAM_NOTIFICATIONS_ENABLED` is set to `true`
2. Verify your bot token is correct
3. Make sure you've sent at least one message to your bot
4. Check that your chat ID is correctly configured
5. Look for any errors in the application logs
