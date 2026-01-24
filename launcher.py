import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
import subprocess
import os
import json
import threading
import queue
import logging

import bot_mobile_lite

bot_process = None
log_queue = queue.Queue()
log_text = None

class QueueHandler(logging.Handler):
    def __init__(self, queue):
        super().__init__()
        self.queue = queue

    def emit(self, record):
        self.queue.put(self.format(record))

queue_handler = QueueHandler(log_queue)
queue_handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
logging.getLogger().addHandler(queue_handler)
logging.getLogger().setLevel(logging.INFO)

def append_log(message):
    if log_text:
        log_text.insert(tk.END, message + '\n')
        log_text.see(tk.END)

def process_log_queue():
    try:
        while True:
            message = log_queue.get_nowait()
            append_log(message)
    except queue.Empty:
        pass
    root.after(100, process_log_queue)

def edit_config():
    config_file = 'mobile_config.json'
    if os.path.exists(config_file):
        subprocess.run(['notepad', config_file])
    else:
        messagebox.showerror("Error", "mobile_config.json not found")

def run_bot():
    global bot_process
    try:
        bot_mobile_lite.stop_flag = False
        bot_process = threading.Thread(target=bot_mobile_lite.main, daemon=True)
        bot_process.start()
        append_log("Bot started.")
    except Exception as e:
        append_log(f"Failed to start bot: {e}")

def stop_bot():
    global bot_process
    if bot_process and bot_process.is_alive():
        bot_mobile_lite.stop_flag = True
        bot_process.join(timeout=5)
        bot_process = None
        append_log("Bot stopped.")

def create_config_if_not_exists():
    config_file = 'mobile_config.json'
    if not os.path.exists(config_file):
        default_config = {
            "api_key": "YOUR_API_KEY",
            "api_secret": "YOUR_API_SECRET",
            "testnet": True,
            "demo": False,
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
            json.dump(default_config, f, indent=4)

# Create config if not exists
create_config_if_not_exists()

root = tk.Tk()
root.title("Bybit Trading Bot")
root.geometry("600x400")

# Top frame for buttons
button_frame = tk.Frame(root)
button_frame.pack(pady=10)

tk.Label(button_frame, text="Xan's Trading Bot utilizing Twin Range Filter Strategy").grid(row=0, column=0, columnspan=3, pady=5)

tk.Button(button_frame, text="Edit mobile_config.json", command=edit_config).grid(row=1, column=0, padx=5)
tk.Button(button_frame, text="Run Bot", command=run_bot).grid(row=1, column=1, padx=5)
tk.Button(button_frame, text="Stop Bot", command=stop_bot).grid(row=1, column=2, padx=5)

# Log frame
log_frame = tk.Frame(root)
log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

tk.Label(log_frame, text="Bot Logs:").pack(anchor=tk.W)
log_text = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD, height=15)
log_text.pack(fill=tk.BOTH, expand=True)

# Start processing log queue
process_log_queue()

root.mainloop()