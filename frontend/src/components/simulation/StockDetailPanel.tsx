/**
 * Stock Detail Panel - Display stock chart and indicator details
 */

import { useState } from 'react';
import { Card } from '../common/Card';
import {
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
  Area,
  ComposedChart,
} from 'recharts';
import type { StockDetail, ExecuteTradeRequest } from '../../types/simulation';
import { TradeActionButtons } from './TradeActionButtons';
import { BuyInputModal } from './BuyInputModal';
import { executeTrade } from '../../services/simulation';

interface StockDetailPanelProps {
  stockDetail: StockDetail | null;
  isLoading?: boolean;
  sessionId?: string;
  availableCash?: number;
  sessionStatus?: string;
  onTradeExecuted?: () => void;
}

export function StockDetailPanel({
  stockDetail,
  isLoading = false,
  sessionId,
  availableCash = 0,
  sessionStatus,
  onTradeExecuted,
}: StockDetailPanelProps) {
  const [isBuyModalOpen, setIsBuyModalOpen] = useState(false);
  const [isTradeLoading, setIsTradeLoading] = useState(false);
  const [tradeError, setTradeError] = useState<string | null>(null);

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

  const formatDate = (date: string) => {
    const d = new Date(date);
    return `${d.getMonth() + 1}/${d.getDate()}`;
  };

  // Trade handlers
  const handleBuy = () => {
    setTradeError(null);
    setIsBuyModalOpen(true);
  };

  const handleBuyConfirm = async (params: { quantity?: number; amount?: number }) => {
    if (!sessionId || !stockDetail) return;

    setIsTradeLoading(true);
    setTradeError(null);

    try {
      const request: ExecuteTradeRequest = {
        stock_code: stockDetail.stock_code,
        action: 'BUY',
        quantity: params.quantity,
        amount: params.amount,
      };

      await executeTrade(sessionId, request);
      setIsBuyModalOpen(false);
      onTradeExecuted?.();
    } catch (err) {
      const error = err as { detail?: string; message?: string };
      setTradeError(error.detail || error.message || '매수 주문에 실패했습니다');
    } finally {
      setIsTradeLoading(false);
    }
  };

  const handleSell = async () => {
    if (!sessionId || !stockDetail) return;

    setIsTradeLoading(true);
    setTradeError(null);

    try {
      const request: ExecuteTradeRequest = {
        stock_code: stockDetail.stock_code,
        action: 'SELL',
        // No quantity = sell all
      };

      await executeTrade(sessionId, request);
      onTradeExecuted?.();
    } catch (err) {
      const error = err as { detail?: string; message?: string };
      setTradeError(error.detail || error.message || '매도 주문에 실패했습니다');
    } finally {
      setIsTradeLoading(false);
    }
  };

  const handleSkip = () => {
    // Skip does nothing, just a visual action
    // User will proceed by clicking "Next Turn" button elsewhere
  };

  const handleHold = () => {
    // Hold does nothing, just a visual action
    // User will proceed by clicking "Next Turn" button elsewhere
  };

  // Should show trade buttons?
  const showTradeButtons = stockDetail && sessionId && sessionStatus === 'IN_PROGRESS';

  if (isLoading) {
    return (
      <Card className="h-full">
        <div className="p-6 flex flex-col items-center justify-center h-96">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mb-4" />
          <p className="text-gray-500">종목 정보 불러오는 중...</p>
        </div>
      </Card>
    );
  }

  if (!stockDetail) {
    return (
      <Card className="h-full">
        <div className="p-8 flex flex-col items-center justify-center text-center h-96">
          <div className="w-20 h-20 rounded-full bg-gray-100 flex items-center justify-center mb-4">
            <svg className="w-10 h-10 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M7 12l3-3 3 3 4-4M8 21l4-4 4 4M3 4h18M4 4h16v12a1 1 0 01-1 1H5a1 1 0 01-1-1V4z" />
            </svg>
          </div>
          <p className="text-gray-600 font-medium mb-1">종목을 선택하세요</p>
          <p className="text-sm text-gray-400">
            왼쪽 추천 종목 리스트에서 종목을 선택하면<br />
            차트와 상세 정보를 확인할 수 있습니다
          </p>
        </div>
      </Card>
    );
  }

  const { indicators, price_history } = stockDetail;

  const chartData = price_history.map((p) => ({
    date: formatDate(p.date),
    fullDate: p.date,
    close: p.close,
    high: p.high,
    low: p.low,
    volume: p.volume,
  }));

  const latestPrice = price_history.length > 0 ? price_history[price_history.length - 1] : null;

  const getScoreColor = (score: number) => {
    if (score >= 20) return 'text-green-600';
    if (score >= 10) return 'text-amber-600';
    return 'text-gray-600';
  };

  const getScoreBgColor = (score: number) => {
    if (score >= 20) return 'bg-green-500';
    if (score >= 10) return 'bg-amber-500';
    return 'bg-gray-400';
  };

  return (
    <div className="space-y-4" data-testid="stock-detail">
      <Card>
        <div className="p-4 border-b border-gray-100">
          <div className="flex items-start justify-between">
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-xl font-bold text-gray-900">
                  {stockDetail.stock_name}
                </h3>
                {stockDetail.is_owned && (
                  <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-primary-100 text-primary-700">
                    보유중
                  </span>
                )}
              </div>
              <p className="text-sm text-gray-500">{stockDetail.stock_code}</p>
            </div>
            <div className="text-right">
              <p className="text-2xl font-bold text-gray-900">
                {formatCurrency(stockDetail.current_price)}
              </p>
              <div className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-lg text-sm font-bold ${
                stockDetail.confidence_score >= 70 ? 'bg-green-50 text-green-600' :
                stockDetail.confidence_score >= 55 ? 'bg-amber-50 text-amber-600' :
                'bg-gray-50 text-gray-600'
              }`}>
                신뢰도 {stockDetail.confidence_score}점
              </div>
            </div>
          </div>
        </div>

        {stockDetail.is_owned && stockDetail.avg_entry_price !== null && (
          <div className="px-4 py-3 bg-blue-50 border-b border-blue-100">
            <div className="grid grid-cols-4 gap-4 text-sm">
              <div>
                <span className="text-blue-600">보유수량</span>
                <p className="font-semibold text-blue-900">{stockDetail.owned_quantity?.toLocaleString()}주</p>
              </div>
              <div>
                <span className="text-blue-600">평균단가</span>
                <p className="font-semibold text-blue-900">{formatCurrency(stockDetail.avg_entry_price)}</p>
              </div>
              <div>
                <span className="text-blue-600">평가손익</span>
                <p className={`font-semibold ${
                  (stockDetail.unrealized_pnl ?? 0) >= 0 ? 'text-green-600' : 'text-red-600'
                }`}>
                  {formatCurrency(stockDetail.unrealized_pnl ?? 0)}
                </p>
              </div>
              <div>
                <span className="text-blue-600">수익률</span>
                <p className={`font-semibold ${
                  (stockDetail.unrealized_pnl_pct ?? 0) >= 0 ? 'text-green-600' : 'text-red-600'
                }`}>
                  {formatPercent(stockDetail.unrealized_pnl_pct ?? 0)}
                </p>
              </div>
            </div>
          </div>
        )}

        <div className="p-4">
          <ResponsiveContainer width="100%" height={280}>
            <ComposedChart data={chartData}>
              <defs>
                <linearGradient id="colorPrice" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.1}/>
                  <stop offset="95%" stopColor="#3b82f6" stopOpacity={0}/>
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <XAxis 
                dataKey="date" 
                tick={{ fontSize: 11, fill: '#6b7280' }}
                tickLine={false}
              />
              <YAxis 
                tick={{ fontSize: 11, fill: '#6b7280' }}
                tickFormatter={(v) => `${(v / 1000).toFixed(0)}k`}
                tickLine={false}
                axisLine={false}
                domain={['auto', 'auto']}
              />
              <Tooltip
                labelFormatter={(label) => {
                  const item = chartData.find((d) => d.date === label);
                  return item?.fullDate || String(label);
                }}
                formatter={(value, name) => {
                  const labels: Record<string, string> = {
                    close: '종가',
                    high: '고가',
                    low: '저가',
                  };
                  return [formatCurrency(Number(value)), labels[String(name)] || String(name)];
                }}
                contentStyle={{
                  backgroundColor: 'rgba(255, 255, 255, 0.95)',
                  border: '1px solid #e5e7eb',
                  borderRadius: '8px',
                  boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
                }}
              />
              {indicators.bollinger && (
                <>
                  <ReferenceLine
                    y={indicators.bollinger.upper}
                    stroke="#ef4444"
                    strokeDasharray="5 5"
                    label={{ value: '상단', position: 'right', fontSize: 10, fill: '#ef4444' }}
                  />
                  <ReferenceLine
                    y={indicators.bollinger.middle}
                    stroke="#f59e0b"
                    strokeDasharray="3 3"
                    label={{ value: '중간', position: 'right', fontSize: 10, fill: '#f59e0b' }}
                  />
                  <ReferenceLine
                    y={indicators.bollinger.lower}
                    stroke="#22c55e"
                    strokeDasharray="5 5"
                    label={{ value: '하단', position: 'right', fontSize: 10, fill: '#22c55e' }}
                  />
                </>
              )}
              <Area
                type="monotone"
                dataKey="close"
                stroke="#3b82f6"
                strokeWidth={2}
                fill="url(#colorPrice)"
              />
              <Line
                type="monotone"
                dataKey="high"
                stroke="#ef444480"
                strokeWidth={1}
                dot={false}
                strokeDasharray="2 2"
              />
              <Line
                type="monotone"
                dataKey="low"
                stroke="#22c55e80"
                strokeWidth={1}
                dot={false}
                strokeDasharray="2 2"
              />
            </ComposedChart>
          </ResponsiveContainer>

          {latestPrice && (
            <div className="mt-2 flex items-center justify-center gap-6 text-xs text-gray-500">
              <span>시가: {formatCurrency(latestPrice.open)}</span>
              <span className="text-red-500">고가: {formatCurrency(latestPrice.high)}</span>
              <span className="text-green-500">저가: {formatCurrency(latestPrice.low)}</span>
              <span>종가: {formatCurrency(latestPrice.close)}</span>
            </div>
          )}
        </div>
      </Card>

      <Card>
        <div className="p-4 border-b border-gray-100">
          <h4 className="font-semibold text-gray-900">기술적 지표</h4>
        </div>
        <div className="p-4 grid grid-cols-2 lg:grid-cols-4 gap-4">
          <IndicatorCard
            name="볼린저 밴드"
            score={indicators.bollinger.score}
            details={[
              { label: '상단', value: formatCurrency(indicators.bollinger.upper) },
              { label: '중간', value: formatCurrency(indicators.bollinger.middle) },
              { label: '하단', value: formatCurrency(indicators.bollinger.lower) },
              { label: '밴드폭', value: `${(indicators.bollinger.bandwidth * 100).toFixed(1)}%` },
            ]}
            maxScore={25}
            getScoreColor={getScoreColor}
            getScoreBgColor={getScoreBgColor}
          />
          <IndicatorCard
            name="RSI"
            score={indicators.rsi.score}
            details={[
              { label: '값', value: indicators.rsi.value.toFixed(1) },
              { 
                label: '상태', 
                value: indicators.rsi.value >= 70 ? '과매수' : 
                       indicators.rsi.value <= 30 ? '과매도' : '중립'
              },
            ]}
            maxScore={20}
            getScoreColor={getScoreColor}
            getScoreBgColor={getScoreBgColor}
          />
          <IndicatorCard
            name="MACD"
            score={indicators.macd.score}
            details={[
              { label: 'MACD', value: indicators.macd.macd.toFixed(0) },
              { label: 'Signal', value: indicators.macd.signal.toFixed(0) },
              { label: 'Histogram', value: indicators.macd.histogram.toFixed(0) },
            ]}
            maxScore={30}
            getScoreColor={getScoreColor}
            getScoreBgColor={getScoreBgColor}
          />
          <IndicatorCard
            name="거래량"
            score={indicators.volume.score}
            details={[
              { label: '현재', value: `${(indicators.volume.current / 1000).toFixed(0)}K` },
              { label: '평균', value: `${(indicators.volume.average / 1000).toFixed(0)}K` },
              { label: '비율', value: `${indicators.volume.ratio.toFixed(1)}x` },
            ]}
            maxScore={25}
            getScoreColor={getScoreColor}
            getScoreBgColor={getScoreBgColor}
          />
        </div>
      </Card>

      {/* Trade Action Buttons */}
      {showTradeButtons && (
        <Card>
          <div className="p-4">
            {tradeError && (
              <div className="mb-4 p-3 bg-red-50 rounded-lg border border-red-200">
                <p className="text-sm text-red-600 flex items-center gap-2">
                  <svg className="w-4 h-4 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  {tradeError}
                </p>
              </div>
            )}
            <TradeActionButtons
              isOwned={stockDetail.is_owned}
              isLoading={isTradeLoading}
              onBuy={handleBuy}
              onSkip={handleSkip}
              onSell={handleSell}
              onHold={handleHold}
            />
          </div>
        </Card>
      )}

      {/* Buy Input Modal */}
      <BuyInputModal
        isOpen={isBuyModalOpen}
        onClose={() => setIsBuyModalOpen(false)}
        stockCode={stockDetail.stock_code}
        stockName={stockDetail.stock_name}
        currentPrice={stockDetail.current_price}
        availableCash={availableCash}
        onConfirm={handleBuyConfirm}
        isLoading={isTradeLoading}
      />
    </div>
  );
}

interface IndicatorCardProps {
  name: string;
  score: number;
  details: { label: string; value: string }[];
  maxScore: number;
  getScoreColor: (score: number) => string;
  getScoreBgColor: (score: number) => string;
}

function IndicatorCard({ 
  name, 
  score, 
  details, 
  maxScore,
  getScoreColor,
  getScoreBgColor,
}: IndicatorCardProps) {
  const percentage = (score / maxScore) * 100;
  
  return (
    <div className="bg-gray-50 rounded-lg p-3">
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm font-medium text-gray-700">{name}</span>
        <span className={`text-sm font-bold ${getScoreColor(score)}`}>
          {score}/{maxScore}
        </span>
      </div>
      <div className="h-1.5 bg-gray-200 rounded-full overflow-hidden mb-3">
        <div
          className={`h-full rounded-full transition-all ${getScoreBgColor(score)}`}
          style={{ width: `${percentage}%` }}
        />
      </div>
      <div className="space-y-1">
        {details.map((d, i) => (
          <div key={i} className="flex justify-between text-xs">
            <span className="text-gray-500">{d.label}</span>
            <span className="text-gray-700 font-medium">{d.value}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
