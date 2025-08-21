package com.wyday.turboactivate;

import com.sun.jna.Library;
import com.sun.jna.Native;
import com.sun.jna.Platform;
import com.sun.jna.Structure;
import com.sun.jna.WString;
import com.sun.jna.Callback;
import com.sun.jna.ptr.*;
import java.io.File;
import java.io.UnsupportedEncodingException;
import java.nio.ByteBuffer;
import java.nio.CharBuffer;
import java.util.Arrays;
import java.util.List;
import java.util.ArrayList;

public class TurboActivate
{
	private static String TurboActivateFolder;

	private String VersionGUID;
	private int handle = 0;
	private TurboActivateNative.TrialCallbackType callback = null;

	// Our collection of classes that are subscribed as listeners of our
	// callback event from TurboActivate.
	protected ArrayList<TrialChangeEvent> _listeners;

	public static final int TA_SYSTEM = 1;
	public static final int TA_USER = 2;

	/**
	 * Use the TA_DISALLOW_VM in UseTrial() to disallow trials in virtual machines.
	 * If you use this flag in UseTrial() and the customer's machine is a Virtual
	 * Machine, then UseTrial() will throw VirtualMachineException.
	 */
	public static final int TA_DISALLOW_VM = 4;

	/**
	 * Use this flag in TA_UseTrial() to tell TurboActivate to use client-side
	 * unverified trials. For more information about verified vs. unverified trials,
	 * see here: https://wyday.com/limelm/help/trials/
	 * Note: unverified trials are unsecured and can be reset by malicious customers.
	 */
	public static final int TA_UNVERIFIED_TRIAL = 16;

	/**
	 * Use the TA_VERIFIED_TRIAL flag to use verified trials instead
	 * of unverified trials. This means the trial is locked to a particular computer.
	 * The customer can't reset the trial.
	 */
	public static final int TA_VERIFIED_TRIAL = 32;


	public static final int TA_HAS_NOT_EXPIRED = 1;
	

	/**
	 * Callback-status value used when the trial has expired.
	 */
	public static final int TA_CB_EXPIRED = 0;

	/**
	 * Callback-status value used when the trial has expired due to date/time fraud.
	 */
	public static final int TA_CB_EXPIRED_FRAUD = 1;


	/**
	 * Creates a new TurboActivate instance.
	 * 
	 * @param vGuid The Version GUID you get from the LimeLM.
	 * @throws TurboActivateException
	 */
	public TurboActivate(String vGuid) throws TurboActivateException
	{
		SetPDetsLocation();
		setVersionGUID(vGuid);
	}

	/**
	 * Creates a new TurboActivate instance.
	 * 
	 * @param vGuid The Version GUID you get from the LimeLM.
	 * @param tfFolder The location of the folder that contains the TurboActivate.dat file and all the native binary subfolders (like. "win-x86", etc.)
	 * @throws TurboActivateException
	 */
	public TurboActivate(String vGuid, String tfFolder) throws TurboActivateException
	{
		if (tfFolder != null)
			SetTurboActivateFolder(tfFolder);

		SetPDetsLocation();
		setVersionGUID(vGuid);
	}

	/**
	 * Creates a new TurboActivate instance.
	 * 
	 * @param vGuid The Version GUID you get from the LimeLM.
	 * @param tfFolder The location of the folder that contains all the native binary subfolders (like. "win-x86", etc.)
	 * @param pdetsData The TurboActivate.dat file loaded into a byte array.
	 * @throws TurboActivateException
	 */
	public TurboActivate(String vGuid, String tfFolder, byte[] pdetsData) throws TurboActivateException
	{
		if (tfFolder != null)
			SetTurboActivateFolder(tfFolder);

		// load the TurboActivate.dat from the byte array
		switch (TurboActivateNative.INSTANCE.TA_PDetsFromByteArray(pdetsData, pdetsData.length))
		{
			case 0: // successful
				break;
			case 0x08: // TA_E_PDETS
				throw new ProductDetailsException();
			case 0x01: // TA_FAIL
				// the TurboActivate.dat already loaded.
				break;
			default:
				throw new TurboActivateException("The TurboActivate.dat file failed to load.");
		}

		setVersionGUID(vGuid);
	}

	
	private static TurboActivateException taHresultToExcep(int ret, String funcName)
	{
		switch (ret)
		{
			case 0x01: // TA_FAIL
				return new TurboActivateException(funcName + " general failure.");
			case 0x02: // TA_E_PKEY
				return new InvalidProductKeyException();
			case 0x03: // TA_E_ACTIVATE
				return new NotActivatedException();
			case 0x04: // TA_E_INET
				return new InternetException();
			case 0x05: // TA_E_INUSE
				return new PkeyMaxUsedException();
			case 0x06: // TA_E_REVOKED
				return new PkeyRevokedException();
			case 0x09: // TA_E_TRIAL
				return new TrialDateCorruptedException();
			case 0x0B: // TA_E_COM
				return new COMException();
			case 0x0C: // TA_E_TRIAL_EUSED
				return new TrialExtUsedException();
			case 0x0D: // TA_E_EXPIRED
				return new DateTimeException(false);
			case 0x0F: // TA_E_PERMISSION
				return new PermissionException();
			case 0x10: // TA_E_INVALID_FLAGS
				return new InvalidFlagsException();
			case 0x11: // TA_E_IN_VM
				return new VirtualMachineException();
			case 0x12: // TA_E_EDATA_LONG
				return new ExtraDataTooLongException();
			case 0x13: // TA_E_INVALID_ARGS
				return new InvalidArgsException();
			case 0x14: // TA_E_KEY_FOR_TURBOFLOAT
				return new TurboFloatKeyException();
			case 0x18: // TA_E_NO_MORE_DEACTIVATIONS
				return new NoMoreDeactivationsException();
			case 0x19: // TA_E_ACCOUNT_CANCELED
				return new AccountCanceledException();
			case 0x1A: // TA_E_ALREADY_ACTIVATED
				return new AlreadyActivatedException();
			case 0x1B: // TA_E_INVALID_HANDLE
				return new InvalidHandleException();
			case 0x1C: // TA_E_ENABLE_NETWORK_ADAPTERS
				return new EnableNetworkAdaptersException();
			case 0x1D: // TA_E_ALREADY_VERIFIED_TRIAL
				return new AlreadyVerifiedTrialException();
			case 0x1E: // TA_E_TRIAL_EXPIRED
				return new TrialExpiredException();
			case 0x1F: // TA_E_MUST_SPECIFY_TRIAL_TYPE
				return new MustSpecifyTrialTypeException();
			case 0x20: // TA_E_MUST_USE_TRIAL
				return new MustUseTrialException();
			case 0x21: // TA_E_NO_MORE_TRIALS_ALLOWED
				return new NoMoreTrialsAllowedException();
			case 0x22: // TA_E_BROKEN_WMI
				return new BrokenWMIException();
			case 0x23: // TA_E_INET_TIMEOUT
				return new InternetTimeoutException();
			case 0x24: // TA_E_INET_TLS
				return new InternetTLSException();
			default:

				// Make sure you're using the latest TurboActivate.java, we occassionally add new error codes
				// and you need latest version of this file to get a detailed description of the error.

				// More information about upgrading here: https://wyday.com/limelm/help/faq/#update-libs

				// You can also view error directly from the source: TurboActivate.h
				return new TurboActivateException(funcName + " failed with an unknown error code: " + ret);
		}
	}
	
	
	private void setVersionGUID(String vGuid) throws TurboActivateException
	{
		if (handle != 0)
			throw new TurboActivateException("There's already a VersionGUID associated with this TurboActivate instance.");

		VersionGUID = vGuid;

		if (Platform.isWindows())
			handle = TurboActivateNative.INSTANCE.TA_GetHandle(new WString(VersionGUID));
		else
			handle = TurboActivateNative.INSTANCE.TA_GetHandle(VersionGUID);

		// if the handle is still unset then immediately throw an exception
		// telling the user that they need to actually load the correct
		// TurboActivate.dat and/or use the correct GUID for the TurboActivate.dat
		if (handle == 0)
			throw new ProductDetailsException();
	}

