package com.wyday.turboactivate;

public class PermissionException extends TurboActivateException
{
	public PermissionException()
	{
		super("Insufficient system permission. Either start your process as an admin / elevated user or call the function again with the TA_USER flag.");
	}
}