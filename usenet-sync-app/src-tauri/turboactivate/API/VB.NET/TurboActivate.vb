Imports System
Imports System.ComponentModel
Imports System.Runtime.InteropServices
Imports System.Text
Imports System.Threading


Namespace wyDay.TurboActivate

    <Flags>
    Public Enum TA_Flags As UInteger
        TA_SYSTEM = 1
        TA_USER = 2

        ''' <summary>
        ''' Use the TA_DISALLOW_VM in UseTrial() to disallow trials in virtual machines. 
        ''' If you use this flag in UseTrial() and the customer's machine is a Virtual
        ''' Machine, then UseTrial() will throw VirtualMachineException.
        ''' </summary>
        TA_DISALLOW_VM = 4

        ''' <summary>
        ''' Use this flag in TA_UseTrial() to tell TurboActivate to use client-side 
        ''' unverified trials. For more information about verified vs. unverified trials,
        ''' see here: https://wyday.com/limelm/help/trials/
        ''' Note: unverified trials are unsecured and can be reset by malicious customers.
        ''' </summary>
        TA_UNVERIFIED_TRIAL = 16

        ''' <summary>
        ''' Use the TA_VERIFIED_TRIAL flag to use verified trials instead 
        ''' of unverified trials. This means the trial is locked to a particular computer.
        ''' The customer can't reset the trial.
        ''' </summary>
        TA_VERIFIED_TRIAL = 32
    End Enum

    <Flags()>
    Public Enum TA_DateCheckFlags As UInteger
        ''' <summary>TAHasNotExpired when passed into IsDateValid() verifies that the passed in UTC date-time has not elapsed.</summary>
        TA_HAS_NOT_EXPIRED = 1
    End Enum


    ''' <summary>Represents the method that will handle an event that is cancelable.</summary>
    ''' <param name="sender">The source of the event.</param>
    ''' <param name="e">A StatusArgs that shows you the result of the trial change.</param>
    Public Delegate Sub TrialCallbackHandler(sender As Object, e As StatusArgs)

    Public Enum TA_TrialStatus As UInteger
        ''' <summary>Callback-status value used when the trial has expired.</summary>
        TA_CB_EXPIRED = 0

        ''' <summary>Callback-status value used when the trial has expired due to date/time fraud.</summary>
        TA_CB_EXPIRED_FRAUD = 1
    End Enum

    ''' <summary>Event data for a trial callback.</summary>
    Public Class StatusArgs
        Inherits EventArgs

        ''' <summary>The status of the trial.</summary>
        Public Property Status() As TA_TrialStatus
    End Class


    Public Class TurboActivate
        Private ReadOnly handle As UInteger = 0

        Public ReadOnly Property VersionGUID() As String

        ''' <summary>Creates a TurboActivate object instance.</summary>
        ''' <param name="vGUID">The GUID for this product version. This is found on the LimeLM site on the version overview.</param>
        ''' <param name="pdetsFilename">The absolute location to the TurboActivate.dat file on the disk.</param>
        Public Sub New(vGUID As String, Optional pdetsFilename As String = Nothing)
            If pdetsFilename <> Nothing Then

#If TA_BOTH_DLL Then
                Select Case If(IntPtr.Size = 8, Native64.TA_PDetsFromPath(pdetsFilename), Native.TA_PDetsFromPath(pdetsFilename))
#Else
                Select Case Native.TA_PDetsFromPath(pdetsFilename)
#End If
                    Case TA_OK
                        ' successful
                    Case TA_FAIL
                        ' the TurboActivate.dat already loaded.
                    Case TA_E_PDETS
                        Throw New ProductDetailsException
                    Case Else
                        Throw New TurboActivateException("The TurboActivate.dat file failed to load.")
                End Select
            End If

            VersionGUID = vGUID

#If TA_BOTH_DLL Then
            handle = If(IntPtr.Size = 8, Native64.TA_GetHandle(vGUID), Native.TA_GetHandle(vGUID))
#Else
            handle = Native.TA_GetHandle(vGUID)
#End If

            ' if the handle is still unset then immediately throw an exception
            ' telling the user that they need to actually load the correct
            ' TurboActivate.dat and/or use the correct GUID for the TurboActivate.dat
            If handle = 0 Then
                Throw New ProductDetailsException()
            End If
        End Sub

        ' <summary>Creates a TurboActivate object instance.</summary>
        ' <param name="vGUID">The GUID for this product version. This Is found on the LimeLM site on the version overview.</param>
        ' <param name="pdetsData">The TurboActivate.dat file loaded into a byte array.</param>
        Public Sub New(vGUID As String, pdetsData As Byte())
#If TA_BOTH_DLL Then
            Select Case If(IntPtr.Size = 8, Native64.TA_PDetsFromByteArray(pdetsData, pdetsData.Length), Native.TA_PDetsFromByteArray(pdetsData, pdetsData.Length))
#Else
            Select Case Native.TA_PDetsFromByteArray(pdetsData, pdetsData.Length)
#End If
                Case TA_OK
                        ' successful
                Case TA_FAIL
                        ' the TurboActivate.dat already loaded.
                Case TA_E_PDETS
                    Throw New ProductDetailsException
                Case Else
                    Throw New TurboActivateException("The TurboActivate.dat file failed to load.")
            End Select


            VersionGUID = vGUID

#If TA_BOTH_DLL Then
            handle = If(IntPtr.Size = 8, Native64.TA_GetHandle(VersionGUID), Native.TA_GetHandle(VersionGUID))
#Else
            handle = Native.TA_GetHandle(VersionGUID)
#End If

            ' if the handle is still unset then immediately throw an exception
            ' telling the user that they need to actually load the correct
            ' TurboActivate.dat and/or use the correct GUID for the TurboActivate.dat
            If handle = 0 Then
                Throw New ProductDetailsException()
            End If
        End Sub


        ''' <summary>The trial callback delegate.</summary>
        ''' <param name="status">The status that's returned from TurboActivate to the callback function.</param>
        <UnmanagedFunctionPointer(CallingConvention.Cdecl)>
        Private Delegate Sub TrialCallbackType(status As UInteger)

        ''' <summary>The async operation variable to manage the various thread contexts without forcing the user to do this.</summary>
        Private _operation As AsyncOperation

        ''' <summary>Holds the actual callback event, while the public version does a whole bunch of junk to initialize the callback with native code, etc.</summary>
        Private Event privTrialChange As TrialCallbackHandler

        ''' <summary>Storing the native callback delegate instance so it doesn't get garbage collected (.NET garbage collector will collect a local delegate if we just pass it to the native function like this TA_SetTrialCallback(TrialCallbackFn) )</summary>
        Private privTrialCallback As TrialCallbackType


        Public Custom Event TrialChange As TrialCallbackHandler
            AddHandler(ByVal value As TrialCallbackHandler)
                If privTrialChangeEvent Is Nothing Then

                    ' prevent garbage collection of the delegate by storing it in a local variable.
                    privTrialCallback = New TrialCallbackType(AddressOf TrialCallbackFn)

#If TA_BOTH_DLL Then
                    Select Case If(IntPtr.Size = 8, Native64.TA_SetTrialCallback(handle, privTrialCallback), Native.TA_SetTrialCallback(handle, privTrialCallback))
#Else
                    Select Case Native.TA_SetTrialCallback(handle, privTrialCallback)
#End If
                        Case TA_E_INVALID_HANDLE
                            Throw New InvalidHandleException()
                        Case TA_OK ' successful, don't do anything
                        Case Else
                            Throw New TurboActivateException("Failed to save trial callback.")
                    End Select
                End If

                AddHandler privTrialChange, value
            End AddHandler

            RemoveHandler(ByVal value As TrialCallbackHandler)
                RemoveHandler privTrialChange, value

                If privTrialChangeEvent Is Nothing Then
                    AddHandler privTrialChange, value
                    Throw New TurboActivateException("You must have at least one subscriber to the TrialChange event.")
                End If

            End RemoveHandler

            RaiseEvent(ByVal sender As System.Object, ByVal e As StatusArgs)
                ' pass the raise event to the actual internal event
                RaiseEvent privTrialChange(sender, e)
            End RaiseEvent
        End Event


        Private Class Native
            <StructLayout(LayoutKind.Sequential, CharSet:=CharSet.Unicode)>
            Public Structure ACTIVATE_OPTIONS
                Public nLength As UInteger

                <MarshalAs(UnmanagedType.LPWStr)>
                Public sExtraData As String
            End Structure

            <Flags()>
            Public Enum GenuineFlags As UInteger
                TA_SKIP_OFFLINE = 1
                TA_OFFLINE_SHOW_INET_ERR = 2
            End Enum

            <StructLayout(LayoutKind.Sequential, CharSet:=CharSet.Unicode)>
            Public Structure GENUINE_OPTIONS
                Public nLength As UInteger

                Public flags As GenuineFlags

                Public nDaysBetweenChecks As UInteger

                Public nGraceDaysOnInetErr As UInteger
            End Structure

            <DllImport("TurboActivate.dll", CharSet:=CharSet.Unicode, CallingConvention:=CallingConvention.Cdecl)>
            Public Shared Function TA_GetHandle(ByVal versionGUID As String) As Integer
            End Function

            <DllImport("TurboActivate.dll", CharSet:=CharSet.Unicode, CallingConvention:=CallingConvention.Cdecl)>
            Public Shared Function TA_Activate(handle As UInteger, ByRef options As ACTIVATE_OPTIONS) As Integer
            End Function

            <DllImport("TurboActivate.dll", CharSet:=CharSet.Unicode, CallingConvention:=CallingConvention.Cdecl)>
            Public Shared Function TA_Activate(handle As UInteger, options As IntPtr) As Integer
            End Function

            <DllImport("TurboActivate.dll", CharSet:=CharSet.Unicode, CallingConvention:=CallingConvention.Cdecl)>
            Public Shared Function TA_ActivationRequestToFile(handle As UInteger, ByVal filename As String, ByRef options As ACTIVATE_OPTIONS) As Integer
            End Function

            <DllImport("TurboActivate.dll", CharSet:=CharSet.Unicode, CallingConvention:=CallingConvention.Cdecl)>
            Public Shared Function TA_ActivationRequestToFile(handle As UInteger, ByVal filename As String, options As IntPtr) As Integer
            End Function

            <DllImport("TurboActivate.dll", CharSet:=CharSet.Unicode, CallingConvention:=CallingConvention.Cdecl)>
            Public Shared Function TA_ActivateFromFile(handle As UInteger, ByVal filename As String) As Integer
            End Function

            <DllImport("TurboActivate.dll", CharSet:=CharSet.Unicode, CallingConvention:=CallingConvention.Cdecl)>
            Public Shared Function TA_CheckAndSavePKey(handle As UInteger, ByVal productKey As String, ByVal flags As TA_Flags) As Integer
            End Function

            <DllImport("TurboActivate.dll", CharSet:=CharSet.Unicode, CallingConvention:=CallingConvention.Cdecl)>
            Public Shared Function TA_Deactivate(handle As UInteger, ByVal erasePkey As Byte) As Integer
            End Function

            <DllImport("TurboActivate.dll", CharSet:=CharSet.Unicode, CallingConvention:=CallingConvention.Cdecl)>
            Public Shared Function TA_DeactivationRequestToFile(handle As UInteger, ByVal filename As String, ByVal erasePkey As Byte) As Integer
            End Function

            <DllImport("TurboActivate.dll", CharSet:=CharSet.Unicode, CallingConvention:=CallingConvention.Cdecl)>
            Public Shared Function TA_GetExtraData(handle As UInteger, ByVal lpValueStr As StringBuilder, ByVal cchValue As Integer) As Integer
            End Function

            <DllImport("TurboActivate.dll", CharSet:=CharSet.Unicode, CallingConvention:=CallingConvention.Cdecl)>
            Public Shared Function TA_GetFeatureValue(handle As UInteger, ByVal featureName As String, ByVal lpValueStr As StringBuilder, ByVal cchValue As Integer) As Integer
            End Function

            <DllImport("TurboActivate.dll", CharSet:=CharSet.Unicode, CallingConvention:=CallingConvention.Cdecl)>
            Public Shared Function TA_GetPKey(handle As UInteger, ByVal lpPKeyStr As StringBuilder, ByVal cchPKey As Integer) As Integer
            End Function

            <DllImport("TurboActivate.dll", CharSet:=CharSet.Unicode, CallingConvention:=CallingConvention.Cdecl)>
            Public Shared Function TA_IsActivated(handle As UInteger) As Integer
            End Function

            <DllImport("TurboActivate.dll", CharSet:=CharSet.Unicode, CallingConvention:=CallingConvention.Cdecl)>
            Public Shared Function TA_IsDateValid(handle As UInteger, ByVal date_time As String, ByVal flags As TA_DateCheckFlags) As Integer
            End Function

            <DllImport("TurboActivate.dll", CharSet:=CharSet.Unicode, CallingConvention:=CallingConvention.Cdecl)>
            Public Shared Function TA_IsGenuine(handle As UInteger) As Integer
            End Function

            <DllImport("TurboActivate.dll", CharSet:=CharSet.Unicode, CallingConvention:=CallingConvention.Cdecl)>
            Public Shared Function TA_IsGenuineEx(handle As UInteger, ByRef options As GENUINE_OPTIONS) As Integer
            End Function

            <DllImport("TurboActivate.dll", CharSet:=CharSet.Unicode, CallingConvention:=CallingConvention.Cdecl)>
            Public Shared Function TA_GenuineDays(handle As UInteger, nDaysBetweenChecks As UInteger, nGraceDaysOnInetErr As UInteger, ByRef DaysRemaining As UInteger, ByRef inGracePeriod As Char) As Integer
            End Function

            <DllImport("TurboActivate.dll", CharSet:=CharSet.Unicode, CallingConvention:=CallingConvention.Cdecl)>
            Public Shared Function TA_IsProductKeyValid(handle As UInteger) As Integer
            End Function

            <DllImport("TurboActivate.dll", CharSet:=CharSet.Unicode, CallingConvention:=CallingConvention.Cdecl)>
            Public Shared Function TA_SetCustomProxy(ByVal proxy As String) As Integer
            End Function

            <DllImport("TurboActivate.dll", CharSet:=CharSet.Unicode, CallingConvention:=CallingConvention.Cdecl)>
            Public Shared Function TA_TrialDaysRemaining(handle As UInteger, useTrialFlags As TA_Flags, ByRef DaysRemaining As UInteger) As Integer
            End Function

            <DllImport("TurboActivate.dll", CharSet:=CharSet.Unicode, CallingConvention:=CallingConvention.Cdecl)>
            Public Shared Function TA_UseTrial(handle As UInteger, flags As TA_Flags, extra_data As String) As Integer
            End Function

            <DllImport("TurboActivate.dll", CharSet:=CharSet.Unicode, CallingConvention:=CallingConvention.Cdecl)>
            Public Shared Function TA_UseTrialVerifiedRequest(handle As UInteger, filename As String, extra_data As String) As Integer
            End Function

            <DllImport("TurboActivate.dll", CharSet:=CharSet.Unicode, CallingConvention:=CallingConvention.Cdecl)>
            Public Shared Function TA_UseTrialVerifiedFromFile(handle As UInteger, filename As String, flags As TA_Flags) As Integer
            End Function

            <DllImport("TurboActivate.dll", CharSet:=CharSet.Unicode, CallingConvention:=CallingConvention.Cdecl)>
            Public Shared Function TA_ExtendTrial(handle As UInteger, flags As TA_Flags, trialExtension As String) As Integer
            End Function

            <DllImport("TurboActivate.dll", CharSet:=CharSet.Unicode, CallingConvention:=CallingConvention.Cdecl)>
            Public Shared Function TA_PDetsFromPath(ByVal filename As String) As Integer
            End Function

            <DllImport("TurboActivate.dll", CharSet:=CharSet.Unicode, CallingConvention:=CallingConvention.Cdecl)>
            Public Shared Function TA_PDetsFromByteArray(pArray As Byte(), nSize As Integer) As Integer
            End Function

            <DllImport("TurboActivate.dll", CharSet:=CharSet.Unicode, CallingConvention:=CallingConvention.Cdecl)>
            Public Shared Function TA_SetCustomActDataPath(handle As UInteger, directory As String) As Integer
            End Function

            <DllImport("TurboActivate.dll", CharSet:=CharSet.Unicode, CallingConvention:=CallingConvention.Cdecl)>
            Public Shared Function TA_SetTrialCallback(handle As UInteger, callback As TrialCallbackType) As Integer
            End Function

            <DllImport("TurboActivate.dll", CharSet:=CharSet.Unicode, CallingConvention:=CallingConvention.Cdecl)>
            Public Shared Function TA_GetVersion(<Out()> ByRef MajorVersion As UInteger, <Out()> ByRef MinorVersion As UInteger, <Out()> ByRef BuildVersion As UInteger, <Out()> ByRef RevisionVersion As UInteger) As Integer
            End Function
        End Class

        ' To use "AnyCPU" Target CPU type, first copy the x64 TurboActivate.dll and rename to TurboActivate64.dll
        ' Then in your project properties go to the Compile panel, click "Advanced Compile Options..." and add
        ' the following custom constant: TA_BOTH_DLL=TRUE

#If TA_BOTH_DLL Then
        Private Class Native64

            <DllImport("TurboActivate64.dll", CharSet:=CharSet.Unicode, CallingConvention:=CallingConvention.Cdecl)>
            Public Shared Function TA_GetHandle(ByVal versionGUID As String) As Integer
            End Function

            <DllImport("TurboActivate64.dll", CharSet:=CharSet.Unicode, CallingConvention:=CallingConvention.Cdecl)>
            Public Shared Function TA_Activate(handle As UInteger, ByRef options As Native.ACTIVATE_OPTIONS) As Integer
            End Function

            <DllImport("TurboActivate64.dll", CharSet:=CharSet.Unicode, CallingConvention:=CallingConvention.Cdecl)>
            Public Shared Function TA_Activate(handle As UInteger, options As IntPtr) As Integer
            End Function

            <DllImport("TurboActivate64.dll", CharSet:=CharSet.Unicode, CallingConvention:=CallingConvention.Cdecl)>
            Public Shared Function TA_ActivationRequestToFile(handle As UInteger, ByVal filename As String, ByRef options As Native.ACTIVATE_OPTIONS) As Integer
            End Function

            <DllImport("TurboActivate64.dll", CharSet:=CharSet.Unicode, CallingConvention:=CallingConvention.Cdecl)>
            Public Shared Function TA_ActivationRequestToFile(handle As UInteger, ByVal filename As String, options As IntPtr) As Integer
            End Function

            <DllImport("TurboActivate64.dll", CharSet:=CharSet.Unicode, CallingConvention:=CallingConvention.Cdecl)>
            Public Shared Function TA_ActivateFromFile(handle As UInteger, ByVal filename As String) As Integer
            End Function

            <DllImport("TurboActivate64.dll", CharSet:=CharSet.Unicode, CallingConvention:=CallingConvention.Cdecl)>
            Public Shared Function TA_CheckAndSavePKey(handle As UInteger, ByVal productKey As String, ByVal flags As TA_Flags) As Integer
            End Function

            <DllImport("TurboActivate64.dll", CharSet:=CharSet.Unicode, CallingConvention:=CallingConvention.Cdecl)>
            Public Shared Function TA_Deactivate(handle As UInteger, ByVal erasePkey As Byte) As Integer
            End Function

            <DllImport("TurboActivate64.dll", CharSet:=CharSet.Unicode, CallingConvention:=CallingConvention.Cdecl)>
            Public Shared Function TA_DeactivationRequestToFile(handle As UInteger, ByVal filename As String, ByVal erasePkey As Byte) As Integer
            End Function

            <DllImport("TurboActivate64.dll", CharSet:=CharSet.Unicode, CallingConvention:=CallingConvention.Cdecl)>
            Public Shared Function TA_GetExtraData(handle As UInteger, ByVal lpValueStr As StringBuilder, ByVal cchValue As Integer) As Integer
            End Function

            <DllImport("TurboActivate64.dll", CharSet:=CharSet.Unicode, CallingConvention:=CallingConvention.Cdecl)>
            Public Shared Function TA_GetFeatureValue(handle As UInteger, ByVal featureName As String, ByVal lpValueStr As StringBuilder, ByVal cchValue As Integer) As Integer
            End Function

            <DllImport("TurboActivate64.dll", CharSet:=CharSet.Unicode, CallingConvention:=CallingConvention.Cdecl)>
            Public Shared Function TA_GetPKey(handle As UInteger, ByVal lpPKeyStr As StringBuilder, ByVal cchPKey As Integer) As Integer
            End Function

            <DllImport("TurboActivate64.dll", CharSet:=CharSet.Unicode, CallingConvention:=CallingConvention.Cdecl)>
            Public Shared Function TA_IsActivated(handle As UInteger) As Integer
            End Function

            <DllImport("TurboActivate64.dll", CharSet:=CharSet.Unicode, CallingConvention:=CallingConvention.Cdecl)>
            Public Shared Function TA_IsDateValid(handle As UInteger, ByVal date_time As String, ByVal flags As TA_DateCheckFlags) As Integer
            End Function

            <DllImport("TurboActivate64.dll", CharSet:=CharSet.Unicode, CallingConvention:=CallingConvention.Cdecl)>
            Public Shared Function TA_IsGenuine(handle As UInteger) As Integer
            End Function

            <DllImport("TurboActivate64.dll", CharSet:=CharSet.Unicode, CallingConvention:=CallingConvention.Cdecl)>
            Public Shared Function TA_IsGenuineEx(handle As UInteger, ByRef options As Native.GENUINE_OPTIONS) As Integer
            End Function

            <DllImport("TurboActivate64.dll", CharSet:=CharSet.Unicode, CallingConvention:=CallingConvention.Cdecl)>
            Public Shared Function TA_GenuineDays(handle As UInteger, nDaysBetweenChecks As UInteger, nGraceDaysOnInetErr As UInteger, ByRef DaysRemaining As UInteger, ByRef inGracePeriod As Char) As Integer
            End Function

            <DllImport("TurboActivate64.dll", CharSet:=CharSet.Unicode, CallingConvention:=CallingConvention.Cdecl)>
            Public Shared Function TA_IsProductKeyValid(handle As UInteger) As Integer
            End Function

            <DllImport("TurboActivate64.dll", CharSet:=CharSet.Unicode, CallingConvention:=CallingConvention.Cdecl)>
            Public Shared Function TA_SetCustomProxy(ByVal proxy As String) As Integer
            End Function

            <DllImport("TurboActivate64.dll", CharSet:=CharSet.Unicode, CallingConvention:=CallingConvention.Cdecl)>
            Public Shared Function TA_TrialDaysRemaining(handle As UInteger, useTrialFlags As TA_Flags, ByRef DaysRemaining As UInteger) As Integer
            End Function

            <DllImport("TurboActivate64.dll", CharSet:=CharSet.Unicode, CallingConvention:=CallingConvention.Cdecl)>
            Public Shared Function TA_UseTrial(handle As UInteger, flags As TA_Flags, extra_data As String) As Integer
            End Function

            <DllImport("TurboActivate64.dll", CharSet:=CharSet.Unicode, CallingConvention:=CallingConvention.Cdecl)>
            Public Shared Function TA_UseTrialVerifiedRequest(handle As UInteger, filename As String, extra_data As String) As Integer
            End Function

            <DllImport("TurboActivate64.dll", CharSet:=CharSet.Unicode, CallingConvention:=CallingConvention.Cdecl)>
            Public Shared Function TA_UseTrialVerifiedFromFile(handle As UInteger, filename As String, flags As TA_Flags) As Integer
            End Function

            <DllImport("TurboActivate64.dll", CharSet:=CharSet.Unicode, CallingConvention:=CallingConvention.Cdecl)>
            Public Shared Function TA_ExtendTrial(handle As UInteger, flags As TA_Flags, trialExtension As String) As Integer
            End Function

            <DllImport("TurboActivate64.dll", CharSet:=CharSet.Unicode, CallingConvention:=CallingConvention.Cdecl)>
            Public Shared Function TA_PDetsFromPath(ByVal filename As String) As Integer
            End Function

            <DllImport("TurboActivate64.dll", CharSet:=CharSet.Unicode, CallingConvention:=CallingConvention.Cdecl)>
            Public Shared Function TA_PDetsFromByteArray(pArray As Byte(), nSize As Integer) As Integer
            End Function

            <DllImport("TurboActivate64.dll", CharSet:=CharSet.Unicode, CallingConvention:=CallingConvention.Cdecl)>
            Public Shared Function TA_SetCustomActDataPath(handle As UInteger, directory As String) As Integer
            End Function

            <DllImport("TurboActivate64.dll", CharSet:=CharSet.Unicode, CallingConvention:=CallingConvention.Cdecl)>
            Public Shared Function TA_SetTrialCallback(handle As UInteger, callback As TrialCallbackType) As Integer
            End Function

            <DllImport("TurboActivate64.dll", CharSet:=CharSet.Unicode, CallingConvention:=CallingConvention.Cdecl)>
            Public Shared Function TA_GetVersion(<Out()> ByRef MajorVersion As UInteger, <Out()> ByRef MinorVersion As UInteger, <Out()> ByRef BuildVersion As UInteger, <Out()> ByRef RevisionVersion As UInteger) As Integer
            End Function
        End Class
#End If


        Private Const TA_OK As Integer = 0
        Private Const TA_FAIL As Integer = &H1

        Private Const TA_E_PKEY As Integer = &H2
        Private Const TA_E_ACTIVATE As Integer = &H3
        Private Const TA_E_INET As Integer = &H4
        Private Const TA_E_INUSE As Integer = &H5
        Private Const TA_E_REVOKED As Integer = &H6
        Private Const TA_E_GUID As Integer = &H7
        Private Const TA_E_PDETS As Integer = &H8
        Private Const TA_E_TRIAL As Integer = &H9
        Private Const TA_E_TRIAL_EUSED As Integer = &HC
        Private Const TA_E_TRIAL_EEXP As Integer = &HD
        Private Const TA_E_EXPIRED As Integer = &HD
        Private Const TA_E_REACTIVATE As Integer = &HA
        Private Const TA_E_COM As Integer = &HB
        Private Const TA_E_INSUFFICIENT_BUFFER As Integer = &HE ' never should get this in our code
        Private Const TA_E_PERMISSION As Integer = &HF
        Private Const TA_E_INVALID_FLAGS As Integer = &H10
        Private Const TA_E_IN_VM As Integer = &H11
        Private Const TA_E_EDATA_LONG As Integer = &H12
        Private Const TA_E_INVALID_ARGS As Integer = &H13
        Private Const TA_E_KEY_FOR_TURBOFLOAT As Integer = &H14
        Private Const TA_E_INET_DELAYED As Integer = &H15
        Private Const TA_E_FEATURES_CHANGED As Integer = &H16
        Private Const TA_E_NO_MORE_DEACTIVATIONS As Integer = &H18
        Private Const TA_E_ACCOUNT_CANCELED As Integer = &H19
        Private Const TA_E_ALREADY_ACTIVATED As Integer = &H1A
        Private Const TA_E_INVALID_HANDLE As Integer = &H1B
        Private Const TA_E_ENABLE_NETWORK_ADAPTERS As Integer = &H1C
        Private Const TA_E_ALREADY_VERIFIED_TRIAL As Integer = &H1D
        Private Const TA_E_TRIAL_EXPIRED As Integer = &H1E
        Private Const TA_E_MUST_SPECIFY_TRIAL_TYPE As Integer = &H1F
        Private Const TA_E_MUST_USE_TRIAL As Integer = &H20
        Private Const TA_E_NO_MORE_TRIALS_ALLOWED As Integer = &H21
        Private Const TA_E_BROKEN_WMI As Integer = &H22
        Private Const TA_E_INET_TIMEOUT As Integer = &H23
        Private Const TA_E_INET_TLS As Integer = &H24

        Private Shared Function taHresultToExcep(ret As Integer, funcName As String) As TurboActivateException
            Select Case ret
                Case TA_FAIL
                    Return New TurboActivateException(funcName + " general failure.")
                Case TA_E_PKEY
                    Return New InvalidProductKeyException()
                Case TA_E_ACTIVATE
                    Return New NotActivatedException()
                Case TA_E_INET
                    Return New InternetException()
                Case TA_E_INUSE
                    Return New PkeyMaxUsedException()
                Case TA_E_REVOKED
                    Return New PkeyRevokedException()
                Case TA_E_TRIAL
                    Return New TrialDateCorruptedException()
                Case TA_E_COM
                    Return New COMException()
                Case TA_E_TRIAL_EUSED
                    Return New TrialExtUsedException()
                Case TA_E_EXPIRED
                    Return New DateTimeException()
                Case TA_E_PERMISSION
                    Return New PermissionException()
                Case TA_E_INVALID_FLAGS
                    Return New InvalidArgsException()
                Case TA_E_KEY_FOR_TURBOFLOAT
                    Return New TurboFloatKeyException()
                Case TA_E_NO_MORE_DEACTIVATIONS
                    Return New NoMoreDeactivationsException()
                Case TA_E_ACCOUNT_CANCELED
                    Return New AccountCanceledException()
                Case TA_E_ALREADY_ACTIVATED
                    Return New AlreadyActivatedException()
                Case TA_E_INVALID_HANDLE
                    Return New InvalidHandleException()
                Case TA_E_ENABLE_NETWORK_ADAPTERS
                    Return New EnableNetworkAdaptersException()
                Case TA_E_ALREADY_VERIFIED_TRIAL
                    Return New AlreadyVerifiedTrialException()
                Case TA_E_TRIAL_EXPIRED
                    Return New TrialExpiredException()
                Case TA_E_MUST_SPECIFY_TRIAL_TYPE
                    Return New MustSpecifyTrialTypeException()
                Case TA_E_MUST_USE_TRIAL
                    Return New MustUseTrialException()
                Case TA_E_NO_MORE_TRIALS_ALLOWED
                    Return New NoMoreTrialsAllowedException()
                Case TA_E_BROKEN_WMI
                    Return New BrokenWMIException()
                Case TA_E_INET_TIMEOUT
                    Return New InternetTimeoutException()
                Case TA_E_INET_TLS
                    Return New InternetTLSException()
                Case Else

                    ' Make sure you're using the latest TurboActivate.vb, we occassionally add new error codes
                    ' And you need latest version of this file to get a detailed description of the error.

                    ' More information about upgrading here https://wyday.com/limelm/help/faq/#update-libs

                    ' You can also view error directly from the source TurboActivate.h
                    Return New TurboActivateException(funcName + " failed with an unknown error code: " + ret.ToString())
            End Select
        End Function


        Private Sub TrialCallbackFn(status As UInteger)
            If _operation IsNot Nothing Then
                Dim e As StatusArgs = New StatusArgs() With {.Status = CType(status, TA_TrialStatus)}

                ' finish off the operation
                _operation.PostOperationCompleted(New SendOrPostCallback(AddressOf RaiseTrialCallbackFn), e)
            End If
        End Sub

        Private Sub RaiseTrialCallbackFn(args As Object)
            Dim stArgs As StatusArgs = CType(args, StatusArgs)

            ' null out the _operation
            _operation = Nothing

            RaiseEvent privTrialChange(Nothing, stArgs)
        End Sub


        ''' <summary>Activates the product on this computer. You must call <see cref="CheckAndSavePKey"/> with a valid product key or have used the TurboActivate wizard sometime before calling this function.</summary>
        ''' <param name="extraData">Extra data to pass to the LimeLM servers that will be visible for you to see and use. Maximum size is 255 UTF-8 characters.</param>
        Public Sub Activate(Optional ByVal extraData As String = Nothing)
            Dim ret As Integer

            If extraData <> Nothing Then
                Dim opts As Native.ACTIVATE_OPTIONS = New Native.ACTIVATE_OPTIONS() With {.sExtraData = extraData}
                opts.nLength = CUInt(Marshal.SizeOf(opts))

#If TA_BOTH_DLL Then
                ret = If(IntPtr.Size = 8, Native64.TA_Activate(handle, opts), Native.TA_Activate(handle, opts))
#Else
                ret = Native.TA_Activate(handle, opts)
#End If
            Else
#If TA_BOTH_DLL Then
                ret = If(IntPtr.Size = 8, Native64.TA_Activate(handle, IntPtr.Zero), Native.TA_Activate(handle, IntPtr.Zero))
#Else
                ret = Native.TA_Activate(handle, IntPtr.Zero)
#End If
            End If

            If Not ret = TA_OK Then
                Throw taHresultToExcep(ret, "Activate")
            End If
        End Sub

        ''' <summary>Get the "activation request" file for offline activation.  You must call <see cref="CheckAndSavePKey"/> with a valid product key or have used the TurboActivate wizard sometime before calling this function.</summary>
        ''' <param name="filename">The location where you want to save the activation request file.</param>
        ''' <param name="extraData">Extra data to pass to the LimeLM servers that will be visible for you to see and use. Maximum size is 255 UTF-8 characters.</param>
        Public Sub ActivationRequestToFile(filename As String, extraData As String)
            Dim ret As Integer

            If extraData <> Nothing Then
                Dim opts As Native.ACTIVATE_OPTIONS = New Native.ACTIVATE_OPTIONS() With {.sExtraData = extraData}
                opts.nLength = CUInt(Marshal.SizeOf(opts))

#If TA_BOTH_DLL Then
                ret = If(IntPtr.Size = 8, Native64.TA_ActivationRequestToFile(handle, filename, opts), Native.TA_ActivationRequestToFile(handle, filename, opts))
#Else
                ret = Native.TA_ActivationRequestToFile(handle, filename, opts)
#End If
            Else
#If TA_BOTH_DLL Then
                ret = If(IntPtr.Size = 8, Native64.TA_ActivationRequestToFile(handle, filename, IntPtr.Zero), Native.TA_ActivationRequestToFile(handle, filename, IntPtr.Zero))
#Else
                ret = Native.TA_ActivationRequestToFile(handle, filename, IntPtr.Zero)
#End If
            End If

            If Not ret = TA_OK Then
                Throw taHresultToExcep(ret, "ActivationRequestToFile")
            End If
        End Sub

        ''' <summary>Activate from the "activation response" file for offline activation.</summary>
        ''' <param name="filename">The location of the activation response file.</param>
        Public Sub ActivateFromFile(ByVal filename As String)
            Dim ret As Integer

#If TA_BOTH_DLL Then
            ret = If(IntPtr.Size = 8, Native64.TA_ActivateFromFile(handle, filename), Native.TA_ActivateFromFile(handle, filename))
#Else
            ret = Native.TA_ActivateFromFile(handle, filename)
#End If

            If Not ret = TA_OK Then
                Throw taHresultToExcep(ret, "ActivateFromFile")
            End If
        End Sub


        ''' <summary>Checks and save the product key.</summary>
        ''' <param name="productKey">The product key you want to save.</param>
        ''' <param name="flags">Whether to create the activation either user-wide or system-wide.</param>
        ''' <returns>True if the product key is valid, false if it's not</returns>
        Public Function CheckAndSavePKey(ByVal productKey As String, Optional ByVal flags As TA_Flags = TA_Flags.TA_SYSTEM) As Boolean
            Dim ret As Integer

#If TA_BOTH_DLL Then
            ret = If(IntPtr.Size = 8, Native64.TA_CheckAndSavePKey(handle, productKey, flags), Native.TA_CheckAndSavePKey(handle, productKey, flags))
#Else
            ret = Native.TA_CheckAndSavePKey(handle, productKey, flags)
#End If

            Select Case ret
                Case TA_OK ' successful
                    Return True
                Case TA_FAIL ' not successful
                    Return False
                Case Else
                    Throw taHresultToExcep(ret, "CheckAndSavePKey")
            End Select
        End Function

        ''' <summary>Deactivates the product on this computer.</summary>
        ''' <param name="eraseProductKey">Erase the product key so the user will have to enter a new product key if they wish to reactivate.</param>
        Public Sub Deactivate(Optional ByVal eraseProductKey As Boolean = False)
            Dim ret As Integer

#If TA_BOTH_DLL Then
            ret = If(IntPtr.Size = 8, Native64.TA_Deactivate(handle, IIf(eraseProductKey, CByte(1), CByte(0))), Native.TA_Deactivate(handle, IIf(eraseProductKey, CByte(1), CByte(0))))
#Else
            ret = Native.TA_Deactivate(handle, IIf(eraseProductKey, CByte(1), CByte(0)))
#End If

            If Not ret = TA_OK Then
                Throw taHresultToExcep(ret, "Deactivate")
            End If
        End Sub

        ''' <summary>Get the "deactivation request" file for offline deactivation.</summary>
        ''' <param name="filename">The location where you want to save the deactivation request file.</param>
        ''' <param name="eraseProductKey">Erase the product key so the user will have to enter a new product key if they wish to reactivate.</param>
        Public Sub DeactivationRequestToFile(ByVal filename As String, Optional ByVal eraseProductKey As Boolean = False)
            Dim ret As Integer

#If TA_BOTH_DLL Then
            ret = If(IntPtr.Size = 8, Native64.TA_DeactivationRequestToFile(handle, filename, IIf(eraseProductKey, CByte(1), CByte(0))), Native.TA_DeactivationRequestToFile(handle, filename, IIf(eraseProductKey, CByte(1), CByte(0))))
#Else
            ret = Native.TA_DeactivationRequestToFile(handle, filename, IIf(eraseProductKey, CByte(1), CByte(0)))
#End If

            If Not ret = TA_OK Then
                Throw taHresultToExcep(ret, "DeactivationRequestToFile")
            End If
        End Sub

        ''' <summary>Gets the extra data value you passed in when activating.</summary>
        ''' <returns>Returns the extra data if it exists, otherwise it returns null.</returns>
        Public Function GetExtraData() As String
#If TA_BOTH_DLL Then
            Dim length As Integer = If(IntPtr.Size = 8, Native64.TA_GetExtraData(handle, Nothing, 0), Native.TA_GetExtraData(handle, Nothing, 0))
#Else
            Dim length As Integer = Native.TA_GetExtraData(handle, Nothing, 0)
#End If
            Dim sb As StringBuilder = New StringBuilder(length)

#If TA_BOTH_DLL Then
            Select Case If(IntPtr.Size = 8, Native64.TA_GetExtraData(handle, sb, length), Native.TA_GetExtraData(handle, sb, length))
#Else
            Select Case Native.TA_GetExtraData(handle, sb, length)
#End If
                Case TA_OK
                    Return sb.ToString()
                Case TA_E_INVALID_HANDLE
                    Throw New InvalidHandleException
                Case Else
                    Return Nothing
            End Select
        End Function

        ''' <summary>Gets the value of a feature.</summary>
        ''' <param name="featureName">The name of the feature to retrieve the value for.</param>
        ''' <returns>Returns the feature value.</returns>
        Public Function GetFeatureValue(ByVal featureName As String) As String

            Dim value As String = GetFeatureValue(featureName, Nothing)

            If value = Nothing Then
                Throw New TurboActivateException("Failed to get feature value. The feature doesn't exist.")
            End If

            Return value
        End Function

        ''' <summary>Gets the value of a custom license field.</summary>
        ''' <param name="featureName">The name of the feature to retrieve the value for.</param>
        ''' <param name="defaultValue">The default value to return if the feature doesn't exist.</param>
        ''' <returns>Returns the feature value.</returns>
        Public Function GetFeatureValue(ByVal featureName As String, ByVal defaultValue As String) As String
#If TA_BOTH_DLL Then
            Dim length As Integer = If(IntPtr.Size = 8, Native64.TA_GetFeatureValue(handle, featureName, Nothing, 0), Native.TA_GetFeatureValue(handle, featureName, Nothing, 0))
#Else
            Dim length As Integer = Native.TA_GetFeatureValue(handle, featureName, Nothing, 0)
#End If
            Dim sb As New StringBuilder(length)

#If TA_BOTH_DLL Then
            Select Case If(IntPtr.Size = 8, Native64.TA_GetFeatureValue(handle, featureName, sb, length), Native.TA_GetFeatureValue(handle, featureName, sb, length))
#Else
            Select Case Native.TA_GetFeatureValue(handle, featureName, sb, length)
#End If
                Case TA_E_INVALID_HANDLE
                    Throw New InvalidHandleException
                Case TA_OK
                    Return sb.ToString
                Case Else
                    Return defaultValue
            End Select
        End Function

        ''' <summary>Gets the stored product key. NOTE: if you want to check if a product key is valid simply call <see cref="IsProductKeyValid()"/>. If you want to check if your app is locked to the computer then call IsGenuineEx() or IsActivated().</summary>
        ''' <returns>string Product key.</returns>
        Public Function GetPKey() As String

            ' this makes the assumption that the PKey is 34+NULL characters long.
            ' This may or may not be true in the future.
            Dim sb As New StringBuilder(35)

#If TA_BOTH_DLL Then
            Select Case If(IntPtr.Size = 8, Native64.TA_GetPKey(handle, sb, 35), Native.TA_GetPKey(handle, sb, 35))
#Else
            Select Case Native.TA_GetPKey(handle, sb, 35)
#End If
                Case TA_E_PKEY
                    Throw New InvalidProductKeyException
                Case TA_E_INVALID_HANDLE
                    Throw New InvalidHandleException
                Case TA_OK
                    Return sb.ToString
                Case Else
                    Throw New TurboActivateException("Failed to get the product key.")
            End Select
        End Function

        ''' <summary>Checks whether the computer has been activated.</summary>
        ''' <returns>True if the computer is activated. False otherwise.</returns>
        Public Function IsActivated() As Boolean
            Dim ret As Integer

#If TA_BOTH_DLL Then
            ret = If(IntPtr.Size = 8, Native64.TA_IsActivated(handle), Native.TA_IsActivated(handle))
#Else
            ret = Native.TA_IsActivated(handle)
#End If

            Select Case ret
                Case TA_OK ' is activated
                    Return True

                Case TA_FAIL ' not activated
                    Return False

                Case Else
                    Throw taHresultToExcep(ret, "IsActivated")
            End Select
        End Function

        ''' <summary>Checks if the string in the form "YYYY-MM-DD HH:mm:ss" is a valid date/time. The date must be in UTC time and "24-hour" format. If your date is in some other time format first convert it to UTC time before passing it into this function.</summary>
        ''' <param name="date_time">The date time string to check.</param>
        ''' <param name="flags">The type of date time check. Valid flags are <see cref="TA_DateCheckFlags.TA_HAS_NOT_EXPIRED"/>.</param>
        ''' <returns>True if the date is valid, false if it's not</returns>
        Public Function IsDateValid(ByVal date_time As String, ByVal flags As TA_DateCheckFlags) As Boolean
            Dim ret As Integer

#If TA_BOTH_DLL Then
            ret = If(IntPtr.Size = 8, Native64.TA_IsDateValid(handle, date_time, flags), Native.TA_IsDateValid(handle, date_time, flags))
#Else
            ret = Native.TA_IsDateValid(handle, date_time, flags)
#End If

            Select Case ret
                Case TA_OK ' date is valid and not expired
                    Return True

                Case TA_FAIL ' date is invalid or not expired
                    Return False

                Case Else
                    Throw taHresultToExcep(ret, "IsDateValid")
            End Select
        End Function

        ''' <summary>Checks whether the computer is genuinely activated by verifying with the LimeLM servers.</summary>
        ''' <returns>IsGenuineResult</returns>
        Public Function IsGenuine() As IsGenuineResult
            Dim ret As Integer

#If TA_BOTH_DLL Then
            ret = If(IntPtr.Size = 8, Native64.TA_IsGenuine(handle), Native.TA_IsGenuine(handle))
#Else
            ret = Native.TA_IsGenuine(handle)
#End If

            Select Case ret
                Case TA_OK ' is activated and/or Genuine
                    Return IsGenuineResult.Genuine

                Case TA_E_FEATURES_CHANGED
                    Return IsGenuineResult.GenuineFeaturesChanged

                Case TA_E_INET
                    Return IsGenuineResult.InternetError

                Case TA_FAIL, TA_E_REVOKED, TA_E_ACTIVATE
                    Return IsGenuineResult.NotGenuine

                Case TA_E_IN_VM
                    Return IsGenuineResult.NotGenuineInVM

                Case Else
                    Throw taHresultToExcep(ret, "IsGenuine")
            End Select
        End Function

        ''' <summary>Checks whether the computer is activated, and every "daysBetweenChecks" days it check if the customer is genuinely activated by verifying with the LimeLM servers.</summary>
        ''' <param name="daysBetweenChecks">How often to contact the LimeLM servers for validation. 90 days recommended.</param>
        ''' <param name="graceDaysOnInetErr">If the call fails because of an internet error, how long, in days, should the grace period last (before returning deactivating and returning TA_FAIL).
        ''' 
        ''' 14 days is recommended.</param>
        ''' <param name="skipOffline">If the user activated using offline activation 
        ''' (ActivateRequestToFile(), ActivateFromFile() ), then with this
        ''' option IsGenuineEx() will still try to validate with the LimeLM
        ''' servers, however instead of returning <see cref="IsGenuineResult.InternetError"/> (when within the
        ''' grace period) or <see cref="IsGenuineResult.NotGenuine"/> (when past the grace period) it will
        ''' instead only return <see cref="IsGenuineResult.Genuine"/> (if IsActivated()).
        ''' 
        ''' If the user activated using online activation then this option
        ''' is ignored.</param>
        ''' <param name="offlineShowInetErr">If the user activated using offline activation, and you're
        ''' using this option in tandem with skipOffline, then IsGenuineEx()
        ''' will return <see cref="IsGenuineResult.InternetError"/> on internet failure instead of <see cref="IsGenuineResult.Genuine"/>.
        '''
        ''' If the user activated using online activation then this flag
        ''' is ignored.</param>
        ''' <returns>IsGenuineResult</returns>
        Public Function IsGenuine(daysBetweenChecks As UInteger, graceDaysOnInetErr As UInteger, Optional skipOffline As Boolean = False, Optional offlineShowInetErr As Boolean = False) As IsGenuineResult
            Dim opts As Native.GENUINE_OPTIONS = New Native.GENUINE_OPTIONS() With {.nDaysBetweenChecks = daysBetweenChecks, .nGraceDaysOnInetErr = graceDaysOnInetErr, .flags = 0}
            opts.nLength = CUInt(Marshal.SizeOf(opts))

            If skipOffline Then
                opts.flags = Native.GenuineFlags.TA_SKIP_OFFLINE

                If offlineShowInetErr Then
                    opts.flags = opts.flags Or Native.GenuineFlags.TA_OFFLINE_SHOW_INET_ERR
                End If
            End If

            Dim ret As Integer

#If TA_BOTH_DLL Then
            ret = If(IntPtr.Size = 8, Native64.TA_IsGenuineEx(handle, opts), Native.TA_IsGenuineEx(handle, opts))
#Else
            ret = Native.TA_IsGenuineEx(handle, opts)
#End If
            Select Case ret
                Case TA_OK ' is activated and/or Genuine
                    Return IsGenuineResult.Genuine

                Case TA_E_FEATURES_CHANGED
                    Return IsGenuineResult.GenuineFeaturesChanged

                Case TA_E_INET, TA_E_INET_DELAYED
                    Return IsGenuineResult.InternetError

                Case TA_FAIL, TA_E_REVOKED, TA_E_ACTIVATE
                    Return IsGenuineResult.NotGenuine

                Case TA_E_IN_VM
                    Return IsGenuineResult.NotGenuineInVM

                Case Else
                    Throw taHresultToExcep(ret, "IsGenuineEx")
            End Select
        End Function

        ''' <summary>Get the number of days until the next time that the <see cref="IsGenuine"/> function contacts the LimeLM activation servers to reverify the activation.</summary>
        ''' <param name="daysBetweenChecks">How often to contact the LimeLM servers for validation. Use the exact same value as used in <see cref="IsGenuine"/>.</param>
        ''' <param name="graceDaysOnInetErr">If the call fails because of an internet error, how long, in days, should the grace period last (before returning deactivating and returning TA_FAIL). Again, use the exact same value as used in <see cref="IsGenuine"/>.</param>
        ''' <param name="inGracePeriod">Get whether the user is in the grace period.</param>
        ''' <returns>The number of days remaining. 0 days if both the days between checks and the grace period have expired. (E.g. 1 day means *at most* 1 day. That is, it could be 30 seconds.)</returns>
        Public Function GenuineDays(daysBetweenChecks As UInteger, graceDaysOnInetErr As UInteger, ByRef inGracePeriod As Boolean) As UInteger
            Dim ret As Integer
            Dim daysRemain As UInteger = 0UI
            Dim inGrace As Char = vbNullChar

#If TA_BOTH_DLL Then
            ret = If(IntPtr.Size = 8, Native64.TA_GenuineDays(handle, daysBetweenChecks, graceDaysOnInetErr, daysRemain, inGrace), Native.TA_GenuineDays(handle, daysBetweenChecks, graceDaysOnInetErr, daysRemain, inGrace))
#Else
            ret = Native.TA_GenuineDays(handle, daysBetweenChecks, graceDaysOnInetErr, daysRemain, inGrace)
#End If

            If Not ret = TA_OK Then
                Throw taHresultToExcep(ret, "GenuineDays")
            End If

            ' set whether we're in a grace period or not
            inGracePeriod = (inGrace = Chr(1))
            Return daysRemain
        End Function

        ''' <summary>Checks if the product key installed for this product is valid. This does NOT check if the product key is activated or genuine. Use <see cref="IsActivated"/> and <see cref="IsGenuine"/> instead.</summary>
        ''' <returns>True if the product key is valid.</returns>
        Public Function IsProductKeyValid() As Boolean
#If TA_BOTH_DLL Then
            Select Case If(IntPtr.Size = 8, Native64.TA_IsProductKeyValid(handle), Native.TA_IsProductKeyValid(handle))
#Else
            Select Case Native.TA_IsProductKeyValid(handle)
#End If
                Case TA_E_INVALID_HANDLE
                    Throw New InvalidHandleException
                Case TA_OK ' is valid
                    Return True
            End Select

            ' not valid
            Return False
        End Function

        ''' <summary>Sets the custom proxy to be used by functions that connect to the internet.</summary>
        ''' <param name="proxy">The proxy to use. Proxy must be in the form "http://username:password@host:port/".</param>
        Public Sub SetCustomProxy(ByVal proxy As String)
#If TA_BOTH_DLL Then
            If (If(IntPtr.Size = 8, Native64.TA_SetCustomProxy(proxy), Native.TA_SetCustomProxy(proxy)) <> 0) Then
#Else
            If (Native.TA_SetCustomProxy(proxy) <> TA_OK) Then
#End If
                Throw New TurboActivateException("Failed to set the custom proxy.")
            End If
        End Sub

        ''' <summary>Get the number of trial days remaining. You must call <see cref="UseTrial"/> at least once in the past before calling this function.</summary>
        ''' <param name="useTrialFlags">The same exact flags you passed to <see cref="UseTrial"/>.</param>
        ''' <returns>The number of days remaining. 0 days if the trial has expired. (E.g. 1 day means *at most* 1 day. That is it could be 30 seconds.)</returns>
        Public Function TrialDaysRemaining(Optional useTrialFlags As TA_Flags = TA_Flags.TA_SYSTEM Or TA_Flags.TA_VERIFIED_TRIAL) As UInteger
            Dim ret As Integer
            Dim daysRemain As UInteger = 0

#If TA_BOTH_DLL Then
            ret = If(IntPtr.Size = 8, Native64.TA_TrialDaysRemaining(handle, useTrialFlags, daysRemain), Native.TA_TrialDaysRemaining(handle, useTrialFlags, daysRemain))
#Else
            ret = Native.TA_TrialDaysRemaining(handle, useTrialFlags, daysRemain)
#End If

            If Not ret = TA_OK Then
                Throw taHresultToExcep(ret, "TrialDaysRemaining")
            End If

            Return daysRemain
        End Function

        ''' <summary>Begins the trial the first time it's called. Calling it again will validate the trial data hasn't been tampered with.</summary>
        ''' <param name="flags">Whether to create the trial (verified or unverified) either user-wide or system-wide and whether to allow trials in virtual machines. Valid flags are <see cref="TA_Flags.TA_SYSTEM"/>, <see cref="TA_Flags.TA_USER"/>, <see cref="TA_Flags.TA_DISALLOW_VM"/>, <see cref="TA_Flags.TA_VERIFIED_TRIAL"/>, and <see cref="TA_Flags.TA_UNVERIFIED_TRIAL"/>.</param>
        ''' <param name="extraData">Extra data to pass to the LimeLM servers that will be visible for you to see and use. Maximum size is 255 UTF-8 characters.</param>
        Public Sub UseTrial(Optional flags As TA_Flags = TA_Flags.TA_SYSTEM Or TA_Flags.TA_VERIFIED_TRIAL, Optional extraData As String = Nothing)
            Dim ret As Integer

#If TA_BOTH_DLL Then
            ret = If(IntPtr.Size = 8, Native64.TA_UseTrial(handle, flags, extraData), Native.TA_UseTrial(handle, flags, extraData))
#Else
            ret = Native.TA_UseTrial(handle, flags, extraData)
#End If

            If Not ret = TA_OK Then
                Throw taHresultToExcep(ret, "UseTrial")
            End If

            ' create operation for trial callback (if not already created)
            If _operation Is Nothing Then
                _operation = AsyncOperationManager.CreateOperation(Nothing)
            End If
        End Sub

        ''' <summary>Generate a "verified trial" offline request file. This file will then need to be submitted to LimeLM. You will then need to use the TA_UseTrialVerifiedFromFile() function with the response file from LimeLM to actually start the trial.</summary>
        ''' <param name="filename">The location where you want to save the trial request file.</param>
        ''' <param name="extraData">Extra data to pass to the LimeLM servers that will be visible for you to see and use. Maximum size is 255 UTF-8 characters.</param>
        Public Sub UseTrialVerifiedRequest(filename As String, Optional extraData As String = Nothing)
            Dim ret As Integer

#If TA_BOTH_DLL Then
            ret = If(IntPtr.Size = 8, Native64.TA_UseTrialVerifiedRequest(handle, filename, extraData), Native.TA_UseTrialVerifiedRequest(handle, filename, extraData))
#Else
            ret = Native.TA_UseTrialVerifiedRequest(handle, filename, extraData)
#End If

            If Not ret = TA_OK Then
                Throw taHresultToExcep(ret, "UseTrialVerifiedRequest")
            End If
        End Sub

        ''' <summary>Use the "verified trial response" from LimeLM to start the verified trial.</summary>
        ''' <param name="filename">The location of the trial response file.</param>
        ''' <param name="flags">Whether to create the trial (verified or unverified) either user-wide or system-wide and whether to allow trials in virtual machines. Valid flags are <see cref="TA_Flags.TA_SYSTEM"/>, <see cref="TA_Flags.TA_USER"/>, <see cref="TA_Flags.TA_DISALLOW_VM"/>, <see cref="TA_Flags.TA_VERIFIED_TRIAL"/>, and <see cref="TA_Flags.TA_UNVERIFIED_TRIAL"/>.</param>
        Public Sub UseTrialVerifiedFromFile(filename As String, Optional flags As TA_Flags = TA_Flags.TA_SYSTEM Or TA_Flags.TA_VERIFIED_TRIAL)
            Dim ret As Integer

#If TA_BOTH_DLL Then
            ret = If(IntPtr.Size = 8, Native64.TA_UseTrialVerifiedFromFile(handle, filename, flags), Native.TA_UseTrialVerifiedFromFile(handle, filename, flags))
#Else
            ret = Native.TA_UseTrialVerifiedFromFile(handle, filename, flags)
#End If

            If Not ret = TA_OK Then
                Throw taHresultToExcep(ret, "UseTrialVerifiedFromFile")
            End If

            ' create operation for trial callback (if not already created)
            If _operation Is Nothing Then
                _operation = AsyncOperationManager.CreateOperation(Nothing)
            End If
        End Sub

        ''' <summary>Extends the trial using a trial extension created in LimeLM.</summary>
        ''' <param name="trialExtension">The trial extension generated from LimeLM.</param>
        ''' <param name="useTrialFlags">The same exact flags you passed to <see cref="UseTrial"/>.</param>
        Public Sub ExtendTrial(trialExtension As String, Optional useTrialFlags As TA_Flags = TA_Flags.TA_SYSTEM Or TA_Flags.TA_VERIFIED_TRIAL)
            Dim ret As Integer

#If TA_BOTH_DLL Then
            ret = If(IntPtr.Size = 8, Native64.TA_ExtendTrial(handle, useTrialFlags, trialExtension), Native.TA_ExtendTrial(handle, useTrialFlags, trialExtension))
#Else
            ret = Native.TA_ExtendTrial(handle, useTrialFlags, trialExtension)
#End If

            If Not ret = TA_OK Then
                Throw taHresultToExcep(ret, "ExtendTrial")
            End If

            ' create operation for trial callback (if not already created)
            If _operation Is Nothing Then
                _operation = AsyncOperationManager.CreateOperation(Nothing)
            End If
        End Sub


        ''' <summary>This function allows you to set a custom folder to store the activation
        '''data files. For normal use we do Not recommend you use this function.
        '''
        '''Only use this function if you absolutely must store data into a separate
        '''folder. For example if your application runs on a USB drive And can't write
        '''any files to the main disk, then you can use this function to save the activation
        '''data files to a directory on the USB disk.
        '''
        '''If you are using this function (which we only recommend for very special use-cases)
        '''then you must call this function on every start of your program at the very top of
        '''your app before any other functions are called.
        '''
        '''The directory you pass in must already exist. And the process using TurboActivate
        '''must have permission to create, write, And delete files in that directory.</summary>
        ''' <param name="directory">The full directory to store the activation files.</param>
        Public Sub SetCustomActDataPath(directory As String)
            Dim ret As Integer

#If TA_BOTH_DLL Then
            ret = If(IntPtr.Size = 8, Native64.TA_SetCustomActDataPath(handle, directory), Native.TA_SetCustomActDataPath(handle, directory))
#Else
            ret = Native.TA_SetCustomActDataPath(handle, directory)
#End If

            If Not ret = TA_OK Then
                Throw taHresultToExcep(ret, "SetCustomActDataPath")
            End If
        End Sub

        ''' <summary>
        ''' Gets the version number of the currently used TurboActivate library.
        '''
        ''' This Is a useful alternative for platforms which don't support file meta-data
        ''' (Like Linux, FreeBSD, And other unix variants).
        ''' </summary>
        ''' <returns>Version class with the version number of the currently used TurboActivate library.</returns>
        Public Shared Function GetVersion() As Version
            Dim ret As Integer
            Dim major As UInteger = 0
            Dim minor As UInteger = 0
            Dim build As UInteger = 0
            Dim rev As UInteger = 0

#If TA_BOTH_DLL Then
            ret = If(IntPtr.Size = 8, Native64.TA_GetVersion(major, minor, build, rev), Native.TA_GetVersion(major, minor, build, rev))
#Else
            ret = Native.TA_GetVersion(major, minor, build, rev)
#End If

            If Not ret = TA_OK Then
                Throw taHresultToExcep(ret, "GetVersion")
            End If

            Return New Version(Int(major), Int(minor), Int(build), Int(rev))
        End Function
    End Class



    Public Class COMException
        Inherits TurboActivateException
        Public Sub New()
            MyBase.New("CoInitializeEx failed. Re-enable Windows Management Instrumentation (WMI) service. Contact your system admin for more information.")
        End Sub
    End Class

    Public Class AccountCanceledException
        Inherits TurboActivateException
        Public Sub New()
            MyBase.New("Can't activate because the LimeLM account is cancelled.")
        End Sub
    End Class

    Public Class PkeyRevokedException
        Inherits TurboActivateException
        Public Sub New()
            MyBase.New("The product key has been revoked.")
        End Sub
    End Class

    Public Class PkeyMaxUsedException
        Inherits TurboActivateException
        Public Sub New()
            MyBase.New("The product key has already been activated with the maximum number of computers.")
        End Sub
    End Class

    Public Class InternetException
        Inherits TurboActivateException
        ' More information here: https://wyday.com/limelm/help/faq/#internet-error
        Public Sub New()
            MyBase.New("Connection to the servers failed.")
        End Sub

        Public Sub New(message As String)
            MyBase.New(message)
        End Sub
    End Class

    Public Class InternetTimeoutException
        Inherits InternetException
        Public Sub New()
            MyBase.New("The connection to the server timed out because a long period of time elapsed since the last data was sent or received.")
        End Sub
    End Class

    Public Class InternetTLSException
        Inherits InternetException
        ' More information here: https://wyday.com/limelm/help/faq/#internet-error
        Public Sub New()
            MyBase.New("The secure connection to the activation servers failed due to a TLS or certificate error. More information here: https://wyday.com/limelm/help/faq/#internet-error")
        End Sub
    End Class

    Public Class InvalidProductKeyException
        Inherits TurboActivateException
        Public Sub New()
            MyBase.New("The product key is invalid or there's no product key.")
        End Sub
    End Class

    Public Class NotActivatedException
        Inherits TurboActivateException
        Public Sub New()
            MyBase.New("The product needs to be activated.")
        End Sub
    End Class

    Public Class ProductDetailsException
        Inherits TurboActivateException
        Public Sub New()
            MyBase.New("The product details file ""TurboActivate.dat"" failed to load. It's either missing or corrupt.")
        End Sub
    End Class

    Public Class InvalidHandleException
        Inherits TurboActivateException
        Public Sub New()
            MyBase.New("The handle is not valid. You must set a valid VersionGUID when constructing TurboActivate object.")
        End Sub
    End Class

    Public Class TrialDateCorruptedException
        Inherits TurboActivateException
        Public Sub New()
            MyBase.New("The trial data has been corrupted, using the oldest date possible.")
        End Sub
    End Class

    Public Class TrialExtUsedException
        Inherits TurboActivateException
        Public Sub New()
            MyBase.New("The trial extension has already been used.")
        End Sub
    End Class

    Public Class TrialExtExpiredException
        Inherits TurboActivateException
        Public Sub New()
            MyBase.New("The trial extension has expired.")
        End Sub
    End Class

    Public Class DateTimeException
        Inherits TurboActivateException
        Public Sub New()
            MyBase.New("The activation has expired or the system time has been tampered with. Ensure your time, timezone, and date settings are correct. After fixing them restart your computer.")
        End Sub
    End Class

    Public Class PermissionException
        Inherits TurboActivateException
        Public Sub New()
            MyBase.New("Insufficient system permission. Either start your process as an admin / elevated user or call the function again with the TA_USER flag.")
        End Sub
    End Class

    Public Class InvalidFlagsException
        Inherits TurboActivateException
        Public Sub New()
            MyBase.New("The flags you passed to the function were invalid (or missing). Flags like ""TA_SYSTEM"" and ""TA_USER"" are mutually exclusive -- you can only use one or the other.")
        End Sub
    End Class

    Public Class VirtualMachineException
        Inherits TurboActivateException
        Public Sub New()
            MyBase.New("The function failed because this instance of your program is running inside a virtual machine / hypervisor and you've prevented the function from running inside a VM.")
        End Sub
    End Class

    Public Class ExtraDataTooLongException
        Inherits TurboActivateException
        Public Sub New()
            MyBase.New("The ""extra data"" was too long. You're limited to 255 UTF-8 characters. Or, on Windows, a Unicode string that will convert into 255 UTF-8 characters or less.")
        End Sub
    End Class

    Public Class InvalidArgsException
        Inherits TurboActivateException
        Public Sub New()
            MyBase.New("The arguments passed to the function are invalid. Double check your logic.")
        End Sub
    End Class

    Public Class TurboFloatKeyException
        Inherits TurboActivateException
        Public Sub New()
            MyBase.New("The product key used is for TurboFloat Server, not TurboActivate.")
        End Sub
    End Class

    Public Class NoMoreDeactivationsException
        Inherits TurboActivateException
        Public Sub New()
            MyBase.New("No more deactivations are allowed for the product key. This product is still activated on this computer.")
        End Sub
    End Class

    Public Class EnableNetworkAdaptersException
        Inherits TurboActivateException
        ' More information here: https://wyday.com/limelm/help/faq/#disabled-adapters
        Public Sub New()
            MyBase.New("There are network adapters on the system that are disabled and TurboActivate couldn't read their hardware properties (even after trying and failing to enable the adapters automatically). Enable the network adapters, re-run the function, and TurboActivate will be able to ""remember"" the adapters even if the adapters are disabled in the future.")
        End Sub
    End Class

    Public Class AlreadyActivatedException
        Inherits TurboActivateException
        Public Sub New()
            MyBase.New("You can't use a product key because your app is already activated with a product key. To use a new product key, then first deactivate using either the Deactivate() or DeactivationRequestToFile().")
        End Sub
    End Class

    Public Class AlreadyVerifiedTrialException
        Inherits TurboActivateException
        Public Sub New()
            MyBase.New("The trial is already a verified trial. You need to use the ""TA_VERIFIED_TRIAL"" flag. Can't ""downgrade"" a verified trial to an unverified trial.")
        End Sub
    End Class

    Public Class TrialExpiredException
        Inherits TurboActivateException
        Public Sub New()
            MyBase.New("The verified trial has expired. You must request a trial extension from the company.")
        End Sub
    End Class

    Public Class NoMoreTrialsAllowedException
        Inherits TurboActivateException
        Public Sub New()
            MyBase.New("In the LimeLM account either the trial days is set to 0, OR the account is set to not auto-upgrade and thus no more verified trials can be made.")
        End Sub
    End Class

    Public Class MustSpecifyTrialTypeException
        Inherits TurboActivateException
        Public Sub New()
            MyBase.New("You must specify the trial type (TA_UNVERIFIED_TRIAL or TA_VERIFIED_TRIAL). And you can't use both flags. Choose one or the other. We recommend TA_VERIFIED_TRIAL.")
        End Sub
    End Class

    Public Class BrokenWMIException
        Inherits TurboActivateException
        Public Sub New()
            MyBase.New("The WMI repository on the computer is broken. To fix the WMI repository see the instructions here: https://wyday.com/limelm/help/faq/#fix-broken-wmi")
        End Sub
    End Class

    Public Class MustUseTrialException
        Inherits TurboActivateException
        Public Sub New()
            MyBase.New("You must call TA_UseTrial() before you can get the number of trial days remaining.")
        End Sub
    End Class

    Public Class TurboActivateException
        Inherits Exception
        Public Sub New(ByVal message As String)
            MyBase.New(message)
        End Sub
    End Class

    Public Enum IsGenuineResult
        ''' <summary>Is activated and genuine.</summary>
        Genuine = 0

        ''' <summary>Is activated and genuine and the features changed.</summary>
        GenuineFeaturesChanged = 1

        ''' <summary>Not genuine (note: use this in tandem with NotGenuineInVM).</summary>
        NotGenuine = 2

        ''' <summary>Not genuine because you're in a Virtual Machine.</summary>
        NotGenuineInVM = 3

        ''' <summary>Treat this error as a warning. That is, tell the user that the activation couldn't be validated with the servers and that they can manually recheck with the servers immediately.</summary>
        InternetError = 4
    End Enum
End Namespace
