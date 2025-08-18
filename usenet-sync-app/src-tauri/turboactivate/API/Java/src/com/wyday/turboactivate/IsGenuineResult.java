package com.wyday.turboactivate;

import java.util.EnumSet;
import java.util.HashMap;
import java.util.Map;

public enum IsGenuineResult
{
	/**
	* Is activated and genuine.
	*/
	Genuine(0),

	/**
	* Is activated and genuine and the features changed.
	*/
	GenuineFeaturesChanged(1),

	/**
	* Not genuine (note: use this in tandem with NotGenuineInVM).
	*/
	NotGenuine(2),

	/**
	* Not genuine because you're in a Virtual Machine.
	*/
	NotGenuineInVM(3),

	/**
	* Treat this error as a warning. That is, tell the user that the activation couldn't be validated with the servers and that they can manually recheck with the servers immediately.
	*/
	InternetError(4);

	private static final Map<Integer, IsGenuineResult> lookup = new HashMap<Integer, IsGenuineResult>();

	static
	{
		for (IsGenuineResult s : EnumSet.allOf(IsGenuineResult.class))
			lookup.put(s.getCode(), s);
	}

	private int code;

	private IsGenuineResult(int code)
	{
		this.code = code;	
	}

	public int getCode() { return code; }

	public static IsGenuineResult get(int code)
	{ 
		return lookup.get(code); 
	}
};