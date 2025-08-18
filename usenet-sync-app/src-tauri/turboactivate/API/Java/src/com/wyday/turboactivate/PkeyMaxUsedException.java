package com.wyday.turboactivate;

public class PkeyMaxUsedException extends TurboActivateException
{
	public PkeyMaxUsedException()
	{
		super("The product key has already been activated with the maximum number of computers.");
	}
}