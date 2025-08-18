unit TrialExtension;

interface

uses
  Windows, Messages, SysUtils, Variants, Classes, Graphics, Controls, Forms,
  Dialogs, StdCtrls, TurboActivateUnit;

type
  TfrmTrialExtension = class(TForm)
    btnOK: TButton;
    btnCancel: TButton;
    Label1: TLabel;
    txtExtension: TMemo;
    procedure btnOKClick(Sender: TObject);
    procedure btnCancelClick(Sender: TObject);
  private
      ta : TurboActivate;
      trialFlags: LongWord;
  public
      constructor Create(AOwner: TComponent; turboAct: TurboActivate; useTrialFlags: LongWord); reintroduce;
  end;

var
  frmTrialExtension: TfrmTrialExtension;


implementation

{$R *.dfm}

constructor TfrmTrialExtension.Create(AOwner: TComponent; turboAct: TurboActivate; useTrialFlags: LongWord);
begin
  inherited Create(AOwner);
  self.ta := turboAct;
  self.trialFlags := useTrialFlags;
end;


procedure TfrmTrialExtension.btnOKClick(Sender: TObject);
begin
  Try
    // try to extend the trial and close the form
    ta.ExtendTrial(txtExtension.Text, trialFlags);
    ModalResult := mrOK;
  except
    on E : Exception do begin
      ShowMessage(E.Message);
      txtExtension.SetFocus;
    end;
  end;
end;

procedure TfrmTrialExtension.btnCancelClick(Sender: TObject);
begin
    ModalResult := mrCancel;
end;

end.
