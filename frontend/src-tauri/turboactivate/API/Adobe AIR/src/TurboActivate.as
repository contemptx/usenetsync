package
{
	import flash.desktop.NativeProcess;
	import flash.desktop.NativeProcessStartupInfo;
	import flash.events.EventDispatcher;
	import flash.events.IOErrorEvent;
	import flash.events.NativeProcessExitEvent;
	import flash.events.ProgressEvent;
	import flash.filesystem.File;
	import flash.system.Capabilities;
	import flash.utils.ByteArray;
	import flash.utils.Endian;

	public class TurboActivate extends EventDispatcher
	{
		/**
		 * The GUID for this product version. This is found on the LimeLM site on the version overview.
		 */
		private var VersionGUID : String;
		private var PDetsFilename : String;

		private var trialCallback:Function;

		private var process:NativeProcess;

		private var FunctionProcessing:int = -1;
		private var RetCode:int;

		internal const FUNC_Activate:int = 0;
		internal const FUNC_ActivationRequestToFile:int = 1;
		internal const FUNC_ActivateFromFile:int = 2;
		internal const FUNC_CheckAndSavePKey:int = 3;
		internal const FUNC_Deactivate:int = 4;
		internal const FUNC_GetFeatureValue:int = 5;
		internal const FUNC_GetPKey:int = 6;
		internal const FUNC_GenuineDays:int = 7;
		internal const FUNC_IsActivated:int = 8;
		internal const FUNC_IsGenuine:int = 9;
		internal const FUNC_IsProductKeyValid:int = 10;
		internal const FUNC_SetCustomProxy:int = 11;
		internal const FUNC_TrialDaysRemaining:int = 12;
		internal const FUNC_UseTrial:int = 13;
		internal const FUNC_ExtendTrial:int = 14;
		internal const FUNC_DeactivationRequestToFile:int = 16;
		internal const FUNC_IsGenuineEx:int = 21;

		internal const TA_INTERNAL_IS_FUNC:int = 0;
		internal const TA_INTERNAL_IS_CALLBACK:int = 1;

		// The version of TurboActivate & systa that this script works for.
		// Do *not* change this value.
		internal const TA_ACTIONSCRIPT_VERS:String = "7";

		/**
		 * TurboActivate contructor.
		 */
		public function TurboActivate(vGUID:String, pdetsFilename:String = null)
		{
			this.VersionGUID = vGUID;
			this.PDetsFilename = pdetsFilename;

			if (NativeProcess.isSupported)
			{
				// setup the native process
				launchSysta();
			}
			else
			{
				throw new Error("You must add <supportedProfiles>extendedDesktop</supportedProfiles> to your Adobe AIR Application Descriptor File (e.g. AppName-app.xml) before you can use TurboActivate.");
			}

			responseBuffer.endian = Endian.LITTLE_ENDIAN;
		}

		private function launchSysta():void
		{
			// throw an exception if the version GUID is null or empty
			if (VersionGUID === null || VersionGUID === "")
				throw new Error("You must set the VersionGUID property.");


			var file:File = File.applicationDirectory;

			if (Capabilities.os.toLowerCase().indexOf("win") > -1)
				file = file.resolvePath("Windows/systa.exe");
			else if (Capabilities.os.toLowerCase().indexOf("mac") > -1)
				file = file.resolvePath("Mac/systa");
			else if (Capabilities.os.toLowerCase().indexOf("lin") > -1)
				file = file.resolvePath("Linux/systa");

			var nativeProcessStartupInfo:NativeProcessStartupInfo = new NativeProcessStartupInfo();
			nativeProcessStartupInfo.executable = file;
			var args:Vector.<String> = new Vector.<String>();

			// push the TA_ActionScript version that we're using.
			// this ensures that we're using the correct systa.exe
			args.push(TA_ACTIONSCRIPT_VERS); 

			// push the version GUID to get the handle
			args.push(VersionGUID);

			// if the customer specified a TurboActivate.dat file also pass that along
			if (!(PDetsFilename === null || PDetsFilename === ""))
				args.push("\"" + PDetsFilename + "\"");

			nativeProcessStartupInfo.arguments = args;

			process = new NativeProcess();
			process.start(nativeProcessStartupInfo);
			process.addEventListener(ProgressEvent.STANDARD_OUTPUT_DATA, onOutputData);
			process.addEventListener(NativeProcessExitEvent.EXIT, onExit);
			process.addEventListener(IOErrorEvent.STANDARD_INPUT_IO_ERROR, onIOError);
			process.addEventListener(IOErrorEvent.STANDARD_OUTPUT_IO_ERROR, onIOError);

			// the Input/Output streams must be set to Little_endian
			// (since Adobe Air only runs on little endian machines)
			process.standardInput.endian = Endian.LITTLE_ENDIAN;
			process.standardOutput.endian = Endian.LITTLE_ENDIAN;
		}

		private function onExit(event:NativeProcessExitEvent):void
		{
			if (event.exitCode == 42)
			{
				FunctionProcessing = -1;
				UnfinishedProcessing = false;
				throw new Error("You must use the \"systa\" executable that comes with this version of TurboActivate.", 42);
			}

			if (event.exitCode == 43)
			{
				FunctionProcessing = -1;
				UnfinishedProcessing = false;
				throw new Error("The product details file \"TurboActivate.dat\" failed to load. It's either missing or corrupt.", TA_E_PDETS);
			}



			if (FunctionProcessing !== -1)
			{
				var evt:TurboActivateEvent;
				var err:Error = new Error("The systa process ended before the response could be delivered.", 1);

				// show an error for the function we're processing
				switch (FunctionProcessing)
				{
					case FUNC_Activate:
						evt = new TurboActivateEvent(TurboActivateEvent.ACTIVATE, 1, err);
						break;
					case FUNC_ActivationRequestToFile:
						evt = new TurboActivateEvent(TurboActivateEvent.ACTIVATION_REQUEST_TO_FILE, 1, err);
						break;
					case FUNC_ActivateFromFile:
						evt = new TurboActivateEvent(TurboActivateEvent.ACTIVATE_FROM_FILE, 1, err);
						break;
					case FUNC_CheckAndSavePKey:
						evt = new TurboActivateEvent(TurboActivateEvent.CHECK_AND_SAVE_PKEY, 1, err);
						break;
					case FUNC_Deactivate:
						evt = new TurboActivateEvent(TurboActivateEvent.DEACTIVATE, 1, err);
						break;
					case FUNC_GetFeatureValue:
						evt = new TurboActivateEvent(TurboActivateEvent.GET_FEATURE_VALUE, 1, err);
						break;
					case FUNC_GetPKey:
						evt = new TurboActivateEvent(TurboActivateEvent.GET_PKEY, 1, err);
						break;
					case FUNC_IsActivated:
						evt = new TurboActivateEvent(TurboActivateEvent.IS_ACTIVATED, 1, err);
						break;
					case FUNC_IsGenuine:
						evt = new TurboActivateEvent(TurboActivateEvent.IS_GENUINE, 1, err);
						break;
					case FUNC_IsProductKeyValid:
						evt = new TurboActivateEvent(TurboActivateEvent.IS_PRODUCT_KEY_VALID, 1, err);
						break;
					case FUNC_SetCustomProxy:
						evt = new TurboActivateEvent(TurboActivateEvent.SET_CUSTOM_PROXY, 1, err);
						break;
					case FUNC_TrialDaysRemaining:
						evt = new TurboActivateEvent(TurboActivateEvent.TRIAL_DAYS_REMAINING, 1, err);
						break;
					case FUNC_GenuineDays:
						evt = new TurboActivateEvent(TurboActivateEvent.GENUINE_DAYS, 1, err);
						break;
					case FUNC_UseTrial:
						evt = new TurboActivateEvent(TurboActivateEvent.USE_TRIAL, 1, err);
						break;
					case FUNC_ExtendTrial:
						evt = new TurboActivateEvent(TurboActivateEvent.EXTEND_TRIAL, 1, err);
						break;
					case FUNC_DeactivationRequestToFile:
						evt = new TurboActivateEvent(TurboActivateEvent.DEACT_REQ_TO_FILE, 1, err);
						break;
					case FUNC_IsGenuineEx:
						evt = new TurboActivateEvent(TurboActivateEvent.IS_GENUINE_EX, 1, err);
						break;
				}

				this.dispatchEvent(evt);

				FunctionProcessing = -1;
				UnfinishedProcessing = false;
			}
		}

		private function onIOError(event:IOErrorEvent):void
		{
			// failed to write/read to/from STDIN or STDOUT
			// kill the bad process (onExit should be called)
			if (process.running)
				process.exit(true);
		}

		private var UnfinishedProcessing:Boolean = false;
		private var responseBuffer: ByteArray = new ByteArray;
		private var remainingResp:int = 0;

		private function ReadString():Boolean
		{
			// read in the string length only on the first call
			if (!UnfinishedProcessing)
			{
				remainingResp = process.standardOutput.readInt();
				responseBuffer.clear();
			}

			// fill the buffer with all available bytes. 
			process.standardOutput.readBytes(responseBuffer, responseBuffer.length);

			remainingResp -= responseBuffer.length;

			// if we're all done, return false
			if (remainingResp === 0)
				return false;

			// we need to read more bytes
			UnfinishedProcessing = true;
			return true;
		}

		public static const TA_SYSTEM:uint = 1;
		public static const TA_USER:uint = 2;

		/**
		 * Use the TA_DISALLOW_VM in UseTrial() to disallow trials in virtual machines. 
		 * If you use this flag in UseTrial() and the customer's machine is a Virtual
		 * Machine, then UseTrial() will throw VirtualMachineException.
		 */
		public static const TA_DISALLOW_VM:uint = 4;

		/**
			Use this flag in TA_UseTrial() to tell TurboActivate to use client-side
			unverified trials. For more information about verified vs. unverified trials,
			see here: https://wyday.com/limelm/help/trials/
			Note: unverified trials are unsecured and can be reset by malicious customers.
		*/
		public static const TA_UNVERIFIED_TRIAL:uint = 16;

		/**
			Use the TA_VERIFIED_TRIAL flag to use verified trials instead
			of unverified trials. This means the trial is locked to a particular computer.
			The customer can't reset the trial.
		*/
		public static const TA_VERIFIED_TRIAL:uint = 32;

		/**
		 * Callback-status value used when the trial has expired.
		 */
		public static const TA_CB_EXPIRED:uint = 0;

		/**
		 * Callback-status value used when the trial has expired due to date/time fraud.
		 */
		public static const TA_CB_EXPIRED_FRAUD:uint = 1;

		// Possible IsGenuineEx() return values from uintResponse.

		/**
		 * Is activated and genuine.
		 */
		public static const IGRet_Genuine:uint = 0;

		/**
		 * Is activated and genuine and the features changed.
		 */
		public static const IGRet_GenuineFeaturesChanged:uint = 1;

		/**
		 * Not genuine (note: use this in tandem with IGRet_NotGenuineInVM).
		 */
		public static const IGRet_NotGenuine:uint = 2;

		/**
		 * Not genuine because you're in a Virtual Machine.
		 */
		public static const IGRet_NotGenuineInVM:uint = 3;

		/**
		 * Treat this error as a warning. That is, tell the user that the activation couldn't be validated with the servers and that they can manually recheck with the servers immediately.
		 */
		public static const IGRet_InternetError:uint = 4;


		public static const TA_OK:int = 0;
		public static const TA_E_PKEY:int = 0x02;
		public static const TA_E_ACTIVATE:int = 0x03;
		public static const TA_E_INET:int = 0x04;
		public static const TA_E_INUSE:int = 0x05;
		public static const TA_E_REVOKED:int = 0x06;
		public static const TA_E_PDETS:int = 0x08;
		public static const TA_E_TRIAL:int = 0x09;
		public static const TA_E_COM:int = 0x0B;
		public static const TA_E_TRIAL_EUSED:int = 0x0C;
		public static const TA_E_EXPIRED:int = 0x0D;
		public static const TA_E_PERMISSION:int = 0x0F;
		public static const TA_E_INVALID_FLAGS:int = 0x10;
		public static const TA_E_IN_VM:int = 0x11;
		public static const TA_E_EDATA_LONG:int = 0x12;
		public static const TA_E_INVALID_ARGS:int = 0x13;
		public static const TA_E_KEY_FOR_TURBOFLOAT:int = 0x14;
		public static const TA_E_FEATURES_CHANGED:int = 0x16;
		public static const TA_E_NO_MORE_DEACTIVATIONS:int = 0x18;
		public static const TA_E_ACCOUNT_CANCELED:int = 0x19;
		public static const TA_E_ALREADY_ACTIVATED:int = 0x1A;
		public static const TA_E_INVALID_HANDLE:int = 0x1B;
		public static const TA_E_ENABLE_NETWORK_ADAPTERS:int = 0x1C;
		public static const TA_E_ALREADY_VERIFIED_TRIAL:int = 0x1D;
		public static const TA_E_TRIAL_EXPIRED:int = 0x1E;
		public static const TA_E_MUST_SPECIFY_TRIAL_TYPE:int = 0x1F;
		public static const TA_E_MUST_USE_TRIAL:int = 0x20;
		public static const TA_E_NO_MORE_TRIALS_ALLOWED:int = 0x21;
		public static const TA_E_BROKEN_WMI:int = 0x22;
		public static const TA_E_INET_TIMEOUT:int = 0x23;
		public static const TA_E_INET_TLS:int = 0x24;


		private function GetError(retCode:int, fallthroughError:String = null):Error
		{
			switch (retCode)
			{
				case TA_OK:
					return null;

				case TA_E_PKEY:
					return new Error("The product key is invalid or there's no product key.", TA_E_PKEY);

				case TA_E_ACTIVATE:
					return new Error("The product needs to be activated.", TA_E_ACTIVATE);

				case TA_E_INET:
					return new Error("Connection to the server failed.", TA_E_INET);

				case TA_E_INUSE:
					return new Error("The product key has already been activated with the maximum number of computers.", TA_E_INUSE);

				case TA_E_REVOKED:
					return new Error("The product key has been revoked.", TA_E_REVOKED);

				case TA_E_PDETS:
					return new Error("The product details file \"TurboActivate.dat\" failed to load. It's either missing or corrupt.", TA_E_PDETS);

				case TA_E_TRIAL:
					return new Error("The trial data has been corrupted, using the oldest date possible.", TA_E_TRIAL);

				case TA_E_COM:
					return new Error("CoInitializeEx failed. Re-enable Windows Management Instrumentation (WMI) service. Contact your system admin for more information.", TA_E_COM);

				case TA_E_TRIAL_EUSED:
					return new Error("The trial extension has already been used.", TA_E_TRIAL_EUSED);

				case TA_E_EXPIRED:
					return new Error("Failed because your system date and time settings are incorrect. Fix your date and time settings, restart your computer, and try to activate again.", TA_E_EXPIRED);

				case TA_E_PERMISSION:
					return new Error("Insufficient system permission. Either start your process as an admin / elevated user or call the function again with the TA_USER flag.", TA_E_PERMISSION);

				case TA_E_INVALID_FLAGS:
					return new Error("The flags you passed to the function were invalid (or missing). Flags like \"TA_SYSTEM\" and \"TA_USER\" are mutually exclusive -- you can only use one or the other.", TA_E_INVALID_FLAGS);

				case TA_E_IN_VM:
					return new Error("The function failed because this instance of your program is running inside a virtual machine / hypervisor and you've prevented the function from running inside a VM.", TA_E_IN_VM);

				case TA_E_EDATA_LONG:
					return new Error("The \"extra data\" was too long. You're limited to 255 UTF-8 characters. Or, on Windows, a Unicode string that will convert into 255 UTF-8 characters or less.", TA_E_EDATA_LONG);

				case TA_E_INVALID_ARGS:
					return new Error("The arguments passed to the function are invalid. Double check your logic.", TA_E_INVALID_ARGS);

				case TA_E_KEY_FOR_TURBOFLOAT:
					return new Error("The product key used is for TurboFloat, not TurboActivate.", TA_E_KEY_FOR_TURBOFLOAT);

				case TA_E_NO_MORE_DEACTIVATIONS:
					return new Error("This product key had a limited number of allowed deactivations. No more deactivations are allowed for the product key. This product is still activated on this computer.", TA_E_NO_MORE_DEACTIVATIONS);

				case TA_E_ACCOUNT_CANCELED:
					return new Error("Can't activate or start a verified trial because the LimeLM account is cancelled.", TA_E_ACCOUNT_CANCELED);

				case TA_E_ALREADY_ACTIVATED:
					return new Error("You can't use a product key because your app is already activated with a product key. To use a new product key, then first deactivate using either the TA_Deactivate() or TA_DeactivationRequestToFile().", TA_E_ALREADY_ACTIVATED);

				case TA_E_INVALID_HANDLE:
					return new Error("The handle is not valid. To get a handle use TA_GetHandle().", TA_E_INVALID_HANDLE);

				case TA_E_ENABLE_NETWORK_ADAPTERS:
					return new Error("There are network adapters on the system that are disabled and TurboActivate couldn't read their hardware properties (even after trying and failing to enable the adapters automatically). Enable the network adapters, re-run the function, and TurboActivate will be able to \"remember\" the adapters even if the adapters are disabled in the future.", TA_E_ENABLE_NETWORK_ADAPTERS);

				case TA_E_ALREADY_VERIFIED_TRIAL:
					return new Error("The trial is already a verified trial. You need to use the \"TA_VERIFIED_TRIAL\" flag. Can't \"downgrade\" a verified trial to an unverified trial.", TA_E_ALREADY_VERIFIED_TRIAL);

				case TA_E_TRIAL_EXPIRED:
					return new Error("The verified trial has expired. You must request a trial extension from the company.", TA_E_TRIAL_EXPIRED);

				case TA_E_MUST_SPECIFY_TRIAL_TYPE:
					return new Error("You must specify the trial type (TA_UNVERIFIED_TRIAL or TA_VERIFIED_TRIAL). And you can't use both flags. Choose one or the other. We recommend TA_VERIFIED_TRIAL.", TA_E_MUST_SPECIFY_TRIAL_TYPE);

				case TA_E_MUST_USE_TRIAL:
					return new Error("You must call TA_UseTrial() before you can get the number of trial days remaining.", TA_E_MUST_USE_TRIAL);

				case TA_E_NO_MORE_TRIALS_ALLOWED:
					return new Error("In the LimeLM account either the trial days is set to 0, OR the account is set to not auto-upgrade and thus no more verified trials can be made.", TA_E_NO_MORE_TRIALS_ALLOWED);

				case TA_E_BROKEN_WMI:
					return new Error("The WMI repository on the computer is broken. To fix the WMI repository see the instructions here: https://wyday.com/limelm/help/faq/#fix-broken-wmi", TA_E_BROKEN_WMI);

				case TA_E_INET_TIMEOUT:
					return new Error("The connection to the server timed out because a long period of time elapsed since the last data was sent or received.", TA_E_INET_TIMEOUT);

				case TA_E_INET_TLS:
					return new Error("The secure connection to the activation servers failed due to a TLS or certificate error. More information here: https://wyday.com/limelm/help/faq/#internet-error", TA_E_INET_TLS);

				default:

					return fallthroughError === null ? null : new Error(fallthroughError, retCode);
			}
		}

		private function onOutputData(event:ProgressEvent):void
		{
			var evt:TurboActivateEvent;

			if (!UnfinishedProcessing)
			{
				var respType:int = process.standardOutput.readByte();

				if (respType === TA_INTERNAL_IS_CALLBACK)
				{
					var callbackStatus:uint = process.standardOutput.readUnsignedInt();

					// call the user's defined callback with the status
                	trialCallback(callbackStatus);
					return;
				}

				// get the return code
				RetCode = process.standardOutput.readInt();
			}

			switch (FunctionProcessing)
			{
				case FUNC_Activate:
					evt = new TurboActivateEvent(TurboActivateEvent.ACTIVATE, RetCode, GetError(RetCode, "Failed to activate."));
					FinishedProcessing();
					this.dispatchEvent(evt);
					break;
				case FUNC_ActivationRequestToFile:
					evt = new TurboActivateEvent(TurboActivateEvent.ACTIVATION_REQUEST_TO_FILE, RetCode, GetError(RetCode, "Failed to save the activation request file."));
					FinishedProcessing();
					this.dispatchEvent(evt);
					break;
				case FUNC_ActivateFromFile:
					evt = new TurboActivateEvent(TurboActivateEvent.ACTIVATE_FROM_FILE, RetCode, GetError(RetCode, "Failed to activate."));
					FinishedProcessing();
					this.dispatchEvent(evt);
					break;
				case FUNC_CheckAndSavePKey:
					evt = new TurboActivateEvent(TurboActivateEvent.CHECK_AND_SAVE_PKEY, RetCode, GetError(RetCode));
					evt.boolResponse = RetCode === TA_OK;

					FinishedProcessing();
					this.dispatchEvent(evt);
					break;
				case FUNC_Deactivate:
					evt = new TurboActivateEvent(TurboActivateEvent.DEACTIVATE, RetCode, GetError(RetCode, "Failed to deactivate."));
					FinishedProcessing();
					this.dispatchEvent(evt);
					break;
				case FUNC_GetFeatureValue:
					// read in the string
					if (RetCode === TA_OK && ReadString())
						return;

					evt = new TurboActivateEvent(TurboActivateEvent.GET_FEATURE_VALUE, RetCode, GetError(RetCode, "Failed to get feature value. The feature doesn't exist."));

					if (RetCode === TA_OK)
						evt.stringResponse = responseBuffer.readUTFBytes(responseBuffer.length);

					FinishedProcessing();
					this.dispatchEvent(evt);
					break;
				case FUNC_GetPKey:
					// read in the string
					if (RetCode === TA_OK && ReadString())
						return;

					evt = new TurboActivateEvent(TurboActivateEvent.GET_PKEY, RetCode, GetError(RetCode, "Failed to get the product key."));

					if (RetCode === TA_OK)
						evt.stringResponse = responseBuffer.readUTFBytes(responseBuffer.length);

					FinishedProcessing();
					this.dispatchEvent(evt);
					break;
				case FUNC_IsActivated:
					evt = new TurboActivateEvent(TurboActivateEvent.IS_ACTIVATED, RetCode, GetError(RetCode));
					evt.boolResponse = RetCode === TA_OK;
					FinishedProcessing();
					this.dispatchEvent(evt);
					break;
				case FUNC_IsGenuine:
					evt = new TurboActivateEvent(TurboActivateEvent.IS_GENUINE, RetCode, GetError(RetCode));

					// is genuine if TA_OK or TA_E_FEATURES_CHANGED
					evt.boolResponse = RetCode === TA_OK || RetCode === TA_E_FEATURES_CHANGED;
					FinishedProcessing();
					this.dispatchEvent(evt);
					break;

				case FUNC_IsGenuineEx:
					evt = new TurboActivateEvent(TurboActivateEvent.IS_GENUINE_EX, RetCode, GetError(RetCode));

					// because the following errors are handled by GetError() we have to null out the error in those cases
					if (RetCode === TA_E_INET
						|| RetCode === TA_E_ACTIVATE
						|| RetCode === TA_E_IN_VM
						|| RetCode === TA_E_REVOKED)
					{
						evt.ErrorObj = null;
					}

					switch (RetCode)
					{
						case TA_E_INET:
						case 21: // TA_E_INET_DELAYED
							evt.uintResponse = IGRet_InternetError;
							break;

						case TA_E_IN_VM:
							evt.uintResponse = IGRet_NotGenuineInVM;
							break;

						case TA_E_FEATURES_CHANGED:
							evt.uintResponse = IGRet_GenuineFeaturesChanged;
							break;

						case TA_OK: // is activated and/or Genuine
							evt.uintResponse = IGRet_Genuine;
							break;

						default:
							evt.uintResponse = IGRet_NotGenuine;
					}

					FinishedProcessing();
					this.dispatchEvent(evt);
					break;
				case FUNC_IsProductKeyValid:
					evt = new TurboActivateEvent(TurboActivateEvent.IS_PRODUCT_KEY_VALID, RetCode, GetError(RetCode));
					evt.boolResponse = RetCode === TA_OK;
					FinishedProcessing();
					this.dispatchEvent(evt);
					break;
				case FUNC_SetCustomProxy:
					evt = new TurboActivateEvent(TurboActivateEvent.SET_CUSTOM_PROXY, RetCode, GetError(RetCode, "Failed to set the custom proxy."));
					FinishedProcessing();
					this.dispatchEvent(evt);
					break;

				case FUNC_TrialDaysRemaining:
					evt = new TurboActivateEvent(TurboActivateEvent.TRIAL_DAYS_REMAINING, RetCode, GetError(RetCode, "Failed to get the trial data."));

					if (RetCode === TA_OK)
					{
						if (process.standardOutput.bytesAvailable === 0)
						{
							UnfinishedProcessing = true;
							return;
						}
						else
							evt.uintResponse = process.standardOutput.readUnsignedInt();
					}

					FinishedProcessing();
					this.dispatchEvent(evt);
					break;

				case FUNC_GenuineDays:
					evt = new TurboActivateEvent(TurboActivateEvent.GENUINE_DAYS, RetCode, GetError(RetCode, "Failed to get the genuine days."));

					if (RetCode === TA_OK)
					{
						if (process.standardOutput.bytesAvailable === 0)
						{
							UnfinishedProcessing = true;
							return;
						}
						else
						{
							// get the genuine days remaining
							evt.uintResponse = process.standardOutput.readUnsignedInt();

							// get whether we're in the grace period or not
							// true, if in grace period, false otherwise
							evt.boolResponse = process.standardOutput.readByte() === 1;
						}
					}

					FinishedProcessing();
					this.dispatchEvent(evt);
					break;

				case FUNC_UseTrial:
					evt = new TurboActivateEvent(TurboActivateEvent.USE_TRIAL, RetCode, GetError(RetCode, "Failed to save the trial data."));
					FinishedProcessing();
					this.dispatchEvent(evt);
					break;
				case FUNC_ExtendTrial:
					evt = new TurboActivateEvent(TurboActivateEvent.EXTEND_TRIAL, RetCode, GetError(RetCode, "Failed to extend trial."));
					FinishedProcessing();
					this.dispatchEvent(evt);
					break;
				case FUNC_DeactivationRequestToFile:
					evt = new TurboActivateEvent(TurboActivateEvent.DEACT_REQ_TO_FILE, RetCode, GetError(RetCode, "Failed to deactivate."));
					FinishedProcessing();
					this.dispatchEvent(evt);
					break;
			}
		}

		private function FinishedProcessing():void
		{
			// we've finished processing the function
			FunctionProcessing = -1;
			UnfinishedProcessing = false;
		}

		private function PreRun():void
		{
			if (process === null || !process.running)
				launchSysta();

			// throw an exception if another function is mid-processing
			if (FunctionProcessing !== -1)
				throw new Error("Another TurboActivate function is waiting for a response, you must wait for a function to respond before making other function calls.");
		}

		/**
		 * Activates the product on this computer. You must call CheckAndSavePKey(String) with a valid product key or have used the TurboActivate wizard sometime before calling this function.
		 */
		public function Activate(extraData:String = null):void
		{
			PreRun();

			FunctionProcessing = FUNC_Activate;
			process.standardInput.writeInt(FUNC_Activate);

			var hasExtraData:Boolean = !(extraData === null || extraData === "");

			process.standardInput.writeBoolean(hasExtraData);

			if (hasExtraData)
				process.standardInput.writeUTF(extraData);
		}

		/**
		 * Get the "activation request" file for offline activation. You must call CheckAndSavePKey(String) with a valid product key or have used the TurboActivate wizard sometime before calling this function.
		 * @param filename The location where you want to save the activation request file.
		 */
		public function ActivationRequestToFile(filename:String, extraData:String = null):void
		{
			PreRun();

			FunctionProcessing = FUNC_ActivationRequestToFile;
			process.standardInput.writeInt(FUNC_ActivationRequestToFile);
			process.standardInput.writeUTF(filename);

			var hasExtraData:Boolean = !(extraData === null || extraData === "");

			process.standardInput.writeBoolean(hasExtraData);

			if (hasExtraData)
				process.standardInput.writeUTF(extraData);
		}

		/**
		 * Activate from the "activation response" file for offline activation.
		 * @param filename The location of the activation response file.
		 */
		public function ActivateFromFile(filename:String):void
		{
			PreRun();

			FunctionProcessing = FUNC_ActivateFromFile;
			process.standardInput.writeInt(FUNC_ActivateFromFile);
			process.standardInput.writeUTF(filename);
		}

		/**
		 * Checks and saves the product key.
		 * @param productKey The product key you want to save.
		 * @param flags Whether to create the activation either user-wide or system-wide. Valid flags are TA_SYSTEM and TA_USER.
		 */
		public function CheckAndSavePKey(productKey:String, flags:uint = TA_USER):void
		{
			PreRun();

			FunctionProcessing = FUNC_CheckAndSavePKey;
			process.standardInput.writeInt(FUNC_CheckAndSavePKey);
			process.standardInput.writeUTF(productKey);
			process.standardInput.writeUnsignedInt(flags);
		}

		/**
		 * Deactivates the product on this computer.
		 * @param eraseProductKey Erase the product key so the user will have to enter a new product key if they wish to reactivate.
		 */
		public function Deactivate(eraseProductKey:Boolean = false):void
		{
			PreRun();

			FunctionProcessing = FUNC_Deactivate;
			process.standardInput.writeInt(FUNC_Deactivate);
			process.standardInput.writeBoolean(eraseProductKey);
		}

		/**
		 * Get the "deactivation request" file for offline deactivation.
		 * @param filename The location where you want to save the deactivation request file.
		 * @param eraseProductKey Erase the product key so the user will have to enter a new product key if they wish to reactivate.
		 */
		public function DeactivationRequestToFile(filename:String, eraseProductKey:Boolean):void
		{
			PreRun();

			FunctionProcessing = FUNC_DeactivationRequestToFile;
			process.standardInput.writeInt(FUNC_DeactivationRequestToFile);
			process.standardInput.writeUTF(filename);
			process.standardInput.writeBoolean(eraseProductKey);
		}

		/**
		 * Gets the value of a feature.
		 * @param featureName The name of the feature to retrieve the value for.
		 */
		public function GetFeatureValue(featureName:String):void
		{
			PreRun();

			FunctionProcessing = FUNC_GetFeatureValue;
			process.standardInput.writeInt(FUNC_GetFeatureValue);
			process.standardInput.writeUTF(featureName);
		}

		/**
		 * Gets the stored product key. NOTE: if you want to check if a product key is valid simply call IsProductKeyValid().
		 */
		public function GetPKey():void
		{
			PreRun();

			FunctionProcessing = FUNC_GetPKey;
			process.standardInput.writeInt(FUNC_GetPKey);
		}

		/**
		 * Checks whether the computer has been activated.
		 */
		public function IsActivated():void
		{
			PreRun();

			FunctionProcessing = FUNC_IsActivated;
			process.standardInput.writeInt(FUNC_IsActivated);
		}

		/**
		 * Checks whether the computer is genuinely activated by verifying with the LimeLM servers.
		 */
		public function IsGenuine():void
		{
			PreRun();

			FunctionProcessing = FUNC_IsGenuine;
			process.standardInput.writeInt(FUNC_IsGenuine);
		}

		/**
		 * Checks whether the computer is genuinely activated by verifying with the LimeLM servers.
		 * @param daysBetweenChecks How often to contact the LimeLM servers for validation. 90 days recommended.
		 * @param graceDaysOnInetErr If the call fails because of an internet error, how long, in days, should the grace period last (before returning deactivating and returning TA_FAIL).
		 *
		 * 14 days is recommended.
		 */
		public function IsGenuineEx(daysBetweenChecks:uint, graceDaysOnInetErr:uint, skipOffline:Boolean = false, offlineShowInetErr:Boolean = false):void
		{
			PreRun();

			var flags:uint = 0;

			if (skipOffline)
			{
				// TA_SKIP_OFFLINE = 1
				flags |= 1;

				// TA_OFFLINE_SHOW_INET_ERR = 2
				if (offlineShowInetErr)
					flags |= 2;
			}

			FunctionProcessing = FUNC_IsGenuineEx;
			process.standardInput.writeInt(FUNC_IsGenuineEx);
			process.standardInput.writeUnsignedInt(flags);
			process.standardInput.writeUnsignedInt(daysBetweenChecks);
			process.standardInput.writeUnsignedInt(graceDaysOnInetErr);
		}

		/**
			Get the number of days until the next time that the TA_IsGenuineEx() function contacts
			the LimeLM activation servers to reverify the activation.

			You must use the same "nDaysBetweenChecks" and "nGraceDaysOnInetErr" parameters you passed
			to TA_IsGenuineEx() using the GENUINE_OPTIONS structure.

			The number of days remaining until the next reverification with the servers will be put
			in the "DaysRemaining" variable. And if the customer is already in the grace period, then
			the "DaysRemaining" remaining will reflect the number of days left in the grace period and
			"inGracePeriod" will be 1.

			If both nDaysBetweenChecks and the nGraceDaysOnInetErr have passed, then "DaysRemaining"
			will be 0.

			Also, if TurboActivate determines that system date, time, or timezone are fraudulent then
			"DaysRemaining" will be 0.


			Returns: TA_OK on success. Handle all other return codes as failures.

			Possible return codes: TA_OK, TA_FAIL, TA_E_ACTIVATE, TA_E_INVALID_HANDLE
		 */
		public function GenuineDays(daysBetweenChecks:uint, graceDaysOnInetErr:uint):void
		{
			PreRun();

			var flags:uint = 0;

			FunctionProcessing = FUNC_GenuineDays;
			process.standardInput.writeInt(FUNC_GenuineDays);
			process.standardInput.writeUnsignedInt(daysBetweenChecks);
			process.standardInput.writeUnsignedInt(graceDaysOnInetErr);
		}

		/**
		 * Checks if the product key installed for this product is valid. This does NOT check if the product key is activated or genuine. Use IsActivated() and IsGenuine() instead.
		 */
		public function IsProductKeyValid():void
		{
			PreRun();

			FunctionProcessing = FUNC_IsProductKeyValid;
			process.standardInput.writeInt(FUNC_IsProductKeyValid);
		}

		/**
		 * Sets the custom proxy to be used by functions that connect to the internet.
		 * @param proxy The proxy to use. Proxy must be in the form "http://username:password@host:port/".
		 */
		public function SetCustomProxy(proxy:String):void
		{
			PreRun();

			FunctionProcessing = FUNC_SetCustomProxy;
			process.standardInput.writeInt(FUNC_SetCustomProxy);
			process.standardInput.writeUTF(proxy);
		}

		/**
		 * Get the number of trial days remaining.
		 */
		public function TrialDaysRemaining(flags:uint):void
		{
			PreRun();

			FunctionProcessing = FUNC_TrialDaysRemaining;
			process.standardInput.writeInt(FUNC_TrialDaysRemaining);
			process.standardInput.writeUnsignedInt(flags);
		}

		/**
		 * Begins the trial the first time it's called. Calling it again will validate the trial data hasn't been tampered with.
		 * 
		 * @param flags Whether to create the trial either user-wide or system-wide. Valid flags are TA_SYSTEM and TA_USER.
		 */
		public function UseTrial(trialCb:Function, flags:uint, extraData:String = null):void
		{
			PreRun();

			trialCallback = trialCb;

			FunctionProcessing = FUNC_UseTrial;
			process.standardInput.writeInt(FUNC_UseTrial);
			process.standardInput.writeUnsignedInt(flags);

			var hasExtraData:Boolean = !(extraData === null || extraData === "");

			process.standardInput.writeBoolean(hasExtraData);

			if (hasExtraData)
				process.standardInput.writeUTF(extraData);
		}

		/**
		 * Extends the trial using a trial extension created in LimeLM.
		 * @param trialExtension The trial extension generated from LimeLM.
		 */
		public function ExtendTrial(trialExtension:String, flags:uint):void
		{
			PreRun();

			FunctionProcessing = FUNC_ExtendTrial;
			process.standardInput.writeInt(FUNC_ExtendTrial);
			process.standardInput.writeUTF(trialExtension);
			process.standardInput.writeUnsignedInt(flags);
		}
	}
}