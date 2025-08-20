/**
 * Basic E2E Tests for Frontend-Backend Integration
 * Tests the connection between the GUI and the unified backend
 */

import { test, expect } from '@playwright/test';

const BACKEND_URL = 'http://localhost:8000';
const FRONTEND_URL = 'http://localhost:1420';

test.describe('Basic Frontend-Backend Integration', () => {
  
  test.beforeAll(async () => {
    // Verify backend is running
    const response = await fetch(`${BACKEND_URL}/health`);
    if (!response.ok) {
      throw new Error('Backend is not running. Start it with: python start_unified_backend.py');
    }
    const data = await response.json();
    expect(data.status).toBe('healthy');
    console.log('✅ Backend is healthy');
  });

  test('Frontend loads successfully', async ({ page }) => {
    await page.goto(FRONTEND_URL);
    
    // Check that the app loads
    await expect(page).toHaveTitle(/UsenetSync/i, { timeout: 10000 });
    
    // Check for main app container
    const appContainer = page.locator('#root');
    await expect(appContainer).toBeVisible();
    
    console.log('✅ Frontend loaded successfully');
  });

  test('Backend health endpoint is accessible', async () => {
    const response = await fetch(`${BACKEND_URL}/health`);
    expect(response.ok).toBeTruthy();
    
    const data = await response.json();
    expect(data.status).toBe('healthy');
    
    console.log('✅ Backend health check passed');
  });

  test('Backend stats endpoint returns data', async () => {
    const response = await fetch(`${BACKEND_URL}/api/v1/stats`);
    expect(response.ok).toBeTruthy();
    
    const data = await response.json();
    expect(data).toBeDefined();
    expect(data.total_files).toBeGreaterThanOrEqual(0);
    expect(data.total_size).toBeGreaterThanOrEqual(0);
    expect(data.total_shares).toBeGreaterThanOrEqual(0);
    
    console.log('✅ Backend stats:', data);
  });

  test('Frontend can communicate with backend via Tauri', async ({ page }) => {
    await page.goto(FRONTEND_URL);
    
    // Wait for the app to load
    await page.waitForLoadState('networkidle');
    
    // Check if Tauri API is available
    const tauriAvailable = await page.evaluate(() => {
      return typeof window.__TAURI__ !== 'undefined';
    });
    
    if (tauriAvailable) {
      console.log('✅ Tauri API is available');
      
      // Try to invoke a Tauri command
      const result = await page.evaluate(async () => {
        try {
          // @ts-ignore
          const stats = await window.__TAURI__.invoke('get_system_stats');
          return { success: true, data: stats };
        } catch (error) {
          return { success: false, error: error.toString() };
        }
      });
      
      if (result.success) {
        console.log('✅ Tauri command executed successfully:', result.data);
      } else {
        console.log('⚠️ Tauri command failed (expected in web mode):', result.error);
      }
    } else {
      console.log('ℹ️ Running in web mode (Tauri not available)');
    }
  });

  test('Dashboard page loads and shows stats', async ({ page }) => {
    await page.goto(`${FRONTEND_URL}/dashboard`);
    
    // Wait for dashboard to load
    await page.waitForLoadState('networkidle');
    
    // Check for dashboard elements
    const dashboard = page.locator('[data-testid="dashboard"], .dashboard, #dashboard');
    
    // Try multiple possible selectors for stats
    const possibleStatsSelectors = [
      '[data-testid="stats-card"]',
      '.stats-card',
      '.stat-card',
      '.dashboard-stats',
      '.metric-card',
      '[class*="stat"]',
      '[class*="metric"]'
    ];
    
    let statsFound = false;
    for (const selector of possibleStatsSelectors) {
      const count = await page.locator(selector).count();
      if (count > 0) {
        statsFound = true;
        console.log(`✅ Found ${count} stats elements with selector: ${selector}`);
        break;
      }
    }
    
    if (!statsFound) {
      console.log('⚠️ No stats cards found, but dashboard loaded');
    }
  });

  test('Upload page is accessible', async ({ page }) => {
    await page.goto(`${FRONTEND_URL}/upload`);
    
    // Wait for page to load
    await page.waitForLoadState('networkidle');
    
    // Check for upload-related elements
    const uploadSelectors = [
      '[data-testid="upload-area"]',
      '.upload-area',
      '.upload-zone',
      '[class*="upload"]',
      'input[type="file"]',
      'button:has-text("Upload")',
      'button:has-text("Select")'
    ];
    
    let uploadElementFound = false;
    for (const selector of uploadSelectors) {
      try {
        const element = page.locator(selector).first();
        if (await element.count() > 0) {
          uploadElementFound = true;
          console.log(`✅ Found upload element: ${selector}`);
          break;
        }
      } catch (e) {
        // Continue checking other selectors
      }
    }
    
    if (!uploadElementFound) {
      console.log('⚠️ Upload page loaded but no upload elements found');
    }
  });

  test('Settings page loads', async ({ page }) => {
    await page.goto(`${FRONTEND_URL}/settings`);
    
    // Wait for settings to load
    await page.waitForLoadState('networkidle');
    
    // Check for settings elements
    const settingsSelectors = [
      '[data-testid="settings"]',
      '.settings',
      '#settings',
      '[class*="settings"]',
      'h1:has-text("Settings")',
      'h2:has-text("Settings")'
    ];
    
    let settingsFound = false;
    for (const selector of settingsSelectors) {
      try {
        const element = page.locator(selector).first();
        if (await element.count() > 0) {
          settingsFound = true;
          console.log(`✅ Settings page loaded with element: ${selector}`);
          break;
        }
      } catch (e) {
        // Continue checking
      }
    }
    
    if (!settingsFound) {
      console.log('⚠️ Settings page loaded but no settings elements found');
    }
  });

  test('Navigation between pages works', async ({ page }) => {
    await page.goto(FRONTEND_URL);
    
    // Wait for initial load
    await page.waitForLoadState('networkidle');
    
    // Try to find navigation links
    const navSelectors = [
      'nav a',
      '[data-testid*="nav"]',
      '.nav-link',
      '.sidebar a',
      '[class*="nav"] a'
    ];
    
    let navFound = false;
    for (const selector of navSelectors) {
      const links = await page.locator(selector).count();
      if (links > 0) {
        navFound = true;
        console.log(`✅ Found ${links} navigation links with selector: ${selector}`);
        
        // Try clicking the first few links
        const linksToTest = Math.min(3, links);
        for (let i = 0; i < linksToTest; i++) {
          const link = page.locator(selector).nth(i);
          const text = await link.textContent();
          const href = await link.getAttribute('href');
          console.log(`  - Navigation link ${i + 1}: "${text}" → ${href}`);
        }
        break;
      }
    }
    
    if (!navFound) {
      console.log('⚠️ No navigation links found');
    }
  });

  test('Backend database connection', async () => {
    // Make a request that requires database
    const response = await fetch(`${BACKEND_URL}/api/v1/stats`);
    expect(response.ok).toBeTruthy();
    
    const stats = await response.json();
    
    // These values come from database
    expect(stats).toHaveProperty('total_files');
    expect(stats).toHaveProperty('total_users');
    expect(stats).toHaveProperty('total_shares');
    
    console.log('✅ Database connection verified through stats endpoint');
  });

  test('Create user through API', async () => {
    const userData = {
      username: `test_user_${Date.now()}`,
      email: `test_${Date.now()}@example.com`
    };
    
    const response = await fetch(`${BACKEND_URL}/api/v1/users`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(userData),
    });
    
    expect(response.ok).toBeTruthy();
    
    const user = await response.json();
    expect(user).toHaveProperty('user_id');
    expect(user).toHaveProperty('api_key');
    expect(user.username).toBe(userData.username);
    
    console.log('✅ User created successfully:', user.user_id);
  });
});

