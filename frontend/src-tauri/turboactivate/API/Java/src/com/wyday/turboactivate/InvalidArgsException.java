package com.wyday.turboactivate;

public class InvalidArgsException extends TurboActivateException
{
	public InvalidArgsException()
	{
		super("The arguments passed to the function are invalid. Double check your logic.");
	}
}