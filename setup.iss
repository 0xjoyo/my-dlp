[Setup]
AppName=my-dlp
AppVersion=1.0.0
AppPublisher=0xjoyo
AppPublisherURL=https://github.com/0xjoyo/my-dlp
DefaultDirName={pf}\my-dlp
DefaultGroupName=my-dlp
UninstallDisplayIcon={app}\my-dlp.exe
Compression=lzma2
SolidCompression=yes
OutputDir=dist
OutputBaseFilename=my-dlp_installer
SetupIconFile=assets\icon.ico
DisableProgramGroupPage=yes

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "dist\my-dlp\my-dlp.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "dist\my-dlp\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
; NOTE: Don't use "Flags: ignoreversion" on any shared system files

[Icons]
Name: "{group}\my-dlp"; Filename: "{app}\my-dlp.exe"
Name: "{group}\{cm:UninstallProgram,my-dlp}"; Filename: "{uninstallexe}"
Name: "{commondesktop}\my-dlp"; Filename: "{app}\my-dlp.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\my-dlp.exe"; Description: "{cm:LaunchProgram,my-dlp}"; Flags: nowait postinstall skipifsilent