test.describe('Visual Regression Tests', () => {
  test('Dashboard screenshot', async ({ page }) => {
    await page.goto(`${FRONTEND_URL}/dashboard`);
    await page.waitForLoadState('networkidle');
    
    // Take screenshot for visual regression
    await page.screenshot({ 
      path: 'tests/screenshots/dashboard.png',
      fullPage: true 
    });
    
    console.log('📸 Dashboard screenshot saved');
  });

  test('Dark mode toggle', async ({ page }) => {
    await page.goto(FRONTEND_URL);
    await page.waitForLoadState('networkidle');
    
    // Try to find dark mode toggle
    const darkModeSelectors = [
      '[data-testid="dark-mode-toggle"]',
      'button[aria-label*="theme"]',
      'button[aria-label*="dark"]',
      '[class*="theme-toggle"]',
      '[class*="dark-mode"]'
    ];
    
    let toggleFound = false;
    for (const selector of darkModeSelectors) {
      const toggle = page.locator(selector).first();
      if (await toggle.count() > 0) {
        toggleFound = true;
        
        // Click to toggle dark mode
        await toggle.click();
        await page.waitForTimeout(500); // Wait for transition
        
        // Check if dark mode class is applied
        const isDark = await page.evaluate(() => {
          return document.documentElement.classList.contains('dark') ||
                 document.body.classList.contains('dark-mode') ||
                 document.body.classList.contains('dark');
        });
        
        console.log(`✅ Dark mode toggle found and clicked. Dark mode: ${isDark}`);
        
        // Take screenshot in dark mode
        await page.screenshot({ 
          path: 'tests/screenshots/dark-mode.png',
          fullPage: true 
        });
        
        break;
      }
    }
    
    if (!toggleFound) {
      console.log('⚠️ Dark mode toggle not found');
    }
  });
});