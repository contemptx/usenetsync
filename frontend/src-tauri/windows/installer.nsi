; UsenetSync NSIS Installer Script
; Modern UI installer for UsenetSync

!include "MUI2.nsh"
!include "LogicLib.nsh"
!include "WinVer.nsh"
!include "x64.nsh"

; Constants
!define PRODUCT_NAME "UsenetSync"
!define PRODUCT_VERSION "1.0.0"
!define PRODUCT_PUBLISHER "UsenetSync"
!define PRODUCT_WEB_SITE "https://github.com/contemptx/usenetsync"
!define PRODUCT_DIR_REGKEY "Software\Microsoft\Windows\CurrentVersion\App Paths\UsenetSync.exe"
!define PRODUCT_UNINST_KEY "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME}"
!define PRODUCT_UNINST_ROOT_KEY "HKLM"

; MUI Settings
!define MUI_ABORTWARNING
!define MUI_ICON "..\icons\icon.ico"
!define MUI_UNICON "..\icons\icon.ico"
!define MUI_WELCOMEFINISHPAGE_BITMAP "installer-banner.bmp"
!define MUI_HEADERIMAGE
!define MUI_HEADERIMAGE_BITMAP "installer-header.bmp"
!define MUI_HEADERIMAGE_RIGHT

; Welcome page
!insertmacro MUI_PAGE_WELCOME

; License page
!insertmacro MUI_PAGE_LICENSE "LICENSE.txt"

; Components page
!insertmacro MUI_PAGE_COMPONENTS

; Directory page
!insertmacro MUI_PAGE_DIRECTORY

; Install files page
!insertmacro MUI_PAGE_INSTFILES

; Finish page
!define MUI_FINISHPAGE_RUN "$INSTDIR\UsenetSync.exe"
!define MUI_FINISHPAGE_RUN_TEXT "Launch UsenetSync"
!define MUI_FINISHPAGE_SHOWREADME "$INSTDIR\README.md"
!insertmacro MUI_PAGE_FINISH

; Uninstaller pages
!insertmacro MUI_UNPAGE_INSTFILES

; Language files
!insertmacro MUI_LANGUAGE "English"

; Installer attributes
Name "${PRODUCT_NAME} ${PRODUCT_VERSION}"
OutFile "UsenetSync-${PRODUCT_VERSION}-Setup.exe"
InstallDir "$PROGRAMFILES64\UsenetSync"
InstallDirRegKey HKLM "${PRODUCT_DIR_REGKEY}" ""
ShowInstDetails show
ShowUnInstDetails show

; Version Information
VIProductVersion "${PRODUCT_VERSION}.0"
VIAddVersionKey "ProductName" "${PRODUCT_NAME}"
VIAddVersionKey "ProductVersion" "${PRODUCT_VERSION}"
VIAddVersionKey "CompanyName" "${PRODUCT_PUBLISHER}"
VIAddVersionKey "LegalCopyright" "© 2024 ${PRODUCT_PUBLISHER}"
VIAddVersionKey "FileDescription" "UsenetSync Installer"
VIAddVersionKey "FileVersion" "${PRODUCT_VERSION}"

; Request admin privileges
RequestExecutionLevel admin

; Check Windows version
Function .onInit
  ${If} ${RunningX64}
    SetRegView 64
  ${Else}
    MessageBox MB_OK|MB_ICONSTOP "UsenetSync requires a 64-bit version of Windows."
    Abort
  ${EndIf}
  
  ${If} ${IsWin7}
  ${OrIf} ${IsWin8}
  ${OrIf} ${IsWin8.1}
  ${OrIf} ${IsWin10}
  ${OrIf} ${IsWin11}
    ; Supported Windows version
  ${Else}
    MessageBox MB_OK|MB_ICONSTOP "UsenetSync requires Windows 7 or later."
    Abort
  ${EndIf}
FunctionEnd

; Main installation section
Section "UsenetSync Core" SEC_CORE
  SectionIn RO
  
  SetOutPath "$INSTDIR"
  SetOverwrite try
  
  ; Main application files
  File "..\target\release\UsenetSync.exe"
  File "..\README.md"
  File "LICENSE.txt"
  
  ; TurboActivate files
  SetOutPath "$INSTDIR\turboactivate"
  File "..\turboactivate\TurboActivate.dll"
  File "..\turboactivate\TurboActivate.dat"
  
  ; Python backend
  SetOutPath "$INSTDIR\backend"
  File /r "..\..\..\..\src\*.*"
  
  ; Create directories
  CreateDirectory "$INSTDIR\logs"
  CreateDirectory "$INSTDIR\cache"
  CreateDirectory "$INSTDIR\data"
  
  ; Store installation folder
  WriteRegStr HKLM "${PRODUCT_DIR_REGKEY}" "" "$INSTDIR\UsenetSync.exe"
  
  ; Create uninstaller
  WriteUninstaller "$INSTDIR\Uninstall.exe"
  
  ; Write registry keys for Add/Remove Programs
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "DisplayName" "${PRODUCT_NAME}"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "UninstallString" "$INSTDIR\Uninstall.exe"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "DisplayIcon" "$INSTDIR\UsenetSync.exe"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "DisplayVersion" "${PRODUCT_VERSION}"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "Publisher" "${PRODUCT_PUBLISHER}"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "URLInfoAbout" "${PRODUCT_WEB_SITE}"
  
  ; Estimate size
  ${GetSize} "$INSTDIR" "/S=0K" $0 $1 $2
  IntFmt $0 "0x%08X" $0
  WriteRegDWORD ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "EstimatedSize" "$0"
SectionEnd

