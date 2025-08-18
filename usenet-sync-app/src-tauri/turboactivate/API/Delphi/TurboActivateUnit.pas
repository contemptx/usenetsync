unit TurboActivateUnit;

interface

uses
  {$IFNDEF MACOS}
  Windows,
  {$ENDIF}
  SysUtils;

  {$IFDEF MACOS}
  // external functions in libTurboActivate.dylib
  function TA_GetHandle(versionGUID: System.PAnsiChar):LongWord; cdecl; external 'libTurboActivate.dylib' name '_TA_GetHandle';
  function TA_Activate(handle: LongWord; options: Pointer):LongInt; cdecl; external 'libTurboActivate.dylib' name '_TA_Activate';
  function TA_ActivationRequestToFile(handle: LongWord; filename: System.PAnsiChar; options: Pointer):LongInt; cdecl; external 'libTurboActivate.dylib' name '_TA_ActivationRequestToFile';
  function TA_ActivateFromFile(handle: LongWord; filename: System.PAnsiChar):LongInt; cdecl; external 'libTurboActivate.dylib' name '_TA_ActivateFromFile';
  function TA_CheckAndSavePKey(handle: LongWord; productKey: System.PAnsiChar; flags: LongWord):LongInt; cdecl; external 'libTurboActivate.dylib' name '_TA_CheckAndSavePKey';
  function TA_Deactivate(handle: LongWord; erasePkey: boolean):LongInt; cdecl; external 'libTurboActivate.dylib' name '_TA_Deactivate';
  function TA_DeactivationRequestToFile(handle: LongWord; filename: System.PAnsiChar; erasePkey: boolean):LongInt; cdecl; external 'libTurboActivate.dylib' name '_TA_DeactivationRequestToFile';
  function TA_GetExtraData(handle: LongWord; lpValueStr: System.PAnsiChar; cchValue: Integer):LongInt; cdecl; external 'libTurboActivate.dylib' name '_TA_GetExtraData';
  function TA_GetFeatureValue(handle: LongWord; featureName: System.PAnsiChar; lpValueStr: System.PAnsiChar; cchValue: Integer):LongInt; cdecl; external 'libTurboActivate.dylib' name '_TA_GetFeatureValue';
  function TA_GetPKey(handle: LongWord; lpValueStr: System.PAnsiChar; cchValue: Integer):LongInt; cdecl; external 'libTurboActivate.dylib' name '_TA_GetPKey';
  function TA_IsActivated(handle: LongWord):LongInt; cdecl; external 'libTurboActivate.dylib' name '_TA_IsActivated';
  function TA_IsDateValid(handle: LongWord; date_time: System.PAnsiChar; flags: LongWord):LongInt; cdecl; external 'libTurboActivate.dylib' name '_TA_IsDateValid';
  function TA_IsGenuine(handle: LongWord):LongInt; cdecl; external 'libTurboActivate.dylib' name '_TA_IsGenuine';
  function TA_IsGenuineEx(handle: LongWord; options: Pointer):LongInt; cdecl; external 'libTurboActivate.dylib' name '_TA_IsGenuineEx';
  function TA_GenuineDays(handle: LongWord; nDaysBetweenChecks: LongWord; nGraceDaysOnInetErr: LongWord; var DaysRemaining: LongWord; var inGracePeriod: Byte):LongInt; cdecl; external 'libTurboActivate.dylib' name '_TA_GenuineDays';
  function TA_IsProductKeyValid(handle: LongWord):LongInt; cdecl; external 'libTurboActivate.dylib' name '_TA_IsProductKeyValid';
  function TA_SetCustomProxy(proxy: System.PAnsiChar):LongInt; cdecl; external 'libTurboActivate.dylib' name '_TA_SetCustomProxy';
  function TA_TrialDaysRemaining(handle: LongWord; useTrialFlags: LongWord; var DaysRemaining: LongWord):LongInt; cdecl; external 'libTurboActivate.dylib' name '_TA_TrialDaysRemaining';
  function TA_UseTrial(handle: LongWord; flags: LongWord; extra_data: System.PAnsiChar):LongInt; cdecl; external 'libTurboActivate.dylib' name '_TA_UseTrial';
  function TA_UseTrialVerifiedRequest(handle: LongWord; filename: System.PAnsiChar; extra_data: System.PAnsiChar):LongInt; cdecl; external 'libTurboActivate.dylib' name '_TA_UseTrialVerifiedRequest';
  function TA_UseTrialVerifiedFromFile(handle: LongWord; filename: System.PAnsiChar; flags: LongWord):LongInt; cdecl; external 'libTurboActivate.dylib' name '_TA_UseTrialVerifiedFromFile';
  function TA_ExtendTrial(handle: LongWord; flags: LongWord; trialExtension: System.PAnsiChar):LongInt; cdecl; external 'libTurboActivate.dylib' name '_TA_ExtendTrial';
  function TA_PDetsFromPath(filename: System.PAnsiChar):LongInt; cdecl; external 'libTurboActivate.dylib' name '_TA_PDetsFromPath';

  {$ELSE}

  // external functions in TurboActivate.dll
  function TA_GetHandle(versionGUID: LPCWSTR):LongWord; cdecl; external 'TurboActivate.dll';
  function TA_Activate(handle: LongWord; options: Pointer):LongInt; cdecl; external 'TurboActivate.dll';
  function TA_ActivationRequestToFile(handle: LongWord; filename: LPCWSTR; options: Pointer):LongInt; cdecl; external 'TurboActivate.dll';
  function TA_ActivateFromFile(handle: LongWord; filename: LPCWSTR):LongInt; cdecl; external 'TurboActivate.dll';
  function TA_CheckAndSavePKey(handle: LongWord; productKey: LPCWSTR; flags: LongWord):LongInt; cdecl; external 'TurboActivate.dll';
  function TA_Deactivate(handle: LongWord; erasePkey: boolean):LongInt; cdecl; external 'TurboActivate.dll';
  function TA_DeactivationRequestToFile(handle: LongWord; filename: LPCWSTR; erasePkey: boolean):LongInt; cdecl; external 'TurboActivate.dll';
  function TA_GetExtraData(handle: LongWord; lpValueStr: LPWSTR; cchValue: Integer):LongInt; cdecl; external 'TurboActivate.dll';
  function TA_GetFeatureValue(handle: LongWord; featureName: LPCWSTR; lpValueStr: LPWSTR; cchValue: Integer):LongInt; cdecl; external 'TurboActivate.dll';
  function TA_GetPKey(handle: LongWord; lpValueStr: LPWSTR; cchValue: Integer):LongInt; cdecl; external 'TurboActivate.dll';
  function TA_IsActivated(handle: LongWord):LongInt; cdecl; external 'TurboActivate.dll';
  function TA_IsDateValid(handle: LongWord; date_time: LPCWSTR; flags: LongWord):LongInt; cdecl; external 'TurboActivate.dll';
  function TA_IsGenuine(handle: LongWord):LongInt; cdecl; external 'TurboActivate.dll';
  function TA_IsGenuineEx(handle: LongWord; options: Pointer):LongInt; cdecl; external 'TurboActivate.dll';
  function TA_GenuineDays(handle: LongWord; nDaysBetweenChecks: LongWord; nGraceDaysOnInetErr: LongWord; var DaysRemaining: LongWord; var inGracePeriod: Byte):LongInt; cdecl; external 'TurboActivate.dll';
  function TA_IsProductKeyValid(handle: LongWord):LongInt; cdecl; external 'TurboActivate.dll';
  function TA_SetCustomProxy(proxy: LPCWSTR):LongInt; cdecl; external 'TurboActivate.dll';
  function TA_TrialDaysRemaining(handle: LongWord; useTrialFlags: LongWord; var DaysRemaining: LongWord):LongInt; cdecl; external 'TurboActivate.dll';
  function TA_UseTrial(handle: LongWord; flags: LongWord; extra_data: LPCWSTR):LongInt; cdecl; external 'TurboActivate.dll';
  function TA_UseTrialVerifiedRequest(handle: LongWord; filename: LPCWSTR; extra_data: LPCWSTR):LongInt; cdecl; external 'TurboActivate.dll';
  function TA_UseTrialVerifiedFromFile(handle: LongWord; filename: LPCWSTR; flags: LongWord):LongInt; cdecl; external 'TurboActivate.dll';
  function TA_ExtendTrial(handle: LongWord; flags: LongWord; trialExtension: LPCWSTR):LongInt; cdecl; external 'TurboActivate.dll';
  function TA_PDetsFromPath(filename: LPCWSTR):LongInt; cdecl; external 'TurboActivate.dll';
  {$ENDIF}

