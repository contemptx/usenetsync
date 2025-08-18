object Form1: TForm1
  Left = 284
  Top = 713
  BorderIcons = [biSystemMenu, biMinimize]
  BorderStyle = bsSingle
  Caption = 'Text Editor Plus'
  ClientHeight = 194
  ClientWidth = 441
  Color = clBtnFace
  Font.Charset = DEFAULT_CHARSET
  Font.Color = clWindowText
  Font.Height = -11
  Font.Name = 'Tahoma'
  Font.Style = []
  Menu = MainMenu1
  OldCreateOrder = False
  Position = poScreenCenter
  OnCreate = FormCreate
  PixelsPerInch = 96
  TextHeight = 13
  object lblTrialMessage: TLabel
    Left = 8
    Top = 161
    Width = 110
    Height = 13
    Caption = 'Your trial expires in'
    Font.Charset = DEFAULT_CHARSET
    Font.Color = clWindowText
    Font.Height = -11
    Font.Name = 'Tahoma'
    Font.Style = [fsBold]
    ParentFont = False
    Visible = False
  end
  object txtMain: TMemo
    Left = 8
    Top = 8
    Width = 425
    Height = 145
    ScrollBars = ssVertical
    TabOrder = 0
  end
  object btnExtendTrial: TButton
    Left = 344
    Top = 160
    Width = 89
    Height = 25
    Caption = 'Extend trial'
    TabOrder = 1
    OnClick = btnExtendTrialClick
  end
  object MainMenu1: TMainMenu
    Top = 16
    object File1: TMenuItem
      Caption = 'File'
      object New1: TMenuItem
        Caption = 'New'
      end
    end
    object Help1: TMenuItem
      Caption = 'Help'
      object Helpcontents1: TMenuItem
        Caption = 'Help contents'
      end
      object mnuActDeact: TMenuItem
        Caption = 'Deactivate...'
        OnClick = mnuActDeactClick
      end
    end
  end
end
