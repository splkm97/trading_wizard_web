/**
 * Simulation Page - Turn-Based Trading Simulation Game
 * 
 * Main game page with three-column layout:
 * - Left: Stock recommendations list
 * - Center: Stock detail panel with chart
 * - Right: Portfolio summary
 */

import { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { GameSetupForm } from '../components/simulation/GameSetupForm';
import { StockRecommendationList } from '../components/simulation/StockRecommendationList';
import { StockDetailPanel } from '../components/simulation/StockDetailPanel';
import { PortfolioSummary } from '../components/simulation/PortfolioSummary';
import { TurnProgressBar } from '../components/simulation/TurnProgressBar';
import { GameReportModal } from '../components/simulation/GameReportModal';
import { Button } from '../components/common/Button';
import {
  getSession,
  getRecommendations,
  getStockDetail,
  getSessions,
  advanceTurn,
  precomputeRecommendations,
} from '../services/simulation';
import type {
  GameSessionWithSummary,
  StockRecommendation,
  StockDetail,
  GameSession,
} from '../types/simulation';

type PageState = 'loading' | 'setup' | 'playing' | 'game_over' | 'error';

export function SimulationPage() {
  const { sessionId } = useParams<{ sessionId: string }>();
  const navigate = useNavigate();

  const [pageState, setPageState] = useState<PageState>('loading');
  const [error, setError] = useState<string | null>(null);

  const [session, setSession] = useState<GameSessionWithSummary | null>(null);
  const [recommendations, setRecommendations] = useState<StockRecommendation[]>([]);
  const [selectedStockCode, setSelectedStockCode] = useState<string | null>(null);
  const [stockDetail, setStockDetail] = useState<StockDetail | null>(null);

  const [isLoadingSession, setIsLoadingSession] = useState(false);
  const [isLoadingRecommendations, setIsLoadingRecommendations] = useState(false);
  const [isLoadingStockDetail, setIsLoadingStockDetail] = useState(false);
  const [isAdvancingTurn, setIsAdvancingTurn] = useState(false);
  const [isInitialRecommendationsLoad, setIsInitialRecommendationsLoad] = useState(true);

  const [existingSessions, setExistingSessions] = useState<GameSession[]>([]);
  const [isReportModalOpen, setIsReportModalOpen] = useState(false);

  const loadSession = useCallback(async (id: string) => {
    setIsLoadingSession(true);
    setError(null);
    try {
      const sessionData = await getSession(id);
      setSession(sessionData);

      if (sessionData.is_game_over || sessionData.status === 'COMPLETED') {
        setPageState('game_over');
      } else {
        setPageState('playing');
      }

      return sessionData;
    } catch (err: unknown) {
      const message = err && typeof err === 'object' && 'detail' in err
        ? (err as { detail: string }).detail
        : '세션을 불러오는데 실패했습니다.';
      setError(message);
      setPageState('error');
      return null;
    } finally {
      setIsLoadingSession(false);
    }
  }, []);

  const loadRecommendations = useCallback(async (id: string, isInitial: boolean = false) => {
    setIsLoadingRecommendations(true);
    if (isInitial) {
      setIsInitialRecommendationsLoad(true);
    }
    try {
      const recs = await getRecommendations(id);
      setRecommendations(recs);

      if (recs.length > 0 && !selectedStockCode) {
        setSelectedStockCode(recs[0].stock_code);
      }

      if (isInitial) {
        precomputeRecommendations(id, 3).catch(() => {});
      }
    } catch (err) {
      console.error('Failed to load recommendations:', err);
      setRecommendations([]);
    } finally {
      setIsLoadingRecommendations(false);
      setIsInitialRecommendationsLoad(false);
    }
  }, [selectedStockCode]);

  const loadStockDetail = useCallback(async (id: string, stockCode: string) => {
    setIsLoadingStockDetail(true);
    try {
      const detail = await getStockDetail(id, stockCode);
      setStockDetail(detail);
    } catch (err) {
      console.error('Failed to load stock detail:', err);
      setStockDetail(null);
    } finally {
      setIsLoadingStockDetail(false);
    }
  }, []);

  const loadExistingSessions = useCallback(async () => {
    try {
      const sessions = await getSessions('IN_PROGRESS');
      setExistingSessions(sessions);
    } catch (err) {
      console.error('Failed to load existing sessions:', err);
    }
  }, []);

  useEffect(() => {
    if (sessionId) {
      loadSession(sessionId).then((sessionData) => {
        if (sessionData) {
          loadRecommendations(sessionId, true);
        }
      });
    } else {
      loadExistingSessions();
      setPageState('setup');
      setIsInitialRecommendationsLoad(false);
    }
  }, [sessionId, loadSession, loadRecommendations, loadExistingSessions]);

  useEffect(() => {
    if (sessionId && selectedStockCode) {
      loadStockDetail(sessionId, selectedStockCode);
    }
  }, [sessionId, selectedStockCode, loadStockDetail]);

  const handleSelectStock = (stockCode: string) => {
    setSelectedStockCode(stockCode);
  };

  const handleContinueSession = (id: string) => {
    navigate(`/simulation/${id}`);
  };

  const handleTradeExecuted = useCallback(() => {
    if (sessionId) {
      loadSession(sessionId);
      loadRecommendations(sessionId);
      if (selectedStockCode) {
        loadStockDetail(sessionId, selectedStockCode);
      }
    }
  }, [sessionId, selectedStockCode, loadSession, loadRecommendations, loadStockDetail]);

  const handleAdvanceTurn = useCallback(async () => {
    if (!sessionId) return;
    
    setIsAdvancingTurn(true);
    try {
      const response = await advanceTurn(sessionId);
      setSession(response.session);
      setRecommendations(response.recommendations);
      
      if (response.is_game_over) {
        setPageState('game_over');
      } else if (response.recommendations.length > 0) {
        setSelectedStockCode(response.recommendations[0].stock_code);
      }
    } catch (err) {
      console.error('Failed to advance turn:', err);
    } finally {
      setIsAdvancingTurn(false);
    }
  }, [sessionId]);

  if (pageState === 'loading') {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-primary-600 mx-auto mb-4" />
          <p className="text-gray-600">게임 데이터 불러오는 중...</p>
        </div>
      </div>
    );
  }

  if (pageState === 'setup') {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-slate-100 py-12 px-4">
        <div className="max-w-4xl mx-auto">
          <div className="text-center mb-8">
            <h1 className="text-3xl font-bold text-gray-900 mb-2">
              트레이딩 시뮬레이션
            </h1>
            <p className="text-gray-600">
              볼린저 밴드 전략으로 가상 주식 투자를 체험하세요
            </p>
          </div>

          {existingSessions.length > 0 && (
            <div className="mb-8">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">진행중인 게임</h2>
              <div className="grid gap-3">
                {existingSessions.map((sess) => (
                  <div
                    key={sess.id}
                    className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 flex items-center justify-between hover:border-primary-300 transition-colors"
                  >
                    <div>
                      <p className="font-medium text-gray-900">
                        {sess.name || '이름 없는 게임'}
                      </p>
                      <p className="text-sm text-gray-500">
                        {sess.start_date} ~ {sess.end_date} | 현재: {sess.current_date}
                      </p>
                    </div>
                    <Button
                      variant="secondary"
                      size="sm"
                      onClick={() => handleContinueSession(sess.id)}
                    >
                      이어하기
                    </Button>
                  </div>
                ))}
              </div>
            </div>
          )}

          <GameSetupForm />
        </div>
      </div>
    );
  }

  if (pageState === 'error') {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 px-4">
        <div className="text-center max-w-md">
          <div className="w-20 h-20 rounded-full bg-red-100 flex items-center justify-center mx-auto mb-4">
            <svg className="w-10 h-10 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
          </div>
          <h2 className="text-xl font-bold text-gray-900 mb-2">오류 발생</h2>
          <p className="text-gray-600 mb-6">{error}</p>
          <Button onClick={() => navigate('/simulation')}>
            새 게임 시작
          </Button>
        </div>
      </div>
    );
  }

  if (pageState === 'game_over') {
    const isActuallyCompleted = session?.status === 'COMPLETED' || session?.is_game_over;
    
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-slate-100 py-12 px-4">
        <div className="max-w-2xl mx-auto text-center">
          <div className={`w-24 h-24 rounded-full flex items-center justify-center mx-auto mb-6 ${
            isActuallyCompleted 
              ? 'bg-gradient-to-br from-primary-500 to-primary-700' 
              : 'bg-gradient-to-br from-amber-500 to-orange-600'
          }`}>
            <svg className="w-12 h-12 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              {isActuallyCompleted ? (
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              ) : (
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              )}
            </svg>
          </div>
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            {isActuallyCompleted ? '게임 완료!' : '중간 결과'}
          </h1>
          <p className="text-gray-600 mb-8">
            {isActuallyCompleted 
              ? `${session?.start_date} ~ ${session?.end_date} 시뮬레이션이 종료되었습니다.`
              : `${session?.start_date} ~ ${session?.current_date} 현재까지의 성과입니다.`
            }
          </p>

          {session && (
            <div className="bg-white rounded-xl shadow-lg p-8 mb-8">
              <h2 className="text-xl font-semibold text-gray-900 mb-6">
                {isActuallyCompleted ? '최종 결과' : '현재 성과'}
              </h2>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
                <div>
                  <p className="text-sm text-gray-500 mb-1">초기 자본금</p>
                  <p className="text-xl font-bold text-gray-900">
                    {new Intl.NumberFormat('ko-KR', { style: 'currency', currency: 'KRW', maximumFractionDigits: 0 }).format(session.initial_capital)}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-gray-500 mb-1">{isActuallyCompleted ? '최종 평가액' : '현재 평가액'}</p>
                  <p className="text-xl font-bold text-gray-900">
                    {new Intl.NumberFormat('ko-KR', { style: 'currency', currency: 'KRW', maximumFractionDigits: 0 }).format(session.total_value)}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-gray-500 mb-1">총 수익</p>
                  <p className={`text-xl font-bold ${session.total_return >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                    {new Intl.NumberFormat('ko-KR', { style: 'currency', currency: 'KRW', maximumFractionDigits: 0 }).format(session.total_return)}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-gray-500 mb-1">수익률</p>
                  <p className={`text-xl font-bold ${session.total_return_pct >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                    {session.total_return_pct >= 0 ? '+' : ''}{session.total_return_pct.toFixed(2)}%
                  </p>
                </div>
              </div>
            </div>
          )}

          <div className="flex items-center justify-center gap-4">
            {!isActuallyCompleted && (
              <Button onClick={() => setPageState('playing')}>
                계속하기
              </Button>
            )}
            <Button variant={isActuallyCompleted ? 'primary' : 'secondary'} onClick={() => navigate('/simulation')}>
              {isActuallyCompleted ? '새 게임 시작' : '게임 목록'}
            </Button>
            <Button variant="secondary" onClick={() => navigate('/backtest')}>
              백테스트 비교
            </Button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="border-b border-gray-200 bg-white">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between gap-6">
            <div className="shrink-0">
              <h1 className="text-xl font-bold text-gray-900">
                {session?.name || '트레이딩 시뮬레이션'}
              </h1>
            </div>
            
            {session && (
              <TurnProgressBar
                currentDate={session.current_date}
                startDate={session.start_date}
                endDate={session.end_date}
                isGameOver={session.is_game_over}
                isLoading={isAdvancingTurn}
                onAdvanceTurn={handleAdvanceTurn}
              />
            )}
            
            <div className="flex items-center gap-3 shrink-0">
              <Button variant="secondary" size="sm" onClick={() => setIsReportModalOpen(true)}>
                리포트
              </Button>
              <Button variant="secondary" size="sm" onClick={() => setPageState('game_over')}>
                결과 보기
              </Button>
              <Button variant="secondary" size="sm" onClick={() => navigate('/simulation')}>
                게임 목록
              </Button>
            </div>
          </div>
        </div>
      </div>

      {((isInitialRecommendationsLoad && isLoadingRecommendations) || isAdvancingTurn) && (
        <div className="fixed inset-0 bg-black/80 z-50 flex items-center justify-center">
          <div className="text-center">
            <div className="w-12 h-12 border-4 border-white/20 border-t-white rounded-full animate-spin mx-auto mb-4"></div>
            <p className="text-white text-lg">
              {isAdvancingTurn ? '다음 날로 이동 중...' : '추천 종목 분석 중...'}
            </p>
          </div>
        </div>
      )}

      <div className="container mx-auto px-4 py-6">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 h-[calc(100vh-180px)]">
          <div className="lg:col-span-3 overflow-hidden">
            <StockRecommendationList
              recommendations={recommendations}
              selectedStockCode={selectedStockCode}
              onSelectStock={handleSelectStock}
              isLoading={isLoadingRecommendations || isLoadingSession}
            />
          </div>

          <div className="lg:col-span-6 overflow-y-auto">
            <StockDetailPanel
              stockDetail={stockDetail}
              isLoading={isLoadingStockDetail}
              sessionId={sessionId}
              availableCash={session?.cash_balance}
              sessionStatus={session?.status}
              onTradeExecuted={handleTradeExecuted}
            />
          </div>

          <div className="lg:col-span-3 overflow-hidden">
            <PortfolioSummary
              session={session}
              isLoading={isLoadingSession}
            />
          </div>
        </div>
      </div>

      {sessionId && (
        <GameReportModal
          isOpen={isReportModalOpen}
          onClose={() => setIsReportModalOpen(false)}
          sessionId={sessionId}
          sessionName={session?.name}
          isGameCompleted={session?.status === 'COMPLETED'}
        />
      )}
    </div>
  );
}
