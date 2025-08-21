;Basic TurboActivate Example Script

;--------------------------------
;Include Modern UI, Logic Library, 

  !include "MUI2.nsh"
  !include LogicLib.nsh
  !include nsDialogs.nsh
  !include WinVer.nsh

  ; TODO: paste your version GUID here
  !define VersionGUID '18324776654b3946fc44a5f3.49025204'

  ; Comment out the next 1 or 2 lines
  ; if you don't want to require the user enter
  ; their product key or activate before they can
  ; install your app.
  !define REQUIRE_ACT
  !define REQUIRE_PKEY


;--------------------------------
;General

  ;Name and file
  Name "YourApp"
  OutFile "Setup.exe"

  ;Default installation folder
  InstallDir "$PROGRAMFILES\YourApp"

  ;Get installation folder from registry if available
  InstallDirRegKey HKCU "Software\YourApp" ""

  ;Request application privileges for Windows Vista+
  RequestExecutionLevel admin

  ; best compression
  SetCompressor /SOLID lzma

;--------------------------------
;Pages

  !insertmacro MUI_PAGE_LICENSE "${NSISDIR}\Docs\Modern UI\License.txt"
  Page custom PagePKey PagePKeyLeave
  !insertmacro MUI_PAGE_COMPONENTS
  !insertmacro MUI_PAGE_DIRECTORY
  !insertmacro MUI_PAGE_INSTFILES

  !insertmacro MUI_UNPAGE_CONFIRM
  !insertmacro MUI_UNPAGE_INSTFILES

;--------------------------------
;Languages

  !insertmacro MUI_LANGUAGE "English"


; "Reserve" TurboActivate (thus put them at the top of the compressed block)
; This speeds up installer.
  ReserveFile "TurboActivate.dll"
  ReserveFile "TurboActivate.dat"


Function .onInit

	; TurboActivate requires at least Windows XP
	${IfNot} ${AtLeastWinXP}
		MessageBox MB_OK "Windows XP (or newer) is required to run $(^NameDA)."
		Quit
	${EndIf}

	; create the plugins folder
	InitPluginsDir

	; extract the TurboActivate files to the plugns folder
	File /oname=$PLUGINSDIR\TurboActivate.dll "TurboActivate.dll"
	File /oname=$PLUGINSDIR\TurboActivate.dat "TurboActivate.dat"

FunctionEnd


;--------------------------------
;Installer Sections

Section "Dummy Section" SecDummy

	SetOutPath "$INSTDIR"

	File "TurboActivate.dll"
	File "TurboActivate.dat"

	;ADD YOUR OWN FILES HERE...

	;Store installation folder
	WriteRegStr HKCU "Software\YourApp" "" $INSTDIR

	;Create uninstaller
	WriteUninstaller "$INSTDIR\Uninstall.exe"

SectionEnd

;--------------------------------
;Descriptions

  ;Language strings
  LangString DESC_SecDummy ${LANG_ENGLISH} "A test section."

  ;Assign language strings to sections
  !insertmacro MUI_FUNCTION_DESCRIPTION_BEGIN
  !insertmacro MUI_DESCRIPTION_TEXT ${SecDummy} $(DESC_SecDummy)
  !insertmacro MUI_FUNCTION_DESCRIPTION_END


;--------------------------------
; Product key page

Var txtPKey

Function PagePKey
	; TurboActivate is in the plugins directory.
	; Setting the output path ensures we can call it.
	SetOutPath $PLUGINSDIR

	; Check if we're activated
	System::Call "TurboActivate::IsActivated(w'${VersionGUID}') i.r2 ? c"

	; Skip this page if we're already activated
	${If} $2 == 0
		Abort
	${EndIf}


	!insertmacro MUI_HEADER_TEXT "Type your product key" ""

	nsDialogs::Create 1018
	Pop $0

	nsDialogs::CreateControl STATIC ${WS_VISIBLE}|${WS_CHILD}|${WS_CLIPSIBLINGS} 0 0 0 100% 30 "You can find the $(^NameDA) product key in the email we sent you. Activation will register the product key to this computer."
	Pop $0

	nsDialogs::CreateControl STATIC ${WS_VISIBLE}|${WS_CHILD}|${WS_CLIPSIBLINGS} 0 0 50 100% 20 "Product Key:"
	Pop $0

	nsDialogs::CreateControl EDIT ${WS_VISIBLE}|${WS_CHILD}|${WS_CLIPSIBLINGS}|${ES_AUTOHSCROLL}|${WS_TABSTOP} ${WS_EX_CLIENTEDGE} 0 75 100% 12u ""
	Pop $txtPKey

	; focus the product key box
	SendMessage $HWNDPARENT ${WM_NEXTDLGCTL} $txtPKey 1

	nsDialogs::Show

