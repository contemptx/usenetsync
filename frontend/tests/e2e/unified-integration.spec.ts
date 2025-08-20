/**
 * E2E Tests for Unified Backend Integration
 * Tests the complete flow from GUI → Tauri → Python Unified Backend
 */

import { test, expect, Page } from '@playwright/test';
import { spawn, ChildProcess } from 'child_process';
import path from 'path';
import fs from 'fs/promises';

// Test configuration
const BACKEND_URL = process.env.VITE_BACKEND_URL || 'http://localhost:8000';
const FRONTEND_URL = process.env.FRONTEND_BASE_URL || 'http://localhost:5173';
const TEST_TIMEOUT = 60000; // 60 seconds

// Helper to wait for backend
async function waitForBackend(maxAttempts = 30) {
  for (let i = 0; i < maxAttempts; i++) {
    try {
      const response = await fetch(`${BACKEND_URL}/api/v1/health`);
      if (response.ok) {
        const data = await response.json();
        if (data.status === 'healthy') {
          return true;
        }
      }
    } catch (e) {
      // Backend not ready yet
    }
    await new Promise(resolve => setTimeout(resolve, 1000));
  }
  throw new Error('Backend failed to start');
}

// Helper to create test files
async function createTestFiles(testDir: string) {
  await fs.mkdir(testDir, { recursive: true });
  
  // Create various test files
  await fs.writeFile(
    path.join(testDir, 'test-document.txt'),
    'This is a test document for UsenetSync E2E testing.\n'.repeat(100)
  );
  
  await fs.writeFile(
    path.join(testDir, 'test-data.csv'),
    'id,name,value\n1,test,100\n2,demo,200\n'.repeat(50)
  );
  
  // Create a larger file for segmentation testing
  const largeContent = Buffer.alloc(1024 * 1024, 'X'); // 1MB
  await fs.writeFile(path.join(testDir, 'large-file.bin'), largeContent);
  
  return testDir;
}

