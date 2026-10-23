; Per-user Orbe installer with the compact installation confirmation.
#define AppVersion GetEnv("ORBE_VERSION")
#if AppVersion == ""
  #define AppVersion "2.0.0"
#endif

[Setup]
AppId={{F20B9816-69F4-4828-92D8-BA5442871084}
AppName=Orbe
AppVersion={#AppVersion}
AppPublisher=Nexo Atelier
DefaultDirName={localappdata}\Programs\Orbe
DefaultGroupName=Orbe
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
OutputDir=..\dist
OutputBaseFilename=Orbe-Setup
SetupIconFile=..\orbe\assets\orbe.ico
UninstallDisplayIcon={app}\Orbe.exe
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
CloseApplications=yes
RestartApplications=no

[Languages]
Name: "brazilianportuguese"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"

[Tasks]
Name: "autostart"; Description: "Iniciar o Orbe ao entrar no Windows"; Flags: checkedonce
Name: "contextmenu"; Description: "Adicionar o Orbe ao menu de contexto dos arquivos"; Flags: checkedonce
Name: "desktopicon"; Description: "Criar um atalho na área de trabalho"; Flags: unchecked

[Files]
Source: "..\dist\Orbe\*"; DestDir: "{app}"; Flags: recursesubdirs ignoreversion

[Icons]
Name: "{autoprograms}\Orbe"; Filename: "{app}\Orbe.exe"
Name: "{autodesktop}\Orbe"; Filename: "{app}\Orbe.exe"; Tasks: desktopicon
Name: "{usersendto}\Orbe"; Filename: "{app}\Orbe.exe"

[Registry]
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; ValueType: string; ValueName: "Orbe"; ValueData: """{app}\Orbe.exe"" --quiet"; Tasks: autostart; Flags: uninsdeletevalue
Root: HKCU; Subkey: "Software\Classes\*\shell\Orbe"; ValueType: string; ValueName: "MUIVerb"; ValueData: "Orbe…"; Tasks: contextmenu; Flags: uninsdeletekey
Root: HKCU; Subkey: "Software\Classes\*\shell\Orbe"; ValueType: string; ValueName: "Icon"; ValueData: "{app}\Orbe.exe"; Tasks: contextmenu
Root: HKCU; Subkey: "Software\Classes\*\shell\Orbe"; ValueType: string; ValueName: "MultiSelectModel"; ValueData: "Player"; Tasks: contextmenu
Root: HKCU; Subkey: "Software\Classes\*\shell\Orbe\command"; ValueType: string; ValueName: ""; ValueData: """{app}\Orbe.exe"" ""%1"""; Tasks: contextmenu

[Run]
Filename: "{app}\Orbe.exe"; Parameters: "--installed"; Flags: nowait skipifsilent

[UninstallRun]
Filename: "{cmd}"; Parameters: "/C taskkill /F /IM Orbe.exe"; Flags: runhidden; RunOnceId: "KillOrbe"
