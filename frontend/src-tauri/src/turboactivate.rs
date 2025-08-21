#![allow(dead_code)]
// TurboActivate integration for license management
// This is a stubbed version for development/testing
// In production, replace with actual TurboActivate library integration

use serde::{Deserialize, Serialize};
use std::sync::Mutex;
use once_cell::sync::Lazy;
use sysinfo::System;

// Error codes
#[allow(dead_code)]
pub const TA_OK: i32 = 0;
#[allow(dead_code)]
pub const TA_FAIL: i32 = 1;
#[allow(dead_code)]
pub const TA_E_PDETS: i32 = 2;
#[allow(dead_code)]
pub const TA_E_ACTIVATE: i32 = 3;
#[allow(dead_code)]
pub const TA_E_INET: i32 = 4;
#[allow(dead_code)]
pub const TA_E_INUSE: i32 = 5;
#[allow(dead_code)]
pub const TA_E_REVOKED: i32 = 6;
#[allow(dead_code)]
pub const TA_E_INVALID_KEY: i32 = 7;
#[allow(dead_code)]
pub const TA_E_EXPIRED: i32 = 8;
#[allow(dead_code)]
pub const TA_E_TRIAL_EXPIRED: i32 = 9;

// Mock state for development
static MOCK_STATE: Lazy<Mutex<MockLicenseState>> = Lazy::new(|| {
    Mutex::new(MockLicenseState {
        is_activated: false,
        is_genuine: true,
        trial_days: 30,
        product_key: None,
    })
});

#[derive(Clone)]
struct MockLicenseState {
    is_activated: bool,
    is_genuine: bool,
    trial_days: u32,
    product_key: Option<String>,
}

pub struct TurboActivate {
    _dat_file: Option<String>,
}

impl TurboActivate {
    pub fn new(dat_file: Option<&str>) -> Result<Self, String> {
        // In development, always succeed
        Ok(TurboActivate {
            _dat_file: dat_file.map(|s| s.to_string()),
        })
    }
    
    pub fn activate(&self, product_key: &str, _extra_data: Option<&str>) -> Result<(), String> {
        // Mock activation
        let mut state = MOCK_STATE.lock().unwrap();
        
        // Simple validation - just check if key has right format
        if product_key.len() >= 16 && product_key.contains('-') {
            state.is_activated = true;
            state.product_key = Some(product_key.to_string());
            Ok(())
        } else {
            Err("Invalid product key format".to_string())
        }
    }
    
    pub fn deactivate(&self, _erase_pdets: bool) -> Result<(), String> {
        let mut state = MOCK_STATE.lock().unwrap();
        state.is_activated = false;
        state.product_key = None;
        Ok(())
    }
    
    pub fn is_activated(&self) -> Result<bool, String> {
        let state = MOCK_STATE.lock().unwrap();
        Ok(state.is_activated)
    }
    
    pub fn is_genuine(&self) -> Result<bool, String> {
        let state = MOCK_STATE.lock().unwrap();
        Ok(state.is_genuine && state.is_activated)
    }
    
    pub fn get_trial_days_remaining(&self) -> Result<u32, String> {
        let state = MOCK_STATE.lock().unwrap();
        if state.is_activated {
            Ok(0) // No trial needed if activated
        } else {
            Ok(state.trial_days)
        }
    }
    
    pub fn start_trial(&self) -> Result<(), String> {
        let mut state = MOCK_STATE.lock().unwrap();
        state.trial_days = 30; // Reset to 30 days
        Ok(())
    }
    
    pub fn get_hardware_id(&self) -> Result<String, String> {
        // Generate a hardware ID based on system info
        let mut sys = System::new_all();
        sys.refresh_all();
        
        let cpu_info = sys.cpus().first()
            .map(|cpu| cpu.brand())
            .unwrap_or("Unknown");
        
        // Try to get MAC address
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
        
        Ok(hw_id)
    }
    
    pub fn get_feature_value(&self, feature_name: &str) -> Result<String, String> {
        // Mock feature values
        match feature_name {
            "max_uploads" => Ok("unlimited".to_string()),
            "max_downloads" => Ok("unlimited".to_string()),
            "encryption" => Ok("enabled".to_string()),
            "premium" => {
                let state = MOCK_STATE.lock().unwrap();
                Ok(if state.is_activated { "true" } else { "false" }.to_string())
            }
            _ => Ok("".to_string())
        }
    }
}

// License status for API responses
#[derive(Serialize, Deserialize)]
pub struct LicenseStatus {
    pub is_activated: bool,
    pub is_genuine: bool,
    pub is_trial: bool,
    pub trial_days_remaining: u32,
    pub hardware_id: String,
    pub features: std::collections::HashMap<String, String>,
}

impl TurboActivate {
    pub fn get_license_status(&self) -> Result<LicenseStatus, String> {
        let state = MOCK_STATE.lock().unwrap();
        let mut features = std::collections::HashMap::new();
        
        features.insert("max_uploads".to_string(), "unlimited".to_string());
        features.insert("max_downloads".to_string(), "unlimited".to_string());
        features.insert("encryption".to_string(), "enabled".to_string());
        features.insert("premium".to_string(), 
            if state.is_activated { "true" } else { "false" }.to_string());
        
        Ok(LicenseStatus {
            is_activated: state.is_activated,
            is_genuine: state.is_genuine,
            is_trial: !state.is_activated && state.trial_days > 0,
            trial_days_remaining: if state.is_activated { 0 } else { state.trial_days },
            hardware_id: self.get_hardware_id().unwrap_or_default(),
            features,
        })
    }
}

// Tauri command handlers
pub async fn activate_license(key: String) -> Result<String, String> {
    let ta = TurboActivate::new(None)?;
    ta.activate(&key, None)?;
    Ok("License activated successfully".to_string())
}

pub async fn deactivate_license() -> Result<String, String> {
    let ta = TurboActivate::new(None)?;
    ta.deactivate(true)?;
    Ok("License deactivated".to_string())
}

pub async fn get_license_status() -> Result<LicenseStatus, String> {
    let ta = TurboActivate::new(None)?;
    ta.get_license_status()
}

pub async fn start_trial() -> Result<String, String> {
    let ta = TurboActivate::new(None)?;
    ta.start_trial()?;
    Ok("Trial started - 30 days remaining".to_string())
}

pub async fn get_hardware_id() -> Result<String, String> {
    let ta = TurboActivate::new(None)?;
    ta.get_hardware_id()
}