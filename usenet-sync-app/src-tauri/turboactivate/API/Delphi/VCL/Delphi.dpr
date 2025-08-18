program Delphi;

uses
  Forms,
  frmMain in 'frmMain.pas' {Form1},
  TrialExtension in 'TrialExtension.pas' {frmTrialExtension},
  ReVerifyNow in 'ReVerifyNow.pas' {frmReVerifyNow},
  TurboActivateUnit in '..\TurboActivateUnit.pas';

{$R *.res}

begin
  Application.Initialize;
  Application.CreateForm(TForm1, Form1);
  Application.CreateForm(TfrmTrialExtension, frmTrialExtension);
  Application.CreateForm(TfrmReVerifyNow, frmReVerifyNow);
  Application.Run;
end.
