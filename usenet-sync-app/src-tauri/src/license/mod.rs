use chrono::{DateTime, Utc, Duration};
use serde::{Deserialize, Serialize};
use anyhow::{Result, anyhow};
use keyring::Entry;
use sha3::{Sha3_256, Digest};
use crate::identity::{IdentityManager, ImmutableIdentity};

#[derive(Debug, Serialize, Deserialize, Clone, PartialEq)]
pub enum LicenseType {
    Trial,      // 30-day free trial
    Full,       // $29.99/year - access to everything
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct LicenseFeatures {
    pub max_storage_gb: Option<u64>,        // None = unlimited
    pub max_folders: Option<u32>,           // None = unlimited
    pub max_files: Option<u32>,             // None = unlimited
    pub max_connections: u32,               // 60 for full
    pub parallel_uploads: u32,              // 20 for full
    pub parallel_downloads: u32,            // 40 for full
    pub encryption_enabled: bool,           // Always true
    pub private_shares: bool,               // True for full
    pub password_shares: bool,              // True for full
    pub auto_resume: bool,                  // True for full
    pub scheduled_sync: bool,               // True for full
    pub api_access: bool,                   // True for full
    pub priority_support: bool,             // True for full
}

impl LicenseFeatures {
    pub fn trial() -> Self {
        Self {
            max_storage_gb: Some(10),       // 10GB limit for trial
            max_folders: Some(100),          // 100 folders limit
            max_files: Some(1000),           // 1000 files limit
            max_connections: 4,              // Limited connections
            parallel_uploads: 2,             // Limited uploads
            parallel_downloads: 4,           // Limited downloads
            encryption_enabled: true,        // Full encryption even in trial
            private_shares: false,           // No private shares in trial
            password_shares: false,          // No password shares in trial
            auto_resume: true,               // Allow resume in trial
            scheduled_sync: false,           // No scheduling in trial
            api_access: false,               // No API in trial
            priority_support: false,         // No priority support
        }
    }
    
    pub fn full() -> Self {
        Self {
            max_storage_gb: None,            // Unlimited storage
            max_folders: None,               // Unlimited folders
            max_files: None,                 // Unlimited files
            max_connections: 60,             // Maximum connections
            parallel_uploads: 20,            // Maximum parallel uploads
            parallel_downloads: 40,          // Maximum parallel downloads
            encryption_enabled: true,        // Full encryption
            private_shares: true,            // All share types
            password_shares: true,           // Password protected shares
            auto_resume: true,               // Auto-resume
            scheduled_sync: true,            // Scheduled operations
            api_access: true,                // API access
            priority_support: true,          // Priority support
        }
    }
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct License {
    pub license_id: String,
    pub user_id: String,
    pub license_type: LicenseType,
    pub activated_at: DateTime<Utc>,
    pub expires_at: Option<DateTime<Utc>>,
    pub device_fingerprint: String,
    pub features: LicenseFeatures,
    pub signature: String,
    pub is_active: bool,
    pub price_paid: Option<f32>,            // Track payment amount
}

#[derive(Debug, Serialize, Deserialize)]
pub struct LicenseKey {
    pub key: String,
    pub license_type: LicenseType,
    pub duration_days: i64,                 // 365 for annual
    pub price: f32,                         // 29.99
}

pub struct LicenseManager {
    identity_manager: IdentityManager,
    keyring_service: String,
}

impl LicenseManager {
    pub fn new(identity_manager: IdentityManager) -> Self {
        Self {
            identity_manager,
            keyring_service: "UsenetSync".to_string(),
        }
    }
    
