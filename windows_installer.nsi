; UsenetSync Windows Installer
; One-click installation for Windows users
; Includes all dependencies and automatic setup

!include "MUI2.nsh"
!include "x64.nsh"
!include "LogicLib.nsh"

; General Settings
Name "UsenetSync"
OutFile "UsenetSync-Setup.exe"
InstallDir "$PROGRAMFILES64\UsenetSync"
InstallDirRegKey HKLM "Software\UsenetSync" "InstallPath"
RequestExecutionLevel admin

; Version Information
VIProductVersion "1.0.0.0"
VIAddVersionKey "ProductName" "UsenetSync"
VIAddVersionKey "CompanyName" "UsenetSync Team"
VIAddVersionKey "LegalCopyright" "© 2024 UsenetSync"
VIAddVersionKey "FileDescription" "UsenetSync Installer"
VIAddVersionKey "FileVersion" "1.0.0"

; Interface Settings
!define MUI_ABORTWARNING
!define MUI_ICON "assets\icon.ico"
!define MUI_UNICON "assets\icon.ico"
!define MUI_WELCOMEFINISHPAGE_BITMAP "assets\installer_banner.bmp"
!define MUI_HEADERIMAGE
!define MUI_HEADERIMAGE_BITMAP "assets\header.bmp"
!define MUI_HEADERIMAGE_RIGHT

; Pages
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "LICENSE.txt"
!insertmacro MUI_PAGE_COMPONENTS
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES

; Custom page for configuration
Page custom ConfigPage ConfigPageLeave

!insertmacro MUI_PAGE_FINISH

; Uninstaller Pages
!insertmacro MUI_UNPAGE_WELCOME
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_UNPAGE_FINISH

; Languages
!insertmacro MUI_LANGUAGE "English"

; Variables
Var UsenetServer
Var UsenetPort
Var UsenetUsername
Var UsenetPassword
Var UseSSL

; Sections
Section "UsenetSync Core" SecCore
    SectionIn RO ; Required
    
    SetOutPath "$INSTDIR"
    
    ; Install main application
    File /r "dist\usenet-sync\*.*"
    
    ; Create required directories
    CreateDirectory "$INSTDIR\data"
    CreateDirectory "$INSTDIR\temp"
    CreateDirectory "$INSTDIR\logs"
    CreateDirectory "$INSTDIR\config"
    
    ; Install configuration template
    File "usenet_sync_config.template.json"
    
    ; Write registry keys
    WriteRegStr HKLM "Software\UsenetSync" "InstallPath" "$INSTDIR"
    WriteRegStr HKLM "Software\UsenetSync" "Version" "1.0.0"
    
    ; Create uninstaller
    WriteUninstaller "$INSTDIR\Uninstall.exe"
    
    ; Add to Windows Programs
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\UsenetSync" \
                     "DisplayName" "UsenetSync"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\UsenetSync" \
                     "UninstallString" "$INSTDIR\Uninstall.exe"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\UsenetSync" \
                     "DisplayIcon" "$INSTDIR\usenet-sync.exe"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\UsenetSync" \
                     "Publisher" "UsenetSync Team"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\UsenetSync" \
                     "DisplayVersion" "1.0.0"
    WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\UsenetSync" \
                      "EstimatedSize" 150000
    
SectionEnd

