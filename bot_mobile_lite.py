"""
Lightweight Mobile Trading Bot - No pandas required!
Only needs: requests
"""

import time
import logging
import json
from datetime import datetime
import os
import sys

from bybit_client_lite import BybitClientLite
from twin_range_filter_lite import calculate_signals

try:
    import requests as _requests
except ImportError:
    _requests = None

stop_flag = False

# ─── PHP conversion for demo mode ───────────────────────────────────────────
_PHP_RATE = 56.5       # fallback USD → PHP
_php_last_fetch = 0

def _refresh_php_rate():
    global _PHP_RATE, _php_last_fetch
    if _requests is None:
        return
    try:
        r = _requests.get('https://open.er-api.com/v6/latest/USD', timeout=10)
        if r.status_code == 200:
            rate = r.json().get('rates', {}).get('PHP')
            if rate:
                _PHP_RATE = float(rate)
    except Exception:
        pass
    _php_last_fetch = time.time()

def _php(usd_amount):
    """Convert USD amount to PHP and return formatted string."""
    return f"\u20b1{usd_amount * _PHP_RATE:,.2f}"

# Create user data directory
user_data_dir = os.path.join(os.environ.get('APPDATA', ''), 'TwinRangeFilterBot')
os.makedirs(user_data_dir, exist_ok=True)

# Configure logging
log_file = os.path.join(user_data_dir, 'bot.log')
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file)
    ]
)
logger = logging.getLogger(__name__)


