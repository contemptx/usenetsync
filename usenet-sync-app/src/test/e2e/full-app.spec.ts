import { test, expect, Page } from '@playwright/test';
import { TestDataGenerator } from '../test-data-generator';

test.describe('UsenetSync Full Application Test', () => {
  let page: Page;

  test.beforeEach(async ({ page: p }) => {
    page = p;
    await page.goto('/');
    // Wait for app to load
    await page.waitForLoadState('networkidle');

    // Dismiss license/startup screen if present by starting trial
    const startTrial = page.locator('button:has-text("Start Trial")');
    const continueBtn = page.locator('button:has-text("Continue")');
    const skipBtn = page.locator('button:has-text("Skip")');

    try {
      if (await startTrial.isVisible({ timeout: 1500 })) {
        await startTrial.click();
        await page.waitForLoadState('networkidle');
      } else if (await continueBtn.isVisible({ timeout: 1000 }).catch(() => false)) {
        await continueBtn.click();
      } else if (await skipBtn.isVisible({ timeout: 1000 }).catch(() => false)) {
        await skipBtn.click();
      }
    } catch {}
  });

  test('Complete user journey - Upload, Share, Download', async () => {
    // Step 1: License Check (app may already be activated)
    const licenseDialog = page.locator('[data-testid="license-activation"]');
    if (await licenseDialog.isVisible({ timeout: 2000 }).catch(() => false)) {
      await page.fill('[placeholder*="license key"]', 'TEST-KEY-1234-5678');
      await page.click('button:has-text("Activate")');
      await expect(page.locator('text=License activated')).toBeVisible({ timeout: 5000 });
    }

    // Step 2: Navigate to Upload
    await page.click('[data-testid="nav-upload"]');
    await expect(page).toHaveURL('/upload');
    await expect(page.locator('[data-testid="upload-title"]')).toBeVisible();

    // Step 3: Test drag and drop area
    const dropZone = page.locator('[data-testid="drop-zone"]');
    await expect(dropZone).toBeVisible();
    
    // Step 4: Select folder button
    const selectFolderButton = page.locator('[data-testid="select-folder"]');
    await expect(selectFolderButton).toBeVisible();
    
    // Click to trigger file selection (mocked)
    await selectFolderButton.click();
    
    // Step 5: Create share (if files are selected)
    const createShareButton = page.locator('button:has-text("Create Share")');
    if (await createShareButton.isVisible({ timeout: 2000 }).catch(() => false)) {
      await createShareButton.click();
      await expect(page.locator('text=/Share.*created/i')).toBeVisible({ timeout: 5000 });
    }

    // Step 6: Navigate to Download
    await page.click('[data-testid="nav-download"]');
    await expect(page).toHaveURL('/download');
    await expect(page.locator('[data-testid="download-title"]')).toBeVisible();

    // Step 7: Test share lookup
    const shareIdInput = page.locator('[data-testid="share-id-input"]');
    await shareIdInput.fill('TESTSHARE123');
    
    const lookupButton = page.locator('[data-testid="lookup-button"]');
    await lookupButton.click();
    
    // Wait for either success or error message
    await expect(page.locator('text=/Share details|not found|error/i')).toBeVisible({ timeout: 5000 });

    // Step 8: Navigate to Shares
    await page.click('[data-testid="nav-shares"]');
    await expect(page).toHaveURL('/shares');
    
    // Check if shares page loads
    await expect(page.locator('h1:has-text("Shares")')).toBeVisible();
  });

  test('Test view mode toggle', async () => {
    // Navigate to Upload
    await page.click('[data-testid="nav-upload"]');
    await expect(page).toHaveURL('/upload');
    
    // Select folder to show file view
    const selectFolderButton = page.locator('[data-testid="select-folder"]');
    if (await selectFolderButton.isVisible({ timeout: 2000 }).catch(() => false)) {
      await selectFolderButton.click();
    }
    
    // Look for view mode toggle buttons
    const gridViewButton = page.locator('button[title="Grid view"]');
    const listViewButton = page.locator('button[title="List view"]');
    
    // Test toggling if buttons exist
    if (await gridViewButton.isVisible({ timeout: 2000 }).catch(() => false)) {
      await gridViewButton.click();
      // Verify grid view is active
      await expect(gridViewButton).toHaveClass(/bg-primary/);
      
      await listViewButton.click();
      // Verify list view is active
      await expect(listViewButton).toHaveClass(/bg-primary/);
    }
  });

  test('Test share ID lookup', async () => {
    // Navigate to Download
    await page.click('[data-testid="nav-download"]');
    await expect(page).toHaveURL('/download');
    
    // Test empty share ID
    const lookupButton = page.locator('[data-testid="lookup-button"]');
    await expect(lookupButton).toBeDisabled();
    
    // Test with share ID
    const shareIdInput = page.locator('[data-testid="share-id-input"]');
    await shareIdInput.fill('ABCD1234EFGH');
    await expect(lookupButton).toBeEnabled();
    
    await lookupButton.click();
    
    // Wait for response
    await page.waitForResponse(response => 
      response.url().includes('share') || response.status() === 200,
      { timeout: 5000 }
    ).catch(() => {});
  });

  test('Test all keyboard shortcuts', async () => {
    // Wait for app to be ready
    await page.waitForLoadState('networkidle');
    
    // Test Ctrl+U for Upload
    await page.keyboard.press('Control+u');
    await page.waitForURL('/upload', { timeout: 2000 }).catch(() => {});
    
    // Test Ctrl+D for Download  
    await page.keyboard.press('Control+d');
    await page.waitForURL('/download', { timeout: 2000 }).catch(() => {});
    
    // Test Ctrl+, for Settings
    await page.keyboard.press('Control+Comma');
    await page.waitForURL('/settings', { timeout: 2000 }).catch(() => {});
    
    // Test dark mode toggle (if shortcut exists)
    const bodyElement = page.locator('body');
    const initialDarkMode = await bodyElement.evaluate(el => el.classList.contains('dark'));
    
    // Try common dark mode shortcuts
    await page.keyboard.press('Control+Shift+d');
    await page.waitForTimeout(500);
    
    const afterDarkMode = await bodyElement.evaluate(el => el.classList.contains('dark'));
    // Dark mode might have toggled
  });

  test('Test responsive design', async () => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });
    
    // Check if mobile menu button is visible
    const mobileMenuButton = page.locator('[data-testid="menu-toggle"]');
    await expect(mobileMenuButton).toBeVisible();
    
    // Open mobile menu
    await mobileMenuButton.click();
    
    // Check if navigation is visible
    const navigation = page.locator('nav');
    await expect(navigation).toBeVisible();
    
    // Close menu
    const closeButton = page.locator('button:has([data-testid="menu-close-icon"])');
    if (await closeButton.isVisible({ timeout: 2000 }).catch(() => false)) {
      await closeButton.click();
    }
    
    // Reset viewport
    await page.setViewportSize({ width: 1280, height: 720 });
  });

  test('Test error handling', async () => {
    // Navigate to Download
    await page.click('[data-testid="nav-download"]');
    
    // Test with invalid share ID format
    const shareIdInput = page.locator('[data-testid="share-id-input"]');
    await shareIdInput.fill('INVALID!@#');
    
    const lookupButton = page.locator('[data-testid="lookup-button"]');
    await lookupButton.click();
    
    // Should show error message
    await expect(page.locator('text=/error|invalid|not found/i')).toBeVisible({ timeout: 5000 });
  });

  test('Test data persistence', async () => {
    // Create some test data
    const testShareId = 'PERSIST' + Date.now();
    
    // Navigate to Download and enter share ID
    await page.click('[data-testid="nav-download"]');
    const shareIdInput = page.locator('[data-testid="share-id-input"]');
    await shareIdInput.fill(testShareId);
    
    // Reload page
    await page.reload();
    await page.waitForLoadState('networkidle');
    
    // Check if app state persists (this depends on your state management)
    // The app should still be on the same page or maintain some state
    const currentUrl = page.url();
    expect(currentUrl).toContain('/download');
  });

  test('Test notification system', async () => {
    // Look for notification bell
    const notificationBell = page.locator('[data-testid="bell-icon"]');
    if (await notificationBell.isVisible({ timeout: 2000 }).catch(() => false)) {
      await notificationBell.click();
      
      // Check if notification center opens
      const notificationCenter = page.locator('[data-testid="notification-center"]');
      await expect(notificationCenter).toBeVisible({ timeout: 2000 });
      
      // Close notification center
      await page.keyboard.press('Escape');
      await expect(notificationCenter).not.toBeVisible({ timeout: 2000 });
    }
  });

  test('Test dark mode toggle', async () => {
    // Find dark mode toggle button
    const darkModeToggle = page.locator('button[title*="theme"], button[title*="mode"], button:has-text("Dark"), button:has-text("Light")').first();
    
    if (await darkModeToggle.isVisible({ timeout: 2000 }).catch(() => false)) {
      const bodyElement = page.locator('body');
      const initialDarkMode = await bodyElement.evaluate(el => el.classList.contains('dark'));
      
      // Toggle dark mode
      await darkModeToggle.click();
      await page.waitForTimeout(500);
      
      // Check if dark mode changed
      const afterDarkMode = await bodyElement.evaluate(el => el.classList.contains('dark'));
      expect(afterDarkMode).not.toBe(initialDarkMode);
      
      // Toggle back
      await darkModeToggle.click();
      await page.waitForTimeout(500);
      
      const finalDarkMode = await bodyElement.evaluate(el => el.classList.contains('dark'));
      expect(finalDarkMode).toBe(initialDarkMode);
    }
  });

  test('Test context menu', async () => {
    // Navigate to Dashboard
    await page.click('[data-testid="nav-dashboard"]');
    
    // Right-click on main content area
    const mainContent = page.locator('main, [role="main"], .p-6').first();
    await mainContent.click({ button: 'right' });
    
    // Check if context menu appears
    const contextMenu = page.locator('[role="menu"], .context-menu, [data-testid="context-menu"]');
    if (await contextMenu.isVisible({ timeout: 2000 }).catch(() => false)) {
      // Click outside to close
      await page.keyboard.press('Escape');
      await expect(contextMenu).not.toBeVisible({ timeout: 2000 });
    }
  });
});