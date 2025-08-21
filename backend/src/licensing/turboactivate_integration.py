#!/usr/bin/env python3
"""
TurboActivate Integration for UsenetSync
Full implementation with your Version GUID: lzyz4mi2lgoawqj5bkjjvjceygsqfdi
"""

import ctypes
import platform
import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, Tuple
from enum import IntEnum
from dataclasses import dataclass

# Configure logging
logger = logging.getLogger(__name__)

# TurboActivate Version GUID for UsenetSync 1.0
VERSION_GUID = "lzyz4mi2lgoawqj5bkjjvjceygsqfdi"

# TurboActivate Error Codes
class TAError(IntEnum):
    """TurboActivate error codes"""
    TA_OK = 0
    TA_FAIL = 1
    TA_E_ACTIVATE = 2
    TA_E_INET = 3
    TA_E_INUSE = 4
    TA_E_REVOKED = 5
    TA_E_GUID = 6
    TA_E_PDETS = 7
    TA_E_TRIAL = 8
    TA_E_TRIAL_EUSED = 9
    TA_E_TRIAL_EEXP = 10
    TA_E_EXPIRED = 11
    TA_E_REACTIVATE = 12
    TA_E_COM = 13
    TA_E_INSUFFICIENT_BUFFER = 14
    TA_E_PERMISSION = 15
    TA_E_INVALID_FLAGS = 16
    TA_E_IN_VM = 17
    TA_E_EDATA_LONG = 18
    TA_E_INVALID_ARGS = 19
    TA_E_KEY_FOR_TURBOFLOAT = 20
    TA_E_INET_DELAYED = 21
    TA_E_FEATURES_CHANGED = 22
    TA_E_ANDROID_NOT_INIT = 23
    TA_E_NO_MORE_DEACTIVATIONS = 24
    TA_E_ACCOUNT_CANCELED = 25
    TA_E_ALREADY_ACTIVATED = 26
    TA_E_INVALID_HANDLE = 27
    TA_E_TOO_MANY_INSTANCES = 28
    TA_E_MUST_USE_TRIAL = 29
    TA_E_MUST_BE_DEACTIVATED = 30
    TA_E_MUST_SPECIFY_TRIAL_TYPE = 31
    TA_E_REACTIVATE_REVOKED = 32

# Genuine Flags
class TAFlags(IntEnum):
    """TurboActivate flags for IsGenuineEx"""
    TA_SKIP_OFFLINE = 1
    TA_OFFLINE_SHOW_INET_ERR = 2
    TA_DISALLOW_VM = 4
    TA_VERIFIED_TRIAL = 8
    TA_UNVERIFIED_TRIAL = 16
    TA_HAS_NOT_EXPIRED = 32

@dataclass
class ActivationInfo:
    """Activation information"""
    is_activated: bool
    is_genuine: bool
    trial_days_remaining: Optional[int] = None
    features: Dict[str, str] = None
    hardware_id: Optional[str] = None

