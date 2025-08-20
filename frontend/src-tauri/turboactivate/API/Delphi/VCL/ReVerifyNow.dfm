object frmReVerifyNow: TfrmReVerifyNow
  Left = 192
  Top = 107
  BorderIcons = [biSystemMenu]
  BorderStyle = bsDialog
  Caption = 'Re-verify with the activation servers'
  ClientHeight = 86
  ClientWidth = 405
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
  object lblDescr: TLabel
    Left = 8
    Top = 8
    Width = 385
    Height = 25
    Caption = 'You have X days to re-verify with the activation servers.'
  end
  object btnReverify: TButton
    Left = 16
    Top = 40
    Width = 105
    Height = 33
    Caption = 'Re-verify now'
    TabOrder = 0
    OnClick = btnReverifyClick
  end
  object btnExit: TButton
    Left = 248
    Top = 40
    Width = 145
    Height = 33
    Caption = 'Exit application'
    TabOrder = 1
    OnClick = btnExitClick
  end
end
