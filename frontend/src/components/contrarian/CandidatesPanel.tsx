/**
 * CandidatesPanel - Displays MACD/RSI contrarian pre-signal candidates
 *
 * Shows stocks that are approaching signal conditions but haven't triggered yet.
 */

import { useState, useEffect } from 'react';
import { Card } from '../common';
import { getContrarianCandidates } from '../../services/api';
import type {
  ContrarianCandidatesResponse,
  ContrarianCandidate,
  ContrarianCandidateStage,
} from '../../types';

interface CandidatesPanelProps {
  maxResults?: number;
  scanDate?: string;
  onSelectCandidate?: (candidate: ContrarianCandidate) => void;
}

// Stage display configuration
const STAGE_CONFIG: Record<
  ContrarianCandidateStage,
  { label: string; color: string; bgColor: string; icon: string }
> = {
  RSI_OVERSOLD_WAITING: {
    label: 'RSI 과매도 (MACD 대기)',
    color: 'text-orange-700',
    bgColor: 'bg-orange-100',
    icon: '⏳',
  },
  MACD_CROSSED_RSI_RECOVERING: {
    label: 'MACD 돌파 (RSI 회복중)',
    color: 'text-green-700',
    bgColor: 'bg-green-100',
    icon: '📈',
  },
  APPROACHING: {
    label: '신호 접근 중',
    color: 'text-yellow-700',
    bgColor: 'bg-yellow-100',
    icon: '👀',
  },
};

export function CandidatesPanel({
  maxResults = 20,
  scanDate,
  onSelectCandidate,
}: CandidatesPanelProps) {
  const [data, setData] = useState<ContrarianCandidatesResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedCode, setSelectedCode] = useState<string | null>(null);

  const fetchCandidates = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await getContrarianCandidates(maxResults, scanDate);
      setData(response);
    } catch (err) {
      const apiError = err as { detail?: string; message?: string };
      setError(
        apiError.detail || apiError.message || '후보군을 불러오는데 실패했습니다.'
      );
      console.error('Failed to fetch contrarian candidates:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCandidates();
  }, [maxResults, scanDate]);

  const handleCandidateClick = (candidate: ContrarianCandidate) => {
    setSelectedCode(candidate.stock_code);
    if (onSelectCandidate) {
      onSelectCandidate(candidate);
    }
  };

  // Loading state
  if (loading) {
    return (
      <Card title="예비 신호 (후보군)">
        <div className="animate-pulse space-y-4">
          <div className="h-4 bg-gray-200 rounded w-3/4" />
          <div className="h-24 bg-gray-200 rounded" />
          <div className="h-24 bg-gray-200 rounded" />
          <div className="h-24 bg-gray-200 rounded" />
        </div>
        <p className="text-sm text-gray-500 mt-4">
          신호 조건 접근 중인 종목 스캔 중...
        </p>
      </Card>
    );
  }

  // Error state
  if (error) {
    return (
      <Card title="예비 신호 (후보군)">
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
            onClick={fetchCandidates}
            className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors"
          >
            다시 시도
          </button>
        </div>
      </Card>
    );
  }

  const candidates = data?.candidates || [];
  const scannedCount = data?.scanned_count || 0;
  const candidateCount = data?.candidate_count || 0;

  // Group candidates by stage
  const groupedCandidates = candidates.reduce(
    (acc, candidate) => {
      const stage = candidate.signal_stage;
      if (!acc[stage]) {
        acc[stage] = [];
      }
      acc[stage].push(candidate);
      return acc;
    },
    {} as Record<ContrarianCandidateStage, ContrarianCandidate[]>
  );

  return (
    <Card title="예비 신호 (후보군)">
      <div className="space-y-4">
        {/* Info Banner */}
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
          <div className="flex items-start gap-2">
            <span className="text-lg">💡</span>
            <div className="text-sm text-blue-700">
              <p className="font-medium mb-1">예비 신호란?</p>
              <p className="text-xs text-blue-600">
                아직 매수 조건을 충족하지 않았지만, 곧 신호가 발생할 가능성이 있는 종목들입니다.
                관심 종목으로 등록하고 모니터링하세요.
              </p>
            </div>
          </div>
        </div>

        {/* Summary Stats */}
        <div className="flex justify-between items-center text-sm text-gray-500 pb-3 border-b border-gray-200">
          <span>스캔: {scannedCount}개</span>
          <span>후보군: {candidateCount}개</span>
          <button
            onClick={fetchCandidates}
            className="text-purple-600 hover:text-purple-800 font-medium transition-colors"
          >
            새로고침
          </button>
        </div>

        {/* Empty state */}
        {candidates.length === 0 ? (
          <div className="text-center py-8">
            <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-gray-100 flex items-center justify-center">
              <span className="text-2xl">🔍</span>
            </div>
            <p className="text-gray-600 font-medium mb-1">예비 신호가 없습니다</p>
            <p className="text-sm text-gray-400">
              신호 조건에 접근 중인 종목이 현재 감지되지 않았습니다.
            </p>
          </div>
        ) : (
          /* Candidates grouped by stage */
          <div className="space-y-6">
            {/* Stage 1: RSI Oversold Waiting */}
            {groupedCandidates.RSI_OVERSOLD_WAITING?.length > 0 && (
              <CandidateGroup
                stage="RSI_OVERSOLD_WAITING"
                candidates={groupedCandidates.RSI_OVERSOLD_WAITING}
                selectedCode={selectedCode}
                onSelect={handleCandidateClick}
              />
            )}

            {/* Stage 2: MACD Crossed RSI Recovering */}
            {groupedCandidates.MACD_CROSSED_RSI_RECOVERING?.length > 0 && (
              <CandidateGroup
                stage="MACD_CROSSED_RSI_RECOVERING"
                candidates={groupedCandidates.MACD_CROSSED_RSI_RECOVERING}
                selectedCode={selectedCode}
                onSelect={handleCandidateClick}
              />
            )}

            {/* Stage 3: Approaching */}
            {groupedCandidates.APPROACHING?.length > 0 && (
              <CandidateGroup
                stage="APPROACHING"
                candidates={groupedCandidates.APPROACHING}
                selectedCode={selectedCode}
                onSelect={handleCandidateClick}
              />
            )}
          </div>
        )}
      </div>
    </Card>
  );
}

