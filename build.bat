@echo off
cd /d "%~dp0"
echo Installing pyinstaller in venv...
.venv\Scripts\python.exe -m pip install pyinstaller
echo Running pyinstaller...
.venv\Scripts\pyinstaller.exe --onedir launcher.py
echo Copying data files...
copy mobile_config.json dist\launcher\
copy bot_mobile_lite.py dist\launcher\
copy bybit_client_lite.py dist\launcher\
copy twin_range_filter_lite.py dist\launcher\
copy bot_state.json dist\launcher\
copy requirements.txt dist\launcher\
copy v2ray_singapore_config.json dist\launcher\
echo Build complete. Run dist\launcher\launcher.exe
echo Note: Download v2ray.exe from https://github.com/v2fly/v2ray-core/releases and place in dist\launcher\ for VPN functionality.
pause