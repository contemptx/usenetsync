package com.wyday.turboactivate;

public class COMException extends TurboActivateException
{
	public COMException()
	{
		super("CoInitializeEx failed. Re-enable Windows Management Instrumentation (WMI) service. Contact your system admin for more information.");
	}
}