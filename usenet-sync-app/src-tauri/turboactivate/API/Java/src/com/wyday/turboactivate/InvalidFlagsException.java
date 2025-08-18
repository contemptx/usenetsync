package com.wyday.turboactivate;

public class InvalidFlagsException extends TurboActivateException
{
	public InvalidFlagsException()
	{
		super("The flags you passed to the function were invalid (or missing). Flags like \"TA_SYSTEM\" and \"TA_USER\" are mutually exclusive -- you can only use one or the other.");
	}
}