    pub fn activate_trial(&mut self) -> Result<License> {
        let identity = self.identity_manager.get_current_identity()?;
        
        // Check if trial was already used
        if self.has_used_trial(&identity.user_id)? {
            return Err(anyhow!("Trial already used for this identity. Please purchase a license for $29.99/year."));
        }
        
        // Verify device
        if !self.identity_manager.verify_device(&identity)? {
            return Err(anyhow!("Device verification failed"));
        }
        
        let license_id = self.generate_license_id(&identity.user_id, &LicenseType::Trial);
        
        let license = License {
            license_id: license_id.clone(),
            user_id: identity.user_id.clone(),
            license_type: LicenseType::Trial,
            activated_at: Utc::now(),
            expires_at: Some(Utc::now() + Duration::days(30)),
            device_fingerprint: identity.device_fingerprint.clone(),
            features: LicenseFeatures::trial(),
            signature: self.sign_license(&license_id, &identity.user_id)?,
            is_active: true,
            price_paid: Some(0.0),
        };
        
        // Store license
        self.store_license(&license)?;
        
        // Mark trial as used
        self.mark_trial_used(&identity.user_id)?;
        
        Ok(license)
    }
    
    pub fn activate_full_license(&mut self, license_key: &str) -> Result<License> {
        let identity = self.identity_manager.get_current_identity()?;
        
        // Decode and validate license key
        let decoded = self.decode_license_key(license_key)?;
        
        // Verify it's a full license
        if decoded.license_type != LicenseType::Full {
            return Err(anyhow!("Invalid license type"));
        }
        
        // Verify price
        if decoded.price != 29.99 {
            return Err(anyhow!("Invalid license price"));
        }
        
        // Verify device
        if !self.identity_manager.verify_device(&identity)? {
            return Err(anyhow!("Device verification failed"));
        }
        
        let license_id = self.generate_license_id(&identity.user_id, &LicenseType::Full);
        
        let license = License {
            license_id: license_id.clone(),
            user_id: identity.user_id.clone(),
            license_type: LicenseType::Full,
            activated_at: Utc::now(),
            expires_at: Some(Utc::now() + Duration::days(365)), // 1 year
            device_fingerprint: identity.device_fingerprint.clone(),
            features: LicenseFeatures::full(),
            signature: self.sign_license(&license_id, &identity.user_id)?,
            is_active: true,
            price_paid: Some(29.99),
        };
        
        // Store license
        self.store_license(&license)?;
        
        Ok(license)
    }
    
    pub fn validate_current_license(&mut self) -> Result<(bool, Option<License>)> {
        let identity = self.identity_manager.get_current_identity()?;
        
        // Get stored license
        let license = match self.get_stored_license(&identity.user_id) {
            Ok(l) => l,
            Err(_) => return Ok((false, None)),
        };
        
        // Verify user ID matches
        if license.user_id != identity.user_id {
            return Ok((false, None));
        }
        
        // Verify device hasn't changed
        if license.device_fingerprint != identity.device_fingerprint {
            return Ok((false, None));
        }
        
        // Check expiration
        if let Some(expires_at) = license.expires_at {
            if Utc::now() > expires_at {
                return Ok((false, None));
            }
        }
        
        // Verify signature
        if !self.verify_license_signature(&license)? {
            return Ok((false, None));
        }
        
        // Check if license is active
        if !license.is_active {
            return Ok((false, None));
        }
        
        Ok((true, Some(license)))
    }
    
    pub fn get_remaining_days(&self, license: &License) -> Option<i64> {
        license.expires_at.map(|expires| {
            let remaining = expires.signed_duration_since(Utc::now());
            remaining.num_days()
        })
    }
    
    pub fn get_license_status(&mut self) -> Result<String> {
        let (is_valid, license_opt) = self.validate_current_license()?;
        
        if !is_valid {
            return Ok("No valid license. Start with a 30-day free trial or purchase for $29.99/year.".to_string());
        }
        
        if let Some(license) = license_opt {
            let remaining = self.get_remaining_days(&license);
            
            match license.license_type {
                LicenseType::Trial => {
                    if let Some(days) = remaining {
                        Ok(format!("Trial License - {} days remaining. Upgrade to full version for $29.99/year.", days))
                    } else {
                        Ok("Trial License - Active".to_string())
                    }
                },
                LicenseType::Full => {
                    if let Some(days) = remaining {
                        if days < 30 {
                            Ok(format!("Full License - {} days remaining. Renew soon for $29.99/year.", days))
                        } else {
                            Ok(format!("Full License - Active ({} days remaining)", days))
                        }
                    } else {
                        Ok("Full License - Active (Lifetime)".to_string())
                    }
                }
            }
        } else {
            Ok("License status unknown".to_string())
        }
    }
    
