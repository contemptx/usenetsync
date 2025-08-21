VERSION 5.00
Begin {C62A69F0-16DC-11CE-9E98-00AA00574A4F} frmActivateOffline 
   Caption         =   "Activate YourApp offline"
   ClientHeight    =   3756
   ClientLeft      =   0
   ClientTop       =   -2208
   ClientWidth     =   7068
   OleObjectBlob   =   "frmActivateOffline.frx":0000
   StartUpPosition =   1  'CenterOwner
End
Attribute VB_Name = "frmActivateOffline"
Attribute VB_GlobalNameSpace = False
Attribute VB_Creatable = False
Attribute VB_PredeclaredId = True
Attribute VB_Exposed = False


' Note: this has a runtime error when the user clicks cancel.
' This is a bug in the MacScript. I didn't have time to fix it.
Function myGetOpenFileName(Optional sPath As String) As String
Dim sFile As String
Dim sMacScript As String

        If sPath = vbNullString Then
            sPath = "the path to documents folder"
        Else
            sPath = " alias """ & sPath & """"
        End If
        sMacScript = "set sFile to (choose file of type ({""public.xml""}) with prompt " & _
            """Open the activation response file."" default location " & sPath & ") as string" _
            & vbLf & _
            "return sFile"
         Debug.Print sMacScript
        sFile = MacScript(sMacScript)

    myGetOpenFileName = sFile
End Function


Private Sub btnActivate_Click()
    Dim sFile As String
    sFile = myGetOpenFileName()
    
    ' Convert horrible Mac format path to POSIX form paths (required by TurboActivate)
    sFile = Replace(Mid(sFile, InStr(sFile, ":")), ":", "/")
    
    If TurboActivate.ActivateFromFile(sFile) Then
        'TODO: re-enable features of SigmaXL
        MsgBox ("Activation successful!")
        Unload Me
    End If
End Sub

Private Sub btnActivationRequest_Click()

    ' TODO: handle the user canceling the dialog
    Dim sFile As String
    sFile = MacScript("set myFile to (choose file name with prompt ""Save file as:"" default name ""ActivationRequest.xml"") as string" _
                                 & vbLf & "return myFile")

    ' Convert horrible Mac format path to POSIX form paths (required by TurboActivate)
    sFile = Replace(Mid(sFile, InStr(sFile, ":")), ":", "/")

    TurboActivate.ActivationRequestToFile (sFile)
End Sub

Private Sub cmdcancel_Click()
    Unload Me
End Sub

