import { useState, useEffect } from 'react';
import { api } from '../services/api';
import { Card } from '../components/common/Card';

interface WatchlistItem {
  stock_code: string;
  stock_name: string;
  current_price: { close: number } | null;
  indicators: { rsi: number; macd: number } | null;
  recommendation_score: number | null;
  recommendation_reason: string | null;
  added_at: string;
}

export default function WatchlistPage() {
  const [watchlist, setWatchlist] = useState<WatchlistItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [expandedIndex, setExpandedIndex] = useState<number | null>(null);

  useEffect(() => {
    fetchWatchlist();
  }, []);

  const fetchWatchlist = async () => {
    try {
      setLoading(true);
      const response = await api.get<WatchlistItem[]>('/watchlists');
      setWatchlist(response);
    } catch (error) {
      console.error('Failed to fetch watchlist:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleRemove = async (e: React.MouseEvent, stockCode: string) => {
    e.stopPropagation();
    try {
      await api.delete(`/watchlists/${stockCode}`);
      setWatchlist(watchlist.filter(item => item.stock_code !== stockCode));
    } catch (error) {
      console.error('Failed to remove from watchlist:', error);
    }
  };

  const formatKRW = (value: number) => {
    return new Intl.NumberFormat('ko-KR', {
      maximumFractionDigits: 0,
    }).format(value);
  };

  const getScoreColor = (score: number) => {
    if (score >= 80) return 'text-green-600 dark:text-green-400';
    if (score >= 60) return 'text-yellow-600 dark:text-yellow-400';
    return 'text-gray-500 dark:text-gray-400';
  };

  const getScoreBgColor = (score: number) => {
    if (score >= 80) return 'bg-green-100 dark:bg-green-900/30';
    if (score >= 60) return 'bg-yellow-100 dark:bg-yellow-900/30';
    return 'bg-gray-100 dark:bg-gray-700';
  };

  const getRsiColor = (rsi: number) => {
    if (rsi <= 30) return 'text-blue-600 dark:text-blue-400';
    if (rsi >= 70) return 'text-red-600 dark:text-red-400';
    return 'text-green-600 dark:text-green-400';
  };

  const getRsiStatus = (rsi: number) => {
    if (rsi <= 30) return '과매도';
    if (rsi >= 70) return '과매수';
    return '중립';
  };

  if (loading) {
    return (
      <div className="max-w-6xl mx-auto px-4 py-8">
        <h1 className="text-3xl font-bold mb-6 text-gray-900 dark:text-white">관심 종목 모아보기</h1>
        <Card>
          <div className="space-y-4 p-4">
            <div className="animate-pulse space-y-3">
              <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-1/4" />
              <div className="h-24 bg-gray-200 dark:bg-gray-700 rounded" />
              <div className="h-24 bg-gray-200 dark:bg-gray-700 rounded" />
              <div className="h-24 bg-gray-200 dark:bg-gray-700 rounded" />
            </div>
          </div>
        </Card>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">관심 종목 모아보기</h1>
        <button
          onClick={() => fetchWatchlist()}
          className="px-4 py-2 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
        >
          새로고침
        </button>
      </div>

      {watchlist.length === 0 ? (
        <Card className="p-8 text-center">
          <p className="text-gray-600 dark:text-gray-400">관심 종목이 없습니다.</p>
          <p className="text-gray-500 dark:text-gray-500 mt-2 text-sm">
            Daily Wizard 추천 종목에서 '관심 종목 등록' 버튼을 클릭하여 종목을 추가하세요.
          </p>
        </Card>
      ) : (
        <Card>
          <div className="space-y-4 p-4">
            {/* Summary Header */}
            <div className="flex justify-between items-center text-sm text-gray-500 dark:text-gray-400 pb-3 border-b border-gray-200 dark:border-gray-700">
              <span>총 {watchlist.length}개 종목</span>
              <span>
                평균 점수:{' '}
                <span className="font-medium text-gray-700 dark:text-gray-300">
                  {watchlist.filter(i => i.recommendation_score !== null).length > 0
                    ? (watchlist.reduce((sum, i) => sum + (i.recommendation_score || 0), 0) / watchlist.filter(i => i.recommendation_score !== null).length).toFixed(1)
                    : '-'}
                  점
                </span>
              </span>
            </div>

            {/* Watchlist Items */}
            <div className="space-y-3">
              {watchlist.map((item, index) => (
                <div
                  key={item.stock_code}
                  className="border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden"
                >
                  {/* Header (always visible) */}
                  <div
                    className="flex items-center justify-between p-4 cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
                    onClick={() => setExpandedIndex(expandedIndex === index ? null : index)}
                  >
                    <div className="flex-1">
                      <div className="flex items-center gap-3 flex-wrap">
                        <span className="text-lg font-semibold text-gray-900 dark:text-white">
                          {item.stock_name}
                        </span>
                        <span className="text-sm text-gray-500 dark:text-gray-400">
                          {item.stock_code}
                        </span>
                        {item.recommendation_score !== null && (
                          <span
                            className={`text-sm px-2 py-0.5 rounded font-medium ${getScoreBgColor(item.recommendation_score)} ${getScoreColor(item.recommendation_score)}`}
                          >
                            {item.recommendation_score}점
                          </span>
                        )}
                      </div>
                      {item.current_price && (
                        <div className="text-base text-gray-600 dark:text-gray-300 mt-1">
                          현재가: <span className="font-medium">{formatKRW(item.current_price.close)}원</span>
                        </div>
                      )}
                    </div>
                    <div className="flex items-center gap-4">
                      {item.indicators && (
                        <div className="text-right text-sm hidden sm:block">
                          <div className="text-gray-500 dark:text-gray-400">
                            RSI:{' '}
                            <span className={`font-medium ${getRsiColor(item.indicators.rsi)}`}>
                              {item.indicators.rsi.toFixed(1)}
                            </span>
                          </div>
                          <div className="text-gray-500 dark:text-gray-400">
                            MACD:{' '}
                            <span className={`font-medium ${item.indicators.macd > 0 ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}`}>
                              {item.indicators.macd.toFixed(2)}
                            </span>
                          </div>
                        </div>
                      )}
                      <span className="text-gray-400 text-lg">
                        {expandedIndex === index ? '▲' : '▼'}
                      </span>
                    </div>
                  </div>

                  {/* Expanded Content */}
                  {expandedIndex === index && (
                    <div className="p-4 bg-gray-50 dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700">
                      {/* Recommendation Section */}
                      {item.recommendation_reason && (
                        <div className="mb-4 p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-800">
                          <div className="flex items-center gap-2 mb-2">
                            <span className="text-sm font-medium text-blue-700 dark:text-blue-300">
                              추천 사유
                            </span>
                            {item.recommendation_score !== null && (
                              <span className={`text-sm font-bold ${getScoreColor(item.recommendation_score)}`}>
                                {item.recommendation_score}점 / 100
                              </span>
                            )}
                          </div>
                          <p className="text-sm text-gray-700 dark:text-gray-300 whitespace-pre-line leading-relaxed">
                            {item.recommendation_reason}
                          </p>
                        </div>
                      )}

                      {/* Technical Indicators Grid */}
                      {item.indicators && (
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
                          <div className="p-3 bg-white dark:bg-gray-700 rounded-lg border border-gray-200 dark:border-gray-600">
                            <div className="text-xs text-gray-500 dark:text-gray-400 mb-1">RSI (14)</div>
                            <div className={`text-xl font-bold ${getRsiColor(item.indicators.rsi)}`}>
                              {item.indicators.rsi.toFixed(1)}
                            </div>
                            <div className={`text-xs mt-1 ${getRsiColor(item.indicators.rsi)}`}>
                              {getRsiStatus(item.indicators.rsi)}
                            </div>
                          </div>
                          <div className="p-3 bg-white dark:bg-gray-700 rounded-lg border border-gray-200 dark:border-gray-600">
                            <div className="text-xs text-gray-500 dark:text-gray-400 mb-1">MACD</div>
                            <div className={`text-xl font-bold ${item.indicators.macd > 0 ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}`}>
                              {item.indicators.macd.toFixed(2)}
                            </div>
                            <div className={`text-xs mt-1 ${item.indicators.macd > 0 ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}`}>
                              {item.indicators.macd > 0 ? '상승 추세' : '하락 추세'}
                            </div>
                          </div>
                          {item.current_price && (
                            <div className="p-3 bg-white dark:bg-gray-700 rounded-lg border border-gray-200 dark:border-gray-600">
                              <div className="text-xs text-gray-500 dark:text-gray-400 mb-1">현재가</div>
                              <div className="text-xl font-bold text-gray-900 dark:text-white">
                                {formatKRW(item.current_price.close)}
                              </div>
                              <div className="text-xs mt-1 text-gray-500">원</div>
                            </div>
                          )}
                          {item.recommendation_score !== null && (
                            <div className="p-3 bg-white dark:bg-gray-700 rounded-lg border border-gray-200 dark:border-gray-600">
                              <div className="text-xs text-gray-500 dark:text-gray-400 mb-1">추천 점수</div>
                              <div className={`text-xl font-bold ${getScoreColor(item.recommendation_score)}`}>
                                {item.recommendation_score}
                              </div>
                              <div className="text-xs mt-1 text-gray-500">/ 100점</div>
                            </div>
                          )}
                        </div>
                      )}

                      {/* Footer with Date and Actions */}
                      <div className="flex justify-between items-center pt-3 border-t border-gray-200 dark:border-gray-600">
                        <span className="text-sm text-gray-500 dark:text-gray-400">
                          등록일: {new Date(item.added_at).toLocaleDateString('ko-KR')}
                        </span>
                        <button
                          onClick={(e) => handleRemove(e, item.stock_code)}
                          className="px-4 py-2 text-sm bg-red-100 text-red-600 hover:bg-red-200 dark:bg-red-900/30 dark:text-red-400 dark:hover:bg-red-900/50 rounded-lg transition-colors"
                        >
                          관심 종목 삭제
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        </Card>
      )}
    </div>
  );
}