import { test, expect } from '@playwright/test';

test('has title', async ({ page }) => {
  await page.goto('/');
  await expect(page).toHaveTitle(/Flying Coin/);
});

test('login link works', async ({ page }) => {
  await page.goto('/');
  const loginButton = page.getByRole('button', { name: /sign in/i });
  await expect(loginButton).toBeVisible();
});
