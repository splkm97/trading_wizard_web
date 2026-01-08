/**
 * GameReportModal - Shows backtest-style report for simulation game
 * 
 * Displays:
 * - Summary metrics (return, MDD, win rate, etc.)
 * - Equity curve chart
 * - Stock contributions
 * - Export button for JSON download
 */

import { useState, useEffect } from 'react';
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
import { Card } from '../common/Card';
import { Button } from '../common/Button';
import { getReport, downloadTradesJson } from '../../services/simulation';
import type { GameReport } from '../../types/simulation';

interface GameReportModalProps {
  isOpen: boolean;
  onClose: () => void;
  sessionId: string;
  sessionName?: string | null;
  isGameCompleted?: boolean;
}

export function GameReportModal({
  isOpen,
  onClose,
  sessionId,
  sessionName,
  isGameCompleted = false,
}: GameReportModalProps) {
  const [report, setReport] = useState<GameReport | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isExporting, setIsExporting] = useState(false);

  useEffect(() => {
    if (isOpen && sessionId) {
      loadReport();
    }
  }, [isOpen, sessionId]);

  const loadReport = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await getReport(sessionId);
      setReport(data);
    } catch (err) {
      console.error('Failed to load report:', err);
      setError('리포트를 불러오는데 실패했습니다.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleExport = async () => {
    setIsExporting(true);
    try {
      const filename = `simulation_${sessionName || sessionId}_${new Date().toISOString().split('T')[0]}.json`;
      await downloadTradesJson(sessionId, filename);
    } catch (err) {
      console.error('Failed to export trades:', err);
    } finally {
      setIsExporting(false);
    }
  };

  if (!isOpen) return null;

  const formatCurrency = (value: number) =>
    new Intl.NumberFormat('ko-KR', {
      style: 'currency',
      currency: 'KRW',
      maximumFractionDigits: 0,
    }).format(value);

  const formatPercent = (value: number | null | undefined, showSign = true) => {
    if (value === null || value === undefined) return '-';
    const sign = showSign && value >= 0 ? '+' : '';
    return `${sign}${value.toFixed(2)}%`;
  };

  const formatDate = (date: string) => {
    const d = new Date(date);
    return `${d.getMonth() + 1}/${d.getDate()}`;
  };

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="fixed inset-0 bg-black/50 transition-opacity" onClick={onClose} />
      
      <div className="flex min-h-full items-center justify-center p-4">
        <div className="relative w-full max-w-4xl bg-white rounded-xl shadow-2xl transform transition-all">
          {/* Header */}
          <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200">
            <div>
              <h2 className="text-xl font-bold text-gray-900">
                {isGameCompleted ? '최종 리포트' : '중간 리포트'}
              </h2>
              <p className="text-sm text-gray-500">
                {sessionName || '트레이딩 시뮬레이션'}
              </p>
            </div>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 transition-colors"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          {/* Content */}
          <div className="px-6 py-6 max-h-[70vh] overflow-y-auto">
            {isLoading && (
              <div className="flex items-center justify-center py-12">
                <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-primary-600" />
              </div>
            )}

            {error && (
              <div className="text-center py-12">
                <p className="text-red-600">{error}</p>
                <Button variant="secondary" size="sm" onClick={loadReport} className="mt-4">
                  다시 시도
                </Button>
              </div>
            )}

            {report && !isLoading && (
              <div className="space-y-6">
                {/* Summary Metrics */}
                <Card className="p-6">
                  <h3 className="text-lg font-semibold mb-4">성과 요약</h3>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <MetricItem
                      label="기간"
                      value={`${report.start_date} ~ ${report.current_date}`}
                    />
                    <MetricItem
                      label="초기자본"
                      value={formatCurrency(report.initial_capital)}
                    />
                    <MetricItem
                      label="현재평가"
                      value={formatCurrency(report.current_value)}
                    />
                    <MetricItem
                      label="총 수익률"
                      value={formatPercent(report.total_return_pct)}
                      valueColor={report.total_return_pct >= 0 ? 'text-green-600' : 'text-red-600'}
                    />
                    <MetricItem
                      label="최대낙폭(MDD)"
                      value={`-${report.max_drawdown_pct.toFixed(2)}%`}
                      valueColor="text-red-600"
                    />
                    <MetricItem
                      label="승률"
                      value={`${report.win_rate_pct.toFixed(1)}%`}
                    />
                    <MetricItem
                      label="총 거래"
                      value={`${report.total_trades}건`}
                    />
                    <MetricItem
                      label="Profit Factor"
                      value={report.profit_factor ? report.profit_factor.toFixed(2) : '-'}
                    />
                  </div>
                </Card>

                {/* Equity Curve */}
                {report.equity_curve.length > 1 && (
                  <Card className="p-6">
                    <h3 className="text-lg font-semibold mb-4">자산 변화</h3>
                    <ResponsiveContainer width="100%" height={300}>
                      <LineChart
                        data={report.equity_curve.map((d) => ({
                          date: formatDate(d.date),
                          fullDate: d.date,
                          value: d.value,
                          return: ((d.value - report.initial_capital) / report.initial_capital) * 100,
                        }))}
                      >
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="date" />
                        <YAxis tickFormatter={formatCurrency} />
                        <Tooltip
                          labelFormatter={(_, payload) => {
                            if (payload && payload[0]) {
                              return payload[0].payload.fullDate;
                            }
                            return '';
                          }}
                          formatter={(value) => [formatCurrency(value as number), '자산']}
                        />
                        <Legend />
                        <Line
                          type="monotone"
                          dataKey="value"
                          name="포트폴리오"
                          stroke="#3b82f6"
                          strokeWidth={2}
                          dot={false}
                        />
                      </LineChart>
                    </ResponsiveContainer>
                  </Card>
                )}

                {/* Stock Contributions */}
                {report.stock_contributions.length > 0 && (
                  <Card className="p-6">
                    <h3 className="text-lg font-semibold mb-4">종목별 기여도</h3>
                    <div className="space-y-3">
                      {report.stock_contributions.slice(0, 10).map((stock) => (
                        <div
                          key={stock.stock_code}
                          className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
                        >
                          <div className="flex items-center gap-3">
                            <span className="font-mono text-sm text-gray-500">
                              {stock.stock_code}
                            </span>
                            <span className="font-medium">{stock.stock_name}</span>
                            <span className="text-sm text-gray-500">
                              ({stock.total_trades}건)
                            </span>
                          </div>
                          <div className="flex items-center gap-4">
                            <span
                              className={`font-medium ${
                                stock.realized_pnl >= 0 ? 'text-green-600' : 'text-red-600'
                              }`}
                            >
                              {formatCurrency(stock.realized_pnl)}
                            </span>
                            <span className="text-sm text-gray-500 w-16 text-right">
                              {stock.contribution_pct.toFixed(1)}%
                            </span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </Card>
                )}

                {report.stock_contributions.length === 0 && report.total_trades === 0 && (
                  <Card className="p-6">
                    <div className="text-center py-8 text-gray-500">
                      <svg
                        className="w-12 h-12 mx-auto mb-3 text-gray-300"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={1.5}
                          d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
                        />
                      </svg>
                      <p>아직 완료된 거래가 없습니다.</p>
                      <p className="text-sm mt-1">종목을 매수한 후 매도하면 거래 기록이 표시됩니다.</p>
                    </div>
                  </Card>
                )}
              </div>
            )}
          </div>

          {/* Footer */}
          <div className="flex items-center justify-between px-6 py-4 border-t border-gray-200 bg-gray-50 rounded-b-xl">
            <p className="text-sm text-gray-500">
              {report && `마지막 업데이트: ${report.current_date}`}
            </p>
            <div className="flex items-center gap-3">
              <Button
                variant="secondary"
                size="sm"
                onClick={handleExport}
                disabled={isExporting || isLoading || !report}
              >
                {isExporting ? '내보내는 중...' : '거래 내역 내보내기'}
              </Button>
              <Button size="sm" onClick={onClose}>
                닫기
              </Button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

interface MetricItemProps {
  label: string;
  value: string;
  valueColor?: string;
}

function MetricItem({ label, value, valueColor = 'text-gray-900' }: MetricItemProps) {
  return (
    <div>
      <p className="text-sm text-gray-500 mb-1">{label}</p>
      <p className={`text-lg font-semibold ${valueColor}`}>{value}</p>
    </div>
  );
}