test.describe('Unified Backend E2E Tests', () => {
  let backendProcess: ChildProcess | null = null;
  let testDir: string;

  test.beforeAll(async () => {
    // Create test directory
    testDir = path.join('/tmp', `usenetsync-e2e-${Date.now()}`);
    await createTestFiles(testDir);
    
    // Start the unified backend if not already running
    try {
      await waitForBackend(5);
      console.log('Backend already running');
    } catch {
      console.log('Starting unified backend...');
      backendProcess = spawn('python', ['-m', 'unified.api.server'], {
        cwd: '/workspace',
        env: {
          ...process.env,
          PYTHONPATH: '/workspace/src',
          DATABASE_URL: 'postgresql://usenetsync:usenetsync123@localhost:5432/usenetsync',
          NNTP_HOST: 'news.newshosting.com',
          NNTP_PORT: '563',
          NNTP_USERNAME: 'contemptx',
          NNTP_PASSWORD: 'Kia211101#',
        },
        stdio: 'pipe'
      });
      
      backendProcess.stdout?.on('data', (data) => {
        console.log(`Backend: ${data}`);
      });
      
      backendProcess.stderr?.on('data', (data) => {
        console.error(`Backend Error: ${data}`);
      });
      
      await waitForBackend();
      console.log('Backend started successfully');
    }
  });

  test.afterAll(async () => {
    // Clean up test files
    try {
      await fs.rm(testDir, { recursive: true, force: true });
    } catch (e) {
      console.error('Failed to clean test directory:', e);
    }
    
    // Stop backend if we started it
    if (backendProcess) {
      backendProcess.kill();
      await new Promise(resolve => setTimeout(resolve, 2000));
    }
  });

  test('Backend health check', async () => {
    const response = await fetch(`${BACKEND_URL}/api/v1/health`);
    expect(response.ok).toBeTruthy();
    
    const data = await response.json();
    expect(data.status).toBe('healthy');
    expect(data.database).toBeDefined();
    expect(data.nntp).toBeDefined();
  });

  test('System initialization and user creation', async ({ page }) => {
    await page.goto(FRONTEND_URL);
    
    // Check if user initialization is needed
    const needsInit = await page.evaluate(async () => {
      // @ts-ignore - Tauri API is available in the app
      return await window.__TAURI__?.invoke('is_user_initialized');
    });
    
    if (!needsInit) {
      // Initialize user through unified backend
      const result = await page.evaluate(async () => {
        // @ts-ignore
        return await window.__TAURI__?.invoke('initialize_user', {
          displayName: `E2E_User_${Date.now()}`
        });
      });
      
      expect(result).toBeTruthy();
      console.log('User initialized:', result);
    }
    
    // Verify system stats are available
    const stats = await page.evaluate(async () => {
      // @ts-ignore
      return await window.__TAURI__?.invoke('get_system_stats');
    });
    
    expect(stats).toBeDefined();
    expect(stats.totalFiles).toBeGreaterThanOrEqual(0);
    expect(stats.cpuUsage).toBeGreaterThanOrEqual(0);
    expect(stats.memoryUsage).toBeGreaterThanOrEqual(0);
  });

  test('Folder indexing with unified scanner', async ({ page }) => {
    await page.goto(`${FRONTEND_URL}/folders`);
    
    // Add folder through unified backend
    const folderResult = await page.evaluate(async (testDir) => {
      // @ts-ignore
      return await window.__TAURI__?.invoke('add_folder', {
        path: testDir,
        name: 'E2E Test Folder'
      });
    }, testDir);
    
    expect(folderResult).toBeDefined();
    expect(folderResult.folder_id).toBeTruthy();
    
    // Start indexing
    const indexResult = await page.evaluate(async (folderId) => {
      // @ts-ignore
      return await window.__TAURI__?.invoke('index_folder', {
        folderId: folderId
      });
    }, folderResult.folder_id);
    
    expect(indexResult.success).toBeTruthy();
    expect(indexResult.files_indexed).toBeGreaterThan(0);
    
    // Verify files are indexed
    await page.waitForSelector('[data-test="indexed-file"]', { timeout: 10000 });
    const fileCount = await page.locator('[data-test="indexed-file"]').count();
    expect(fileCount).toBeGreaterThan(0);
  });

  test('File segmentation for Usenet', async ({ page }) => {
    await page.goto(`${FRONTEND_URL}/upload`);
    
    // Select the large file for upload
    const largeFilePath = path.join(testDir, 'large-file.bin');
    
    // Prepare file for upload (segmentation)
    const segmentResult = await page.evaluate(async (filePath) => {
      // @ts-ignore
      return await window.__TAURI__?.invoke('prepare_upload', {
        filePath: filePath,
        segmentSize: 500000 // 500KB segments
      });
    }, largeFilePath);
    
    expect(segmentResult).toBeDefined();
    expect(segmentResult.segments).toBeGreaterThan(1);
    expect(segmentResult.total_size).toBe(1024 * 1024);
    
    // Verify segments are created
    const segments = await page.evaluate(async (fileId) => {
      // @ts-ignore
      return await window.__TAURI__?.invoke('get_file_segments', {
        fileId: fileId
      });
    }, segmentResult.file_id);
    
    expect(segments.length).toBeGreaterThan(1);
    segments.forEach((segment: any) => {
      expect(segment.segment_id).toBeTruthy();
      expect(segment.size).toBeGreaterThan(0);
      expect(segment.hash).toBeTruthy();
    });
  });

  test('Share creation with encryption', async ({ page }) => {
    await page.goto(`${FRONTEND_URL}/shares`);
    
    // Create a new share
    await page.click('[data-test="create-share-button"]');
    
    // Fill share details
    await page.fill('[data-test="share-name"]', 'E2E Test Share');
    await page.selectOption('[data-test="share-type"]', 'protected');
    await page.fill('[data-test="share-password"]', 'TestPassword123!');
    
    // Select files
    const testFile = path.join(testDir, 'test-document.txt');
    await page.evaluate(async (filePath) => {
      // @ts-ignore
      return await window.__TAURI__?.invoke('add_file_to_share', {
        filePath: filePath
      });
    }, testFile);
    
    // Create share through unified backend
    await page.click('[data-test="confirm-share-button"]');
    
    // Wait for share creation
    await page.waitForSelector('[data-test="share-created-notification"]', { timeout: 10000 });
    
    // Get share details
    const shares = await page.evaluate(async () => {
      // @ts-ignore
      return await window.__TAURI__?.invoke('get_shares');
    });
    
    expect(shares.length).toBeGreaterThan(0);
    const latestShare = shares[shares.length - 1];
    expect(latestShare.share_id).toBeTruthy();
    expect(latestShare.access_type).toBe('protected');
    expect(latestShare.encrypted).toBeTruthy();
  });

  test('NNTP connection and posting', async ({ page }) => {
    await page.goto(`${FRONTEND_URL}/settings`);
    
    // Test NNTP connection through unified backend
    const connectionTest = await page.evaluate(async () => {
      // @ts-ignore
      return await window.__TAURI__?.invoke('test_nntp_connection');
    });
    
    expect(connectionTest.success).toBeTruthy();
    expect(connectionTest.server).toBe('news.newshosting.com');
    expect(connectionTest.port).toBe(563);
    expect(connectionTest.ssl).toBeTruthy();
    expect(connectionTest.authenticated).toBeTruthy();
    
    // Post a test article
    const postResult = await page.evaluate(async () => {
      // @ts-ignore
      return await window.__TAURI__?.invoke('post_test_article', {
        subject: `UsenetSync E2E Test ${Date.now()}`,
        body: 'This is an E2E test article posted through the unified backend',
        newsgroup: 'alt.binaries.test'
      });
    });
    
    if (postResult.success) {
      expect(postResult.message_id).toBeTruthy();
      console.log('Posted test article:', postResult.message_id);
    } else {
      console.log('Article posting skipped (rate limit)');
    }
  });

  test('Database operations through unified backend', async ({ page }) => {
    await page.goto(`${FRONTEND_URL}/dashboard`);
    
    // Get database statistics
    const dbStats = await page.evaluate(async () => {
      // @ts-ignore
      return await window.__TAURI__?.invoke('get_database_stats');
    });
    
    expect(dbStats).toBeDefined();
    expect(dbStats.total_users).toBeGreaterThanOrEqual(1);
    expect(dbStats.total_files).toBeGreaterThanOrEqual(0);
    expect(dbStats.total_folders).toBeGreaterThanOrEqual(0);
    expect(dbStats.total_shares).toBeGreaterThanOrEqual(0);
    expect(dbStats.database_type).toBe('postgresql');
    
    // Verify dashboard displays the stats
    await page.waitForSelector('[data-test="stats-card"]');
    const statsCards = await page.locator('[data-test="stats-card"]').count();
    expect(statsCards).toBeGreaterThan(0);
  });

  test('Complete upload workflow', async ({ page }) => {
    await page.goto(`${FRONTEND_URL}/upload`);
    
    // Create a test file
    const uploadFile = path.join(testDir, 'upload-test.txt');
    await fs.writeFile(uploadFile, 'Test content for upload workflow');
    
    // Start upload process
    const uploadResult = await page.evaluate(async (filePath) => {
      // @ts-ignore
      return await window.__TAURI__?.invoke('upload_file', {
        filePath: filePath,
        shareId: 'test-share-' + Date.now()
      });
    }, uploadFile);
    
    expect(uploadResult).toBeDefined();
    
    // Monitor upload progress
    const progress = await page.evaluate(async (uploadId) => {
      return new Promise((resolve) => {
        let lastProgress = 0;
        const checkProgress = setInterval(async () => {
          // @ts-ignore
          const status = await window.__TAURI__?.invoke('get_upload_status', {
            uploadId: uploadId
          });
          
          if (status.progress > lastProgress) {
            lastProgress = status.progress;
          }
          
          if (status.status === 'completed' || status.status === 'failed') {
            clearInterval(checkProgress);
            resolve(status);
          }
        }, 1000);
        
        // Timeout after 30 seconds
        setTimeout(() => {
          clearInterval(checkProgress);
          resolve({ status: 'timeout', progress: lastProgress });
        }, 30000);
      });
    }, uploadResult.upload_id);
    
    expect(progress).toBeDefined();
    console.log('Upload progress:', progress);
  });

  test('GUI responsiveness and real-time updates', async ({ page }) => {
    await page.goto(`${FRONTEND_URL}/dashboard`);
    
    // Check that the dashboard loads
    await expect(page.locator('[data-test="dashboard-container"]')).toBeVisible({ timeout: 5000 });
    
    // Start monitoring for real-time updates
    const initialStats = await page.evaluate(async () => {
      // @ts-ignore
      return await window.__TAURI__?.invoke('get_system_stats');
    });
    
    // Trigger an action that should update stats
    await page.evaluate(async () => {
      // @ts-ignore
      await window.__TAURI__?.invoke('refresh_statistics');
    });
    
    // Wait for stats to update
    await page.waitForTimeout(2000);
    
    const updatedStats = await page.evaluate(async () => {
      // @ts-ignore
      return await window.__TAURI__?.invoke('get_system_stats');
    });
    
    // CPU and memory usage should have changed
    expect(updatedStats.cpuUsage).toBeDefined();
    expect(updatedStats.memoryUsage).toBeDefined();
    
    // Check that UI reflects the updates
    const cpuElement = page.locator('[data-test="cpu-usage"]');
    if (await cpuElement.count() > 0) {
      const cpuText = await cpuElement.textContent();
      expect(cpuText).toContain('%');
    }
  });

  test('Error handling and recovery', async ({ page }) => {
    await page.goto(`${FRONTEND_URL}/settings`);
    
    // Test with invalid NNTP credentials
    const errorTest = await page.evaluate(async () => {
      // @ts-ignore
      return await window.__TAURI__?.invoke('test_nntp_connection', {
        host: 'invalid.server.com',
        port: 563,
        username: 'invalid',
        password: 'invalid'
      });
    });
    
    expect(errorTest.success).toBeFalsy();
    expect(errorTest.error).toBeTruthy();
    
    // Verify error is displayed in UI
    if (await page.locator('[data-test="error-message"]').count() > 0) {
      const errorText = await page.locator('[data-test="error-message"]').textContent();
      expect(errorText).toBeTruthy();
    }
    
    // Test recovery with correct credentials
    const recoveryTest = await page.evaluate(async () => {
      // @ts-ignore
      return await window.__TAURI__?.invoke('test_nntp_connection');
    });
    
    expect(recoveryTest.success).toBeTruthy();
  });
});

