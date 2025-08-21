unit frmMain;

interface

uses
  System.SysUtils, System.Types, System.UITypes, System.Classes, System.Variants,
  FMX.Types, FMX.Controls, FMX.Forms, FMX.Graphics, FMX.Dialogs, FMX.Menus,
  FMX.Controls.Presentation, FMX.ScrollBox, FMX.Memo, FMX.StdCtrls,
  TurboActivateUnit, TrialExtension, ReVerifyNow, PKey;

type
  TForm1 = class(TForm)
    MainMenu1: TMainMenu;
    MenuItem1: TMenuItem;
    MenuItem2: TMenuItem;
    MenuItem3: TMenuItem;
    MenuItem4: TMenuItem;
    mnuActDeact: TMenuItem;
    txtMain: TMemo;
    lblTrialMessage: TLabel;
    btnExtendTrial: TButton;
    procedure mnuActDeactClick(Sender: TObject);
    procedure btnExtendTrialClick(Sender: TObject);
    procedure FormCreate(Sender: TObject);
  private
    procedure ShowActivateMessage(show: boolean);
    procedure ShowTrial(show: boolean);
    procedure DisableAppFeatures();
    procedure ReEnableAppFeatures();
  public
    { Public declarations }
  end;

var
  Form1: TForm1;
  isGenuine : Boolean;
  ta : TurboActivate;
  trialFlags: LongWord;
  DaysBetweenChecks: LongWord;
  GracePeriodLength: LongWord;

implementation

{$R *.fmx}

procedure TForm1.FormCreate(Sender: TObject);
var
  gr : IsGenuineResult;
  frmReverify : TfrmReVerifyNow;

  //featureValue : String;
begin
   txtMain.Text := 'This is a simple Text Editor app that demonstrates how to use TurboActivate in your application.' + sLineBreak + sLineBreak + 'The one "feature" of this app is this text editor. This will be disabled when the user is not activated and the trial is expired. All other times this text box will be enabled.';


   // Set the trial flags you want to use. Here we've selected that the
   // trial data should be stored system-wide (TA_SYSTEM) and that we should
   // use un-resetable verified trials (TA_VERIFIED_TRIAL).
   trialFlags := TA_USER or TA_VERIFIED_TRIAL;

   // Don't use 0 for either of these values.
   // We recommend 90, 14. But if you want to lower the values
   // we don't recommend going below 7 days for each value.
   // Anything lower and you're just punishing legit users.
   DaysBetweenChecks := 90;
   GracePeriodLength := 14;


   Try
       //TODO: goto the version page at LimeLM and paste this GUID here
       ta := TurboActivate.Create('17738358944b7a7316ec5fe9.23132283');

       // Check if we're activated, and every 90 days verify it with the activation servers
       // In this example we won't show an error if the activation was done offline
       // (see the 3rd parameter of the IsGenuine() function) -- http://wyday.com/limelm/help/offline-activation/
       gr := ta.IsGenuine(DaysBetweenChecks, GracePeriodLength, true);

       isGenuine := (gr = Genuine)
                     or (gr = GenuineFeaturesChanged)

                     // an internet error means the user is activated but
                     // TurboActivate failed to contact the LimeLM servers
                     or (gr = InternetError);


       // If IsGenuineEx() is telling us we're not activated
       // but the IsActivated() function is telling us that the activation
       // data on the computer is valid (i.e. the crypto-signed-fingerprint matches the computer)
       // then that means that the customer has passed the grace period and they must re-verify
       // with the servers to continue to use your app.

       //Note: DO NOT allow the customer to just continue to use your app indefinitely with absolutely
       //      no reverification with the servers. If you want to do that then don't use IsGenuine() or
       //      IsGenuineEx() at all -- just use IsActivated().
       if (not isGenuine) And ta.IsActivated then
       begin
           // We're treating the customer as is if they aren't activated, so they can't use your app.

           // However, we show them a dialog where they can reverify with the servers immediately.
           frmReverify := TfrmReVerifyNow.Create(nil, ta, DaysBetweenChecks, GracePeriodLength);

           if frmReverify.ShowModal = mrOk then begin
              isGenuine := true;
           end
           else if (not frmReverify.noLongerActivated) then begin // the user clicked cancel and the user is still activated
              // Just bail out of your app
              Application.Terminate;
              exit;
           end;
       end;
   except
     on E : ETurboActivateException do
     begin
       ShowMessage('Failed to check if activated: ' + E.Message);

       // Exit the app, and exit the function immediately
       Application.Terminate;
       exit;
     end;
   end;

   ShowTrial(not isGenuine);


   // If this app is activated then you can get custom license fields.
   // See: https://wyday.com/limelm/help/license-features/

   //if isGenuine then
   //begin
   //    // read in a custom license field named "update_expires"
   //    featureValue := ta.GetFeatureValue('update_expires', '');

   //    // if the date has passed then kill the app immediately
   //    if (featureValue = '') Or (not ta.IsDateValid(featureValue, TA_HAS_NOT_EXPIRED)) then begin
   //       ShowMessage('Your subscription has expired. Buy a renewal.');

   //       // Exit the app, and exit the function immediately
   //       Application.Terminate;
   //       exit;
   //    end;
   //end;
