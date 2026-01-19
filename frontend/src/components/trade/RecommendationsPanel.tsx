import { useState, useEffect, useRef } from 'react';
import { Card } from '../common';
import { api, addToWatchlist } from '../../services/api';
import { AppliedSettings } from '../../types';

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
  reason_detail: string;
  indicators: Record<string, number>;
  affordable: boolean;
}

interface RecommendationsResponse {
  buy_recommendations: BuyRecommendation[];
  sell_recommendations: SellRecommendation[];
  all_buy_signals: BuySignal[];
  scanned_count: number;
  signal_count: number;
  applied_settings: AppliedSettings;
}

export default function RecommendationsPanel() {
  const [buyRecs, setBuyRecs] = useState<BuyRecommendation[]>([]);
  const [sellRecs, setSellRecs] = useState<SellRecommendation[]>([]);
  const [allBuySignals, setAllBuySignals] = useState<BuySignal[]>([]);
  const [appliedSettings, setAppliedSettings] = useState<AppliedSettings | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [scannedCount, setScannedCount] = useState(0);
  const [expandedBuyIndex, setExpandedBuyIndex] = useState<number | null>(null);
  const [expandedSignalIndex, setExpandedSignalIndex] = useState<number | null>(null);
  const [showAllSignals, setShowAllSignals] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const [loadingTime, setLoadingTime] = useState(0);
  const [isForceFetch, setIsForceFetch] = useState(false);
  const loadingTimerRef = useRef<number | null>(null);

  const fetchRecommendations = async (forceFetch: boolean = false) => {
    setIsLoading(true);
    setError(null);
    setLoadingTime(0);
    setIsForceFetch(forceFetch);

    // Start loading timer
    loadingTimerRef.current = window.setInterval(() => {
      setLoadingTime((prev) => prev + 1);
    }, 1000);

    try {
      const url = forceFetch
        ? '/recommendations?max_results=5&force_fetch=true'
        : '/recommendations?max_results=5';
      const response = await api.get<RecommendationsResponse>(url);
      setBuyRecs(response.buy_recommendations);
      setSellRecs(response.sell_recommendations);
      setAllBuySignals(response.all_buy_signals || []);
      setScannedCount(response.scanned_count);
      setAppliedSettings(response.applied_settings);
    } catch (err) {
      setError('추천 데이터를 불러오는데 실패했습니다.');
      console.error('Failed to fetch recommendations:', err);
    } finally {
      // Clear loading timer
      if (loadingTimerRef.current) {
        clearInterval(loadingTimerRef.current);
        loadingTimerRef.current = null;
      }
      setIsLoading(false);
      setIsForceFetch(false);
    }
  };

  // Cleanup timer on unmount
  useEffect(() => {
    return () => {
      if (loadingTimerRef.current) {
        clearInterval(loadingTimerRef.current);
      }
    };
  }, []);

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

  const handleAddToWatchlist = async (e: React.MouseEvent, stockCode: string, stockName: string) => {
    e.stopPropagation();
    try {
      await addToWatchlist({ stock_code: stockCode, stock_name: stockName });
      alert('관심 종목에 등록되었습니다.');
    } catch (error) {
      console.error('Failed to add to watchlist:', error);
      alert('관심 종목 등록에 실패했습니다.');
    }
  };

  if (isLoading) {
    // Loading messages based on elapsed time
    const getLoadingMessage = () => {
      if (isForceFetch) {
        if (loadingTime < 5) return 'yfinance에서 최신 데이터를 가져오는 중...';
        if (loadingTime < 15) return `실시간 데이터 수집 중... (${loadingTime}초)`;
        if (loadingTime < 30) return `100개 종목 분석 중... (${loadingTime}초) - 잠시만 기다려주세요`;
        return `데이터 처리 중... (${loadingTime}초) - 네트워크 상태에 따라 시간이 걸릴 수 있습니다`;
      }
      if (loadingTime < 3) return 'KOSPI Top 100 스캔 중...';
      if (loadingTime < 10) return `캐시 데이터 확인 중... (${loadingTime}초)`;
      if (loadingTime < 20) return `데이터베이스에서 조회 중... (${loadingTime}초)`;
      return `실시간 데이터 수집 중... (${loadingTime}초) - 캐시가 만료되어 새로 가져오는 중입니다`;
    };

    const getLoadingStatus = () => {
      if (loadingTime < 5) return { color: 'text-blue-600', bg: 'bg-blue-100' };
      if (loadingTime < 15) return { color: 'text-yellow-600', bg: 'bg-yellow-100' };
      return { color: 'text-orange-600', bg: 'bg-orange-100' };
    };

    const status = getLoadingStatus();

    return (
      <Card title="Daily Wizard 추천">
        <div className="space-y-4">
          {/* Progress indicator */}
          <div className="flex items-center gap-3">
            <div className="animate-spin rounded-full h-5 w-5 border-2 border-blue-600 border-t-transparent" />
            <span className={`text-sm font-medium ${status.color}`}>
              {getLoadingMessage()}
            </span>
          </div>

          {/* Progress bar for force fetch */}
          {isForceFetch && (
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className="bg-blue-600 h-2 rounded-full transition-all duration-1000"
                style={{ width: `${Math.min(loadingTime * 2, 95)}%` }}
              />
            </div>
          )}

          {/* Skeleton UI */}
          <div className="animate-pulse space-y-3">
            <div className="h-4 bg-gray-200 rounded w-3/4" />
            <div className="h-20 bg-gray-200 rounded" />
            <div className="h-20 bg-gray-200 rounded" />
          </div>

          {/* Extended loading notice */}
          {loadingTime >= 10 && (
            <div className={`p-3 rounded-lg ${status.bg} border`}>
              <p className={`text-sm ${status.color}`}>
                {loadingTime >= 20 ? (
                  <>
                    <strong>알림:</strong> 캐시된 데이터가 없거나 만료되어 실시간 데이터를 수집하고 있습니다.
                    최초 로딩 시 또는 장중에는 시간이 더 걸릴 수 있습니다.
                  </>
                ) : (
                  <>
                    <strong>안내:</strong> 데이터를 준비하고 있습니다. 잠시만 기다려주세요.
                  </>
                )}
              </p>
            </div>
          )}

          {/* Loading time indicator */}
          {loadingTime >= 5 && (
            <div className="flex justify-between text-xs text-gray-500">
              <span>경과 시간: {loadingTime}초</span>
              <span>예상 소요: {isForceFetch ? '30-60초' : '5-10초'}</span>
            </div>
          )}
        </div>
      </Card>
    );
  }

  if (error) {
    return (
      <Card title="Daily Wizard 추천">
        <div className="text-center py-4">
          <p className="text-red-500 mb-3">{error}</p>
          <button
            onClick={() => fetchRecommendations(true)}
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
        {/* Applied Settings Summary */}
        {appliedSettings && (
          <div className="bg-gray-50 rounded-lg p-3 border border-gray-200">
            <div
              className="flex justify-between items-center cursor-pointer"
              onClick={() => setShowSettings(!showSettings)}
            >
              <div className="flex items-center gap-2">
                <span className="text-xs font-medium text-gray-700">적용된 설정</span>
                <span className="text-xs px-2 py-0.5 bg-green-100 text-green-700 rounded">
                  활성
                </span>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-xs text-gray-500">
                  신뢰도 ≥{appliedSettings.confidence_threshold}점 | 손절 {appliedSettings.stop_loss_pct}%
                </span>
                <span className="text-gray-400 text-xs">
                  {showSettings ? '▲' : '▼'}
                </span>
              </div>
            </div>

            {showSettings && (
              <div className="mt-3 pt-3 border-t border-gray-200 grid grid-cols-2 gap-x-4 gap-y-2 text-xs">
                <div className="col-span-2 text-gray-500 font-medium mb-1">리스크 관리</div>
                <div className="flex justify-between">
                  <span className="text-gray-500">손절선:</span>
                  <span className="text-gray-700">{appliedSettings.stop_loss_pct}%</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500">최대 포지션:</span>
                  <span className="text-gray-700">{appliedSettings.max_positions}개</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500">종목당 비중:</span>
                  <span className="text-gray-700">{appliedSettings.max_position_pct}%</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500">신뢰도 임계값:</span>
                  <span className="text-gray-700">{appliedSettings.confidence_threshold}점</span>
                </div>

                <div className="col-span-2 text-gray-500 font-medium mt-2 mb-1">익절/매도</div>
                <div className="flex justify-between">
                  <span className="text-gray-500">익절 목표:</span>
                  <span className="text-gray-700">{appliedSettings.take_profit_pct}%</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500">익절 비율:</span>
                  <span className="text-gray-700">{(appliedSettings.take_profit_ratio * 100).toFixed(0)}%</span>
                </div>
                <div className="flex justify-between col-span-2">
                  <span className="text-gray-500">중간밴드 하향 시 매도:</span>
                  <span className={appliedSettings.sell_on_middle_band ? 'text-green-600' : 'text-gray-400'}>
                    {appliedSettings.sell_on_middle_band ? '활성' : '비활성'}
                  </span>
                </div>

                <div className="col-span-2 text-gray-500 font-medium mt-2 mb-1">볼린저밴드</div>
                <div className="flex justify-between">
                  <span className="text-gray-500">기간:</span>
                  <span className="text-gray-700">{appliedSettings.bollinger_period}일</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500">표준편차:</span>
                  <span className="text-gray-700">{appliedSettings.bollinger_std_dev}σ</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500">스퀴즈 임계값:</span>
                  <span className="text-gray-700">{appliedSettings.squeeze_threshold_pct}%</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500">스퀴즈 관측일:</span>
                  <span className="text-gray-700">{appliedSettings.squeeze_lookback_days}일</span>
                </div>

                <div className="col-span-2 mt-2 pt-2 border-t border-gray-200">
                  <a
                    href="/settings"
                    className="text-blue-600 hover:text-blue-800 text-xs"
                  >
                    설정 변경하기 →
                  </a>
                </div>
              </div>
            )}
          </div>
        )}

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
            onClick={() => fetchRecommendations(true)}
            className="text-blue-600 hover:text-blue-800"
            title="yfinance에서 최신 데이터 가져오기"
          >
            🔄 새로고침
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
            {allBuySignals.map((sig, index) => (
              <div
                key={sig.stock_code}
                className={`border rounded-lg overflow-hidden ${
                  sig.affordable
                    ? 'border-green-200 bg-green-50'
                    : 'border-gray-200 bg-gray-50'
                }`}
              >
                <div
                  className="flex items-center justify-between p-3 cursor-pointer hover:bg-opacity-80"
                  onClick={() =>
                    setExpandedSignalIndex(expandedSignalIndex === index ? null : index)
                  }
                >
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="font-medium">{sig.stock_name}</span>
                      <span className="text-xs text-gray-500">{sig.stock_code}</span>
                      <span
                        className={`text-xs px-2 py-0.5 rounded ${getConfidenceBgColor(sig.confidence_score)} ${getConfidenceColor(sig.confidence_score)}`}
                      >
                        {sig.confidence_score.toFixed(3)}점
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
                  <div className="flex items-center gap-3">
                    <div className="text-right text-xs text-gray-500">
                      <div>RSI: {sig.indicators.rsi?.toFixed(1)}</div>
                      <div>거래량: {sig.indicators.volume_ratio?.toFixed(1)}x</div>
                    </div>
                    <span className="text-gray-400">
                      {expandedSignalIndex === index ? '▲' : '▼'}
                    </span>
                  </div>
                </div>

                {expandedSignalIndex === index && (
                  <div className="p-3 bg-white border-t text-sm">
                    <div className="p-2 bg-gray-50 rounded border text-xs whitespace-pre-line mb-3">
                      {sig.reason_detail}
                    </div>

                    {!sig.affordable && (
                      <div className="p-2 bg-orange-50 rounded border border-orange-200 text-xs text-orange-700">
                        현재 잔액으로는 이 종목을 매수할 수 없습니다. 잔액을 확인해주세요.
                      </div>
                    )}
                  </div>
                )}
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
                        {rec.confidence_score.toFixed(3)}점
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
                          handleAddToWatchlist(e, rec.stock_code, rec.stock_name);
                        }}
                        className="px-3 py-1 bg-blue-600 text-white text-sm rounded hover:bg-blue-700"
                      >
                        관심 종목 등록
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
