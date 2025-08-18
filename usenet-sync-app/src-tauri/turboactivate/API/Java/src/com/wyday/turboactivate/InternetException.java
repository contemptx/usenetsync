package com.wyday.turboactivate;

public class InternetException extends TurboActivateException
{
	public InternetException()
	{
		super("Connection to the servers failed.");
	}
}