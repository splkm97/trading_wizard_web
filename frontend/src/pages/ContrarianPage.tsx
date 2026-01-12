/**
 * ContrarianPage - MACD/RSI Contrarian Strategy Page
 *
 * Displays contrarian buy signals based on RSI oversold conditions
 * combined with MACD golden cross patterns.
 */

import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { ContrarianPanel } from '../components/contrarian';
import { Button, DatePicker } from '../components/common';

// Helper to get today's date in YYYY-MM-DD format
function getTodayString(): string {
  const today = new Date();
  return today.toISOString().split('T')[0];
}

export function ContrarianPage() {
  const navigate = useNavigate();
  const [scanDate, setScanDate] = useState<string>(getTodayString());

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Header */}
      <header className="bg-white shadow-sm">
        <div className="max-w-6xl mx-auto px-4 py-4 flex items-center justify-between">
          <h1 className="text-xl font-bold text-gray-800">MACD/RSI 역추세 전략</h1>
          <Button variant="secondary" onClick={() => navigate('/dashboard')}>
            ← 대시보드
          </Button>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-6xl mx-auto px-4 py-8">
        {/* Strategy Description */}
        <div className="mb-6">
          <p className="text-gray-600 text-lg">
            RSI 과매도와 MACD 골든크로스를 결합한 역추세 매수 신호를 제공합니다.
          </p>
        </div>

        {/* Date Picker Section */}
        <div className="mb-6 p-4 bg-white rounded-lg shadow-sm">
          <div className="flex flex-col sm:flex-row sm:items-center gap-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-full bg-purple-100 flex items-center justify-center shrink-0">
                <svg
                  className="w-5 h-5 text-purple-600"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"
                  />
                </svg>
              </div>
              <div>
                <h3 className="font-medium text-gray-900">신호 조회 날짜</h3>
                <p className="text-xs text-gray-500">과거 날짜의 신호를 확인할 수 있습니다</p>
              </div>
            </div>
            <div className="flex-1 max-w-xs">
              <DatePicker
                value={scanDate}
                onChange={(e) => setScanDate(e.target.value)}
                max={getTodayString()}
              />
            </div>
            {scanDate !== getTodayString() && (
              <button
                onClick={() => setScanDate(getTodayString())}
                className="text-sm text-purple-600 hover:text-purple-800 font-medium transition-colors"
              >
                오늘로 돌아가기
              </button>
            )}
          </div>
        </div>

        {/* Strategy Switcher */}
        <div className="mb-8 p-4 bg-white rounded-lg shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-gray-700">다른 전략 보기:</span>
            <Link
              to="/trade"
              className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-blue-700 bg-blue-50 rounded-lg hover:bg-blue-100 transition-colors"
            >
              <svg
                className="w-4 h-4"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6"
                />
              </svg>
              볼린저 밴드 전략
              <svg
                className="w-4 h-4"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9 5l7 7-7 7"
                />
              </svg>
            </Link>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Column - Strategy Explanation Cards */}
          <div className="lg:col-span-1 space-y-4">
            {/* RSI Explanation Card */}
            <div className="bg-white rounded-lg shadow-sm p-5">
              <div className="flex items-center gap-3 mb-3">
                <div className="w-10 h-10 rounded-full bg-purple-100 flex items-center justify-center">
                  <svg
                    className="w-5 h-5 text-purple-600"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M13 17h8m0 0V9m0 8l-8-8-4 4-6-6"
                    />
                  </svg>
                </div>
                <h3 className="font-semibold text-gray-900">RSI 과매도란?</h3>
              </div>
              <p className="text-sm text-gray-600 leading-relaxed">
                RSI(상대강도지수)가 <span className="font-medium text-purple-700">30 이하</span>일 때
                과매도 상태로 판단합니다. 이는 주가가 단기간에 급락하여 반등 가능성이 높아진
                상태를 의미합니다.
              </p>
              <div className="mt-3 p-2 bg-purple-50 rounded text-xs text-purple-700">
                기본 설정: RSI ≤ 30 (14일 기준)
              </div>
            </div>

            {/* MACD Explanation Card */}
            <div className="bg-white rounded-lg shadow-sm p-5">
              <div className="flex items-center gap-3 mb-3">
                <div className="w-10 h-10 rounded-full bg-green-100 flex items-center justify-center">
                  <svg
                    className="w-5 h-5 text-green-600"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
                    />
                  </svg>
                </div>
                <h3 className="font-semibold text-gray-900">MACD 골든크로스란?</h3>
              </div>
              <p className="text-sm text-gray-600 leading-relaxed">
                MACD 선이 <span className="font-medium text-green-700">시그널 선을 상향 돌파</span>할 때
                발생합니다. 이는 하락 추세가 상승 추세로 전환되는 초기 신호로 해석됩니다.
              </p>
              <div className="mt-3 p-2 bg-green-50 rounded text-xs text-green-700">
                기본 설정: MACD(12, 26, 9)
              </div>
            </div>

            {/* Contrarian Strategy Explanation Card */}
            <div className="bg-white rounded-lg shadow-sm p-5">
              <div className="flex items-center gap-3 mb-3">
                <div className="w-10 h-10 rounded-full bg-blue-100 flex items-center justify-center">
                  <svg
                    className="w-5 h-5 text-blue-600"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4"
                    />
                  </svg>
                </div>
                <h3 className="font-semibold text-gray-900">역추세 전략이란?</h3>
              </div>
              <p className="text-sm text-gray-600 leading-relaxed">
                다수의 투자자들이 <span className="font-medium text-blue-700">공포에 매도</span>할 때
                오히려 매수 기회를 포착하는 전략입니다. RSI 과매도와 MACD 골든크로스가
                동시에 발생하면 반등 확률이 높아집니다.
              </p>
              <div className="mt-3 p-2 bg-blue-50 rounded text-xs text-blue-700">
                "남들이 팔 때 사라" - 워런 버핏
              </div>
            </div>

            {/* Risk Warning Card */}
            <div className="bg-amber-50 border border-amber-200 rounded-lg p-4">
              <div className="flex items-start gap-2">
                <svg
                  className="w-5 h-5 text-amber-600 mt-0.5 shrink-0"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
                  />
                </svg>
                <div>
                  <h4 className="font-medium text-amber-800 text-sm mb-1">투자 유의사항</h4>
                  <p className="text-xs text-amber-700 leading-relaxed">
                    역추세 전략은 하락 추세가 지속될 경우 손실이 커질 수 있습니다.
                    반드시 손절매 기준을 설정하고, 분산 투자를 권장합니다.
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* Right Column - Contrarian Panel */}
          <div className="lg:col-span-2">
            <ContrarianPanel scanDate={scanDate} />
          </div>
        </div>
      </main>
    </div>
  );
}

export default ContrarianPage;
