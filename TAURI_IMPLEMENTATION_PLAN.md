# Tauri + React Implementation Plan for UsenetSync
## Zero-Knowledge Architecture with Immutable Identifiers

## Table of Contents
1. [Architecture Overview](#architecture-overview)
2. [Security Implementation](#security-implementation)
3. [Project Structure](#project-structure)
4. [Implementation Phases](#implementation-phases)
5. [Code Examples](#code-examples)

## Architecture Overview

### Core Principles
- **Immutable Identity**: Once generated, user ID can NEVER be recovered
- **Zero-Knowledge**: No server knows user data or identity
- **Local-First**: All operations happen on user's machine
- **No Cloud**: No external dependencies for core functionality
- **Cryptographic Security**: Ed25519 keys stored in OS keychain

### Technology Stack
```
┌─────────────────────────────────────────────────────────────┐
│                     Tauri Application                        │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌────────────────────────┐  ┌────────────────────────┐    │
│  │     Rust Backend       │  │    React Frontend      │    │
│  │                        │  │                        │    │
│  │ • Identity Manager     │◄─┤ • Virtual Rendering    │    │
│  │ • PostgreSQL Client    │  │ • Immutable UI State   │    │
│  │ • File System Access   │  │ • Secure Forms         │    │
│  │ • Crypto Operations    │  │ • License Display      │    │
│  │ • NNTP Client         │  │ • Progress Tracking    │    │
│  └────────────────────────┘  └────────────────────────┘    │
│            ▲                            ▲                   │
│            └────────────┬───────────────┘                   │
│                         │                                   │
│         ┌───────────────▼──────────────────┐               │
│         │   Secure IPC Communication       │               │
│         │   • Encrypted messages           │               │
│         │   • Type-safe commands           │               │
│         └──────────────────────────────────┘               │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              OS Secure Storage                       │  │
│  │  • Windows: Credential Manager                       │  │
│  │  • macOS: Keychain                                  │  │
│  │  • Linux: Secret Service / KWallet                  │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## Security Implementation

### 1. Immutable Identity Generation

```rust
// src-tauri/src/identity.rs
use ed25519_dalek::{Keypair, PublicKey, SecretKey};
use keyring::Entry;
use serde::{Deserialize, Serialize};
use sha3::{Sha3_256, Digest};

#[derive(Serialize, Deserialize)]
pub struct ImmutableIdentity {
    pub user_id: String,
    pub public_key: Vec<u8>,
    pub created_at: i64,
    pub device_fingerprint: String,
}

pub struct IdentityManager {
    keyring_service: String,
    keyring_user: String,
}

impl IdentityManager {
    pub fn new() -> Self {
        Self {
            keyring_service: "UsenetSync",
            keyring_user: "Identity",
        }
    }
    
    pub fn initialize_identity(&self) -> Result<ImmutableIdentity, String> {
        // Check if identity already exists
        let entry = Entry::new(&self.keyring_service, &self.keyring_user)?;
        
        if let Ok(existing) = entry.get_password() {
            // Identity exists - deserialize and return
            return Ok(serde_json::from_str(&existing)?);
        }
        
        // Generate new identity (ONE TIME ONLY)
        let keypair = Keypair::generate(&mut OsRng);
        let device_fingerprint = self.generate_device_fingerprint()?;
        
        // Create deterministic user ID from public key
        let mut hasher = Sha3_256::new();
        hasher.update(&keypair.public.to_bytes());
        hasher.update(device_fingerprint.as_bytes());
        let user_id = format!("USN-{}", hex::encode(&hasher.finalize()[..16]));
        
        let identity = ImmutableIdentity {
            user_id: user_id.clone(),
            public_key: keypair.public.to_bytes().to_vec(),
            created_at: chrono::Utc::now().timestamp(),
            device_fingerprint,
        };
        
        // Store private key in OS keychain (PERMANENT)
        let private_entry = Entry::new(&self.keyring_service, &format!("{}_private", user_id))?;
        private_entry.set_password(&base64::encode(&keypair.secret.to_bytes()))?;
        
        // Store identity
        entry.set_password(&serde_json::to_string(&identity)?)?;
        
        // Show critical warning to user
        self.show_backup_warning(&identity);
        
        Ok(identity)
    }
    
    fn generate_device_fingerprint(&self) -> Result<String, String> {
        // Combine multiple hardware identifiers
        let mut hasher = Sha3_256::new();
        
        // CPU ID
        if let Ok(cpu_id) = self.get_cpu_id() {
            hasher.update(cpu_id.as_bytes());
        }
        
        // MAC addresses
        for mac in self.get_mac_addresses()? {
            hasher.update(mac.as_bytes());
        }
        
        // Disk serial
        if let Ok(disk_serial) = self.get_disk_serial() {
            hasher.update(disk_serial.as_bytes());
        }
        
        Ok(hex::encode(hasher.finalize()))
    }
    
    pub fn verify_device(&self, identity: &ImmutableIdentity) -> Result<bool, String> {
        let current_fingerprint = self.generate_device_fingerprint()?;
        Ok(current_fingerprint == identity.device_fingerprint)
    }
    
    // NO RECOVERY METHODS - BY DESIGN
    // NO EXPORT METHODS - BY DESIGN
    // NO CLOUD SYNC - BY DESIGN
}
```

### 2. Frontend Identity Display

```typescript
// src/components/IdentityManager.tsx
import React, { useState, useEffect } from 'react';
import { invoke } from '@tauri-apps/api/tauri';
import { Alert, AlertTitle, AlertDescription } from './ui/alert';
import { Copy, AlertTriangle, Lock } from 'lucide-react';

interface Identity {
  userId: string;
  publicKey: string;
  createdAt: number;
  deviceFingerprint: string;
}

export function IdentityManager() {
  const [identity, setIdentity] = useState<Identity | null>(null);
  const [isFirstRun, setIsFirstRun] = useState(false);
  const [copied, setCopied] = useState(false);
  
  useEffect(() => {
    loadIdentity();
  }, []);
  
  async function loadIdentity() {
    try {
      const result = await invoke<{ identity: Identity, isNew: boolean }>('get_identity');
      setIdentity(result.identity);
      setIsFirstRun(result.isNew);
    } catch (error) {
      console.error('Failed to load identity:', error);
    }
  }
  
  function copyToClipboard() {
    if (identity) {
      navigator.clipboard.writeText(identity.userId);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  }
  
  if (isFirstRun && identity) {
    return (
      <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
        <div className="bg-white dark:bg-gray-900 rounded-lg max-w-2xl w-full p-6">
          <div className="flex items-center gap-3 mb-4">
            <AlertTriangle className="h-8 w-8 text-red-500" />
            <h2 className="text-2xl font-bold text-red-500">
              CRITICAL: Save Your Identity
            </h2>
          </div>
          
          <Alert className="mb-6 border-red-500 bg-red-50 dark:bg-red-950">
            <AlertTitle>This is your ONLY chance to save this information!</AlertTitle>
            <AlertDescription>
              Your unique identity CANNOT be recovered if lost. There is no password reset,
              no email recovery, and no support that can help you. This is by design for
              maximum security and privacy.
            </AlertDescription>
          </Alert>
          
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-2">
                Your Unique Identity (User ID)
              </label>
              <div className="flex gap-2">
                <input
                  type="text"
                  value={identity.userId}
                  readOnly
                  className="flex-1 px-3 py-2 bg-gray-100 dark:bg-gray-800 rounded font-mono"
                />
                <button
                  onClick={copyToClipboard}
                  className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 flex items-center gap-2"
                >
                  <Copy className="h-4 w-4" />
                  {copied ? 'Copied!' : 'Copy'}
                </button>
              </div>
            </div>
            
            <div className="bg-yellow-50 dark:bg-yellow-950 p-4 rounded">
              <h3 className="font-semibold mb-2">⚠️ Important Instructions:</h3>
              <ol className="list-decimal list-inside space-y-1 text-sm">
                <li>Write this ID on paper and store it securely</li>
                <li>Save it in a password manager</li>
                <li>Do NOT share this with anyone</li>
                <li>Do NOT store it in cloud services</li>
                <li>If you lose this, you lose access FOREVER</li>
              </ol>
            </div>
            
            <div className="flex items-start gap-2">
              <input
                type="checkbox"
                id="understood"
                className="mt-1"
                onChange={(e) => {
                  if (e.target.checked) {
                    setTimeout(() => setIsFirstRun(false), 500);
                  }
                }}
              />
              <label htmlFor="understood" className="text-sm">
                I understand that if I lose this identity, I will permanently lose access
                to all my data and will need to start over with a new identity.
              </label>
            </div>
          </div>
        </div>
      </div>
    );
  }
  
  if (!identity) return null;
  
  return (
    <div className="fixed bottom-4 right-4 bg-white dark:bg-gray-900 rounded-lg shadow-lg p-3 flex items-center gap-3">
      <Lock className="h-4 w-4 text-green-500" />
      <span className="text-xs font-mono">{identity.userId.slice(0, 12)}...</span>
      <span className="text-xs text-gray-500">Secured</span>
    </div>
  );
}
```

### 3. License Management

```rust
// src-tauri/src/license.rs
use chrono::{DateTime, Utc, Duration};
use serde::{Deserialize, Serialize};

#[derive(Serialize, Deserialize, Clone)]
pub enum LicenseType {
    Trial,
    Personal,
    Professional,
    Enterprise,
}

#[derive(Serialize, Deserialize)]
pub struct License {
    pub user_id: String,
    pub license_type: LicenseType,
    pub activated_at: DateTime<Utc>,
    pub expires_at: Option<DateTime<Utc>>,
    pub device_fingerprint: String,
    pub features: Vec<String>,
    pub max_storage_gb: Option<u64>,
    pub signature: String,
}

pub struct LicenseManager {
    identity_manager: IdentityManager,
}

impl LicenseManager {
    pub fn activate_trial(&self) -> Result<License, String> {
        let identity = self.identity_manager.get_current_identity()?;
        
        // Check if trial was already used
        if self.has_used_trial(&identity.user_id)? {
            return Err("Trial already used for this identity".to_string());
        }
        
        let license = License {
            user_id: identity.user_id.clone(),
            license_type: LicenseType::Trial,
            activated_at: Utc::now(),
            expires_at: Some(Utc::now() + Duration::days(30)),
            device_fingerprint: identity.device_fingerprint,
            features: vec![
                "basic_sync".to_string(),
                "10gb_storage".to_string(),
            ],
            max_storage_gb: Some(10),
            signature: self.sign_license(&identity.user_id),
        };
        
        // Store locally
        self.store_license(&license)?;
        
        // Mark trial as used (permanent record)
        self.mark_trial_used(&identity.user_id)?;
        
        Ok(license)
    }
    
    pub fn activate_paid_license(&self, license_key: &str) -> Result<License, String> {
        let identity = self.identity_manager.get_current_identity()?;
        
        // Validate license key format (offline validation)
        let decoded = self.decode_license_key(license_key)?;
        
        // Verify license is for this user
        if decoded.user_id != identity.user_id {
            return Err("License is for a different identity".to_string());
        }
        
        // Verify device
        if !self.identity_manager.verify_device(&identity)? {
            return Err("License cannot be activated on this device".to_string());
        }
        
        // Create and store license
        let license = License {
            user_id: identity.user_id.clone(),
            license_type: decoded.license_type,
            activated_at: Utc::now(),
            expires_at: decoded.expires_at,
            device_fingerprint: identity.device_fingerprint,
            features: decoded.features,
            max_storage_gb: decoded.max_storage_gb,
            signature: self.sign_license(&identity.user_id),
        };
        
        self.store_license(&license)?;
        Ok(license)
    }
    
    pub fn validate_current_license(&self) -> Result<bool, String> {
        let identity = self.identity_manager.get_current_identity()?;
        let license = self.get_stored_license()?;
        
        // Verify user ID matches
        if license.user_id != identity.user_id {
            return Ok(false);
        }
        
        // Verify device hasn't changed
        if license.device_fingerprint != identity.device_fingerprint {
            return Ok(false);
        }
        
        // Check expiration
        if let Some(expires_at) = license.expires_at {
            if Utc::now() > expires_at {
                return Ok(false);
            }
        }
        
        // Verify signature
        if !self.verify_signature(&license) {
            return Ok(false);
        }
        
        Ok(true)
    }
}
```

## Project Structure

```
usenet-sync-tauri/
├── src-tauri/                    # Rust backend
│   ├── Cargo.toml
│   ├── tauri.conf.json
│   ├── src/
│   │   ├── main.rs              # Entry point
│   │   ├── identity.rs          # Identity management
│   │   ├── license.rs           # License management
│   │   ├── database.rs          # PostgreSQL interface
│   │   ├── crypto.rs            # Cryptographic operations
│   │   ├── nntp.rs              # NNTP client wrapper
│   │   ├── file_system.rs       # File operations
│   │   └── commands.rs          # Tauri commands
│   └── migrations/              # PostgreSQL migrations
│
├── src/                         # React frontend
│   ├── App.tsx
│   ├── main.tsx
│   ├── components/
│   │   ├── IdentityManager.tsx
│   │   ├── LicenseStatus.tsx
│   │   ├── FileExplorer.tsx
│   │   ├── VirtualSegmentGrid.tsx
│   │   ├── UploadQueue.tsx
│   │   └── ProgressTracker.tsx
│   ├── hooks/
│   │   ├── useIdentity.ts
│   │   ├── useLicense.ts
│   │   ├── useVirtualScroll.ts
│   │   └── useSegments.ts
│   ├── lib/
│   │   ├── crypto.ts           # Frontend crypto helpers
│   │   ├── storage.ts          # IndexedDB wrapper
│   │   └── commands.ts         # Tauri command wrappers
│   └── styles/
│
├── package.json
├── tsconfig.json
├── vite.config.ts
└── README.md
```

## Implementation Phases

### Phase 1: Core Security (Week 1)
```bash
# Initialize Tauri project
npm create tauri-app@latest usenet-sync -- --template react-ts
cd usenet-sync

# Add Rust dependencies
cd src-tauri
cargo add ed25519-dalek keyring sha3 hex
cargo add tokio --features full
cargo add sqlx --features postgres,runtime-tokio-rustls
cargo add serde serde_json
```

**Tasks:**
- [ ] Implement identity generation and storage
- [ ] Create OS keychain integration
- [ ] Build device fingerprinting
- [ ] Add identity verification
- [ ] Create first-run experience

### Phase 2: Database Integration (Week 2)
```rust
// src-tauri/src/database.rs
use sqlx::{PgPool, postgres::PgPoolOptions};

pub struct DatabaseManager {
    pool: PgPool,
}

impl DatabaseManager {
    pub async fn new(identity: &ImmutableIdentity) -> Result<Self, String> {
        // Use identity for database encryption key
        let db_key = self.derive_db_key(&identity.user_id)?;
        
        // Connect to local PostgreSQL
        let pool = PgPoolOptions::new()
            .max_connections(20)
            .connect("postgresql://localhost/usenet_sync")
            .await?;
            
        // Run migrations
        sqlx::migrate!("./migrations").run(&pool).await?;
        
        Ok(Self { pool })
    }
    
    pub async fn get_segments_paginated(
        &self,
        folder_id: &str,
        offset: i64,
        limit: i64
    ) -> Result<Vec<Segment>, String> {
        // Efficient pagination for 30M segments
        let segments = sqlx::query_as!(
            Segment,
            r#"
            SELECT * FROM segments 
            WHERE folder_id = $1
            ORDER BY segment_index
            LIMIT $2 OFFSET $3
            "#,
            folder_id,
            limit,
            offset
        )
        .fetch_all(&self.pool)
        .await?;
        
        Ok(segments)
    }
}
```

**Tasks:**
- [ ] PostgreSQL connection management
- [ ] Migration system
- [ ] Sharded table implementation
- [ ] Streaming queries for large datasets
- [ ] Connection pooling

### Phase 3: Frontend Core (Week 3)
```typescript
// src/App.tsx
import { useState, useEffect } from 'react';
import { IdentityManager } from './components/IdentityManager';
import { VirtualFileTree } from './components/VirtualFileTree';
import { SegmentGrid } from './components/SegmentGrid';
import { useIdentity } from './hooks/useIdentity';
import { useLicense } from './hooks/useLicense';

function App() {
  const { identity, loading: identityLoading } = useIdentity();
  const { license, isValid } = useLicense();
  
  if (identityLoading) {
    return <LoadingScreen />;
  }
  
  if (!identity) {
    return <IdentitySetup />;
  }
  
  if (!isValid) {
    return <LicenseActivation identity={identity} />;
  }
  
  return (
    <div className="app h-screen flex flex-col">
      <Header identity={identity} license={license} />
      
      <div className="flex-1 flex overflow-hidden">
        <aside className="w-80 border-r">
          <VirtualFileTree
            rootId="root"
            onSelect={handleFolderSelect}
          />
        </aside>
        
        <main className="flex-1 overflow-hidden">
          <SegmentGrid
            folderId={selectedFolder}
            pageSize={1000}
          />
        </main>
        
        <aside className="w-96 border-l">
          <DetailPanel selection={selection} />
        </aside>
      </div>
      
      <StatusBar operations={operations} />
      <IdentityManager />
    </div>
  );
}
```

**Tasks:**
- [ ] Virtual scrolling implementation
- [ ] IndexedDB caching layer
- [ ] WebWorker for heavy operations
- [ ] Real-time progress tracking
- [ ] Memory management

### Phase 4: Advanced Features (Week 4)
```typescript
// src/hooks/useVirtualSegments.ts
import { useVirtualizer } from '@tanstack/react-virtual';
import { useInfiniteQuery } from '@tanstack/react-query';
import { invoke } from '@tauri-apps/api/tauri';

export function useVirtualSegments(folderId: string) {
  const {
    data,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
  } = useInfiniteQuery({
    queryKey: ['segments', folderId],
    queryFn: async ({ pageParam = 0 }) => {
      return invoke<SegmentPage>('get_segments', {
        folderId,
        offset: pageParam,
        limit: 1000,
      });
    },
    getNextPageParam: (lastPage) => lastPage.nextOffset,
  });
  
  const allSegments = data?.pages.flatMap(page => page.segments) ?? [];
  
  const virtualizer = useVirtualizer({
    count: hasNextPage ? allSegments.length + 1 : allSegments.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 150,
    overscan: 5,
  });
  
  // Load more when scrolling near the end
  useEffect(() => {
    const lastItem = virtualizer.getVirtualItems().at(-1);
    
    if (
      lastItem &&
      lastItem.index >= allSegments.length - 1 &&
      hasNextPage &&
      !isFetchingNextPage
    ) {
      fetchNextPage();
    }
  }, [virtualizer.getVirtualItems(), fetchNextPage, hasNextPage]);
  
  return {
    segments: allSegments,
    virtualizer,
    isLoading: isFetchingNextPage,
  };
}
```

**Tasks:**
- [ ] NNTP integration
- [ ] Upload/download queues
- [ ] Progress persistence
- [ ] Crash recovery
- [ ] Performance optimization

## Build & Distribution

### Development
```bash
# Install dependencies
npm install

# Run in development
npm run tauri dev

# Run tests
npm test
cargo test
```

### Production Build
```bash
# Build for current platform
npm run tauri build

# Build for all platforms (requires CI)
npm run tauri build -- --target all
```

### Code Signing
```toml
# tauri.conf.json
{
  "tauri": {
    "bundle": {
      "windows": {
        "certificateThumbprint": "YOUR_CERT_THUMBPRINT",
        "digestAlgorithm": "sha256",
        "timestampUrl": "http://timestamp.digicert.com"
      },
      "macOS": {
        "identity": "Developer ID Application: Your Name",
        "providerShortName": "YOURTEAMID"
      }
    }
  }
}
```

## Security Considerations

### 1. No Network Identity Verification
- All identity operations are local only
- No phone home or online verification
- License validation happens offline

### 2. Secure Storage
- Private keys never leave OS keychain
- Database encrypted with user-specific key
- No plain text storage of sensitive data

### 3. Anti-Tampering
```rust
// Verify binary integrity on startup
pub fn verify_integrity() -> Result<bool, String> {
    let exe_path = std::env::current_exe()?;
    let exe_bytes = std::fs::read(&exe_path)?;
    
    // Compare with embedded signature
    let signature = include_bytes!("../signature.sig");
    
    // Verify using embedded public key
    let public_key = include_bytes!("../public.key");
    
    verify_signature(&exe_bytes, signature, public_key)
}
```

### 4. Memory Protection
- Clear sensitive data from memory after use
- Use secure string types for passwords
- Implement memory locking for crypto operations

## Performance Optimizations

### 1. Lazy Loading Everything
```typescript
// Only load what's visible
const LazyComponent = lazy(() => 
  import('./HeavyComponent')
);

// Intersection Observer for infinite scroll
const observer = new IntersectionObserver(
  entries => {
    if (entries[0].isIntersecting) {
      loadMore();
    }
  },
  { threshold: 0.1 }
);
```

### 2. WebAssembly for Heavy Operations
```rust
// Compile to WASM for frontend use
#[wasm_bindgen]
pub fn search_segments(query: &str, data: &[u8]) -> Vec<u32> {
    // Fast searching in WASM
    let segments = deserialize_segments(data);
    segments.iter()
        .filter(|s| s.matches(query))
        .map(|s| s.id)
        .collect()
}
```

### 3. Streaming Everything
```rust
// Stream large results
#[tauri::command]
async fn stream_segments(
    folder_id: String,
    mut tx: mpsc::Sender<Segment>
) -> Result<(), String> {
    let mut stream = sqlx::query_as::<_, Segment>(
        "SELECT * FROM segments WHERE folder_id = $1"
    )
    .bind(&folder_id)
    .fetch(&pool);
    
    while let Some(segment) = stream.try_next().await? {
        tx.send(segment).await?;
    }
    
    Ok(())
}
```

## Testing Strategy

### 1. Unit Tests
```rust
#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_identity_generation() {
        let manager = IdentityManager::new();
        let identity = manager.generate_test_identity().unwrap();
        
        assert!(identity.user_id.starts_with("USN-"));
        assert_eq!(identity.public_key.len(), 32);
    }
}
```

### 2. Integration Tests
```typescript
describe('Identity Management', () => {
  it('should prevent identity recovery', async () => {
    const identity = await createIdentity();
    
    // Delete from keychain
    await deleteIdentity();
    
    // Attempt recovery should fail
    await expect(recoverIdentity()).rejects.toThrow(
      'Identity cannot be recovered'
    );
  });
});
```

### 3. E2E Tests
```typescript
test('Complete user flow', async () => {
  // Launch app
  const app = await launch();
  
  // First run - create identity
  await app.firstRun.complete();
  
  // Activate trial
  await app.license.activateTrial();
  
  // Upload file
  await app.upload.addFile('/test/file.zip');
  
  // Verify segments created
  const segments = await app.segments.getAll();
  expect(segments.length).toBeGreaterThan(0);
});
```

This implementation provides a secure, performant desktop application that maintains your zero-knowledge, immutable identity requirements while handling massive datasets efficiently.