	public String getVersionGUID()
	{
		return VersionGUID;
	}

	// Method for listener classes to register themselves
	public void addTrialChangeListener(TrialChangeEvent listener) throws TurboActivateException
	{
		if (_listeners == null)
			_listeners = new ArrayList<>();

		_listeners.add(listener);

		if (callback == null)
		{
			// create the native callback handler, and prevent
			// garbage collection of the callback by storing it
			// as a member of this TurboActivate class
			callback = new TurboActivateNative.TrialCallbackType()
				{
					public void invoke(int status)
					{
						for (TrialChangeEvent evt : _listeners)
							evt.TrialChange(status);
					}
				};

			// tell TurboActivate about the native callback handler
			switch (TurboActivateNative.INSTANCE.TA_SetTrialCallback(handle, callback))
			{
				case 0x1B: // TA_E_INVALID_HANDLE
					throw new InvalidHandleException();
				case 0: // successful
					break;
				default:
					throw new TurboActivateException("Failed to save trial callback.");
			}
		}
	}

	/**
	 * Activates the product on this computer. You must call {@link #CheckAndSavePKey(String)} with a valid product key or have used the TurboActivate wizard sometime before calling this function.
	 * 
	 * @throws TurboActivateException
	 */
	public void Activate() throws TurboActivateException
	{
		Activate(null);
	}

	/**
	 * Activates the product on this computer. You must call {@link #CheckAndSavePKey(String)} with a valid product key or have used the TurboActivate wizard sometime before calling this function.
	 * 
	 * @param extraData Extra data to pass to the LimeLM servers that will be visible for you to see and use. Maximum size is 255 UTF-8 characters.
	 * @throws TurboActivateException
	 */
	public void Activate(String extraData) throws TurboActivateException
	{
		int ret;
		if (Platform.isWindows())
		{
			TurboActivateNative.W_ACTIVATE_OPTIONS opts = null;

			if (extraData != null)
			{
				opts = new TurboActivateNative.W_ACTIVATE_OPTIONS();
				opts.nLength = opts.size();
				opts.sExtraData = new WString(extraData);
			}

			ret = TurboActivateNative.INSTANCE.TA_Activate(handle, opts);
		}
		else
		{
			TurboActivateNative.ACTIVATE_OPTIONS opts = null;

			if (extraData != null)
			{
				opts = new TurboActivateNative.ACTIVATE_OPTIONS();
				opts.nLength = opts.size();
				opts.sExtraData = extraData;
			}

			ret = TurboActivateNative.INSTANCE.TA_Activate(handle, opts);
		}

		if (ret != 0) // TA_OK
			throw taHresultToExcep(ret, "Activate");
	}

	/**
	 * Get the "activation request" file for offline activation. You must call {@link #CheckAndSavePKey(String)} with a valid product key or have used the TurboActivate wizard sometime before calling this function.
	 * 
	 * @param filename The location where you want to save the activation request file.
	 * @throws TurboActivateException
	 */
	public void ActivationRequestToFile(String filename) throws TurboActivateException
	{
		ActivationRequestToFile(filename, null);
	}

