# Trading Wobot 2.0 — Release Notes

**Release Date:** February 8, 2026  
**Build:** Windows x64 Installer (`TradingWobotSetup.exe`)  
**Author:** beaver

---

## What's New in 2.0

This release is a complete overhaul of the desktop application, transforming it from a basic log viewer into a full-featured trading HUD with a proper Windows installer.

---

### New GUI (launcher.py — Full Rewrite)

The launcher has been completely rewritten with a dark-themed dashboard:

- **App renamed** to **Trading Wobot** (window title, installer, Start Menu, desktop shortcut)
- **Custom app icon** generated from the robot logo (`D:\Documents\logo\`)
- **Status indicator** — clearly shows `STOPPED`, `RUNNING`, or `STOPPING` with color coding (red / green / orange)
- **Uptime counter** — displays how long the bot has been running (`HH:MM:SS`)
- **Wallet Balance card** — shows current USDT balance, updated every 8 seconds
- **Unrealised PnL card** — shows total unrealised profit/loss across all open positions (green when positive, red when negative)
- **Next Check In card** — countdown timer showing seconds until the next signal check cycle
- **Open Positions card** — shows count vs. max (e.g., `2 / 3`)
- **LONG Positions panel** — lists all open long positions with symbol, PnL, and entry price
- **SHORT Positions panel** — lists all open short positions with symbol, PnL, and entry price
- **"beaver" signature** in the lower-right corner of the app

### Control Buttons

| Button | Description |
|---|---|
| **▶ Start Bot** | Starts the trading bot. Validates config before launching. |
| **■ Stop Bot** | Stops the bot **immediately** — sets `stop_flag=True` and forces `bot.running=False` so there's no waiting for the sleep interval to finish. |
| **⚙ Settings** | Opens `mobile_config.json` in **Notepad** (always Notepad, not the system default JSON handler). |
| **⊞ All Pairs / [PAIR]** | Pair filter toggle — cycles through: All Pairs → BTCUSDT → ETHUSDT → ... → back to All Pairs. Applies immediately to the running bot without restart. |

### Proxy / VPN Removal

All proxy and VPN-related code has been **completely removed** from:

- `mobile_config.json` — `"proxy"` field deleted
- `bot_mobile_lite.py` — removed proxy parameter from client initialization; deleted the HTTP Injector VPN launch block
- `bybit_client_lite.py` — removed `proxy` parameter, `self.proxy` attribute, and `session.proxies` setup
- `launcher.py` — removed proxy from default config template

The bot now connects directly to Bybit's API without any proxy layer.

---

### Build System (Recreated)

All build scripts were rewritten from scratch:

#### `build.ps1`
- 6-step pipeline: Clean → Venv check → Install deps → Generate icon.ico → PyInstaller build → Copy data files
- Builds as `--onedir --windowed` with `--name TradingWobot` and `--icon icon.ico`
- Bundles `bot_mobile_lite.py`, `bybit_client_lite.py`, `twin_range_filter_lite.py`, and `mobile_config.json` via `--add-data`
- Auto-converts the PNG logo to multi-size ICO (16px–256px) using Pillow

#### `build.bat`
- Simple wrapper that calls `build.ps1` via PowerShell with `ExecutionPolicy Bypass`

#### `installer.iss` (Inno Setup 6)
- App name: **Trading Wobot 2.0**
- Shows as **"Trading Wobot 2.0"** in Windows Control Panel → Apps & Features (`AppName`, `AppVerName`, `UninstallDisplayName`)
- Publisher: **beaver**
- Custom setup icon and uninstall icon
- Desktop shortcut created by default
- Start Menu group with app shortcut, Settings shortcut (opens config in Notepad), and Uninstall
- `PrivilegesRequired=lowest` — no admin rights needed to install
- LZMA2 ultra compression (installer is ~13 MB)
- Launches the app after install

#### `requirements.txt`
- Cleaned up: removed unused `flask` and `flask-cors` dependencies
- Now only requires `requests` and `Pillow`

---

### Files Changed

| File | Change |
|---|---|
| `launcher.py` | Complete rewrite — new HUD with cards, position panels, pair filter, immediate stop |
| `bot_mobile_lite.py` | Removed proxy param from client init, removed VPN launch block |
| `bybit_client_lite.py` | Removed proxy parameter and session proxy setup |
| `mobile_config.json` | Removed `"proxy"` field |
| `build.ps1` | Rewritten — full build pipeline with icon generation |
| `build.bat` | Rewritten — calls build.ps1 |
| `installer.iss` | Rewritten — Trading Wobot 2.0 branding, proper installer config |
| `requirements.txt` | Cleaned up deps |
| `icon.ico` | New — generated from robot logo PNG |

---

### How to Build from Source

1. Open PowerShell in the project directory
2. Run `.\build.ps1` (or double-click `build.bat`)
3. The exe will be at `dist\TradingWobot\TradingWobot.exe`

### How to Create the Installer

1. Install [Inno Setup 6](https://jrsoftware.org/isinfo.php)
2. Open `installer.iss` with Inno Setup Compiler
3. Click **Build → Compile**
4. Installer will be at `installer\TradingWobotSetup.exe`

### How to Install

1. Run `TradingWobotSetup.exe`
2. Follow the wizard (no admin rights required)
3. Launch from desktop shortcut or Start Menu
4. Click **Settings** to configure your API keys
5. Click **Start Bot** to begin trading