// Candidate Group Component
interface CandidateGroupProps {
  stage: ContrarianCandidateStage;
  candidates: ContrarianCandidate[];
  selectedCode: string | null;
  onSelect: (candidate: ContrarianCandidate) => void;
}

function CandidateGroup({
  stage,
  candidates,
  selectedCode,
  onSelect,
}: CandidateGroupProps) {
  const config = STAGE_CONFIG[stage];

  return (
    <div>
      <div className="flex items-center gap-2 mb-3">
        <span
          className={`${config.bgColor} ${config.color} px-2.5 py-1 rounded-lg text-xs font-medium`}
        >
          {config.icon} {config.label}
        </span>
        <span className="text-sm text-gray-500">{candidates.length}개</span>
      </div>
      <div className="grid gap-3">
        {candidates.map((candidate) => (
          <CandidateCard
            key={candidate.stock_code}
            candidate={candidate}
            isSelected={selectedCode === candidate.stock_code}
            onClick={() => onSelect(candidate)}
          />
        ))}
      </div>
    </div>
  );
}

// Candidate Card Component
interface CandidateCardProps {
  candidate: ContrarianCandidate;
  isSelected: boolean;
  onClick: () => void;
}

function CandidateCard({ candidate, isSelected, onClick }: CandidateCardProps) {
  const config = STAGE_CONFIG[candidate.signal_stage];

  return (
    <div
      className={`p-4 rounded-lg border cursor-pointer transition-all ${
        isSelected
          ? 'border-purple-400 bg-purple-50 shadow-md'
          : 'border-gray-200 bg-white hover:border-gray-300 hover:shadow-sm'
      }`}
      onClick={onClick}
    >
      <div className="flex justify-between items-start mb-2">
        <div>
          <div className="flex items-center gap-2">
            <h4 className="font-semibold text-gray-900">{candidate.stock_name}</h4>
            <span className="text-xs text-gray-400">{candidate.stock_code}</span>
          </div>
          <p className="text-lg font-bold text-gray-800 mt-1">
            ₩{candidate.current_price.toLocaleString()}
          </p>
        </div>
        <div className="text-right">
          <div
            className={`inline-flex items-center px-2 py-1 rounded text-xs font-medium ${config.bgColor} ${config.color}`}
          >
            {config.icon}
          </div>
          <p className="text-xs text-gray-500 mt-1">
            신뢰도 {candidate.confidence_score.toFixed(0)}점
          </p>
        </div>
      </div>

      {/* Indicators */}
      <div className="grid grid-cols-2 gap-2 text-xs mb-2">
        <div className="bg-gray-50 rounded px-2 py-1">
          <span className="text-gray-500">RSI: </span>
          <span
            className={`font-medium ${
              candidate.indicators.rsi <= 30 ? 'text-purple-600' : 'text-gray-700'
            }`}
          >
            {candidate.indicators.rsi.toFixed(1)}
          </span>
        </div>
        <div className="bg-gray-50 rounded px-2 py-1">
          <span className="text-gray-500">MACD H: </span>
          <span
            className={`font-medium ${
              candidate.indicators.macd_histogram >= 0
                ? 'text-green-600'
                : 'text-red-600'
            }`}
          >
            {candidate.indicators.macd_histogram.toFixed(2)}
          </span>
        </div>
      </div>

      {/* Reason Detail */}
      <p className="text-xs text-gray-600 leading-relaxed">
        {candidate.reason_detail}
      </p>
    </div>
  );
}

export default CandidatesPanel;
