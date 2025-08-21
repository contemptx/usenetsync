package com.wyday.turboactivate;

public class VirtualMachineException extends TurboActivateException
{
	public VirtualMachineException()
	{
		super("The function failed because this instance of your program is running inside a virtual machine / hypervisor and you've prevented the function from running inside a VM.");
	}
}