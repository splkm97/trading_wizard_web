import { Card } from '../common/Card';

interface BacktestMonthlyHeatmapProps {
  dailyValues: Array<{ date: string; value: number }>;
  initialCapital: number;
}

interface MonthData {
  startValue: number;
  endValue: number;
  startDate: string;
  endDate: string;
}

export function BacktestMonthlyHeatmap({
  dailyValues,
}: BacktestMonthlyHeatmapProps) {
  const monthlyData = new Map<string, MonthData>();

  const sortedValues = [...dailyValues].sort((a, b) => a.date.localeCompare(b.date));

  sortedValues.forEach((d) => {
    const date = new Date(d.date);
    const yearMonth = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`;

    if (!monthlyData.has(yearMonth)) {
      monthlyData.set(yearMonth, { 
        startValue: d.value, 
        endValue: d.value,
        startDate: d.date,
        endDate: d.date
      });
    } else {
      const data = monthlyData.get(yearMonth)!;
      if (d.date < data.startDate) {
        data.startValue = d.value;
        data.startDate = d.date;
      }
      if (d.date > data.endDate) {
        data.endValue = d.value;
        data.endDate = d.date;
      }
    }
  });

  const years = Array.from(new Set(
    Array.from(monthlyData.keys()).map((k) => k.split('-')[0]),
  )).sort();

  const months = ['1월', '2월', '3월', '4월', '5월', '6월', '7월', '8월', '9월', '10월', '11월', '12월'];

  const getColor = (value: number) => {
    if (value >= 10) return 'bg-green-700 text-white';
    if (value >= 5) return 'bg-green-500 text-white';
    if (value >= 2) return 'bg-green-300 text-green-900';
    if (value >= 0) return 'bg-green-100 text-green-800';
    if (value >= -2) return 'bg-red-100 text-red-800';
    if (value >= -5) return 'bg-red-300 text-red-900';
    if (value >= -10) return 'bg-red-500 text-white';
    return 'bg-red-700 text-white';
  };

  const calculateMonthlyReturn = (data: MonthData): number => {
    if (data.startValue === 0) return 0;
    return ((data.endValue - data.startValue) / data.startValue) * 100;
  };

  return (
    <Card className="p-6">
      <h3 className="text-lg font-semibold mb-4">월별 수익률 히트맵</h3>
      <div className="overflow-x-auto">
        <table className="w-full text-xs">
          <thead>
            <tr>
              <th className="p-2 text-left">연도</th>
              {months.map((m) => (
                <th key={m} className="p-2 text-center">
                  {m}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {years.map((year) => (
              <tr key={year}>
                <td className="p-2 font-medium">{year}</td>
                {months.map((_, monthIndex) => {
                  const monthNum = monthIndex + 1;
                  const monthKey = `${year}-${String(monthNum).padStart(2, '0')}`;
                  const data = monthlyData.get(monthKey);

                  if (!data) {
                    return <td key={monthIndex} className="p-2 bg-gray-50" />;
                  }

                  const returnPct = calculateMonthlyReturn(data);
                  const colorClass = getColor(returnPct);

                  return (
                    <td
                      key={monthIndex}
                      className={`p-2 text-center ${colorClass}`}
                      title={`${year}년 ${monthNum}월: ${returnPct >= 0 ? '+' : ''}${returnPct.toFixed(2)}%`}
                    >
                      {returnPct >= 0 ? '+' : ''}
                      {returnPct.toFixed(1)}%
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Card>
  );
}
