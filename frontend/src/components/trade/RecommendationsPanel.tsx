import { useState, useEffect } from 'react';
import { Card } from '../common';
import { api } from '../../services/api';

interface BuyRecommendation {
  stock_code: string;
  stock_name: string;
  recommended_price: number;
  quantity: number;
  total_cost: number;
  confidence_score: number;
  reason: string;
  reason_detail: string;
  indicators: {
    rsi: number;
    macd_histogram: number;
    volume_ratio: number;
    bb_width: number;
    bb_upper: number;
    bb_middle: number;
    bb_lower: number;
  };
}

interface SellRecommendation {
  stock_code: string;
  stock_name: string;
  current_price: number;
  quantity: number;
  entry_price: number;
  pnl_pct: number;
  reason: string;
  indicators: Record<string, number>;
}

interface BuySignal {
  stock_code: string;
  stock_name: string;
  current_price: number;
  confidence_score: number;
  reason: string;
  indicators: Record<string, number>;
  affordable: boolean;
}

interface RecommendationsResponse {
  buy_recommendations: BuyRecommendation[];
  sell_recommendations: SellRecommendation[];
  all_buy_signals: BuySignal[];
  scanned_count: number;
  signal_count: number;
}

interface RecommendationsPanelProps {
  onSelectRecommendation?: (rec: BuyRecommendation) => void;
}