const
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
  TA_E_NO_MORE_TRIALS_ALLOWED = $21;
  TA_E_BROKEN_WMI = $22;
  TA_E_INET_TIMEOUT = $23;
  TA_E_INET_TLS = $24;



type
  ETurboActivateException = class(Exception);

  IsGenuineResult = (Genuine = 0, GenuineFeaturesChanged = 1, NotGenuine = 2, NotGenuineInVM = 3, InternetError = 4);

  pACTIVATE_OPTIONS = ^ACTIVATE_OPTIONS;
  ACTIVATE_OPTIONS=packed record
    nLength: LongWord;
    {$IFDEF MACOS}
      sExtraData: PAnsiChar;
    {$ELSE}
      sExtraData: PWideChar;
    {$ENDIF}
  end;

  pGENUINE_OPTIONS = ^GENUINE_OPTIONS;
  GENUINE_OPTIONS=packed record
    nLength: LongWord;
    flags: LongWord;
    nDaysBetweenChecks: LongWord;
    nGraceDaysOnInetErr: LongWord;
  end;

  TurboActivate = class
  private
    versGUID   : String;
    handle     : LongWord;

    function TaHresultToExcep(ret: LongInt; funcName: String): ETurboActivateException;

  public
  {$IFDEF MACOS}
    // TurboActivate constructor
    Constructor Create(vGUID: System.PAnsiChar; pdetsFilename: System.PAnsiChar = nil);

    // function declarations
    procedure Activate(extraData: String = '');
    procedure ActivationRequestToFile(filename: String; extraData: String = '');
    procedure ActivateFromFile(filename: String);
    function CheckAndSavePKey(productKey: String; flags: LongWord = TA_SYSTEM): boolean;
    procedure DeactivationRequestToFile(filename: String; erasePkey: boolean);
    function GetExtraData(): String;
    function GetFeatureValue(featureName: String): String; overload;
    function GetFeatureValue(featureName: String; defaultValue: String): String; overload;
    function GetPKey(): String;
    function IsDateValid(date_time: String; flags: LongWord): boolean;
    procedure SetCustomProxy(proxy: String);
    procedure UseTrial(flags: LongWord = TA_SYSTEM or TA_VERIFIED_TRIAL; extraData: String = '');
    procedure UseTrialVerifiedRequest(filename: String; extraData: String = '');
    procedure UseTrialVerifiedFromFile(filename: String; flags: LongWord = TA_SYSTEM or TA_VERIFIED_TRIAL);
    procedure ExtendTrial(trialExtension: String; useTrialFlags: LongWord = TA_SYSTEM or TA_VERIFIED_TRIAL);
  {$ELSE}
    // TurboActivate constructor
    Constructor Create(vGUID: LPCWSTR; pdetsFilename: LPCWSTR = nil);

    // function declarations
    procedure Activate(extraData: WideString = '');
    procedure ActivationRequestToFile(filename: WideString; extraData: WideString = '');
    procedure ActivateFromFile(filename: WideString);
    function CheckAndSavePKey(productKey: WideString; flags: LongWord = TA_SYSTEM): boolean;
    procedure DeactivationRequestToFile(filename: WideString; erasePkey: boolean);
    function GetExtraData(): WideString;
    function GetFeatureValue(featureName: WideString): WideString; overload;
    function GetFeatureValue(featureName: WideString; defaultValue: WideString): WideString; overload;
    function GetPKey(): WideString;
    function IsDateValid(date_time: WideString; flags: LongWord): boolean;
    procedure SetCustomProxy(proxy: WideString);
    procedure UseTrial(flags: LongWord = TA_SYSTEM or TA_VERIFIED_TRIAL; extraData: WideString = '');
    procedure UseTrialVerifiedRequest(filename: WideString; extraData: WideString = '');
    procedure UseTrialVerifiedFromFile(filename: WideString; flags: LongWord = TA_SYSTEM or TA_VERIFIED_TRIAL);
    procedure ExtendTrial(trialExtension: WideString; useTrialFlags: LongWord = TA_SYSTEM or TA_VERIFIED_TRIAL);
  {$ENDIF}

    procedure Deactivate(erasePkey: boolean = false);
    function IsActivated(): boolean;
    function IsGenuine(): IsGenuineResult; overload;
    function IsGenuine(daysBetweenChecks: LongWord; graceDaysOnInetErr: LongWord; skipOffline: boolean = false; offlineShowInetErr: boolean = false): IsGenuineResult; overload;
    function GenuineDays(daysBetweenChecks: LongWord; graceDaysOnInetErr: LongWord; var inGracePeriod: boolean): LongWord;
    function IsProductKeyValid(): boolean;
    function TrialDaysRemaining(useTrialFlags: LongWord = TA_SYSTEM or TA_VERIFIED_TRIAL): LongWord;
  end;



  ECOMException = class(ETurboActivateException)
  public
    constructor Create();
  end;

  EAccountCanceledException = class(ETurboActivateException)
  public
    constructor Create();
  end;

  EPkeyRevokedException = class(ETurboActivateException)
  public
    constructor Create();
  end;

  EPkeyMaxUsedException = class(ETurboActivateException)
  public
    constructor Create();
  end;

  EInternetException = class(ETurboActivateException)
  public
    constructor Create(); overload;
    constructor Create(msg: String); overload;
  end;

  EInternetTimeoutException = class(EInternetException)
  public
    constructor Create();
  end;

  EInternetTLSException = class(EInternetException)
  public
    constructor Create();
  end;

  EInvalidProductKeyException = class(ETurboActivateException)
  public
    constructor Create();
  end;

  ENotActivatedException = class(ETurboActivateException)
  public
    constructor Create();
  end;

  EProductDetailsException = class(ETurboActivateException)
  public
    constructor Create();
  end;

  EInvalidHandleException = class(ETurboActivateException)
  public
    constructor Create();
  end;

  ETrialExtUsedException = class(ETurboActivateException)
  public
    constructor Create();
  end;

  ETrialDateCorruptedException = class(ETurboActivateException)
  public
    constructor Create();
  end;

  ETrialExtExpiredException = class(ETurboActivateException)
  public
    constructor Create();
  end;

  EDateTimeException = class(ETurboActivateException)
  public
    constructor Create();
  end;

  EPermissionException = class(ETurboActivateException)
  public
    constructor Create();
  end;

  EInvalidFlagsException = class(ETurboActivateException)
  public
    constructor Create();
  end;

  EVirtualMachineException = class(ETurboActivateException)
  public
    constructor Create();
  end;

  EExtraDataTooLongException = class(ETurboActivateException)
  public
    constructor Create();
  end;

  EInvalidArgsException = class(ETurboActivateException)
  public
    constructor Create();
  end;

  ETurboFloatKeyException = class(ETurboActivateException)
  public
    constructor Create();
  end;

  ENoMoreDeactivationsException = class(ETurboActivateException)
  public
    constructor Create();
  end;

  EEnableNetworkAdaptersException = class(ETurboActivateException)
  public
    constructor Create();
  end;

  EAlreadyActivatedException = class(ETurboActivateException)
  public
    constructor Create();
  end;

  EAlreadyVerifiedTrialException = class(ETurboActivateException)
  public
    constructor Create();
  end;

  ETrialExpiredException = class(ETurboActivateException)
  public
    constructor Create();
  end;

  ENoMoreTrialsAllowedException = class(ETurboActivateException)
  public
    constructor Create();
  end;

  EMustSpecifyTrialTypeException = class(ETurboActivateException)
  public
    constructor Create();
  end;

  EMustUseTrialException = class(ETurboActivateException)
  public
    constructor Create();
  end;

  EBrokenWMIException = class(ETurboActivateException)
  public
    constructor Create();
  end;

