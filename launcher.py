import tkinter as tk
from tkinter import filedialog, messagebox
import subprocess
import os
import json

bot_process = None
vpn_process = None

def edit_config():
    config_file = 'mobile_config.json'
    if os.path.exists(config_file):
        subprocess.run(['notepad', config_file])
    else:
        messagebox.showerror("Error", "mobile_config.json not found")

def enter_vpn_config():
    # Info for VPN setup
    messagebox.showinfo("HTTP Injector / V2ray Config", 
                        "For integrated VPN:\n"
                        "1. Download v2ray.exe from https://github.com/v2fly/v2ray-core/releases\n"
                        "2. Place v2ray.exe in this folder\n"
                        "3. Edit v2ray_singapore_config.json with a real Singapore server\n"
                        "4. The bot will start V2ray automatically\n"
                        "Alternatively, configure HTTP Injector on Android as per ANDROID_SETUP.md")

def run_bot():
    global bot_process, vpn_process
    try:
        # Start V2ray VPN
        if os.path.exists('v2ray.exe'):
            vpn_process = subprocess.Popen(['v2ray.exe', '-config', 'v2ray_singapore_config.json'])
            messagebox.showinfo("VPN", "V2ray VPN started with Singapore config.")
        else:
            messagebox.showwarning("VPN", "v2ray.exe not found. Download V2ray for Windows and place in this folder.")
        
        # Run the bot
        bot_process = subprocess.Popen(['python', 'bot_mobile_lite.py'])
        messagebox.showinfo("Bot", "Bot started in background.")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to start: {e}")

def stop_bot():
    global bot_process, vpn_process
    if bot_process:
        bot_process.terminate()
        bot_process = None
        messagebox.showinfo("Bot", "Bot stopped.")
    if vpn_process:
        vpn_process.terminate()
        vpn_process = None
        messagebox.showinfo("VPN", "VPN stopped.")

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
root.title("Trading Bot Launcher")
root.geometry("300x200")

tk.Label(root, text="Twin Range Filter Trading Bot").pack(pady=10)

tk.Button(root, text="Edit mobile_config.json", command=edit_config).pack(pady=5)
tk.Button(root, text="VPN Config Info", command=enter_vpn_config).pack(pady=5)
tk.Button(root, text="Run Bot", command=run_bot).pack(pady=5)
tk.Button(root, text="Stop Bot", command=stop_bot).pack(pady=5)

root.mainloop()