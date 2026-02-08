@echo off
title Trading Wobot - Build
echo ========================================
echo   Trading Wobot - Build
echo ========================================
echo.

REM ── Run the PowerShell build script ──
powershell -ExecutionPolicy Bypass -File "%~dp0build.ps1"
if errorlevel 1 (
    echo.
    echo Build failed. See errors above.
    pause
    exit /b 1
)

echo.
echo ========================================
echo   BUILD COMPLETE
echo   Output: dist\TradingWobot\TradingWobot.exe
echo ========================================
echo.
echo To create the Windows installer:
echo   1. Install Inno Setup from https://jrsoftware.org/isinfo.php
echo   2. Open installer.iss with Inno Setup Compiler
echo   3. Click Build ^> Compile
echo   4. Installer: installer\TradingWobotSetup.exe
echo.
pause