package com.wyday.turboactivate;

public class InvalidProductKeyException extends TurboActivateException
{
	public InvalidProductKeyException()
	{
		super("The product key is invalid or there's no product key.");
	}
}