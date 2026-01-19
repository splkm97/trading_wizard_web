/**
 * E2E Test Fixtures for Simulation Game
 *
 * Provides helper functions for setting up test sessions, logging in, and cleanup.
 */

import { Page } from '@playwright/test';

export const TEST_DATES = {
  startDate: '2024-01-02',
  endDate: '2024-03-29',
  shortPeriod: {
    start: '2024-01-02',
    end: '2024-01-15',
  },
} as const;

export const TEST_DATA = {
  initialCapital: 100000000,
  gameName: 'E2E Test Session',
} as const;

export const BASE_URL = 'http://localhost:5173';
export const SIMULATION_URL = `${BASE_URL}/simulation`;

type LoginResult = {
  token: string;
  userId: string;
  username: string;
};

export class SimulationTestHelpers {
  static async loginWithTestUser(page: Page): Promise<LoginResult> {
    await page.goto(`${BASE_URL}/login`);

    await page.fill('[name="username"]', 'test_e2e_user');
    await page.click('button[type="submit"]');

    await page.waitForURL(`${BASE_URL}/(dashboard|simulation)`, { timeout: 10000 });

    const storage = await page.evaluate(() => {
      return {
        token: localStorage.getItem('auth_token'),
        userId: localStorage.getItem('user_id'),
        username: localStorage.getItem('username'),
      };
    });

    if (!storage.token || !storage.userId) {
      throw new Error('Login failed - no token or userId in storage');
    }

    return {
      token: storage.token!,
      userId: storage.userId!,
      username: storage.username || 'test_e2e_user',
    };
  }

  static async createTestSession(page: Page): Promise<string> {
    await page.goto(SIMULATION_URL);

    await page.getByRole('button', { name: /new game|새 게임|게임 시작/i }).click();

    await page.fill('input[name="start_date"]', TEST_DATES.startDate);
    await page.fill('input[name="end_date"]', TEST_DATES.endDate);
    await page.fill('input[name="initial_capital"]', TEST_DATA.initialCapital.toString());
    await page.fill('input[name="name"]', TEST_DATA.gameName);

    await page.getByRole('button', { name: /start|게임 시작/i }).click();

    await page.waitForURL(/\/simulation\/[a-f0-9-]+/, { timeout: 15000 });

    const currentUrl = page.url();
    const sessionId = currentUrl.split('/').pop();
    if (!sessionId) {
      throw new Error('Failed to extract session ID from URL');
    }

    return sessionId;
  }

  static async deleteTestSession(page: Page, sessionId: string): Promise<void> {
    await page.goto(SIMULATION_URL);

    const existingGameCard = page.getByText(TEST_DATA.gameName);
    if (await existingGameCard.count() > 0) {
      const deleteButton = existingGameCard.getByRole('button', { name: /delete|삭제/i });
      await deleteButton.click();

      const confirmButton = page.getByRole('button', { name: /confirm|확인/i });
      await confirmButton.click();

      await page.waitForTimeout(1000);
    }
  }

  static async cleanupAll(page: Page): Promise<void> {
    await page.goto(SIMULATION_URL);

    const gameCards = page.locator('.game-card');
    const count = await gameCards.count();

    for (let i = 0; i < count; i++) {
      const card = gameCards.nth(i);
      await card.hover();
      const deleteButton = card.getByRole('button', { name: /delete|삭제/i });
      if (await deleteButton.isVisible()) {
        await deleteButton.click();

        const confirmButton = page.getByRole('button', { name: /confirm|확인/i });
        await confirmButton.click();

        await page.waitForTimeout(500);
      }
    }
  }

  static async waitForRecommendations(page: Page): Promise<void> {
    await page.waitForSelector('[data-testid="recommendation-list"]', { timeout: 10000 });
  }

  static async selectStock(page: Page, stockCode: string): Promise<void> {
    const stockItem = page.locator(`[data-stock-code="${stockCode}"]`);
    await stockItem.scrollIntoViewIfNeeded();
    await stockItem.click();
    
    await page.waitForSelector('[data-testid="stock-detail"]', { timeout: 10000 });
  }

  static async executeBuyTrade(page: Page, params: { quantity?: number; amount?: number }): Promise<void> {
    const buyButton = page.getByRole('button', { name: /buy|매수/i });
    await buyButton.click();

    const modal = page.locator('[role="dialog"]');
    if (params.quantity) {
      await modal.fill('input[name="quantity"]', params.quantity.toString());
    } else if (params.amount) {
      await modal.fill('input[name="amount"]', params.amount.toString());
    }

    await modal.getByRole('button', { name: /confirm|확인/i }).click();

    await page.waitForSelector('text=/loading|처리 중/i', { state: 'hidden', timeout: 10000 });
  }

  static async executeSellTrade(page: Page): Promise<void> {
    const sellButton = page.getByRole('button', { name: /sell|매도/i });
    await sellButton.click();

    await page.waitForSelector('text=/loading|처리 중/i', { state: 'hidden', timeout: 10000 });
  }

  static async advanceTurn(page: Page): Promise<void> {
    const nextDayButton = page.getByRole('button', { name: /next day|next turn|다음 날/i });
    await nextDayButton.click();

    await page.waitForSelector('text=/loading|처리 중|이동 중/i', { state: 'hidden', timeout: 15000 });
  }

  static async openReportModal(page: Page): Promise<void> {
    const reportButton = page.getByRole('button', { name: /report|리포트/i });
    await reportButton.click();

    await page.waitForSelector('[data-testid="report-modal"]', { timeout: 10000 });
  }

  static async closeReportModal(page: Page): Promise<void> {
    const modal = page.locator('[data-testid="report-modal"]');
    const closeButton = modal.getByRole('button', { name: /close|닫기/i });
    if (await closeButton.isVisible()) {
      await closeButton.click();

      await page.waitForSelector('[data-testid="report-modal"]', { state: 'hidden', timeout: 5000 });
    }
  }
}
