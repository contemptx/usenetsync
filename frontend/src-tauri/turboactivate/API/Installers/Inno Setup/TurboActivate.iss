; -- TurboActivate.iss --
;
; This script shows how to use TurboActivate in your installer.

[Setup]
AppName=My Program
AppVersion=1.5
DefaultDirName={pf}\My Program
DisableProgramGroupPage=yes
UninstallDisplayIcon={app}\MyProg.exe
OutputDir=output

[Files]
; Install TurboActivate to {app} so we can access it at uninstall time
; Also, notice we're putting the TurboActivate files at the top of the file
; list. This is so that if you're using "SolidCompression=yes" your installer
; can still start relatively quickly.
Source: "TurboActivate.dll"; DestDir: "{app}"
Source: "TurboActivate.dat"; DestDir: "{app}"

;TODO: add your files that you'll be installing 
Source: "MyProg.exe"; DestDir: "{app}"


[Code]
//TODO: go to the version page in your LimeLM account and paste this GUID here
const
  VERSION_GUID = '18324776654b3946fc44a5f3.49025204';

  TA_SYSTEM = 1;
  TA_USER = 2;

  /// <summary>
  /// Use the TA_DISALLOW_VM in UseTrial() to disallow trials in virtual machines. 
  /// If you use this flag in UseTrial() and the customer's machine is a Virtual
  /// Machine, then UseTrial() will throw VirtualMachineException.
  /// </summary>
  TA_DISALLOW_VM = 4;

  /// <summary>
  /// Use this flag in TA_UseTrial() to tell TurboActivate to use client-side
  /// unverified trials. For more information about verified vs. unverified trials,
  /// see here: https://wyday.com/limelm/help/trials/
  /// Note: unverified trials are unsecured and can be reset by malicious customers.
  /// </summary>
  TA_UNVERIFIED_TRIAL = 16;

  /// <summary>
  /// Use the TA_VERIFIED_TRIAL flag to use verified trials instead
  /// of unverified trials. This means the trial is locked to a particular computer.
  /// The customer can't reset the trial.
  /// </summary>
  TA_VERIFIED_TRIAL = 32;


  TA_HAS_NOT_EXPIRED = 1;


  TA_OK = $00;
  TA_FAIL = $01;
  TA_E_PKEY = $02;
  TA_E_ACTIVATE = $03;
  TA_E_INET = $04;
  TA_E_INUSE = $05;
  TA_E_REVOKED = $06;
  TA_E_PDETS = $08;
  TA_E_TRIAL = $09;
  TA_E_COM = $0B;
  TA_E_TRIAL_EUSED = $0C;
  TA_E_TRIAL_EEXP = $0D;
  TA_E_EXPIRED = $0D;
  TA_E_INSUFFICIENT_BUFFER = $0E;
  TA_E_PERMISSION = $0F;
  TA_E_INVALID_FLAGS = $10;
  TA_E_IN_VM = $11;
  TA_E_EDATA_LONG = $12;
  TA_E_INVALID_ARGS = $13;
  TA_E_KEY_FOR_TURBOFLOAT = $14;
  TA_E_INET_DELAYED = $15;
  TA_E_FEATURES_CHANGED = $16;
  TA_E_NO_MORE_DEACTIVATIONS = $18;
  TA_E_ACCOUNT_CANCELED = $19;
  TA_E_ALREADY_ACTIVATED = $1A;
  TA_E_INVALID_HANDLE = $1B;
  TA_E_ENABLE_NETWORK_ADAPTERS = $1C;
  TA_E_ALREADY_VERIFIED_TRIAL = $1D;
  TA_E_TRIAL_EXPIRED = $1E;
  TA_E_MUST_SPECIFY_TRIAL_TYPE = $1F;
  TA_E_MUST_USE_TRIAL = $20;



// functions for activation
function TA_GetHandle(versionGUID: WideString): longint;
external 'TA_GetHandle@files:TurboActivate.dll,TurboActivate.dat cdecl setuponly';

function TA_IsActivated(handle: longint): longint;
external 'TA_IsActivated@files:TurboActivate.dll,TurboActivate.dat cdecl setuponly';

function TA_CheckAndSavePKey(handle: longint; productKey: WideString; flags: UINT): longint;
external 'TA_CheckAndSavePKey@files:TurboActivate.dll,TurboActivate.dat cdecl setuponly';

function TA_Activate(handle: longint; options: cardinal): longint;
external 'TA_Activate@files:TurboActivate.dll,TurboActivate.dat cdecl setuponly';


// functions for the uninstaller
function TA_GetHandleUninstall(versionGUID: WideString): longint;
external 'TA_GetHandle@{app}\TurboActivate.dll cdecl uninstallonly';

function TA_IsActivatedUninstall(handle: longint): longint;
external 'TA_IsActivated@{app}\TurboActivate.dll cdecl uninstallonly';

function TA_Deactivate(handle: longint; erasePkey: boolean): longint;
external 'TA_Deactivate@{app}\TurboActivate.dll cdecl uninstallonly';

function TA_Cleanup(): longint;
external 'TA_Cleanup@{app}\TurboActivate.dll cdecl uninstallonly';

