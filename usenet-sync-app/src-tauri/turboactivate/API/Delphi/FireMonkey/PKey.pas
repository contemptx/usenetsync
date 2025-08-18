unit PKey;

interface

uses
  System.SysUtils, System.Types, System.UITypes, System.Classes, System.Variants,
  FMX.Types, FMX.Controls, FMX.Forms, FMX.Graphics, FMX.Dialogs,
  FMX.Controls.Presentation, FMX.StdCtrls, FMX.Edit, TurboActivateUnit;

type
  TfrmPKey = class(TForm)
    Label1: TLabel;
    txtPKey: TEdit;
    btnActivate: TButton;
    btnCancel: TButton;
    procedure btnCancelClick(Sender: TObject);
    procedure btnActivateClick(Sender: TObject);
  private
      ta : TurboActivate;
      pkeyFlags: LongWord;
  public
    constructor Create(AOwner: TComponent; turboAct: TurboActivate; usePkeyFlags: LongWord); reintroduce;
  end;

var
  frmPKey: TfrmPKey;

implementation

{$R *.fmx}

constructor TfrmPKey.Create(AOwner: TComponent; turboAct: TurboActivate; usePkeyFlags: LongWord);
begin
  inherited Create(AOwner);
  self.ta := turboAct;
  self.pkeyFlags := usePkeyFlags;

  Try
    // get the existing product key
    txtPKey.Text := ta.GetPKey();
  except
    on E : Exception do begin
    end;
  end;
end;

procedure TfrmPKey.btnActivateClick(Sender: TObject);
begin
  Try
    // try to extend the trial and close the form
    ta.CheckAndSavePKey(txtPKey.Text, pkeyFlags);

    ta.Activate();

    ModalResult := mrOK;
  except
    on E : Exception do begin
      ShowMessage('Activation failed: ' + E.Message);
      txtPKey.SetFocus;
    end;
  end;
end;

procedure TfrmPKey.btnCancelClick(Sender: TObject);
begin
    ModalResult := mrCancel;
end;

end.