class LiteMobileBot:
    """Ultra-lightweight mobile trading bot"""
    
    # Default risk management values
    DEFAULT_STOP_LOSS_PERCENT = 37
    DEFAULT_TAKE_PROFIT_PERCENT = 150
    
    def __init__(self):
        """Initialize bot"""
        self.config = self.load_config()
        self.state_file = os.path.join(user_data_dir, 'bot_state.json')
        
        self.client = BybitClientLite(
            api_key=self.config['api_key'],
            api_secret=self.config['api_secret'],
            testnet=self.config['testnet']
        )
        self.pairs = self.config['trading_pairs']
        self.last_signals = {pair: 'none' for pair in self.pairs}
        self.running = False
        self.wallet = 0.0
        # Demo position tracking
        self.demo_positions = {}  # {symbol: {side, size, entry, leverage, qty, sl, tp}}
        self.demo_pnl_total = 0.0  # Accumulated realized PnL in demo
        self.demo_state_file = os.path.join(user_data_dir, 'demo_state.json')
        self._load_demo_state()
        # Ensure ZECUSDT leverage is set to 20x
        if 'ZECUSDT' in self.config['leverage']:
            self.config['leverage']['ZECUSDT'] = 20
        logger.info("\ud83d\udcf1 Lite Bot Started")
        logger.info(f"Mode: {'DEMO' if self.config.get('demo', False) else 'TEST' if self.config['testnet'] else 'LIVE'}")
        logger.info(f"Pairs: {len(self.pairs)}")
        # Fetch PHP rate on startup for demo currency display
        if self.config.get('demo', False):
            try:
                _refresh_php_rate()
            except Exception:
                pass
    
    def load_config(self):
        """Load or create config"""
        config_file = 'mobile_config.json'
        
        if not os.path.exists(config_file):
            logger.info("Creating config file...")
            config = {
                "api_key": "YOUR_API_KEY",
                "api_secret": "YOUR_API_SECRET",
                "testnet": True,
                "demo": False,
                "demo_balance": 4800.0,
                "position_mode": "one-way",
                "trading_pairs": ["BTCUSDT", "ETHUSDT", "SOLUSDT", "XRPUSDT", "DOGEUSDT", "ZECUSDT", "FARTCOINUSDT"],
                "leverage": {
                    "BTCUSDT": 35,
                    "ETHUSDT": 35,
                    "SOLUSDT": 35,
                    "XRPUSDT": 35,
                    "DOGEUSDT": 35,
                    "ZECUSDT": 35,
                    "FARTCOINUSDT": 35
                },
                "position_size_percent": 35,
                "timeframe": "60",
                "twin_range_fast_period": 27,
                "twin_range_fast_range": 1.6,
                "twin_range_slow_period": 55,
                "twin_range_slow_range": 2.0,
                "stop_loss_percent": 37,
                "enable_stop_loss": True,
                "take_profit_percent": 150,
                "enable_take_profit": True,
                "check_interval": 60
            }
            with open(config_file, 'w') as f:
                json.dump(config, f, indent=4)
            logger.info(f"Edit {config_file} with your API keys!")
            logger.info("")
            logger.info("IMPORTANT:")
            logger.info("- If testnet = true, get keys from: https://testnet.bybit.com")
            logger.info("- If testnet = false, get keys from: https://www.bybit.com")
            logger.info("- Testnet keys DON'T work on mainnet and vice versa!")
            sys.exit(0)
        
        with open(config_file, 'r') as f:
            config = json.load(f)
        
        # Validate config
        if config['api_key'] == 'YOUR_API_KEY':
            logger.error("Please edit mobile_config.json with your API keys!")
            sys.exit(1)
        
        return config
    
    def save_state(self):
        """Save state"""
        with open(self.state_file, 'w') as f:
            json.dump({'signals': self.last_signals, 'time': datetime.now().isoformat()}, f)
    
    def has_any_position(self):
        """Check if ANY position is open"""
        for symbol in self.pairs:
            pos = self.get_position(symbol)
            if pos['size'] > 0:
                return True
        return False
    
    def get_active_positions_count(self):
        """Return the number of currently open positions across all pairs"""
        count = 0
        for symbol in self.pairs:
            pos = self.get_position(symbol)
            if pos['size'] > 0:
                count += 1
        return count
    
    def has_position_limit(self):
        """Return True if the number of active positions is at or above the limit"""
        max_trades = self.config.get('max_open_trades', 3)
        return self.get_active_positions_count() >= max_trades
    
    def _load_demo_state(self):
        """Load demo positions and PnL from disk"""
        if os.path.exists(self.demo_state_file):
            try:
                with open(self.demo_state_file, 'r') as f:
                    data = json.load(f)
                    self.demo_positions = data.get('positions', {})
                    self.demo_pnl_total = data.get('pnl_total', 0.0)
                    if self.demo_positions:
                        logger.info(f"🎭 Restored {len(self.demo_positions)} demo position(s)")
            except Exception:
                pass

    def _save_demo_state(self):
        """Persist demo positions and PnL to disk"""
        try:
            with open(self.demo_state_file, 'w') as f:
                json.dump({'positions': self.demo_positions,
                           'pnl_total': self.demo_pnl_total,
                           'time': datetime.now().isoformat()}, f, indent=2)
        except Exception:
            pass

    def load_state(self):
        """Load state"""
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, 'r') as f:
                    state = json.load(f)
                    self.last_signals = state.get('signals', self.last_signals)
            except:
                pass
    
    def setup_leverage(self):
        """Setup leverage"""
        for symbol in self.pairs:
            lev = self.config['leverage'].get(symbol, 10)
            if self.client.set_leverage(symbol, lev):
                logger.info(f"✓ {symbol}: {lev}x")
    
    def update_wallet(self):
        """Update balance"""
        if self.config.get('demo', False):
            # Demo balance is stored in PHP; convert to USD for internal use
            base_php = self.config.get('demo_balance', 4800.0)
            base_usd = base_php / _PHP_RATE if _PHP_RATE else base_php
            unrealised = 0.0
            for sym, dp in self.demo_positions.items():
                ticker = self.client.get_ticker(sym)
                price = float(ticker.get('lastPrice', 0)) if ticker else 0
                if price and dp['entry']:
                    if dp['side'] == 'Buy':
                        unrealised += (price - dp['entry']) / dp['entry'] * dp['size']
                    else:
                        unrealised += (dp['entry'] - price) / dp['entry'] * dp['size']
            self.wallet = base_usd + unrealised
            return self.wallet
        bal = self.client.get_wallet_balance()
        if bal:
            for coin in bal.get('list', [{}])[0].get('coin', []):
                if coin.get('coin') == 'USDT':
                    self.wallet = float(coin.get('walletBalance', 0))
                    return self.wallet
        return 0.0
    
    def calc_size(self, symbol):
        """Calculate position size"""
        self.update_wallet()
        return self.wallet * (self.config['position_size_percent'] / 100)
    
    def get_position(self, symbol):
        """Get position (uses simulated data in demo mode)"""
        if self.config.get('demo', False):
            dp = self.demo_positions.get(symbol)
            if dp:
                # Calculate unrealised PnL from live price
                ticker = self.client.get_ticker(symbol)
                price = float(ticker.get('lastPrice', 0)) if ticker else 0
                if price and dp['entry']:
                    if dp['side'] == 'Buy':
                        pnl = (price - dp['entry']) / dp['entry'] * dp['size']
                    else:
                        pnl = (dp['entry'] - price) / dp['entry'] * dp['size']
                else:
                    pnl = 0
                return {
                    'side': dp['side'],
                    'size': dp['size'],
                    'entry': dp['entry'],
                    'pnl': pnl,
                    'leverage': dp['leverage']
                }
            return {'side': 'None', 'size': 0, 'entry': 0, 'pnl': 0, 'leverage': 0}

        pos = self.client.get_position(symbol)
        if not pos:
            return {'side': 'None', 'size': 0, 'entry': 0, 'pnl': 0}
        
        def safe(val, default=0):
            try:
                return float(val) if val and val != '' else default
            except:
                return default
        
        return {
            'side': pos.get('side', 'None'),
            'size': safe(pos.get('size')),
            'entry': safe(pos.get('avgPrice')),
            'pnl': safe(pos.get('unrealisedPnl')),
            'leverage': safe(pos.get('leverage'))
        }
    
    def close_pos(self, symbol):
        """Close position"""
        pos = self.get_position(symbol)
        if pos['size'] == 0:
            return True
        
        side = 'Sell' if pos['side'] == 'Buy' else 'Buy'
        logger.info(f"Closing {pos['side']} {symbol}")
        
        if self.config.get('demo', False):
            dp = self.demo_positions.get(symbol)
            if dp:
                # Calculate realized PnL
                ticker = self.client.get_ticker(symbol)
                price = float(ticker.get('lastPrice', 0)) if ticker else dp['entry']
                if dp['side'] == 'Buy':
                    pnl = (price - dp['entry']) / dp['entry'] * dp['size']
                else:
                    pnl = (dp['entry'] - price) / dp['entry'] * dp['size']
                self.demo_pnl_total += pnl
                # Update demo wallet balance
                demo_bal = self.config.get('demo_balance', 4800.0)
                self.config['demo_balance'] = demo_bal + pnl * _PHP_RATE
                logger.info(f"\ud83c\udfad DEMO CLOSE {pos['side']} {symbol} | PnL: {_php(pnl)} | Wallet: {_php(self.config['demo_balance'] / _PHP_RATE)}")
                del self.demo_positions[symbol]
                self._save_demo_state()
            else:
                logger.info(f"🎭 DEMO: No position to close for {symbol}")
            return True
        
        resp = self.client.place_order(symbol, side, pos['size'], reduce_only=True)
        return resp.get('retCode') == 0
    
    def open_long(self, symbol):
        """Open long"""
        # Close all short positions across all pairs first
        for sym in self.pairs:
            pos = self.get_position(sym)
            if pos['side'] == 'Sell' and pos['size'] > 0:
                logger.info(f"Closing SHORT position on {sym} before opening LONG on {symbol}")
                if not self.close_pos(sym):
                    logger.error(f"Failed to close short position on {sym}")
                time.sleep(1)
        
        # Only allow up to max_open_trades positions at a time (across all pairs)
        if self.has_position_limit():
            max_t = self.config.get('max_open_trades', 3)
            logger.info(f"❌ {max_t} active positions already open, cannot open LONG on {symbol}")
            return False
        
        usd = self.calc_size(symbol)
        lev = self.config['leverage'].get(symbol, 35)
        
        # Set leverage
        if not self.client.set_leverage(symbol, lev):
            logger.error(f"Failed to set leverage for {symbol}")
            return False
        
        qty = self.client.calculate_qty(symbol, usd, lev)
        
        if qty == 0:
            logger.error(f"Could not calculate quantity for {symbol}")
            return False
        
        # Get current price for SL/TP calculation
        ticker = self.client.get_ticker(symbol)
        if not ticker:
            logger.error(f"Failed to get ticker for {symbol}")
            return False
        
        entry_price = float(ticker.get('lastPrice', 0))
        if entry_price == 0:
            logger.error(f"Invalid price for {symbol}")
            return False
        
        # Calculate stop loss and take profit prices for LONG
        # IMPORTANT: Account for leverage! With 35x leverage, 1% price move = 35% ROI
        stop_loss_price = None
        take_profit_price = None
        
        if self.config.get('enable_stop_loss', True):
            sl_percent = self.config.get('stop_loss_percent', self.DEFAULT_STOP_LOSS_PERCENT)
            # Price move needed = ROI% / leverage
            price_move_percent = sl_percent / lev
            stop_loss_price = entry_price * (1 - price_move_percent / 100)
        
        if self.config.get('enable_take_profit', True):
            tp_percent = self.config.get('take_profit_percent', self.DEFAULT_TAKE_PROFIT_PERCENT)
            # Price move needed = ROI% / leverage
            price_move_percent = tp_percent / lev
            take_profit_price = entry_price * (1 + price_move_percent / 100)
        
        _is_demo = self.config.get('demo', False)
        _amt = _php(usd) if _is_demo else f'${usd:.2f}'
        logger.info(f"🟢 LONG {symbol} {_amt} @ ${entry_price:.2f} | {lev}x")
        if stop_loss_price:
            actual_price_move = ((entry_price - stop_loss_price) / entry_price) * 100
            logger.info(f"   ⛔ SL: ${stop_loss_price:.2f} ({actual_price_move:.2f}% price = {sl_percent}% ROI)")
        if take_profit_price:
            actual_price_move = ((take_profit_price - entry_price) / entry_price) * 100
            logger.info(f"   🎯 TP: ${take_profit_price:.2f} ({actual_price_move:.2f}% price = {tp_percent}% ROI)")
        
        if _is_demo:
            self.demo_positions[symbol] = {
                'side': 'Buy',
                'size': usd,
                'entry': entry_price,
                'leverage': lev,
                'qty': qty,
                'sl': stop_loss_price,
                'tp': take_profit_price,
                'time': datetime.now().isoformat()
            }
            self._save_demo_state()
            logger.info(f"🎭 DEMO OPENED LONG {symbol} {_php(usd)} @ ${entry_price:.2f} | {lev}x")
            return True
        
        resp = self.client.place_order(symbol, 'Buy', qty, stop_loss=stop_loss_price, take_profit=take_profit_price)
        return resp.get('retCode') == 0
    
    def open_short(self, symbol):
        """Open short"""
        # Close all long positions across all pairs first
        for sym in self.pairs:
            pos = self.get_position(sym)
            if pos['side'] == 'Buy' and pos['size'] > 0:
                logger.info(f"Closing LONG position on {sym} before opening SHORT on {symbol}")
                if not self.close_pos(sym):
                    logger.error(f"Failed to close long position on {sym}")
                time.sleep(1)
        
        # Only allow up to max_open_trades positions at a time (across all pairs)
        if self.has_position_limit():
            max_t = self.config.get('max_open_trades', 3)
            logger.info(f"❌ {max_t} active positions already open, cannot open SHORT on {symbol}")
            return False
        
        usd = self.calc_size(symbol)
        lev = self.config['leverage'].get(symbol, 35)
        
        # Set leverage
        if not self.client.set_leverage(symbol, lev):
            logger.error(f"Failed to set leverage for {symbol}")
            return False
        
        qty = self.client.calculate_qty(symbol, usd, lev)
        
        if qty == 0:
            logger.error(f"Could not calculate quantity for {symbol}")
            return False
        
        # Get current price for SL/TP calculation
        ticker = self.client.get_ticker(symbol)
        if not ticker:
            logger.error(f"Failed to get ticker for {symbol}")
            return False
        
        entry_price = float(ticker.get('lastPrice', 0))
        if entry_price == 0:
            logger.error(f"Invalid price for {symbol}")
            return False
        
        # Calculate stop loss and take profit prices for SHORT
        # IMPORTANT: Account for leverage! With 35x leverage, 1% price move = 35% ROI
        stop_loss_price = None
        take_profit_price = None
        
        if self.config.get('enable_stop_loss', True):
            sl_percent = self.config.get('stop_loss_percent', self.DEFAULT_STOP_LOSS_PERCENT)
            # For SHORT: stop loss is ABOVE entry price (price goes up = loss)
            # Price move needed = ROI% / leverage
            price_move_percent = sl_percent / lev
            stop_loss_price = entry_price * (1 + price_move_percent / 100)
        
        if self.config.get('enable_take_profit', True):
            tp_percent = self.config.get('take_profit_percent', self.DEFAULT_TAKE_PROFIT_PERCENT)
            # For SHORT: take profit is BELOW entry price (price goes down = profit)
            # Price move needed = ROI% / leverage
            price_move_percent = tp_percent / lev
            take_profit_price = entry_price * (1 - price_move_percent / 100)
        
        _is_demo = self.config.get('demo', False)
        _amt = _php(usd) if _is_demo else f'${usd:.2f}'
        logger.info(f"🔴 SHORT {symbol} {_amt} @ ${entry_price:.2f} | {lev}x")
        if stop_loss_price:
            actual_price_move = ((stop_loss_price - entry_price) / entry_price) * 100
            logger.info(f"   ⛔ SL: ${stop_loss_price:.2f} ({actual_price_move:.2f}% price = {sl_percent}% ROI)")
        if take_profit_price:
            actual_price_move = ((entry_price - take_profit_price) / entry_price) * 100
            logger.info(f"   🎯 TP: ${take_profit_price:.2f} ({actual_price_move:.2f}% price = {tp_percent}% ROI)")
        
        if _is_demo:
            self.demo_positions[symbol] = {
                'side': 'Sell',
                'size': usd,
                'entry': entry_price,
                'leverage': lev,
                'qty': qty,
                'sl': stop_loss_price,
                'tp': take_profit_price,
                'time': datetime.now().isoformat()
            }
            self._save_demo_state()
            logger.info(f"🎭 DEMO OPENED SHORT {symbol} {_php(usd)} @ ${entry_price:.2f} | {lev}x")
            return True
        
        resp = self.client.place_order(symbol, 'Sell', qty, stop_loss=stop_loss_price, take_profit=take_profit_price)
        return resp.get('retCode') == 0
    
    def check_stop_loss_take_profit(self):
        """Check stop loss and take profit based on ROI"""
        if not self.config.get('enable_stop_loss', True) and not self.config.get('enable_take_profit', True):
            return
        
        for symbol in self.pairs:
            if stop_flag:
                break
            try:
                pos = self.get_position(symbol)
                if pos['size'] == 0:
                    continue
                
                ticker = self.client.get_ticker(symbol)
                if not ticker:
                    continue
                
                price = float(ticker.get('lastPrice', 0))
                if pos['entry'] == 0 or price == 0 or pos['leverage'] == 0:
                    continue
                
                # Calculate ROI (Return on Investment) percentage
                if pos['side'] == 'Buy':
                    roi = ((price - pos['entry']) / pos['entry']) * pos['leverage'] * 100
                else:
                    roi = ((pos['entry'] - price) / pos['entry']) * pos['leverage'] * 100
                
                # Check Stop Loss
                if self.config.get('enable_stop_loss', True):
                    stop_loss_percent = self.config.get('stop_loss_percent', self.DEFAULT_STOP_LOSS_PERCENT)
                    if roi <= -stop_loss_percent:
                        logger.warning(f"🛑 STOP LOSS {symbol} - ROI: {roi:.2f}%")
                        self.close_pos(symbol)
                        continue
                
                # Check Take Profit
                if self.config.get('enable_take_profit', True):
                    take_profit_percent = self.config.get('take_profit_percent', self.DEFAULT_TAKE_PROFIT_PERCENT)
                    if roi >= take_profit_percent:
                        logger.info(f"💰 TAKE PROFIT {symbol} - ROI: {roi:.2f}%")
                        self.close_pos(symbol)
                        
            except Exception as e:
                logger.error(f"SL/TP error {symbol}: {e}")
    
    def check_signals(self):
        """Check signals"""
        for symbol in self.pairs:
            if stop_flag:
                break
            try:
                # Get klines (already returns list of lists)
                candles = self.client.get_klines(symbol, self.config['timeframe'], limit=200)
                
                if not candles:
                    continue
                
                # Calculate Twin Range Filter signals
                result = calculate_signals(
                    candles,
                    fast_period=self.config.get('twin_range_fast_period', 27),
                    fast_range=self.config.get('twin_range_fast_range', 1.6),
                    slow_period=self.config.get('twin_range_slow_period', 55),
                    slow_range=self.config.get('twin_range_slow_range', 2.0)
                )
                
                # Determine signal
                if result['long_signal']:
                    signal = 'long'
                elif result['short_signal']:
                    signal = 'short'
                else:
                    signal = 'none'
                
                # Execute if new signal
                if signal != 'none' and signal != self.last_signals[symbol]:
                    self.last_signals[symbol] = signal
                    
                    # Only allow up to max_open_trades positions at a time
                    if self.has_position_limit():
                        max_t = self.config.get('max_open_trades', 3)
                        logger.info(f"❌ {max_t} active positions already open, cannot trade {symbol} ({signal})")
                    elif signal == 'long':
                        self.open_long(symbol)
                    elif signal == 'short':
                        self.open_short(symbol)
                    
                    self.save_state()
                elif signal == 'none':
                    self.last_signals[symbol] = 'none'
                
            except Exception as e:
                logger.error(f"{symbol}: {e}")
    
    def status(self):
        """Print status"""
        logger.info("=" * 40)
        self.update_wallet()
        _is_demo = self.config.get('demo', False)
        if _is_demo:
            logger.info(f"💰 {_php(self.wallet)}")
        else:
            logger.info(f"💰 ${self.wallet:.2f}")
        
        total_pnl = 0
        active = 0
        
        for symbol in self.pairs:
            pos = self.get_position(symbol)
            ticker = self.client.get_ticker(symbol)
            price = float(ticker.get('lastPrice', 0)) if ticker else 0
            
            if pos['size'] > 0:
                if _is_demo:
                    logger.info(f"{symbol}: {pos['side']} {_php(pos['pnl'])} @ {price:.4f}")
                else:
                    logger.info(f"{symbol}: {pos['side']} ${pos['pnl']:.2f} @ {price:.4f}")
                total_pnl += pos['pnl']
                active += 1
            else:
                logger.info(f"{symbol}: - @ {price:.4f}")
        
        if _is_demo:
            logger.info(f"Active: {active} | PnL: {_php(total_pnl)}")
        else:
            logger.info(f"Active: {active} | PnL: ${total_pnl:.2f}")
        logger.info("=" * 40)
    
    def run(self):
        """Main loop"""
        logger.info("=" * 40)
        logger.info("🤖 TRADING BOT")
        logger.info("=" * 40)
        
        self.load_state()
        self.setup_leverage()
        self.status()
        self.running = True
        
        logger.info(f"⏰ Check every {self.config['check_interval']}s")
        logger.info("Ctrl+C to stop")
        
        last_status = time.time()
        
        try:
            while self.running and not stop_flag:
                if stop_flag:
                    logger.info("Stop flag detected, stopping bot...")
                    break
                # Reload config for live updates
                try:
                    with open('mobile_config.json', 'r') as f:
                        self.config = json.load(f)
                except Exception:
                    pass
                self.check_stop_loss_take_profit()
                if stop_flag:
                    break
                self.check_signals()
                
                if time.time() - last_status > 300:
                    self.status()
                    last_status = time.time()
                
                # Sleep in 1-second intervals to allow quick stopping
                for _ in range(self.config['check_interval']):
                    if stop_flag:
                        logger.info("Stop flag detected during sleep, stopping bot...")
                        break
                    time.sleep(1)
                if stop_flag:
                    break
        
        except KeyboardInterrupt:
            logger.info("\n👋 Stopping...")
            self.running = False
        except Exception as e:
            logger.error(f"Error: {e}")
            self.running = False
        
        self.save_state()
        self.status()
        logger.info("✓ Stopped")


