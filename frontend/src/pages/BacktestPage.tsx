import { useState, useEffect } from 'react';
import { BacktestForm } from '../components/backtest/BacktestForm';
import { BacktestResultCard } from '../components/backtest/BacktestResultCard';
import { BacktestDetail } from '../components/backtest/BacktestDetail';
import { api } from '../services/api';

interface BacktestResult {
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
  created_at: string;
}

interface BacktestDetailResult extends BacktestResult {
  result_json: {
    backtest_metrics: {
      buy_trades: number;
      sell_trades: number;
      losing_trades: number;
      total_pnl: number;
      avg_win: number;
      avg_loss: number;
    };
    positions: Array<{
      stock_code: string;
      stock_name: string;
      quantity: number;
      entry_price: number;
      entry_date: string;
    }>;
    trade_history: Array<{
      date: string;
      stock_code: string;
      stock_name: string;
      action: string;
      price: number;
      quantity: number;
      reason: string;
      pnl: number | null;
      pnl_pct: number | null;
    }>;
    daily_values: Array<{ date: string; value: number }>;
  };
}

export function BacktestPage() {
  const [results, setResults] = useState<BacktestResult[]>([]);
  const [selectedResult, setSelectedResult] = useState<BacktestDetailResult | null>(null);
  const [isRunning, setIsRunning] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchResults();
  }, []);

  const fetchResults = async () => {
    try {
      const response = await api.get<{ results: BacktestResult[]; total: number }>(
        '/backtest/results'
      );
      setResults(response.results);
    } catch (err) {
      console.error('Failed to fetch results:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleRunBacktest = async (params: {
    start_date: string;
    end_date: string;
    stock_list: string;
    initial_capital: number;
    name?: string;
  }) => {
    setIsRunning(true);
    setError(null);

    try {
      const result = await api.post<BacktestResult>('/backtest/run', params);
      setResults((prev) => [result, ...prev]);

      // Load full details
      const detail = await api.get<BacktestDetailResult>(`/backtest/${result.id}`);
      setSelectedResult(detail);
    } catch (err: unknown) {
      const message = err && typeof err === 'object' && 'detail' in err
        ? (err as { detail: string }).detail
        : '백테스트 실행에 실패했습니다.';
      setError(message);
    } finally {
      setIsRunning(false);
    }
  };

  const handleSelectResult = async (result: BacktestResult) => {
    try {
      const detail = await api.get<BacktestDetailResult>(`/backtest/${result.id}`);
      setSelectedResult(detail);
    } catch (err) {
      console.error('Failed to fetch result detail:', err);
    }
  };

  return (
    <div className="container mx-auto px-4 py-6">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">백테스트</h1>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-6">
          {error}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left: Form and Results List */}
        <div className="space-y-6">
          <BacktestForm onSubmit={handleRunBacktest} isLoading={isRunning} />

          <div>
            <h2 className="text-lg font-semibold text-gray-900 mb-4">
              이전 결과
            </h2>
            {isLoading ? (
              <div className="flex justify-center py-8">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600" />
              </div>
            ) : results.length === 0 ? (
              <p className="text-gray-500 text-center py-4">
                아직 실행된 백테스트가 없습니다.
              </p>
            ) : (
              <div className="space-y-3 max-h-[600px] overflow-y-auto">
                {results.map((result) => (
                  <BacktestResultCard
                    key={result.id}
                    result={result}
                    onClick={() => handleSelectResult(result)}
                    isSelected={selectedResult?.id === result.id}
                  />
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Right: Detail View */}
        <div className="lg:col-span-2">
          {selectedResult ? (
            <BacktestDetail result={selectedResult} />
          ) : (
            <div className="bg-gray-50 rounded-lg p-12 text-center text-gray-500">
              <p className="text-lg mb-2">결과를 선택하세요</p>
              <p className="text-sm">
                왼쪽에서 백테스트를 실행하거나 이전 결과를 선택하면
                상세 내용을 확인할 수 있습니다.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
