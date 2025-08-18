VERSION 5.00
Begin {C62A69F0-16DC-11CE-9E98-00AA00574A4F} frmTrialExtension 
   Caption         =   "Trial extension"
   ClientHeight    =   2844
   ClientLeft      =   108
   ClientTop       =   456
   ClientWidth     =   5004
   OleObjectBlob   =   "frmTrialExtension.frx":0000
   StartUpPosition =   1  'CenterOwner
End
Attribute VB_Name = "frmTrialExtension"
Attribute VB_GlobalNameSpace = False
Attribute VB_Creatable = False
Attribute VB_PredeclaredId = True
Attribute VB_Exposed = False
Option Explicit

Private ta As TurboActivate
Private trialFlags As Long
Private OKClicked As Boolean

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

Private Sub btnCancel_Click()
    Unload Me
End Sub

Public Function ShowDialog(ByRef turboAct As TurboActivate, ByVal useTrialFlags As Long) As VbMsgBoxResult
    Set ta = turboAct
    trialFlags = useTrialFlags

    Me.show vbModal
    ShowDialog = IIf(OKClicked, vbOK, vbCancel)
    Unload Me
End Function
