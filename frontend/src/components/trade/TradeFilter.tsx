import { useState, useEffect } from 'react';
import { Input } from '../common/Input';
import { Button } from '../common/Button';
import { TradeAction } from '../../types';

export interface TradeFilters {
  stockCode?: string;
  action?: TradeAction | '';
  startDate?: string;
  endDate?: string;
}

interface TradeFilterProps {
  filters: TradeFilters;
  onFilterChange: (filters: TradeFilters) => void;
  onExport?: () => void;
  isExporting?: boolean;
}

export function TradeFilter({
  filters,
  onFilterChange,
  onExport,
  isExporting = false,
}: TradeFilterProps) {
  const [localFilters, setLocalFilters] = useState<TradeFilters>(filters);

  useEffect(() => {
    setLocalFilters(filters);
  }, [filters]);

  const handleInputChange = (field: keyof TradeFilters, value: string) => {
    setLocalFilters((prev) => ({ ...prev, [field]: value }));
  };

  const handleApply = () => {
    onFilterChange(localFilters);
  };

  const handleReset = () => {
    const resetFilters: TradeFilters = {
      stockCode: '',
      action: '',
      startDate: '',
      endDate: '',
    };
    setLocalFilters(resetFilters);
    onFilterChange(resetFilters);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleApply();
    }
  };

  return (
    <div className="bg-white p-4 rounded-lg shadow-sm border border-gray-200 mb-4">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
        <Input
          label="종목코드"
          placeholder="000000"
          value={localFilters.stockCode || ''}
          onChange={(e) => handleInputChange('stockCode', e.target.value)}
          onKeyDown={handleKeyDown}
          maxLength={6}
        />

        <div className="w-full">
          <label className="block text-sm font-medium text-gray-700 mb-1">
            거래유형
          </label>
          <select
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
            value={localFilters.action || ''}
            onChange={(e) => handleInputChange('action', e.target.value)}
          >
            <option value="">전체</option>
            <option value="BUY">매수</option>
            <option value="SELL">매도</option>
          </select>
        </div>

        <Input
          label="시작일"
          type="date"
          value={localFilters.startDate || ''}
          onChange={(e) => handleInputChange('startDate', e.target.value)}
          onKeyDown={handleKeyDown}
        />

        <Input
          label="종료일"
          type="date"
          value={localFilters.endDate || ''}
          onChange={(e) => handleInputChange('endDate', e.target.value)}
          onKeyDown={handleKeyDown}
        />

        <div className="flex items-end gap-2">
          <Button onClick={handleApply} className="flex-1">
            검색
          </Button>
          <Button variant="secondary" onClick={handleReset}>
            초기화
          </Button>
        </div>
      </div>

      {onExport && (
        <div className="mt-4 pt-4 border-t border-gray-200 flex justify-end">
          <Button
            variant="secondary"
            onClick={onExport}
            isLoading={isExporting}
            disabled={isExporting}
          >
            CSV 내보내기
          </Button>
        </div>
      )}
    </div>
  );
}