; Desktop shortcut section
Section "Desktop Shortcut" SEC_DESKTOP
  CreateShortcut "$DESKTOP\UsenetSync.lnk" "$INSTDIR\UsenetSync.exe"
SectionEnd

; Start menu shortcuts section
Section "Start Menu Shortcuts" SEC_STARTMENU
  CreateDirectory "$SMPROGRAMS\UsenetSync"
  CreateShortcut "$SMPROGRAMS\UsenetSync\UsenetSync.lnk" "$INSTDIR\UsenetSync.exe"
  CreateShortcut "$SMPROGRAMS\UsenetSync\Uninstall.lnk" "$INSTDIR\Uninstall.exe"
  CreateShortcut "$SMPROGRAMS\UsenetSync\README.lnk" "$INSTDIR\README.md"
SectionEnd

; PostgreSQL installation section
Section "PostgreSQL (Required)" SEC_POSTGRESQL
  SectionIn RO
  
  ; Check if PostgreSQL is already installed
  ReadRegStr $0 HKLM "SOFTWARE\PostgreSQL\Installations" "Version"
  ${If} $0 == ""
    DetailPrint "Installing PostgreSQL..."
    
    ; Download PostgreSQL installer if not present
    IfFileExists "$TEMP\postgresql-installer.exe" +2
      NSISdl::download "https://get.enterprisedb.com/postgresql/postgresql-15.5-1-windows-x64.exe" "$TEMP\postgresql-installer.exe"
    
    ; Run PostgreSQL installer silently
    ExecWait '"$TEMP\postgresql-installer.exe" --mode unattended --unattendedmodeui none --superpassword "postgres" --servicename "PostgreSQL" --servicepassword "postgres" --serverport 5432'
    
    ; Create UsenetSync database
    ExecWait '"$PROGRAMFILES64\PostgreSQL\15\bin\psql.exe" -U postgres -c "CREATE DATABASE usenet_sync;"'
    ExecWait '"$PROGRAMFILES64\PostgreSQL\15\bin\psql.exe" -U postgres -c "CREATE USER usenet_user WITH PASSWORD ''usenet_pass'';"'
    ExecWait '"$PROGRAMFILES64\PostgreSQL\15\bin\psql.exe" -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE usenet_sync TO usenet_user;"'
  ${Else}
    DetailPrint "PostgreSQL is already installed."
  ${EndIf}
SectionEnd

; Python runtime section
Section "Python Runtime (Required)" SEC_PYTHON
  SectionIn RO
  
  ; Check if Python is installed
  ExecWait 'python --version' $0
  ${If} $0 != 0
    DetailPrint "Installing Python runtime..."
    
    ; Download Python embeddable package
    IfFileExists "$TEMP\python-embed.zip" +2
      NSISdl::download "https://www.python.org/ftp/python/3.11.7/python-3.11.7-embed-amd64.zip" "$TEMP\python-embed.zip"
    
    ; Extract Python to installation directory
    CreateDirectory "$INSTDIR\python"
    nsisunz::UnzipToLog "$TEMP\python-embed.zip" "$INSTDIR\python"
    
    ; Install pip
    ExecWait '"$INSTDIR\python\python.exe" -m ensurepip'
    
    ; Install Python dependencies
    ExecWait '"$INSTDIR\python\python.exe" -m pip install -r "$INSTDIR\backend\requirements.txt"'
  ${Else}
    DetailPrint "Python is already installed."
    
    ; Install Python dependencies using system Python
    ExecWait 'python -m pip install -r "$INSTDIR\backend\requirements.txt"'
  ${EndIf}
SectionEnd

; Section descriptions
!insertmacro MUI_FUNCTION_DESCRIPTION_BEGIN
  !insertmacro MUI_DESCRIPTION_TEXT ${SEC_CORE} "Core UsenetSync application files (required)"
  !insertmacro MUI_DESCRIPTION_TEXT ${SEC_DESKTOP} "Create a desktop shortcut"
  !insertmacro MUI_DESCRIPTION_TEXT ${SEC_STARTMENU} "Create Start Menu shortcuts"
  !insertmacro MUI_DESCRIPTION_TEXT ${SEC_POSTGRESQL} "PostgreSQL database server (required for operation)"
  !insertmacro MUI_DESCRIPTION_TEXT ${SEC_PYTHON} "Python runtime and dependencies (required for backend)"
!insertmacro MUI_FUNCTION_DESCRIPTION_END

; Uninstaller section
Section Uninstall
  ; Stop services if running
  ExecWait 'taskkill /F /IM UsenetSync.exe'
  
  ; Remove files
  Delete "$INSTDIR\UsenetSync.exe"
  Delete "$INSTDIR\Uninstall.exe"
  Delete "$INSTDIR\README.md"
  Delete "$INSTDIR\LICENSE.txt"
  
  ; Remove directories
  RMDir /r "$INSTDIR\turboactivate"
  RMDir /r "$INSTDIR\backend"
  RMDir /r "$INSTDIR\python"
  RMDir /r "$INSTDIR\logs"
  RMDir /r "$INSTDIR\cache"
  RMDir /r "$INSTDIR\data"
  RMDir "$INSTDIR"
  
  ; Remove shortcuts
  Delete "$DESKTOP\UsenetSync.lnk"
  Delete "$SMPROGRAMS\UsenetSync\*.*"
  RMDir "$SMPROGRAMS\UsenetSync"
  
  ; Remove registry keys
  DeleteRegKey ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}"
  DeleteRegKey HKLM "${PRODUCT_DIR_REGKEY}"
  
  SetAutoClose true
SectionEnd