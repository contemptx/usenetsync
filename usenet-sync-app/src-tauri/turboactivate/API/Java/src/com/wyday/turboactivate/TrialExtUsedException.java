package com.wyday.turboactivate;

public class TrialExtUsedException extends TurboActivateException
{
	public TrialExtUsedException()
	{
		super("The trial extension has already been used.");
	}
}