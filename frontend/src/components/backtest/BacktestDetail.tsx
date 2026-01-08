import { Card } from '../common/Card';
import { Table } from '../common/Table';
import { BacktestPortfolioChart } from './BacktestPortfolioChart';
import { BacktestMonthlyHeatmap } from './BacktestMonthlyHeatmap';
import { BacktestStockRanking } from './BacktestStockRanking';
import { BacktestTradeHistory } from './BacktestTradeHistory';

interface BacktestDetailData {
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
    daily_values: Array<{
      date: string;
      value: number;
    }>;
  };
}

interface BacktestDetailProps {
  result: BacktestDetailData;
}

export function BacktestDetail({ result }: BacktestDetailProps) {
  const formatCurrency = (value: number) =>
    new Intl.NumberFormat('ko-KR', {
      style: 'currency',
      currency: 'KRW',
      maximumFractionDigits: 0,
    }).format(value);

  const metrics = result.result_json.backtest_metrics;
  const trades = result.result_json.trade_history;
  const positions = result.result_json.positions;
  const dailyValues = result.result_json.daily_values;

  const positionColumns = [
    { key: 'stock_code', header: '종목코드' },
    { key: 'stock_name', header: '종목명' },
    { key: 'quantity', header: '수량', className: 'text-right' },
    {
      key: 'entry_price',
      header: '매수가',
      className: 'text-right',
      render: (p: (typeof positions)[0]) => formatCurrency(p.entry_price),
    },
    { key: 'entry_date', header: '매수일' },
  ];

  return (
    <div className="space-y-6">
      {/* Summary Metrics */}
      <Card className="p-6">
        <h3 className="text-lg font-semibold mb-4">성과 요약</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <MetricItem
            label="총 수익률"
            value={`${result.total_return_pct >= 0 ? '+' : ''}${result.total_return_pct.toFixed(2)}%`}
            className={result.total_return_pct >= 0 ? 'text-green-600' : 'text-red-600'}
          />
          <MetricItem
            label="최대 낙폭"
            value={`-${result.max_drawdown_pct.toFixed(2)}%`}
            className="text-red-600"
          />
          <MetricItem
            label="승률"
            value={`${result.win_rate_pct.toFixed(1)}%`}
          />
          <MetricItem
            label="총 실현손익"
            value={formatCurrency(metrics.total_pnl || 0)}
            className={metrics.total_pnl >= 0 ? 'text-green-600' : 'text-red-600'}
          />
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-4 pt-4 border-t">
          <MetricItem label="총 거래" value={`${result.total_trades}건`} />
          <MetricItem label="매수" value={`${metrics.buy_trades}건`} />
          <MetricItem label="매도" value={`${metrics.sell_trades}건`} />
          <MetricItem
            label="승/패"
            value={`${result.winning_trades}승 ${metrics.losing_trades}패`}
          />
          <MetricItem
            label="평균 수익"
            value={formatCurrency(metrics.avg_win || 0)}
            className="text-green-600"
          />
          <MetricItem
            label="평균 손실"
            value={formatCurrency(metrics.avg_loss || 0)}
            className="text-red-600"
          />
        </div>
      </Card>

      {/* Portfolio Value Chart */}
      {dailyValues.length > 0 && (
        <BacktestPortfolioChart
          dailyValues={dailyValues}
          initialCapital={result.initial_capital}
        />
      )}

      {/* Monthly Heatmap */}
      {dailyValues.length > 0 && (
        <BacktestMonthlyHeatmap
          dailyValues={dailyValues}
          initialCapital={result.initial_capital}
        />
      )}

      {/* Stock Ranking */}
      <BacktestStockRanking trades={trades} />

      {/* Remaining Positions */}
      {positions.length > 0 && (
        <Card className="p-6">
          <h3 className="text-lg font-semibold mb-4">
            잔여 포지션 ({positions.length}개)
          </h3>
          <Table
            columns={positionColumns}
            data={positions}
            keyExtractor={(p, _i) => p.stock_code}
          />
        </Card>
      )}

      {/* Trade History with Pagination */}
      <BacktestTradeHistory trades={trades} />
    </div>
  );
}

function MetricItem({
  label,
  value,
  className = '',
}: {
  label: string;
  value: string;
  className?: string;
}) {
  return (
    <div>
      <p className="text-sm text-gray-500">{label}</p>
      <p className={`text-lg font-semibold ${className}`}>{value}</p>
    </div>
  );
}
