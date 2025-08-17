/**
 * Web Worker for compression/decompression operations
 * Offloads heavy compression tasks from main thread
 */

import pako from 'pako';

interface WorkerMessage {
  id: string;
  type: 'compress' | 'decompress' | 'compress-stream' | 'decompress-stream';
  data: any;
  options?: any;
}

interface WorkerResponse {
  id: string;
  result?: any;
  error?: string;
  progress?: number;
}

/**
 * Compress data using DEFLATE algorithm
 */
function compressData(data: Uint8Array, level: number = 6): Uint8Array {
  return pako.deflate(data, { level });
}

/**
 * Decompress DEFLATE compressed data
 */
function decompressData(data: Uint8Array): Uint8Array {
  return pako.inflate(data);
}

/**
 * Compress data in chunks for large files
 */
async function compressStream(
  data: Uint8Array, 
  chunkSize: number = 1024 * 1024,
  onProgress?: (progress: number) => void
): Promise<Uint8Array> {
  const deflator = new pako.Deflate({ level: 6 });
  const totalChunks = Math.ceil(data.length / chunkSize);
  
  for (let i = 0; i < totalChunks; i++) {
    const start = i * chunkSize;
    const end = Math.min(start + chunkSize, data.length);
    const chunk = data.slice(start, end);
    const isLast = i === totalChunks - 1;
    
    deflator.push(chunk, isLast);
    
    if (onProgress) {
      const progress = ((i + 1) / totalChunks) * 100;
      onProgress(progress);
    }
    
    // Yield to prevent blocking
    await new Promise(resolve => setTimeout(resolve, 0));
  }
  
  if (deflator.err) {
    throw new Error(deflator.msg || 'Compression failed');
  }
  
  return deflator.result as Uint8Array;
}

/**
 * Decompress data in chunks for large files
 */
async function decompressStream(
  data: Uint8Array,
  chunkSize: number = 1024 * 1024,
  onProgress?: (progress: number) => void
): Promise<Uint8Array> {
  const inflator = new pako.Inflate();
  const totalChunks = Math.ceil(data.length / chunkSize);
  
  for (let i = 0; i < totalChunks; i++) {
    const start = i * chunkSize;
    const end = Math.min(start + chunkSize, data.length);
    const chunk = data.slice(start, end);
    const isLast = i === totalChunks - 1;
    
    inflator.push(chunk, isLast);
    
    if (onProgress) {
      const progress = ((i + 1) / totalChunks) * 100;
      onProgress(progress);
    }
    
    // Yield to prevent blocking
    await new Promise(resolve => setTimeout(resolve, 0));
  }
  
  if (inflator.err) {
    throw new Error(inflator.msg || 'Decompression failed');
  }
  
  return inflator.result as Uint8Array;
}

/**
 * Calculate compression ratio
 */
function calculateCompressionRatio(original: number, compressed: number): number {
  if (original === 0) return 0;
  return ((original - compressed) / original) * 100;
}

// Handle messages from main thread
self.addEventListener('message', async (event: MessageEvent<WorkerMessage>) => {
  const { id, type, data, options = {} } = event.data;
  
  try {
    let result: any;
    
    switch (type) {
      case 'compress': {
        const input = new Uint8Array(data);
        const level = options.level || 6;
        const compressed = compressData(input, level);
        
        result = {
          compressed: Array.from(compressed),
          originalSize: input.length,
          compressedSize: compressed.length,
          ratio: calculateCompressionRatio(input.length, compressed.length)
        };
        break;
      }
      
      case 'decompress': {
        const input = new Uint8Array(data);
        const decompressed = decompressData(input);
        
        result = {
          decompressed: Array.from(decompressed),
          compressedSize: input.length,
          decompressedSize: decompressed.length
        };
        break;
      }
      
      case 'compress-stream': {
        const input = new Uint8Array(data);
        const chunkSize = options.chunkSize || 1024 * 1024;
        
        const compressed = await compressStream(
          input,
          chunkSize,
          (progress) => {
            const response: WorkerResponse = { id, progress };
            self.postMessage(response);
          }
        );
        
        result = {
          compressed: Array.from(compressed),
          originalSize: input.length,
          compressedSize: compressed.length,
          ratio: calculateCompressionRatio(input.length, compressed.length)
        };
        break;
      }
      
      case 'decompress-stream': {
        const input = new Uint8Array(data);
        const chunkSize = options.chunkSize || 1024 * 1024;
        
        const decompressed = await decompressStream(
          input,
          chunkSize,
          (progress) => {
            const response: WorkerResponse = { id, progress };
            self.postMessage(response);
          }
        );
        
        result = {
          decompressed: Array.from(decompressed),
          compressedSize: input.length,
          decompressedSize: decompressed.length
        };
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