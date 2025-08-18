package com.wyday.turboactivate;

public class InternetTimeoutException extends TurboActivateException
{
	public InternetTimeoutException()
	{
		super("The connection to the server timed out because a long period of time elapsed since the last data was sent or received.");
	}
}