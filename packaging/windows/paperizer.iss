; Script generated for Paperizer Windows Installer
#ifndef MyAppVersion
#define MyAppVersion "0.1.0"
#endif

#define MyAppName "Paperizer"
#define MyAppPublisher "Humanitas Labs & Kai"
#define MyAppURL "https://github.com/Refayatul/paperizer"
#define MyAppExeName "Paperizer.exe"

[Setup]
; AppId uniquely identifies this application in Windows. Do NOT change this in future versions.
AppId={{D37E6F89-A6D1-456B-B65A-B6D74B469901}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DisableProgramGroupPage=yes
OutputDir=..\..\dist
OutputBaseFilename=Paperizer-{#MyAppVersion}-Setup-x64
SetupIconFile=..\..\assets\icon.ico
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64
ChangesAssociations=yes

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "..\..\dist\Paperizer\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\assets\icon.ico"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\assets\icon.ico"; Tasks: desktopicon

[Registry]
; Register "Open with Paperizer" in the Windows Explorer context menu for PDF files
Root: HKA; Subkey: "Software\Classes\SystemFileAssociations\.pdf\shell\Paperizer"; ValueType: string; ValueName: ""; ValueData: "Open with Paperizer"; Flags: uninsdeletekey
Root: HKA; Subkey: "Software\Classes\SystemFileAssociations\.pdf\shell\Paperizer"; ValueType: string; ValueName: "Icon"; ValueData: """{app}\assets\icon.ico"""
Root: HKA; Subkey: "Software\Classes\SystemFileAssociations\.pdf\shell\Paperizer\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" ""%1"""

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent
