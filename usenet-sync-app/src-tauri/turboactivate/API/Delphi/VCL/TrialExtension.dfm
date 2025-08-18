object frmTrialExtension: TfrmTrialExtension
  Left = 208
  Top = 667
  ActiveControl = txtExtension
  BorderIcons = [biSystemMenu]
  BorderStyle = bsDialog
  Caption = 'Trial extension'
  ClientHeight = 166
  ClientWidth = 311
  Color = clBtnFace
  Font.Charset = DEFAULT_CHARSET
  Font.Color = clWindowText
  Font.Height = -11
  Font.Name = 'MS Sans Serif'
  Font.Style = []
  OldCreateOrder = False
  Position = poOwnerFormCenter
  PixelsPerInch = 96
  TextHeight = 13
  object Label1: TLabel
    Left = 8
    Top = 8
    Width = 144
    Height = 13
    Caption = 'Paste your trial extension here:'
  end
  object btnOK: TButton
    Left = 144
    Top = 136
    Width = 75
    Height = 25
    Caption = 'OK'
    TabOrder = 0
    OnClick = btnOKClick
  end
  object btnCancel: TButton
    Left = 224
    Top = 136
    Width = 75
    Height = 25
    Caption = 'Cancel'
    ModalResult = 2
    TabOrder = 1
    OnClick = btnCancelClick
  end
  object txtExtension: TMemo
    Left = 8
    Top = 32
    Width = 289
    Height = 97
    ScrollBars = ssVertical
    TabOrder = 2
  end
end