	/**
	 * Get the "activation request" file for offline activation. You must call {@link #CheckAndSavePKey(String)} with a valid product key or have used the TurboActivate wizard sometime before calling this function.
	 * 
	 * @param filename The location where you want to save the activation request file.
	 * @param extraData Extra data to pass to the LimeLM servers that will be visible for you to see and use. Maximum size is 255 UTF-8 characters.
	 * @throws TurboActivateException
	 */
	public void ActivationRequestToFile(String filename, String extraData) throws TurboActivateException
	{
		int ret;
		if (Platform.isWindows())
		{
			TurboActivateNative.W_ACTIVATE_OPTIONS opts = null;

			if (extraData != null)
			{
				opts = new TurboActivateNative.W_ACTIVATE_OPTIONS();
				opts.nLength = opts.size();
				opts.sExtraData = new WString(extraData);
			}

			ret = TurboActivateNative.INSTANCE.TA_ActivationRequestToFile(handle, new WString(filename), opts);
		}
		else
		{
			TurboActivateNative.ACTIVATE_OPTIONS opts = null;

			if (extraData != null)
			{
				opts = new TurboActivateNative.ACTIVATE_OPTIONS();
				opts.nLength = opts.size();
				opts.sExtraData = extraData;
			}

			ret = TurboActivateNative.INSTANCE.TA_ActivationRequestToFile(handle, filename, opts);
		}

		if (ret != 0) // TA_OK
			throw taHresultToExcep(ret, "ActivationRequestToFile");
	}

	/**
	 * Activate from the "activation response" file for offline activation.
	 * 
	 * @param filename The location of the activation response file.
	 * @throws TurboActivateException
	 */
	public void ActivateFromFile(String filename) throws TurboActivateException
	{
		int ret;

		if (Platform.isWindows())
			ret = TurboActivateNative.INSTANCE.TA_ActivateFromFile(handle, new WString(filename));
		else
			ret = TurboActivateNative.INSTANCE.TA_ActivateFromFile(handle, filename);

		if (ret != 0) // TA_OK
			throw taHresultToExcep(ret, "ActivateFromFile");
	}

	/**
	 * Checks and saves the product key.
	 * 
	 * @param productKey The product key you want to save.
	 * @return           True if the product key is valid, false if it's not
	 * @throws TurboActivateException
	 */
	public boolean CheckAndSavePKey(String productKey) throws TurboActivateException
	{
		return CheckAndSavePKey(productKey, TA_SYSTEM);
	}

	/**
	 * Checks and saves the product key.
	 * 
	 * @param productKey The product key you want to save.
	 * @param flags		 Whether to create the activation either user-wide or system-wide. Valid flags are {@link #TA_SYSTEM} and {@link #TA_USER}.
	 * @return           True if the product key is valid, false if it's not
	 * @throws TurboActivateException
	 */
	public boolean CheckAndSavePKey(String productKey, int flags) throws TurboActivateException
	{
		int ret;

		if (Platform.isWindows())
			ret = TurboActivateNative.INSTANCE.TA_CheckAndSavePKey(handle, new WString(productKey), flags);
		else
			ret = TurboActivateNative.INSTANCE.TA_CheckAndSavePKey(handle, productKey, flags);

		switch (ret)
		{
			case 0: // TA_OK, successful
				return true;
			case 1: // TA_FAIL, not successful
				return false;
			default:
				throw taHresultToExcep(ret, "CheckAndSavePKey");
		}
	}

	/**
	 * Deactivates the product on this computer.
	 * @throws TurboActivateException
	 */
	public void Deactivate() throws TurboActivateException
	{
		Deactivate(false);
	}

	/**
	 * Deactivates the product on this computer.
	 * 
	 * @param eraseProductKey Erase the product key so the user will have to enter a new product key if they wish to reactivate.
	 * @throws TurboActivateException
	 */
	public void Deactivate(boolean eraseProductKey) throws TurboActivateException
	{
		int ret = TurboActivateNative.INSTANCE.TA_Deactivate(handle, (byte)(eraseProductKey ? 1 : 0));

		if (ret != 0) // TA_OK
			throw taHresultToExcep(ret, "Deactivate");
	}

	/**
	 * Get the "deactivation request" file for offline deactivation.
	 * 
	 * @param filename The location where you want to save the deactivation request file.
	 * @param eraseProductKey Erase the product key so the user will have to enter a new product key if they wish to reactivate.
	 * @throws TurboActivateException
	 */
	public void DeactivationRequestToFile(String filename, boolean eraseProductKey) throws TurboActivateException
	{
		int ret;

		if (Platform.isWindows())
			ret = TurboActivateNative.INSTANCE.TA_DeactivationRequestToFile(handle, new WString(filename), (byte)(eraseProductKey ? 1 : 0));
		else
			ret = TurboActivateNative.INSTANCE.TA_DeactivationRequestToFile(handle, filename, (byte)(eraseProductKey ? 1 : 0));

		if (ret != 0) // TA_OK
			throw taHresultToExcep(ret, "DeactivationRequestToFile");
	}

	/**
	 * Gets the extra data value you passed in when activating.
	 * 
	 * @return            Returns the extra data set using ActivateEx() or null is no data was set.
	 * @throws TurboActivateException
	 * @throws UnsupportedEncodingException
	 */
	public String GetExtraData() throws TurboActivateException, UnsupportedEncodingException
	{
		int ret;

		if (Platform.isWindows())
		{
			ret = TurboActivateNative.INSTANCE.TA_GetExtraData(handle, (CharBuffer)null, 0);
			CharBuffer buf = CharBuffer.allocate(ret);
			ret = TurboActivateNative.INSTANCE.TA_GetExtraData(handle, buf, ret);

			if (ret == 0)
				return buf.toString().trim();
		}
		else
		{
			ret = TurboActivateNative.INSTANCE.TA_GetExtraData(handle, (ByteBuffer)null, 0);
			ByteBuffer buf = ByteBuffer.allocate(ret);
			ret = TurboActivateNative.INSTANCE.TA_GetExtraData(handle, buf, ret);

			if (ret == 0)
				return new String(buf.array(), "UTF-8").trim();
		}

		switch (ret)
		{
			case 0x1B: // TA_E_INVALID_HANDLE
				throw new InvalidHandleException();
			default:
				return null;
		}
	}

