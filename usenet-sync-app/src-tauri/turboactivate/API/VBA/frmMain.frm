VERSION 5.00
Begin {C62A69F0-16DC-11CE-9E98-00AA00574A4F} frmMain 
   Caption         =   "Text Editor Plus"
   ClientHeight    =   3612
   ClientLeft      =   108
   ClientTop       =   456
   ClientWidth     =   6384
   OleObjectBlob   =   "frmMain.frx":0000
   StartUpPosition =   1  'CenterOwner
End
Attribute VB_Name = "frmMain"
Attribute VB_GlobalNameSpace = False
Attribute VB_Creatable = False
Attribute VB_PredeclaredId = True
Attribute VB_Exposed = False
' store the isGenuine result
' You don't need to do this -- you can simply
' Call TurboActivate.IsActivated() if you would rather
' do that.
Dim IsGenuine As Boolean


Dim trialFlags As Long

Dim DaysBetweenChecks As Long
Dim GracePeriodLength As Long

' define the TurboActivate instance ("ta")
Public ta As TurboActivate

Private Sub UserForm_Initialize()
    ' Set the trial flags you want to use. Here we've selected that the
    ' trial data should be stored system-wide (TA_SYSTEM) and that we should
    ' use un-resetable verified trials (TA_VERIFIED_TRIAL).
    trialFlags = TA_SYSTEM Or TA_VERIFIED_TRIAL

    ' Don't use 0 for either of these values.
    ' We recommend 90, 14. But if you want to lower the values
    ' we don't recommend going below 7 days for each value.
    ' Anything lower and you're just punishing legit users.
    DaysBetweenChecks = 90
    GracePeriodLength = 14


    ' create the new TurboFloat instance
    Set ta = New TurboActivate

    ' tell your app to handle errors in the section
    ' at the end of the sub
    On Error GoTo TAProcError

    'TODO: goto the version page at LimeLM and paste this GUID here
    Call ta.Init("18324776654b3946fc44a5f3.49025204")

    Dim gr As IsGenuineResult

    ' Check if we're activated, and every 90 days verify it with the activation servers
    ' In this example we won't show an error if the activation was done offline
    ' (see the 3rd parameter of the IsGenuine() function)
    ' https://wyday.com/limelm/help/offline-activation/
    gr = ta.IsGenuineEx(DaysBetweenChecks, GracePeriodLength, True)

    IsGenuine = gr = IsGenuineResult.Genuine Or _
                gr = IsGenuineResult.GenuineFeaturesChanged Or _
                gr = IsGenuineResult.InternetError


    ' If IsGenuineEx() is telling us we're not activated
    ' but the IsActivated() function is telling us that the activation
    ' data on the computer is valid (i.e. the crypto-signed-fingerprint matches the computer)
    ' then that means that the customer has passed the grace period and they must re-verify
    ' with the servers to continue to use your app.

    'Note: DO NOT allow the customer to just continue to use your app indefinitely with absolutely
    '      no reverification with the servers. If you want to do that then don't use IsGenuine() or
    '      IsGenuineEx() at all -- just use IsActivated().
    If Not IsGenuine And ta.IsActivated Then
        ' We're treating the customer as is if they aren't activated, so they can't use your app.

        ' However, we show them a dialog where they can reverify with the servers immediately.

        Dim frmReverify As frmReVerifyNow
        Set frmReverify = New frmReVerifyNow

        If frmReverify.ShowDialog(ta, DaysBetweenChecks, GracePeriodLength) = vbOK Then
            IsGenuine = True
        ElseIf Not frmReverify.noLongerActivated Then ' the user clicked cancel and the user is still activated
            ' Just bail out of your app
            End
            Exit Sub
        End If
    End If

    ShowTrial (Not IsGenuine)

    ' if this app is activated then you can get a feature value
    ' See: https://wyday.com/limelm/help/license-features/
    'If isGenuine Then
    '    Dim featureValue As String = ta.GetFeatureValue("your feature name")

    '    'TODO: do something with the featureValue
    'End If

ProcExit:
    Exit Sub

TAProcError:
    MsgBox "Failed to check if activated: " & Err.Description

    ' End your application immediately
    End
End Sub



Private Sub btnActDeact_Click()
    If IsGenuine Then
        ' tell your app to handle errors in the section
        ' at the end of the sub
        On Error GoTo TAProcError


        'deactivate product without deleting the product key
        'allows the user to easily reactivate
        ta.Deactivate
        IsGenuine = False
        Call ShowTrial(True)
    Else
        ' tell your app to handle errors in the section
        ' at the end of the sub
        On Error GoTo TAProcIsActError

        ' launch the product key form
        Dim pkeyBox As frmPKey
        Set pkeyBox = New frmPKey

        Dim diagResult As VbMsgBoxResult
        diagResult = pkeyBox.ShowDialog(ta)

        If diagResult = vbOK And ta.IsActivated Then
            IsGenuine = True
            ReEnableAppFeatures
            Call ShowTrial(False)
        End If
    End If

ProcExit:
    Exit Sub

TAProcError:
    MsgBox "Failed to deactivate: " & Err.Description
    Resume ProcExit

TAProcIsActError:
    MsgBox "Failed to check if activated: " & Err.Description
    Resume ProcExit
End Sub

''' <summary>Put this app in either trial mode or "full mode"</summary>
''' <param name="show">If true show the trial, otherwise hide the trial.</param>
Private Sub ShowTrial(ByVal show As Boolean)
    lblTrialMessage.Visible = show
    btnExtendTrial.Visible = show

    If show Then
        btnActDeact.Caption = "Activate..."

        Dim TrialDaysRemaining As Long
        TrialDaysRemaining = 0

        ' ignore errors for the following 2 functions
        On Error Resume Next

        Call ta.UseTrial(trialFlags)

        ' get the number of remaining trial days
        TrialDaysRemaining = ta.TrialDaysRemaining(trialFlags)

        ' re-enable error handling
        On Error GoTo 0

        ' if no more trial days then disable all app features
        If TrialDaysRemaining = 0 Then
            DisableAppFeatures
        Else
            lblTrialMessage.Caption = "Your trial expires in " & TrialDaysRemaining & " days."
        End If
    Else
        btnActDeact.Caption = "Deactivate"
    End If
End Sub

''' <summary>Change this function to disable the features of your app.</summary>
Private Sub DisableAppFeatures()
    'TODO: disable all the features of the program
    txtMain.Enabled = False

    lblTrialMessage.Caption = "The trial has expired. Get an extension at Example.com"
End Sub

''' <summary>Change this function to re-enable the features of your app.</summary>
Private Sub ReEnableAppFeatures()
    'TODO: re-enable all the features of the program
    txtMain.Enabled = True
End Sub

Private Sub btnExtendTrial_Click()
    Dim trialExt As frmTrialExtension
    Set trialExt = New frmTrialExtension

    Dim diagResult As VbMsgBoxResult
    diagResult = trialExt.ShowDialog(ta, trialFlags)

    If diagResult = vbOK Then

        ' get the number of remaining trial days
        Dim TrialDaysRemaining As Long
        TrialDaysRemaining = 0

        ' ignore errors for ta.TrialDaysRemaining
        On Error Resume Next
        TrialDaysRemaining = ta.TrialDaysRemaining(trialFlags)

        ' re-enable error handling
        On Error GoTo 0


        ' if more trial days then re-enable all app features
        If TrialDaysRemaining > 0 Then
            ReEnableAppFeatures
            lblTrialMessage.Caption = "Your trial expires in " & TrialDaysRemaining & " days."
        End If
    End If
End Sub
