// TurboActivate integration for license management
use std::ffi::{CString, CStr};
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
    NotActivated = 11,
    AlreadyActivated = 15,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct LicenseStatus {
    pub activated: bool,
    pub genuine: bool,
    pub trial: bool,
    pub hardware_id: String,
    pub tier: String,
}

static TA_HANDLE: Lazy<Mutex<Option<c_uint>>> = Lazy::new(|| Mutex::new(None));

// Real TurboActivate library bindings
#[link(name = "TurboActivate")]
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

pub struct TurboActivate {
    handle: c_uint,
}

impl TurboActivate {
    pub fn new(dat_file_path: Option<&str>) -> Result<Self, String> {
        let mut handle_guard = TA_HANDLE.lock().unwrap();
        
        if handle_guard.is_none() {
            let handle = if let Some(path) = dat_file_path {
                let c_path = CString::new(path).map_err(|e| e.to_string())?;
                unsafe { TA_PDetsFromPath(c_path.as_ptr()) }
            } else {
                // Use default TurboActivate.dat location
                let default_path = if cfg!(windows) {
                    "C:\\ProgramData\\UsenetSync\\TurboActivate.dat"
                } else {
                    "/etc/usenetsync/TurboActivate.dat"
                };
                let c_path = CString::new(default_path).map_err(|e| e.to_string())?;
                unsafe { TA_PDetsFromPath(c_path.as_ptr()) }
            };
            
            if handle == 0 {
                return Err("Failed to initialize TurboActivate".to_string());
            }
            
            *handle_guard = Some(handle);
        }
        
        Ok(TurboActivate {
            handle: handle_guard.unwrap(),
        })
    }
    
    pub fn activate(&self, license_key: &str) -> Result<bool, String> {
        let c_key = CString::new(license_key).map_err(|e| e.to_string())?;
        let result = unsafe { TA_CheckAndSavePKey(self.handle, c_key.as_ptr(), 0) };
        
        if result != 0 {
            return Err(format!("Invalid license key: {}", result));
        }
        
        let result = unsafe { TA_Activate(self.handle, std::ptr::null()) };
        
        match result {
            0 => Ok(true),
            15 => Ok(true), // Already activated
            _ => Err(format!("Activation failed: {}", result))
        }
    }
    
    pub fn deactivate(&self) -> Result<(), String> {
        let result = unsafe { TA_Deactivate(self.handle, 0) };
        
        if result == 0 {
            Ok(())
        } else {
            Err(format!("Deactivation failed: {}", result))
        }
    }
    
    pub fn is_activated(&self) -> bool {
        unsafe { TA_IsActivated(self.handle) == 0 }
    }
    
    pub fn is_genuine(&self) -> bool {
        // Check genuine with 7 days between checks, 14 days grace period
        unsafe { TA_IsGenuineEx(self.handle, 7, 14, 0) == 0 }
    }
    
    pub fn get_trial_days_remaining(&self) -> Result<u32, String> {
        let mut days: c_uint = 0;
        let result = unsafe { TA_TrialDaysRemaining(self.handle, &mut days) };
        
        if result == 0 {
            Ok(days)
        } else {
            Err(format!("Failed to get trial days: {}", result))
        }
    }
    
    pub fn start_trial(&self) -> Result<u32, String> {
        let result = unsafe { TA_UseTrial(self.handle, 0, std::ptr::null()) };
        
        if result == 0 {
            self.get_trial_days_remaining()
        } else {
            Err(format!("Failed to start trial: {}", result))
        }
    }
    
    pub fn get_hardware_id(&self) -> Result<String, String> {
        // Use system info to generate hardware ID
        use sysinfo::System;
        let sys = System::new_all();
        
        let cpu_info = sys.cpus().first()
            .map(|_cpu| "GenericCPU")
            .unwrap_or("Unknown");
        
        let mac_address = mac_address::get_mac_address()
            .ok()
            .flatten()
            .map(|m| m.to_string())
            .unwrap_or_else(|| "00:00:00:00:00:00".to_string());
        
        let hw_id = format!("{}-{}-{}", 
            cpu_info.chars().take(8).collect::<String>(),
            mac_address.replace(":", ""),
            sys.total_memory()
        );
        
        use sha2::{Sha256, Digest};
        let mut hasher = Sha256::new();
        hasher.update(hw_id.as_bytes());
        let result = hasher.finalize();
        
        Ok(format!("{:X}", result))
    }
    
    pub fn get_feature_value(&self, feature: &str) -> Result<String, String> {
        let mut buffer = vec![0u8; 256];
        let c_feature = CString::new(feature).map_err(|e| e.to_string())?;
        
        let result = unsafe {
            TA_GetFeatureValue(
                self.handle,
                c_feature.as_ptr(),
                buffer.as_mut_ptr() as *mut c_char,
                buffer.len() as c_int
            )
        };
        
        if result == 0 {
            let c_str = unsafe { CStr::from_ptr(buffer.as_ptr() as *const c_char) };
            Ok(c_str.to_string_lossy().to_string())
        } else {
            // Default values if feature not found
            match feature {
                "tier" => Ok("basic".to_string()),
                "max_connections" => Ok("10".to_string()),
                "max_speed" => Ok("unlimited".to_string()),
                _ => Err(format!("Feature not found: {}", feature))
            }
        }
    }
    
    pub fn get_status(&self) -> LicenseStatus {
        LicenseStatus {
            activated: self.is_activated(),
            genuine: self.is_genuine(),
            trial: self.get_trial_days_remaining().unwrap_or(0) > 0,
            hardware_id: self.get_hardware_id().unwrap_or_default(),
            tier: self.get_feature_value("tier").unwrap_or_else(|_| "basic".to_string()),
        }
    }
}
