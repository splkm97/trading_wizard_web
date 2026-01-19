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

  const handleRemove = async (stockCode: string) => {
    try {
      await api.delete(`/watchlists/${stockCode}`);
      setWatchlist(watchlist.filter(item => item.stock_code !== stockCode));
    } catch (error) {
      console.error('Failed to remove from watchlist:', error);
    }
  };

  if (loading) {
    return <div className="text-center py-8">로딩 중...</div>;
  }

  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold mb-6">관심 종목 모아보기</h1>
      
      {watchlist.length === 0 ? (
        <Card className="p-8 text-center">
          <p className="text-gray-600">관심 종목이 없습니다.</p>
          <p className="text-gray-600 mt-2">
            Daily Wizard 추천 종목에서 '관심 종목 등록' 버튼을 클릭하여 종목을 추가하세요.
          </p>
        </Card>
      ) : (
        <div className="space-y-4">
          {watchlist.map((item) => (
            <Card key={item.stock_code} className="p-6">
              <div className="flex justify-between items-start">
                <div className="flex-1">
                  <h2 className="text-xl font-bold mb-2">
                    {item.stock_name} ({item.stock_code})
                  </h2>
                  
                  {item.current_price && (
                    <p className="text-lg mb-2">
                      현재가: ₩{item.current_price.close.toLocaleString()}
                    </p>
                  )}
                  
                  {item.indicators && (
                    <div className="grid grid-cols-2 gap-4 mb-4 text-sm">
                      <div>
                        <span className="text-gray-600">RSI:</span>
                        <span className="ml-2 font-medium">{item.indicators.rsi.toFixed(1)}</span>
                      </div>
                      <div>
                        <span className="text-gray-600">MACD:</span>
                        <span className="ml-2 font-medium">{item.indicators.macd.toFixed(2)}</span>
                      </div>
                    </div>
                  )}
                  
                  {item.recommendation_score !== null && (
                    <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-4">
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="text-sm text-gray-600">추천 점수</p>
                          <p className="text-2xl font-bold text-blue-600">
                            {item.recommendation_score} / 100
                          </p>
                        </div>
                        {item.recommendation_reason && (
                          <p className="text-sm text-gray-700 ml-4">
                            {item.recommendation_reason}
                          </p>
                        )}
                      </div>
                    </div>
                  )}
                  
                  <p className="text-sm text-gray-500">
                    등록일: {new Date(item.added_at).toLocaleDateString('ko-KR')}
                  </p>
                </div>
                
                <button
                  onClick={() => handleRemove(item.stock_code)}
                  className="ml-4 px-4 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600 transition-colors"
                >
                  삭제
                </button>
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}