import { vi } from 'vitest';

// Mock event listener
export const listen = vi.fn((event: string, callback: (payload: any) => void) => {
  console.log(`Mock Tauri listen: ${event}`);
  
  // Simulate some events for testing
  if (event === 'transfer-progress') {
    setTimeout(() => {
      callback({
        payload: {
          id: 'transfer-1',
          progress: 0.5,
          speed: 1024000,
          eta: 300
        }
      });
    }, 100);
  }
  
  // Return unsubscribe function
  return Promise.resolve(() => {
    console.log(`Unsubscribed from ${event}`);
  });
});

// Mock event emitter
export const emit = vi.fn((event: string, payload?: any) => {
  console.log(`Mock Tauri emit: ${event}`, payload);
  return Promise.resolve();
});

// Mock once listener
export const once = vi.fn((event: string, callback: (payload: any) => void) => {
  console.log(`Mock Tauri once: ${event}`);
  
  // Return unsubscribe function
  return Promise.resolve(() => {
    console.log(`Unsubscribed from ${event}`);
  });
});