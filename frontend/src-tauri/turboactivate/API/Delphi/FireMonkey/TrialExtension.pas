unit TrialExtension;

interface

uses
  System.SysUtils, System.Types, System.UITypes, System.Classes, System.Variants,
  FMX.Types, FMX.Controls, FMX.Forms, FMX.Graphics, FMX.Dialogs,
  TurboActivateUnit, FMX.StdCtrls, FMX.ScrollBox, FMX.Memo,
  FMX.Controls.Presentation;

type
  TfrmTrialExtension = class(TForm)
    Label1: TLabel;
    txtExtension: TMemo;
    btnOK: TButton;
    btnCancel: TButton;
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

{$R *.fmx}

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