implementation


/// <summary>Creates a TurboActivate object instance.</summary>
/// <param name="vGUID">The GUID for this product version. This is found on the LimeLM site on the version overview.</param>
/// <param name="pdetsFilename">The absolute location to the TurboActivate.dat file on the disk.</param>
{$IFDEF MACOS}
constructor TurboActivate.Create(vGUID: System.PAnsiChar; pdetsFilename: System.PAnsiChar);
{$ELSE}
constructor TurboActivate.Create(vGUID: LPCWSTR; pdetsFilename: LPCWSTR);
{$ENDIF}
var
  ret : LongInt;
begin

  if not (pdetsFilename = nil) then begin
    ret := TurboActivateUnit.TA_PDetsFromPath(pdetsFilename);

    case ret of
      TA_E_PDETS:
        raise EProductDetailsException.Create();
      TA_OK, TA_FAIL: // successful or the TurboActivate.dat already loaded.
            ; // don't do anything
      else
        raise ETurboActivateException.Create('The TurboActivate.dat file failed to load.');
    end;
  end;

  self.versGUID := vGUID;

  //  get the handle
  self.handle := TurboActivateUnit.TA_GetHandle(vGUID);

  // if the handle is still unset then immediately throw an exception
  // telling the user that they need to actually load the correct
  // TurboActivate.dat and/or use the correct GUID for the TurboActivate.dat
  if self.handle = 0 then begin
    raise EProductDetailsException.Create();
  end;
end;



