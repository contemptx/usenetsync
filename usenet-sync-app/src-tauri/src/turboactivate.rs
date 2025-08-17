use std::os::raw::{c_char, c_int, c_uint};
use std::sync::Mutex;
use once_cell::sync::Lazy;
use serde::{Deserialize, Serialize};

const VERSION_GUID: &str = "lzyz4mi2lgoawqj5bkjjvjceygsqfdi";

// Error codes from TurboActivate
#[derive(Debug)]
pub enum TAError {
    Ok = 0,
    Fail = 1,
    InvalidHandle = 2,
    InvalidProductKey = 3,
    Offline = 4,
    VMNotAllowed = 5,
    InvalidArgs = 6,
    KeyAlreadyUsed = 7,
    Revoked = 8,
    GuidMismatch = 9,
    NoMoreDeactivations = 10,
    TrialExpired = 11,
    TrialCorrupted = 12,
    MustBeDeactivated = 13,
    MustReactivate = 14,
    InvalidTrialExtension = 15,
    GracePeriodExpired = 16,
    TrialExtensionExpired = 17,
    ExcessActivations = 18,
    InVm = 19,
    NetworkError = 20,
    InetError = 21,
    InetTimeout = 22,
    ServerError = 23,
    InvalidResponse = 24,
    NotActivated = 25,
    InvalidProductFile = 26,
    AuthenticationNeeded = 27,
    InvalidProductInfo = 28,
    BackendSystemError = 29,
    BadHandleOrProductFile = 30,
    IsGenuineFailed = 31,
    TooManyProducts = 32,
    InvalidIntegration = 33,
    UnsupportedOs = 34,
    UnsupportedArch = 35,
}

// External C functions (would link to actual TurboActivate library)
extern "C" {
    fn TA_PDetsFromPath(path: *const c_char) -> c_uint;
    fn TA_Activate(handle: c_uint, extra_data: *const c_char) -> c_int;
    fn TA_ActivateEx(handle: c_uint, options: *const c_char) -> c_int;
    fn TA_Deactivate(handle: c_uint, erase_pdets: c_int) -> c_int;
    fn TA_IsActivated(handle: c_uint) -> c_int;
    fn TA_IsGenuine(handle: c_uint) -> c_int;
    fn TA_IsGenuineEx(handle: c_uint, days_between_checks: c_uint, grace_days: c_uint, offline: c_int) -> c_int;
    fn TA_TrialDaysRemaining(handle: c_uint, days_remaining: *mut c_uint) -> c_int;
    fn TA_UseTrial(handle: c_uint, flags: c_uint, extra_data: *const c_char) -> c_int;
    fn TA_CheckAndSavePKey(handle: c_uint, product_key: *const c_char, flags: c_uint) -> c_int;
    fn TA_GetPKey(handle: c_uint, product_key: *mut c_char, buffer_size: c_int) -> c_int;
    fn TA_GetFeatureValue(handle: c_uint, feature_name: *const c_char, feature_value: *mut c_char, buffer_size: c_int) -> c_int;
    fn TA_GetExtraData(handle: c_uint, extra_data: *mut c_char, buffer_size: c_int) -> c_int;
}

static TA_HANDLE: Lazy<Mutex<Option<c_uint>>> = Lazy::new(|| Mutex::new(None));

#[derive(Debug, Serialize, Deserialize)]
pub struct LicenseStatus {
    pub activated: bool,
    pub genuine: bool,
    pub trial: bool,
    pub trial_days: Option<u32>,
    pub hardware_id: String,
    pub tier: String,
}

pub struct TurboActivate;

impl TurboActivate {
    pub fn new(_dat_file_path: Option<&str>) -> Result<Self, String> {
        // In a real implementation, this would initialize the TurboActivate library
        // For now, we'll create a mock implementation
        
        let mut handle_guard = TA_HANDLE.lock().unwrap();
        if handle_guard.is_none() {
            // Mock: In reality, would call TA_PDetsFromPath
            *handle_guard = Some(1); // Mock handle
        }
        
        Ok(TurboActivate)
    }
    
    pub fn activate(&self, license_key: &str) -> Result<bool, String> {
        // Mock implementation
        // In reality, would validate the key format and call TA_Activate
        
        if license_key.len() == 19 && license_key.chars().filter(|c| *c == '-').count() == 3 {
            Ok(true)
        } else {
            Err("Invalid license key format".to_string())
        }
    }
    
    pub fn deactivate(&self) -> Result<(), String> {
        // Mock implementation
        Ok(())
    }
    
    pub fn is_activated(&self) -> bool {
        // Mock implementation
        // In reality, would call TA_IsActivated
        false
    }
    
    pub fn is_genuine(&self) -> bool {
        // Mock implementation
        // In reality, would call TA_IsGenuine
        true
    }
    
    pub fn get_trial_days_remaining(&self) -> Result<u32, String> {
        // Mock implementation
        Ok(14) // 14 days trial
    }
    
    pub fn start_trial(&self) -> Result<u32, String> {
        // Mock implementation
        Ok(14)
    }
    
    pub fn get_hardware_id(&self) -> Result<String, String> {
        // Mock implementation
        // In reality, would generate based on actual hardware
        Ok("MOCK-HW-ID-123456789".to_string())
    }
    
    pub fn get_feature_value(&self, feature: &str) -> Result<String, String> {
        // Mock implementation
        match feature {
            "tier" => Ok("pro".to_string()),
            "max_file_size" => Ok("10737418240".to_string()), // 10GB
            "max_connections" => Ok("30".to_string()),
            _ => Ok("".to_string())
        }
    }
    
    pub fn get_status(&self) -> LicenseStatus {
        LicenseStatus {
            activated: self.is_activated(),
            genuine: self.is_genuine(),
            trial: !self.is_activated() && self.get_trial_days_remaining().unwrap_or(0) > 0,
            trial_days: if !self.is_activated() {
                self.get_trial_days_remaining().ok()
            } else {
                None
            },
            hardware_id: self.get_hardware_id().unwrap_or_else(|_| "unknown".to_string()),
            tier: self.get_feature_value("tier").unwrap_or_else(|_| "basic".to_string()),
        }
    }
}