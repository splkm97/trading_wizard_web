import { useState, useEffect } from 'react';
import RecommendationsPanel from '../components/trade/RecommendationsPanel';
import { Card, Button } from '../components/common';
import { useNavigate } from 'react-router-dom';
import { getWatchlist, removeFromWatchlist, type WatchlistItem } from '../services/api';

export default function DashboardPage() {
  const navigate = useNavigate();
  const [watchlist, setWatchlist] = useState<WatchlistItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [expandedIndex, setExpandedIndex] = useState<number | null>(null);

  useEffect(() => {
    fetchWatchlist();
  }, []);

  const fetchWatchlist = async () => {
    try {
      setLoading(true);
      const response = await getWatchlist();
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
      await removeFromWatchlist(stockCode);
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

  return (
    <div className="min-h-screen bg-gray-100 dark:bg-gray-900">
      <main className="max-w-7xl mx-auto px-4 py-6">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Daily Wizard Recommendations */}
          <div>
            <RecommendationsPanel />
          </div>

          {/* Watchlist */}
          <div>
            <Card title="관심 종목">
            {loading ? (
              <div className="space-y-4 p-4">
                <div className="animate-pulse space-y-3">
                  <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-3/4" />
                  <div className="h-20 bg-gray-200 dark:bg-gray-700 rounded" />
                  <div className="h-20 bg-gray-200 dark:bg-gray-700 rounded" />
                </div>
              </div>
            ) : watchlist.length === 0 ? (
              <div className="p-6 text-center">
                <p className="text-gray-600 dark:text-gray-400 mb-4">
                  등록된 관심 종목이 없습니다.
                </p>
                <p className="text-sm text-gray-500 dark:text-gray-500">
                  왼쪽의 추천 종목에서 '관심 종목 등록' 버튼을 클릭하여 추가하세요.
                </p>
              </div>
            ) : (
              <div className="space-y-4 p-4">
                {/* Summary */}
                <div className="flex justify-between items-center text-sm text-gray-500 dark:text-gray-400 pb-2 border-b border-gray-200 dark:border-gray-700">
                  <span>총 {watchlist.length}개 종목</span>
                  <button
                    onClick={() => fetchWatchlist()}
                    className="text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-300"
                  >
                    새로고침
                  </button>
                </div>

                {/* Watchlist Items */}
                <div className="space-y-2">
                  {watchlist.map((item, index) => (
                    <div
                      key={item.stock_code}
                      className="border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden"
                    >
                      <div
                        className="flex items-center justify-between p-3 cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800"
                        onClick={() => setExpandedIndex(expandedIndex === index ? null : index)}
                      >
                        <div className="flex-1">
                          <div className="flex items-center gap-2">
                            <span className="font-medium text-gray-900 dark:text-white">
                              {item.stock_name}
                            </span>
                            <span className="text-xs text-gray-500 dark:text-gray-400">
                              {item.stock_code}
                            </span>
                            {item.recommendation_score !== null && (
                              <span
                                className={`text-xs px-2 py-0.5 rounded ${getScoreBgColor(item.recommendation_score)} ${getScoreColor(item.recommendation_score)}`}
                              >
                                {item.recommendation_score}점
                              </span>
                            )}
                          </div>
                          {item.current_price && (
                            <div className="text-sm text-gray-600 dark:text-gray-300 mt-1">
                              현재가: {formatKRW(item.current_price.close)}원
                            </div>
                          )}
                        </div>
                        <div className="flex items-center gap-3">
                          {item.indicators && (
                            <div className="text-right text-xs text-gray-500 dark:text-gray-400">
                              <div>
                                RSI:{' '}
                                <span className={getRsiColor(item.indicators.rsi)}>
                                  {item.indicators.rsi.toFixed(1)}
                                </span>
                              </div>
                              <div>
                                MACD:{' '}
                                <span className={item.indicators.macd > 0 ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}>
                                  {item.indicators.macd.toFixed(2)}
                                </span>
                              </div>
                            </div>
                          )}
                          <span className="text-gray-400">
                            {expandedIndex === index ? '▲' : '▼'}
                          </span>
                        </div>
                      </div>

                      {expandedIndex === index && (
                        <div className="p-3 bg-gray-50 dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700 text-sm">
                          {/* Recommendation Reason */}
                          {item.recommendation_reason && (
                            <div className="mb-3 p-2 bg-blue-50 dark:bg-blue-900/20 rounded border border-blue-200 dark:border-blue-800">
                              <div className="flex items-center gap-2 mb-1">
                                <span className="text-xs font-medium text-blue-700 dark:text-blue-300">
                                  추천 사유
                                </span>
                                {item.recommendation_score !== null && (
                                  <span className={`text-xs font-bold ${getScoreColor(item.recommendation_score)}`}>
                                    {item.recommendation_score}점
                                  </span>
                                )}
                              </div>
                              <p className="text-xs text-gray-700 dark:text-gray-300 whitespace-pre-line">
                                {item.recommendation_reason}
                              </p>
                            </div>
                          )}

                          {/* Technical Indicators */}
                          {item.indicators && (
                            <div className="grid grid-cols-2 gap-2 mb-3">
                              <div className="p-2 bg-white dark:bg-gray-700 rounded border border-gray-200 dark:border-gray-600">
                                <span className="text-gray-500 dark:text-gray-400 text-xs">RSI</span>
                                <div className={`font-medium ${getRsiColor(item.indicators.rsi)}`}>
                                  {item.indicators.rsi.toFixed(1)}
                                  <span className="text-xs text-gray-400 ml-1">
                                    {item.indicators.rsi <= 30 ? '(과매도)' : item.indicators.rsi >= 70 ? '(과매수)' : '(중립)'}
                                  </span>
                                </div>
                              </div>
                              <div className="p-2 bg-white dark:bg-gray-700 rounded border border-gray-200 dark:border-gray-600">
                                <span className="text-gray-500 dark:text-gray-400 text-xs">MACD</span>
                                <div className={`font-medium ${item.indicators.macd > 0 ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}`}>
                                  {item.indicators.macd.toFixed(2)}
                                  <span className="text-xs text-gray-400 ml-1">
                                    {item.indicators.macd > 0 ? '(상승)' : '(하락)'}
                                  </span>
                                </div>
                              </div>
                            </div>
                          )}

                          {/* Meta Info & Actions */}
                          <div className="flex justify-between items-center pt-2 border-t border-gray-200 dark:border-gray-600">
                            <span className="text-xs text-gray-400">
                              등록일: {new Date(item.added_at).toLocaleDateString('ko-KR')}
                            </span>
                            <button
                              onClick={(e) => handleRemove(e, item.stock_code)}
                              className="px-3 py-1 text-xs bg-red-100 text-red-600 hover:bg-red-200 dark:bg-red-900/30 dark:text-red-400 dark:hover:bg-red-900/50 rounded"
                            >
                              삭제
                            </button>
                          </div>
                        </div>
                      )}
                    </div>
                  ))}
                </div>

                {/* View All Button */}
                <div className="pt-2 text-center">
                  <Button variant="secondary" onClick={() => navigate('/watchlist')}>
                    전체 보기
                  </Button>
                </div>
              </div>
            )}
            </Card>
          </div>
        </div>
      </main>
    </div>
  );
}
