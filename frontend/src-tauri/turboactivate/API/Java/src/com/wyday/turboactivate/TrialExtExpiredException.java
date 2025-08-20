package com.wyday.turboactivate;

public class TrialExtExpiredException extends TurboActivateException
{
	public TrialExtExpiredException()
	{
		super("The trial extension has expired.");
	}
}