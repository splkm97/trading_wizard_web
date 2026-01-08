import { Card } from '../common';

interface Position {
  unrealized_pnl?: number;
  unrealized_pnl_pct?: number;
  stock_code: string;
  stock_name: string;
}

interface PnLSummaryProps {
  positions: Position[];
  totalUnrealizedPnl?: number;
  isLoading: boolean;
}

export default function PnLSummary({
  positions,
  totalUnrealizedPnl,
  isLoading,
}: PnLSummaryProps) {
  if (isLoading) {
    return (
      <Card title="손익 현황">
        <div className="animate-pulse space-y-3">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="h-4 bg-gray-200 rounded w-full" />
          ))}
        </div>
      </Card>
    );
  }

  // Filter positions with P&L data
  const positionsWithPnl = positions.filter(
    (p) => p.unrealized_pnl !== undefined
  );

  if (positionsWithPnl.length === 0) {
    return (
      <Card title="손익 현황">
        <div className="text-center py-4 text-gray-500">
          현재가 정보가 없습니다
        </div>
      </Card>
    );
  }

  const formatKRW = (value: number) => {
    return new Intl.NumberFormat('ko-KR', {
      maximumFractionDigits: 0,
    }).format(Math.abs(value));
  };

  const getPnLColor = (value: number) => {
    return value > 0 ? 'text-red-600' : value < 0 ? 'text-blue-600' : 'text-gray-600';
  };

  // Sort by P&L percentage (descending for gains)
  const sortedPositions = [...positionsWithPnl].sort((a, b) => {
    const pnlA = a.unrealized_pnl_pct || 0;
    const pnlB = b.unrealized_pnl_pct || 0;
    return pnlB - pnlA;
  });

  // Top gainers and losers
  const gainers = sortedPositions.filter((p) => (p.unrealized_pnl || 0) > 0);
  const losers = sortedPositions.filter((p) => (p.unrealized_pnl || 0) < 0).reverse();

  return (
    <Card title="손익 현황">
      <div className="space-y-4">
        {/* Total */}
        {totalUnrealizedPnl !== undefined && (
          <div className="text-center pb-3 border-b">
            <div className="text-sm text-gray-500">총 미실현손익</div>
            <div className={`text-2xl font-bold ${getPnLColor(totalUnrealizedPnl)}`}>
              {totalUnrealizedPnl > 0 ? '+' : totalUnrealizedPnl < 0 ? '-' : ''}
              ₩{formatKRW(totalUnrealizedPnl)}
            </div>
          </div>
        )}

        {/* Top Gainers */}
        {gainers.length > 0 && (
          <div>
            <h4 className="text-sm font-medium text-gray-700 mb-2">📈 수익 종목</h4>
            <div className="space-y-2">
              {gainers.slice(0, 3).map((pos) => (
                <div key={pos.stock_code} className="flex justify-between items-center text-sm">
                  <span className="text-gray-700">{pos.stock_name}</span>
                  <span className="text-red-600 font-medium">
                    +{(pos.unrealized_pnl_pct || 0).toFixed(2)}%
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Top Losers */}
        {losers.length > 0 && (
          <div>
            <h4 className="text-sm font-medium text-gray-700 mb-2">📉 손실 종목</h4>
            <div className="space-y-2">
              {losers.slice(0, 3).map((pos) => (
                <div key={pos.stock_code} className="flex justify-between items-center text-sm">
                  <span className="text-gray-700">{pos.stock_name}</span>
                  <span className="text-blue-600 font-medium">
                    {(pos.unrealized_pnl_pct || 0).toFixed(2)}%
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </Card>
  );
}
