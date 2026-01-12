/**
 * ContrarianPanel - Displays MACD/RSI contrarian buy signals
 *
 * This component fetches and displays contrarian signals based on
 * RSI oversold conditions combined with MACD golden cross patterns.
 */

import { useState, useEffect } from 'react';
import { Card } from '../common';
import { getContrarianSignals } from '../../services/api';
import type {
  ContrarianSignalsResponse,
  AppliedContrarianSettings,
  ContrarianSignal,
} from '../../types';
import { ContrarianSignalCard } from './ContrarianSignalCard';

interface ContrarianPanelProps {
  maxResults?: number;
  scanDate?: string; // YYYY-MM-DD format
  onSelectSignal?: (signal: ContrarianSignal) => void;
}

export function ContrarianPanel({
  maxResults = 10,
  scanDate,
  onSelectSignal,
}: ContrarianPanelProps) {
  const [data, setData] = useState<ContrarianSignalsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showSettings, setShowSettings] = useState(false);
  const [selectedSignalCode, setSelectedSignalCode] = useState<string | null>(null);

  const fetchSignals = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await getContrarianSignals(maxResults, scanDate);
      setData(response);
    } catch (err) {
      const apiError = err as { detail?: string; message?: string };
      setError(apiError.detail || apiError.message || '역추세 신호를 불러오는데 실패했습니다.');
      console.error('Failed to fetch contrarian signals:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSignals();
  }, [maxResults, scanDate]);

  const handleSignalClick = (signal: ContrarianSignal) => {
    setSelectedSignalCode(signal.stock_code);
    if (onSelectSignal) {
      onSelectSignal(signal);
    }
  };

  // Loading state
  if (loading) {
    return (
      <Card title="역추세 매수 신호 (MACD/RSI)">
        <div className="animate-pulse space-y-4">
          <div className="h-4 bg-gray-200 rounded w-3/4" />
          <div className="h-32 bg-gray-200 rounded" />
          <div className="h-32 bg-gray-200 rounded" />
          <div className="h-32 bg-gray-200 rounded" />
        </div>
        <p className="text-sm text-gray-500 mt-4">
          KOSPI Top 100 역추세 신호 스캔 중...
        </p>
      </Card>
    );
  }

  // Error state
  if (error) {
    return (
      <Card title="역추세 매수 신호 (MACD/RSI)">
        <div className="text-center py-6">
          <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-red-100 flex items-center justify-center">
            <svg
              className="w-8 h-8 text-red-500"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
          </div>
          <p className="text-red-500 mb-4">{error}</p>
          <button
            onClick={fetchSignals}
            className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors"
          >
            다시 시도
          </button>
        </div>
      </Card>
    );
  }

  // Data loaded
  const signals = data?.signals || [];
  const appliedSettings = data?.applied_settings;
  const scannedCount = data?.scanned_count || 0;
  const signalCount = data?.signal_count || 0;

  return (
    <Card title="역추세 매수 신호 (MACD/RSI)">
      <div className="space-y-4">
        {/* Applied Settings Summary */}
        {appliedSettings && (
          <AppliedSettingsSection
            settings={appliedSettings}
            showDetails={showSettings}
            onToggle={() => setShowSettings(!showSettings)}
          />
        )}

        {/* Summary Stats */}
        <div className="flex justify-between items-center text-sm text-gray-500 pb-3 border-b border-gray-200">
          <span>스캔: {scannedCount}개</span>
          <span>감지된 신호: {signalCount}개</span>
          <button
            onClick={fetchSignals}
            className="text-purple-600 hover:text-purple-800 font-medium transition-colors"
          >
            새로고침
          </button>
        </div>

        {/* Empty state */}
        {signals.length === 0 ? (
          <div className="text-center py-8">
            <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-gray-100 flex items-center justify-center">
              <svg
                className="w-8 h-8 text-gray-400"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={1.5}
                  d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
                />
              </svg>
            </div>
            <p className="text-gray-600 font-medium mb-1">역추세 매수 신호가 없습니다</p>
            <p className="text-sm text-gray-400">
              RSI 과매도 + MACD 골든크로스 조건을 만족하는 종목이<br />
              현재 감지되지 않았습니다.
            </p>
          </div>
        ) : (
          /* Signal list */
          <div className="space-y-4">
            <div className="flex items-center gap-2">
              <span className="bg-purple-100 text-purple-800 px-2.5 py-1 rounded-lg text-xs font-medium">
                매수 신호
              </span>
              <span className="text-sm text-gray-600">
                {signals.length}개 종목 감지됨
              </span>
            </div>
            <div className="grid gap-4">
              {signals.map((signal) => (
                <ContrarianSignalCard
                  key={signal.stock_code}
                  signal={signal}
                  isSelected={selectedSignalCode === signal.stock_code}
                  onClick={() => handleSignalClick(signal)}
                />
              ))}
            </div>
          </div>
        )}
      </div>
    </Card>
  );
}

// Applied Settings Section Component
interface AppliedSettingsSectionProps {
  settings: AppliedContrarianSettings;
  showDetails: boolean;
  onToggle: () => void;
}

function AppliedSettingsSection({
  settings,
  showDetails,
  onToggle,
}: AppliedSettingsSectionProps) {
  return (
    <div className="bg-purple-50 rounded-lg p-3 border border-purple-200">
      <div
        className="flex justify-between items-center cursor-pointer"
        onClick={onToggle}
      >
        <div className="flex items-center gap-2">
          <span className="text-xs font-medium text-gray-700">적용된 설정</span>
          <span className="text-xs px-2 py-0.5 bg-purple-100 text-purple-700 rounded">
            MACD/RSI 전략
          </span>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs text-gray-500">
            RSI ≤{settings.rsi_threshold} | 신뢰도 ≥{settings.confidence_threshold}점
          </span>
          <span className="text-gray-400 text-xs">
            {showDetails ? '▲' : '▼'}
          </span>
        </div>
      </div>

      {showDetails && (
        <div className="mt-3 pt-3 border-t border-purple-200 grid grid-cols-2 gap-x-4 gap-y-2 text-xs">
          <div className="col-span-2 text-gray-500 font-medium mb-1">RSI 설정</div>
          <div className="flex justify-between">
            <span className="text-gray-500">RSI 기간:</span>
            <span className="text-gray-700">{settings.rsi_period}일</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-500">RSI 임계값:</span>
            <span className="text-gray-700">{settings.rsi_threshold}</span>
          </div>

          <div className="col-span-2 text-gray-500 font-medium mt-2 mb-1">MACD 설정</div>
          <div className="flex justify-between">
            <span className="text-gray-500">Fast 기간:</span>
            <span className="text-gray-700">{settings.macd_fast_period}일</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-500">Slow 기간:</span>
            <span className="text-gray-700">{settings.macd_slow_period}일</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-500">Signal 기간:</span>
            <span className="text-gray-700">{settings.macd_signal_period}일</span>
          </div>

          <div className="col-span-2 text-gray-500 font-medium mt-2 mb-1">신뢰도</div>
          <div className="flex justify-between col-span-2">
            <span className="text-gray-500">신뢰도 임계값:</span>
            <span className="text-gray-700">{settings.confidence_threshold}점</span>
          </div>

          <div className="col-span-2 mt-2 pt-2 border-t border-purple-200">
            <a
              href="/settings?tab=contrarian"
              className="text-purple-600 hover:text-purple-800 text-xs"
            >
              MACD/RSI 설정 변경하기 →
            </a>
          </div>
        </div>
      )}
    </div>
  );
}

export default ContrarianPanel;
