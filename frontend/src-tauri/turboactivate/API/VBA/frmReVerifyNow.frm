VERSION 5.00
Begin {C62A69F0-16DC-11CE-9E98-00AA00574A4F} frmReVerifyNow 
   Caption         =   "Re-verify with the activation servers"
   ClientHeight    =   1452
   ClientLeft      =   108
   ClientTop       =   456
   ClientWidth     =   5496
   OleObjectBlob   =   "frmReVerifyNow.frx":0000
   StartUpPosition =   1  'CenterOwner
End
Attribute VB_Name = "frmReVerifyNow"
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
    MsgBox "Failed to deactivate: " & Err.Description
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
