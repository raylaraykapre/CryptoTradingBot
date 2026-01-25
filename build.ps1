Write-Host "Installing pyinstaller in venv..."
python -m pip install pyinstaller
Write-Host "Running pyinstaller..."
python -m pyinstaller --onedir --windowed -y launcher.py
Write-Host "Copying data files..."
Copy-Item mobile_config.json dist\launcher\
Copy-Item bot_mobile_lite.py dist\launcher\
Copy-Item bybit_client_lite.py dist\launcher\
Copy-Item twin_range_filter_lite.py dist\launcher\
Copy-Item bot_state.json dist\launcher\
Copy-Item requirements.txt dist\launcher\
Write-Host "Build complete. Run dist\launcher\launcher.exe"
Read-Host "Press Enter to continue"