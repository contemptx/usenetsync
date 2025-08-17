use chrono::{DateTime, Utc, Duration};
use serde::{Deserialize, Serialize};
use anyhow::{Result, anyhow};
use keyring::Entry;
use sha3::{Sha3_256, Digest};
use crate::identity::{IdentityManager, ImmutableIdentity};

#[derive(Debug, Serialize, Deserialize, Clone, PartialEq)]
pub enum LicenseType {
    Trial,
    Personal,
    Professional,
    Enterprise,
    Lifetime,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct LicenseFeatures {
    pub max_storage_gb: Option<u64>,
    pub max_folders: Option<u32>,
    pub max_files: Option<u32>,
    pub max_connections: u32,
    pub parallel_uploads: u32,
    pub parallel_downloads: u32,
    pub encryption_enabled: bool,
    pub private_shares: bool,
    pub password_shares: bool,
    pub auto_resume: bool,
    pub scheduled_sync: bool,
    pub api_access: bool,
    pub priority_support: bool,
}

impl LicenseFeatures {
    pub fn trial() -> Self {
        Self {
            max_storage_gb: Some(10),
            max_folders: Some(100),
            max_files: Some(1000),
            max_connections: 2,
            parallel_uploads: 1,
            parallel_downloads: 2,
            encryption_enabled: true,
            private_shares: false,
            password_shares: false,
            auto_resume: false,
            scheduled_sync: false,
            api_access: false,
            priority_support: false,
        }
    }
    
    pub fn personal() -> Self {
        Self {
            max_storage_gb: Some(1000), // 1TB
            max_folders: Some(10000),
            max_files: Some(100000),
            max_connections: 10,
            parallel_uploads: 4,
            parallel_downloads: 8,
            encryption_enabled: true,
            private_shares: true,
            password_shares: true,
            auto_resume: true,
            scheduled_sync: true,
            api_access: false,
            priority_support: false,
        }
    }
    
    pub fn professional() -> Self {
        Self {
            max_storage_gb: Some(10000), // 10TB
            max_folders: None, // Unlimited
            max_files: None, // Unlimited
            max_connections: 30,
            parallel_uploads: 10,
            parallel_downloads: 20,
            encryption_enabled: true,
            private_shares: true,
            password_shares: true,
            auto_resume: true,
            scheduled_sync: true,
            api_access: true,
            priority_support: true,
        }
    }
    
    pub fn enterprise() -> Self {
        Self {
            max_storage_gb: None, // Unlimited
            max_folders: None,
            max_files: None,
            max_connections: 60,
            parallel_uploads: 20,
            parallel_downloads: 40,
            encryption_enabled: true,
            private_shares: true,
            password_shares: true,
            auto_resume: true,
            scheduled_sync: true,
            api_access: true,
            priority_support: true,
        }
    }
    
    pub fn lifetime() -> Self {
        Self::enterprise() // Same as enterprise but permanent
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
    pub activation_count: u32,
    pub max_activations: u32,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct LicenseKey {
    pub key: String,
    pub license_type: LicenseType,
    pub duration_days: Option<i64>,
    pub max_activations: u32,
    pub features: LicenseFeatures,
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
            return Err(anyhow!("Trial already used for this identity"));
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
            activation_count: 1,
            max_activations: 1,
        };
        
        // Store license
        self.store_license(&license)?;
        
        // Mark trial as used
        self.mark_trial_used(&identity.user_id)?;
        
        Ok(license)
    }
    
    pub fn activate_paid_license(&mut self, license_key: &str) -> Result<License> {
        let identity = self.identity_manager.get_current_identity()?;
        
        // Decode and validate license key
        let decoded = self.decode_license_key(license_key)?;
        
        // Verify device
        if !self.identity_manager.verify_device(&identity)? {
            return Err(anyhow!("Device verification failed"));
        }
        
        // Check activation limit
        let activation_count = self.get_activation_count(&decoded.key)?;
        if activation_count >= decoded.max_activations {
            return Err(anyhow!("License activation limit reached"));
        }
        
        let license_id = self.generate_license_id(&identity.user_id, &decoded.license_type);
        
        let expires_at = decoded.duration_days.map(|days| Utc::now() + Duration::days(days));
        
        let license = License {
            license_id: license_id.clone(),
            user_id: identity.user_id.clone(),
            license_type: decoded.license_type.clone(),
            activated_at: Utc::now(),
            expires_at,
            device_fingerprint: identity.device_fingerprint.clone(),
            features: decoded.features.clone(),
            signature: self.sign_license(&license_id, &identity.user_id)?,
            is_active: true,
            activation_count: activation_count + 1,
            max_activations: decoded.max_activations,
        };
        
        // Store license
        self.store_license(&license)?;
        
        // Record activation
        self.record_activation(&decoded.key, &identity.user_id)?;
        
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
    
    pub fn deactivate_license(&mut self) -> Result<()> {
        let identity = self.identity_manager.get_current_identity()?;
        
        // Get current license
        let mut license = self.get_stored_license(&identity.user_id)?;
        
        // Mark as inactive
        license.is_active = false;
        
        // Update stored license
        self.store_license(&license)?;
        
        Ok(())
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
    
    fn get_activation_count(&self, license_key: &str) -> Result<u32> {
        // In production, this would check against a license server
        // For now, check local storage
        let entry = Entry::new(&self.keyring_service, &format!("activations_{}", license_key))?;
        match entry.get_password() {
            Ok(count) => Ok(count.parse::<u32>().unwrap_or(0)),
            Err(_) => Ok(0),
        }
    }
    
    fn record_activation(&self, license_key: &str, user_id: &str) -> Result<()> {
        // Record activation locally
        let count = self.get_activation_count(license_key)?;
        let entry = Entry::new(&self.keyring_service, &format!("activations_{}", license_key))?;
        entry.set_password(&(count + 1).to_string())?;
        
        // Also record which user activated
        let activation_entry = Entry::new(&self.keyring_service, &format!("activation_{}_{}", license_key, count + 1))?;
        activation_entry.set_password(user_id)?;
        
        Ok(())
    }
    
    pub fn generate_license_key(&self, license_type: LicenseType, duration_days: Option<i64>, max_activations: u32) -> Result<String> {
        // Generate a new license key (for admin use)
        let mut key_bytes = vec![0u8; 32];
        rand::RngCore::fill_bytes(&mut rand::rngs::OsRng, &mut key_bytes);
        
        let features = match license_type {
            LicenseType::Trial => LicenseFeatures::trial(),
            LicenseType::Personal => LicenseFeatures::personal(),
            LicenseType::Professional => LicenseFeatures::professional(),
            LicenseType::Enterprise => LicenseFeatures::enterprise(),
            LicenseType::Lifetime => LicenseFeatures::lifetime(),
        };
        
        let license_key = LicenseKey {
            key: hex::encode(&key_bytes),
            license_type,
            duration_days,
            max_activations,
            features,
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
        assert_eq!(trial.max_connections, 2);
        assert!(!trial.private_shares);
        
        let enterprise = LicenseFeatures::enterprise();
        assert_eq!(enterprise.max_storage_gb, None); // Unlimited
        assert_eq!(enterprise.max_connections, 60);
        assert!(enterprise.private_shares);
    }
}