	/**
	 * Gets the value of a feature.
	 * 
	 * @param featureName The name of the feature to retrieve the value for.
	 * @return            Returns the feature value.
	 * @throws TurboActivateException
	 * @throws UnsupportedEncodingException
	 */
	public String GetFeatureValue(String featureName) throws TurboActivateException, UnsupportedEncodingException
	{
		String value = GetFeatureValue(featureName, null);

		if (value == null)
			throw new TurboActivateException("Failed to get feature value. The feature doesn't exist.");

		return value;
	}

	/**
	 * Gets the value of a feature.
	 * 
	 * @param featureName The name of the feature to retrieve the value for.
	 * @param defaultValue The default value to return if the feature doesn't exist.
	 * @return            Returns the feature value.
	 * @throws TurboActivateException
	 * @throws UnsupportedEncodingException
	 */
	public String GetFeatureValue(String featureName, String defaultValue) throws TurboActivateException, UnsupportedEncodingException
	{
		int ret;

		if (Platform.isWindows())
		{
			ret = TurboActivateNative.INSTANCE.TA_GetFeatureValue(handle, new WString(featureName), null, 0);

			// the ret value is the length needed to store the value
			CharBuffer buf = CharBuffer.allocate(ret);

			ret = TurboActivateNative.INSTANCE.TA_GetFeatureValue(handle, new WString(featureName), buf, ret);

			if (ret == 0)
				return buf.toString().trim();
		}
		else
		{
			ret = TurboActivateNative.INSTANCE.TA_GetFeatureValue(handle, featureName, null, 0);

			// the ret value is the length needed to store the value
			ByteBuffer buf = ByteBuffer.allocate(ret);

			ret = TurboActivateNative.INSTANCE.TA_GetFeatureValue(handle, featureName, buf, ret);

			if (ret == 0)
				return new String(buf.array(), "UTF-8").trim();
		}

		switch (ret)
		{
			case 0x1B: // TA_E_INVALID_HANDLE
				throw new InvalidHandleException();
			default:
				return defaultValue;
		}
	}

	/**
	 * Gets the stored product key. NOTE: if you want to check if a product key is valid simply call {@link #IsProductKeyValid()}.
	 * 
	 * @return            Returns the product key.
	 * @throws TurboActivateException
	 * @throws UnsupportedEncodingException
	 */
	public String GetPKey() throws TurboActivateException, UnsupportedEncodingException
	{
		// this makes the assumption that the PKey is 34+NULL characters long.
		// This may or may not be true in the future.

		int ret;

		if (Platform.isWindows())
		{
			CharBuffer buf = CharBuffer.allocate(35);
			ret = TurboActivateNative.INSTANCE.TA_GetPKey(handle, buf, 35);

			if (ret == 0)
				return buf.toString().trim();
		}
		else
		{
			ByteBuffer buf = ByteBuffer.allocate(35);
			ret = TurboActivateNative.INSTANCE.TA_GetPKey(handle, buf, 35);

			if (ret == 0)
				return new String(buf.array(), "UTF-8").trim();
		}

		switch (ret)
		{
			case 2: // TA_E_PKEY
				throw new InvalidProductKeyException();
			case 0x1B: // TA_E_INVALID_HANDLE
				throw new InvalidHandleException();
			default:
				throw new TurboActivateException("Failed to get the product key.");
		}
	}

	/**
	 * Checks whether the computer has been activated.
	 * 
	 * @return            True if the computer is activated. False otherwise.
	 * @throws TurboActivateException
	 */
	public boolean IsActivated() throws TurboActivateException
	{
		int ret = TurboActivateNative.INSTANCE.TA_IsActivated(handle);

		switch (ret)
		{
			case 0: // TA_OK, is activated
				return true;
			case 1: // TA_FAIL, not activated
				return false;
			default:
				throw taHresultToExcep(ret, "IsActivated");
		}
	}

	/**
	 * Checks if the string in the form "YYYY-MM-DD HH:mm:ss" is a valid date/time. The date must be in UTC time and "24-hour" format. If your date is in some other time format first convert it to UTC time before passing it into this function.
	 * 
	 * @param date_time The date time string to check.
	 * @param flags		 The type of date time check. Valid flags are {@link #TA_HAS_NOT_EXPIRED}.
	 * @return           True if the date is valid, false if it's not
	 * @throws TurboActivateException
	 */
	public boolean IsDateValid(String date_time, int flags) throws TurboActivateException
	{
		int ret;

		if (Platform.isWindows())
			ret = TurboActivateNative.INSTANCE.TA_IsDateValid(handle, new WString(date_time), flags);
		else
			ret = TurboActivateNative.INSTANCE.TA_IsDateValid(handle, date_time, flags);

		switch (ret)
		{
			case 0: // TA_OK, date is valid and not expired
				return true;
			case 1: // TA_FAIL, date is invalid or not expired
				return false;
			default:
				throw taHresultToExcep(ret, "IsDateValid");
		}
	}

	/**
	 * Checks whether the computer is genuinely activated by verifying with the LimeLM servers.
	 * 
	 * @return            IsGenuineResult
	 * @throws TurboActivateException
	 */
	public IsGenuineResult IsGenuine() throws TurboActivateException
	{
		int ret = TurboActivateNative.INSTANCE.TA_IsGenuine(handle);

		switch (ret)
		{
			case 0: // TA_OK, is activated
				return IsGenuineResult.Genuine;

			case 22: // TA_E_FEATURES_CHANGED
				return IsGenuineResult.GenuineFeaturesChanged;

			case 4: // TA_E_INET
				return IsGenuineResult.InternetError;

			case 1: // TA_FAIL
			case 0x06: // TA_E_REVOKED
			case 0x03: // TA_E_ACTIVATE
				return IsGenuineResult.NotGenuine;

			case 17: // TA_E_IN_VM
				return IsGenuineResult.NotGenuineInVM;

			default:
				throw taHresultToExcep(ret, "IsGenuine");
		}
	}