export default function RecommendationsPanel({
  onSelectRecommendation,
}: RecommendationsPanelProps) {
  const [buyRecs, setBuyRecs] = useState<BuyRecommendation[]>([]);
  const [sellRecs, setSellRecs] = useState<SellRecommendation[]>([]);
  const [allBuySignals, setAllBuySignals] = useState<BuySignal[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [scannedCount, setScannedCount] = useState(0);
  const [expandedBuyIndex, setExpandedBuyIndex] = useState<number | null>(null);
  const [showAllSignals, setShowAllSignals] = useState(false);

  const fetchRecommendations = async () => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await api.get<RecommendationsResponse>(
        '/recommendations?max_results=5'
      );
      setBuyRecs(response.buy_recommendations);
      setSellRecs(response.sell_recommendations);
      setAllBuySignals(response.all_buy_signals || []);
      setScannedCount(response.scanned_count);
    } catch (err) {
      setError('추천 데이터를 불러오는데 실패했습니다.');
      console.error('Failed to fetch recommendations:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchRecommendations();
  }, []);

  const formatKRW = (value: number) => {
    return new Intl.NumberFormat('ko-KR', {
      maximumFractionDigits: 0,
    }).format(value);
  };

  const getConfidenceColor = (score: number) => {
    if (score >= 80) return 'text-green-600';
    if (score >= 60) return 'text-yellow-600';
    return 'text-gray-500';
  };

  const getConfidenceBgColor = (score: number) => {
    if (score >= 80) return 'bg-green-100';
    if (score >= 60) return 'bg-yellow-100';
    return 'bg-gray-100';
  };

  const getPnLColor = (pnl: number) => {
    if (pnl > 0) return 'text-red-600';
    if (pnl < 0) return 'text-blue-600';
    return 'text-gray-600';
  };

  const handleSelect = (rec: BuyRecommendation) => {
    if (onSelectRecommendation) {
      onSelectRecommendation(rec);
    }
  };

  if (isLoading) {
    return (
      <Card title="Daily Wizard 추천">
        <div className="animate-pulse space-y-3">
          <div className="h-4 bg-gray-200 rounded w-3/4" />
          <div className="h-20 bg-gray-200 rounded" />
          <div className="h-20 bg-gray-200 rounded" />
        </div>
        <p className="text-sm text-gray-500 mt-3">
          KOSPI Top 100 스캔 중... (캐시 사용 시 1초 이내)
        </p>
      </Card>
    );
  }

  if (error) {
    return (
      <Card title="Daily Wizard 추천">
        <div className="text-center py-4">
          <p className="text-red-500 mb-3">{error}</p>
          <button
            onClick={fetchRecommendations}
            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
          >
            다시 시도
          </button>
        </div>
      </Card>
    );
  }

  return (
    <Card title="Daily Wizard 추천">
      <div className="space-y-4">
        {/* Summary */}
        <div className="flex justify-between items-center text-sm text-gray-500 pb-2 border-b">
          <span>스캔: {scannedCount}개</span>
          <span>신호: {allBuySignals.length}개</span>
          <button
            onClick={() => setShowAllSignals(!showAllSignals)}
            className="text-purple-600 hover:text-purple-800"
          >
            {showAllSignals ? '추천만 보기' : '전체 신호 보기'}
          </button>
          <button
            onClick={fetchRecommendations}
            className="text-blue-600 hover:text-blue-800"
          >
            새로고침
          </button>
        </div>

        {/* All Buy Signals (regardless of affordability) */}
        {showAllSignals && allBuySignals.length > 0 && (
          <div className="space-y-2">
            <h3 className="text-sm font-semibold text-purple-700 flex items-center gap-1">
              <span className="bg-purple-100 text-purple-800 px-2 py-0.5 rounded text-xs">
                전체
              </span>
              감지된 매수 신호 ({allBuySignals.length}개)
            </h3>
            {allBuySignals.map((sig) => (
              <div
                key={sig.stock_code}
                className={`border rounded-lg p-3 ${
                  sig.affordable
                    ? 'border-green-200 bg-green-50'
                    : 'border-gray-200 bg-gray-50'
                }`}
              >
                <div className="flex items-center justify-between">
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="font-medium">{sig.stock_name}</span>
                      <span className="text-xs text-gray-500">{sig.stock_code}</span>
                      <span
                        className={`text-xs px-2 py-0.5 rounded ${getConfidenceBgColor(sig.confidence_score)} ${getConfidenceColor(sig.confidence_score)}`}
                      >
                        {sig.confidence_score}점
                      </span>
                      {!sig.affordable && (
                        <span className="text-xs px-2 py-0.5 rounded bg-orange-100 text-orange-700">
                          잔액 부족
                        </span>
                      )}
                    </div>
                    <div className="text-sm text-gray-600 mt-1">
                      현재가: {formatKRW(sig.current_price)}원
                    </div>
                  </div>
                  <div className="text-right text-xs text-gray-500">
                    <div>RSI: {sig.indicators.rsi?.toFixed(1)}</div>
                    <div>거래량: {sig.indicators.volume_ratio?.toFixed(1)}x</div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* SELL Recommendations - Priority */}
        <div className="space-y-2">
          <h3 className="text-sm font-semibold text-blue-700 flex items-center gap-1">
            <span className="bg-blue-100 text-blue-800 px-2 py-0.5 rounded text-xs">
              매도
            </span>
            보유 종목 신호
          </h3>
          {sellRecs.length === 0 ? (
            <div className="text-center py-3 text-gray-500 text-sm border border-dashed border-gray-300 rounded-lg">
              <p>매도 신호가 없습니다. 보유 종목이 안정적입니다.</p>
            </div>
          ) : (
            sellRecs.map((rec) => (
              <div
                key={rec.stock_code}
                className="border border-blue-200 rounded-lg p-3 bg-blue-50"
              >
                <div className="flex items-center justify-between">
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="font-medium">{rec.stock_name}</span>
                      <span className="text-xs text-gray-500">{rec.stock_code}</span>
                    </div>
                    <div className="text-sm text-gray-600 mt-1">
                      {rec.quantity}주 @ {formatKRW(rec.entry_price)}원 →{' '}
                      {formatKRW(rec.current_price)}원
                    </div>
                  </div>
                  <div className="text-right">
                    <div className={`font-semibold ${getPnLColor(rec.pnl_pct)}`}>
                      {rec.pnl_pct > 0 ? '+' : ''}
                      {rec.pnl_pct.toFixed(1)}%
                    </div>
                    <div className="text-xs text-gray-500">{rec.reason}</div>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>

        {/* BUY Recommendations */}
        <div className="space-y-2">
          <h3 className="text-sm font-semibold text-red-700 flex items-center gap-1">
            <span className="bg-red-100 text-red-800 px-2 py-0.5 rounded text-xs">
              매수
            </span>
            추천 종목
          </h3>

          {buyRecs.length === 0 ? (
            <div className="text-center py-4 text-gray-500 text-sm">
              <p>현재 매수 추천 종목이 없습니다.</p>
            </div>
          ) : (
            buyRecs.map((rec, index) => (
              <div
                key={rec.stock_code}
                className="border rounded-lg overflow-hidden"
              >
                <div
                  className="flex items-center justify-between p-3 cursor-pointer hover:bg-gray-50"
                  onClick={() =>
                    setExpandedBuyIndex(expandedBuyIndex === index ? null : index)
                  }
                >
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <span className="font-medium">{rec.stock_name}</span>
                      <span className="text-xs text-gray-500">{rec.stock_code}</span>
                      <span
                        className={`text-xs px-2 py-0.5 rounded ${getConfidenceBgColor(rec.confidence_score)} ${getConfidenceColor(rec.confidence_score)}`}
                      >
                        {rec.confidence_score}점
                      </span>
                    </div>
                    <div className="text-sm text-gray-600 mt-1">
                      {formatKRW(rec.recommended_price)}원 x {rec.quantity}주 ={' '}
                      {formatKRW(rec.total_cost)}원
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleSelect(rec);
                      }}
                      className="px-3 py-1 bg-red-600 text-white text-sm rounded hover:bg-red-700"
                    >
                      선택
                    </button>
                    <span className="text-gray-400">
                      {expandedBuyIndex === index ? '▲' : '▼'}
                    </span>
                  </div>
                </div>

                {expandedBuyIndex === index && (
                  <div className="p-3 bg-gray-50 border-t text-sm">
                    <div className="grid grid-cols-3 gap-2 mb-3">
                      <div>
                        <span className="text-gray-500">RSI:</span>{' '}
                        <span
                          className={
                            rec.indicators.rsi >= 30 && rec.indicators.rsi <= 70
                              ? 'text-green-600'
                              : 'text-red-600'
                          }
                        >
                          {rec.indicators.rsi.toFixed(1)}
                        </span>
                      </div>
                      <div>
                        <span className="text-gray-500">MACD:</span>{' '}
                        <span
                          className={
                            rec.indicators.macd_histogram > 0
                              ? 'text-green-600'
                              : 'text-red-600'
                          }
                        >
                          {rec.indicators.macd_histogram.toFixed(2)}
                        </span>
                      </div>
                      <div>
                        <span className="text-gray-500">거래량:</span>{' '}
                        <span
                          className={
                            rec.indicators.volume_ratio >= 1.5
                              ? 'text-green-600'
                              : 'text-gray-600'
                          }
                        >
                          {rec.indicators.volume_ratio.toFixed(1)}x
                        </span>
                      </div>
                    </div>

                    <div className="text-gray-600 mb-2">
                      <div className="flex justify-between text-xs">
                        <span>상단: {formatKRW(rec.indicators.bb_upper)}원</span>
                        <span>중간: {formatKRW(rec.indicators.bb_middle)}원</span>
                        <span>하단: {formatKRW(rec.indicators.bb_lower)}원</span>
                      </div>
                    </div>

                    <div className="mt-2 p-2 bg-white rounded border text-xs whitespace-pre-line">
                      {rec.reason_detail}
                    </div>
                  </div>
                )}
              </div>
            ))
          )}
        </div>

      </div>
    </Card>
  );
}
