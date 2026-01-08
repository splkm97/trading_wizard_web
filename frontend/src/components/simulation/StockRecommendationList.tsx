/**
 * Stock Recommendation List - Display recommended stocks for current turn
 */

import { Card } from '../common/Card';
import type { StockRecommendation } from '../../types/simulation';

interface StockRecommendationListProps {
  recommendations: StockRecommendation[];
  selectedStockCode: string | null;
  onSelectStock: (stockCode: string) => void;
  isLoading?: boolean;
}

export function StockRecommendationList({
  recommendations,
  selectedStockCode,
  onSelectStock,
  isLoading = false,
}: StockRecommendationListProps) {
  const sortedRecommendations = [...recommendations].sort(
    (a, b) => b.confidence_score - a.confidence_score
  );

  const getScoreColor = (score: number) => {
    if (score >= 70) return 'text-green-600 bg-green-50 border-green-200';
    if (score >= 55) return 'text-amber-600 bg-amber-50 border-amber-200';
    return 'text-gray-600 bg-gray-50 border-gray-200';
  };

  const getScoreBarWidth = (score: number) => {
    return `${Math.min(100, score)}%`;
  };

  if (isLoading) {
    return (
      <Card className="h-full">
        <div className="p-4 border-b border-gray-100">
          <h3 className="font-semibold text-gray-900">오늘의 추천 종목</h3>
        </div>
        <div className="p-6 flex flex-col items-center justify-center h-64">
          <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-primary-600 mb-4" />
          <p className="text-sm text-gray-500">추천 종목 분석 중...</p>
        </div>
      </Card>
    );
  }

  if (sortedRecommendations.length === 0) {
    return (
      <Card className="h-full">
        <div className="p-4 border-b border-gray-100">
          <h3 className="font-semibold text-gray-900">오늘의 추천 종목</h3>
        </div>
        <div className="p-8 flex flex-col items-center justify-center text-center h-64">
          <div className="w-16 h-16 rounded-full bg-gray-100 flex items-center justify-center mb-4">
            <svg className="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <p className="text-gray-600 font-medium mb-1">오늘은 추천 종목이 없습니다</p>
          <p className="text-sm text-gray-400">
            시장 상황에 따라 매수 신호가 발생하지 않을 수 있습니다.<br />
            다음 턴으로 진행해보세요.
          </p>
        </div>
      </Card>
    );
  }

  return (
    <Card className="h-full flex flex-col">
      <div className="p-4 border-b border-gray-100 flex items-center justify-between">
        <h3 className="font-semibold text-gray-900">오늘의 추천 종목</h3>
        <span className="text-sm text-gray-500">{sortedRecommendations.length}개</span>
      </div>
      
      <div className="flex-1 overflow-y-auto">
        <ul className="divide-y divide-gray-100">
          {sortedRecommendations.map((rec) => {
            const isSelected = selectedStockCode === rec.stock_code;
            const scoreColorClass = getScoreColor(rec.confidence_score);
            
            return (
              <li key={rec.stock_code}>
                <button
                  onClick={() => onSelectStock(rec.stock_code)}
                  className={`w-full px-4 py-3 text-left transition-all hover:bg-gray-50 ${
                    isSelected ? 'bg-primary-50 border-l-4 border-l-primary-500' : ''
                  }`}
                >
                  <div className="flex items-start justify-between mb-2">
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center gap-2">
                        <span className="font-medium text-gray-900 truncate">
                          {rec.stock_name}
                        </span>
                        {rec.is_owned && (
                          <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-primary-100 text-primary-700">
                            보유중
                          </span>
                        )}
                      </div>
                      <span className="text-sm text-gray-500">{rec.stock_code}</span>
                    </div>
                    <span className={`px-2.5 py-1 rounded-lg border text-sm font-bold ${scoreColorClass}`}>
                      {rec.confidence_score}점
                    </span>
                  </div>
                  
                  <div className="relative h-1.5 bg-gray-200 rounded-full overflow-hidden">
                    <div
                      className={`absolute h-full rounded-full transition-all ${
                        rec.confidence_score >= 70 ? 'bg-green-500' :
                        rec.confidence_score >= 55 ? 'bg-amber-500' : 'bg-gray-400'
                      }`}
                      style={{ width: getScoreBarWidth(rec.confidence_score) }}
                    />
                  </div>
                  
                  <div className="mt-2 flex items-center gap-3 text-xs text-gray-500">
                    <span title="볼린저">B:{rec.bollinger_score}</span>
                    <span title="RSI">R:{rec.rsi_score}</span>
                    <span title="MACD">M:{rec.macd_score}</span>
                    <span title="거래량">V:{rec.volume_score}</span>
                  </div>
                </button>
              </li>
            );
          })}
        </ul>
      </div>
    </Card>
  );
}
