import { Card } from '../common/Card';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';

interface BacktestPortfolioChartProps {
  dailyValues: Array<{ date: string; value: number }>;
  initialCapital: number;
}

export function BacktestPortfolioChart({
  dailyValues,
  initialCapital,
}: BacktestPortfolioChartProps) {
  const formatCurrency = (value: number) =>
    new Intl.NumberFormat('ko-KR', {
      style: 'currency',
      currency: 'KRW',
      maximumFractionDigits: 0,
    }).format(value);

  const formatDate = (date: string) => {
    const d = new Date(date);
    return `${d.getMonth() + 1}/${d.getDate()}`;
  };

  const chartData = dailyValues.map((d) => ({
    date: formatDate(d.date),
    fullDate: d.date,
    value: d.value,
    return: ((d.value - initialCapital) / initialCapital) * 100,
  }));

  return (
    <Card className="p-6">
      <h3 className="text-lg font-semibold mb-4">자산 변화</h3>
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="date" />
          <YAxis tickFormatter={formatCurrency} />
          <Tooltip
            labelFormatter={(label) => {
              const item = chartData.find((d) => d.date === label);
              return item?.fullDate || label;
            }}
            formatter={(value) => [formatCurrency(value as number), '자산']}
          />
          <Legend />
          <Line
            type="monotone"
            dataKey="value"
            stroke="#3b82f6"
            strokeWidth={2}
            dot={false}
          />
        </LineChart>
      </ResponsiveContainer>
    </Card>
  );
}
