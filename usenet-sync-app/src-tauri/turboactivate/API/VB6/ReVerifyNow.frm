VERSION 5.00
Begin VB.Form ReVerifyNow 
   BorderStyle     =   3  'Fixed Dialog
   Caption         =   "Re-verify with the activation servers"
   ClientHeight    =   1440
   ClientLeft      =   45
   ClientTop       =   330
   ClientWidth     =   5415
   LinkTopic       =   "Form1"
   MaxButton       =   0   'False
   MinButton       =   0   'False
   ScaleHeight     =   1440
   ScaleWidth      =   5415
   ShowInTaskbar   =   0   'False
   StartUpPosition =   1  'CenterOwner
   Begin VB.CommandButton btnExit 
      Caption         =   "Exit application"
      Height          =   495
      Left            =   3360
      TabIndex        =   2
      Top             =   840
      Width           =   1935
   End
   Begin VB.CommandButton btnReverify 
      Caption         =   "Re-verify now"
      Height          =   495
      Left            =   120
      TabIndex        =   1
      Top             =   840
      Width           =   1695
   End
   Begin VB.Label lblDescr 
      Caption         =   "You have X days to re-verify with the activation servers."
      Height          =   615
      Left            =   120
      TabIndex        =   0
      Top             =   120
      Width           =   5175
   End
End
Attribute VB_Name = "ReVerifyNow"
Attribute VB_GlobalNameSpace = False
Attribute VB_Creatable = False
Attribute VB_PredeclaredId = True
Attribute VB_Exposed = False
Option Explicit

Private ta As TurboActivate
Private inGrace As Boolean
Public GenuineDaysLeft As Long
Public noLongerActivated As Boolean

Private OKClicked As Boolean


Private Sub btnReverify_Click()
    ' tell your app to handle errors in the section
    ' at the end of the sub
    On Error GoTo TAError

    Select Case ta.IsGenuine()
        Case IsGenuineResult.Genuine, IsGenuineResult.GenuineFeaturesChanged
            OKClicked = True
            Unload Me

        Case IsGenuineResult.NotGenuine, IsGenuineResult.NotGenuineInVM
            noLongerActivated = True
            OKClicked = False
            Unload Me

        Case IsGenuineResult.InternetError
            MsgBox "Failed to connect with the activation servers."
    End Select


SubExit:
    Exit Sub

TAError:
    MsgBox "Failed to re-verify: " & Err.Description
    Resume SubExit
End Sub

Private Sub btnExit_Click()
    Unload Me
End Sub

Public Function ShowDialog(ByRef turboAct As TurboActivate, ByVal DaysBetweenChecks As Long, ByVal GracePeriodLength As Long) As VbMsgBoxResult
    Set ta = turboAct

    ' Use the days between checks and grace period from
    ' the main form
    GenuineDaysLeft = ta.GenuineDays(DaysBetweenChecks, GracePeriodLength, inGrace)
 
    If GenuineDaysLeft = 0 Then
        lblDescr.Caption = "You must re-verify with the activation servers to continue using this app."
    Else
        lblDescr.Caption = "You have " & GenuineDaysLeft & " days to re-verify with the activation servers."
    End If

    Me.show vbModal
    ShowDialog = IIf(OKClicked, vbOK, vbCancel)
    Unload Me
End Function
