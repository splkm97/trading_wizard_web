import { test, expect } from "@playwright/test";

test('basic test', async ({ page }) => {
  await page.goto('http://localhost:5173');
  expect(page.url()).toContain('localhost');
});