	/**
	 * Checks whether the computer is activated, and every "daysBetweenChecks" days it check if the customer is genuinely activated by verifying with the LimeLM servers.
	 * 
	 * @param daysBetweenChecks How often to contact the LimeLM servers for validation. 90 days recommended.
	 * @param graceDaysOnInetErr If the call fails because of an internet error, how long, in days, should the grace period last (before returning deactivating and returning TA_FAIL).
	 * 
	 * 14 days is recommended.
	 * @param skipOffline If the user activated using offline activation 
	 * (ActivateRequestToFile(), ActivateFromFile() ), then with this
	 * option IsGenuineEx() will still try to validate with the LimeLM
	 * servers, however instead of returning {@link #IsGenuineResult.InternetError} (when within the
	 * grace period) or {@link #IsGenuineResult.NotGenuine} (when past the grace period) it will
	 * instead only return {@link #IsGenuineResult.Genuine} (if IsActivated()).
	 * 
	 * If the user activated using online activation then this option
	 * is ignored.
	 * @param offlineShowInetErr If the user activated using offline activation, and you're
	 * using this option in tandem with skipOffline, then IsGenuineEx()
	 * will return {@link #IsGenuineResult.InternetError} on internet failure instead of {@link #IsGenuineResult.Genuine}.
	 *
	 * If the user activated using online activation then this flag
	 * is ignored.
	 * 
	 * @return            IsGenuineResult
	 * @throws TurboActivateException
	 */
	public IsGenuineResult IsGenuine(int daysBetweenChecks, int graceDaysOnInetErr, Boolean skipOffline, Boolean offlineShowInetErr) throws TurboActivateException
	{
		TurboActivateNative.GENUINE_OPTIONS opts = new TurboActivateNative.GENUINE_OPTIONS();
		opts.nLength = opts.size();
		opts.nDaysBetweenChecks = daysBetweenChecks;
		opts.nGraceDaysOnInetErr = graceDaysOnInetErr;
		opts.flags = 0;

		if (skipOffline)
		{
			opts.flags |= TurboActivateNative.TA_SKIP_OFFLINE;

			if (offlineShowInetErr)
				opts.flags |= TurboActivateNative.TA_OFFLINE_SHOW_INET_ERR;
		}

		int ret =  TurboActivateNative.INSTANCE.TA_IsGenuineEx(handle, opts);

		switch (ret)
		{
			case 0: // TA_OK, is activated and/or Genuine
				return IsGenuineResult.Genuine;

			case 22: // TA_E_FEATURES_CHANGED
				return IsGenuineResult.GenuineFeaturesChanged;

			case 4: // TA_E_INET
			case 0x15: // TA_E_INET_DELAYED
				return IsGenuineResult.InternetError;

			case 1: // TA_FAIL
			case 0x06: // TA_E_REVOKED
			case 0x03: // TA_E_ACTIVATE
				return IsGenuineResult.NotGenuine;

			case 17: // TA_E_IN_VM
				return IsGenuineResult.NotGenuineInVM;

			default:
				throw taHresultToExcep(ret, "IsGenuineEx");
		}
	}

	/**
	 * Get the number of days until the next time that the {@link #IsGenuine(int, int, Boolean, Boolean)} function contacts the LimeLM activation servers to reverify the activation.
	 * 
	 * @param daysBetweenChecks How often to contact the LimeLM servers for validation. Use the exact same value as used in {@link #IsGenuine(int, int, Boolean, Boolean)}.
	 * @param graceDaysOnInetErr If the call fails because of an internet error, how long, in days, should the grace period last (before returning deactivating and returning TA_FAIL). Again, use the exact same value as used in {@link #IsGenuine(int, int, bool, bool)}.
	 * @param inGracePeriod Get whether the user is in the grace period.
	 * 
	 * @return The number of days remaining. 0 days if both the days between checks and the grace period have expired. (E.g. 1 day means *at most* 1 day. That is, it could be 30 seconds.)
	 * @throws TurboActivateException
	 */
	public int GenuineDays(int daysBetweenChecks, int graceDaysOnInetErr, BoolRef inGracePeriod) throws TurboActivateException
	{
		IntByReference daysRemain = new IntByReference(0);
		ByteByReference inGrace = new ByteByReference((byte)0);

		int ret = TurboActivateNative.INSTANCE.TA_GenuineDays(handle, daysBetweenChecks, graceDaysOnInetErr, daysRemain, inGrace);

		if (ret != 0) // TA_OK
			throw taHresultToExcep(ret, "GenuineDays");

		// set whether we're in a grace period or not
		inGracePeriod.setValue(inGrace.getValue() == (byte)1);

		return daysRemain.getValue();
	}

	/**
	 * Checks if the product key installed for this product is valid. This does NOT check if the product key is activated or genuine. Use {@link #IsActivated()} and {@link #IsGenuine(BoolRef)} instead.
	 * 
	 * @return            True if the product key is valid.
	 * @throws TurboActivateException
	 */
	public boolean IsProductKeyValid() throws TurboActivateException
	{
		int ret = TurboActivateNative.INSTANCE.TA_IsProductKeyValid(handle);;

		switch (ret)
		{
			case 0x1B: // TA_E_INVALID_HANDLE
				throw new InvalidHandleException();
			case 0: // is valid
				return true;
		}

		// not valid
		return false;
	}