class TurboActivate:
    """
    TurboActivate wrapper for UsenetSync
    Handles licensing, activation, and verification
    """
    
    def __init__(self, dat_file_path: Optional[str] = None):
        """
        Initialize TurboActivate with the UsenetSync product details
        
        Args:
            dat_file_path: Path to TurboActivate.dat file (optional if using PDetsFromPath)
        """
        self.lib = None
        self.handle = None
        self.version_guid = VERSION_GUID
        self.dat_file = dat_file_path or self._find_dat_file()
        
        # Load the appropriate library
        self._load_library()
        
        # Initialize TurboActivate
        self._initialize()
    
    def _find_dat_file(self) -> str:
        """Find TurboActivate.dat in common locations"""
        possible_paths = [
            Path(__file__).parent / "data" / "TurboActivate.dat",  # Primary location
            Path(__file__).parent / "TurboActivate.dat",
            Path.cwd() / "TurboActivate.dat",
            Path(sys.executable).parent / "TurboActivate.dat",
            Path("/workspace") / "TurboActivate.dat",
            Path("/workspace/src/licensing/data") / "TurboActivate.dat",
        ]
        
        for path in possible_paths:
            if path.exists():
                logger.info(f"Found TurboActivate.dat at: {path}")
                return str(path)
        
        raise FileNotFoundError(
            "TurboActivate.dat not found. Download from: "
            "https://wyday.com/limelm/version/10798/TurboActivate.dat"
        )
    
    def _load_library(self):
        """Load the TurboActivate library for the current platform"""
        system = platform.system()
        machine = platform.machine().lower()
        
        # Base path for libraries
        lib_base = Path(__file__).parent.parent.parent / "libs"
        
        # Determine library name and path
        if system == "Windows":
            if "64" in machine or "amd64" in machine:
                lib_name = "TurboActivate64.dll"
            else:
                lib_name = "TurboActivate.dll"
            lib_path = lib_base / "windows" / lib_name
            
            # Try to load from path, fallback to system
            try:
                if lib_path.exists():
                    self.lib = ctypes.CDLL(str(lib_path))
                else:
                    self.lib = ctypes.CDLL(lib_name)
            except OSError:
                self.lib = ctypes.CDLL(lib_name)
            
        elif system == "Darwin":  # macOS
            lib_name = "libTurboActivate.dylib"
            lib_path = lib_base / "macos" / lib_name
            
            try:
                if lib_path.exists():
                    self.lib = ctypes.CDLL(str(lib_path))
                else:
                    self.lib = ctypes.CDLL(lib_name)
            except OSError:
                self.lib = ctypes.CDLL(lib_name)
            
        elif system == "Linux":
            if "64" in machine or "x86_64" in machine:
                lib_name = "libTurboActivate.so"
            else:
                lib_name = "libTurboActivate.x86.so"
            lib_path = lib_base / "linux" / lib_name
            
            try:
                if lib_path.exists():
                    self.lib = ctypes.CDLL(str(lib_path))
                else:
                    self.lib = ctypes.CDLL(lib_name)
            except OSError:
                self.lib = ctypes.CDLL(lib_name)
        else:
            raise OSError(f"Unsupported platform: {system}")
        
        # Set up function signatures
        self._setup_functions()
        
        logger.info(f"Loaded TurboActivate library: {lib_name}")
    
    def _setup_functions(self):
        """Set up ctypes function signatures"""
        # TA_PDetsFromPath
        self.lib.TA_PDetsFromPath.argtypes = [ctypes.c_char_p]
        self.lib.TA_PDetsFromPath.restype = ctypes.c_int
        
        # TA_GetHandle
        self.lib.TA_GetHandle.argtypes = [ctypes.c_char_p]
        self.lib.TA_GetHandle.restype = ctypes.c_uint32
        
        # TA_Activate
        self.lib.TA_Activate.argtypes = [ctypes.c_uint32, ctypes.c_void_p]
        self.lib.TA_Activate.restype = ctypes.c_int
        
        # TA_ActivateEx
        self.lib.TA_ActivateEx.argtypes = [ctypes.c_uint32, ctypes.c_void_p, ctypes.c_void_p]
        self.lib.TA_ActivateEx.restype = ctypes.c_int
        
        # TA_CheckAndSavePKey
        self.lib.TA_CheckAndSavePKey.argtypes = [ctypes.c_uint32, ctypes.c_char_p, ctypes.c_uint32]
        self.lib.TA_CheckAndSavePKey.restype = ctypes.c_int
        
        # TA_Deactivate
        self.lib.TA_Deactivate.argtypes = [ctypes.c_uint32, ctypes.c_char]
        self.lib.TA_Deactivate.restype = ctypes.c_int
        
        # TA_GetPKey
        self.lib.TA_GetPKey.argtypes = [ctypes.c_uint32, ctypes.c_char_p, ctypes.c_int]
        self.lib.TA_GetPKey.restype = ctypes.c_int
        
        # TA_IsActivated
        self.lib.TA_IsActivated.argtypes = [ctypes.c_uint32]
        self.lib.TA_IsActivated.restype = ctypes.c_int
        
        # TA_IsGenuine
        self.lib.TA_IsGenuine.argtypes = [ctypes.c_uint32]
        self.lib.TA_IsGenuine.restype = ctypes.c_int
        
        # TA_IsGenuineEx
        self.lib.TA_IsGenuineEx.argtypes = [ctypes.c_uint32, ctypes.c_uint32, ctypes.c_void_p, ctypes.c_uint32]
        self.lib.TA_IsGenuineEx.restype = ctypes.c_int
        
        # TA_TrialDaysRemaining
        self.lib.TA_TrialDaysRemaining.argtypes = [ctypes.c_uint32, ctypes.c_uint32, ctypes.POINTER(ctypes.c_uint32)]
        self.lib.TA_TrialDaysRemaining.restype = ctypes.c_int
        
        # TA_GetFeatureValue
        self.lib.TA_GetFeatureValue.argtypes = [ctypes.c_uint32, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_int]
        self.lib.TA_GetFeatureValue.restype = ctypes.c_int
        
        # TA_UseTrial
        self.lib.TA_UseTrial.argtypes = [ctypes.c_uint32, ctypes.c_uint32, ctypes.c_void_p]
        self.lib.TA_UseTrial.restype = ctypes.c_int
        
        # TA_GetExtraData
        self.lib.TA_GetExtraData.argtypes = [ctypes.c_uint32, ctypes.c_char_p, ctypes.c_int]
        self.lib.TA_GetExtraData.restype = ctypes.c_int
        
        # TA_GetHardwareID
        self.lib.TA_GetHardwareID.argtypes = [ctypes.c_uint32, ctypes.c_char_p, ctypes.c_int]
        self.lib.TA_GetHardwareID.restype = ctypes.c_int
    
    def _initialize(self):
        """Initialize TurboActivate with product details"""
        # Load product details from dat file
        result = self.lib.TA_PDetsFromPath(self.dat_file.encode('utf-8'))
        if result != TAError.TA_OK:
            raise RuntimeError(f"Failed to load product details from {self.dat_file}: {self._get_error_string(result)}")
        
        # Get handle for this instance
        self.handle = self.lib.TA_GetHandle(self.version_guid.encode('utf-8'))
        if self.handle == 0:
            raise RuntimeError("Failed to get TurboActivate handle")
        
        logger.info(f"TurboActivate initialized with handle: {self.handle}")
    
    def _get_error_string(self, error_code: int) -> str:
        """Get human-readable error string"""
        error_messages = {
            TAError.TA_FAIL: "General failure",
            TAError.TA_E_ACTIVATE: "Activation failed",
            TAError.TA_E_INET: "No internet connection",
            TAError.TA_E_INUSE: "Product key already in use",
            TAError.TA_E_REVOKED: "Product key has been revoked",
            TAError.TA_E_GUID: "Invalid product GUID",
            TAError.TA_E_PDETS: "Invalid product details",
            TAError.TA_E_TRIAL: "Trial error",
            TAError.TA_E_EXPIRED: "License has expired",
            TAError.TA_E_IN_VM: "Running in virtual machine",
            TAError.TA_E_ALREADY_ACTIVATED: "Already activated",
            TAError.TA_E_ACCOUNT_CANCELED: "Account has been canceled",
        }
        return error_messages.get(error_code, f"Unknown error ({error_code})")
    
    def activate(self, product_key: str, extra_data: Optional[str] = None) -> Tuple[bool, str]:
        """
        Activate the product with a license key
        
        Args:
            product_key: The license key to activate
            extra_data: Optional extra data to store with activation
            
        Returns:
            Tuple of (success, message)
        """
        try:
            # Prepare activation options
            class ACTIVATE_OPTIONS(ctypes.Structure):
                _fields_ = [
                    ("nLength", ctypes.c_uint32),
                    ("sExtraData", ctypes.c_char_p)
                ]
            
            options = None
            if extra_data:
                options = ACTIVATE_OPTIONS()
                options.nLength = ctypes.sizeof(ACTIVATE_OPTIONS)
                options.sExtraData = extra_data.encode('utf-8')
                result = self.lib.TA_ActivateEx(
                    self.handle,
                    options,
                    product_key.encode('utf-8') if product_key else None
                )
            else:
                result = self.lib.TA_Activate(
                    self.handle,
                    product_key.encode('utf-8') if product_key else None
                )
            
            if result == TAError.TA_OK:
                logger.info("Product activated successfully")
                return True, "Product activated successfully"
            elif result == TAError.TA_E_ALREADY_ACTIVATED:
                logger.info("Product already activated")
                return True, "Product already activated"
            else:
                error_msg = self._get_error_string(result)
                logger.error(f"Activation failed: {error_msg}")
                return False, error_msg
                
        except Exception as e:
            logger.error(f"Activation error: {e}")
            return False, str(e)
    
    def deactivate(self, erase_product_key: bool = True) -> Tuple[bool, str]:
        """
        Deactivate the product
        
        Args:
            erase_product_key: Whether to erase the stored product key
            
        Returns:
            Tuple of (success, message)
        """
        try:
            result = self.lib.TA_Deactivate(
                self.handle,
                ctypes.c_char(1 if erase_product_key else 0)
            )
            
            if result == TAError.TA_OK:
                logger.info("Product deactivated successfully")
                return True, "Product deactivated successfully"
            else:
                error_msg = self._get_error_string(result)
                logger.error(f"Deactivation failed: {error_msg}")
                return False, error_msg
                
        except Exception as e:
            logger.error(f"Deactivation error: {e}")
            return False, str(e)
    
    def is_activated(self) -> bool:
        """Check if the product is activated"""
        result = self.lib.TA_IsActivated(self.handle)
        return result == TAError.TA_OK
    
    def is_genuine(self, skip_offline: bool = False, allow_vm: bool = True) -> bool:
        """
        Check if the current activation is genuine
        
        Args:
            skip_offline: Skip offline checks
            allow_vm: Allow running in virtual machines
            
        Returns:
            True if genuine, False otherwise
        """
        flags = 0
        if skip_offline:
            flags |= TAFlags.TA_SKIP_OFFLINE
        if not allow_vm:
            flags |= TAFlags.TA_DISALLOW_VM
        
        if flags:
            result = self.lib.TA_IsGenuineEx(self.handle, flags, None, 0)
        else:
            result = self.lib.TA_IsGenuine(self.handle)
        
        return result == TAError.TA_OK
    
    def check_and_save_product_key(self, product_key: str) -> Tuple[bool, str]:
        """
        Check if a product key is valid and save it
        
        Args:
            product_key: The product key to check
            
        Returns:
            Tuple of (success, message)
        """
        try:
            # Flags: 1 = Verify the product key is valid
            result = self.lib.TA_CheckAndSavePKey(
                self.handle,
                product_key.encode('utf-8'),
                1
            )
            
            if result == TAError.TA_OK:
                logger.info("Product key is valid and saved")
                return True, "Product key is valid and saved"
            else:
                error_msg = self._get_error_string(result)
                logger.error(f"Product key validation failed: {error_msg}")
                return False, error_msg
                
        except Exception as e:
            logger.error(f"Product key check error: {e}")
            return False, str(e)
    
    def get_product_key(self) -> Optional[str]:
        """Get the stored product key"""
        buffer = ctypes.create_string_buffer(256)
        result = self.lib.TA_GetPKey(self.handle, buffer, 256)
        
        if result == TAError.TA_OK:
            return buffer.value.decode('utf-8')
        return None
    
    def get_trial_days_remaining(self, use_verified_trial: bool = True) -> Optional[int]:
        """
        Get the number of trial days remaining
        
        Args:
            use_verified_trial: Use verified (online) trial
            
        Returns:
            Number of days remaining or None if not in trial
        """
        flags = TAFlags.TA_VERIFIED_TRIAL if use_verified_trial else TAFlags.TA_UNVERIFIED_TRIAL
        days_remaining = ctypes.c_uint32()
        
        result = self.lib.TA_TrialDaysRemaining(
            self.handle,
            flags,
            ctypes.byref(days_remaining)
        )
        
        if result == TAError.TA_OK:
            return days_remaining.value
        return None
    
    def use_trial(self, use_verified_trial: bool = True, extra_data: Optional[str] = None) -> Tuple[bool, str]:
        """
        Start using trial
        
        Args:
            use_verified_trial: Use verified (online) trial
            extra_data: Optional extra data to store
            
        Returns:
            Tuple of (success, message)
        """
        try:
            flags = TAFlags.TA_VERIFIED_TRIAL if use_verified_trial else TAFlags.TA_UNVERIFIED_TRIAL
            
            # Prepare trial options
            class TRIAL_OPTIONS(ctypes.Structure):
                _fields_ = [
                    ("nLength", ctypes.c_uint32),
                    ("sExtraData", ctypes.c_char_p)
                ]
            
            options = None
            if extra_data:
                options = TRIAL_OPTIONS()
                options.nLength = ctypes.sizeof(TRIAL_OPTIONS)
                options.sExtraData = extra_data.encode('utf-8')
            
            result = self.lib.TA_UseTrial(
                self.handle,
                flags,
                ctypes.byref(options) if options else None
            )
            
            if result == TAError.TA_OK:
                days = self.get_trial_days_remaining(use_verified_trial)
                msg = f"Trial started successfully. {days} days remaining"
                logger.info(msg)
                return True, msg
            else:
                error_msg = self._get_error_string(result)
                logger.error(f"Trial activation failed: {error_msg}")
                return False, error_msg
                
        except Exception as e:
            logger.error(f"Trial activation error: {e}")
            return False, str(e)
    
    def get_feature_value(self, feature_name: str) -> Optional[str]:
        """
        Get the value of a licensed feature
        
        Args:
            feature_name: Name of the feature
            
        Returns:
            Feature value or None if not found
        """
        buffer = ctypes.create_string_buffer(256)
        result = self.lib.TA_GetFeatureValue(
            self.handle,
            feature_name.encode('utf-8'),
            buffer,
            256
        )
        
        if result == TAError.TA_OK:
            return buffer.value.decode('utf-8')
        return None
    
    def get_hardware_id(self) -> Optional[str]:
        """Get the hardware ID for this machine"""
        buffer = ctypes.create_string_buffer(256)
        result = self.lib.TA_GetHardwareID(self.handle, buffer, 256)
        
        if result == TAError.TA_OK:
            return buffer.value.decode('utf-8')
        return None
    
    def get_extra_data(self) -> Optional[str]:
        """Get extra data stored with activation"""
        buffer = ctypes.create_string_buffer(256)
        result = self.lib.TA_GetExtraData(self.handle, buffer, 256)
        
        if result == TAError.TA_OK:
            return buffer.value.decode('utf-8')
        return None
    
    def get_activation_info(self) -> ActivationInfo:
        """Get comprehensive activation information"""
        info = ActivationInfo(
            is_activated=self.is_activated(),
            is_genuine=self.is_genuine(),
            hardware_id=self.get_hardware_id()
        )
        
        # Get trial info if applicable
        trial_days = self.get_trial_days_remaining()
        if trial_days is not None:
            info.trial_days_remaining = trial_days
        
        # Get all feature values
        features = {}
        for feature in ['max_file_size', 'max_connections', 'max_shares', 'tier']:
            value = self.get_feature_value(feature)
            if value:
                features[feature] = value
        
        if features:
            info.features = features
        
        return info
    
    def verify_at_runtime(self) -> bool:
        """
        Perform runtime verification checks
        Should be called periodically during application runtime
        """
        # Check if still activated
        if not self.is_activated():
            logger.warning("Product is not activated")
            return False
        
        # Check if genuine (with offline fallback)
        if not self.is_genuine(skip_offline=False):
            logger.warning("Product activation is not genuine")
            return False
        
        # Check if not expired
        result = self.lib.TA_IsGenuineEx(
            self.handle,
            TAFlags.TA_HAS_NOT_EXPIRED,
            None,
            0
        )
        
        if result != TAError.TA_OK:
            logger.warning("Product license has expired")
            return False
        
        return True


