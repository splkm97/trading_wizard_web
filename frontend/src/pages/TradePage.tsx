import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { TradeInputForm, RecommendationsPanel } from '../components/trade';
import { Button } from '../components/common';

interface SelectedRecommendation {
  stock_code: string;
  stock_name: string;
  quantity: number;
  price: number;
  reason?: string;
}

export default function TradePage() {
  const navigate = useNavigate();
  const [selectedRec, setSelectedRec] = useState<SelectedRecommendation | null>(
    null
  );

  const handleTradeSuccess = () => {
    // Clear selection after successful trade
    setSelectedRec(null);
  };

  const handleSelectRecommendation = (rec: {
    stock_code: string;
    stock_name: string;
    recommended_price: number;
    quantity: number;
    reason: string;
  }) => {
    setSelectedRec({
      stock_code: rec.stock_code,
      stock_name: rec.stock_name,
      quantity: rec.quantity,
      price: rec.recommended_price,
      reason: rec.reason,
    });

    // Scroll to form on mobile
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Header */}
      <header className="bg-white shadow-sm">
        <div className="max-w-6xl mx-auto px-4 py-4 flex items-center justify-between">
          <h1 className="text-xl font-bold text-gray-800">거래 입력</h1>
          <Button variant="secondary" onClick={() => navigate('/dashboard')}>
            ← 대시보드
          </Button>
        </div>
      </header>

      {/* Main Content - Two Column Layout */}
      <main className="max-w-6xl mx-auto px-4 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Left Column - Trade Form */}
          <div>
            <TradeInputForm
              onSuccess={handleTradeSuccess}
              initialValues={selectedRec}
            />

            <div className="mt-4 text-center text-sm text-gray-500">
              <p>거래 입력 후 포트폴리오에 자동 반영됩니다.</p>
              <p className="mt-1">매수: 현금 차감, 포지션 추가</p>
              <p>매도: 현금 증가, 실현손익 계산</p>
            </div>
          </div>

          {/* Right Column - Recommendations */}
          <div>
            <RecommendationsPanel
              onSelectRecommendation={handleSelectRecommendation}
            />

            <div className="mt-4 p-4 bg-blue-50 rounded-lg text-sm text-blue-800">
              <p className="font-medium mb-1">Daily Wizard 전략</p>
              <p>
                볼린저 밴드 스퀴즈 브레이크아웃 전략을 기반으로
                KOSPI Top 100 종목을 스캔합니다.
              </p>
              <ul className="mt-2 list-disc list-inside text-xs">
                <li>볼린저 밴드 상단 돌파 시 매수 신호</li>
                <li>RSI, MACD, 거래량으로 신뢰도 산정</li>
                <li>포지션당 최대 10% 자금 배분</li>
              </ul>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