end;



procedure TForm1.mnuActDeactClick(Sender: TObject);
var
  frmPkey : TfrmPKey;
begin
  if isGenuine then
  begin
    // deactivate product without deleting the product key
    // allows the user to easily reactivate
    ta.Deactivate(false);
    isGenuine := false;
    ShowTrial(True);
  end
  else // this app isn't activated - launch TurboActivate and wait for it to exit
  begin

     // use a simple activation interface
     frmPkey := TfrmPKey.Create(nil, ta, TA_SYSTEM);

     // recheck if activated
     if (frmPkey.ShowModal = mrOk) And (ta.IsActivated()) then begin
        ShowActivateMessage(false);
        mnuActDeact.Text := 'Deactivate';
        isGenuine := true;
     end;
  end;
end;

procedure TForm1.ShowActivateMessage(show: boolean);
begin
  //TODO: disable all the features of the program
  txtMain.Enabled := not show;

  //TODO: show the "Activate now" message
  lblTrialMessage.Visible := show;
  btnExtendTrial.Visible := show;
end;

procedure TForm1.ShowTrial(show: boolean);
var
  trialDaysRemaining : LongWord;
begin
  lblTrialMessage.Visible := show;
  btnExtendTrial.Visible := show;

  if show then
  begin
    mnuActDeact.Text := 'Activate';

    trialDaysRemaining := 0;
    Try
        ta.UseTrial(trialFlags);

        // get the number of remaining trial days
        trialDaysRemaining := ta.TrialDaysRemaining(trialFlags);
    except
     on E : ETurboActivateException do
     begin
       ShowMessage('Failed to start the trial: ' + E.Message);
     end;
    end;

    // if no more trial days then disable all app features
    if trialDaysRemaining = 0 then
       DisableAppFeatures()
    else
       lblTrialMessage.Text := 'Your trial expires in ' + IntToStr(trialDaysRemaining) + ' days.';
  end
  else
    mnuActDeact.Text := 'Deactivate'
end;

procedure TForm1.DisableAppFeatures();
begin
  //TODO: disable all the features of the program
  txtMain.Enabled := False;

  lblTrialMessage.Text := 'The trial has expired. Get an extension at Example.com';
end;

procedure TForm1.ReEnableAppFeatures();
begin
  //TODO: re-enable all the features of the program
  txtMain.Enabled := True;
end;

procedure TForm1.btnExtendTrialClick(Sender: TObject);
var
  trialExt : TfrmTrialExtension;
  trialDaysRemaining : LongWord;
begin
  trialExt := TfrmTrialExtension.Create(nil, ta, trialFlags);
  trialDaysRemaining := 0;

  if trialExt.ShowModal = mrOk then begin
    Try
      // get the number of remaining trial days
      trialDaysRemaining := ta.TrialDaysRemaining(trialFlags);
    except
     on E : ETurboActivateException do
     begin
       ShowMessage('Failed to get the trial days remaining: ' + E.Message);
     end;
    end;

    // if more trial days then re-enable all app features
    if trialDaysRemaining > 0 then begin
       ReEnableAppFeatures();
       lblTrialMessage.Text := 'Your trial expires in ' + IntToStr(trialDaysRemaining) + ' days.';
    end;
  end;

  trialExt.Release;
end;

end.
