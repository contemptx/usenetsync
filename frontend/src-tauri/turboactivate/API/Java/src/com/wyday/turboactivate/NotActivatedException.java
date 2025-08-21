package com.wyday.turboactivate;

public class NotActivatedException extends TurboActivateException
{
	public NotActivatedException()
	{
		super("The product needs to be activated.");
	}
}