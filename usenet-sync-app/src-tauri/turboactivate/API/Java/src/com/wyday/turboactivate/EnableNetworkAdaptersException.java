package com.wyday.turboactivate;

public class EnableNetworkAdaptersException extends TurboActivateException
{
	public EnableNetworkAdaptersException()
	{
		super("There are network adapters on the system that are disabled and TurboActivate couldn't read their hardware properties (even after trying and failing to enable the adapters automatically). Enable the network adapters, re-run the function, and TurboActivate will be able to \"remember\" the adapters even if the adapters are disabled in the future.");
	}
}