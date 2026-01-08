import { useState, useEffect } from 'react';
import { Button, Input, Card } from '../common';
import StockSearchInput from './StockSearchInput';
import { api } from '../../services/api';

interface TradeFormData {
  trade_date: string;
  stock_code: string;
  stock_name: string;
  action: 'BUY' | 'SELL';
  quantity: number;
  price: number;
  reason: string;
}

interface InitialValues {
  stock_code: string;
  stock_name: string;
  quantity: number;
  price: number;
  reason?: string;
}

interface TradeInputFormProps {
  onSuccess?: () => void;
  initialValues?: InitialValues | null;
}

export default function TradeInputForm({
  onSuccess,
  initialValues,
}: TradeInputFormProps) {
  const today = new Date().toISOString().split('T')[0];

  const [formData, setFormData] = useState<TradeFormData>({
    trade_date: today,
    stock_code: '',
    stock_name: '',
    action: 'BUY',
    quantity: 0,
    price: 0,
    reason: '',
  });

  const [errors, setErrors] = useState<Record<string, string>>({});
  const [isLoading, setIsLoading] = useState(false);
  const [successMessage, setSuccessMessage] = useState('');

  // Update form when initialValues change (from recommendation selection)
  useEffect(() => {
    if (initialValues) {
      setFormData((prev) => ({
        ...prev,
        stock_code: initialValues.stock_code,
        stock_name: initialValues.stock_name,
        quantity: initialValues.quantity,
        price: initialValues.price,
        reason: initialValues.reason || 'squeeze_breakout_buy',
        action: 'BUY',
      }));
      setSuccessMessage('');
      setErrors({});
    }
  }, [initialValues]);

  const validate = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!formData.trade_date) {
      newErrors.trade_date = '거래일을 입력하세요';
    }

    if (!formData.stock_code || !/^[0-9]{6}$/.test(formData.stock_code)) {
      newErrors.stock_code = '6자리 종목코드를 입력하세요';
    }

    if (formData.quantity <= 0) {
      newErrors.quantity = '수량은 0보다 커야 합니다';
    }

    if (formData.price <= 0) {
      newErrors.price = '가격은 0보다 커야 합니다';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validate()) return;

    setIsLoading(true);
    setSuccessMessage('');

    try {
      await api.post('/trades', {
        trade_date: formData.trade_date,
        stock_code: formData.stock_code,
        action: formData.action,
        quantity: formData.quantity,
        price: formData.price,
        reason: formData.reason || undefined,
      });

      const actionText = formData.action === 'BUY' ? '매수' : '매도';
      const totalAmount = (formData.quantity * formData.price).toLocaleString();
      setSuccessMessage(
        `${formData.stock_name || formData.stock_code} ${formData.quantity}주 ${actionText} 완료 (${totalAmount}원)`
      );

      // Reset form
      setFormData({
        trade_date: today,
        stock_code: '',
        stock_name: '',
        action: 'BUY',
        quantity: 0,
        price: 0,
        reason: '',
      });

      onSuccess?.();
    } catch (err) {
      const error = err as { detail?: string };
      setErrors({ submit: error.detail || '거래 등록에 실패했습니다' });
    } finally {
      setIsLoading(false);
    }
  };

  const handleStockChange = (code: string, name: string) => {
    setFormData((prev) => ({
      ...prev,
      stock_code: code,
      stock_name: name,
    }));
  };

  const totalAmount = formData.quantity * formData.price;

  return (
    <Card>
      <h2 className="text-xl font-semibold mb-4">거래 입력</h2>

      {successMessage && (
        <div className="mb-4 p-3 bg-green-100 text-green-700 rounded-lg text-sm">
          {successMessage}
        </div>
      )}

      {errors.submit && (
        <div className="mb-4 p-3 bg-red-100 text-red-700 rounded-lg text-sm">
          {errors.submit}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-4">
        {/* Trade Date */}
        <Input
          label="거래일"
          type="date"
          value={formData.trade_date}
          onChange={(e) =>
            setFormData((prev) => ({ ...prev, trade_date: e.target.value }))
          }
          error={errors.trade_date}
          max={today}
        />

        {/* Action Toggle */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            거래유형
          </label>
          <div className="flex space-x-2">
            <button
              type="button"
              className={`flex-1 py-2 px-4 rounded-lg font-medium transition-colors ${
                formData.action === 'BUY'
                  ? 'bg-red-600 text-white'
                  : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
              }`}
              onClick={() =>
                setFormData((prev) => ({ ...prev, action: 'BUY' }))
              }
            >
              매수
            </button>
            <button
              type="button"
              className={`flex-1 py-2 px-4 rounded-lg font-medium transition-colors ${
                formData.action === 'SELL'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
              }`}
              onClick={() =>
                setFormData((prev) => ({ ...prev, action: 'SELL' }))
              }
            >
              매도
            </button>
          </div>
        </div>

        {/* Stock Search */}
        <StockSearchInput
          value={formData.stock_code}
          onChange={handleStockChange}
          error={errors.stock_code}
        />

        {/* Quantity */}
        <Input
          label="수량"
          type="number"
          value={formData.quantity || ''}
          onChange={(e) =>
            setFormData((prev) => ({
              ...prev,
              quantity: parseInt(e.target.value) || 0,
            }))
          }
          error={errors.quantity}
          min={1}
          placeholder="주"
        />

        {/* Price */}
        <Input
          label="가격"
          type="number"
          value={formData.price || ''}
          onChange={(e) =>
            setFormData((prev) => ({
              ...prev,
              price: parseFloat(e.target.value) || 0,
            }))
          }
          error={errors.price}
          min={1}
          step={1}
          placeholder="원"
        />

        {/* Total Amount Display */}
        {totalAmount > 0 && (
          <div className="p-3 bg-gray-50 rounded-lg">
            <span className="text-sm text-gray-600">거래금액: </span>
            <span className="font-semibold text-lg">
              {totalAmount.toLocaleString()}원
            </span>
          </div>
        )}

        {/* Reason */}
        <Input
          label="거래사유 (선택)"
          value={formData.reason}
          onChange={(e) =>
            setFormData((prev) => ({ ...prev, reason: e.target.value }))
          }
          placeholder="예: 스퀴즈 브레이크아웃"
          maxLength={100}
        />

        {/* Submit */}
        <Button type="submit" isLoading={isLoading} className="w-full">
          {formData.action === 'BUY' ? '매수 등록' : '매도 등록'}
        </Button>
      </form>
    </Card>
  );
}
