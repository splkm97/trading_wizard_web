/**
 * Playwright E2E Tests for Contrarian Strategy Navigation
 *
 * Tests covering T029-T032 from tasks.md:
 * - T029: Navigate to /contrarian page and verify it loads correctly
 * - T030-T032: Navigation between strategies
 */

import { test, expect, Page } from "@playwright/test";

const BASE_URL = 'http://localhost:5173';
const CONTRARIAN_URL = `${BASE_URL}/contrarian`;
const TRADE_URL = `${BASE_URL}/trade`;

class StrategyNavigationHelpers {
  static async setupPage(page: Page): Promise<void> {
    await page.waitForTimeout(500);

    const disclaimerButton = page.getByRole('button', { name: /동의합니다|agree|이해하고 동의/i });
    if (await disclaimerButton.isVisible({ timeout: 1000 }).catch(() => false)) {
      await disclaimerButton.click();
      await page.waitForTimeout(500);
    }

    const loginTab = page.getByRole('button', { name: /회원가입/i });
    if (await loginTab.isVisible({ timeout: 1000 }).catch(() => false)) {
      await loginTab.click();
      await page.getByRole('button', { name: /새 키 생성/i }).click();

      // Wait for key generation to complete
      await page.waitForTimeout(2000);

      // Wait for the registration button to be enabled (not loading)
      const registerButton = page.getByRole('button', { name: /등록 완료/i });
      await expect(registerButton).toBeEnabled({ timeout: 30000 });
      await registerButton.click();

      // Wait for navigation with longer timeout
      await page.waitForURL(/\/(dashboard|contrarian|trade)/, { timeout: 90000 });
      await page.waitForTimeout(500);

      const disclaimerAfterLogin = page.getByRole('button', { name: /동의합니다|agree|이해하고 동의/i });
      if (await disclaimerAfterLogin.isVisible({ timeout: 2000 }).catch(() => false)) {
        await disclaimerAfterLogin.click();
        await page.waitForTimeout(500);
      }
    }
  }

  static async ensureLoggedIn(page: Page): Promise<void> {
    await this.setupPage(page);
  }

  static async dismissDisclaimerIfPresent(page: Page): Promise<void> {
    const disclaimerButton = page.getByRole('button', { name: /동의합니다|agree|이해하고 동의/i });
    if (await disclaimerButton.isVisible({ timeout: 1000 }).catch(() => false)) {
      await disclaimerButton.click();
      await page.waitForTimeout(500);
    }
  }
}

/**
 * T029 [US4] E2E: Strategy Navigation - Contrarian Page
 */
test.describe('Contrarian Strategy Navigation', () => {
  test('T029: Navigate to /contrarian page and verify it loads correctly', async ({ page }) => {
    page.on('console', msg => console.log('BROWSER:', msg.type(), msg.text()));
    page.on('pageerror', err => console.error('PAGE ERROR:', err));

    await page.goto(CONTRARIAN_URL, { waitUntil: 'networkidle' });
    await StrategyNavigationHelpers.ensureLoggedIn(page);
    await StrategyNavigationHelpers.dismissDisclaimerIfPresent(page);

    // Verify page title is visible
    await expect(page.getByRole('heading', { name: /MACD\/RSI 역추세 전략/i })).toBeVisible();

    // Verify strategy explanation cards are present
    await expect(page.getByText(/RSI 과매도란/)).toBeVisible();
    await expect(page.getByText(/MACD 골든크로스란/)).toBeVisible();
    await expect(page.getByText(/역추세 전략이란/)).toBeVisible();

    // Verify risk warning is present
    await expect(page.getByText(/투자 유의사항/)).toBeVisible();
  });

  test('T029: Navigate from /contrarian to /trade via strategy switcher', async ({ page }) => {
    await page.goto(CONTRARIAN_URL, { waitUntil: 'networkidle' });
    await StrategyNavigationHelpers.ensureLoggedIn(page);
    await StrategyNavigationHelpers.dismissDisclaimerIfPresent(page);

    // Click on the Bollinger Band strategy link
    const bollingerLink = page.getByRole('link', { name: /볼린저 밴드 전략|Bollinger Band/i });
    await expect(bollingerLink).toBeVisible();
    await bollingerLink.click();

    // Verify navigation to TradePage
    await page.waitForURL(/\/trade/, { timeout: 10000 });
    expect(page.url()).toContain('/trade');

    // Verify TradePage content
    await expect(page.getByRole('heading', { name: /거래 입력/i })).toBeVisible();
  });

  test('T029: Navigate from /trade to /contrarian via strategy switcher', async ({ page }) => {
    await page.goto(TRADE_URL, { waitUntil: 'networkidle' });
    await StrategyNavigationHelpers.ensureLoggedIn(page);
    await StrategyNavigationHelpers.dismissDisclaimerIfPresent(page);

    // Click on the MACD/RSI strategy link
    const contrarianLink = page.getByRole('link', { name: /MACD\/RSI 역추세 전략|역추세 전략/i });
    await expect(contrarianLink).toBeVisible();
    await contrarianLink.click();

    // Verify navigation to ContrarianPage
    await page.waitForURL(/\/contrarian/, { timeout: 10000 });
    expect(page.url()).toContain('/contrarian');

    // Verify ContrarianPage content
    await expect(page.getByRole('heading', { name: /MACD\/RSI 역추세 전략/i })).toBeVisible();
  });

  test('T030: Verify MACD/RSI Strategy link in main navigation', async ({ page }) => {
    await page.goto(BASE_URL, { waitUntil: 'networkidle' });
    await StrategyNavigationHelpers.ensureLoggedIn(page);
    await StrategyNavigationHelpers.dismissDisclaimerIfPresent(page);

    // Navigate to dashboard first
    await page.goto(`${BASE_URL}/dashboard`, { waitUntil: 'networkidle' });

    // Look for MACD/RSI strategy link in navigation
    const navLink = page.locator('nav').getByRole('link', { name: /MACD\/RSI|역추세/i });
    await expect(navLink).toBeVisible();

    // Click navigation link
    await navLink.click();

    // Verify navigation to contrarian page
    await page.waitForURL(/\/contrarian/, { timeout: 10000 });
    expect(page.url()).toContain('/contrarian');
  });

  test('T029: Round-trip navigation between strategies', async ({ page }) => {
    // Start at Contrarian page
    await page.goto(CONTRARIAN_URL, { waitUntil: 'networkidle' });
    await StrategyNavigationHelpers.ensureLoggedIn(page);
    await StrategyNavigationHelpers.dismissDisclaimerIfPresent(page);

    // Navigate to TradePage
    const bollingerLink = page.getByRole('link', { name: /볼린저 밴드 전략|Bollinger Band/i });
    await bollingerLink.click();
    await page.waitForURL(/\/trade/, { timeout: 10000 });

    // Navigate back to Contrarian
    const contrarianLink = page.getByRole('link', { name: /MACD\/RSI 역추세 전략|역추세 전략/i });
    await contrarianLink.click();
    await page.waitForURL(/\/contrarian/, { timeout: 10000 });

    // Verify we're back at Contrarian page
    await expect(page.getByRole('heading', { name: /MACD\/RSI 역추세 전략/i })).toBeVisible();
  });
});

test.afterEach(async ({ page }, testInfo) => {
  if (testInfo.status === 'failed') {
    await page.screenshot({
      path: `test-results/${testInfo.title}-fail.png`,
      fullPage: true
    });
  }
});