Section "PostgreSQL (Embedded)" SecPostgreSQL
    
    SetOutPath "$INSTDIR\postgresql"
    
    ; Download PostgreSQL if not included
    DetailPrint "Installing PostgreSQL..."
    
    ; Check if PostgreSQL binaries are bundled
    IfFileExists "$INSTDIR\postgresql\bin\postgres.exe" PostgreSQLExists
    
    ; Download PostgreSQL portable
    DetailPrint "Downloading PostgreSQL..."
    NSISdl::download "https://get.enterprisedb.com/postgresql/postgresql-15.4-1-windows-x64-binaries.zip" \
                     "$TEMP\postgresql.zip"
    Pop $0
    StrCmp $0 "success" +3
        MessageBox MB_OK "Download failed: $0"
        Abort
    
    ; Extract PostgreSQL
    DetailPrint "Extracting PostgreSQL..."
    nsUnzip::Extract "$TEMP\postgresql.zip" "$INSTDIR\postgresql" "<ALL>"
    Pop $0
    
    ; Delete temp file
    Delete "$TEMP\postgresql.zip"
    
    PostgreSQLExists:
    
    ; Initialize PostgreSQL database
    DetailPrint "Initializing PostgreSQL database..."
    
    ; Create data directory
    CreateDirectory "$INSTDIR\postgresql\data"
    
    ; Initialize database cluster
    ExecWait '"$INSTDIR\postgresql\bin\initdb.exe" -D "$INSTDIR\postgresql\data" -E UTF8 --locale=C -U postgres'
    
    ; Create PostgreSQL configuration
    FileOpen $0 "$INSTDIR\postgresql\data\postgresql.conf" a
    FileWrite $0 "$\r$\n# UsenetSync Optimizations$\r$\n"
    FileWrite $0 "shared_buffers = 256MB$\r$\n"
    FileWrite $0 "effective_cache_size = 1GB$\r$\n"
    FileWrite $0 "work_mem = 16MB$\r$\n"
    FileWrite $0 "max_connections = 100$\r$\n"
    FileWrite $0 "port = 5433$\r$\n" ; Use different port to avoid conflicts
    FileClose $0
    
    ; Register PostgreSQL as Windows service
    DetailPrint "Registering PostgreSQL service..."
    ExecWait '"$INSTDIR\postgresql\bin\pg_ctl.exe" register -N "UsenetSyncDB" -D "$INSTDIR\postgresql\data"'
    
    ; Start PostgreSQL service
    DetailPrint "Starting PostgreSQL service..."
    ExecWait 'net start UsenetSyncDB'
    
    ; Create UsenetSync database
    Sleep 2000 ; Wait for service to start
    ExecWait '"$INSTDIR\postgresql\bin\createdb.exe" -U postgres -p 5433 usenet_sync'
    
SectionEnd

Section "Python Runtime" SecPython
    
    SetOutPath "$INSTDIR\python"
    
    ; Check if Python is bundled
    IfFileExists "$INSTDIR\python\python.exe" PythonExists
    
    ; Download Python embeddable package
    DetailPrint "Downloading Python runtime..."
    NSISdl::download "https://www.python.org/ftp/python/3.11.7/python-3.11.7-embed-amd64.zip" \
                     "$TEMP\python.zip"
    Pop $0
    StrCmp $0 "success" +3
        MessageBox MB_OK "Python download failed: $0"
        Abort
    
    ; Extract Python
    DetailPrint "Extracting Python..."
    nsUnzip::Extract "$TEMP\python.zip" "$INSTDIR\python" "<ALL>"
    Pop $0
    
    ; Delete temp file
    Delete "$TEMP\python.zip"
    
    PythonExists:
    
    ; Install pip
    DetailPrint "Installing pip..."
    NSISdl::download "https://bootstrap.pypa.io/get-pip.py" "$TEMP\get-pip.py"
    ExecWait '"$INSTDIR\python\python.exe" "$TEMP\get-pip.py"'
    Delete "$TEMP\get-pip.py"
    
    ; Install required Python packages
    DetailPrint "Installing Python dependencies..."
    ExecWait '"$INSTDIR\python\python.exe" -m pip install --no-warn-script-location \
              click cryptography colorama psutil tabulate tqdm sqlalchemy \
              requests urllib3 prometheus-client python-dateutil PyYAML \
              python-dotenv watchdog pynntp psycopg2-binary'
    
SectionEnd

Section "Desktop Shortcuts" SecShortcuts
    
    ; Create Start Menu shortcuts
    CreateDirectory "$SMPROGRAMS\UsenetSync"
    CreateShortcut "$SMPROGRAMS\UsenetSync\UsenetSync.lnk" \
                   "$INSTDIR\usenet-sync.exe" "" \
                   "$INSTDIR\usenet-sync.exe" 0
    CreateShortcut "$SMPROGRAMS\UsenetSync\Configuration.lnk" \
                   "$INSTDIR\config\usenet_sync_config.json"
    CreateShortcut "$SMPROGRAMS\UsenetSync\Uninstall.lnk" \
                   "$INSTDIR\Uninstall.exe"
    
    ; Create Desktop shortcut
    CreateShortcut "$DESKTOP\UsenetSync.lnk" \
                   "$INSTDIR\usenet-sync.exe" "" \
                   "$INSTDIR\usenet-sync.exe" 0
    
SectionEnd

Section "Windows Firewall Rules" SecFirewall
    
    ; Add firewall exceptions
    DetailPrint "Adding Windows Firewall rules..."
    
    ; UsenetSync main application
    ExecWait 'netsh advfirewall firewall add rule name="UsenetSync" \
              dir=in action=allow program="$INSTDIR\usenet-sync.exe" enable=yes'
    ExecWait 'netsh advfirewall firewall add rule name="UsenetSync" \
              dir=out action=allow program="$INSTDIR\usenet-sync.exe" enable=yes'
    
    ; PostgreSQL
    ExecWait 'netsh advfirewall firewall add rule name="UsenetSync Database" \
              dir=in action=allow program="$INSTDIR\postgresql\bin\postgres.exe" enable=yes'
    
