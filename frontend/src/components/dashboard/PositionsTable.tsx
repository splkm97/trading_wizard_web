import { Card } from '../common';

interface Position {
  id: string;
  stock_code: string;
  stock_name: string;
  quantity: number;
  avg_entry_price: number;
  total_cost: number;
  first_entry_date: string;
  entry_reason?: string;
  confidence_score?: number;
  current_price?: number;
  current_value?: number;
  unrealized_pnl?: number;
  unrealized_pnl_pct?: number;
}

interface PositionsTableProps {
  positions: Position[];
  isLoading: boolean;
  includePrices: boolean;
}

export default function PositionsTable({
  positions,
  isLoading,
  includePrices,
}: PositionsTableProps) {
  const formatKRW = (value: number) => {
    return new Intl.NumberFormat('ko-KR', {
      maximumFractionDigits: 0,
    }).format(value);
  };

  const getPnLColor = (value: number | undefined) => {
    if (value === undefined) return '';
    return value > 0 ? 'text-red-600' : value < 0 ? 'text-blue-600' : '';
  };

  if (isLoading) {
    return (
      <Card title="보유 종목">
        <div className="animate-pulse space-y-3">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="h-8 bg-gray-200 rounded w-full" />
          ))}
        </div>
      </Card>
    );
  }

  if (positions.length === 0) {
    return (
      <Card title="보유 종목">
        <div className="text-center py-8 text-gray-500">
          보유 종목이 없습니다
        </div>
      </Card>
    );
  }

  return (
    <Card title="보유 종목">
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                종목
              </th>
              <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                수량
              </th>
              <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                평균단가
              </th>
              <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                매수금액
              </th>
              {includePrices && (
                <>
                  <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                    현재가
                  </th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                    손익
                  </th>
                </>
              )}
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {positions.map((pos) => (
              <tr key={pos.id} className="hover:bg-gray-50">
                <td className="px-4 py-3 whitespace-nowrap">
                  <div className="font-medium text-sm">{pos.stock_name}</div>
                  <div className="text-xs text-gray-500">{pos.stock_code}</div>
                </td>
                <td className="px-4 py-3 whitespace-nowrap text-sm text-right">
                  {pos.quantity.toLocaleString()}
                </td>
                <td className="px-4 py-3 whitespace-nowrap text-sm text-right">
                  ₩{formatKRW(pos.avg_entry_price)}
                </td>
                <td className="px-4 py-3 whitespace-nowrap text-sm text-right">
                  ₩{formatKRW(pos.total_cost)}
                </td>
                {includePrices && (
                  <>
                    <td className="px-4 py-3 whitespace-nowrap text-sm text-right">
                      {pos.current_price ? `₩${formatKRW(pos.current_price)}` : '-'}
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap text-sm text-right">
                      {pos.unrealized_pnl !== undefined ? (
                        <div className={getPnLColor(pos.unrealized_pnl)}>
                          <div>
                            {pos.unrealized_pnl > 0 ? '+' : ''}
                            ₩{formatKRW(pos.unrealized_pnl)}
                          </div>
                          <div className="text-xs">
                            ({pos.unrealized_pnl_pct !== undefined
                              ? (pos.unrealized_pnl_pct > 0 ? '+' : '') +
                                pos.unrealized_pnl_pct.toFixed(2)
                              : '0.00'}
                            %)
                          </div>
                        </div>
                      ) : (
                        '-'
                      )}
                    </td>
                  </>
                )}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Card>
  );
}
