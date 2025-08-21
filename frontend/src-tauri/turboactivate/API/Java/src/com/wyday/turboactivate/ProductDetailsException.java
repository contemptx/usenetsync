package com.wyday.turboactivate;

public class ProductDetailsException extends TurboActivateException
{
	public ProductDetailsException()
	{
		super("The product details file \"TurboActivate.dat\" failed to load. It's either missing or corrupt.");
	}
}