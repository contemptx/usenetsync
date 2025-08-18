VERSION 5.00
Begin VB.Form TrialExtension 
   BorderStyle     =   3  'Fixed Dialog
   Caption         =   "Trial extension"
   ClientHeight    =   3015
   ClientLeft      =   2760
   ClientTop       =   3750
   ClientWidth     =   5430
   LinkTopic       =   "Form1"
   MaxButton       =   0   'False
   MinButton       =   0   'False
   ScaleHeight     =   3015
   ScaleWidth      =   5430
   ShowInTaskbar   =   0   'False
   StartUpPosition =   1  'CenterOwner
   Begin VB.TextBox txtExtension 
      Height          =   1935
      Left            =   120
      MultiLine       =   -1  'True
      ScrollBars      =   2  'Vertical
      TabIndex        =   2
      Top             =   480
      Width           =   5175
   End
   Begin VB.CommandButton btnCancel 
      Cancel          =   -1  'True
      Caption         =   "Cancel"
      Height          =   375
      Left            =   4080
      TabIndex        =   1
      Top             =   2520
      Width           =   1215
   End
   Begin VB.CommandButton btnOK 
      Caption         =   "OK"
      Height          =   375
      Left            =   2640
      TabIndex        =   0
      Top             =   2520
      Width           =   1215
   End
   Begin VB.Label Label1 
      Caption         =   "Paste your trial extension here:"
      Height          =   255
      Left            =   120
      TabIndex        =   3
      Top             =   120
      Width           =   2775
   End
End
Attribute VB_Name = "TrialExtension"
Attribute VB_GlobalNameSpace = False
Attribute VB_Creatable = False
Attribute VB_PredeclaredId = True
Attribute VB_Exposed = False
Option Explicit

Private ta As TurboActivate
Private trialFlags As Long
Private OKClicked As Boolean

Private Sub btnCancel_Click()
    Unload Me
End Sub

Private Sub btnOK_Click()
    ' tell your app to handle errors in the section
    ' at the end of the sub
    On Error GoTo TAProcError

    Call ta.ExtendTrial(txtExtension.Text, trialFlags)
    OKClicked = True

    ' Close the form only if there isn't an error.
    Unload Me

ProcExit:
    Exit Sub

TAProcError:
    MsgBox "Trial extension failed. " & Err.Description, vbCritical
    txtExtension.SetFocus
    Resume ProcExit
End Sub

Public Function ShowDialog(ByRef turboAct As TurboActivate, ByVal useTrialFlags As Long) As VbMsgBoxResult
    Set ta = turboAct
    trialFlags = useTrialFlags

    Me.show vbModal
    ShowDialog = IIf(OKClicked, vbOK, vbCancel)
    Unload Me
End Function

