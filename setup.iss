[Setup]
AppName=my-dlp
AppVersion=1.3.1
AppPublisher=0xjoyo
AppPublisherURL=https://github.com/0xjoyo/my-dlp
DefaultDirName={pf}\my-dlp
DefaultGroupName=my-dlp
UninstallDisplayIcon={app}\my-dlp.exe
Compression=lzma2
SolidCompression=yes
OutputDir=dist
OutputBaseFilename=my-dlp_v1.3.1_installer
SetupIconFile=assets\icon.ico
DisableProgramGroupPage=yes

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: checkablealone

; Always-on shortcuts (no user choice needed): Start Menu entry + Desktop icon
; are both created for every install. Users can remove the desktop icon
; afterwards if they don't want it.

[Files]
Source: "dist\my-dlp\my-dlp.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "dist\my-dlp\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
; NOTE: Don't use "Flags: ignoreversion" on any shared system files

[Icons]
Name: "{group}\my-dlp"; Filename: "{app}\my-dlp.exe"
Name: "{group}\{cm:UninstallProgram,my-dlp}"; Filename: "{uninstallexe}"
; Desktop shortcut — created unconditionally for every install.
; No IconFilename — Windows picks up the icon embedded in the EXE
; by PyInstaller's --icon flag.
Name: "{commondesktop}\my-dlp"; Filename: "{app}\my-dlp.exe"

[Run]
Filename: "{app}\my-dlp.exe"; Description: "{cm:LaunchProgram,my-dlp}"; Flags: nowait postinstall skipifsilent
