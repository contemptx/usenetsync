import { defineConfig } from '@playwright/test';

export default defineConfig({
  use: {
    baseURL: process.env.FRONTEND_BASE_URL || 'http://localhost:5173',
    headless: true,
  },
  reporter: 'line',
  timeout: 60000
});