import { Card } from '../common';

interface PortfolioSummary {
  initial_capital: number;
  cash_balance: number;
  total_invested: number;
  total_value: number;
  return_pct: number;
  position_count: number;
  total_unrealized_pnl?: number;
}

interface PortfolioSummaryCardProps {
  summary: PortfolioSummary | null;
  isLoading: boolean;
}

export default function PortfolioSummaryCard({
  summary,
  isLoading,
}: PortfolioSummaryCardProps) {
  if (isLoading) {
    return (
      <Card title="포트폴리오 요약">
        <div className="animate-pulse space-y-3">
          {[...Array(5)].map((_, i) => (
            <div key={i} className="h-4 bg-gray-200 rounded w-full" />
          ))}
        </div>
      </Card>
    );
  }

  if (!summary) {
    return (
      <Card title="포트폴리오 요약">
        <div className="text-center py-4 text-gray-500">
          데이터를 불러올 수 없습니다
        </div>
      </Card>
    );
  }

  const formatKRW = (value: number) => {
    return new Intl.NumberFormat('ko-KR', {
      style: 'currency',
      currency: 'KRW',
      maximumFractionDigits: 0,
    }).format(value);
  };

  const returnColor =
    summary.return_pct > 0
      ? 'text-red-600'
      : summary.return_pct < 0
      ? 'text-blue-600'
      : 'text-gray-600';

  return (
    <Card title="포트폴리오 요약">
      <div className="space-y-4">
        <div className="flex justify-between items-center">
          <span className="text-gray-600">초기자본</span>
          <span className="font-medium">{formatKRW(summary.initial_capital)}</span>
        </div>

        <div className="flex justify-between items-center">
          <span className="text-gray-600">총 평가액</span>
          <span className="font-semibold text-lg">{formatKRW(summary.total_value)}</span>
        </div>

        <div className="flex justify-between items-center">
          <span className="text-gray-600">현금잔고</span>
          <span className="font-medium">{formatKRW(summary.cash_balance)}</span>
        </div>

        <div className="flex justify-between items-center">
          <span className="text-gray-600">투자금액</span>
          <span className="font-medium">{formatKRW(summary.total_invested)}</span>
        </div>

        <div className="border-t pt-3">
          <div className="flex justify-between items-center">
            <span className="text-gray-600">수익률</span>
            <span className={`font-semibold text-lg ${returnColor}`}>
              {summary.return_pct > 0 ? '+' : ''}
              {summary.return_pct.toFixed(2)}%
            </span>
          </div>

          {summary.total_unrealized_pnl !== undefined && (
            <div className="flex justify-between items-center mt-2">
              <span className="text-gray-600">미실현손익</span>
              <span
                className={`font-medium ${
                  summary.total_unrealized_pnl > 0
                    ? 'text-red-600'
                    : summary.total_unrealized_pnl < 0
                    ? 'text-blue-600'
                    : 'text-gray-600'
                }`}
              >
                {summary.total_unrealized_pnl > 0 ? '+' : ''}
                {formatKRW(summary.total_unrealized_pnl)}
              </span>
            </div>
          )}
        </div>

        <div className="text-sm text-gray-500 text-center pt-2">
          보유종목: {summary.position_count}개
        </div>
      </div>
    </Card>
  );
}
