package com.wyday.turboactivate;

public class TrialDateCorruptedException extends TurboActivateException
{
	public TrialDateCorruptedException()
	{
		super("The trial data has been corrupted, using the oldest date possible.");
	}
}