import { useState, useEffect, useRef } from 'react';
import { Button } from '../common/Button';
import { Input } from '../common/Input';
import { Card } from '../common/Card';
import { api } from '../../services/api';
import { UserSettings, BacktestParams } from '../../types';

interface BacktestFormProps {
  onSubmit: (params: BacktestParams) => void;
  isLoading?: boolean;
}

interface StockList {
  id: string;
  name: string;
  description: string | null;
  stock_count: number;
  created_at: string;
}

const DEFAULT_STRATEGY: Partial<UserSettings> = {
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
};

export function BacktestForm({ onSubmit, isLoading = false }: BacktestFormProps) {
  const [params, setParams] = useState<BacktestParams>({
    start_date: '2025-01-02',
    end_date: '2025-12-31',
    stock_list: '',
    initial_capital: 1000000,
    name: '',
  });

  const [customLists, setCustomLists] = useState<StockList[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [uploadSuccess, setUploadSuccess] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Advanced settings state
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [useCustomStrategy, setUseCustomStrategy] = useState(false);
  const [strategyOverrides, setStrategyOverrides] = useState<Partial<UserSettings>>(DEFAULT_STRATEGY);

  // Fetch user's custom stock lists
  useEffect(() => {
    const fetchCustomLists = async () => {
      try {
        const lists = await api.get<StockList[]>('/stock-lists');
        setCustomLists(lists);
      } catch (err) {
        console.error('Failed to fetch custom stock lists:', err);
      }
    };
    fetchCustomLists();
  }, []);

  // Fetch user's saved settings when using custom strategy
  useEffect(() => {
    const fetchUserSettings = async () => {
      try {
        const settings = await api.get<UserSettings>('/settings');
        setStrategyOverrides(settings);
      } catch (err) {
        console.error('Failed to fetch user settings:', err);
      }
    };
    if (useCustomStrategy) {
      fetchUserSettings();
    }
  }, [useCustomStrategy]);

  const handleChange = (field: keyof BacktestParams, value: string | number) => {
    setParams((prev) => ({ ...prev, [field]: value }));
  };

  const handleStrategyChange = (field: keyof UserSettings, value: number | boolean) => {
    setStrategyOverrides((prev) => ({ ...prev, [field]: value }));
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const submitParams: BacktestParams = {
      ...params,
      strategy_overrides: useCustomStrategy ? strategyOverrides : undefined,
    };
    onSubmit(submitParams);
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploadError(null);
    setUploadSuccess(null);
    setIsUploading(true);

    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('name', file.name.replace('.txt', ''));

      const result = await api.upload<StockList>('/stock-lists/upload', formData);

      setCustomLists((prev) => [result, ...prev]);
      setParams((prev) => ({ ...prev, stock_list: result.id }));
      setUploadSuccess(`"${result.name}" 업로드 완료 (${result.stock_count}개 종목)`);
    } catch (err: unknown) {
      const error = err as { detail?: string };
      setUploadError(error.detail || '파일 업로드에 실패했습니다');
    } finally {
      setIsUploading(false);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  const handleDeleteList = async (listId: string, listName: string) => {
    if (!confirm(`"${listName}" 리스트를 삭제하시겠습니까?`)) return;

    try {
      await api.delete(`/stock-lists/${listId}`);
      setCustomLists((prev) => prev.filter((l) => l.id !== listId));
      if (params.stock_list === listId) {
        setParams((prev) => ({ ...prev, stock_list: '' }));
      }
    } catch (err) {
      console.error('Failed to delete stock list:', err);
    }
  };

  return (
    <Card className="p-6">
      <h2 className="text-lg font-semibold text-gray-900 mb-4">
        백테스트 실행
      </h2>
      <form onSubmit={handleSubmit} className="space-y-4">
        <Input
          label="백테스트 이름 (선택)"
          placeholder="예: 2025년 전체 백테스트"
          value={params.name || ''}
          onChange={(e) => handleChange('name', e.target.value)}
          maxLength={100}
        />

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Input
            label="시작일"
            type="date"
            value={params.start_date}
            onChange={(e) => handleChange('start_date', e.target.value)}
            required
          />
          <Input
            label="종료일"
            type="date"
            value={params.end_date}
            onChange={(e) => handleChange('end_date', e.target.value)}
            required
          />
        </div>

        <div className="w-full">
          <label className="block text-sm font-medium text-gray-700 mb-1">
            종목 리스트
          </label>
          <select
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
            value={params.stock_list}
            onChange={(e) => handleChange('stock_list', e.target.value)}
            required
          >
            <option value="">-- 종목 리스트를 선택하세요 --</option>
            {customLists.map((list) => (
              <option key={list.id} value={list.id}>
                {list.name} ({list.stock_count}개)
              </option>
            ))}
          </select>
          {customLists.length === 0 && (
            <p className="mt-1 text-sm text-amber-600">
              종목 리스트를 먼저 업로드해주세요.
            </p>
          )}

          {/* File upload section */}
          <div className="mt-3 p-3 border border-dashed border-gray-300 rounded-lg">
            <input
              type="file"
              ref={fileInputRef}
              accept=".txt"
              onChange={handleFileUpload}
              className="hidden"
              id="stock-list-upload"
            />
            <label
              htmlFor="stock-list-upload"
              className="flex items-center justify-center gap-2 cursor-pointer text-sm text-gray-600 hover:text-gray-800"
            >
              {isUploading ? (
                <span>업로드 중...</span>
              ) : (
                <>
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                  </svg>
                  <span>종목 리스트 파일 업로드 (.txt)</span>
                </>
              )}
            </label>
            <p className="mt-1 text-xs text-gray-500 text-center">
              한 줄에 하나의 종목코드 (예: 005930)
            </p>
          </div>

          {uploadError && (
            <p className="mt-2 text-sm text-red-600">{uploadError}</p>
          )}
          {uploadSuccess && (
            <p className="mt-2 text-sm text-green-600">{uploadSuccess}</p>
          )}

          {/* Custom lists management */}
          {customLists.length > 0 && (
            <div className="mt-3">
              <p className="text-xs text-gray-500 mb-2">내 종목 리스트:</p>
              <div className="flex flex-wrap gap-2">
                {customLists.map((list) => (
                  <span
                    key={list.id}
                    className="inline-flex items-center gap-1 px-2 py-1 text-xs bg-gray-100 rounded-full"
                  >
                    {list.name} ({list.stock_count})
                    <button
                      type="button"
                      onClick={() => handleDeleteList(list.id, list.name)}
                      className="text-gray-400 hover:text-red-500"
                    >
                      &times;
                    </button>
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>

        <Input
          label="초기 자본금 (KRW)"
          type="number"
          value={params.initial_capital}
          onChange={(e) => handleChange('initial_capital', Number(e.target.value))}
          min={100000}
          step={100000}
          required
          helperText="최소 100,000원"
        />

        {/* Advanced Strategy Settings Collapsible */}
        <div className="border border-gray-200 rounded-lg">
          <button
            type="button"
            onClick={() => setShowAdvanced(!showAdvanced)}
            className="w-full px-4 py-3 flex items-center justify-between text-left bg-gray-50 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <span className="font-medium text-gray-700">고급 전략 설정</span>
            <svg
              className={`w-5 h-5 text-gray-500 transition-transform ${showAdvanced ? 'rotate-180' : ''}`}
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </button>

          {showAdvanced && (
            <div className="p-4 space-y-4 border-t border-gray-200">
              {/* Toggle for custom strategy */}
              <div className="flex items-center gap-3 pb-3 border-b border-gray-100">
                <input
                  type="checkbox"
                  id="use_custom_strategy"
                  checked={useCustomStrategy}
                  onChange={(e) => setUseCustomStrategy(e.target.checked)}
                  className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                />
                <label htmlFor="use_custom_strategy" className="text-sm font-medium text-gray-700">
                  이 백테스트에 커스텀 전략 설정 사용
                </label>
              </div>

              {useCustomStrategy ? (
                <div className="space-y-4">
                  {/* Risk Management Section */}
                  <div>
                    <h4 className="text-sm font-medium text-gray-800 mb-3">리스크 관리</h4>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                      <Input
                        label="최대 포지션 수"
                        type="number"
                        value={strategyOverrides.max_positions || 15}
                        onChange={(e) => handleStrategyChange('max_positions', Number(e.target.value))}
                        min={1}
                        max={50}
                      />
                      <Input
                        label="종목당 최대 비중 (%)"
                        type="number"
                        value={strategyOverrides.max_position_pct || 10}
                        onChange={(e) => handleStrategyChange('max_position_pct', Number(e.target.value))}
                        min={1}
                        max={100}
                        step={0.5}
                      />
                      <Input
                        label="손절선 (%)"
                        type="number"
                        value={strategyOverrides.stop_loss_pct || 5}
                        onChange={(e) => handleStrategyChange('stop_loss_pct', Number(e.target.value))}
                        min={1}
                        max={50}
                        step={0.5}
                      />
                      <Input
                        label="신뢰도 임계값"
                        type="number"
                        value={strategyOverrides.confidence_threshold || 60}
                        onChange={(e) => handleStrategyChange('confidence_threshold', Number(e.target.value))}
                        min={0}
                        max={100}
                      />
                    </div>
                  </div>

                  {/* Sell Conditions Section */}
                  <div>
                    <h4 className="text-sm font-medium text-gray-800 mb-3">매도 조건</h4>
                    <div className="flex items-center gap-3 mb-3">
                      <input
                        type="checkbox"
                        id="override_sell_on_middle_band"
                        checked={strategyOverrides.sell_on_middle_band ?? false}
                        onChange={(e) => handleStrategyChange('sell_on_middle_band', e.target.checked)}
                        className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                      />
                      <label htmlFor="override_sell_on_middle_band" className="text-sm text-gray-700">
                        중간 밴드 이탈 시 매도 (OFF 권장)
                      </label>
                    </div>
                  </div>

                  {/* Take Profit Section */}
                  <div>
                    <h4 className="text-sm font-medium text-gray-800 mb-3">익절 설정</h4>
                    <div className="flex items-center gap-3 mb-3">
                      <input
                        type="checkbox"
                        id="override_take_profit_enabled"
                        checked={strategyOverrides.take_profit_enabled ?? true}
                        onChange={(e) => handleStrategyChange('take_profit_enabled', e.target.checked)}
                        className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                      />
                      <label htmlFor="override_take_profit_enabled" className="text-sm text-gray-700">
                        익절 기능 활성화
                      </label>
                    </div>
                    {strategyOverrides.take_profit_enabled && (
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                        <Input
                          label="익절 목표 (%)"
                          type="number"
                          value={strategyOverrides.take_profit_pct || 12}
                          onChange={(e) => handleStrategyChange('take_profit_pct', Number(e.target.value))}
                          min={5}
                          max={50}
                          step={0.5}
                        />
                        <Input
                          label="익절 비율"
                          type="number"
                          value={strategyOverrides.take_profit_ratio || 1.0}
                          onChange={(e) => handleStrategyChange('take_profit_ratio', Number(e.target.value))}
                          min={0.1}
                          max={1.0}
                          step={0.1}
                        />
                      </div>
                    )}
                  </div>

                  {/* Bollinger Band Section */}
                  <div>
                    <h4 className="text-sm font-medium text-gray-800 mb-3">볼린저 밴드</h4>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                      <Input
                        label="볼린저 기간"
                        type="number"
                        value={strategyOverrides.bollinger_period || 20}
                        onChange={(e) => handleStrategyChange('bollinger_period', Number(e.target.value))}
                        min={5}
                        max={200}
                      />
                      <Input
                        label="표준편차 배수"
                        type="number"
                        value={strategyOverrides.bollinger_std_dev || 2.0}
                        onChange={(e) => handleStrategyChange('bollinger_std_dev', Number(e.target.value))}
                        min={0.5}
                        max={5}
                        step={0.1}
                      />
                    </div>
                  </div>

                  {/* Squeeze Detection Section */}
                  <div>
                    <h4 className="text-sm font-medium text-gray-800 mb-3">스퀴즈 감지</h4>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                      <Input
                        label="스퀴즈 임계값 (%)"
                        type="number"
                        value={strategyOverrides.squeeze_threshold_pct || 30}
                        onChange={(e) => handleStrategyChange('squeeze_threshold_pct', Number(e.target.value))}
                        min={5}
                        max={100}
                      />
                      <Input
                        label="스퀴즈 룩백 기간 (일)"
                        type="number"
                        value={strategyOverrides.squeeze_lookback_days || 10}
                        onChange={(e) => handleStrategyChange('squeeze_lookback_days', Number(e.target.value))}
                        min={2}
                        max={30}
                      />
                    </div>
                  </div>

                  <p className="text-xs text-gray-500 mt-2">
                    * 이 설정은 현재 백테스트에만 적용되며, 저장된 설정에는 영향을 주지 않습니다.
                  </p>
                </div>
              ) : (
                <p className="text-sm text-gray-600">
                  저장된 전략 설정을 사용합니다. 커스텀 설정을 사용하려면 위 체크박스를 활성화하세요.
                </p>
              )}
            </div>
          )}
        </div>

        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
          <p className="text-sm text-yellow-800">
            <strong>주의:</strong> 백테스트 실행에는 최대 3분이 소요될 수 있습니다.
            Yahoo Finance API에서 데이터를 수집하고 분석합니다.
          </p>
        </div>

        <Button
          type="submit"
          className="w-full"
          isLoading={isLoading}
          disabled={isLoading}
        >
          {isLoading ? '실행 중...' : '백테스트 실행'}
        </Button>
      </form>
    </Card>
  );
}
