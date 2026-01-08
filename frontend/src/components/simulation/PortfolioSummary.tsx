/**
 * Portfolio Summary - Display current portfolio status
 */

import { Card } from '../common/Card';
import type { GameSessionWithSummary } from '../../types/simulation';

interface PortfolioSummaryProps {
  session: GameSessionWithSummary | null;
  isLoading?: boolean;
}

export function PortfolioSummary({ session, isLoading = false }: PortfolioSummaryProps) {
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

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    return `${date.getFullYear()}.${String(date.getMonth() + 1).padStart(2, '0')}.${String(date.getDate()).padStart(2, '0')}`;
  };

  if (isLoading) {
    return (
      <Card className="h-full">
        <div className="p-4 border-b border-gray-100">
          <h3 className="font-semibold text-gray-900">포트폴리오</h3>
        </div>
        <div className="p-6 flex flex-col items-center justify-center h-48">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600" />
        </div>
      </Card>
    );
  }

  if (!session) {
    return null;
  }

  const progress = (() => {
    const start = new Date(session.start_date).getTime();
    const end = new Date(session.end_date).getTime();
    const current = new Date(session.current_date).getTime();
    return Math.min(100, Math.max(0, ((current - start) / (end - start)) * 100));
  })();

  return (
    <Card className="h-full">
      <div className="p-4 border-b border-gray-100">
        <div className="flex items-center justify-between">
          <h3 className="font-semibold text-gray-900">포트폴리오</h3>
          <span className={`text-xs px-2 py-1 rounded-full font-medium ${
            session.status === 'IN_PROGRESS' ? 'bg-green-100 text-green-700' :
            session.status === 'COMPLETED' ? 'bg-blue-100 text-blue-700' :
            'bg-gray-100 text-gray-700'
          }`}>
            {session.status === 'IN_PROGRESS' ? '진행중' :
             session.status === 'COMPLETED' ? '완료' : '중단'}
          </span>
        </div>
      </div>
      
      <div className="p-4 space-y-4">
        <div className="text-center py-2">
          <p className="text-sm text-gray-500 mb-1">현재 날짜</p>
          <p className="text-lg font-bold text-gray-900">{formatDate(session.current_date)}</p>
          <div className="mt-2">
            <div className="flex items-center justify-between text-xs text-gray-500 mb-1">
              <span>{formatDate(session.start_date)}</span>
              <span>{formatDate(session.end_date)}</span>
            </div>
            <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-primary-500 to-primary-600 rounded-full transition-all"
                style={{ width: `${progress}%` }}
              />
            </div>
            <p className="text-xs text-gray-500 mt-1">{progress.toFixed(0)}% 진행</p>
          </div>
        </div>

        <div className="border-t border-gray-100 pt-4">
          <div className="grid grid-cols-2 gap-3">
            <div className="text-center p-3 bg-gray-50 rounded-lg">
              <p className="text-xs text-gray-500 mb-1">총 평가액</p>
              <p className="text-lg font-bold text-gray-900">
                {formatCurrency(session.total_value)}
              </p>
            </div>
            <div className="text-center p-3 bg-gray-50 rounded-lg">
              <p className="text-xs text-gray-500 mb-1">총 수익률</p>
              <p className={`text-lg font-bold ${
                session.total_return_pct >= 0 ? 'text-green-600' : 'text-red-600'
              }`}>
                {formatPercent(session.total_return_pct)}
              </p>
            </div>
          </div>
        </div>

        <div className="space-y-2">
          <div className="flex justify-between text-sm">
            <span className="text-gray-500">현금</span>
            <span className="font-medium text-gray-900">{formatCurrency(session.cash_balance)}</span>
          </div>
          <div className="flex justify-between text-sm">
            <span className="text-gray-500">주식 평가액</span>
            <span className="font-medium text-gray-900">{formatCurrency(session.total_positions_value)}</span>
          </div>
          <div className="flex justify-between text-sm">
            <span className="text-gray-500">미실현 손익</span>
            <span className={`font-medium ${
              session.unrealized_pnl >= 0 ? 'text-green-600' : 'text-red-600'
            }`}>
              {formatCurrency(session.unrealized_pnl)}
            </span>
          </div>
          <div className="flex justify-between text-sm pt-2 border-t border-gray-100">
            <span className="text-gray-500">총 수익</span>
            <span className={`font-bold ${
              session.total_return >= 0 ? 'text-green-600' : 'text-red-600'
            }`}>
              {formatCurrency(session.total_return)}
            </span>
          </div>
        </div>

        {session.positions.length > 0 && (
          <div className="border-t border-gray-100 pt-4">
            <h4 className="text-sm font-medium text-gray-700 mb-2">
              보유 종목 ({session.positions.length})
            </h4>
            <div className="space-y-2 max-h-32 overflow-y-auto">
              {session.positions.map((pos) => (
                <div key={pos.id} className="flex items-center justify-between text-xs">
                  <div className="min-w-0 flex-1">
                    <p className="font-medium text-gray-900 truncate">{pos.stock_name}</p>
                    <p className="text-gray-500">{pos.quantity}주</p>
                  </div>
                  <span className={`font-medium ${
                    (pos.unrealized_pnl_pct ?? 0) >= 0 ? 'text-green-600' : 'text-red-600'
                  }`}>
                    {pos.unrealized_pnl_pct !== undefined ? formatPercent(pos.unrealized_pnl_pct) : '-'}
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
