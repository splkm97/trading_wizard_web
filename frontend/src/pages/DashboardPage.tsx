import { useState, useEffect } from 'react';
import RecommendationsPanel from '../components/trade/RecommendationsPanel';
import { Card, Button } from '../components/common';
import { useNavigate } from 'react-router-dom';
import { getWatchlist, removeFromWatchlist, type WatchlistItem } from '../services/api';

export default function DashboardPage() {
  const navigate = useNavigate();
  const [watchlist, setWatchlist] = useState<WatchlistItem[]>([]);
  const [loading, setLoading] = useState(true);

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

  const handleRemove = async (stockCode: string) => {
    try {
      await removeFromWatchlist(stockCode);
      setWatchlist(watchlist.filter(item => item.stock_code !== stockCode));
    } catch (error) {
      console.error('Failed to remove from watchlist:', error);
    }
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
              <div className="p-6 text-center text-gray-500">로딩 중...</div>
            ) : watchlist.length === 0 ? (
              <div className="p-6 text-center">
                <p className="text-gray-600 dark:text-gray-400 mb-4">
                  등록된 관심 종목이 없습니다.
                </p>
                <p className="text-sm text-gray-500 dark:text-gray-500">
                  위의 추천 종목에서 '관심 종목 등록' 버튼을 클릭하여 추가하세요.
                </p>
              </div>
            ) : (
              <div className="divide-y divide-gray-200 dark:divide-gray-700">
                {watchlist.map((item) => (
                  <div key={item.stock_code} className="p-4 flex justify-between items-center hover:bg-gray-50 dark:hover:bg-gray-800">
                    <div className="flex-1">
                      <div className="flex items-center gap-3">
                        <h3 className="font-semibold text-gray-900 dark:text-white">
                          {item.stock_name}
                        </h3>
                        <span className="text-sm text-gray-500 dark:text-gray-400">
                          {item.stock_code}
                        </span>
                      </div>
                      <p className="text-xs text-gray-400 mt-1">
                        등록일: {new Date(item.added_at).toLocaleDateString('ko-KR')}
                      </p>
                    </div>
                    <button
                      onClick={() => handleRemove(item.stock_code)}
                      className="px-3 py-1 text-sm text-red-600 hover:text-red-800 dark:text-red-400 dark:hover:text-red-300"
                    >
                      삭제
                    </button>
                  </div>
                ))}
                <div className="p-4 text-center">
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
