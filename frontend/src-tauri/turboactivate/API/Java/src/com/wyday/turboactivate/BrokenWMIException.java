package com.wyday.turboactivate;

public class BrokenWMIException extends TurboActivateException
{
	public BrokenWMIException()
	{
		super("The WMI repository on the computer is broken. To fix the WMI repository see the instructions here: https://wyday.com/limelm/help/faq/#fix-broken-wmi");
	}
}