package com.wyday.turboactivate;

public class PkeyRevokedException extends TurboActivateException
{
	public PkeyRevokedException()
	{
		super("The product key has been revoked.");
	}
}