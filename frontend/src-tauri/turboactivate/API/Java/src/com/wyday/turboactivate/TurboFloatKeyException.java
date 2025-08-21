package com.wyday.turboactivate;

public class TurboFloatKeyException extends TurboActivateException
{
	public TurboFloatKeyException()
	{
		super("The product key used is for TurboFloat, not TurboActivate.");
	}
}