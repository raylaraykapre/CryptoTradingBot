# Twin Range Filter Trading Bot

Automated trading bot for Bybit derivatives using the Twin Range Filter strategy.

## Features

- **Twin Range Filter Strategy**: Implements the popular Twin Range Filter indicator
- **Multi-symbol trading**: Supports BTCUSDT, ETHUSDT, SOLUSDT, XRPUSDT, DOGEUSDT, ZECUSDT, FARTCOINUSDT (configurable)
- **Position management**: Automatically closes opposite positions before opening new ones
- **ROI-based Stop Loss & Take Profit**: Properly calculated based on leverage
- **Bybit integration**: Connects to Bybit USDT perpetual futures
- **Testnet support**: Test your strategy safely before going live
- **Mobile optimized**: Lightweight version for Android devices
- **Web dashboard**: Control and monitor from any device

## Strategy Overview

The Twin Range Filter indicator uses two smoothed range filters to identify trend direction:

- **Long Signal**: When both fast and slow filters show uptrend
- **Short Signal**: When both fast and slow filters show downtrend

### Parameters

- **Fast Period**: 27 (default) - Period for fast range filter
- **Fast Range**: 1.6 (default) - Multiplier for fast range
- **Slow Period**: 55 (default) - Period for slow range filter
- **Slow Range**: 2.0 (default) - Multiplier for slow range

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Get Bybit API Keys

1. Go to [Bybit](https://www.bybit.com)
2. Navigate to API Management (Account → API)
3. Create a new API key with the following permissions:
   - Read-Write
   - Contract (USDT Perpetual)
4. **For testing**, use the testnet: [Bybit Testnet](https://testnet.bybit.com)

### 3. Configure the Bot

Edit `mobile_config.json` (created automatically on first run):

```json
{
    "api_key": "your_api_key_here",
    "api_secret": "your_api_secret_here",
    "testnet": true,
    "demo": false,
    "trading_pairs": ["BTCUSDT", "ETHUSDT", "SOLUSDT"],
    "leverage": {
        "BTCUSDT": 35,
        "ETHUSDT": 35,
        "SOLUSDT": 35
    },
    "position_size_percent": 35,
    "timeframe": "60",
    "twin_range_fast_period": 27,
    "twin_range_fast_range": 1.6,
    "twin_range_slow_period": 55,
    "twin_range_slow_range": 2.0,
    "stop_loss_percent": 37,
    "enable_stop_loss": true,
    "take_profit_percent": 150,
    "enable_take_profit": true,
    "check_interval": 60
}
```

```

### 4. Run the Bot

#### Option 1: Command Line
```bash
python bot_mobile_lite.py
```

#### Option 2: Web Dashboard (Recommended for mobile)
```bash
python web_dashboard.py
```
Then access from any device:
- Local: http://localhost:5000
- Network: http://YOUR_IP:5000

## Mobile Access

### Android Phone Setup

1. **Start the dashboard** on your computer:
   ```bash
   py web_dashboard.py
   ```

2. **Find your computer's IP address**:
   - Windows: Open Command Prompt → `ipconfig` → Look for "IPv4 Address"

3. **Connect from phone**:
   - Open browser on phone
   - Go to: `http://YOUR_IP:5000`
   - Example: `http://192.168.1.100:5000`

### Features Available on Mobile
- ✅ Start/Stop bot
- ✅ Real-time position monitoring
- ✅ Emergency position closure
- ✅ Wallet balance display
- ✅ PnL tracking

## Strategy Logic

### Twin Range Filter Indicator

The Twin Range Filter combines two smoothed range filters:

1. **Fast Filter**: Quick trend detection (27 period, 1.6 range)
2. **Slow Filter**: Trend confirmation (55 period, 2.0 range)
3. **Signal Generation**:
   - LONG when both filters show uptrend
   - SHORT when both filters show downtrend

### Position Management

- When a **LONG** signal appears:
  1. **Close ALL short positions FIRST**
  2. Open new LONG position
  3. Set Stop Loss at 42% ROI loss
  4. Set Take Profit at 150% ROI gain

- When a **SHORT** signal appears:
  1. **Close ALL long positions FIRST**
  2. Open new SHORT position
  3. Set Stop Loss at 42% ROI loss
  4. Set Take Profit at 150% ROI gain

### Stop Loss & Take Profit (ROI-Based)

**CRITICAL**: SL/TP are calculated based on ROI (Return on Investment), accounting for leverage:

**For LONG positions:**
```
Stop Loss Price = Entry Price × (1 - (42 / Leverage) / 100)
Take Profit Price = Entry Price × (1 + (150 / Leverage) / 100)
```

**For SHORT positions:**
```
Stop Loss Price = Entry Price × (1 + (42 / Leverage) / 100)
Take Profit Price = Entry Price × (1 - (150 / Leverage) / 100)
```

**Example with 100x leverage:**
- 42% ROI loss = 0.42% price move
- 150% ROI gain = 1.5% price move

## Configuration Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `ATR_PERIOD` | 5 | ATR calculation period |
| `SUPERTREND_FACTOR` | 3.0 | ATR multiplier for bands |
| `POSITION_SIZE_PERCENT` | 35 | % of wallet balance per trade |
| `STOP_LOSS_PERCENT` | 42 | ROI % loss to trigger stop loss |
| `TAKE_PROFIT_PERCENT` | 150 | ROI % gain to trigger take profit |
| `TIMEFRAME` | "5" | Candle timeframe in minutes |
| `CHECK_INTERVAL` | 60 | Seconds between signal checks |

## Files

```
Bybit-Auto-Bot/
├── bot.py                 # Main bot script
├── bot_mobile_lite.py     # Lightweight mobile bot
├── web_bot.py             # Web interface bot
├── bybit_client.py        # Bybit API client (pandas)
├── bybit_client_lite.py   # Bybit API client (no pandas)
├── supertrend.py          # Supertrend indicator (pandas)
├── supertrend_lite.py     # Supertrend indicator (no pandas)
├── android_app/           # Android app files
├── templates/             # Web UI templates
├── requirements.txt       # Python dependencies
├── trading_bot.log        # Log file (created on run)
└── README.md              # This file
```

## Safety Recommendations

1. **Always test on testnet first** before using real funds
2. **Start with small position sizes** when going live
3. **Monitor the bot** regularly, especially in the beginning
4. **Set appropriate leverage** - lower is safer
5. **Never share your API keys**

## Testnet vs Mainnet

- **Testnet**: Set `USE_TESTNET = True` in config.py
  - Get testnet API keys from: https://testnet.bybit.com
  - Uses fake money for testing
  
- **Mainnet**: Set `USE_TESTNET = False` in config.py
  - Get mainnet API keys from: https://www.bybit.com
  - Uses real money - BE CAREFUL!

## Troubleshooting

### "API Error: Invalid API Key"
- Check that your API key and secret are correct
- Ensure you're using testnet keys with testnet mode (or mainnet with mainnet)

### "API Error: Insufficient balance"
- Top up your account balance
- Reduce position size in config

### No signals generated
- The strategy may be waiting for a valid signal
- Check that the market is active
- Verify the timeframe is appropriate

## Disclaimer

This bot is for educational purposes. Trading cryptocurrencies involves substantial risk of loss. The Supertrend strategy is a trend-following system that works best in trending markets but can generate false signals in ranging markets. Always do your own research and never trade with money you cannot afford to lose.

## License

MIT License - See LICENSE file for details

Copyright (c) 2026 beaver

Portions Copyright (c) colinmck (Original Twin Range Filter Logic)

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
