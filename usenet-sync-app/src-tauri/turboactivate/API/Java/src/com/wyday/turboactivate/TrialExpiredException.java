package com.wyday.turboactivate;

public class TrialExpiredException extends TurboActivateException
{
	public TrialExpiredException()
	{
		super("The verified trial has expired. You must request a trial extension from the company.");
	}
}