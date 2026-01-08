/**
 * Type definitions for Turn-Based Trading Simulation Game.
 */

// Game Status
export type GameStatus = 'IN_PROGRESS' | 'COMPLETED' | 'ABANDONED';

// Trade Action
export type SimulatedTradeAction = 'BUY' | 'SELL';

// Game Session
export interface GameSession {
  id: string;
  name: string | null;
  start_date: string;
  end_date: string;
  current_date: string;
  initial_capital: number;
  cash_balance: number;
  status: GameStatus;
  created_at: string;
  updated_at: string;
}

// Game Session with computed portfolio summary
export interface GameSessionWithSummary extends GameSession {
  positions: SimulatedPosition[];
  total_positions_value: number;
  total_value: number;
  total_return: number;
  total_return_pct: number;
  unrealized_pnl: number;
  is_game_over: boolean;
}

// Simulated Position
export interface SimulatedPosition {
  id: string;
  stock_code: string;
  stock_name: string;
  quantity: number;
  avg_entry_price: number;
  entry_date: string;
  // Computed fields (added by API)
  current_price?: number;
  current_value?: number;
  unrealized_pnl?: number;
  unrealized_pnl_pct?: number;
}

// Simulated Trade
export interface SimulatedTrade {
  id: string;
  trade_date: string;
  stock_code: string;
  stock_name: string;
  action: SimulatedTradeAction;
  quantity: number;
  price: number;
  total_amount: number;
  realized_pnl: number | null;
  realized_pnl_pct: number | null;
  confidence_score: number | null;
  created_at: string;
}

// Stock Recommendation (computed each turn)
export interface StockRecommendation {
  stock_code: string;
  stock_name: string;
  confidence_score: number;
  is_owned: boolean;
  // Indicator details
  bollinger_score: number;
  rsi_score: number;
  macd_score: number;
  volume_score: number;
}

// Stock Detail (for chart and indicators)
export interface StockDetail {
  stock_code: string;
  stock_name: string;
  current_price: number;
  confidence_score: number;
  is_owned: boolean;
  owned_quantity: number | null;
  avg_entry_price: number | null;
  unrealized_pnl: number | null;
  unrealized_pnl_pct: number | null;
  // Indicators
  indicators: {
    bollinger: {
      upper: number;
      middle: number;
      lower: number;
      bandwidth: number;
      score: number;
    };
    rsi: {
      value: number;
      score: number;
    };
    macd: {
      macd: number;
      signal: number;
      histogram: number;
      score: number;
    };
    volume: {
      current: number;
      average: number;
      ratio: number;
      score: number;
    };
  };
  // Price history for chart (last 60 days from current_date)
  price_history: {
    date: string;
    open: number;
    high: number;
    low: number;
    close: number;
    volume: number;
  }[];
}

// Backtest Report (real-time during game)
export interface GameReport {
  session_id: string;
  start_date: string;
  end_date: string;
  current_date: string;
  initial_capital: number;
  current_value: number;
  total_return_pct: number;
  max_drawdown_pct: number;
  total_trades: number;
  winning_trades: number;
  win_rate_pct: number;
  profit_factor: number | null;
  // Equity curve for chart
  equity_curve: {
    date: string;
    value: number;
  }[];
  // Stock contributions
  stock_contributions: {
    stock_code: string;
    stock_name: string;
    total_trades: number;
    realized_pnl: number;
    contribution_pct: number;
  }[];
}

// API Request/Response Types

export interface CreateSessionRequest {
  name?: string;
  start_date: string;
  end_date: string;
  initial_capital?: number;
}

export interface ExecuteTradeRequest {
  stock_code: string;
  action: SimulatedTradeAction;
  quantity?: number;  // Required for BUY, optional for SELL (full position)
  amount?: number;    // Alternative to quantity for BUY (calculate quantity from amount)
}

export interface ExecuteTradeResponse {
  trade: SimulatedTrade;
  session: GameSessionWithSummary;
}

export interface AdvanceTurnResponse {
  session: GameSessionWithSummary;
  recommendations: StockRecommendation[];
  is_game_over: boolean;
}

export interface ExportTradesResponse {
  start_date: string;
  end_date: string;
  initial_capital: number;
  final_value: number;
  total_return_pct: number;
  max_drawdown_pct: number;
  total_trades: number;
  winning_trades: number;
  win_rate_pct: number;
  trades: {
    date: string;
    stock_code: string;
    stock_name: string;
    action: SimulatedTradeAction;
    price: number;
    quantity: number;
    pnl: number | null;
    pnl_pct: number | null;
  }[];
  daily_values: [string, number][];
}
