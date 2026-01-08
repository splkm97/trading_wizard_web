import { useState } from 'react';
import { Card } from '../common/Card';
import { Table } from '../common/Table';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
  Cell,
} from 'recharts';

interface BacktestTradeHistoryProps {
  trades: Array<{
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
}

function categorizeSellReason(reason: string): string {
  const lowerReason = reason.toLowerCase();

  if (lowerReason.includes('stop_loss') || lowerReason.includes('stop-loss')) {
    return '손절매';
  }
  if (lowerReason.includes('take_profit') || lowerReason.includes('take-profit')) {
    return '익절';
  }
  if (lowerReason.includes('trend')) {
    return '추세 반전';
  }
  if (lowerReason.includes('band') || lowerReason.includes('squeeze')) {
    return '밴드 탈락';
  }
  if (lowerReason.includes('target')) {
    return '목표가 도달';
  }
  if (lowerReason.includes('wizard') || lowerReason.includes('signal')) {
    return '시그널';
  }

  return '기타';
}

export function BacktestTradeHistory({ trades }: BacktestTradeHistoryProps) {
  const [page, setPage] = useState(1);
  const pageSize = 20;

  const totalPages = Math.ceil(trades.length / pageSize);
  const paginatedTrades = trades.slice((page - 1) * pageSize, page * pageSize);

  const formatCurrency = (value: number) =>
    new Intl.NumberFormat('ko-KR', {
      style: 'currency',
      currency: 'KRW',
      maximumFractionDigits: 0,
    }).format(value);

  const tradeColumns = [
    { key: 'date', header: '날짜' },
    {
      key: 'stock_code',
      header: '종목',
      render: (t: (typeof paginatedTrades)[0]) => (
        <div>
          <span className="font-mono text-sm">{t.stock_code}</span>
          <br />
          <span className="text-xs text-gray-500">{t.stock_name}</span>
        </div>
      ),
    },
    {
      key: 'action',
      header: '유형',
      render: (t: (typeof paginatedTrades)[0]) => (
        <span
          className={`px-2 py-1 rounded text-xs font-medium ${
            t.action === 'BUY'
              ? 'bg-red-100 text-red-800'
              : 'bg-blue-100 text-blue-800'
          }`}
        >
          {t.action === 'BUY' ? '매수' : '매도'}
        </span>
      ),
    },
    {
      key: 'price',
      header: '가격',
      className: 'text-right',
      render: (t: (typeof paginatedTrades)[0]) => formatCurrency(t.price),
    },
    { key: 'quantity', header: '수량', className: 'text-right' },
    {
      key: 'pnl',
      header: '손익',
      className: 'text-right',
      render: (t: (typeof paginatedTrades)[0]) => {
        if (t.pnl === null) return '-';
        const color = t.pnl >= 0 ? 'text-green-600' : 'text-red-600';
        const sign = t.pnl >= 0 ? '+' : '';
        return <span className={color}>{sign}{formatCurrency(t.pnl)}</span>;
      },
    },
    {
      key: 'reason',
      header: '사유',
      render: (t: (typeof paginatedTrades)[0]) => (
        <span className="text-xs text-gray-500">{t.reason}</span>
      ),
    },
  ];

  const reasonAnalysis = new Map<string, { count: number; totalPnL: number }>();
  trades
    .filter((t) => t.action === 'SELL' && t.pnl !== null)
    .forEach((t) => {
      const category = categorizeSellReason(t.reason);
      if (!reasonAnalysis.has(category)) {
        reasonAnalysis.set(category, { count: 0, totalPnL: 0 });
      }
      const data = reasonAnalysis.get(category)!;
      data.count += 1;
      data.totalPnL += t.pnl!;
    });

  const reasonData = Array.from(reasonAnalysis.entries())
    .map(([category, data]) => ({
      category,
      count: data.count,
      avgPnL: data.totalPnL / data.count,
    }))
    .sort((a, b) => b.count - a.count);

  const PnLTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length > 0) {
      const data = payload[0].payload;
      return (
        <div className="bg-white p-3 rounded shadow border">
          <p className="font-medium mb-1">{data.category}</p>
          <p className="text-sm">평균 손익: {formatCurrency(data.avgPnL)}</p>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="space-y-6">
      <Card className="p-6">
        <h3 className="text-lg font-semibold mb-4">
          거래 내역 (총 {trades.length}건)
        </h3>
        <Table
          columns={tradeColumns}
          data={paginatedTrades}
          keyExtractor={(t, i) => `${t.date}-${t.stock_code}-${i}`}
          emptyMessage="거래 내역이 없습니다."
        />
        {totalPages > 1 && (
          <div className="mt-4 flex justify-center gap-2">
            <button
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page === 1}
              className="px-4 py-2 bg-gray-100 hover:bg-gray-200 disabled:opacity-50 rounded"
            >
              이전
            </button>
            <span className="px-4 py-2">
              {page} / {totalPages}
            </span>
            <button
              onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
              disabled={page === totalPages}
              className="px-4 py-2 bg-gray-100 hover:bg-gray-200 disabled:opacity-50 rounded"
            >
              다음
            </button>
          </div>
        )}
      </Card>

      {reasonData.length > 0 && (
        <Card className="p-6">
          <h3 className="text-lg font-semibold mb-4">매도 사유 분석</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <h4 className="text-sm font-medium text-gray-600 mb-2">사유별 횟수</h4>
              <ResponsiveContainer width="100%" height={200}>
                <BarChart data={reasonData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="category" fontSize={12} />
                  <YAxis />
                  <Tooltip formatter={(value) => [`${value}건`, '횟수']} />
                  <Bar dataKey="count" fill="#3b82f6" />
                </BarChart>
              </ResponsiveContainer>
            </div>
            <div>
              <h4 className="text-sm font-medium text-gray-600 mb-2">사유별 평균 손익</h4>
              <ResponsiveContainer width="100%" height={200}>
                <BarChart data={reasonData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="category" fontSize={12} />
                  <YAxis tickFormatter={(v) => `${(v / 10000).toFixed(0)}만`} />
                  <Tooltip content={<PnLTooltip />} />
                  <ReferenceLine y={0} stroke="#000" />
                  <Bar dataKey="avgPnL">
                    {reasonData.map((entry, index) => (
                      <Cell
                        key={`cell-${index}`}
                        fill={entry.avgPnL >= 0 ? '#22c55e' : '#ef4444'}
                      />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </Card>
      )}
    </div>
  );
}