function TurboActivate.TaHresultToExcep(ret: LongInt; funcName: String): ETurboActivateException;
begin
  case ret of
    TA_FAIL:
      Result := ETurboActivateException.Create(funcName + ' general failure.');
    TA_E_PKEY:
      Result := EInvalidProductKeyException.Create();
    TA_E_ACTIVATE:
      Result := ENotActivatedException.Create();
    TA_E_INET:
      Result := EInternetException.Create();
    TA_E_INET_TIMEOUT:
      Result := EInternetTimeoutException.Create();
    TA_E_INET_TLS:
      Result := EInternetTLSException.Create();
    TA_E_INUSE:
      Result := EPkeyMaxUsedException.Create();
    TA_E_REVOKED:
      Result := EPkeyRevokedException.Create();
    TA_E_TRIAL:
      Result := ETrialDateCorruptedException.Create();
    TA_E_COM:
      Result := ECOMException.Create();
    TA_E_INVALID_HANDLE:
      Result := EInvalidHandleException.Create();
    TA_E_TRIAL_EUSED:
      Result := ETrialExtUsedException.Create();
    TA_E_EXPIRED:
      Result := EDateTimeException.Create();
    TA_E_PERMISSION:
      Result := EPermissionException.Create();
    TA_E_INVALID_FLAGS:
      Result := EInvalidFlagsException.Create();
    TA_E_IN_VM:
      Result := EVirtualMachineException.Create();
    TA_E_EDATA_LONG:
      Result := EExtraDataTooLongException.Create();
    TA_E_INVALID_ARGS:
      Result := EInvalidArgsException.Create();
    TA_E_KEY_FOR_TURBOFLOAT:
      Result := ETurboFloatKeyException.Create();
    TA_E_NO_MORE_DEACTIVATIONS:
      Result := ENoMoreDeactivationsException.Create();
    TA_E_ACCOUNT_CANCELED:
      Result := EAccountCanceledException.Create();
    TA_E_ALREADY_ACTIVATED:
      Result := EAlreadyActivatedException.Create();
    TA_E_ENABLE_NETWORK_ADAPTERS:
      Result := EEnableNetworkAdaptersException.Create();
    TA_E_ALREADY_VERIFIED_TRIAL:
      Result := EAlreadyVerifiedTrialException.Create();
    TA_E_TRIAL_EXPIRED:
      Result := ETrialExpiredException.Create();
    TA_E_MUST_SPECIFY_TRIAL_TYPE:
      Result := EMustSpecifyTrialTypeException.Create();
    TA_E_MUST_USE_TRIAL:
      Result := EMustUseTrialException.Create();
    TA_E_NO_MORE_TRIALS_ALLOWED:
      Result := ENoMoreTrialsAllowedException.Create();
    TA_E_BROKEN_WMI:
      Result := EBrokenWMIException.Create();
    else
      Result := ETurboActivateException.Create(funcName + ' failed with an unknown error code: ' + IntToStr(ret));
  end;
end;



/// <summary>
/// Activates the product on this computer. You must call CheckAndSavePKey(string) with a valid product key or have used the TurboActivate wizard sometime before calling this function.
/// </summary>
{$IFDEF MACOS}
procedure TurboActivate.Activate(extraData: String);
{$ELSE}
procedure TurboActivate.Activate(extraData: WideString);
{$ENDIF}
var
  ret : LongInt;
  options : ACTIVATE_OPTIONS;
begin

  if extraData = '' then
    begin
      ret := TurboActivateUnit.TA_Activate(self.handle, nil);
    end
  else
    begin
      options.nLength := SizeOf(ACTIVATE_OPTIONS);
      options.sExtraData := Addr(extraData[1]);

      ret := TurboActivateUnit.TA_Activate(self.handle, Addr(options));
    end;

  if (ret <> TA_OK) then begin
    raise TaHresultToExcep(ret, 'Activate');
  end;
end;

/// <summary>
/// Get the "activation request" file for offline activation.
/// </summary>
{$IFDEF MACOS}
procedure TurboActivate.ActivationRequestToFile(filename: String; extraData: String);
{$ELSE}
procedure TurboActivate.ActivationRequestToFile(filename: WideString; extraData: WideString);
{$ENDIF}
var
  ret : LongInt;
  options : ACTIVATE_OPTIONS;
begin
  if extraData = '' then
    begin
      ret := TurboActivateUnit.TA_ActivationRequestToFile(self.handle, Addr(filename[1]), nil);
    end
  else
    begin
      options.nLength := SizeOf(ACTIVATE_OPTIONS);
      options.sExtraData := Addr(extraData[1]);

      ret := TurboActivateUnit.TA_ActivationRequestToFile(self.handle, Addr(filename[1]), Addr(options));
    end;

  if (ret <> TA_OK) then begin
    raise TaHresultToExcep(ret, 'ActivationRequestToFile');
  end;
end;

/// <summary>
/// Activate from the "activation response" file for offline activation.
/// </summary>
{$IFDEF MACOS}
procedure TurboActivate.ActivateFromFile(filename: String);
{$ELSE}
procedure TurboActivate.ActivateFromFile(filename: WideString);
{$ENDIF}
var
  ret : LongInt;
begin
  ret := TurboActivateUnit.TA_ActivateFromFile(self.handle, Addr(filename[1]));

  if (ret <> TA_OK) then begin
    raise TaHresultToExcep(ret, 'ActivateFromFile');
  end;
end;

/// <summary>
/// Checks and save the product key.
/// </summary>
/// <param name="productKey">The product key you want to save.</param>
/// <returns>True if the product key is valid, false if it's not</returns>
{$IFDEF MACOS}
function TurboActivate.CheckAndSavePKey(productKey: String; flags: LongWord):boolean;
{$ELSE}
function TurboActivate.CheckAndSavePKey(productKey: WideString; flags: LongWord):boolean;
{$ENDIF}
var
  ret : LongInt;
begin
  ret := TurboActivateUnit.TA_CheckAndSavePKey(self.handle, Addr(productKey[1]), flags);

  case ret of
    TA_OK: // successful
        Result := True;
    TA_FAIL: // not successful
        Result := False;
    else
        raise TaHresultToExcep(ret, 'CheckAndSavePKey');
  end;
end;

/// <summary>
/// Deactivates the product on this computer.
/// </summary>
/// <param name="eraseProductKey">Erase the product key so the user will have to enter a new product key if they wish to reactivate.</param>
procedure TurboActivate.Deactivate(erasePkey: boolean = false);
var
  ret : LongInt;
begin
  ret := TurboActivateUnit.TA_Deactivate(self.handle, erasePkey);

  if (ret <> TA_OK) then begin
    raise TaHresultToExcep(ret, 'Deactivate');
  end;
end;

