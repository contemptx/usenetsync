import { test, expect } from '@playwright/test';

test('Fetch and render live Usenet sample', async ({ page }) => {
  await page.goto('/');
  // Replace selectors to match your UI:
  await page.getByRole('button', { name: /fetch latest/i }).click();

  // Backend should log/reflect live connection
  await page.getByText(/connected to/i).waitFor({ timeout: 15000 });

  const rows = page.locator('[data-test="article-row"]');
  await expect(rows).toHaveCountGreaterThan(0);

  await rows.first().click();
  await expect(page.locator('[data-test="article-body"]')).toContainText(/.+/);
});