def main():
    bot = LiteMobileBot()
    
    logger.info("=" * 50)
    logger.info(f"Testing {'TESTNET' if bot.config['testnet'] else 'MAINNET'} connection...")
    logger.info("=" * 50)
    
    # Test public endpoint first (doesn't need auth)
    logger.info("Step 1: Testing market data (no auth)...")
    for i in range(3):
        ticker = bot.client.get_ticker('BTCUSDT')
        if ticker and ticker.get('lastPrice'):
            logger.info(f"✅ Market data OK - BTC: ${ticker.get('lastPrice')}")
            break
        logger.warning(f"Retry {i+1}/3...")
        time.sleep(2)
    else:
        logger.error("❌ Cannot reach Bybit API")
        logger.info("Check your internet connection")
        return
    
    # Test authenticated endpoint
    logger.info("Step 2: Testing API keys...")
    balance = bot.client.get_wallet_balance()
    if balance and balance.get('list'):
        logger.info("✅ API keys valid!")
        
        # Show balance
        for coin in balance.get('list', [{}])[0].get('coin', []):
            if coin.get('coin') == 'USDT':
                logger.info(f"💰 USDT Balance: {coin.get('walletBalance', 'N/A')}")
        
        logger.info("=" * 50)
        bot.run()
    else:
        logger.error("❌ API key authentication failed")
        logger.info("")
        logger.info("⚠️ COMMON ISSUE: Bybit testnet API often has problems")
        logger.info("")
        logger.info("SOLUTION: Use MAINNET with real API keys")
        logger.info("(Don't worry - just use small position sizes!)")
        logger.info("")
        logger.info("Steps to switch to mainnet:")
        logger.info("1. Edit mobile_config.json")
        logger.info("2. Change: \"testnet\": true → \"testnet\": false")
        logger.info("3. Use API keys from: https://www.bybit.com (not testnet)")
        logger.info("4. Set small position_size_percent (like 10-20%)")
        logger.info("5. Use lower leverage (10-25x instead of 100x)")
        logger.info("")
        logger.info("Alternative troubleshooting:")
        logger.info("- Wait a few hours and try testnet again")
        logger.info("- Verify API key has 'Derivatives Contract' permission")
        logger.info("- Check API key hasn't expired")
        return


if __name__ == "__main__":
    main()