/// <summary>
/// Get the "deactivation request" file for offline deactivation.
/// </summary>
{$IFDEF MACOS}
procedure TurboActivate.DeactivationRequestToFile(filename: String; erasePkey: boolean);
{$ELSE}
procedure TurboActivate.DeactivationRequestToFile(filename: WideString; erasePkey: boolean);
{$ENDIF}
var
  ret : LongInt;
begin
  ret := TurboActivateUnit.TA_DeactivationRequestToFile(self.handle, Addr(filename[1]), erasePkey);

  if (ret <> TA_OK) then begin
    raise TaHresultToExcep(ret, 'DeactivationRequestToFile');
  end;
end;

/// <summary>Gets the extra data value you passed in when activating.</summary>
{$IFDEF MACOS}
function TurboActivate.GetExtraData(): String;
{$ELSE}
function TurboActivate.GetExtraData(): WideString;
{$ENDIF}
var
  ret : LongInt;
{$IFDEF MACOS}
  extraData : PAnsiChar;
{$ELSE}
  extraData : PWideChar;
{$ENDIF}
begin
  // get the length of the string we need to allocate
  ret := TurboActivateUnit.TA_GetExtraData(self.handle, nil, 0);

  // make the string
  {$IFDEF MACOS}
    extraData := AnsiStrAlloc(ret);
  {$ELSE} // Windows
    {$IF CompilerVersion >= 20} // for Delphi 2009 +
      extraData := StrAlloc(ret);
    {$ELSE}
      extraData := PWideChar(StrAlloc(ret * 2 + 2));
    {$IFEND}
  {$ENDIF}

  // get the string
  ret := TurboActivateUnit.TA_GetExtraData(self.handle, extraData, ret);

  // free the string if an error happens
  if (ret <> 0) then
  begin
  {$IF CompilerVersion >= 20} // for Delphi 2009 +
    StrDispose(extraData);
  {$ELSE}
    StrDispose(PChar(extraData));
  {$IFEND}
  end;

  case ret of
    TA_E_INVALID_HANDLE:
      raise EInvalidHandleException.Create();
    TA_OK: // success
      {$IFDEF MACOS}
        Result := System.Utf8ToUnicodeString(extraData);
      {$ELSE} // Windows
        Result := extraData;
      {$ENDIF}
    else
      Result := '';
  end;
end;

/// <summary>
/// Gets the value of a feature.
/// </summary>
/// <param name="featureName">The name of the feature to retrieve the value for.</param>
{$IFDEF MACOS}
function TurboActivate.GetFeatureValue(featureName: String): String;
{$ELSE}
function TurboActivate.GetFeatureValue(featureName: WideString): WideString;
{$ENDIF}
var
{$IFDEF MACOS}
  value : UnicodeString;
{$ELSE}
  value : WideString;
{$ENDIF}
begin
  value := GetFeatureValue(featureName, '');

  if (value = '') then begin
     raise ETurboActivateException.Create('Failed to get feature value. The feature doesn''t exist.');
  end;

  Result := value;
end;

/// <summary>
/// Gets the value of a feature.
/// </summary>
/// <param name="featureName">The name of the feature to retrieve the value for.</param>
/// <param name="defaultValue">The default value to return if the feature doesn't exist.</param>
{$IFDEF MACOS}
function TurboActivate.GetFeatureValue(featureName: String; defaultValue: String): String;
{$ELSE}
function TurboActivate.GetFeatureValue(featureName: WideString; defaultValue: WideString): WideString;
{$ENDIF}
var
  ret : LongInt;
{$IFDEF MACOS}
  featValue : PAnsiChar;
{$ELSE}
  featValue : PWideChar;
{$ENDIF}
begin

  {$IFDEF MACOS}
    // get the length of the string we need to allocate
    ret := TurboActivateUnit.TA_GetFeatureValue(self.handle, PAnsiChar(featureName), nil, 0);

    // make the string
    featValue := AnsiStrAlloc(ret);

    // get the string
    ret := TurboActivateUnit.TA_GetFeatureValue(self.handle, PAnsiChar(featureName), featValue, ret);
  {$ELSE} // Windows
    // get the length of the string we need to allocate
    ret := TurboActivateUnit.TA_GetFeatureValue(self.handle, PWideChar(featureName), nil, 0);

    // make the string
    {$IF CompilerVersion >= 20} // for Delphi 2009 +
      featValue := StrAlloc(ret);
    {$ELSE}
      featValue := PWideChar(StrAlloc(ret * 2 + 2));
    {$IFEND}

     // get the string
     ret := TurboActivateUnit.TA_GetFeatureValue(self.handle, PWideChar(featureName), featValue, ret);
  {$ENDIF}


  // free the string if an error happens
  if (ret <> 0) then begin
  {$IF CompilerVersion >= 20} // for Delphi 2009 +
    StrDispose(featValue);
  {$ELSE}
    StrDispose(PChar(featValue));
  {$IFEND}
  end;

  case ret of
    TA_E_INVALID_HANDLE:
      raise EInvalidHandleException.Create();
    TA_OK: // success

      {$IFDEF MACOS}
        Result := System.Utf8ToUnicodeString(featValue);
      {$ELSE} // Windows
        Result := featValue;
      {$ENDIF}
    else
      Result := defaultValue;
  end;
end;

/// <summary>
/// Gets the stored product key. NOTE: if you want to check if a product key is valid simply call IsProductKeyValid().
/// </summary>
{$IFDEF MACOS}
function TurboActivate.GetPKey(): String;
{$ELSE}
function TurboActivate.GetPKey(): WideString;
{$ENDIF}
var
  ret : LongInt;
{$IFDEF MACOS}
  pkey : PAnsiChar;
{$ELSE}
  pkey : PWideChar;
{$ENDIF}
begin

  // make the string
  {$IFDEF MACOS}
    pkey := AnsiStrAlloc(35);
  {$ELSE} // Windows
    {$IF CompilerVersion >= 20} // for Delphi 2009 +
      pkey := StrAlloc(35);
    {$ELSE}
      pkey := PWideChar(StrAlloc(72));
    {$IFEND}
  {$ENDIF}

  // get the string
  ret := TurboActivateUnit.TA_GetPKey(self.handle, pkey, 35);

  // free the string if an error happens
  if (ret <> 0) then begin
  {$IF CompilerVersion >= 20} // for Delphi 2009 +
    StrDispose(pkey);
  {$ELSE}
    StrDispose(PChar(pkey));
  {$IFEND}
  end;

  case ret of
    TA_E_PKEY:
      raise EInvalidProductKeyException.Create();
    TA_E_INVALID_HANDLE:
      raise EInvalidHandleException.Create();
    TA_OK: // success
      {$IFDEF MACOS}
        Result := System.Utf8ToUnicodeString(pkey);
      {$ELSE} // Windows
        Result := pkey;
      {$ENDIF}
    else
      raise ETurboActivateException.Create('Failed to get the product key.');
  end;
