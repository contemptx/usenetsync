package com.wyday.turboactivate;

public class NoMoreDeactivationsException extends TurboActivateException
{
	public NoMoreDeactivationsException()
	{
		super("No more deactivations are allowed for the product key. This product is still activated on this computer.");
	}
}