"""
Trading Wobot - Full HUD Launcher
"""

import tkinter as tk
from tkinter import messagebox, scrolledtext, font as tkfont
import subprocess
import os
import json
import threading
import queue
import logging
import time
import sys
import gc
import requests

import bot_mobile_lite

# ─── Globals ────────────────────────────────────────────────────────────────────
bot_thread = None
log_queue = queue.Queue()
bot_start_time = None
last_cycle_time = None          # timestamp of last cycle start

# ─── Logging bridge ─────────────────────────────────────────────────────────────
class QueueHandler(logging.Handler):
    def __init__(self, q):
        super().__init__()
        self.q = q
    def emit(self, record):
        self.q.put(self.format(record))

queue_handler = QueueHandler(log_queue)
queue_handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
logging.getLogger().addHandler(queue_handler)
logging.getLogger().setLevel(logging.INFO)

# Monkey-patch bot_mobile_lite.time.sleep so we can track cycle timing
_original_sleep = time.sleep

# ─── Colour palette ─────────────────────────────────────────────────────────────
BG           = "#1a1a2e"
BG_CARD      = "#16213e"
BG_CARD_ALT  = "#0f3460"
FG           = "#e0e0e0"
FG_DIM       = "#7a7a8a"
ACCENT       = "#00d2ff"
GREEN        = "#00e676"
RED          = "#ff1744"
ORANGE       = "#ffa726"
BTN_START_BG = "#00c853"
BTN_STOP_BG  = "#d50000"
BTN_SET_BG   = "#2979ff"
BTN_PAIR_BG  = "#7c4dff"
BTN_DEMO_BG  = "#ff6f00"
BTN_REAL_BG  = "#00b8d4"

# ─── PHP conversion ──────────────────────────────────────────────────────────
PHP_RATE = 56.5          # fallback USDT → PHP rate
_php_last_fetch = 0

# ─── Helpers ─────────────────────────────────────────────────────────────────────

def _app_dir():
    """Directory where the exe (or script) lives."""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def _config_path():
    return os.path.join(_app_dir(), 'mobile_config.json')


def load_config():
    p = _config_path()
    if os.path.exists(p):
        with open(p, 'r') as f:
            return json.load(f)
    return {}


def save_config(cfg):
    with open(_config_path(), 'w') as f:
        json.dump(cfg, f, indent=4)


def fmt_uptime(secs):
    h, rem = divmod(int(secs), 3600)
    m, s = divmod(rem, 60)
    return f"{h:02d}:{m:02d}:{s:02d}"


def _find_bot_instance():
    """Walk GC to locate the live LiteMobileBot."""
    for obj in gc.get_objects():
        if isinstance(obj, bot_mobile_lite.LiteMobileBot):
            return obj
    return None


def _refresh_php_rate():
    """Fetch live USD→PHP exchange rate (non-blocking)."""
    global PHP_RATE, _php_last_fetch
    try:
        r = requests.get('https://open.er-api.com/v6/latest/USD', timeout=10)
        if r.status_code == 200:
            rate = r.json().get('rates', {}).get('PHP')
            if rate:
                PHP_RATE = float(rate)
    except Exception:
        pass
    _php_last_fetch = time.time()


def _php(usd):
    """Format a USDT amount as Philippine Peso."""
    return f"\u20b1{usd * PHP_RATE:,.2f}"