	/**
	 * Sets the custom proxy to be used by functions that connect to the internet.
	 * 
	 * @param proxy The proxy to use. Proxy must be in the form "http://username:password@host:port/".
	 * @throws TurboActivateException
	 */
	public void SetCustomProxy(String proxy) throws TurboActivateException
	{
		int ret;

		if (Platform.isWindows())
		{
			// handle the special null and empty string cases.
			// apparently WString doesn't support either.
			if ("".equals(proxy) || proxy == null)
				ret = TurboActivateNative.INSTANCE.TA_SetCustomProxy(proxy);
			else
				ret = TurboActivateNative.INSTANCE.TA_SetCustomProxy(new WString(proxy));
		}
		else
			ret = TurboActivateNative.INSTANCE.TA_SetCustomProxy(proxy);

		if (ret != 0)
			throw new TurboActivateException("Failed to set the custom proxy.");
	}

	/**
	 * Get the number of trial days remaining. You must call {@link #UseTrial()} at least once in the past before calling this function.
	 * @throws TurboActivateException
	 */
	public int TrialDaysRemaining() throws TurboActivateException
	{
		return TrialDaysRemaining(TA_SYSTEM | TA_VERIFIED_TRIAL);
	}

	/**
	 * Get the number of trial days remaining. You must call {@link #UseTrial()} at least once in the past before calling this function.
	 * 
	 * @param useTrialFlags The same exact flags you passed to {@link #UseTrial()}.
	 * 
	 * @return The number of days remaining. 0 days if the trial has expired. (E.g. 1 day means *at most* 1 day. That is it could be 30 seconds.)
	 * @throws TurboActivateException
	 */
	public int TrialDaysRemaining(int useTrialFlags) throws TurboActivateException
	{
		IntByReference daysRemain = new IntByReference(0);

		int ret = TurboActivateNative.INSTANCE.TA_TrialDaysRemaining(handle, useTrialFlags, daysRemain);

		if (ret != 0) // TA_OK
			throw taHresultToExcep(ret, "TrialDaysRemaining");

		return daysRemain.getValue();
	}

	/**
	 * Begins the trial the first time it's called. Calling it again will validate the trial data hasn't been tampered with.
	 * @throws TurboActivateException
	 */
	public void UseTrial() throws TurboActivateException
	{
		UseTrial(TA_SYSTEM | TA_VERIFIED_TRIAL, null);
	}

	/**
	 * Begins the trial the first time it's called. Calling it again will validate the trial data hasn't been tampered with.
	 * 
	 * @param flags Whether to create the trial (verified or unverified) either user-wide or system-wide and whether to allow trials in virtual machines. Valid flags are {@link #TA_SYSTEM}, {@link #TA_USER}, {@link #TA_DISALLOW_VM}, {@link #TA_VERIFIED_TRIAL}, and {@link #TA_UNVERIFIED_TRIAL}.
	 * @throws TurboActivateException
	 */
	public void UseTrial(int flags) throws TurboActivateException
	{
		UseTrial(flags, null);
	}

	/**
	 * Begins the trial the first time it's called. Calling it again will validate the trial data hasn't been tampered with.
	 * 
	 * @param flags Whether to create the trial (verified or unverified) either user-wide or system-wide and whether to allow trials in virtual machines. Valid flags are {@link #TA_SYSTEM}, {@link #TA_USER}, {@link #TA_DISALLOW_VM}, {@link #TA_VERIFIED_TRIAL}, and {@link #TA_UNVERIFIED_TRIAL}.
	 * @param extraData Extra data to pass to the LimeLM servers that will be visible for you to see and use. Maximum size is 255 UTF-8 characters.
	 * @throws TurboActivateException
	 */
	public void UseTrial(int flags, String extraData) throws TurboActivateException
	{
		int ret;

		if (Platform.isWindows())
			ret = TurboActivateNative.INSTANCE.TA_UseTrial(handle, flags, extraData != null ? new WString(extraData) : null);
		else
			ret = TurboActivateNative.INSTANCE.TA_UseTrial(handle, flags, extraData);

		if (ret != 0) // TA_OK
			throw taHresultToExcep(ret, "UseTrial");
	}

	/**
	 * Generate a "verified trial" offline request file. This file will then need to be submitted to LimeLM. You will then need to use the TA_UseTrialVerifiedFromFile() function with the response file from LimeLM to actually start the trial.
	 * 
	 * @param filename The location where you want to save the trial request file.
	 * @throws TurboActivateException
	 */
	public void UseTrialVerifiedRequest(String filename) throws TurboActivateException
	{
		UseTrialVerifiedRequest(filename, null);
	}

	/**
	 * Generate a "verified trial" offline request file. This file will then need to be submitted to LimeLM. You will then need to use the TA_UseTrialVerifiedFromFile() function with the response file from LimeLM to actually start the trial.
	 * 
	 * @param filename The location where you want to save the trial request file.
	 * @param extraData Extra data to pass to the LimeLM servers that will be visible for you to see and use. Maximum size is 255 UTF-8 characters.
	 * @throws TurboActivateException
	 */
	public void UseTrialVerifiedRequest(String filename, String extraData) throws TurboActivateException
	{
		int ret;

		if (Platform.isWindows())
		{
			WString convExData = null;

			// Only convert the extra data if the customer passed in extraData
			if (extraData != null)
				convExData = new WString(extraData);

			ret = TurboActivateNative.INSTANCE.TA_UseTrialVerifiedRequest(handle, new WString(filename), convExData);
		}
		else
			ret = TurboActivateNative.INSTANCE.TA_UseTrialVerifiedRequest(handle, filename, extraData);

		if (ret != 0) // TA_OK
			throw taHresultToExcep(ret, "UseTrialVerifiedRequest");
	}

