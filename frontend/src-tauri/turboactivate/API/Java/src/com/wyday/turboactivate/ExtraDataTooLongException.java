package com.wyday.turboactivate;

public class ExtraDataTooLongException extends TurboActivateException
{
	public ExtraDataTooLongException()
	{
		super("The \"extra data\" was too long. You're limited to 255 UTF-8 characters. Or, on Windows, a Unicode string that will convert into 255 UTF-8 characters or less.");
	}
}