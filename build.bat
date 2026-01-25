@echo off
cd /d "%~dp0"
echo Installing pyinstaller in venv...
"%~dp0.venv\Scripts\python.exe" -m pip install pyinstaller
echo Running pyinstaller...
"%~dp0.venv\Scripts\python.exe" -m pyinstaller --onedir --windowed -y launcher.py
echo Copying data files...
copy mobile_config.json dist\launcher\
copy bot_mobile_lite.py dist\launcher\
copy bybit_client_lite.py dist\launcher\
copy twin_range_filter_lite.py dist\launcher\
copy bot_state.json dist\launcher\
copy requirements.txt dist\launcher\
echo Build complete. Run dist\launcher\launcher.exe
pause