end;

/// <summary>
/// Checks whether the computer has been activated.
/// </summary>
/// <returns>True if the computer is activated. False otherwise.</returns>
function TurboActivate.IsActivated(): boolean;
var
  ret : LongInt;
begin
  ret := TurboActivateUnit.TA_IsActivated(self.handle);

  case ret of
    TA_OK: // is activated
        Result := True;
    TA_FAIL: // not activated
        Result := False;
    else
        raise TaHresultToExcep(ret, 'IsActivated');
  end;
end;

/// <summary>
/// Checks if the string in the form "YYYY-MM-DD HH:mm:ss" is a valid date/time. The date must be in UTC time and "24-hour" format. If your date is in some other time format first convert it to UTC time before passing it into this function.
/// </summary>
/// <param name="date_time">The type of date time check. Valid flags are TA_HAS_NOT_EXPIRED.</param>
/// <returns>True if the date is valid, false if it's not</returns>
{$IFDEF MACOS}
function TurboActivate.IsDateValid(date_time: String; flags: LongWord):boolean;
{$ELSE}
function TurboActivate.IsDateValid(date_time: WideString; flags: LongWord):boolean;
{$ENDIF}
var
  ret : LongInt;
begin
  ret := TurboActivateUnit.TA_IsDateValid(self.handle, Addr(date_time[1]), flags);

  case ret of
    TA_OK: // date is valid and not expired
        Result := True;
    TA_FAIL: // date is invalid or not expired
        Result := False;
    else
        raise TaHresultToExcep(ret, 'IsDateValid');
  end;
end;

/// <summary>Checks whether the computer is genuinely activated by verifying with the LimeLM servers.</summary>
/// <returns>IsGenuineResult</returns>
function TurboActivate.IsGenuine(): IsGenuineResult;
var
  ret : LongInt;
begin
  ret := TurboActivateUnit.TA_IsGenuine(self.handle);

  case ret of
    TA_E_INET:
    begin
        Result := InternetError;
        exit;
    end;
    TA_E_IN_VM:
    begin
        Result := NotGenuineInVM;
        exit;
    end;
    TA_E_FEATURES_CHANGED:
    begin
        Result := GenuineFeaturesChanged;
        exit;
    end;
    TA_OK: // is activated
    begin
        Result := Genuine;
        exit;
    end;

    TA_FAIL, TA_E_REVOKED, TA_E_ACTIVATE: // not activated
    begin
        Result := NotGenuine;
        exit;
    end;

    else
    begin
        raise TaHresultToExcep(ret, 'IsGenuine') ;
    end;
  end;
end;


/// <summary>Checks whether the computer is activated, and every "daysBetweenChecks" days it check if the customer is genuinely activated by verifying with the LimeLM servers.</summary>
/// <param name="daysBetweenChecks">How often to contact the LimeLM servers for validation. 90 days recommended.</param>
/// <param name="graceDaysOnInetErr">If the call fails because of an internet error, how long, in days, should the grace period last (before returning deactivating and returning TA_FAIL).
/// 
/// 14 days is recommended.</param>
/// <param name="skipOffline">If the user activated using offline activation 
/// (ActivateRequestToFile(), ActivateFromFile() ), then with this
/// option IsGenuineEx() will still try to validate with the LimeLM
/// servers, however instead of returning <see cref="IsGenuineResult.InternetError"/> (when within the
/// grace period) or <see cref="IsGenuineResult.NotGenuine"/> (when past the grace period) it will
/// instead only return <see cref="IsGenuineResult.Genuine"/> (if IsActivated()).
/// 
/// If the user activated using online activation then this option
/// is ignored.</param>
/// <param name="offlineShowInetErr">If the user activated using offline activation, and you're
/// using this option in tandem with skipOffline, then IsGenuineEx()
/// will return <see cref="IsGenuineResult.InternetError"/> on internet failure instead of <see cref="IsGenuineResult.Genuine"/>.
///
/// If the user activated using online activation then this flag
/// is ignored.</param>
/// <returns>IsGenuineResult</returns>
function TurboActivate.IsGenuine(daysBetweenChecks : LongWord; graceDaysOnInetErr: LongWord; skipOffline: boolean = false; offlineShowInetErr: boolean = false): IsGenuineResult;
var
  ret : LongInt;
  options : GENUINE_OPTIONS;
begin
  options.nLength := SizeOf(GENUINE_OPTIONS);
  options.nDaysBetweenChecks := daysBetweenChecks;
  options.nGraceDaysOnInetErr := graceDaysOnInetErr;

  if skipOffline then begin
    // TA_SKIP_OFFLINE = 1
    options.flags := 1;

    // TA_OFFLINE_SHOW_INET_ERR = 2
    if offlineShowInetErr then options.flags := options.flags or 2;
  end;

  ret := TurboActivateUnit.TA_IsGenuineEx(self.handle, Addr(options));

  case ret of
    TA_E_INET, TA_E_INET_DELAYED:
    begin
        Result := InternetError;
        exit;
    end;
    TA_E_IN_VM:
    begin
        Result := NotGenuineInVM;
        exit;
    end;
    TA_E_FEATURES_CHANGED:
    begin
        Result := GenuineFeaturesChanged;
        exit;
    end;
    TA_OK: // is activated and/or Genuine
    begin
        Result := Genuine;
        exit;
    end;

    TA_FAIL, TA_E_REVOKED, TA_E_ACTIVATE: // not activated
    begin
        Result := NotGenuine;
        exit;
    end;

    else
    begin
        raise TaHresultToExcep(ret, 'IsGenuine') ;
    end;
  end;