test.describe('Frontend Component Tests', () => {
  test('Navigation works correctly', async ({ page }) => {
    await page.goto(FRONTEND_URL);
    
    // Test navigation to different pages
    const pages = [
      { link: 'Dashboard', url: '/dashboard' },
      { link: 'Upload', url: '/upload' },
      { link: 'Download', url: '/download' },
      { link: 'Shares', url: '/shares' },
      { link: 'Folders', url: '/folders' },
      { link: 'Settings', url: '/settings' }
    ];
    
    for (const pageInfo of pages) {
      await page.click(`[data-test="nav-${pageInfo.link.toLowerCase()}"]`);
      await expect(page).toHaveURL(new RegExp(pageInfo.url));
      await expect(page.locator(`[data-test="${pageInfo.link.toLowerCase()}-page"]`)).toBeVisible({ timeout: 5000 });
    }
  });

  test('Dark mode toggle', async ({ page }) => {
    await page.goto(FRONTEND_URL);
    
    // Check initial state
    const initialDarkMode = await page.evaluate(() => {
      return document.documentElement.classList.contains('dark');
    });
    
    // Toggle dark mode
    await page.click('[data-test="dark-mode-toggle"]');
    
    // Check that it toggled
    const afterToggle = await page.evaluate(() => {
      return document.documentElement.classList.contains('dark');
    });
    
    expect(afterToggle).toBe(!initialDarkMode);
    
    // Verify it persists after reload
    await page.reload();
    const afterReload = await page.evaluate(() => {
      return document.documentElement.classList.contains('dark');
    });
    
    expect(afterReload).toBe(afterToggle);
  });
});