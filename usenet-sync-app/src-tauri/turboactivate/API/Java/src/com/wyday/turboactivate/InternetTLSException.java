package com.wyday.turboactivate;

public class InternetTLSException extends TurboActivateException
{
	public InternetTLSException()
	{
		super("The secure connection to the activation servers failed due to a TLS or certificate error. More information here: https://wyday.com/limelm/help/faq/#internet-error");
	}
}