var
  PkeyPage: TInputQueryWizardPage;
  activated: Boolean;
  taHandle: longint;

procedure InitializeWizard;
begin
    // create the product key page
    PkeyPage := CreateInputQueryPage(wpWelcome,
        'Type your product key', '',
        'You can find the {#SetupSetting("AppName")} product key in the email we sent you. Activation will register the product key to this computer.');
    PkeyPage.Add('Product Key:', False);
end;


function NextButtonClick(CurPage: Integer): Boolean;
var
  ret: LongInt;
begin

    if CurPage = wpWelcome then begin
        // get the handle for your version GUID
        taHandle := TA_GetHandle(VERSION_GUID);

        // error handling code
        if taHandle = 0 then begin
            MsgBox('Failed to get the TurboActivate handle. Make sure the TurboActivate.dat file is included with your installer and you''re using the correct VersionGUID.', mbError, MB_OK);
            Result := False;
            exit;
        end;


        // after the welcome page, check if we're activated
        ret := TA_IsActivated(taHandle);

        if ret = TA_OK then begin
            activated := true;
        end;
        Result := True;
    end else if CurPage = PkeyPage.ID then begin

        // check if the product key is valid
        ret := TA_CheckAndSavePKey(taHandle, PkeyPage.Values[0], TA_SYSTEM);

        if ret = TA_OK then begin

            // try to activate, show a specific error if it fails
            ret := TA_Activate(taHandle, 0);

            case ret of
              TA_E_PKEY:
                MsgBox('The product key is invalid or there''s no product key.', mbError, MB_OK);
              TA_E_INET:
                MsgBox('Connection to the servers failed.', mbError, MB_OK);
              TA_E_INUSE:
                MsgBox('The product key has already been activated with the maximum number of computers.', mbError, MB_OK);
              TA_E_REVOKED:
                MsgBox('The product key has been revoked.', mbError, MB_OK);
              TA_E_INVALID_HANDLE:
                MsgBox('The handle is not valid. You must set the VersionGUID property.', mbError, MB_OK);
              TA_E_COM:
                MsgBox('CoInitializeEx failed. Re-enable Windows Management Instrumentation (WMI) service. Contact your system admin for more information.', mbError, MB_OK);
              TA_E_ENABLE_NETWORK_ADAPTERS:
                MsgBox('There are network adapters on the system that are disabled and TurboActivate couldn''t read their hardware properties (even after trying and failing to enable the adapters automatically).' + ' Enable the network adapters, re-run the function, and TurboActivate will be able to "remember" the adapters even if the adapters are disabled in the future.', mbError, MB_OK);
              TA_E_EXPIRED:
                MsgBox('Failed because your system date and time settings are incorrect. Fix your date and time settings, restart your computer, and try to activate again.', mbError, MB_OK);
              TA_E_IN_VM:
                MsgBox('Failed to activate because this instance of your program if running inside a virtual machine or hypervisor.', mbError, MB_OK);
              TA_E_INVALID_ARGS:
                MsgBox('The arguments passed to the function are invalid. Double check your logic.', mbError, MB_OK);
              TA_E_KEY_FOR_TURBOFLOAT:
                MsgBox('The product key used is for TurboFloat, not TurboActivate.', mbError, MB_OK);
              TA_E_ACCOUNT_CANCELED:
                MsgBox('Can''t activate because the LimeLM account is cancelled.', mbError, MB_OK); 
              TA_OK: // successful
              begin
                activated := true;
                Result := True
                exit;
              end
              
              else
                MsgBox('Failed to activate. Error code: ' + IntToStr(ret), mbError, MB_OK);
            end;
            Result := False
        end else begin
            MsgBox('You must enter a valid product key. Error code: ' + IntToStr(ret), mbError, MB_OK);
            Result := False;
        end;
    end else
        Result := True;
end;


function ShouldSkipPage(PageID: Integer): Boolean;
begin
    // skip the "Pkey" page if were already activated
    if (PageID = PkeyPage.ID) and activated then
        Result := True
    else
        Result := False;
end;

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
var
  ret: LongInt;
begin
    // Call our function just before the actual uninstall process begins
    if CurUninstallStep = usUninstall then begin

        // get the handle for your version GUID
        taHandle := TA_GetHandleUninstall(VERSION_GUID);

        // error handling code
        if taHandle = 0 then begin
            MsgBox('Failed to get the TurboActivate handle. Make sure the TurboActivate.dat file is included with your installer and you''re using the correct VersionGUID.', mbError, MB_OK);
        end else begin // valid handle

            // deactivate if activated
            if TA_IsActivatedUninstall(taHandle) = TA_OK then begin

                // change the second parameter to "True" if you want to
                // delete the product key from the computer after your app is deactivated
                ret := TA_Deactivate(taHandle, False);
            end;
        end;

        TA_Cleanup();

        // Now that we're finished with it, unload TurboActivate.dll from memory.
        // We have to do this so that the uninstaller will be able to remove the DLL and the {app} directory.
        UnloadDLL(ExpandConstant('{app}\TurboActivate.dll'));
    end;
end;
