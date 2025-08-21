package com.wyday.turboactivate;

public class MustUseTrialException extends TurboActivateException
{
	public MustUseTrialException()
	{
		super("You must call TA_UseTrial() before you can get the number of trial days remaining.");
	}
}