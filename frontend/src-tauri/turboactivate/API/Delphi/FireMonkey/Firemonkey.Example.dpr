program Firemonkey.Example;

uses
  System.StartUpCopy,
  FMX.Forms,
  frmMain in 'frmMain.pas' {Form1},
  TurboActivateUnit in '..\TurboActivateUnit.pas',
  ReVerifyNow in 'ReVerifyNow.pas' {frmReVerifyNow},
  TrialExtension in 'TrialExtension.pas' {frmTrialExtension},
  PKey in 'PKey.pas' {frmPKey};

{$R *.res}

begin
  Application.Initialize;
  Application.CreateForm(TForm1, Form1);
  Application.CreateForm(TfrmPKey, frmPKey);
  //  Application.CreateForm(TfrmReVerifyNow, frmReVerifyNow);
//  Application.CreateForm(TfrmTrialExtension, frmTrialExtension);
  Application.Run;
end.
