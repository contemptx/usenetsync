Imports System.IO
Imports wyDay.TurboActivate

Public Class Form1

    Private ta As TurboActivate
    Private isGenuine As Boolean

    ' Set the trial flags you want to use. Here we've selected that the
    ' trial data should be stored system-wide (TA_SYSTEM) and that we should
    ' use un-resetable verified trials (TA_VERIFIED_TRIAL).
    Private trialFlags As TA_Flags = TA_Flags.TA_SYSTEM Or TA_Flags.TA_VERIFIED_TRIAL

    ' Don't use 0 for either of these values.
    ' We recommend 90, 14. But if you want to lower the values
    ' we don't recommend going below 7 days for each value.
    ' Anything lower and you're just punishing legit users.
    Private Const DaysBetweenChecks As UInteger = 90
    Private Const GracePeriodLength As UInteger = 14

    Public Sub New()
        InitializeComponent()

        Try
            'TODO: goto the version page at LimeLM and paste this GUID here
            ta = New TurboActivate("18324776654b3946fc44a5f3.49025204")

            ' set the trial changed handler
            AddHandler ta.TrialChange, AddressOf TurboActivate_TrialChange

            ' Check if we're activated, and every 90 days verify it with the activation servers
            ' In this example we won't show an error if the activation was done offline
            ' (see the 3rd parameter of the IsGenuine() function)
            ' https://wyday.com/limelm/help/offline-activation/
            Dim gr As IsGenuineResult = ta.IsGenuine(DaysBetweenChecks, GracePeriodLength, True)

            isGenuine = (gr = IsGenuineResult.Genuine _
                         OrElse gr = IsGenuineResult.GenuineFeaturesChanged _
                         OrElse gr = IsGenuineResult.InternetError)
                         ' an internet error means the user is activated but
                         ' TurboActivate failed to contact the LimeLM servers



            ' If IsGenuineEx() is telling us we're not activated
            ' but the IsActivated() function is telling us that the activation
            ' data on the computer is valid (i.e. the crypto-signed-fingerprint matches the computer)
            ' then that means that the customer has passed the grace period and they must re-verify
            ' with the servers to continue to use your app.

            'Note: DO NOT allow the customer to just continue to use your app indefinitely with absolutely
            '      no reverification with the servers. If you want to do that then don't use IsGenuine() or
            '      IsGenuineEx() at all -- just use IsActivated().
			If Not isGenuine AndAlso ta.IsActivated() Then

                ' We're treating the customer as is if they aren't activated, so they can't use your app.

                ' However, we show them a dialog where they can reverify with the servers immediately.

				Dim frmReverify As ReVerifyNow = New ReVerifyNow(ta, DaysBetweenChecks, GracePeriodLength)

				If frmReverify.ShowDialog(Me) = DialogResult.OK Then
					isGenuine = True
				Else If Not frmReverify.noLongerActivated Then ' the user clicked cancel and the user is still activated

                    ' Just bail out of your app
                    Environment.Exit(1)
                    Return
				End If
			End If

        Catch ex As TurboActivateException
            ' failed to check if activated, meaning the customer screwed
            ' something up so kill the app immediately
            MessageBox.Show("Failed to check if activated: " + ex.Message)
            Environment.Exit(1)
            Return
        End Try

        ShowTrial(Not isGenuine)

        ' If this app is activated then you can get custom license fields.
        ' See: https://wyday.com/limelm/help/license-features/
        'If isGenuine Then
        '    Dim featureValue As String = ta.GetFeatureValue("your feature name")

        '    'TODO: do something with the featureValue
        'End If
    End Sub

    Private Sub mnuActDeact_Click(ByVal sender As System.Object, ByVal e As System.EventArgs) Handles mnuActDeact.Click
        If isGenuine Then
            ' deactivate product without deleting the product key
            ' allows the user to easily reactivate
            Try
                ta.Deactivate(False)
            Catch ex As TurboActivateException
                MessageBox.Show("Failed to deactivate: " + ex.Message)
                Return
            End Try

            isGenuine = False
            ShowTrial(True)
        Else
            'Note: you can launch the TurboActivate wizard or you can create you own interface

            'launch TurboActivate.exe to get the product key from the user
            Dim TAProcess As New Process
            TAProcess.StartInfo.FileName = Path.Combine(Path.GetDirectoryName(Application.ExecutablePath), "TurboActivate.exe")
            TAProcess.EnableRaisingEvents = True

            AddHandler TAProcess.Exited, New EventHandler(AddressOf p_Exited)
            TAProcess.Start()
        End If

    End Sub

    ''' <summary>This event handler is called when TurboActivate.exe closes.</summary>
    Private Sub p_Exited(ByVal sender As Object, ByVal e As EventArgs)

        ' remove the event
        RemoveHandler DirectCast(sender, Process).Exited, New EventHandler(AddressOf p_Exited)

        ' the UI thread is running asynchronous to TurboActivate closing
        ' that's why we can't call TAIsActivated(); directly
        Invoke(New IsActivatedDelegate(AddressOf CheckIfActivated))
    End Sub

    Private Delegate Sub IsActivatedDelegate()

    ''' <summary>Rechecks if we're activated -- if so enable the app features.</summary>
    Private Sub CheckIfActivated()
        ' recheck if activated
        Dim isNowActivated As Boolean = False

        Try
            isNowActivated = ta.IsActivated
        Catch ex As TurboActivateException
            MessageBox.Show("Failed to check if activated: " + ex.Message)
            Exit Sub
        End Try

        If isNowActivated Then
            isGenuine = True
            ReEnableAppFeatures()
            ShowTrial(False)
        Else ' maybe the user entered a trial extension
            RecheckTrialLength()
        End If
    End Sub

    ''' <summary>Put this app in either trial mode or "full mode"</summary>
    ''' <param name="show">If true show the trial, otherwise hide the trial.</param>
    Private Sub ShowTrial(ByVal show As Boolean)
        lblTrialMessage.Visible = show
        btnExtendTrial.Visible = show

        mnuActDeact.Text = (If(show, "Activate...", "Deactivate"))

        If show Then
            Dim trialDaysRemaining As UInteger = 0UI

            Try
                ta.UseTrial(trialFlags)

                ' get the number of remaining trial days
                trialDaysRemaining = ta.TrialDaysRemaining(trialFlags)
            Catch ex2 As TrialExpiredException
                ' do nothing because trialDaysRemaining is already set to 0

            Catch ex As TurboActivateException
                MessageBox.Show("Failed to start the trial: " + ex.Message)
            End Try

            ' if no more trial days then disable all app features
            If trialDaysRemaining = 0 Then
                DisableAppFeatures(False)
            Else
                lblTrialMessage.Text = "Your trial expires in " & trialDaysRemaining & " days."
            End If
        End If
    End Sub

    ''' <summary>Change this function to disable the features of your app.</summary>
    ''' <param name="timeFraudFlag">true if the trial has expired due to date/time fraud.</param>
    Private Sub DisableAppFeatures(ByVal timeFraudFlag As Boolean)
        'TODO: disable all the features of the program
        txtMain.Enabled = False

        If Not timeFraudFlag Then
            lblTrialMessage.Text = "The trial has expired. Get an extension at Example.com"
        Else
            lblTrialMessage.Text = "The trial has expired due to date/time fraud detected"
        End If
    End Sub

    ''' <summary>Change this function to re-enable the features of your app.</summary>
    Private Sub ReEnableAppFeatures()
        'TODO: re-enable all the features of the program
        txtMain.Enabled = True
    End Sub

    Private Sub RecheckTrialLength()
        ' get the number of remaining trial days
        Dim trialDaysRemaining As UInteger = 0UI

        Try
            trialDaysRemaining = ta.TrialDaysRemaining(trialFlags)
        Catch ex As TurboActivateException
            MessageBox.Show("Failed to get the trial days remaining: " + ex.Message)
        End Try

        ' if more trial days then re-enable all app features
        If trialDaysRemaining > 0 Then
            ReEnableAppFeatures()
            lblTrialMessage.Text = "Your trial expires in " & trialDaysRemaining & " days."
        End If
    End Sub

    Private Sub btnExtendTrial_Click(sender As System.Object, e As System.EventArgs) Handles btnExtendTrial.Click
        Dim trialExt As New TrialExtension(ta, trialFlags)

        If trialExt.ShowDialog(Me) = Windows.Forms.DialogResult.OK Then
            RecheckTrialLength()
        End If
    End Sub

    Private Sub TurboActivate_TrialChange(sender As Object, e As StatusArgs)
        DisableAppFeatures(e.Status = TA_TrialStatus.TA_CB_EXPIRED_FRAUD)
    End Sub
End Class
