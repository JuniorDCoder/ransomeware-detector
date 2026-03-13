; ─────────────────────────────────────────────────────────────────────────────
;  RansomGuard — Inno Setup Installer Script
;  Produces: RansomGuard-Setup.exe  (~40-80 MB self-contained installer)
;
;  Requirements:
;    - Run windows/build.py first so that windows/dist/RansomGuardApp/ exists
;    - Download Inno Setup 6 from https://jrsoftware.org/isdl.php
;    - Then run: python windows/build.py   (it calls ISCC automatically)
;      Or manually: ISCC.exe windows\setup.iss
; ─────────────────────────────────────────────────────────────────────────────

#define MyAppName      "RansomGuard"
#define MyAppVersion   "1.0.0"
#define MyAppPublisher "RansomGuard Project"
#define MyAppURL       "https://github.com/JuniorDCoder/ransomeware-detector"
#define MyAppExeName   "RansomGuard.exe"
#define MySourceDir    "..\windows\dist\RansomGuardApp"

[Setup]
AppId={{D3F7A1B2-4C5E-4F6A-8B9C-0D1E2F3A4B5C}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
; Require admin rights so we can write to Program Files and install the service
PrivilegesRequired=admin
OutputDir=.
OutputBaseFilename=RansomGuard-Setup
SetupIconFile=
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
WizardResizable=yes
; Minimum Windows version: Windows 10
MinVersion=10.0

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon";     Description: "{cm:CreateDesktopIcon}";    GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "startupentry";    Description: "Start RansomGuard automatically when Windows starts"; GroupDescription: "Startup:"; Flags: unchecked

[Files]
; Main application folder (entire PyInstaller output)
Source: "{#MySourceDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

; Default config (only copy if config.json doesn't already exist)

[Dirs]
; Make sure the install dir is writable for data.db
Name: "{app}"; Permissions: users-modify

[Icons]
Name: "{group}\{#MyAppName}";          Filename: "{app}\{#MyAppExeName}"
Name: "{group}\Open Dashboard";        Filename: "{app}\{#MyAppExeName}"
Name: "{group}\Uninstall {#MyAppName}";Filename: "{uninstallexe}"
Name: "{commondesktop}\{#MyAppName}";  Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Registry]
; Startup entry (optional task)
Root: HKLM; Subkey: "SOFTWARE\Microsoft\Windows\CurrentVersion\Run"; \
  ValueType: string; ValueName: "RansomGuard"; \
  ValueData: """{app}\{#MyAppExeName}"""; \
  Flags: uninsdeletevalue; Tasks: startupentry

[Run]
; Copy default config if not already present
Filename: "{cmd}"; Parameters: "/c if not exist ""{app}\config.json"" copy ""{app}\config.example.json"" ""{app}\config.json"""; \
  Flags: runhidden

; Launch the app after install finishes
Filename: "{app}\{#MyAppExeName}"; \
  Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; \
  Flags: nowait postinstall skipifsilent

[UninstallRun]
; Kill running instances before uninstall
Filename: "{cmd}"; Parameters: "/c taskkill /IM {#MyAppExeName} /F"; Flags: runhidden

[Code]
// Prevent installing over an older version without uninstalling first
function InitializeSetup(): Boolean;
begin
  Result := True;
end;