SectionEnd

; Section Descriptions
!insertmacro MUI_FUNCTION_DESCRIPTION_BEGIN
    !insertmacro MUI_DESCRIPTION_TEXT ${SecCore} "Core UsenetSync application (required)"
    !insertmacro MUI_DESCRIPTION_TEXT ${SecPostgreSQL} "Embedded PostgreSQL database for large datasets"
    !insertmacro MUI_DESCRIPTION_TEXT ${SecPython} "Python runtime and dependencies"
    !insertmacro MUI_DESCRIPTION_TEXT ${SecShortcuts} "Create desktop and Start Menu shortcuts"
    !insertmacro MUI_DESCRIPTION_TEXT ${SecFirewall} "Configure Windows Firewall for UsenetSync"
!insertmacro MUI_FUNCTION_DESCRIPTION_END

; Custom Configuration Page
Function ConfigPage
    nsDialogs::Create 1018
    Pop $0
    
    ${NSD_CreateLabel} 0 0 100% 20u "Configure your Usenet server settings:"
    
    ${NSD_CreateLabel} 0 30u 70u 12u "Server:"
    ${NSD_CreateText} 80u 28u 180u 12u "news.newshosting.com"
    Pop $UsenetServer
    
    ${NSD_CreateLabel} 0 50u 70u 12u "Port:"
    ${NSD_CreateText} 80u 48u 60u 12u "563"
    Pop $UsenetPort
    
    ${NSD_CreateLabel} 0 70u 70u 12u "Username:"
    ${NSD_CreateText} 80u 68u 180u 12u ""
    Pop $UsenetUsername
    
    ${NSD_CreateLabel} 0 90u 70u 12u "Password:"
    ${NSD_CreatePassword} 80u 88u 180u 12u ""
    Pop $UsenetPassword
    
    ${NSD_CreateCheckBox} 80u 108u 100u 12u "Use SSL"
    Pop $UseSSL
    ${NSD_Check} $UseSSL ; Check by default
    
    nsDialogs::Show
FunctionEnd

Function ConfigPageLeave
    ${NSD_GetText} $UsenetServer $0
    ${NSD_GetText} $UsenetPort $1
    ${NSD_GetText} $UsenetUsername $2
    ${NSD_GetText} $UsenetPassword $3
    ${NSD_GetState} $UseSSL $4
    
    ; Create configuration file
    DetailPrint "Creating configuration..."
    
    ; Generate config from template
    CopyFiles "$INSTDIR\usenet_sync_config.template.json" "$INSTDIR\config\usenet_sync_config.json"
    
    ; Update config with user settings
    ; (In real implementation, would use a proper JSON parser)
    
FunctionEnd

; Uninstaller Section
Section "Uninstall"
    
    ; Stop services
    DetailPrint "Stopping services..."
    ExecWait 'net stop UsenetSyncDB'
    
    ; Unregister services
    ExecWait '"$INSTDIR\postgresql\bin\pg_ctl.exe" unregister -N "UsenetSyncDB"'
    
    ; Remove firewall rules
    ExecWait 'netsh advfirewall firewall delete rule name="UsenetSync"'
    ExecWait 'netsh advfirewall firewall delete rule name="UsenetSync Database"'
    
    ; Delete shortcuts
    Delete "$DESKTOP\UsenetSync.lnk"
    RMDir /r "$SMPROGRAMS\UsenetSync"
    
    ; Delete installation directory
    RMDir /r "$INSTDIR"
    
    ; Delete registry keys
    DeleteRegKey HKLM "Software\UsenetSync"
    DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\UsenetSync"
    
SectionEnd

; Installer Functions
Function .onInit
    ; Check for 64-bit Windows
    ${If} ${RunningX64}
        SetRegView 64
    ${Else}
        MessageBox MB_OK "UsenetSync requires 64-bit Windows."
        Abort
    ${EndIf}
    
    ; Check for admin rights
    UserInfo::GetAccountType
    Pop $0
    ${If} $0 != "admin"
        MessageBox MB_OK "Administrator rights required for installation."
        Abort
    ${EndIf}
FunctionEnd

Function .onInstSuccess
    MessageBox MB_YESNO "Installation complete! Would you like to start UsenetSync now?" IDNO NoStart
        Exec "$INSTDIR\usenet-sync.exe"
    NoStart:
FunctionEnd