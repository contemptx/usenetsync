use ed25519_dalek::{Keypair, PublicKey, SecretKey, Signature, Signer, Verifier};
use keyring::Entry;
use serde::{Deserialize, Serialize};
use sha3::{Sha3_256, Digest};
use rand::rngs::OsRng;
use zeroize::Zeroize;
use std::time::{SystemTime, UNIX_EPOCH};
use anyhow::{Result, anyhow};
use sysinfo::{System, SystemExt, NetworkExt};

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct ImmutableIdentity {
    pub user_id: String,
    pub public_key: Vec<u8>,
    pub created_at: i64,
    pub device_fingerprint: String,
    pub version: u32,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct IdentityProof {
    pub user_id: String,
    pub timestamp: i64,
    pub nonce: Vec<u8>,
    pub signature: Vec<u8>,
}

pub struct IdentityManager {
    keyring_service: String,
    keyring_user: String,
    identity_cache: Option<ImmutableIdentity>,
}

impl IdentityManager {
    pub fn new() -> Self {
        Self {
            keyring_service: "UsenetSync".to_string(),
            keyring_user: "Identity".to_string(),
            identity_cache: None,
        }
    }
    
    pub fn initialize_identity(&mut self) -> Result<(ImmutableIdentity, bool)> {
        // Check if identity already exists
        let entry = Entry::new(&self.keyring_service, &self.keyring_user)?;
        
        if let Ok(existing) = entry.get_password() {
            // Identity exists - deserialize and return
            let identity: ImmutableIdentity = serde_json::from_str(&existing)?;
            self.identity_cache = Some(identity.clone());
            return Ok((identity, false)); // false = not new
        }
        
        // Generate new identity (ONE TIME ONLY)
        let mut csprng = OsRng;
        let keypair = Keypair::generate(&mut csprng);
        let device_fingerprint = self.generate_device_fingerprint()?;
        
        // Create deterministic user ID from public key
        let mut hasher = Sha3_256::new();
        hasher.update(&keypair.public.to_bytes());
        hasher.update(device_fingerprint.as_bytes());
        let user_id = format!("USN-{}", hex::encode(&hasher.finalize()[..16]));
        
        let identity = ImmutableIdentity {
            user_id: user_id.clone(),
            public_key: keypair.public.to_bytes().to_vec(),
            created_at: SystemTime::now()
                .duration_since(UNIX_EPOCH)?
                .as_secs() as i64,
            device_fingerprint,
            version: 1,
        };
        
        // Store private key in OS keychain (PERMANENT)
        let private_entry = Entry::new(&self.keyring_service, &format!("{}_private", user_id))?;
        private_entry.set_password(&base64::encode(&keypair.secret.to_bytes()))?;
        
        // Store identity
        entry.set_password(&serde_json::to_string(&identity)?)?;
        
        self.identity_cache = Some(identity.clone());
        
        Ok((identity, true)) // true = new identity created
    }
    
    pub fn get_current_identity(&mut self) -> Result<ImmutableIdentity> {
        if let Some(ref identity) = self.identity_cache {
            return Ok(identity.clone());
        }
        
        let (identity, _) = self.initialize_identity()?;
        Ok(identity)
    }
    
    fn generate_device_fingerprint(&self) -> Result<String> {
        let mut hasher = Sha3_256::new();
        let mut sys = System::new_all();
        sys.refresh_all();
        
        // CPU information
        if let Some(cpu) = sys.cpus().first() {
            hasher.update(cpu.brand().as_bytes());
            hasher.update(&cpu.frequency().to_le_bytes());
        }
        
        // Memory
        hasher.update(&sys.total_memory().to_le_bytes());
        
        // Hostname
        if let Some(hostname) = sys.host_name() {
            hasher.update(hostname.as_bytes());
        }
        
        // Network interfaces (MAC addresses)
        for (interface_name, data) in sys.networks() {
            hasher.update(interface_name.as_bytes());
            hasher.update(data.mac_address().to_string().as_bytes());
        }
        
        // OS info
        if let Some(os_name) = sys.name() {
            hasher.update(os_name.as_bytes());
        }
        
        if let Some(kernel_version) = sys.kernel_version() {
            hasher.update(kernel_version.as_bytes());
        }
        
        Ok(hex::encode(hasher.finalize()))
    }
    
    pub fn verify_device(&self, identity: &ImmutableIdentity) -> Result<bool> {
        let current_fingerprint = self.generate_device_fingerprint()?;
        Ok(current_fingerprint == identity.device_fingerprint)
    }
    
    pub fn sign_data(&self, identity: &ImmutableIdentity, data: &[u8]) -> Result<Vec<u8>> {
        // Retrieve private key from keychain
        let private_entry = Entry::new(&self.keyring_service, &format!("{}_private", identity.user_id))?;
        let private_key_b64 = private_entry.get_password()?;
        let private_key_bytes = base64::decode(&private_key_b64)?;
        
        let secret = SecretKey::from_bytes(&private_key_bytes)?;
        let public = PublicKey::from_bytes(&identity.public_key)?;
        let keypair = Keypair {
            secret,
            public,
        };
        
        let signature = keypair.sign(data);
        Ok(signature.to_bytes().to_vec())
    }
    
    pub fn verify_signature(&self, identity: &ImmutableIdentity, data: &[u8], signature: &[u8]) -> Result<bool> {
        let public_key = PublicKey::from_bytes(&identity.public_key)?;
        let signature = Signature::from_bytes(signature)?;
        
        match public_key.verify(data, &signature) {
            Ok(_) => Ok(true),
            Err(_) => Ok(false),
        }
    }
    
    pub fn create_identity_proof(&self, identity: &ImmutableIdentity) -> Result<IdentityProof> {
        let timestamp = SystemTime::now()
            .duration_since(UNIX_EPOCH)?
            .as_secs() as i64;
        
        let mut nonce = vec![0u8; 32];
        rand::RngCore::fill_bytes(&mut OsRng, &mut nonce);
        
        let mut proof_data = Vec::new();
        proof_data.extend_from_slice(identity.user_id.as_bytes());
        proof_data.extend_from_slice(&timestamp.to_le_bytes());
        proof_data.extend_from_slice(&nonce);
        
        let signature = self.sign_data(identity, &proof_data)?;
        
        Ok(IdentityProof {
            user_id: identity.user_id.clone(),
            timestamp,
            nonce,
            signature,
        })
    }
    
    pub fn export_public_identity(&self, identity: &ImmutableIdentity) -> String {
        // Export only public information (no private keys)
        let public_export = serde_json::json!({
            "user_id": identity.user_id,
            "public_key": hex::encode(&identity.public_key),
            "created_at": identity.created_at,
            "version": identity.version,
        });
        
        base64::encode(public_export.to_string())
    }
    
    // NO RECOVERY METHODS - BY DESIGN
    // NO BACKUP METHODS - BY DESIGN
    // NO CLOUD SYNC - BY DESIGN
    // NO PASSWORD RESET - BY DESIGN
    
    pub fn destroy_identity(&mut self) -> Result<()> {
        // WARNING: This permanently destroys the identity
        // There is NO way to recover after this
        
        if let Some(identity) = &self.identity_cache {
            // Delete private key
            let private_entry = Entry::new(&self.keyring_service, &format!("{}_private", identity.user_id))?;
            let _ = private_entry.delete_password();
            
            // Delete identity
            let entry = Entry::new(&self.keyring_service, &self.keyring_user)?;
            let _ = entry.delete_password();
            
            // Clear cache
            self.identity_cache = None;
        }
        
        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_identity_generation() {
        let mut manager = IdentityManager::new();
        let result = manager.initialize_identity();
        assert!(result.is_ok());
        
        let (identity, is_new) = result.unwrap();
        assert!(identity.user_id.starts_with("USN-"));
        assert_eq!(identity.public_key.len(), 32);
        assert!(is_new);
        
        // Second call should return existing identity
        let result2 = manager.initialize_identity();
        assert!(result2.is_ok());
        let (identity2, is_new2) = result2.unwrap();
        assert_eq!(identity.user_id, identity2.user_id);
        assert!(!is_new2);
    }
    
    #[test]
    fn test_device_verification() {
        let manager = IdentityManager::new();
        let fingerprint1 = manager.generate_device_fingerprint().unwrap();
        let fingerprint2 = manager.generate_device_fingerprint().unwrap();
        assert_eq!(fingerprint1, fingerprint2);
    }
}