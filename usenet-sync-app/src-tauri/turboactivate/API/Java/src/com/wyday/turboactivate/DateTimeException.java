package com.wyday.turboactivate;

public class DateTimeException extends TurboActivateException
{
	public DateTimeException(boolean either)
	{
		super(either ? "Either the activation response file has expired or your date and time settings are incorrect. Fix your date and time settings, restart your computer, and try to activate again." : "Failed because your system date and time settings are incorrect. Fix your date and time settings, restart your computer, and try to activate again.");
	}
}