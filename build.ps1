# ───────────────────────────────────────────────────────────────
#  Trading Wobot – Build Script (PowerShell)
#  Run from the project root:  .\build.ps1
# ───────────────────────────────────────────────────────────────

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Trading Wobot – Build"                -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# ── 1. Clean ────────────────────────────────────────────────────
Write-Host "`n[1/6] Cleaning previous build..."
foreach ($d in @("dist","build")) {
    if (Test-Path $d) { Remove-Item -Recurse -Force $d }
}
if (Test-Path "launcher.spec") { Remove-Item "launcher.spec" }

# ── 2. Venv ─────────────────────────────────────────────────────
$venvPython = ".\.venv\Scripts\python.exe"
if (!(Test-Path $venvPython)) {
    Write-Host "[2/6] Creating virtual environment..."
    python -m venv .venv
} else {
    Write-Host "[2/6] Virtual environment found."
}

# ── 3. Deps ─────────────────────────────────────────────────────
Write-Host "[3/6] Installing dependencies..."
& $venvPython -m pip install --quiet --upgrade pip
& $venvPython -m pip install --quiet -r requirements.txt
& $venvPython -m pip install --quiet pyinstaller Pillow
if ($LASTEXITCODE -ne 0) {
    Write-Host "Failed to install dependencies" -ForegroundColor Red
    Read-Host "Press Enter to exit"; exit 1
}

# ── 4. Ensure icon.ico ──────────────────────────────────────────
Write-Host "[4/6] Preparing icon..."
$logoPng = "D:\Documents\logo\cute-robot-logo-2c42937a-c1fe-493a-b639-d22a0b5f4671.png"
if (!(Test-Path "icon.ico") -and (Test-Path $logoPng)) {
    $pyCode = "from PIL import Image; img = Image.open(r'$logoPng').resize((256,256), Image.LANCZOS); img.save('icon.ico', format='ICO', sizes=[(256,256),(128,128),(64,64),(48,48),(32,32),(16,16)]); print('icon.ico created')"
    & $venvPython -c $pyCode
} elseif (Test-Path "icon.ico") {
    Write-Host "icon.ico already exists."
} else {
    Write-Host "WARNING: Logo PNG not found – building without icon." -ForegroundColor Yellow
}

# ── 5. PyInstaller ──────────────────────────────────────────────
Write-Host "[5/6] Running PyInstaller..."
$pyiArgs = @(
    "-m", "PyInstaller",
    "--onedir",
    "--windowed",
    "--name", "TradingWobot",
    "--add-data", "bot_mobile_lite.py;.",
    "--add-data", "bybit_client_lite.py;.",
    "--add-data", "twin_range_filter_lite.py;.",
    "--add-data", "mobile_config.json;.",
    "-y"
)
if (Test-Path "icon.ico") {
    $pyiArgs += @("--icon", "icon.ico")
}
$pyiArgs += "launcher.py"

& $venvPython @pyiArgs
if ($LASTEXITCODE -ne 0) {
    Write-Host "PyInstaller failed (exit $LASTEXITCODE)" -ForegroundColor Red
    Read-Host "Press Enter to exit"; exit 1
}

# ── 6. Copy extra files ────────────────────────────────────────
Write-Host "[6/6] Copying data files..."
$dest = "dist\TradingWobot"
foreach ($f in @("mobile_config.json","bot_mobile_lite.py",
                 "bybit_client_lite.py","twin_range_filter_lite.py",
                 "icon.ico")) {
    if (Test-Path $f) { Copy-Item $f $dest -Force }
}
if (Test-Path "bot_state.json") { Copy-Item "bot_state.json" $dest -Force }

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  BUILD COMPLETE"                        -ForegroundColor Green
Write-Host "  Output: dist\TradingWobot\TradingWobot.exe" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "To create the installer:"
Write-Host "  1. Install Inno Setup from https://jrsoftware.org/isinfo.php"
Write-Host "  2. Open installer.iss with Inno Setup Compiler"
Write-Host "  3. Click Build > Compile"
Write-Host ""
Read-Host "Press Enter to continue"