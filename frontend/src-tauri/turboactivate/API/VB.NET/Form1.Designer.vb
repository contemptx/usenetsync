<Global.Microsoft.VisualBasic.CompilerServices.DesignerGenerated()>
Partial Class Form1
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
        Me.components = New System.ComponentModel.Container()
        Dim resources As System.ComponentModel.ComponentResourceManager = New System.ComponentModel.ComponentResourceManager(GetType(Form1))
        Me.lblTrialMessage = New System.Windows.Forms.Label()
        Me.txtMain = New System.Windows.Forms.TextBox()
        Me.mainMenu1 = New System.Windows.Forms.MainMenu(Me.components)
        Me.menuItem1 = New System.Windows.Forms.MenuItem()
        Me.menuItem2 = New System.Windows.Forms.MenuItem()
        Me.mnuHelp = New System.Windows.Forms.MenuItem()
        Me.mnuHelpContents = New System.Windows.Forms.MenuItem()
        Me.mnuActDeact = New System.Windows.Forms.MenuItem()
        Me.btnExtendTrial = New System.Windows.Forms.Button()
        Me.SuspendLayout()
        '
        'lblTrialMessage
        '
        Me.lblTrialMessage.Anchor = CType((System.Windows.Forms.AnchorStyles.Bottom Or System.Windows.Forms.AnchorStyles.Left), System.Windows.Forms.AnchorStyles)
        Me.lblTrialMessage.AutoSize = True
        Me.lblTrialMessage.Location = New System.Drawing.Point(9, 169)
        Me.lblTrialMessage.Name = "lblTrialMessage"
        Me.lblTrialMessage.Size = New System.Drawing.Size(95, 13)
        Me.lblTrialMessage.TabIndex = 3
        Me.lblTrialMessage.Text = "Your trial expires in"
        Me.lblTrialMessage.Visible = False
        '
        'txtMain
        '
        Me.txtMain.Location = New System.Drawing.Point(12, 12)
        Me.txtMain.Multiline = True
        Me.txtMain.Name = "txtMain"
        Me.txtMain.ScrollBars = System.Windows.Forms.ScrollBars.Vertical
        Me.txtMain.Size = New System.Drawing.Size(384, 140)
        Me.txtMain.TabIndex = 2
        Me.txtMain.Text = resources.GetString("txtMain.Text")
        '
        'mainMenu1
        '
        Me.mainMenu1.MenuItems.AddRange(New System.Windows.Forms.MenuItem() {Me.menuItem1, Me.mnuHelp})
        '
        'menuItem1
        '
        Me.menuItem1.Index = 0
        Me.menuItem1.MenuItems.AddRange(New System.Windows.Forms.MenuItem() {Me.menuItem2})
        Me.menuItem1.Text = "File"
        '
        'menuItem2
        '
        Me.menuItem2.Index = 0
        Me.menuItem2.Text = "New"
        '
        'mnuHelp
        '
        Me.mnuHelp.Index = 1
        Me.mnuHelp.MenuItems.AddRange(New System.Windows.Forms.MenuItem() {Me.mnuHelpContents, Me.mnuActDeact})
        Me.mnuHelp.Text = "Help"
        '
        'mnuHelpContents
        '
        Me.mnuHelpContents.Index = 0
        Me.mnuHelpContents.Text = "Help contents"
        '
        'mnuActDeact
        '
        Me.mnuActDeact.Index = 1
        Me.mnuActDeact.Text = "Deactivate..."
        '
        'btnExtendTrial
        '
        Me.btnExtendTrial.Anchor = CType((System.Windows.Forms.AnchorStyles.Bottom Or System.Windows.Forms.AnchorStyles.Right), System.Windows.Forms.AnchorStyles)
        Me.btnExtendTrial.Location = New System.Drawing.Point(315, 165)
        Me.btnExtendTrial.Name = "btnExtendTrial"
        Me.btnExtendTrial.Size = New System.Drawing.Size(81, 25)
        Me.btnExtendTrial.TabIndex = 4
        Me.btnExtendTrial.Text = "Extend trial"
        Me.btnExtendTrial.UseVisualStyleBackColor = True
        '
        'Form1
        '
        Me.AutoScaleDimensions = New System.Drawing.SizeF(6.0!, 13.0!)
        Me.AutoScaleMode = System.Windows.Forms.AutoScaleMode.Font
        Me.ClientSize = New System.Drawing.Size(408, 199)
        Me.Controls.Add(Me.btnExtendTrial)
        Me.Controls.Add(Me.lblTrialMessage)
        Me.Controls.Add(Me.txtMain)
        Me.FormBorderStyle = System.Windows.Forms.FormBorderStyle.FixedSingle
        Me.MaximizeBox = False
        Me.Menu = Me.mainMenu1
        Me.Name = "Form1"
        Me.Text = "Text Editor Plus"
        Me.ResumeLayout(False)
        Me.PerformLayout()

    End Sub
    Private WithEvents lblTrialMessage As System.Windows.Forms.Label
    Private WithEvents txtMain As System.Windows.Forms.TextBox
    Private WithEvents mainMenu1 As System.Windows.Forms.MainMenu
    Private WithEvents menuItem1 As System.Windows.Forms.MenuItem
    Private WithEvents menuItem2 As System.Windows.Forms.MenuItem
    Private WithEvents mnuHelp As System.Windows.Forms.MenuItem
    Private WithEvents mnuHelpContents As System.Windows.Forms.MenuItem
    Private WithEvents mnuActDeact As System.Windows.Forms.MenuItem
    Friend WithEvents btnExtendTrial As System.Windows.Forms.Button

End Class
