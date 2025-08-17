/**
 * Web Worker for heavy cryptographic operations
 * Offloads encryption/decryption from main thread
 */

// Import WebAssembly crypto module (would be compiled from Rust)
// For now, we'll use SubtleCrypto API as fallback

interface WorkerMessage {
  id: string;
  type: 'encrypt' | 'decrypt' | 'hash' | 'derive-key';
  data: any;
}

interface WorkerResponse {
  id: string;
  result?: any;
  error?: string;
}

// Initialize crypto
const crypto = self.crypto;

/**
 * Encrypt data using AES-GCM
 */
async function encryptData(data: ArrayBuffer, key: CryptoKey): Promise<ArrayBuffer> {
  const iv = crypto.getRandomValues(new Uint8Array(12));
  
  const encrypted = await crypto.subtle.encrypt(
    {
      name: 'AES-GCM',
      iv: iv
    },
    key,
    data
  );
  
  // Combine IV and encrypted data
  const combined = new Uint8Array(iv.length + encrypted.byteLength);
  combined.set(iv);
  combined.set(new Uint8Array(encrypted), iv.length);
  
  return combined.buffer;
}

/**
 * Decrypt data using AES-GCM
 */
async function decryptData(data: ArrayBuffer, key: CryptoKey): Promise<ArrayBuffer> {
  const dataArray = new Uint8Array(data);
  const iv = dataArray.slice(0, 12);
  const encrypted = dataArray.slice(12);
  
  const decrypted = await crypto.subtle.decrypt(
    {
      name: 'AES-GCM',
      iv: iv
    },
    key,
    encrypted
  );
  
  return decrypted;
}

/**
 * Calculate SHA-256 hash
 */
async function hashData(data: ArrayBuffer): Promise<string> {
  const hashBuffer = await crypto.subtle.digest('SHA-256', data);
  const hashArray = Array.from(new Uint8Array(hashBuffer));
  return hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
}

/**
 * Derive key from password using PBKDF2
 */
async function deriveKey(password: string, salt: ArrayBuffer): Promise<CryptoKey> {
  const encoder = new TextEncoder();
  const passwordKey = await crypto.subtle.importKey(
    'raw',
    encoder.encode(password),
    'PBKDF2',
    false,
    ['deriveBits', 'deriveKey']
  );
  
  const key = await crypto.subtle.deriveKey(
    {
      name: 'PBKDF2',
      salt: salt,
      iterations: 100000,
      hash: 'SHA-256'
    },
    passwordKey,
    { name: 'AES-GCM', length: 256 },
    true,
    ['encrypt', 'decrypt']
  );
  
  return key;
}

// Cache for derived keys
const keyCache = new Map<string, CryptoKey>();

// Handle messages from main thread
self.addEventListener('message', async (event: MessageEvent<WorkerMessage>) => {
  const { id, type, data } = event.data;
  
  try {
    let result: any;
    
    switch (type) {
      case 'encrypt': {
        const { plaintext, password } = data;
        const salt = crypto.getRandomValues(new Uint8Array(16));
        
        // Get or derive key
        const cacheKey = `${password}-${Array.from(salt).join(',')}`;
        let key = keyCache.get(cacheKey);
        if (!key) {
          key = await deriveKey(password, salt);
          keyCache.set(cacheKey, key);
        }
        
        // Convert string to ArrayBuffer
        const encoder = new TextEncoder();
        const dataBuffer = encoder.encode(plaintext);
        
        // Encrypt
        const encrypted = await encryptData(dataBuffer, key);
        
        // Combine salt and encrypted data
        const combined = new Uint8Array(salt.length + encrypted.byteLength);
        combined.set(salt);
        combined.set(new Uint8Array(encrypted), salt.length);
        
        result = {
          encrypted: Array.from(combined),
          salt: Array.from(salt)
        };
        break;
      }
      
      case 'decrypt': {
        const { ciphertext, password } = data;
        const dataArray = new Uint8Array(ciphertext);
        
        // Extract salt
        const salt = dataArray.slice(0, 16);
        const encrypted = dataArray.slice(16);
        
        // Get or derive key
        const cacheKey = `${password}-${Array.from(salt).join(',')}`;
        let key = keyCache.get(cacheKey);
        if (!key) {
          key = await deriveKey(password, salt);
          keyCache.set(cacheKey, key);
        }
        
        // Decrypt
        const decrypted = await decryptData(encrypted.buffer, key);
        
        // Convert ArrayBuffer to string
        const decoder = new TextDecoder();
        result = decoder.decode(decrypted);
        break;
      }
      
      case 'hash': {
        const { data: inputData } = data;
        const encoder = new TextEncoder();
        const dataBuffer = encoder.encode(inputData);
        result = await hashData(dataBuffer);
        break;
      }
      
      case 'derive-key': {
        const { password, salt } = data;
        const saltBuffer = new Uint8Array(salt);
        const key = await deriveKey(password, saltBuffer);
        
        // Export key for storage
        const exported = await crypto.subtle.exportKey('raw', key);
        result = Array.from(new Uint8Array(exported));
        break;
      }
      
      default:
        throw new Error(`Unknown operation: ${type}`);
    }
    
    const response: WorkerResponse = { id, result };
    self.postMessage(response);
    
  } catch (error: any) {
    const response: WorkerResponse = { 
      id, 
      error: error.message || 'Unknown error' 
    };
    self.postMessage(response);
  }
});

// Export for TypeScript
export {};