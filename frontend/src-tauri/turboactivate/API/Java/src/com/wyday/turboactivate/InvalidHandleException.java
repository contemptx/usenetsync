package com.wyday.turboactivate;

public class InvalidHandleException extends TurboActivateException
{
	public InvalidHandleException()
	{
		super("The handle is not valid. You must set the VersionGUID property.");
	}
}