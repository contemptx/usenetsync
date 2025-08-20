Imports wyDay.TurboActivate

Public Class TrialExtension

    Private ta As TurboActivate
    Private trialFlags As TA_Flags

    Public Sub New(ta As TurboActivate, useTrialFlags As TA_Flags)
		Me.ta = ta
		Me.trialFlags = useTrialFlags

        InitializeComponent()
	End Sub

    Private Sub btnCancel_Click(sender As System.Object, e As System.EventArgs) Handles btnCancel.Click
        Close()
    End Sub

    Private Sub btnOK_Click(sender As System.Object, e As System.EventArgs) Handles btnOK.Click
        Try
            ' try to extend the trial and close the form
            ta.ExtendTrial(txtExtension.Text, trialFlags)
            DialogResult = DialogResult.OK
            Close()
        Catch ex As Exception
            MessageBox.Show(ex.Message, "Trial extension failed.", MessageBoxButtons.OK, MessageBoxIcon.Error)
            txtExtension.Focus()
        End Try
    End Sub

End Class