[Setup]
AppName=Trading Bot
AppVersion=1.0
DefaultDirName={pf}\Trading Bot
DefaultGroupName=Trading Bot
OutputDir=installer
OutputBaseFilename=TradingBotInstaller
Compression=lzma
SolidCompression=yes
PrivilegesRequired=admin

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional icons:"; Flags: unchecked

[Files]
Source: "dist\launcher\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs

[Icons]
Name: "{group}\Trading Bot"; Filename: "{app}\launcher.exe"; IconFilename: "{app}\launcher.exe"
Name: "{commondesktop}\Trading Bot"; Filename: "{app}\launcher.exe"; IconFilename: "{app}\launcher.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\launcher.exe"; Description: "Launch Trading Bot"; Flags: nowait postinstall skipifsilent