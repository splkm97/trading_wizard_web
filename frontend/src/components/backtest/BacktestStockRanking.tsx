import { Card } from '../common/Card';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';

interface BacktestStockRankingProps {
  trades: Array<{
    stock_code: string;
    stock_name: string;
    pnl: number | null;
  }>;
}

export function BacktestStockRanking({ trades }: BacktestStockRankingProps) {
  const stockPnL = new Map<string, { name: string; total: number; count: number }>();

  trades
    .filter((t) => t.pnl !== null)
    .forEach((t) => {
      const key = `${t.stock_code}:${t.stock_name}`;
      if (!stockPnL.has(key)) {
        stockPnL.set(key, { name: t.stock_name, total: 0, count: 0 });
      }
      const data = stockPnL.get(key)!;
      data.total += t.pnl!;
      data.count += 1;
    });

  const sorted = Array.from(stockPnL.entries())
    .map(([_, v]) => v)
    .sort((a, b) => b.total - a.total);

  const top10 = sorted.slice(0, 10);
  const bottom10 = sorted.slice(-10).reverse();

  const formatCurrency = (value: number) =>
    new Intl.NumberFormat('ko-KR', {
      style: 'currency',
      currency: 'KRW',
      maximumFractionDigits: 0,
    }).format(value);

  return (
    <div className="space-y-6">
      {top10.length > 0 && (
        <Card className="p-6">
          <h3 className="text-lg font-semibold mb-4">상위 수익 종목 (Top 10)</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={top10} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis type="number" tickFormatter={formatCurrency} />
              <YAxis dataKey="name" type="category" width={80} />
              <Tooltip formatter={(value) => [formatCurrency(value as number), '수익']} />
              <Bar dataKey="total" fill="#22c55e" />
            </BarChart>
          </ResponsiveContainer>
        </Card>
      )}

      {bottom10.length > 0 && (
        <Card className="p-6">
          <h3 className="text-lg font-semibold mb-4">하위 손실 종목 (Bottom 10)</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={bottom10} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis type="number" tickFormatter={formatCurrency} />
              <YAxis dataKey="name" type="category" width={80} />
              <Tooltip formatter={(value) => [formatCurrency(value as number), '손실']} />
              <Bar dataKey="total" fill="#ef4444" />
            </BarChart>
          </ResponsiveContainer>
        </Card>
      )}
    </div>
  );
}