# ═══════════════════════════════════════════════════════════════════════════════
#  Main Application
# ═══════════════════════════════════════════════════════════════════════════════
class TradingWobotApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Trading Wobot")
        self.root.geometry("960x750")
        self.root.minsize(860, 680)
        self.root.configure(bg=BG)
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        # icon
        try:
            ico = os.path.join(_app_dir(), 'icon.ico')
            if os.path.exists(ico):
                self.root.iconbitmap(ico)
        except Exception:
            pass

        # ── fonts ────────────────────────────────────────────────────────────
        self.f_title  = tkfont.Font(family="Segoe UI", size=18, weight="bold")
        self.f_head   = tkfont.Font(family="Segoe UI", size=11, weight="bold")
        self.f_body   = tkfont.Font(family="Segoe UI", size=10)
        self.f_mono   = tkfont.Font(family="Consolas", size=9)
        self.f_big    = tkfont.Font(family="Segoe UI", size=14, weight="bold")
        self.f_sig    = tkfont.Font(family="Segoe UI", size=9, slant="italic")
        self.f_small  = tkfont.Font(family="Segoe UI", size=8)

        # ── state ────────────────────────────────────────────────────────────
        self.running = False
        self.pair_filter = None          # None = all pairs, else a single symbol string
        self._all_pairs = []             # populated from config

        self._build_ui()

        # Fetch PHP rate on startup (in background)
        threading.Thread(target=_refresh_php_rate, daemon=True).start()

        # periodic updates
        self._poll_logs()
        self._tick_uptime()
        self._tick_interval()
        self._tick_config()
        self._refresh_data_loop()
        self._refresh_php_rate_loop()

    # ─────────────────────────────────────────────────────────────────────────
    #  UI
    # ─────────────────────────────────────────────────────────────────────────
    def _build_ui(self):
        # ── Title row ────────────────────────────────────────────────────────
        top = tk.Frame(self.root, bg=BG)
        top.pack(fill=tk.X, padx=16, pady=(12, 4))

        tk.Label(top, text="Trading Wobot", font=self.f_title,
                 bg=BG, fg=ACCENT).pack(side=tk.LEFT)

        self.lbl_status = tk.Label(top, text="●  STOPPED", font=self.f_head,
                                   bg=BG, fg=RED)
        self.lbl_status.pack(side=tk.RIGHT, padx=8)

        self.lbl_uptime = tk.Label(top, text="", font=self.f_body,
                                   bg=BG, fg=FG_DIM)
        self.lbl_uptime.pack(side=tk.RIGHT, padx=8)

        # ── Button row ──────────────────────────────────────────────────────
        brow = tk.Frame(self.root, bg=BG)
        brow.pack(fill=tk.X, padx=16, pady=6)

        _bc = dict(relief=tk.FLAT, bd=0, padx=18, pady=8,
                   font=self.f_head, cursor="hand2", activeforeground="#fff")

        self.btn_start = tk.Button(brow, text="▶  Start Bot",
                                   bg=BTN_START_BG, fg="#fff",
                                   activebackground="#00a844",
                                   command=self._start_bot, **_bc)
        self.btn_start.pack(side=tk.LEFT, padx=(0, 6))

        self.btn_stop = tk.Button(brow, text="■  Stop Bot",
                                  bg=BTN_STOP_BG, fg="#fff",
                                  activebackground="#b71c1c",
                                  command=self._stop_bot,
                                  state=tk.DISABLED, **_bc)
        self.btn_stop.pack(side=tk.LEFT, padx=(0, 6))

        self.btn_settings = tk.Button(brow, text="⚙  Settings",
                                      bg=BTN_SET_BG, fg="#fff",
                                      activebackground="#1565c0",
                                      command=self._open_settings, **_bc)
        self.btn_settings.pack(side=tk.LEFT, padx=(0, 6))

        # Pair filter button
        self.btn_pair = tk.Button(brow, text="⊞  All Pairs",
                                  bg=BTN_PAIR_BG, fg="#fff",
                                  activebackground="#651fff",
                                  command=self._toggle_pair_filter, **_bc)
        self.btn_pair.pack(side=tk.LEFT, padx=(0, 6))

        # Demo / Real toggle button
        cfg = load_config()
        is_demo = cfg.get('demo', False)
        self.btn_mode = tk.Button(
            brow,
            text="🎭  DEMO" if is_demo else "💹  REAL",
            bg=BTN_DEMO_BG if is_demo else BTN_REAL_BG,
            fg="#fff",
            activebackground="#e65100" if is_demo else "#00838f",
            command=self._toggle_demo, **_bc)
        self.btn_mode.pack(side=tk.LEFT)

        # ── Info cards ───────────────────────────────────────────────────────
        cards = tk.Frame(self.root, bg=BG)
        cards.pack(fill=tk.X, padx=16, pady=6)
        cards.columnconfigure(0, weight=1)
        cards.columnconfigure(1, weight=1)
        cards.columnconfigure(2, weight=1)
        cards.columnconfigure(3, weight=1)
        cards.columnconfigure(4, weight=1)

        self.card_wallet   = self._card(cards, "Wallet Balance", "\u20b10.00", 0, 0)
        self.card_pnl      = self._card(cards, "Unrealised PnL", "\u20b10.00", 0, 1)
        self.card_interval = self._card(cards, "Next Check In",  "--:--", 0, 2)
        self.card_poscount = self._card(cards, "Open Positions", "0 / 3", 0, 3)

        # Mode card
        cfg_mode = load_config()
        mode_txt = "DEMO" if cfg_mode.get('demo', False) else "REAL"
        mode_clr = ORANGE if cfg_mode.get('demo', False) else GREEN
        self.card_mode = self._card(cards, "Trading Mode", mode_txt, 0, 4)
        self.card_mode.config(fg=mode_clr)

        # ── Positions panel ──────────────────────────────────────────────────
        pos = tk.Frame(self.root, bg=BG)
        pos.pack(fill=tk.X, padx=16, pady=6)
        pos.columnconfigure(0, weight=1)
        pos.columnconfigure(1, weight=1)

        # LONG side
        lf = tk.LabelFrame(pos, text="  LONG Positions  ", font=self.f_head,
                            bg=BG_CARD, fg=GREEN, bd=1, relief=tk.GROOVE)
        lf.grid(row=0, column=0, sticky="nsew", padx=(0, 4))
        self.lst_long = tk.Listbox(lf, bg=BG_CARD, fg=GREEN, font=self.f_mono,
                                   height=5, bd=0, highlightthickness=0,
                                   selectbackground=BG_CARD_ALT)
        self.lst_long.pack(fill=tk.BOTH, expand=True, padx=6, pady=4)
        self.lst_long.insert(tk.END, "  No open long positions")

        # SHORT side
        sf = tk.LabelFrame(pos, text="  SHORT Positions  ", font=self.f_head,
                            bg=BG_CARD, fg=RED, bd=1, relief=tk.GROOVE)
        sf.grid(row=0, column=1, sticky="nsew", padx=(4, 0))
        self.lst_short = tk.Listbox(sf, bg=BG_CARD, fg=RED, font=self.f_mono,
                                    height=5, bd=0, highlightthickness=0,
                                    selectbackground=BG_CARD_ALT)
        self.lst_short.pack(fill=tk.BOTH, expand=True, padx=6, pady=4)
        self.lst_short.insert(tk.END, "  No open short positions")

        # ── Log area ─────────────────────────────────────────────────────────
        logf = tk.LabelFrame(self.root, text="  Bot Logs  ", font=self.f_head,
                             bg=BG_CARD, fg=ACCENT, bd=1, relief=tk.GROOVE)
        logf.pack(fill=tk.BOTH, expand=True, padx=16, pady=(6, 2))

        self.log_text = scrolledtext.ScrolledText(
            logf, wrap=tk.WORD, bg="#0d1117", fg="#c9d1d9",
            font=self.f_mono, bd=0, insertbackground=FG,
            selectbackground="#264f78", highlightthickness=0)
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)
        self.log_text.configure(state=tk.DISABLED)

        # ── Footer ──────────────────────────────────────────────────────────
        foot = tk.Frame(self.root, bg=BG)
        foot.pack(fill=tk.X, padx=16, pady=(0, 8))
        tk.Label(foot, text="beaver", font=self.f_sig,
                 bg=BG, fg=FG_DIM).pack(side=tk.RIGHT)

    # ── card helper ──────────────────────────────────────────────────────────
    def _card(self, parent, title, value, row, col):
        f = tk.Frame(parent, bg=BG_CARD, bd=1, relief=tk.GROOVE,
                     highlightbackground="#2a2a4a", highlightthickness=1)
        f.grid(row=row, column=col, sticky="nsew", padx=4, pady=2)
        tk.Label(f, text=title, font=self.f_body, bg=BG_CARD, fg=FG_DIM).pack(pady=(8, 0))
        v = tk.Label(f, text=value, font=self.f_big, bg=BG_CARD, fg=FG)
        v.pack(pady=(0, 8))
        return v

    # ─────────────────────────────────────────────────────────────────────────
    #  Demo / Real toggle
    # ─────────────────────────────────────────────────────────────────────────
    def _toggle_demo(self):
        """Switch between Demo and Real mode. Saves to config on disk."""
        if self.running:
            messagebox.showwarning("Bot Running",
                "Stop the bot before switching trading mode.")
            return
        cfg = load_config()
        new_demo = not cfg.get('demo', False)
        cfg['demo'] = new_demo
        save_config(cfg)

        if new_demo:
            self.btn_mode.config(text="🎭  DEMO", bg=BTN_DEMO_BG,
                                 activebackground="#e65100")
            self.card_mode.config(text="DEMO", fg=ORANGE)
            self._log("Switched to DEMO mode")
        else:
            self.btn_mode.config(text="💹  REAL", bg=BTN_REAL_BG,
                                 activebackground="#00838f")
            self.card_mode.config(text="REAL", fg=GREEN)
            self._log("Switched to REAL mode")

    # ─────────────────────────────────────────────────────────────────────────
    #  Pair filter toggle
    # ─────────────────────────────────────────────────────────────────────────
    def _toggle_pair_filter(self):
        """Cycle: All Pairs → each individual pair → All Pairs …"""
        cfg = load_config()
        all_p = cfg.get('trading_pairs', [])
        if not all_p:
            return
        self._all_pairs = all_p

        if self.pair_filter is None:
            # switch to first pair
            self.pair_filter = all_p[0]
        else:
            idx = all_p.index(self.pair_filter) if self.pair_filter in all_p else -1
            if idx < len(all_p) - 1:
                self.pair_filter = all_p[idx + 1]
            else:
                self.pair_filter = None

        if self.pair_filter is None:
            self.btn_pair.config(text="⊞  All Pairs")
            self._log(f"Switched to ALL trading pairs")
        else:
            self.btn_pair.config(text=f"⊞  {self.pair_filter}")
            self._log(f"Switched to {self.pair_filter} only")

        # Apply to running bot instance
        bot = _find_bot_instance()
        if bot:
            if self.pair_filter is None:
                bot.pairs = list(self._all_pairs)
            else:
                bot.pairs = [self.pair_filter]

    # ─────────────────────────────────────────────────────────────────────────
    #  Bot control
    # ─────────────────────────────────────────────────────────────────────────
    def _start_bot(self):
        global bot_thread, bot_start_time, last_cycle_time
        if self.running:
            return
        cfg = load_config()
        if not cfg or cfg.get('api_key', '') in ('', 'YOUR_API_KEY'):
            messagebox.showerror("Config Error",
                "Edit Settings with valid API keys first.")
            return

        self._all_pairs = cfg.get('trading_pairs', [])
        self.pair_filter = None
        self.btn_pair.config(text="⊞  All Pairs")

        self.running = True
        bot_mobile_lite.stop_flag = False
        bot_start_time = time.time()
        last_cycle_time = time.time()

        self.lbl_status.config(text="●  RUNNING", fg=GREEN)
        self.btn_start.config(state=tk.DISABLED)
        self.btn_stop.config(state=tk.NORMAL)
        self._log("Bot starting…")

        bot_thread = threading.Thread(target=self._bot_worker, daemon=True)
        bot_thread.start()

    def _bot_worker(self):
        global last_cycle_time
        try:
            # We hook into the run-loop by monkey-patching the cycle marker
            _orig_check = bot_mobile_lite.LiteMobileBot.check_signals
            def _wrapped_check(bot_self):
                global last_cycle_time
                last_cycle_time = time.time()
                return _orig_check(bot_self)
            bot_mobile_lite.LiteMobileBot.check_signals = _wrapped_check
            bot_mobile_lite.main()
        except Exception as e:
            log_queue.put(f"Bot error: {e}")
        finally:
            self.root.after(0, self._on_bot_stopped)

    def _on_bot_stopped(self):
        global bot_start_time, last_cycle_time
        self.running = False
        bot_start_time = None
        last_cycle_time = None
        self.lbl_status.config(text="●  STOPPED", fg=RED)
        self.lbl_uptime.config(text="")
        self.btn_start.config(state=tk.NORMAL)
        self.btn_stop.config(state=tk.DISABLED)
        self.card_interval.config(text="--:--")
        self._log("Bot stopped.")

    def _stop_bot(self):
        if not self.running:
            return
        self._log("Stopping bot immediately…")
        # Set global stop flag
        bot_mobile_lite.stop_flag = True
        # Also force the instance's running flag to False
        bot = _find_bot_instance()
        if bot:
            bot.running = False
        self.lbl_status.config(text="●  STOPPING…", fg=ORANGE)
        self.btn_stop.config(state=tk.DISABLED)        # Watchdog: if bot hasn't stopped within 5s, force cleanup
        self.root.after(5000, self._force_stop_check)

    def _force_stop_check(self):
        """If the bot thread is still alive after timeout, force UI reset."""
        global bot_thread
        if bot_thread and bot_thread.is_alive():
            self._log("Force-stopping bot (thread still alive)…")
            # Re-set flags to be sure
            bot_mobile_lite.stop_flag = True
            bot = _find_bot_instance()
            if bot:
                bot.running = False
            # Give it one more second, then reset UI regardless
            self.root.after(1000, self._on_bot_stopped)
        # If thread already finished, _on_bot_stopped was called from _bot_worker

    def _open_settings(self):
        p = _config_path()
        if os.path.exists(p):
            subprocess.Popen(['notepad.exe', p])
        else:
            messagebox.showerror("Error", "mobile_config.json not found")

    # ─────────────────────────────────────────────────────────────────────────
    #  Periodic tickers
    # ─────────────────────────────────────────────────────────────────────────
    def _poll_logs(self):
        try:
            while True:
                self._log(log_queue.get_nowait())
        except queue.Empty:
            pass
        self.root.after(200, self._poll_logs)

    def _log(self, msg):
        self.log_text.configure(state=tk.NORMAL)
        self.log_text.insert(tk.END, msg + "\n")
        self.log_text.see(tk.END)
        lines = int(self.log_text.index('end-1c').split('.')[0])
        if lines > 2000:
            self.log_text.delete('1.0', f'{lines - 2000}.0')
        self.log_text.configure(state=tk.DISABLED)

    def _tick_uptime(self):
        if self.running and bot_start_time:
            self.lbl_uptime.config(text=f"Uptime  {fmt_uptime(time.time() - bot_start_time)}")
        self.root.after(1000, self._tick_uptime)

    def _tick_interval(self):
        if self.running and last_cycle_time:
            cfg = load_config()
            interval = cfg.get('check_interval', 15)
            elapsed = time.time() - last_cycle_time
            rem = max(0, interval - elapsed)
            m, s = divmod(int(rem), 60)
            self.card_interval.config(text=f"{m:02d}:{s:02d}")
        self.root.after(1000, self._tick_interval)

    def _tick_config(self):
        """Re-read config every 2s and update config-dependent HUD cards."""
        try:
            cfg = load_config()
            mx = cfg.get('max_open_trades', 3)
            # Only update the denominator; the count is updated from _update_pos
            cur_text = self.card_poscount.cget('text')
            if '/' in cur_text:
                cur_count = cur_text.split('/')[0].strip()
            else:
                cur_count = '0'
            self.card_poscount.config(text=f"{cur_count} / {mx}")

            # Keep mode card + button in sync with config file
            is_demo = cfg.get('demo', False)
            self.card_mode.config(text="DEMO" if is_demo else "REAL",
                                  fg=ORANGE if is_demo else GREEN)
            if is_demo:
                self.btn_mode.config(text="🎭  DEMO", bg=BTN_DEMO_BG,
                                     activebackground="#e65100")
            else:
                self.btn_mode.config(text="💹  REAL", bg=BTN_REAL_BG,
                                     activebackground="#00838f")
        except Exception:
            pass
        self.root.after(2000, self._tick_config)

    def _refresh_php_rate_loop(self):
        """Refresh PHP exchange rate every 5 minutes."""
        if time.time() - _php_last_fetch > 300:
            threading.Thread(target=_refresh_php_rate, daemon=True).start()
        self.root.after(300_000, self._refresh_php_rate_loop)

    def _refresh_data_loop(self):
        if self.running:
            threading.Thread(target=self._fetch_data, daemon=True).start()
        self.root.after(8000, self._refresh_data_loop)

    def _fetch_data(self):
        try:
            bot = _find_bot_instance()
            if bot is None:
                return

            wallet = bot.wallet
            self.root.after(0, lambda w=wallet:
                self.card_wallet.config(text=_php(w),
                                        fg=GREEN if w > 0 else FG))

            longs, shorts = [], []
            total_pnl = 0.0
            for sym in bot.pairs:
                try:
                    pos = bot.get_position(sym)
                    if pos['size'] > 0:
                        total_pnl += pos['pnl']
                        line = f"  {sym}  PnL {_php(pos['pnl'])}  @{pos['entry']:.4f}"
                        if pos['side'] == 'Buy':
                            longs.append(line)
                        elif pos['side'] == 'Sell':
                            shorts.append(line)
                except Exception:
                    pass

            self.root.after(0, lambda l=longs, s=shorts, p=total_pnl: self._update_pos(l, s, p))
        except Exception:
            pass

    def _update_pos(self, longs, shorts, total_pnl=0.0):
        cnt = len(longs) + len(shorts)
        mx = load_config().get('max_open_trades', 3)
        self.card_poscount.config(text=f"{cnt} / {mx}")

        # Update PnL card
        pnl_color = GREEN if total_pnl >= 0 else RED
        self.card_pnl.config(text=_php(total_pnl), fg=pnl_color)

        self.lst_long.delete(0, tk.END)
        for x in (longs or ["  No open long positions"]):
            self.lst_long.insert(tk.END, x)

        self.lst_short.delete(0, tk.END)
        for x in (shorts or ["  No open short positions"]):
            self.lst_short.insert(tk.END, x)

    # ─────────────────────────────────────────────────────────────────────────
    #  Close
    # ─────────────────────────────────────────────────────────────────────────
    def _on_close(self):
        if self.running:
            if messagebox.askyesno("Confirm", "Bot is running. Stop and exit?"):
                bot_mobile_lite.stop_flag = True
                bot = _find_bot_instance()
                if bot:
                    bot.running = False
                self.root.after(600, self.root.destroy)
            else:
                return
        else:
            self.root.destroy()


# ═══════════════════════════════════════════════════════════════════════════════
#  Bootstrap
# ═══════════════════════════════════════════════════════════════════════════════
def _ensure_config():
    p = _config_path()
    if not os.path.exists(p):
        cfg = {
            "api_key": "YOUR_API_KEY",
            "api_secret": "YOUR_API_SECRET",
            "testnet": True,
            "demo": False,
            "demo_balance": 85.0,
            "position_mode": "one-way",
            "trading_pairs": ["BTCUSDT","ETHUSDT","SOLUSDT","XRPUSDT",
                              "DOGEUSDT","ZECUSDT","FARTCOINUSDT"],
            "max_open_trades": 3,
            "leverage": {"BTCUSDT":35,"ETHUSDT":35,"SOLUSDT":35,
                         "XRPUSDT":35,"DOGEUSDT":35,"ZECUSDT":20,
                         "FARTCOINUSDT":35},
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
        with open(p, 'w') as f:
            json.dump(cfg, f, indent=4)

_ensure_config()

if __name__ == "__main__":
    root = tk.Tk()
    app = TradingWobotApp(root)
    root.mainloop()