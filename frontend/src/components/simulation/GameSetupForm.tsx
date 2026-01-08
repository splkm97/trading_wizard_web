/**
 * Game Setup Form - Create new simulation session
 */

import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card } from '../common/Card';
import { Button } from '../common/Button';
import { Input } from '../common/Input';
import { createSession } from '../../services/simulation';
import type { CreateSessionRequest } from '../../types/simulation';

export function GameSetupForm() {
  const navigate = useNavigate();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const [formData, setFormData] = useState<CreateSessionRequest>({
    name: '',
    start_date: '2024-01-02',
    end_date: '2024-12-31',
    initial_capital: 100000000,
  });

  const [validationError, setValidationError] = useState<string | null>(null);

  const handleChange = (field: keyof CreateSessionRequest, value: string | number) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
    setValidationError(null);
    setError(null);
  };

  const validateDates = (): boolean => {
    const start = new Date(formData.start_date);
    const end = new Date(formData.end_date);
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    const minDate = new Date('2015-01-01');
    
    if (start >= end) {
      setValidationError('종료일은 시작일보다 이후여야 합니다');
      return false;
    }

    if (end > today) {
      setValidationError('종료일은 오늘 이전이어야 합니다');
      return false;
    }

    if (start < minDate) {
      setValidationError('시작일은 2015년 1월 1일 이후여야 합니다');
      return false;
    }
    
    const diffDays = Math.ceil((end.getTime() - start.getTime()) / (1000 * 60 * 60 * 24));
    if (diffDays < 7) {
      setValidationError('최소 7일 이상의 기간을 설정해주세요');
      return false;
    }
    
    return true;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validateDates()) {
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const session = await createSession({
        name: formData.name || undefined,
        start_date: formData.start_date,
        end_date: formData.end_date,
        initial_capital: formData.initial_capital,
      });
      
      navigate(`/simulation/${session.id}`);
    } catch (err: unknown) {
      const message = err && typeof err === 'object' && 'detail' in err
        ? (err as { detail: string }).detail
        : '게임 세션 생성에 실패했습니다.';
      setError(message);
    } finally {
      setIsLoading(false);
    }
  };

  const formatCurrency = (value: number) =>
    new Intl.NumberFormat('ko-KR').format(value);

  return (
    <Card className="max-w-lg mx-auto">
      <div className="p-6">
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-gradient-to-br from-primary-500 to-primary-700 mb-4">
            <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
            </svg>
          </div>
          <h2 className="text-2xl font-bold text-gray-900">새 게임 시작</h2>
          <p className="text-gray-500 mt-2">
            볼린저 밴드 전략으로 가상 주식 투자를 시뮬레이션합니다
          </p>
        </div>

        {error && (
          <div className="mb-6 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm">
            {error}
          </div>
        )}

        {validationError && (
          <div className="mb-6 bg-amber-50 border border-amber-200 text-amber-700 px-4 py-3 rounded-lg text-sm">
            {validationError}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-5">
          <Input
            label="게임 이름 (선택)"
            placeholder="예: 2024년 상반기 시뮬레이션"
            value={formData.name || ''}
            onChange={(e) => handleChange('name', e.target.value)}
            maxLength={100}
          />

          <div className="grid grid-cols-2 gap-4">
            <Input
              label="시작일"
              type="date"
              value={formData.start_date}
              onChange={(e) => handleChange('start_date', e.target.value)}
              required
            />
            <Input
              label="종료일"
              type="date"
              value={formData.end_date}
              onChange={(e) => handleChange('end_date', e.target.value)}
              required
            />
          </div>

          <div>
            <Input
              label="초기 자본금 (KRW)"
              type="number"
              value={formData.initial_capital}
              onChange={(e) => handleChange('initial_capital', Number(e.target.value))}
              min={10000000}
              step={10000000}
              required
            />
            <p className="mt-1 text-sm text-gray-500">
              {formatCurrency(formData.initial_capital || 0)}원
            </p>
          </div>

          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <h4 className="font-medium text-blue-800 mb-2">게임 규칙</h4>
            <ul className="text-sm text-blue-700 space-y-1">
              <li>• 매 턴마다 추천 종목 리스트가 제공됩니다</li>
              <li>• 종목별 기술적 지표를 분석하고 매수/매도를 결정하세요</li>
              <li>• 하루가 지나면 다음 턴으로 진행됩니다</li>
              <li>• 종료일까지 최대 수익률을 목표로 하세요!</li>
            </ul>
          </div>

          <Button
            type="submit"
            className="w-full py-3"
            size="lg"
            isLoading={isLoading}
            disabled={isLoading}
          >
            {isLoading ? '생성 중...' : '게임 시작'}
          </Button>
        </form>
      </div>
    </Card>
  );
}