	/**
	 * Begins the trial the first time it's called. Calling it again will validate the trial data hasn't been tampered with.
	 * 
	 * @param filename The location of the trial response file.
	 * @throws TurboActivateException
	 */
	public void UseTrialVerifiedFromFile(String filename) throws TurboActivateException
	{
		UseTrialVerifiedFromFile(filename, TA_SYSTEM | TA_VERIFIED_TRIAL);
	}

	/**
	 * Begins the trial the first time it's called. Calling it again will validate the trial data hasn't been tampered with.
	 * 
	 * @param filename The location of the trial response file.
	 * @param flags Whether to create the trial (verified or unverified) either user-wide or system-wide and whether to allow trials in virtual machines. Valid flags are {@link #TA_SYSTEM}, {@link #TA_USER}, {@link #TA_DISALLOW_VM}, {@link #TA_VERIFIED_TRIAL}, and {@link #TA_UNVERIFIED_TRIAL}.
	 * @throws TurboActivateException
	 */
	public void UseTrialVerifiedFromFile(String filename, int flags) throws TurboActivateException
	{
		int ret;

		if (Platform.isWindows())
			ret = TurboActivateNative.INSTANCE.TA_UseTrialVerifiedFromFile(handle, new WString(filename), flags);
		else
			ret = TurboActivateNative.INSTANCE.TA_UseTrialVerifiedFromFile(handle, filename, flags);

		if (ret != 0) // TA_OK
			throw taHresultToExcep(ret, "UseTrialVerifiedFromFile");
	}

	/**
	 * Extends the trial using a trial extension created in LimeLM.
	 * 
	 * @param trialExtension The trial extension generated from LimeLM.
	 * @throws TurboActivateException
	 */
	public void ExtendTrial(String trialExtension) throws TurboActivateException
	{
		ExtendTrial(trialExtension, TA_SYSTEM | TA_VERIFIED_TRIAL);
	}

	/**
	 * Extends the trial using a trial extension created in LimeLM.
	 * 
	 * @param trialExtension The trial extension generated from LimeLM.
	 * @param useTrialFlags The same exact flags you passed to {@link #UseTrial()}.
	 * @throws TurboActivateException
	 */
	public void ExtendTrial(String trialExtension, int useTrialFlags) throws TurboActivateException
	{
		int ret;

		if (Platform.isWindows())
			ret = TurboActivateNative.INSTANCE.TA_ExtendTrial(handle, useTrialFlags, new WString(trialExtension));
		else
			ret = TurboActivateNative.INSTANCE.TA_ExtendTrial(handle, useTrialFlags, trialExtension);

		if (ret != 0) // TA_OK
			throw taHresultToExcep(ret, "ExtendTrial");
	}

	/**
	 * Explicitly set the TurboActivate folder (the folder that contains the TurboActivate.dat file and the "win-x86", "linux-i386", "mac", etc. folders). If you don't set this folder using this function then this class will try to find the folder containing this compiled jar file.
	 * 
	 * @param folder The folder containing the TurboActivate.dat file and the subfolders for the platform specific TurboActivate libraries.
	 */
	private void SetTurboActivateFolder(String folder)
	{
		TurboActivateFolder = folder;

		if (!folder.endsWith("/") && !folder.endsWith("\\"))
			TurboActivateFolder += File.separator;
	}

	/**
	 * Loads the "TurboActivate.dat" file from a path rather than loading it from the same dir as TurboActivate.dll or the app that uses libTurboActivate.dylib
	 */
	private void SetPDetsLocation() throws TurboActivateException
	{
		int ret = 1;

		try
		{
			String location;

			if (TurboActivateFolder != null)
			{
				location = TurboActivateFolder + "TurboActivate.dat";
			}
			else
			{
				/*
				Note: the following 2 lines will try to retrieve the compiled jar location.
					  This may not work for certain types of apps (e.g. J2EE web apps). You can change the
					  location string to load the path from a configuration file or some other place.

					  See "GetLibraryLocation()" also.
				*/
				File jarFile = new File(TurboActivate.class.getProtectionDomain().getCodeSource().getLocation().toURI().getPath());
				location = (jarFile.isFile() ? jarFile.getParent() : jarFile.toString()) + File.separator + "TurboActivate" + File.separator + "TurboActivate.dat";
			}

			if (Platform.isWindows())
				ret = TurboActivateNative.INSTANCE.TA_PDetsFromPath(new WString(location));
			else
				ret = TurboActivateNative.INSTANCE.TA_PDetsFromPath(location);
		}
		catch (Exception ex)
		{
			throw new TurboActivateException(ex.getMessage());
		}

		if (ret != 0)
			throw new TurboActivateException("Failed to set the TurboActivate.dat location.");
	}

	public static String GetLibraryLocation()
	{
		try
		{
			String arch = System.getProperty("os.arch").toLowerCase();
			String location;

			if (TurboActivateFolder != null)
			{
				location = TurboActivateFolder;
			}
			else
			{
				/*
				Note: the following 2 lines will try to retrieve the compiled jar location.
					  This may not work for certain types of apps (e.g. J2EE web apps). You can change the
					  location string to load the path from a configuration file or some other place.

					  See "SetPDetsLocation()" also.
				*/
				File jarFile = new File(TurboActivate.class.getProtectionDomain().getCodeSource().getLocation().toURI().getPath());
				location = (jarFile.isFile() ? jarFile.getParent() : jarFile.toString()) + File.separator + "TurboActivate" + File.separator;
			}

			switch(Platform.getOSType())
			{
			case Platform.WINDOWS:
				if ("i386".equals(arch))
					arch = "x86";
				else if("amd64".equals(arch))
					arch = "x64";
				else if ("aarch64".equals(arch))
					arch = "arm64";

				location += "win-" + arch + File.separator + "TurboActivate.dll";
				break;
			case Platform.MAC:
				location += "mac" + File.separator + "libTurboActivate.dylib";
				break;
			default: // Linux / FreeBSD / OpenBSD
				location += System.getProperty("os.name").toLowerCase();
				if ("x86".equals(arch))
					arch = "i386";
				else if ("x86_64".equals(arch))
					arch = "amd64";
				else if ("aarch64".equals(arch))
					arch = "arm64";

				location += "-" + arch + File.separator + "libTurboActivate.so";
				break;
			}

			return location;
		}
		catch (Exception ex)
		{
			return null;
		}
	}