end;

/// <summary>Get the number of days until the next time that the <see cref="IsGenuine(uint, uint, bool, bool)"/> function contacts the LimeLM activation servers to reverify the activation.</summary>
/// <param name="daysBetweenChecks">How often to contact the LimeLM servers for validation. Use the exact same value as used in <see cref="IsGenuine(uint, uint, bool, bool)"/>.</param>
/// <param name="graceDaysOnInetErr">If the call fails because of an internet error, how long, in days, should the grace period last (before returning deactivating and returning TA_FAIL). Again, use the exact same value as used in <see cref="IsGenuine(uint, uint, bool, bool)"/>.</param>
/// <param name="inGracePeriod">Get whether the user is in the grace period.</param>
/// <returns>The number of days remaining. 0 days if both the days between checks and the grace period have expired. (E.g. 1 day means *at most* 1 day. That is, it could be 30 seconds.)</returns>
function TurboActivate.GenuineDays(daysBetweenChecks: LongWord; graceDaysOnInetErr: LongWord; var inGracePeriod: boolean): LongWord;
var
  ret : LongInt;
  daysRemain : LongWord;
  inGrace: Byte;
begin
  daysRemain := 0;
  inGrace := 0;
  ret := TurboActivateUnit.TA_GenuineDays(self.handle, daysBetweenChecks, graceDaysOnInetErr, daysRemain, inGrace);

  if (ret <> TA_OK) then begin
    raise TaHresultToExcep(ret, 'GenuineDays');
  end;

  Result := daysRemain;

  if inGrace = 0 then
     inGracePeriod := false
  else
     inGracePeriod := true;
end;

/// <summary>
/// Checks if the product key installed for this product is valid. This does NOT check if the product key is activated or genuine. Use IsActivated() and IsGenuine() instead.
/// </summary>
/// <returns>True if the product key is valid.</returns>
function TurboActivate.IsProductKeyValid(): boolean;
var
  ret : LongInt;
begin
  ret := TurboActivateUnit.TA_IsProductKeyValid(self.handle);

  case ret of
    TA_E_INVALID_HANDLE:
      raise EInvalidHandleException.Create();
    TA_E_ACTIVATE:
      raise ENotActivatedException.Create();
    TA_OK:
    begin
        Result := True;
        exit;
    end;
  end;

  // not valid
  Result := False;
end;

/// <summary>
/// Sets the custom proxy to be used by functions that connect to the internet.
/// </summary>
/// <param name="proxy">The proxy to use. Proxy must be in the form "http://username:password@host:port/".</param>
{$IFDEF MACOS}
procedure TurboActivate.SetCustomProxy(proxy: String);
{$ELSE}
procedure TurboActivate.SetCustomProxy(proxy: WideString);
{$ENDIF}
var
  ret : LongInt;
begin
  ret := TurboActivateUnit.TA_SetCustomProxy(Addr(proxy[1]));

  if (ret <> 0) then begin
      raise ETurboActivateException.Create('Failed to set the custom proxy.');
  end;
end;

/// <summary>
/// Get the number of trial days remaining.
/// </summary>
/// <returns>The number of days remaining. 0 days if the trial has expired. (E.g. 1 day means *at most* 1 day. That is it could be 30 seconds.)</returns>
function TurboActivate.TrialDaysRemaining(useTrialFlags: LongWord): LongWord;
var
  ret : LongInt;
  daysRemain : LongWord;
begin
  daysRemain := 0;
  ret := TurboActivateUnit.TA_TrialDaysRemaining(self.handle, useTrialFlags, daysRemain);

  if (ret <> TA_OK) then begin
    raise TaHresultToExcep(ret, 'TrialDaysRemaining');
  end;

  Result := daysRemain;
end;

/// <summary>
/// Begins the trial the first time it's called. Calling it again will validate the trial data hasn't been tampered with.
/// </summary>
{$IFDEF MACOS}
procedure TurboActivate.UseTrial(flags: LongWord; extraData: String);
{$ELSE}
procedure TurboActivate.UseTrial(flags: LongWord; extraData: WideString);
{$ENDIF}
var
  ret : LongInt;
begin

  if extraData = '' then
    begin
        ret := TurboActivateUnit.TA_UseTrial(self.handle, flags, nil);
    end
  else
    begin
        ret := TurboActivateUnit.TA_UseTrial(self.handle, flags, Addr(extraData[1]));
    end;

  if (ret <> TA_OK) then begin
    raise TaHresultToExcep(ret, 'UseTrial');
  end;
end;

/// <summary>
/// Generate a "verified trial" offline request file. This file will then need to be
/// submitted to LimeLM. You will then need to use the TA_UseTrialVerifiedFromFile()
/// function with the response file from LimeLM to actually start the trial.
/// </summary>
{$IFDEF MACOS}
procedure TurboActivate.UseTrialVerifiedRequest(filename: String; extraData: String);
{$ELSE}
procedure TurboActivate.UseTrialVerifiedRequest(filename: WideString; extraData: WideString);
{$ENDIF}
var
  ret : LongInt;
begin

  if extraData = '' then
    begin
        ret := TurboActivateUnit.TA_UseTrialVerifiedRequest(self.handle, Addr(filename[1]), nil);
    end
  else
    begin
        ret := TurboActivateUnit.TA_UseTrialVerifiedRequest(self.handle, Addr(filename[1]), Addr(extraData[1]));
    end;

  if (ret <> TA_OK) then begin
    raise TaHresultToExcep(ret, 'UseTrialVerifiedRequest');
  end;
end;

/// <summary>
/// Use the "verified trial response" from LimeLM to start the verified trial.
/// </summary>
{$IFDEF MACOS}
procedure TurboActivate.UseTrialVerifiedFromFile(filename: String; flags: LongWord);
{$ELSE}
procedure TurboActivate.UseTrialVerifiedFromFile(filename: WideString; flags: LongWord);
{$ENDIF}
var
  ret : LongInt;
