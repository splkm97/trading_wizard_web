/**
 * Simulation API client for Turn-Based Trading Simulation Game.
 */

import { api } from './api';
import type {
  GameSession,
  GameSessionWithSummary,
  StockRecommendation,
  StockDetail,
  GameReport,
  CreateSessionRequest,
  ExecuteTradeRequest,
  ExecuteTradeResponse,
  AdvanceTurnResponse,
  ExportTradesResponse,
} from '../types/simulation';

const BASE_PATH = '/simulation';

/**
 * Create a new game session.
 */
export async function createSession(params: CreateSessionRequest): Promise<GameSessionWithSummary> {
  return api.post<GameSessionWithSummary>(`${BASE_PATH}/sessions`, params);
}

/**
 * Get list of user's game sessions.
 */
export async function getSessions(status?: string): Promise<GameSession[]> {
  const query = status ? `?status=${status}` : '';
  return api.get<GameSession[]>(`${BASE_PATH}/sessions${query}`);
}

/**
 * Get a specific game session with portfolio summary.
 */
export async function getSession(sessionId: string): Promise<GameSessionWithSummary> {
  return api.get<GameSessionWithSummary>(`${BASE_PATH}/sessions/${sessionId}`);
}

/**
 * Delete a game session.
 */
export async function deleteSession(sessionId: string): Promise<void> {
  return api.delete(`${BASE_PATH}/sessions/${sessionId}`);
}

/**
 * Get stock recommendations for current turn.
 */
export async function getRecommendations(sessionId: string): Promise<StockRecommendation[]> {
  return api.get<StockRecommendation[]>(`${BASE_PATH}/sessions/${sessionId}/recommendations`);
}

/**
 * Get stock detail with chart data and indicators.
 */
export async function getStockDetail(sessionId: string, stockCode: string): Promise<StockDetail> {
  return api.get<StockDetail>(`${BASE_PATH}/sessions/${sessionId}/stocks/${stockCode}`);
}

/**
 * Execute a trade (buy or sell).
 */
export async function executeTrade(
  sessionId: string,
  params: ExecuteTradeRequest
): Promise<ExecuteTradeResponse> {
  return api.post<ExecuteTradeResponse>(`${BASE_PATH}/sessions/${sessionId}/trade`, params);
}

/**
 * Advance to next trading day.
 */
export async function advanceTurn(sessionId: string): Promise<AdvanceTurnResponse> {
  return api.post<AdvanceTurnResponse>(`${BASE_PATH}/sessions/${sessionId}/turn`, {});
}

/**
 * Get game report (backtest-style metrics).
 */
export async function getReport(sessionId: string): Promise<GameReport> {
  return api.get<GameReport>(`${BASE_PATH}/sessions/${sessionId}/report`);
}

/**
 * Export trades as JSON (compatible with existing backtest system).
 */
export async function exportTrades(sessionId: string): Promise<ExportTradesResponse> {
  return api.get<ExportTradesResponse>(`${BASE_PATH}/sessions/${sessionId}/export`);
}

/**
 * Download trades as JSON file.
 */
export async function downloadTradesJson(sessionId: string, filename?: string): Promise<void> {
  const data = await exportTrades(sessionId);
  const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename || `simulation_${sessionId}_trades.json`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

/**
 * Pre-compute recommendations for next N trading days.
 * Call this in the background after initial recommendations are loaded.
 */
export async function precomputeRecommendations(
  sessionId: string,
  daysAhead: number = 3
): Promise<{ days_computed: number; message: string }> {
  return api.post<{ days_computed: number; message: string }>(
    `${BASE_PATH}/sessions/${sessionId}/precompute?days_ahead=${daysAhead}`,
    {}
  );
}

export interface SaveAsBacktestResponse {
  backtest_id: string;
  name: string;
  message: string;
}

/**
 * Save simulation session as a backtest record.
 * Converts the simulation game results to BacktestResult format and saves it
 * to the backtest history for comparison.
 */
export async function saveAsBacktest(
  sessionId: string,
  customName?: string
): Promise<SaveAsBacktestResponse> {
  return api.post<SaveAsBacktestResponse>(
    `${BASE_PATH}/sessions/${sessionId}/save-as-backtest`,
    customName ? { name: customName } : {}
  );
}
