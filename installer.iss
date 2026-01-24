[Setup]
AppName=Twin Range Filter Trading Bot
AppVersion=1.0
DefaultDirName={pf}\Twin Range Filter Bot
DefaultGroupName=Twin Range Filter Bot
OutputDir=installer
OutputBaseFilename=TwinRangeFilterBotInstaller
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
Name: "{group}\Twin Range Filter Trading Bot"; Filename: "{app}\launcher.exe"; IconFilename: "{app}\launcher.exe"
Name: "{commondesktop}\Twin Range Filter Trading Bot"; Filename: "{app}\launcher.exe"; IconFilename: "{app}\launcher.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\launcher.exe"; Description: "Launch Twin Range Filter Trading Bot"; Flags: nowait postinstall skipifsilent