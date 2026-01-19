/**
 * API client for Trading Wizard Web backend.
 */

import type {
  ContrarianSignalsResponse,
  SingleContrarianSignalResponse,
  ContrarianCandidatesResponse,
} from '../types';

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api';

interface RequestOptions {
  method?: 'GET' | 'POST' | 'PUT' | 'DELETE';
  body?: unknown;
  headers?: Record<string, string>;
  timeout?: number; // Timeout in milliseconds
}

// Default timeout values (in milliseconds)
const DEFAULT_TIMEOUT = 30000; // 30 seconds for normal requests
const LONG_TIMEOUT = 120000; // 2 minutes for force_fetch requests

interface ApiError {
  detail: string;
  status: number;
  isTimeout?: boolean;
}

class ApiClient {
  private baseUrl: string;
  private token: string | null = null;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl;
  }

  setToken(token: string | null) {
    this.token = token;
  }

  getToken(): string | null {
    return this.token;
  }

  private async request<T>(endpoint: string, options: RequestOptions = {}): Promise<T> {
    const { method = 'GET', body, headers = {} } = options;

    // Determine timeout based on endpoint or explicit option
    const isLongRequest = endpoint.includes('force_fetch=true');
    const timeout = options.timeout ?? (isLongRequest ? LONG_TIMEOUT : DEFAULT_TIMEOUT);

    const requestHeaders: Record<string, string> = {
      'Content-Type': 'application/json',
      ...headers,
    };

    if (this.token) {
      requestHeaders['Authorization'] = `Bearer ${this.token}`;
    }

    // Create AbortController for timeout
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeout);

    try {
      const response = await fetch(`${this.baseUrl}${endpoint}`, {
        method,
        headers: requestHeaders,
        body: body ? JSON.stringify(body) : undefined,
        signal: controller.signal,
      });

      if (!response.ok) {
        const error: ApiError = {
          detail: 'An error occurred',
          status: response.status,
        };
        try {
          const errorData = await response.json();
          error.detail = errorData.detail || error.detail;
        } catch {
          // Ignore JSON parse errors
        }
        throw error;
      }

      // Handle 204 No Content
      if (response.status === 204) {
        return {} as T;
      }

      return response.json();
    } catch (err) {
      // Handle abort/timeout error
      if (err instanceof Error && err.name === 'AbortError') {
        const timeoutError: ApiError = {
          detail: `요청 시간이 초과되었습니다 (${timeout / 1000}초). 네트워크 상태를 확인하거나 잠시 후 다시 시도해주세요.`,
          status: 408, // Request Timeout
          isTimeout: true,
        };
        throw timeoutError;
      }
      throw err;
    } finally {
      clearTimeout(timeoutId);
    }
  }

  // Health check
  async healthCheck(): Promise<{ status: string; service: string }> {
    return this.request('/health');
  }

  // Generic methods for CRUD operations
  async get<T>(endpoint: string): Promise<T> {
    return this.request<T>(endpoint);
  }

  async post<T>(endpoint: string, body: unknown): Promise<T> {
    return this.request<T>(endpoint, { method: 'POST', body });
  }

  async put<T>(endpoint: string, body: unknown): Promise<T> {
    return this.request<T>(endpoint, { method: 'PUT', body });
  }

  async delete<T>(endpoint: string): Promise<T> {
    return this.request<T>(endpoint, { method: 'DELETE' });
  }

  async upload<T>(endpoint: string, formData: FormData): Promise<T> {
    const headers: Record<string, string> = {};

    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`;
    }

    const response = await fetch(`${this.baseUrl}${endpoint}`, {
      method: 'POST',
      headers,
      body: formData,
    });

    if (!response.ok) {
      const error: ApiError = {
        detail: 'An error occurred',
        status: response.status,
      };
      try {
        const errorData = await response.json();
        error.detail = errorData.detail || error.detail;
      } catch {
        // Ignore JSON parse errors
      }
      throw error;
    }

    return response.json();
  }
}

// Singleton instance
export const api = new ApiClient(API_BASE_URL);

// Contrarian Strategy API functions

/**
 * Get MACD/RSI contrarian signals.
 * Scans for stocks with RSI oversold + MACD golden cross.
 *
 * @param maxResults - Maximum number of signals to return (default: 10)
 * @param scanDate - Date to scan for signals (YYYY-MM-DD format, defaults to today)
 */
export async function getContrarianSignals(
  maxResults: number = 10,
  scanDate?: string
): Promise<ContrarianSignalsResponse> {
  let url = `/contrarian/signals?max_results=${maxResults}`;
  if (scanDate) {
    url += `&scan_date=${scanDate}`;
  }
  return api.get<ContrarianSignalsResponse>(url);
}

/**
 * Get contrarian signal for a specific stock.
 */
export async function getContrarianSignalForStock(
  stockCode: string
): Promise<SingleContrarianSignalResponse> {
  return api.get<SingleContrarianSignalResponse>(
    `/contrarian/signal/${stockCode}`
  );
}

/**
 * Get contrarian candidates (pre-signals).
 *
 * Scans for stocks approaching signal conditions:
 * - RSI_OVERSOLD_WAITING: RSI <= 30, MACD histogram rising
 * - MACD_CROSSED_RSI_RECOVERING: MACD crossed, RSI recovering
 * - APPROACHING: Both indicators approaching thresholds
 *
 * @param maxResults - Maximum number of candidates to return (default: 20)
 * @param scanDate - Date to scan for candidates (YYYY-MM-DD format)
 */
export async function getContrarianCandidates(
  maxResults: number = 20,
  scanDate?: string
): Promise<ContrarianCandidatesResponse> {
  let url = `/contrarian/candidates?max_results=${maxResults}`;
  if (scanDate) {
    url += `&scan_date=${scanDate}`;
  }
  return api.get<ContrarianCandidatesResponse>(url);
}

// Watchlist API functions

export interface WatchlistItem {
  stock_code: string;
  stock_name: string;
  current_price: { close: number } | null;
  indicators: { rsi: number; macd: number } | null;
  recommendation_score: number | null;
  recommendation_reason: string | null;
  added_at: string;
}

export interface AddToWatchlistRequest {
  stock_code: string;
  stock_name: string;
}

/**
 * Get user's watchlist with insights.
 */
export async function getWatchlist(): Promise<WatchlistItem[]> {
  return api.get<WatchlistItem[]>('/watchlists');
}

/**
 * Add stock to watchlist.
 */
export async function addToWatchlist(request: AddToWatchlistRequest): Promise<{ status: string; watchlist_id: string }> {
  return api.post<{ status: string; watchlist_id: string }>('/watchlists', request);
}

/**
 * Remove stock from watchlist.
 */
export async function removeFromWatchlist(stockCode: string): Promise<{ status: string }> {
  return api.delete<{ status: string }>(`/watchlists/${stockCode}`);
}

export type { ApiError };
