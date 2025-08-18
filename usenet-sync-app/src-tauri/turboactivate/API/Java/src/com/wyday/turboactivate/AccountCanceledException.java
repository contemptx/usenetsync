package com.wyday.turboactivate;

public class AccountCanceledException extends TurboActivateException
{
	public AccountCanceledException()
	{
		super("Can't activate because the LimeLM account is cancelled.");
	}
}