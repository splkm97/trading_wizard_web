/**
 * Type definitions for Trading Wizard Web.
 */

// User and Authentication
export interface User {
  id: string;
  fingerprint: string;
  nickname: string | null;
  created_at: string;
  last_login_at: string | null;
}

export interface AuthChallenge {
  challenge: string;
  expires_at: string;
}

export interface AuthToken {
  access_token: string;
  token_type: string;
}

// Portfolio
export interface Portfolio {
  id: string;
  initial_capital: number;
  cash_balance: number;
  created_at: string;
  updated_at: string;
}

export interface PortfolioSummary extends Portfolio {
  total_value: number;
  unrealized_pnl: number;
  unrealized_pnl_pct: number;
  realized_pnl: number;
  total_trades: number;
  positions_count: number;
}

// Position
export interface Position {
  id: string;
  stock_code: string;
  stock_name: string;
  quantity: number;
  avg_entry_price: number;
  first_entry_date: string;
  entry_reason: string | null;
  confidence_score: number | null;
  current_price?: number;
  current_value?: number;
  unrealized_pnl?: number;
  unrealized_pnl_pct?: number;
}

// Trade
export type TradeAction = 'BUY' | 'SELL';

export interface Trade {
  id: string;
  trade_date: string;
  stock_code: string;
  stock_name: string;
  action: TradeAction;
  quantity: number;
  price: number;
  total_amount: number;
  realized_pnl: number | null;
  reason: string | null;
  created_at: string;
}

export interface TradeInput {
  trade_date: string;
  stock_code: string;
  action: TradeAction;
  quantity: number;
  price: number;
  reason?: string;
}

// Stock
export interface Stock {
  code: string;
  name: string;
}

// Backtest
export interface BacktestParams {
  start_date: string;
  end_date: string;
  stock_list: string;
  initial_capital: number;
  name?: string;
  // Optional strategy overrides (if not provided, uses user's saved settings)
  strategy_overrides?: Partial<UserSettings>;
}

export interface BacktestResult {
  id: string;
  name: string | null;
  start_date: string;
  end_date: string;
  stock_list_name: string;
  initial_capital: number;
  final_value: number;
  total_return_pct: number;
  max_drawdown_pct: number;
  total_trades: number;
  winning_trades: number;
  win_rate_pct: number;
  executed_at: string;
}

// Settings
export interface UserSettings {
  // Risk Management
  max_positions: number;
  max_position_pct: number;
  stop_loss_pct: number;
  confidence_threshold: number;

  // Take Profit Settings
  take_profit_enabled: boolean;
  take_profit_pct: number;
  take_profit_ratio: number;

  // Sell Conditions
  sell_on_middle_band: boolean;

  // Bollinger Band Parameters
  bollinger_period: number;
  bollinger_std_dev: number;

  // Squeeze Detection
  squeeze_threshold_pct: number;
  squeeze_lookback_days: number;

  // Advanced Squeeze Settings
  expansion_threshold_pct: number;
  band_touch_tolerance: number;

  // Metrics Configuration
  trading_days_per_year: number;
  days_per_year: number;

  // MACD/RSI Contrarian Strategy Settings
  macd_rsi_rsi_period: number;
  macd_rsi_rsi_threshold: number;
  macd_rsi_macd_fast_period: number;
  macd_rsi_macd_slow_period: number;
  macd_rsi_macd_signal_period: number;
  macd_rsi_confidence_threshold: number;
}

// Pagination
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

// API Response helpers
export interface ApiMessage {
  message: string;
}

export interface ConstitutionWarning {
  field: string;
  message: string;
  recommended_value: number;
}

// Contrarian Strategy Types
export interface ContrarianIndicators {
  rsi: number;
  macd: number;
  macd_signal: number;
  macd_histogram: number;
  reason_detail?: string;
}

export interface ContrarianSignal {
  stock_code: string;
  stock_name: string;
  signal_type: 'BUY';
  confidence_score: number;
  current_price: number;
  reason: string;
  indicators: ContrarianIndicators;
}

export interface AppliedContrarianSettings {
  rsi_period: number;
  rsi_threshold: number;
  macd_fast_period: number;
  macd_slow_period: number;
  macd_signal_period: number;
  confidence_threshold: number;
}

export interface ContrarianSignalsResponse {
  signals: ContrarianSignal[];
  scanned_count: number;
  signal_count: number;
  applied_settings: AppliedContrarianSettings;
  scan_date: string; // YYYY-MM-DD format
}

export interface SingleContrarianSignalResponse {
  signal: ContrarianSignal | null;
  applied_settings: AppliedContrarianSettings;
}

// Contrarian Candidate (Pre-Signal) Types
export type ContrarianCandidateStage =
  | 'RSI_OVERSOLD_WAITING'
  | 'MACD_CROSSED_RSI_RECOVERING'
  | 'APPROACHING';

export interface ContrarianCandidateIndicators {
  rsi: number;
  macd: number;
  macd_signal: number;
  macd_histogram: number;
  signal_stage: ContrarianCandidateStage;
  reason_detail: string;
}

export interface ContrarianCandidate {
  stock_code: string;
  stock_name: string;
  signal_type: 'CANDIDATE';
  signal_stage: ContrarianCandidateStage;
  confidence_score: number;
  current_price: number;
  reason: string;
  reason_detail: string;
  indicators: ContrarianCandidateIndicators;
}

export interface ContrarianCandidatesResponse {
  candidates: ContrarianCandidate[];
  scanned_count: number;
  candidate_count: number;
  applied_settings: AppliedContrarianSettings;
  scan_date: string;
}

// Applied Settings (from recommendations API)
export interface AppliedSettings {
  // Risk Management
  stop_loss_pct: number;
  max_positions: number;
  max_position_pct: number;
  confidence_threshold: number;

  // Take Profit
  take_profit_pct: number;
  take_profit_ratio: number;

  // Sell Conditions
  sell_on_middle_band: boolean;

  // Bollinger Band
  bollinger_period: number;
  bollinger_std_dev: number;

  // Squeeze Detection
  squeeze_threshold_pct: number;
  squeeze_lookback_days: number;
}
