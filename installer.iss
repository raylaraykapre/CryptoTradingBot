; ───────────────────────────────────────────────────────────────
;  Trading Wobot – Inno Setup Installer Script
;  Build with Inno Setup 6+  (https://jrsoftware.org/isinfo.php)
; ───────────────────────────────────────────────────────────────

[Setup]
AppName=Trading Wobot 2.0
AppVersion=2.0
AppVerName=Trading Wobot 2.0
AppPublisher=beaver
DefaultDirName={autopf}\Trading Wobot
DefaultGroupName=Trading Wobot
OutputDir=installer
OutputBaseFilename=TradingWobotSetup
SetupIconFile=icon.ico
UninstallDisplayName=Trading Wobot 2.0
UninstallDisplayIcon={app}\TradingWobot.exe
Compression=lzma2/ultra64
SolidCompression=yes
PrivilegesRequired=lowest
WizardStyle=modern
DisableProgramGroupPage=yes
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional icons:"

[Files]
; Everything PyInstaller produced
Source: "dist\TradingWobot\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
; Ensure editable config is present
Source: "mobile_config.json"; DestDir: "{app}"; Flags: onlyifdoesntexist
; Icon
Source: "icon.ico"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\Trading Wobot"; Filename: "{app}\TradingWobot.exe"; IconFilename: "{app}\icon.ico"
Name: "{group}\Settings (mobile_config.json)"; Filename: "notepad.exe"; Parameters: """{app}\mobile_config.json"""
Name: "{group}\Uninstall Trading Wobot"; Filename: "{uninstallexe}"
Name: "{commondesktop}\Trading Wobot"; Filename: "{app}\TradingWobot.exe"; IconFilename: "{app}\icon.ico"; Tasks: desktopicon

[Run]
Filename: "{app}\TradingWobot.exe"; Description: "Launch Trading Wobot"; Flags: nowait postinstall skipifsilent