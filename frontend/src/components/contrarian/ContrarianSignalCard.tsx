/**
 * ContrarianSignalCard - Displays a contrarian (MACD/RSI) buy signal for a stock
 * T022-T023: Added expandable details section with RSI and MACD visualizations
 */

import { useState } from 'react';
import { ContrarianSignal } from '../../types';

interface ContrarianSignalCardProps {
  signal: ContrarianSignal;
  onClick?: () => void;
  isSelected?: boolean;
}

export function ContrarianSignalCard({
  signal,
  onClick,
  isSelected = false,
}: ContrarianSignalCardProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  const formatKRW = (value: number) => {
    return new Intl.NumberFormat('ko-KR', {
      maximumFractionDigits: 0,
    }).format(value);
  };

  // RSI color based on oversold level
  const getRsiColor = (rsi: number) => {
    if (rsi < 20) return 'text-red-600'; // Extremely oversold
    if (rsi < 30) return 'text-orange-600'; // Oversold
    if (rsi < 40) return 'text-yellow-600'; // Approaching oversold
    return 'text-gray-600'; // Normal
  };

  const getRsiBgColor = (rsi: number) => {
    if (rsi < 20) return 'bg-red-100';
    if (rsi < 30) return 'bg-orange-100';
    if (rsi < 40) return 'bg-yellow-100';
    return 'bg-gray-100';
  };

  // RSI zone description
  const getRsiZoneDescription = (rsi: number) => {
    if (rsi <= 20) return '심각한 과매도';
    if (rsi <= 25) return '강한 과매도';
    if (rsi <= 30) return '과매도';
    if (rsi <= 40) return '약한 과매도';
    if (rsi <= 60) return '중립';
    if (rsi <= 70) return '약한 과매수';
    return '과매수';
  };

  // Confidence score color
  const getConfidenceColor = (score: number) => {
    if (score >= 80) return 'text-green-600';
    if (score >= 60) return 'text-yellow-600';
    return 'text-gray-500';
  };

  const getConfidenceBgColor = (score: number) => {
    if (score >= 80) return 'bg-green-100 border-green-200';
    if (score >= 60) return 'bg-yellow-100 border-yellow-200';
    return 'bg-gray-100 border-gray-200';
  };

  // MACD histogram color
  const getMacdHistogramColor = (histogram: number) => {
    if (histogram > 0) return 'text-green-600';
    if (histogram < 0) return 'text-red-600';
    return 'text-gray-600';
  };

  // MACD cross strength
  const getMacdCrossStrength = (histogram: number, signal_value: number) => {
    if (histogram > Math.abs(signal_value * 0.5)) {
      return { label: '강한 상향 돌파', color: 'bg-green-200 text-green-800' };
    }
    return { label: '상향 돌파', color: 'bg-green-100 text-green-700' };
  };

  const { indicators } = signal;

  const toggleExpanded = (e: React.MouseEvent) => {
    e.stopPropagation();
    setIsExpanded(!isExpanded);
  };

  const macdCross = getMacdCrossStrength(indicators.macd_histogram, indicators.macd_signal);

  return (
    <div
      className={`bg-white rounded-lg shadow-md border transition-all hover:shadow-lg ${
        isSelected ? 'ring-2 ring-primary-500 border-primary-300' : 'border-gray-200'
      } ${onClick ? 'cursor-pointer' : ''}`}
      onClick={onClick}
      role={onClick ? 'button' : undefined}
      tabIndex={onClick ? 0 : undefined}
      onKeyDown={onClick ? (e) => e.key === 'Enter' && onClick() : undefined}
    >
      {/* Header - Stock info and confidence */}
      <div className="px-4 py-3 border-b border-gray-100 flex items-start justify-between">
        <div>
          <div className="flex items-center gap-2">
            <h3 className="font-semibold text-gray-900">{signal.stock_name}</h3>
            <span className="text-sm text-gray-500">{signal.stock_code}</span>
          </div>
          <div className="mt-1 text-lg font-medium text-gray-800">
            {formatKRW(signal.current_price)}원
          </div>
        </div>
        <div className="flex flex-col items-end gap-1">
          <span
            className={`px-2.5 py-1 rounded-lg border text-sm font-bold ${getConfidenceBgColor(signal.confidence_score)} ${getConfidenceColor(signal.confidence_score)}`}
          >
            {signal.confidence_score.toFixed(1)}점
          </span>
          <span className="text-xs text-gray-400">신뢰도</span>
        </div>
      </div>

      {/* Indicators Section */}
      <div className="px-4 py-3">
        {/* RSI Indicator */}
        <div className="mb-3">
          <div className="flex items-center justify-between mb-1">
            <span className="text-sm font-medium text-gray-700">RSI</span>
            <span className={`text-sm font-bold ${getRsiColor(indicators.rsi)}`}>
              {indicators.rsi.toFixed(1)}
            </span>
          </div>
          <div className="relative h-2 bg-gray-200 rounded-full overflow-hidden">
            {/* RSI zones visualization */}
            <div className="absolute inset-0 flex">
              <div className="w-[30%] bg-red-200" title="Oversold zone (0-30)" />
              <div className="w-[40%] bg-gray-200" title="Neutral zone (30-70)" />
              <div className="w-[30%] bg-blue-200" title="Overbought zone (70-100)" />
            </div>
            {/* RSI indicator position */}
            <div
              className={`absolute top-0 h-full w-1 rounded-full ${getRsiBgColor(indicators.rsi).replace('bg-', 'bg-')}`}
              style={{
                left: `${Math.min(100, Math.max(0, indicators.rsi))}%`,
                backgroundColor: indicators.rsi < 30 ? '#dc2626' : indicators.rsi > 70 ? '#2563eb' : '#6b7280',
              }}
            />
          </div>
          <div className="flex justify-between text-xs text-gray-400 mt-0.5">
            <span>과매도</span>
            <span>중립</span>
            <span>과매수</span>
          </div>
        </div>

        {/* MACD Indicators */}
        <div className="grid grid-cols-3 gap-3 text-sm">
          <div className="bg-gray-50 rounded-lg p-2">
            <div className="text-xs text-gray-500 mb-0.5">MACD Line</div>
            <div className={`font-medium ${indicators.macd >= 0 ? 'text-green-600' : 'text-red-600'}`}>
              {indicators.macd.toFixed(2)}
            </div>
          </div>
          <div className="bg-gray-50 rounded-lg p-2">
            <div className="text-xs text-gray-500 mb-0.5">Signal</div>
            <div className={`font-medium ${indicators.macd_signal >= 0 ? 'text-green-600' : 'text-red-600'}`}>
              {indicators.macd_signal.toFixed(2)}
            </div>
          </div>
          <div className="bg-gray-50 rounded-lg p-2">
            <div className="text-xs text-gray-500 mb-0.5">Histogram</div>
            <div className={`font-medium ${getMacdHistogramColor(indicators.macd_histogram)}`}>
              {indicators.macd_histogram > 0 ? '+' : ''}{indicators.macd_histogram.toFixed(2)}
            </div>
          </div>
        </div>

        {/* MACD Visual Indicator */}
        <div className="mt-2 flex items-center gap-2 text-xs">
          <span className="text-gray-500">MACD 상태:</span>
          {indicators.macd > indicators.macd_signal ? (
            <span className={`px-2 py-0.5 rounded font-medium ${macdCross.color}`}>
              {macdCross.label}
            </span>
          ) : (
            <span className="px-2 py-0.5 rounded bg-red-100 text-red-700 font-medium">
              하향 추세
            </span>
          )}
        </div>
      </div>

      {/* Expandable Details Toggle */}
      <div className="px-4 py-2 border-t border-gray-100">
        <button
          onClick={toggleExpanded}
          className="w-full flex items-center justify-center gap-1 text-sm text-gray-500 hover:text-gray-700 transition-colors py-1"
          aria-expanded={isExpanded}
          aria-label={isExpanded ? '상세 정보 접기' : '상세 정보 펼치기'}
        >
          <span>{isExpanded ? '상세 정보 접기' : '상세 정보 보기'}</span>
          <svg
            className={`w-4 h-4 transition-transform duration-200 ${isExpanded ? 'rotate-180' : ''}`}
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </button>
      </div>

      {/* Expandable Details Section */}
      <div
        className={`overflow-hidden transition-all duration-300 ease-in-out ${
          isExpanded ? 'max-h-96 opacity-100' : 'max-h-0 opacity-0'
        }`}
      >
        <div className="px-4 py-3 bg-gradient-to-b from-gray-50 to-white border-t border-gray-100">
          {/* Detailed RSI Explanation */}
          <div className="mb-4">
            <h4 className="text-xs font-semibold text-gray-600 uppercase tracking-wide mb-2">
              RSI 상세 분석
            </h4>
            <div className="bg-white rounded-lg border border-gray-200 p-3">
              {/* Enhanced RSI visualization */}
              <div className="relative h-6 bg-gradient-to-r from-red-300 via-gray-200 to-blue-300 rounded-full overflow-hidden mb-2">
                {/* Zone markers */}
                <div className="absolute inset-0 flex items-center">
                  <div className="absolute left-[20%] h-full w-px bg-red-400" />
                  <div className="absolute left-[30%] h-full w-px bg-gray-400" />
                  <div className="absolute left-[70%] h-full w-px bg-gray-400" />
                  <div className="absolute left-[80%] h-full w-px bg-blue-400" />
                </div>
                {/* RSI position indicator */}
                <div
                  className="absolute top-1/2 -translate-y-1/2 w-4 h-4 rounded-full bg-white border-2 shadow-md transition-all duration-300"
                  style={{
                    left: `calc(${Math.min(100, Math.max(0, indicators.rsi))}% - 8px)`,
                    borderColor: indicators.rsi <= 30 ? '#dc2626' : indicators.rsi >= 70 ? '#2563eb' : '#6b7280',
                  }}
                />
              </div>
              <div className="flex justify-between text-xs text-gray-500 mb-2">
                <span>0</span>
                <span>20</span>
                <span>30</span>
                <span>70</span>
                <span>80</span>
                <span>100</span>
              </div>
              <div className={`text-sm font-medium ${getRsiColor(indicators.rsi)} flex items-center gap-2`}>
                <span className={`inline-block w-2 h-2 rounded-full ${getRsiBgColor(indicators.rsi).replace('100', '500')}`} />
                현재 RSI {indicators.rsi.toFixed(1)}: {getRsiZoneDescription(indicators.rsi)} 구간
              </div>
            </div>
          </div>

          {/* Detailed MACD Explanation */}
          <div className="mb-4">
            <h4 className="text-xs font-semibold text-gray-600 uppercase tracking-wide mb-2">
              MACD 골든크로스 분석
            </h4>
            <div className="bg-white rounded-lg border border-gray-200 p-3">
              {/* MACD cross visualization */}
              <div className="flex items-center justify-center gap-4 mb-3">
                <div className="text-center">
                  <div className="text-xs text-gray-500 mb-1">MACD</div>
                  <div className={`text-lg font-bold ${indicators.macd >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                    {indicators.macd.toFixed(2)}
                  </div>
                </div>
                <div className="flex flex-col items-center">
                  {indicators.macd > indicators.macd_signal ? (
                    <>
                      <svg className="w-8 h-8 text-green-500" fill="currentColor" viewBox="0 0 24 24">
                        <path d="M7 14l5-5 5 5H7z" />
                      </svg>
                      <span className="text-xs text-green-600 font-medium">상향 돌파</span>
                    </>
                  ) : (
                    <>
                      <svg className="w-8 h-8 text-red-500" fill="currentColor" viewBox="0 0 24 24">
                        <path d="M7 10l5 5 5-5H7z" />
                      </svg>
                      <span className="text-xs text-red-600 font-medium">하향</span>
                    </>
                  )}
                </div>
                <div className="text-center">
                  <div className="text-xs text-gray-500 mb-1">Signal</div>
                  <div className={`text-lg font-bold ${indicators.macd_signal >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                    {indicators.macd_signal.toFixed(2)}
                  </div>
                </div>
              </div>
              {/* Histogram bar */}
              <div className="flex items-center gap-2">
                <span className="text-xs text-gray-500 w-16">Histogram:</span>
                <div className="flex-1 h-4 bg-gray-100 rounded relative overflow-hidden">
                  <div
                    className={`absolute top-0 h-full transition-all duration-300 ${
                      indicators.macd_histogram >= 0 ? 'bg-green-400 left-1/2' : 'bg-red-400 right-1/2'
                    }`}
                    style={{
                      width: `${Math.min(50, Math.abs(indicators.macd_histogram) * 5)}%`,
                    }}
                  />
                  <div className="absolute left-1/2 top-0 h-full w-px bg-gray-400" />
                </div>
                <span className={`text-xs font-medium w-16 text-right ${getMacdHistogramColor(indicators.macd_histogram)}`}>
                  {indicators.macd_histogram > 0 ? '+' : ''}{indicators.macd_histogram.toFixed(2)}
                </span>
              </div>
            </div>
          </div>

          {/* Reason Detail Text */}
          {indicators.reason_detail && (
            <div className="bg-blue-50 rounded-lg border border-blue-100 p-3">
              <h4 className="text-xs font-semibold text-blue-700 uppercase tracking-wide mb-2 flex items-center gap-1">
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                AI 분석 요약
              </h4>
              <p className="text-sm text-blue-800 leading-relaxed">
                {indicators.reason_detail}
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Reason Section */}
      <div className="px-4 py-3 bg-gray-50 rounded-b-lg border-t border-gray-100">
        <div className="text-xs text-gray-500 mb-1">신호 근거</div>
        <p className="text-sm text-gray-700 leading-relaxed">{signal.reason}</p>
      </div>
    </div>
  );
}
