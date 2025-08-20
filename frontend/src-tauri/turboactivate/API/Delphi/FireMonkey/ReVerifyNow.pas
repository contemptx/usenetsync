unit ReVerifyNow;

interface

uses
  System.SysUtils, System.Types, System.UITypes, System.Classes, System.Variants,
  FMX.Types, FMX.Controls, FMX.Forms, FMX.Graphics, FMX.Dialogs,
  TurboActivateUnit, FMX.Controls.Presentation, FMX.StdCtrls;

type
  TfrmReVerifyNow = class(TForm)
    lblDescr: TLabel;
    btnReverify: TButton;
    btnExit: TButton;
    procedure btnReverifyClick(Sender: TObject);
    procedure btnExitClick(Sender: TObject);
  private
      ta : TurboActivate;
      inGrace : Boolean;
  public
      GenuineDaysLeft : LongWord;
      noLongerActivated : Boolean;

      constructor Create(AOwner: TComponent; turboAct: TurboActivate; DaysBetweenChecks: LongWord; GracePeriodLength: LongWord); reintroduce;
  end;

var
  frmReVerifyNow: TfrmReVerifyNow;

implementation

{$R *.fmx}

constructor TfrmReVerifyNow.Create(AOwner: TComponent; turboAct: TurboActivate; DaysBetweenChecks: LongWord; GracePeriodLength: LongWord);
begin
  inherited Create(AOwner);
  self.ta := turboAct;

  // Use the days between checks and grace period from
  // the main form
  GenuineDaysLeft := ta.GenuineDays(DaysBetweenChecks, GracePeriodLength, inGrace);

  if GenuineDaysLeft = 0 then
  begin
      lblDescr.Text := 'You must re-verify with the activation servers to continue using this app.';
  end
  else begin
      lblDescr.Text := 'You have ' + IntToStr(GenuineDaysLeft) + ' days to re-verify with the activation servers.';
  end;
end;


procedure TfrmReVerifyNow.btnReverifyClick(Sender: TObject);
begin
  Try
    case ta.IsGenuine() of
      Genuine, GenuineFeaturesChanged:
      begin
          ModalResult := mrOK;
          exit;
      end;

      NotGenuine, NotGenuineInVM:
      begin
          noLongerActivated := true;
          ModalResult := mrCancel;
          exit;
      end;

      InternetError:
      begin
          ShowMessage('Failed to connect with the activations servers.');
          exit;
      end;
    end;
  except
    on E : Exception do begin
      ShowMessage('Failed to re-verify with the activations servers. Full error: ' + E.Message);
    end;
  end;
end;

procedure TfrmReVerifyNow.btnExitClick(Sender: TObject);
begin
    ModalResult := mrCancel;
end;

end.