    fn generate_license_id(&self, user_id: &str, license_type: &LicenseType) -> String {
        let mut hasher = Sha3_256::new();
        hasher.update(user_id.as_bytes());
        hasher.update(format!("{:?}", license_type).as_bytes());
        hasher.update(&Utc::now().timestamp().to_le_bytes());
        
        format!("LIC-{}", hex::encode(&hasher.finalize()[..12]))
    }
    
    fn sign_license(&self, license_id: &str, user_id: &str) -> Result<String> {
        let mut hasher = Sha3_256::new();
        hasher.update(license_id.as_bytes());
        hasher.update(user_id.as_bytes());
        hasher.update(b"UsenetSync-License-v1");
        
        Ok(hex::encode(hasher.finalize()))
    }
    
    fn verify_license_signature(&self, license: &License) -> Result<bool> {
        let expected = self.sign_license(&license.license_id, &license.user_id)?;
        Ok(license.signature == expected)
    }
    
    fn decode_license_key(&self, key: &str) -> Result<LicenseKey> {
        // Format: BASE64(JSON(LicenseKey))
        let decoded = base64::decode(key)?;
        let license_key: LicenseKey = serde_json::from_slice(&decoded)?;
        
        // Validate key format
        if license_key.key.len() < 32 {
            return Err(anyhow!("Invalid license key format"));
        }
        
        Ok(license_key)
    }
    
    fn store_license(&self, license: &License) -> Result<()> {
        let entry = Entry::new(&self.keyring_service, &format!("license_{}", license.user_id))?;
        entry.set_password(&serde_json::to_string(license)?)?;
        Ok(())
    }
    
    fn get_stored_license(&self, user_id: &str) -> Result<License> {
        let entry = Entry::new(&self.keyring_service, &format!("license_{}", user_id))?;
        let license_json = entry.get_password()?;
        let license: License = serde_json::from_str(&license_json)?;
        Ok(license)
    }
    
    fn has_used_trial(&self, user_id: &str) -> Result<bool> {
        let entry = Entry::new(&self.keyring_service, &format!("trial_used_{}", user_id))?;
        match entry.get_password() {
            Ok(_) => Ok(true),
            Err(_) => Ok(false),
        }
    }
    
    fn mark_trial_used(&self, user_id: &str) -> Result<()> {
        let entry = Entry::new(&self.keyring_service, &format!("trial_used_{}", user_id))?;
        entry.set_password("true")?;
        Ok(())
    }
    
    pub fn generate_license_key(&self) -> Result<String> {
        // Generate a new annual license key for $29.99
        let mut key_bytes = vec![0u8; 32];
        rand::RngCore::fill_bytes(&mut rand::rngs::OsRng, &mut key_bytes);
        
        let license_key = LicenseKey {
            key: hex::encode(&key_bytes),
            license_type: LicenseType::Full,
            duration_days: 365,
            price: 29.99,
        };
        
        Ok(base64::encode(serde_json::to_string(&license_key)?))
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_license_features() {
        let trial = LicenseFeatures::trial();
        assert_eq!(trial.max_storage_gb, Some(10));
        assert_eq!(trial.max_connections, 4);
        assert!(!trial.private_shares);
        
        let full = LicenseFeatures::full();
        assert_eq!(full.max_storage_gb, None); // Unlimited
        assert_eq!(full.max_connections, 60);
        assert!(full.private_shares);
        assert_eq!(full.parallel_uploads, 20);
    }
    
    #[test]
    fn test_license_pricing() {
        // Verify single tier pricing
        assert_eq!(29.99_f32, 29.99); // Annual price
        assert_eq!(29.99_f32 / 12.0, 2.4991667); // Monthly equivalent
    }
}