begin
  ret := TurboActivateUnit.TA_UseTrialVerifiedFromFile(self.handle, Addr(filename[1]), flags);

  if (ret <> TA_OK) then begin
    raise TaHresultToExcep(ret, 'UseTrialVerifiedFromFile');
  end;
end;

/// <summary>
/// Extends the trial using a trial extension created in LimeLM.
/// </summary>
/// <param name="trialExtension">The trial extension generated from LimeLM.</param>
{$IFDEF MACOS}
procedure TurboActivate.ExtendTrial(trialExtension: String; useTrialFlags: LongWord);
{$ELSE}
procedure TurboActivate.ExtendTrial(trialExtension: WideString; useTrialFlags: LongWord);
{$ENDIF}
var
  ret : LongInt;
begin
  ret := TurboActivateUnit.TA_ExtendTrial(handle, useTrialFlags, Addr(trialExtension[1]));

  if (ret <> TA_OK) then begin
    raise TaHresultToExcep(ret, 'ExtendTrial');
  end;
end;


// Custom exceptions

constructor ECOMException.Create();
begin
  inherited Create('CoInitializeEx failed. Re-enable Windows Management Instrumentation (WMI) service. Contact your system admin for more information.');
end;

constructor EAccountCanceledException.Create();
begin
  inherited Create('Can''t activate because the LimeLM account is cancelled.');
end;

constructor EPkeyRevokedException.Create();
begin
  inherited Create('The product key has been revoked.');
end;

constructor EPkeyMaxUsedException.Create();
begin
  inherited Create('The product key has already been activated with the maximum number of computers.');
end;

constructor EInternetException.Create();
begin
  inherited Create('Connection to the server failed.');
end;

constructor EInternetException.Create(msg: String);
begin
  inherited Create(msg);
end;

constructor EInternetTimeoutException.Create();
begin
  inherited Create('The connection to the server timed out because a long period of time elapsed since the last data was sent or received.');
end;

constructor EInternetTLSException.Create();
begin
  inherited Create('The secure connection to the activation servers failed due to a TLS or certificate error. More information here: https://wyday.com/limelm/help/faq/#internet-error');
end;

constructor EInvalidProductKeyException.Create();
begin
  inherited Create('The product key is invalid or there''s no product key.');
end;

constructor ENotActivatedException.Create();
begin
  inherited Create('The product needs to be activated.');
end;

constructor EProductDetailsException.Create();
begin
  inherited Create('The product details file "TurboActivate.dat" failed to load. It''s either missing or corrupt.');
end;

constructor EInvalidHandleException.Create();
begin
  inherited Create('The handle is not valid. You must set the VersionGUID property.');
end;

constructor ETrialExtUsedException.Create();
begin
  inherited Create('The trial extension has already been used.');
end;

constructor ETrialDateCorruptedException.Create();
begin
  inherited Create('The trial data has been corrupted, using the oldest date possible.');
end;

constructor ETrialExtExpiredException.Create();
begin
  inherited Create('The trial extension has expired.');
end;

constructor EDateTimeException.Create();
begin
  inherited Create('Failed because your system date and time settings are incorrect. Fix your date and time settings, restart your computer, and try to activate again.');
end;

constructor EPermissionException.Create();
begin
  inherited Create('Insufficient system permission. Either start your process as an admin / elevated user or call the function again with the TA_USER flag.');
end;

constructor EInvalidFlagsException.Create();
begin
  inherited Create('The flags you passed to the function were invalid (or missing). Flags like "TA_SYSTEM" and "TA_USER" are mutually exclusive -- you can only use one or the other.');
end;

constructor EVirtualMachineException.Create();
begin
  inherited Create('The function failed because this instance of your program is running inside a virtual machine / hypervisor and you''ve prevented the function from running inside a VM.');
end;

constructor EExtraDataTooLongException.Create();
begin
  inherited Create('The "extra data" was too long. You''re limited to 255 UTF-8 characters. Or, on Windows, a Unicode string that will convert into 255 UTF-8 characters or less.');
end;

constructor EInvalidArgsException.Create();
begin
  inherited Create('The arguments passed to the function are invalid. Double check your logic.');
end;

constructor ETurboFloatKeyException.Create();
begin
  inherited Create('The product key used is for TurboFloat, not TurboActivate.');
end;

constructor ENoMoreDeactivationsException.Create();
begin
  inherited Create('No more deactivations are allowed for the product key. This product is still activated on this computer.');
end;

constructor EEnableNetworkAdaptersException.Create();
begin
  inherited Create('There are network adapters on the system that are disabled and TurboActivate couldn''t read their hardware properties (even after trying and failing to enable the adapters automatically).' + ' Enable the network adapters, re-run the function, and TurboActivate will be able to "remember" the adapters even if the adapters are disabled in the future.');
end;

constructor EAlreadyActivatedException.Create();
begin
  inherited Create('You can''t use a product key because your app is already activated with a product key. To use a new product key, then first deactivate using either the Deactivate() or DeactivationRequestToFile().');
end;

constructor EAlreadyVerifiedTrialException.Create();
begin
  inherited Create('The trial is already a verified trial. You need to use the "TA_VERIFIED_TRIAL" flag. Can''t "downgrade" a verified trial to an unverified trial.');
end;

constructor ETrialExpiredException.Create();
begin
  inherited Create('The verified trial has expired. You must request a trial extension from the company.');
end;

constructor ENoMoreTrialsAllowedException.Create();
begin
  inherited Create('In the LimeLM account either the trial days is set to 0, OR the account is set to not auto-upgrade and thus no more verified trials can be made.');
end;

constructor EMustSpecifyTrialTypeException.Create();
begin
  inherited Create('You must specify the trial type (TA_UNVERIFIED_TRIAL or TA_VERIFIED_TRIAL). And you can''t use both flags. Choose one or the other. We recommend TA_VERIFIED_TRIAL.');
end;

constructor EMustUseTrialException.Create();
begin
  inherited Create('You must call TA_UseTrial() before you can get the number of trial days remaining.');
end;

constructor EBrokenWMIException.Create();
begin
  inherited Create('The WMI repository on the computer is broken. To fix the WMI repository see the instructions here: https://wyday.com/limelm/help/faq/#fix-broken-wmi');
end;

end. //unit TurboActivateUnit