	/***
	 * Gets the version number of the currently used TurboActivate library.
	 * 
	 * The version format is:  Major.Minor.Build.Revision
	 * 
	 * @param major
	 * @param minor
	 * @param build
	 * @param rev 
	 */
	public static void GetVersion(IntByReference major, IntByReference minor, IntByReference build, IntByReference rev)
	{
		TurboActivateNative.INSTANCE.TA_GetVersion(major, minor, build, rev);
	}
}


interface TurboActivateNative extends Library
{
	// load TurboActivate.dll/.so/.dylib
	TurboActivateNative INSTANCE = (TurboActivateNative) Native.load(TurboActivate.GetLibraryLocation(), TurboActivateNative.class);

	public class ACTIVATE_OPTIONS extends Structure
	{
		public int nLength;
		public String sExtraData;

		@Override
		protected List getFieldOrder()
		{
			return Arrays.asList(new String[] { "nLength", "sExtraData" });
		}
	}

	public class W_ACTIVATE_OPTIONS extends Structure
	{
		public int nLength;
		public WString sExtraData;

		@Override
		protected List getFieldOrder()
		{
			return Arrays.asList(new String[] { "nLength", "sExtraData" });
		}
	}

	public static int TA_SKIP_OFFLINE = 1;
	public static int TA_OFFLINE_SHOW_INET_ERR = 2;

	public class GENUINE_OPTIONS extends Structure
	{
		public int nLength;
		public int flags;
		public int nDaysBetweenChecks;
		public int nGraceDaysOnInetErr;

		@Override
		protected List getFieldOrder()
		{
			return Arrays.asList(new String[] { "nLength", "flags", "nDaysBetweenChecks", "nGraceDaysOnInetErr" });
		}
	}

	interface TrialCallbackType extends Callback
	{
		void invoke(int status);
	}

	// all functions with strings have both a WString and String prototype of the function.
	// only use the WString version on Windows, and the String version on all other systems.

	int TA_GetHandle(WString versionGUID);
	int TA_GetHandle(String versionGUID);
	int TA_Activate(int handle, W_ACTIVATE_OPTIONS options);
	int TA_Activate(int handle, ACTIVATE_OPTIONS options);
	int TA_ActivationRequestToFile(int handle, WString filename, W_ACTIVATE_OPTIONS options);
	int TA_ActivationRequestToFile(int handle, String filename, ACTIVATE_OPTIONS options);
	int TA_ActivateFromFile(int handle, WString filename);
	int TA_ActivateFromFile(int handle, String filename);
	int TA_CheckAndSavePKey(int handle, WString productKey, int flags);
	int TA_CheckAndSavePKey(int handle, String productKey, int flags);
	int TA_Deactivate(int handle, byte erasePkey);
	int TA_DeactivationRequestToFile(int handle, WString filename, byte erasePkey);
	int TA_DeactivationRequestToFile(int handle, String filename, byte erasePkey);
	int TA_GetExtraData(int handle, java.nio.CharBuffer lpValueStr, int cchValue);
	int TA_GetExtraData(int handle, java.nio.ByteBuffer lpValueStr, int cchValue);
	int TA_GetFeatureValue(int handle, WString featureName, java.nio.CharBuffer lpValueStr, int cchValue);
	int TA_GetFeatureValue(int handle, String featureName, java.nio.ByteBuffer lpValueStr, int cchValue);
	int TA_GetPKey(int handle, java.nio.CharBuffer lpPKeyStr, int cchPKey);
	int TA_GetPKey(int handle, java.nio.ByteBuffer lpPKeyStr, int cchPKey);
	int TA_IsActivated(int handle);
	int TA_IsDateValid(int handle, WString date_time, int flags);
	int TA_IsDateValid(int handle, String date_time, int flags);
	int TA_IsGenuine(int handle);
	int TA_IsGenuineEx(int handle, GENUINE_OPTIONS options);
	int TA_GenuineDays(int handle, int nDaysBetweenChecks, int nGraceDaysOnInetErr, IntByReference DaysRemaining, ByteByReference inGracePeriod);
	int TA_IsProductKeyValid(int handle);
	int TA_PDetsFromPath(WString path);
	int TA_PDetsFromPath(String path);
	int TA_PDetsFromByteArray(byte[] byteArr, int byteArrLen);
	int TA_SetCustomProxy(WString versionGUID);
	int TA_SetCustomProxy(String versionGUID);
	int TA_TrialDaysRemaining(int handle, int flags, IntByReference DaysRemaining);
	int TA_UseTrialVerifiedRequest(int handle, WString filename, WString extra_data);
	int TA_UseTrialVerifiedRequest(int handle, String filename, String extra_data);
	int TA_UseTrialVerifiedFromFile(int handle, WString filename, int flags);
	int TA_UseTrialVerifiedFromFile(int handle, String filename, int flags);
	int TA_UseTrial(int handle, int flags, WString extra_data);
	int TA_UseTrial(int handle, int flags, String extra_data);
	int TA_ExtendTrial(int handle, int flags, WString trialExtension);
	int TA_ExtendTrial(int handle, int flags, String trialExtension);
	int TA_SetTrialCallback(int handle, TrialCallbackType callback);
	int TA_GetVersion(IntByReference major, IntByReference minor, IntByReference build, IntByReference rev);
}