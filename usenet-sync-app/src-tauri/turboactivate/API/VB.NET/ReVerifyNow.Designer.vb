<Global.Microsoft.VisualBasic.CompilerServices.DesignerGenerated()>
Partial Class ReVerifyNow
    Inherits System.Windows.Forms.Form

    'Form overrides dispose to clean up the component list.
    <System.Diagnostics.DebuggerNonUserCode()>
    Protected Overrides Sub Dispose(ByVal disposing As Boolean)
        Try
            If disposing AndAlso components IsNot Nothing Then
                components.Dispose()
            End If
        Finally
            MyBase.Dispose(disposing)
        End Try
    End Sub

    'Required by the Windows Form Designer
    Private components As System.ComponentModel.IContainer

    'NOTE: The following procedure is required by the Windows Form Designer
    'It can be modified using the Windows Form Designer.  
    'Do not modify it using the code editor.
    <System.Diagnostics.DebuggerStepThrough()>
    Private Sub InitializeComponent()
        Me.lblDescr = New System.Windows.Forms.Label()
        Me.btnExit = New System.Windows.Forms.Button()
        Me.btnReverify = New System.Windows.Forms.Button()
        Me.SuspendLayout
        '
        'lblDescr
        '
        Me.lblDescr.AutoSize = true
        Me.lblDescr.Location = New System.Drawing.Point(16, 11)
        Me.lblDescr.Margin = New System.Windows.Forms.Padding(4, 0, 4, 0)
        Me.lblDescr.Name = "lblDescr"
        Me.lblDescr.Size = New System.Drawing.Size(358, 17)
        Me.lblDescr.TabIndex = 8
        Me.lblDescr.Text = "You have X days to re-verify with the activation servers."
        '
        'btnExit
        '
        Me.btnExit.DialogResult = System.Windows.Forms.DialogResult.Cancel
        Me.btnExit.FlatStyle = System.Windows.Forms.FlatStyle.System
        Me.btnExit.Location = New System.Drawing.Point(258, 56)
        Me.btnExit.Margin = New System.Windows.Forms.Padding(4)
        Me.btnExit.Name = "btnExit"
        Me.btnExit.Size = New System.Drawing.Size(174, 30)
        Me.btnExit.TabIndex = 7
        Me.btnExit.Text = "Exit application"
        Me.btnExit.UseVisualStyleBackColor = true
        '
        'btnReverify
        '
        Me.btnReverify.FlatStyle = System.Windows.Forms.FlatStyle.System
        Me.btnReverify.Location = New System.Drawing.Point(19, 56)
        Me.btnReverify.Margin = New System.Windows.Forms.Padding(4)
        Me.btnReverify.Name = "btnReverify"
        Me.btnReverify.Size = New System.Drawing.Size(123, 30)
        Me.btnReverify.TabIndex = 6
        Me.btnReverify.Text = "Re-verify now"
        Me.btnReverify.UseVisualStyleBackColor = true
        '
        'ReVerifyNow
        '
        Me.AutoScaleDimensions = New System.Drawing.SizeF(8!, 16!)
        Me.AutoScaleMode = System.Windows.Forms.AutoScaleMode.Font
        Me.ClientSize = New System.Drawing.Size(458, 105)
        Me.Controls.Add(Me.lblDescr)
        Me.Controls.Add(Me.btnExit)
        Me.Controls.Add(Me.btnReverify)
        Me.FormBorderStyle = System.Windows.Forms.FormBorderStyle.FixedDialog
        Me.MaximizeBox = false
        Me.MinimizeBox = false
        Me.Name = "ReVerifyNow"
        Me.ShowIcon = false
        Me.ShowInTaskbar = false
        Me.StartPosition = System.Windows.Forms.FormStartPosition.CenterParent
        Me.Text = "Re-verify with the activation servers"
        Me.ResumeLayout(false)
        Me.PerformLayout

End Sub

    Private WithEvents lblDescr As Label
    Private WithEvents btnExit As Button
    Private WithEvents btnReverify As Button
End Class
