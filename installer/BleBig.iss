#define MyAppName "BleBig"
#define MyAppVersion "0.3.0"
#define MyAppPublisher "Thien Ha"
#define MyAppExeName "BleBig.exe"

[Setup]
AppId={{B6B1A9D4-9E56-4F23-BB6E-77C2E7A92910}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={localappdata}\Programs\BleBig
UsePreviousAppDir=no
DefaultGroupName=BleBig
DisableProgramGroupPage=yes
DisableDirPage=yes
DisableReadyPage=yes
DisableFinishedPage=yes
OutputDir=..\release
OutputBaseFilename=BleBig-Setup
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
SetupIconFile=..\assets\blebig.ico
PrivilegesRequired=lowest
CloseApplications=yes
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
UninstallDisplayIcon={app}\BleBig.exe
SetupLogging=yes

[Files]
Source: "..\dist\BleBig\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs
Source: "..\dist\BleBigUpdater.exe"; DestDir: "{app}"

[Dirs]
Name: "{app}\Update"

[Icons]
Name: "{autoprograms}\BleBig"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\BleBig"; Filename: "{app}\{#MyAppExeName}"

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Mở BleBig"; Flags: nowait skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{app}"

[Code]
procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssInstall then
    WizardForm.Hide;
end;

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
var
  UserChoice: Integer;
begin
  if CurUninstallStep = usUninstall then
  begin
    UserChoice := MsgBox('Bạn có muốn xóa model AI, cấu hình và log của BleBig không?', mbConfirmation, MB_YESNO);
    if UserChoice = IDYES then
      DelTree(ExpandConstant('{localappdata}\BleBig'), True, True, True);
  end;
end;
