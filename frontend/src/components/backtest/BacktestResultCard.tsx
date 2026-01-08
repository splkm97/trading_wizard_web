import { Card } from '../common/Card';

interface BacktestResultSummary {
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

interface BacktestResultCardProps {
  result: BacktestResultSummary;
  onClick?: () => void;
  isSelected?: boolean;
}

export function BacktestResultCard({
  result,
  onClick,
  isSelected = false,
}: BacktestResultCardProps) {
  const formatCurrency = (value: number) =>
    new Intl.NumberFormat('ko-KR', {
      style: 'currency',
      currency: 'KRW',
      maximumFractionDigits: 0,
    }).format(value);

  const formatPercent = (value: number) => {
    const sign = value >= 0 ? '+' : '';
    return `${sign}${value.toFixed(2)}%`;
  };

  const returnColor =
    result.total_return_pct >= 0 ? 'text-green-600' : 'text-red-600';

  return (
    <Card
      className={`p-4 cursor-pointer transition-all hover:shadow-md ${
        isSelected ? 'ring-2 ring-primary-500' : ''
      }`}
      onClick={onClick}
    >
      <div className="flex justify-between items-start mb-3">
        <div>
          <h3 className="font-medium text-gray-900">
            {result.name || '이름 없음'}
          </h3>
          <p className="text-sm text-gray-500">
            {result.start_date} ~ {result.end_date}
          </p>
        </div>
        <span className={`text-lg font-bold ${returnColor}`}>
          {formatPercent(result.total_return_pct)}
        </span>
      </div>

      <div className="grid grid-cols-2 gap-3 text-sm">
        <div>
          <span className="text-gray-500">초기자본</span>
          <p className="font-medium">{formatCurrency(result.initial_capital)}</p>
        </div>
        <div>
          <span className="text-gray-500">최종평가</span>
          <p className="font-medium">{formatCurrency(result.final_value)}</p>
        </div>
        <div>
          <span className="text-gray-500">최대낙폭</span>
          <p className="font-medium text-red-600">
            -{result.max_drawdown_pct.toFixed(2)}%
          </p>
        </div>
        <div>
          <span className="text-gray-500">승률</span>
          <p className="font-medium">{result.win_rate_pct.toFixed(1)}%</p>
        </div>
        <div>
          <span className="text-gray-500">총 거래</span>
          <p className="font-medium">{result.total_trades}건</p>
        </div>
        <div>
          <span className="text-gray-500">승리 거래</span>
          <p className="font-medium">{result.winning_trades}건</p>
        </div>
      </div>

      <div className="mt-3 pt-3 border-t border-gray-100 text-xs text-gray-400">
        {result.stock_list_name} | {new Date(result.created_at).toLocaleString('ko-KR')}
      </div>
    </Card>
  );
}
