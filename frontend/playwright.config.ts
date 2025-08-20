import { defineConfig, devices } from '@playwright/test';

/**
 * Playwright configuration for UsenetSync E2E tests
 * Tests the unified refactored backend with real components
 */

export default defineConfig({
  testDir: './tests/e2e',
  fullyParallel: false, // Run tests sequentially to avoid conflicts
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: 1, // Single worker to avoid database conflicts
  reporter: [
    ['line'],
    ['html', { outputFolder: 'playwright-report' }]
  ],
  
  use: {
    baseURL: process.env.FRONTEND_BASE_URL || 'http://localhost:5173',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
    
    // Longer timeouts for real backend operations
    actionTimeout: 15000,
    navigationTimeout: 30000,
  },

  timeout: 60000, // 60 seconds per test

  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
    // Uncomment to test on other browsers
    // {
    //   name: 'firefox',
    //   use: { ...devices['Desktop Firefox'] },
    // },
    // {
    //   name: 'webkit',
    //   use: { ...devices['Desktop Safari'] },
    // },
  ],

  // Run local dev server before tests
  webServer: [
    {
      command: 'cd /workspace && source venv/bin/activate && PYTHONPATH=/workspace/src python -m unified.api.server',
      port: 8000,
      timeout: 30000,
      reuseExistingServer: !process.env.CI,
      env: {
        DATABASE_URL: 'postgresql://usenetsync:usenetsync123@localhost:5432/usenetsync',
        NNTP_HOST: 'news.newshosting.com',
        NNTP_PORT: '563',
        NNTP_USERNAME: 'contemptx',
        NNTP_PASSWORD: 'Kia211101#',
        NNTP_SSL: 'true',
      },
    },
    {
      command: 'npm run dev',
      port: 5173,
      timeout: 30000,
      reuseExistingServer: !process.env.CI,
    }
  ],
});