FunctionEnd

Function PagePKeyLeave
	; TurboActivate is in the plugins directory.
	; Setting the output path ensures we can call it.
	SetOutPath $PLUGINSDIR

	; get the product key in WCHAR * form, put on $0
	System::Call user32::GetWindowTextW(i$txtPKey,w.r0,i${NSIS_MAX_STRLEN})

	; check if the product key is valid
	System::Call "TurboActivate::CheckAndSavePKey(wr0, i1) i.r2 ? c"

	; require the product key if we're requiring the activation
	!ifdef REQUIRE_ACT
		!ifndef REQUIRE_PKEY
			!define REQUIRE_PKEY
		!endif
	!endif

	${If} $2 == 0

		; try to activate, show a specific error if it fails
		System::Call "TurboActivate::Activate() i.r2 ? c"

		!ifdef REQUIRE_ACT

		${Switch} $2
		  ${Case} 0 ; successful
			Goto actSuccess
		  ${Case} 2 ; TA_E_PKEY
			MessageBox MB_OK|MB_ICONSTOP "The product key is invalid or there's no product key."
			${Break}
		  ${Case} 4 ; TA_E_INET
			MessageBox MB_OK|MB_ICONSTOP "Connection to the server failed."
			${Break}
		  ${Case} 5 ; TA_E_INUSE
			MessageBox MB_OK|MB_ICONSTOP "The product key has already been activated with the maximum number of computers."
			${Break}
		  ${Case} 6 ; TA_E_REVOKED
			MessageBox MB_OK|MB_ICONSTOP "The product key has been revoked."
			${Break}
		  ${Case} 8 ; TA_E_PDETS
			MessageBox MB_OK|MB_ICONSTOP "The product details file 'TurboActivate.dat' failed to load. It's either missing or corrupt."
			${Break}
		  ${Case} 11 ; TA_E_COM
			MessageBox MB_OK|MB_ICONSTOP "CoInitializeEx failed."
			${Break}
		  ${Case} 13 ; TA_E_EXPIRED
			MessageBox MB_OK|MB_ICONSTOP "Failed because your system date and time settings are incorrect. Fix your date and time settings, restart your computer, and try to activate again."
			${Break}
		  ${Case} 17 ; TA_E_IN_VM
			MessageBox MB_OK|MB_ICONSTOP "Failed to activate because this instance of your program if running inside a virtual machine or hypervisor."
			${Break}
		  ${Case} 20 ; TA_E_KEY_FOR_TURBOFLOAT
			MessageBox MB_OK|MB_ICONSTOP "The product key used is for TurboFloat, not TurboActivate."
			${Break}
		  ${Default}
			MessageBox MB_OK|MB_ICONSTOP "Failed to activate."
			${Break}
		${EndSwitch}

		!endif

	${Else}

		!ifdef REQUIRE_PKEY
		MessageBox MB_OK|MB_ICONSTOP "You must enter a valid product key."

		; focus the product key box
		SendMessage $HWNDPARENT ${WM_NEXTDLGCTL} $txtPKey 1
		Abort
		!endif

	${EndIf}

	actSuccess:
FunctionEnd






;--------------------------------
;Uninstaller Section

Section "Uninstall"

	; Set the output path to the installation directory so we can call TurboActivate
	SetOutPath $INSTDIR

	; check if activated
	System::Call "TurboActivate::IsActivated(w'${VersionGUID}') i.r2 ? cu"

	; deactivate if activated
	${If} $2 == 0
		System::Call "TurboActivate::Deactivate(i1) i.r2 ? cu"
	${EndIf}


	; Set the output directory to the temp folder where this uninstaller resides
	; so we can delete the '$INSTDIR'. Otherwise the earlier "SetOutPath" locks the
	; "$INSTDIR" making it impossible to delete.
	SetOutPath $EXEDIR



	;ADD YOUR OWN FILES HERE...

	Delete "$INSTDIR\TurboActivate.dll"
	Delete "$INSTDIR\TurboActivate.dat"
	Delete "$INSTDIR\Uninstall.exe"

	RMDir "$INSTDIR"

	DeleteRegKey /ifempty HKCU "Software\YourApp"

SectionEnd