# Singleton instance
_turboactivate_instance = None

def get_turboactivate() -> TurboActivate:
    """Get or create the TurboActivate singleton instance"""
    global _turboactivate_instance
    if _turboactivate_instance is None:
        _turboactivate_instance = TurboActivate()
    return _turboactivate_instance


# Integration with UsenetSync
class UsenetSyncLicense:
    """
    High-level license management for UsenetSync
    Integrates TurboActivate with the application
    """
    
    def __init__(self):
        self.ta = get_turboactivate()
        self.check_interval = 3600  # Check every hour
        self.last_check = 0
    
    def require_valid_license(self):
        """
        Decorator to require valid license for functions
        
        Usage:
            @license.require_valid_license()
            def create_share(...):
                ...
        """
        def decorator(func):
            def wrapper(*args, **kwargs):
                if not self.is_licensed():
                    raise PermissionError("Valid license required for this operation")
                return func(*args, **kwargs)
            return wrapper
        return decorator
    
    def is_licensed(self) -> bool:
        """Check if application is properly licensed"""
        import time
        
        # Periodic re-verification
        current_time = time.time()
        if current_time - self.last_check > self.check_interval:
            self.last_check = current_time
            return self.ta.verify_at_runtime()
        
        # Quick check
        return self.ta.is_activated() and self.ta.is_genuine(skip_offline=True)
    
    def activate_with_key(self, license_key: str) -> Tuple[bool, str]:
        """Activate UsenetSync with a license key"""
        # Store user info as extra data
        import getpass
        import socket
        
        extra_data = json.dumps({
            'user': getpass.getuser(),
            'hostname': socket.gethostname(),
            'activated_at': str(datetime.now())
        })
        
        return self.ta.activate(license_key, extra_data)
    
    def start_trial(self) -> Tuple[bool, str]:
        """Start a trial period"""
        return self.ta.use_trial(use_verified_trial=True)
    
    def get_license_status(self) -> Dict[str, Any]:
        """Get current license status"""
        info = self.ta.get_activation_info()
        
        return {
            'licensed': info.is_activated and info.is_genuine,
            'activated': info.is_activated,
            'genuine': info.is_genuine,
            'trial': info.trial_days_remaining is not None,
            'trial_days': info.trial_days_remaining,
            'features': info.features or {},
            'hardware_id': info.hardware_id
        }
    
    def get_max_file_size(self) -> int:
        """Get maximum file size allowed by license"""
        value = self.ta.get_feature_value('max_file_size')
        return int(value) if value else 10 * 1024 * 1024 * 1024  # 10GB default
    
    def get_max_connections(self) -> int:
        """Get maximum concurrent connections allowed"""
        value = self.ta.get_feature_value('max_connections')
        return int(value) if value else 30
    
    def get_tier(self) -> str:
        """Get license tier (basic, pro, enterprise)"""
        return self.ta.get_feature_value('tier') or 'basic'


# Example usage
if __name__ == "__main__":
    # Initialize license system
    license_mgr = UsenetSyncLicense()
    
    # Check license status
    status = license_mgr.get_license_status()
    print(f"License Status: {json.dumps(status, indent=2)}")
    
    # Example: Activate with a key
    # success, msg = license_mgr.activate_with_key("YOUR-LICENSE-KEY-HERE")
    # print(f"Activation: {msg}")
    
    # Example: Start trial
    # success, msg = license_mgr.start_trial()
    # print(f"Trial: {msg}")
    
    # Example: Protected function
    @license_mgr.require_valid_license()
    def create_share(files):
        print(f"Creating share with {len(files)} files...")
        # Share creation logic here
    
    # This will raise PermissionError if not licensed
    # create_share(['file1.txt', 'file2.txt'])