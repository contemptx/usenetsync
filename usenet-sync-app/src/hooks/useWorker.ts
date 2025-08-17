import { useRef, useCallback, useEffect } from 'react';

interface WorkerMessage {
  id: string;
  type: string;
  data: any;
  options?: any;
}

interface WorkerResponse {
  id: string;
  result?: any;
  error?: string;
  progress?: number;
}

type WorkerCallback = (response: WorkerResponse) => void;

/**
 * Hook for using Web Workers with async/await support
 */
export function useWorker(workerPath: string) {
  const workerRef = useRef<Worker | null>(null);
  const callbacksRef = useRef<Map<string, WorkerCallback>>(new Map());
  
  // Initialize worker
  useEffect(() => {
    // Create worker
    const worker = new Worker(
      new URL(workerPath, import.meta.url),
      { type: 'module' }
    );
    
    // Handle messages from worker
    worker.addEventListener('message', (event: MessageEvent<WorkerResponse>) => {
      const { id, result, error, progress } = event.data;
      
      const callback = callbacksRef.current.get(id);
      if (callback) {
        callback({ id, result, error, progress });
        
        // Remove callback if not a progress update
        if (progress === undefined) {
          callbacksRef.current.delete(id);
        }
      }
    });
    
    // Handle errors
    worker.addEventListener('error', (error) => {
      console.error('Worker error:', error);
    });
    
    workerRef.current = worker;
    
    // Cleanup
    return () => {
      worker.terminate();
      workerRef.current = null;
      callbacksRef.current.clear();
    };
  }, [workerPath]);
  
  /**
   * Send message to worker and get response
   */
  const sendMessage = useCallback(
    <T = any>(
      type: string,
      data: any,
      options?: any,
      onProgress?: (progress: number) => void
    ): Promise<T> => {
      return new Promise((resolve, reject) => {
        if (!workerRef.current) {
          reject(new Error('Worker not initialized'));
          return;
        }
        
        const id = `${Date.now()}-${Math.random()}`;
        
        // Set up callback
        callbacksRef.current.set(id, (response) => {
          if (response.error) {
            reject(new Error(response.error));
          } else if (response.progress !== undefined) {
            onProgress?.(response.progress);
          } else {
            resolve(response.result);
          }
        });
        
        // Send message to worker
        const message: WorkerMessage = { id, type, data, options };
        workerRef.current.postMessage(message);
      });
    },
    []
  );
  
  /**
   * Terminate worker
   */
  const terminate = useCallback(() => {
    if (workerRef.current) {
      workerRef.current.terminate();
      workerRef.current = null;
      callbacksRef.current.clear();
    }
  }, []);
  
  return {
    sendMessage,
    terminate,
    isReady: !!workerRef.current
  };
}

/**
 * Hook for crypto operations using Web Worker
 */
export function useCryptoWorker() {
  const worker = useWorker('../workers/crypto.worker.ts');
  
  const encrypt = useCallback(
    async (plaintext: string, password: string) => {
      return worker.sendMessage<{ encrypted: number[]; salt: number[] }>(
        'encrypt',
        { plaintext, password }
      );
    },
    [worker]
  );
  
  const decrypt = useCallback(
    async (ciphertext: number[], password: string) => {
      return worker.sendMessage<string>(
        'decrypt',
        { ciphertext, password }
      );
    },
    [worker]
  );
  
  const hash = useCallback(
    async (data: string) => {
      return worker.sendMessage<string>(
        'hash',
        { data }
      );
    },
    [worker]
  );
  
  const deriveKey = useCallback(
    async (password: string, salt: number[]) => {
      return worker.sendMessage<number[]>(
        'derive-key',
        { password, salt }
      );
    },
    [worker]
  );
  
  return {
    encrypt,
    decrypt,
    hash,
    deriveKey,
    isReady: worker.isReady
  };
}

/**
 * Hook for compression operations using Web Worker
 */
export function useCompressionWorker() {
  const worker = useWorker('../workers/compression.worker.ts');
  
  const compress = useCallback(
    async (data: number[], level?: number) => {
      return worker.sendMessage<{
        compressed: number[];
        originalSize: number;
        compressedSize: number;
        ratio: number;
      }>('compress', data, { level });
    },
    [worker]
  );
  
  const decompress = useCallback(
    async (data: number[]) => {
      return worker.sendMessage<{
        decompressed: number[];
        compressedSize: number;
        decompressedSize: number;
      }>('decompress', data);
    },
    [worker]
  );
  
  const compressStream = useCallback(
    async (
      data: number[],
      onProgress?: (progress: number) => void,
      chunkSize?: number
    ) => {
      return worker.sendMessage<{
        compressed: number[];
        originalSize: number;
        compressedSize: number;
        ratio: number;
      }>('compress-stream', data, { chunkSize }, onProgress);
    },
    [worker]
  );
  
  const decompressStream = useCallback(
    async (
      data: number[],
      onProgress?: (progress: number) => void,
      chunkSize?: number
    ) => {
      return worker.sendMessage<{
        decompressed: number[];
        compressedSize: number;
        decompressedSize: number;
      }>('decompress-stream', data, { chunkSize }, onProgress);
    },
    [worker]
  );
  
  return {
    compress,
    decompress,
    compressStream,
    decompressStream,
    isReady: worker.isReady
  };
}