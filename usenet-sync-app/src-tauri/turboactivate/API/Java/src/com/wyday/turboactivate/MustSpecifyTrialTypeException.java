package com.wyday.turboactivate;

public class MustSpecifyTrialTypeException extends TurboActivateException
{
	public MustSpecifyTrialTypeException()
	{
		super("You must specify the trial type (TA_UNVERIFIED_TRIAL or TA_VERIFIED_TRIAL). And you can't use both flags. Choose one or the other. We recommend TA_VERIFIED_TRIAL.");
	}
}