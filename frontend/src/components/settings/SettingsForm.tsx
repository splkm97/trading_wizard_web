import { useState, useEffect } from 'react';
import { Card } from '../common/Card';
import { Button } from '../common/Button';
import { Input } from '../common/Input';
import { UserSettings, ConstitutionWarning } from '../../types';

interface SettingsFormProps {
  initialSettings: UserSettings;
  onSave: (settings: UserSettings) => Promise<ConstitutionWarning[]>;
  isLoading?: boolean;
}

const DEFAULT_SETTINGS: UserSettings = {
  max_positions: 15,
  max_position_pct: 10,
  stop_loss_pct: 4.5,
  confidence_threshold: 55,
  take_profit_enabled: true,
  take_profit_pct: 12,
  take_profit_ratio: 1.0,
  sell_on_middle_band: false,
  bollinger_period: 15,
  bollinger_std_dev: 1.5,
  squeeze_threshold_pct: 60,
  squeeze_lookback_days: 10,
  expansion_threshold_pct: 20,
  band_touch_tolerance: 0.001,
  trading_days_per_year: 252,
  days_per_year: 365,
};

export function SettingsForm({
  initialSettings,
  onSave,
  isLoading = false,
}: SettingsFormProps) {
  const [settings, setSettings] = useState<UserSettings>(initialSettings);
  const [warnings, setWarnings] = useState<ConstitutionWarning[]>([]);
  const [isSaving, setIsSaving] = useState(false);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'risk' | 'bollinger' | 'advanced'>('risk');

  useEffect(() => {
    setSettings(initialSettings);
  }, [initialSettings]);

  // Check for potential Constitution III violations on change
  useEffect(() => {
    const newWarnings: ConstitutionWarning[] = [];

    if (settings.stop_loss_pct < 5) {
      newWarnings.push({
        field: 'stop_loss_pct',
        message: 'Constitution III 권장: 손절선 5% 이상',
        recommended_value: 5,
      });
    }

    if (settings.max_position_pct > 10) {
      newWarnings.push({
        field: 'max_position_pct',
        message: 'Constitution III 권장: 종목당 비중 10% 이하',
        recommended_value: 10,
      });
    }

    if (settings.max_positions > 15) {
      newWarnings.push({
        field: 'max_positions',
        message: 'Constitution III 권장: 최대 포지션 15개 이하',
        recommended_value: 15,
      });
    }

    setWarnings(newWarnings);
  }, [settings]);

  const handleChange = (field: keyof UserSettings, value: number | boolean) => {
    setSettings((prev) => ({ ...prev, [field]: value }));
    setSuccessMessage(null);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSaving(true);
    setSuccessMessage(null);

    try {
      const serverWarnings = await onSave(settings);
      setWarnings(serverWarnings);
      setSuccessMessage('설정이 저장되었습니다.');
    } catch (err) {
      console.error('Failed to save settings:', err);
    } finally {
      setIsSaving(false);
    }
  };

  const handleReset = () => {
    setSettings(DEFAULT_SETTINGS);
    setSuccessMessage(null);
  };

  const tabs = [
    { id: 'risk' as const, label: '리스크 관리' },
    { id: 'bollinger' as const, label: '볼린저 밴드' },
    { id: 'advanced' as const, label: '고급 설정' },
  ];

  return (
    <Card className="p-6">
      <h2 className="text-lg font-semibold text-gray-900 mb-4">전략 설정</h2>

      {warnings.length > 0 && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-4">
          <h3 className="font-medium text-yellow-800 mb-2">
            Constitution III 경고
          </h3>
          <ul className="text-sm text-yellow-700 space-y-1">
            {warnings.map((w, i) => (
              <li key={i}>• {w.message}</li>
            ))}
          </ul>
        </div>
      )}

      {successMessage && (
        <div className="bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded-lg mb-4">
          {successMessage}
        </div>
      )}

      {/* Tab Navigation */}
      <div className="flex border-b border-gray-200 mb-6">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            type="button"
            className={`px-4 py-2 text-sm font-medium border-b-2 -mb-px ${
              activeTab === tab.id
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
            onClick={() => setActiveTab(tab.id)}
          >
            {tab.label}
          </button>
        ))}
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Risk Management Tab */}
        {activeTab === 'risk' && (
          <div className="space-y-6">
            <h3 className="text-md font-medium text-gray-800 border-b pb-2">리스크 관리</h3>

            <div>
              <Input
                label="최대 포지션 수"
                type="number"
                value={settings.max_positions}
                onChange={(e) => handleChange('max_positions', Number(e.target.value))}
                min={1}
                max={50}
                helperText="동시에 보유할 수 있는 최대 종목 수 (권장: 15)"
              />
            </div>

            <div>
              <Input
                label="종목당 최대 비중 (%)"
                type="number"
                value={settings.max_position_pct}
                onChange={(e) => handleChange('max_position_pct', Number(e.target.value))}
                min={1}
                max={100}
                step={0.5}
                helperText="총 자본 대비 단일 종목 최대 투자 비율 (권장: 10%)"
              />
            </div>

            <div>
              <Input
                label="손절선 (%)"
                type="number"
                value={settings.stop_loss_pct}
                onChange={(e) => handleChange('stop_loss_pct', Number(e.target.value))}
                min={1}
                max={50}
                step={0.5}
                helperText="매수가 대비 손절 기준 (기본: 4.5%)"
              />
            </div>

            <div>
              <Input
                label="신뢰도 임계값"
                type="number"
                value={settings.confidence_threshold}
                onChange={(e) => handleChange('confidence_threshold', Number(e.target.value))}
                min={0}
                max={100}
                helperText="매수 신호 최소 신뢰도 점수 (기본: 55)"
              />
            </div>

            <h3 className="text-md font-medium text-gray-800 border-b pb-2 pt-4">매도 조건</h3>

            <div className="flex items-center gap-3">
              <input
                type="checkbox"
                id="sell_on_middle_band"
                checked={settings.sell_on_middle_band}
                onChange={(e) => handleChange('sell_on_middle_band', e.target.checked)}
                className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
              />
              <label htmlFor="sell_on_middle_band" className="text-sm font-medium text-gray-700">
                중간 밴드 이탈 시 매도
              </label>
            </div>
            <p className="text-xs text-gray-500 -mt-3 ml-7">
              활성화 시 가격이 볼린저 중간선 아래로 하락하면 매도 (OFF 권장: 수익률 향상)
            </p>

            <h3 className="text-md font-medium text-gray-800 border-b pb-2 pt-4">익절 설정</h3>

            <div className="flex items-center gap-3">
              <input
                type="checkbox"
                id="take_profit_enabled"
                checked={settings.take_profit_enabled}
                onChange={(e) => handleChange('take_profit_enabled', e.target.checked)}
                className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
              />
              <label htmlFor="take_profit_enabled" className="text-sm font-medium text-gray-700">
                익절 기능 활성화
              </label>
            </div>

            {settings.take_profit_enabled && (
              <>
                <div>
                  <Input
                    label="익절 목표 (%)"
                    type="number"
                    value={settings.take_profit_pct}
                    onChange={(e) => handleChange('take_profit_pct', Number(e.target.value))}
                    min={5}
                    max={50}
                    step={0.5}
                    helperText="목표 수익률 도달 시 일부 익절 (기본: 12%)"
                  />
                </div>

                <div>
                  <Input
                    label="익절 비율"
                    type="number"
                    value={settings.take_profit_ratio}
                    onChange={(e) => handleChange('take_profit_ratio', Number(e.target.value))}
                    min={0.1}
                    max={1.0}
                    step={0.1}
                    helperText="목표 도달 시 매도할 포지션 비율 (0.5 = 50%)"
                  />
                </div>
              </>
            )}
          </div>
        )}

        {/* Bollinger Band Tab */}
        {activeTab === 'bollinger' && (
          <div className="space-y-6">
            <h3 className="text-md font-medium text-gray-800 border-b pb-2">볼린저 밴드 파라미터</h3>

            <div>
              <Input
                label="볼린저 기간"
                type="number"
                value={settings.bollinger_period}
                onChange={(e) => handleChange('bollinger_period', Number(e.target.value))}
                min={5}
                max={200}
                helperText="이동평균 계산 기간 (기본: 15일)"
              />
            </div>

            <div>
              <Input
                label="표준편차 배수"
                type="number"
                value={settings.bollinger_std_dev}
                onChange={(e) => handleChange('bollinger_std_dev', Number(e.target.value))}
                min={0.5}
                max={5}
                step={0.1}
                helperText="밴드 폭 결정 배수 (기본: 1.5)"
              />
            </div>

            <h3 className="text-md font-medium text-gray-800 border-b pb-2 pt-4">스퀴즈 감지</h3>

            <div>
              <Input
                label="스퀴즈 임계값 (%)"
                type="number"
                value={settings.squeeze_threshold_pct}
                onChange={(e) => handleChange('squeeze_threshold_pct', Number(e.target.value))}
                min={5}
                max={100}
                helperText="밴드폭 감소율 기준 (기본: 60%)"
              />
            </div>

            <div>
              <Input
                label="스퀴즈 룩백 기간 (일)"
                type="number"
                value={settings.squeeze_lookback_days}
                onChange={(e) => handleChange('squeeze_lookback_days', Number(e.target.value))}
                min={2}
                max={30}
                helperText="스퀴즈 비교 기간 (기본: 10일)"
              />
            </div>
          </div>
        )}

        {/* Advanced Tab */}
        {activeTab === 'advanced' && (
          <div className="space-y-6">
            <h3 className="text-md font-medium text-gray-800 border-b pb-2">고급 스퀴즈 설정</h3>

            <div>
              <Input
                label="확장 임계값 (%)"
                type="number"
                value={settings.expansion_threshold_pct}
                onChange={(e) => handleChange('expansion_threshold_pct', Number(e.target.value))}
                min={5}
                max={100}
                step={0.5}
                helperText="밴드 확장 확인 기준 (기본: 20%)"
              />
            </div>

            <div>
              <Input
                label="밴드 터치 허용 오차"
                type="number"
                value={settings.band_touch_tolerance}
                onChange={(e) => handleChange('band_touch_tolerance', Number(e.target.value))}
                min={0}
                max={0.01}
                step={0.0001}
                helperText="밴드 터치 판정 허용 오차 (기본: 0.001 = 0.1%)"
              />
            </div>

            <h3 className="text-md font-medium text-gray-800 border-b pb-2 pt-4">지표 계산 설정</h3>

            <div>
              <Input
                label="연간 거래일 수"
                type="number"
                value={settings.trading_days_per_year}
                onChange={(e) => handleChange('trading_days_per_year', Number(e.target.value))}
                min={200}
                max={365}
                helperText="샤프 비율 연환산용 거래일 수 (기본: 252)"
              />
            </div>

            <div>
              <Input
                label="연간 일수"
                type="number"
                value={settings.days_per_year}
                onChange={(e) => handleChange('days_per_year', Number(e.target.value))}
                min={360}
                max={366}
                helperText="CAGR 계산용 연간 일수 (기본: 365)"
              />
            </div>
          </div>
        )}

        <div className="flex gap-3 pt-4 border-t">
          <Button
            type="submit"
            isLoading={isSaving || isLoading}
            disabled={isSaving || isLoading}
            className="flex-1"
          >
            저장
          </Button>
          <Button
            type="button"
            variant="secondary"
            onClick={handleReset}
            disabled={isSaving || isLoading}
          >
            기본값으로 초기화
          </Button>
        </div>
      </form>

      <div className="mt-6 pt-6 border-t border-gray-200">
        <h3 className="font-medium text-gray-900 mb-2">Constitution III 원칙</h3>
        <ul className="text-sm text-gray-600 space-y-1">
          <li>• 손절선: 5% 이상 (리스크 관리)</li>
          <li>• 종목당 비중: 10% 이하 (분산 투자)</li>
          <li>• 최대 포지션: 15개 이하 (집중 관리)</li>
        </ul>
      </div>
    </Card>
  );
}
