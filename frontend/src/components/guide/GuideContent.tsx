import { useNavigate } from 'react-router-dom';
import { Card, Button } from '../common';
import { CollapsibleSection } from './CollapsibleSection';

export function GuideContent() {
  const navigate = useNavigate();

  return (
    <div className="space-y-8">
      {/* Section 1: 애플리케이션 소개 */}
      <section>
        <h2 className="text-2xl font-bold text-gray-900 dark:text-gray-100 mb-4">애플리케이션 소개</h2>
        <Card>
          <div className="space-y-4">
            <p className="text-gray-700 dark:text-gray-300">
              <strong>Trading Wizard</strong>는 기술적 지표 기반 주식 매매 신호를 제공하는 웹 애플리케이션입니다.
            </p>
            <ul className="list-disc list-inside text-gray-600 dark:text-gray-400 space-y-2">
              <li>KOSPI 상위 100개 종목을 대상으로 매수/매도 타이밍을 추천합니다</li>
              <li>신뢰도 점수 기반으로 투자 판단을 보조합니다</li>
              <li>감정적 매매를 방지하고 체계적인 투자를 도와드립니다</li>
            </ul>
          </div>
        </Card>
      </section>

      {/* Section 2: 빠른 시작 가이드 */}
      <section>
        <h2 className="text-2xl font-bold text-gray-900 dark:text-gray-100 mb-4">빠른 시작 가이드</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <QuickStartCard
            title="대시보드"
            description="보유 포지션과 수익률을 한눈에 확인하세요"
            buttonText="대시보드 가기"
            onClick={() => navigate('/dashboard')}
          />
          <QuickStartCard
            title="거래 입력"
            description="실시간 매수 추천을 확인하고 거래를 기록하세요"
            buttonText="추천 보기"
            onClick={() => navigate('/trade')}
          />
          <QuickStartCard
            title="MACD/RSI 역추세"
            description="과매도 반등 신호를 확인하세요"
            buttonText="역추세 보기"
            onClick={() => navigate('/contrarian')}
          />
          <QuickStartCard
            title="시뮬레이션"
            description="과거 데이터로 모의 투자를 체험해보세요"
            buttonText="시뮬레이션 시작"
            onClick={() => navigate('/simulation')}
          />
          <QuickStartCard
            title="백테스트"
            description="전략의 과거 성과를 검증해보세요"
            buttonText="백테스트 가기"
            onClick={() => navigate('/backtest')}
          />
          <QuickStartCard
            title="설정"
            description="매매 전략 파라미터를 조정하세요"
            buttonText="설정 가기"
            onClick={() => navigate('/settings')}
          />
        </div>
      </section>

      {/* Section 3: 추천 전략 소개 */}
      <section>
        <h2 className="text-2xl font-bold text-gray-900 dark:text-gray-100 mb-4">추천 전략 소개</h2>
        <div className="space-y-4">
          {/* 볼린저 밴드 스퀴즈 전략 */}
          <CollapsibleSection
            title="볼린저 밴드 스퀴즈 전략"
            summary="변동성 수축 후 상단 밴드 돌파 시점을 포착하여 매수 신호를 생성합니다."
          >
            <div className="space-y-4 text-sm text-gray-700">
              <div>
                <h4 className="font-semibold text-gray-900 mb-2">전략 원리</h4>
                <p>
                  주가가 일정 기간 좁은 범위에서 움직이다가(스퀴즈) 상단 볼린저 밴드를 돌파하면
                  상승 추세의 시작으로 판단하여 매수 신호를 발생시킵니다.
                </p>
              </div>

              <div>
                <h4 className="font-semibold text-gray-900 mb-2">사용 지표</h4>
                <ul className="list-disc list-inside space-y-1">
                  <li><strong>볼린저 밴드</strong>: 20일 이동평균선 ± 2표준편차</li>
                  <li><strong>거래량 비율</strong>: 20일 평균 거래량 대비 현재 거래량</li>
                  <li><strong>RSI (14일)</strong>: 30-70 중립 구간, 과매수/과매도 판단</li>
                  <li><strong>MACD (12/26/9)</strong>: 추세 방향 및 모멘텀 확인</li>
                </ul>
              </div>

              <div>
                <h4 className="font-semibold text-gray-900 mb-2">신뢰도 점수 계산</h4>
                <div className="bg-white rounded p-3 border border-gray-200">
                  <p className="mb-2">총점 = 기본 + 거래량 + RSI + MACD (최대 100점)</p>
                  <ul className="text-xs space-y-1 text-gray-600">
                    <li>• 기본 점수: 25점 (볼린저 밴드 돌파)</li>
                    <li>• 거래량 보너스: 0~25점 (거래량 1.0x~2.0x에 비례)</li>
                    <li>• RSI 보너스: 0~20점 (RSI 50 근처에서 최대)</li>
                    <li>• MACD 보너스: 0~30점 (히스토그램 강도에 비례)</li>
                  </ul>
                </div>
              </div>

              <div>
                <h4 className="font-semibold text-gray-900 mb-2">매도 조건</h4>
                <ul className="list-disc list-inside space-y-1">
                  <li><strong>손절</strong>: 매입가 대비 -4.5% (기본값, 설정 가능)</li>
                  <li><strong>익절</strong>: 매입가 대비 +12% (기본값, 설정 가능)</li>
                  <li><strong>추세 이탈</strong>: 주가가 중간밴드 하향 돌파 시</li>
                </ul>
              </div>
            </div>
          </CollapsibleSection>

          {/* MACD/RSI 역추세 전략 */}
          <CollapsibleSection
            title="MACD/RSI 역추세 전략"
            summary="과매도 구간에서 MACD 골든크로스 발생 시 반등 타이밍을 포착합니다."
          >
            <div className="space-y-4 text-sm text-gray-700">
              <div>
                <h4 className="font-semibold text-gray-900 mb-2">전략 원리</h4>
                <p>
                  RSI가 과매도 구간(30 이하)에 진입한 상태에서 MACD가 시그널선을 상향 돌파하면
                  급락 후 반등의 시작으로 판단하여 매수 신호를 발생시킵니다.
                </p>
              </div>

              <div>
                <h4 className="font-semibold text-gray-900 mb-2">매수 조건</h4>
                <ul className="list-disc list-inside space-y-1">
                  <li><strong>RSI 과매도</strong>: RSI ≤ 30 (낮을수록 더 강한 신호)</li>
                  <li><strong>MACD 골든크로스</strong>: MACD선이 시그널선을 아래에서 위로 돌파</li>
                </ul>
              </div>

              <div>
                <h4 className="font-semibold text-gray-900 mb-2">신뢰도 점수 계산</h4>
                <div className="bg-white rounded p-3 border border-gray-200">
                  <p className="mb-2">총점 = RSI 기본점수 + MACD 보너스 (최대 100점)</p>
                  <ul className="text-xs space-y-1 text-gray-600">
                    <li>• RSI ≤ 20 (심한 과매도): 기본 80점</li>
                    <li>• RSI 20-25 (과매도): 기본 60점</li>
                    <li>• RSI 25-30 (약한 과매도): 기본 40점</li>
                    <li>• MACD 히스토그램 보너스: 0~20점</li>
                  </ul>
                </div>
              </div>

              <div>
                <h4 className="font-semibold text-gray-900 mb-2">활용 팁</h4>
                <p className="text-gray-600">
                  이 전략은 급락장에서 반등 타이밍을 포착하는 데 유용합니다.
                  다만, 추세적 하락장에서는 '떨어지는 칼날'을 잡을 위험이 있으니
                  다른 지표와 함께 종합적으로 판단하시기 바랍니다.
                </p>
              </div>
            </div>
          </CollapsibleSection>
        </div>
      </section>
    </div>
  );
}

interface QuickStartCardProps {
  title: string;
  description: string;
  buttonText: string;
  onClick: () => void;
}

function QuickStartCard({ title, description, buttonText, onClick }: QuickStartCardProps) {
  return (
    <Card>
      <div className="flex flex-col h-full">
        <h3 className="font-semibold text-gray-900 dark:text-gray-100 mb-2">{title}</h3>
        <p className="text-sm text-gray-600 dark:text-gray-400 mb-4 flex-grow">{description}</p>
        <Button variant="secondary" size="sm" onClick={onClick}>
          {buttonText}
        </Button>
      </div>
    </Card>
  );
}
