import { test, expect, Page } from '@playwright/test';
import { TestDataGenerator } from '../test-data-generator';

test.describe('UsenetSync Full Application Test', () => {
  let page: Page;

  test.beforeEach(async ({ page: p }) => {
    page = p;
    await page.goto('/');
  });

  test('Complete user journey - Upload, Share, Download', async () => {
    // Step 1: License Activation (if needed)
    const licenseDialog = page.locator('[data-testid="license-activation"]');
    if (await licenseDialog.isVisible()) {
      await page.fill('[placeholder*="license key"]', 'TEST-KEY-1234-5678');
      await page.click('button:has-text("Activate")');
      await expect(page.locator('text=License activated')).toBeVisible();
    }

    // Step 2: Navigate to Upload
    await page.click('a[href="/upload"]');
    await expect(page).toHaveURL('/upload');
    await expect(page.locator('h1:has-text("Upload Files")')).toBeVisible();

    // Step 3: Test drag and drop area
    const dropZone = page.locator('[data-testid="drop-zone"], .border-dashed').first();
    await expect(dropZone).toBeVisible();
    
    // Step 4: Select files (simulate)
    await page.click('button:has-text("Select Folder")');
    
    // Step 5: Test view mode toggle
    const gridButton = page.locator('button[title="Grid view"]');
    const listButton = page.locator('button[title="List view"]');
    
    if (await gridButton.isVisible()) {
      await gridButton.click();
      await expect(page.locator('.grid')).toBeVisible();
      await listButton.click();
    }

    // Step 6: Navigate to Download
    await page.click('a[href="/download"]');
    await expect(page).toHaveURL('/download');
    await expect(page.locator('h1:has-text("Download Share")')).toBeVisible();

    // Step 7: Test share ID input
    await page.fill('input[placeholder*="share ID"]', 'TESTSHARE123');
    await page.click('button:has-text("Look up")');

    // Step 8: Navigate to Shares
    await page.click('a[href="/shares"]');
    await expect(page).toHaveURL('/shares');
    await expect(page.locator('h1:has-text("My Shares")')).toBeVisible();

    // Step 9: Test version history
    const historyButton = page.locator('button[title="Version History"]').first();
    if (await historyButton.isVisible()) {
      await historyButton.click();
      await expect(page.locator('h2:has-text("Version History")')).toBeVisible();
      await page.click('button:has-text("×")');
    }

    // Step 10: Test Settings
    await page.click('a[href="/settings"]');
    await expect(page).toHaveURL('/settings');
    await expect(page.locator('h1:has-text("Settings")')).toBeVisible();

    // Step 11: Test bandwidth controls
    const bandwidthSection = page.locator('text=Bandwidth Control').first();
    if (await bandwidthSection.isVisible()) {
      await page.fill('input[placeholder*="upload"]', '1000');
      await page.fill('input[placeholder*="download"]', '5000');
    }

    // Step 12: Test dark mode toggle
    const darkModeToggle = page.locator('button[title*="mode"]').first();
    await darkModeToggle.click();
    await expect(page.locator('html')).toHaveClass(/dark/);
    await darkModeToggle.click();

    // Step 13: Test Logs page
    await page.click('a[href="/logs"]');
    await expect(page).toHaveURL('/logs');
    await expect(page.locator('h1:has-text("System Logs")')).toBeVisible();

    // Step 14: Test log filtering
    await page.selectOption('select:has-text("All Levels")', 'error');
    await page.fill('input[placeholder*="Search"]', 'test error');
    
    // Step 15: Navigate back to Dashboard
    await page.click('a[href="/"]');
    await expect(page).toHaveURL('/');
    await expect(page.locator('h1:has-text("Dashboard")')).toBeVisible();

    // Step 16: Test context menu
    await page.click('body', { button: 'right' });
    const contextMenu = page.locator('[data-testid="context-menu"]');
    if (await contextMenu.isVisible()) {
      await expect(contextMenu.locator('text=New Upload')).toBeVisible();
      await page.keyboard.press('Escape');
    }

    // Step 17: Test notifications
    const notificationBell = page.locator('button:has([data-testid="bell-icon"])');
    if (await notificationBell.isVisible()) {
      await notificationBell.click();
      await expect(page.locator('[data-testid="notification-center"]')).toBeVisible();
      await page.click('body');
    }
  });

  test('Test all keyboard shortcuts', async () => {
    // Test Ctrl+U for Upload
    await page.keyboard.press('Control+u');
    await expect(page).toHaveURL('/upload');

    // Test Ctrl+D for Download
    await page.keyboard.press('Control+d');
    await expect(page).toHaveURL('/download');

    // Test Ctrl+S for Settings
    await page.keyboard.press('Control+s');
    await expect(page).toHaveURL('/settings');

    // Test Escape to close modals
    const modal = page.locator('.fixed.inset-0');
    if (await modal.isVisible()) {
      await page.keyboard.press('Escape');
      await expect(modal).not.toBeVisible();
    }
  });

  test('Test responsive design', async () => {
    // Test mobile view
    await page.setViewportSize({ width: 375, height: 667 });
    
    // Check if mobile menu button is visible
    const mobileMenuButton = page.locator('button:has([data-testid="menu-icon"])');
    await expect(mobileMenuButton).toBeVisible();
    
    // Open mobile menu
    await mobileMenuButton.click();
    await expect(page.locator('aside')).toBeVisible();
    
    // Test tablet view
    await page.setViewportSize({ width: 768, height: 1024 });
    
    // Test desktop view
    await page.setViewportSize({ width: 1920, height: 1080 });
    await expect(page.locator('aside')).toBeVisible();
  });

  test('Test error handling', async () => {
    // Test invalid share ID
    await page.goto('/download');
    await page.fill('input[placeholder*="share ID"]', '');
    await page.click('button:has-text("Look up")');
    await expect(page.locator('text=Please enter a share ID')).toBeVisible();

    // Test network error simulation
    await page.route('**/api/**', route => route.abort());
    await page.goto('/');
    // Should show error state or fallback
  });

  test('Test data persistence', async () => {
    // Add a file to upload
    await page.goto('/upload');
    
    // Navigate away and back
    await page.goto('/dashboard');
    await page.goto('/upload');
    
    // Check if state is preserved
    // This depends on your state management
  });
});