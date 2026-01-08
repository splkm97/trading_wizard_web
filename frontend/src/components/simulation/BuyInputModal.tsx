/**
 * Buy Input Modal - Modal for entering buy quantity or amount
 */

import { useState, useEffect, useCallback } from 'react';
import { Button } from '../common/Button';
import { Input } from '../common/Input';

interface BuyInputModalProps {
  isOpen: boolean;
  onClose: () => void;
  stockCode: string;
  stockName: string;
  currentPrice: number;
  availableCash: number;
  onConfirm: (params: { quantity?: number; amount?: number }) => void;
  isLoading?: boolean;
}

export function BuyInputModal({
  isOpen,
  onClose,
  stockCode,
  stockName,
  currentPrice,
  availableCash,
  onConfirm,
  isLoading = false,
}: BuyInputModalProps) {
  const [inputMode, setInputMode] = useState<'quantity' | 'amount'>('quantity');
  const [quantity, setQuantity] = useState<string>('');
  const [amount, setAmount] = useState<string>('');
  const [error, setError] = useState<string | null>(null);

  // Reset state when modal opens
  useEffect(() => {
    if (isOpen) {
      setQuantity('');
      setAmount('');
      setError(null);
      setInputMode('quantity');
    }
  }, [isOpen]);

  const formatCurrency = (value: number) =>
    new Intl.NumberFormat('ko-KR', {
      style: 'currency',
      currency: 'KRW',
      maximumFractionDigits: 0,
    }).format(value);

  // Calculate derived values
  const quantityNum = parseInt(quantity) || 0;
  const amountNum = parseInt(amount) || 0;

  const calculatedAmount = inputMode === 'quantity' ? quantityNum * currentPrice : amountNum;
  const calculatedQuantity = inputMode === 'amount' ? Math.floor(amountNum / currentPrice) : quantityNum;
  const totalCost = calculatedQuantity * currentPrice;

  // Validate input
  const validate = useCallback(() => {
    if (inputMode === 'quantity') {
      if (quantityNum <= 0) {
        setError('수량을 입력해주세요');
        return false;
      }
      if (calculatedAmount > availableCash) {
        setError(`보유 현금이 부족합니다 (필요: ${formatCurrency(calculatedAmount)})`);
        return false;
      }
    } else {
      if (amountNum <= 0) {
        setError('금액을 입력해주세요');
        return false;
      }
      if (amountNum > availableCash) {
        setError(`보유 현금이 부족합니다 (가용: ${formatCurrency(availableCash)})`);
        return false;
      }
      if (calculatedQuantity <= 0) {
        setError(`최소 1주 이상 매수 가능합니다 (1주 가격: ${formatCurrency(currentPrice)})`);
        return false;
      }
    }
    setError(null);
    return true;
  }, [inputMode, quantityNum, amountNum, calculatedAmount, calculatedQuantity, availableCash, currentPrice]);

  useEffect(() => {
    if (quantity || amount) {
      validate();
    }
  }, [quantity, amount, validate]);

  const handleConfirm = () => {
    if (!validate()) return;

    if (inputMode === 'quantity') {
      onConfirm({ quantity: quantityNum });
    } else {
      onConfirm({ amount: amountNum });
    }
  };

  const handleMaxBuy = () => {
    const maxQuantity = Math.floor(availableCash / currentPrice);
    if (maxQuantity > 0) {
      setInputMode('quantity');
      setQuantity(maxQuantity.toString());
      setAmount('');
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !error && (quantity || amount)) {
      handleConfirm();
    }
    if (e.key === 'Escape') {
      onClose();
    }
  };

  if (!isOpen) return null;

  const maxQuantity = Math.floor(availableCash / currentPrice);

  return (
    <div 
      className="fixed inset-0 z-50 flex items-center justify-center"
      onKeyDown={handleKeyDown}
    >
      {/* Backdrop */}
      <div 
        className="absolute inset-0 bg-black/60 backdrop-blur-sm"
        onClick={onClose}
      />
      
      {/* Modal */}
      <div className="relative bg-white rounded-2xl shadow-2xl w-full max-w-md mx-4 overflow-hidden animate-in fade-in zoom-in-95 duration-200">
        {/* Header */}
        <div className="bg-gradient-to-r from-green-500 to-emerald-600 px-6 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-lg font-bold text-white">매수 주문</h3>
              <p className="text-green-100 text-sm">{stockName} ({stockCode})</p>
            </div>
            <button
              onClick={onClose}
              className="p-1 rounded-full hover:bg-white/20 transition-colors"
            >
              <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>

        {/* Price Info */}
        <div className="px-6 py-4 bg-gray-50 border-b border-gray-200">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <p className="text-xs text-gray-500 mb-1">현재가</p>
              <p className="text-xl font-bold text-gray-900">{formatCurrency(currentPrice)}</p>
            </div>
            <div>
              <p className="text-xs text-gray-500 mb-1">가용 현금</p>
              <p className="text-xl font-bold text-primary-600">{formatCurrency(availableCash)}</p>
            </div>
          </div>
        </div>

        {/* Input Section */}
        <div className="px-6 py-5 space-y-4">
          {/* Input Mode Toggle */}
          <div className="flex rounded-lg bg-gray-100 p-1">
            <button
              type="button"
              onClick={() => {
                setInputMode('quantity');
                setAmount('');
              }}
              className={`flex-1 py-2 text-sm font-medium rounded-md transition-all ${
                inputMode === 'quantity'
                  ? 'bg-white text-gray-900 shadow-sm'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              수량으로 입력
            </button>
            <button
              type="button"
              onClick={() => {
                setInputMode('amount');
                setQuantity('');
              }}
              className={`flex-1 py-2 text-sm font-medium rounded-md transition-all ${
                inputMode === 'amount'
                  ? 'bg-white text-gray-900 shadow-sm'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              금액으로 입력
            </button>
          </div>

          {/* Input Fields */}
          {inputMode === 'quantity' ? (
            <div className="space-y-2">
              <div className="flex items-end gap-2">
                <div className="flex-1">
                  <Input
                    label="매수 수량"
                    type="number"
                    value={quantity}
                    onChange={(e) => setQuantity(e.target.value)}
                    placeholder="0"
                    min={1}
                    max={maxQuantity}
                    autoFocus
                  />
                </div>
                <span className="pb-2 text-gray-500 font-medium">주</span>
              </div>
              <div className="flex items-center justify-between text-sm">
                <span className="text-gray-500">최대 매수 가능: {maxQuantity.toLocaleString()}주</span>
                <button
                  type="button"
                  onClick={handleMaxBuy}
                  className="text-primary-600 hover:text-primary-700 font-medium"
                >
                  최대 매수
                </button>
              </div>
            </div>
          ) : (
            <div className="space-y-2">
              <div className="flex items-end gap-2">
                <div className="flex-1">
                  <Input
                    label="매수 금액"
                    type="number"
                    value={amount}
                    onChange={(e) => setAmount(e.target.value)}
                    placeholder="0"
                    min={currentPrice}
                    max={availableCash}
                    step={10000}
                    autoFocus
                  />
                </div>
                <span className="pb-2 text-gray-500 font-medium">원</span>
              </div>
              <div className="flex items-center justify-between text-sm">
                <span className="text-gray-500">가용 현금: {formatCurrency(availableCash)}</span>
                <button
                  type="button"
                  onClick={() => setAmount(availableCash.toString())}
                  className="text-primary-600 hover:text-primary-700 font-medium"
                >
                  전액 사용
                </button>
              </div>
            </div>
          )}

          {/* Preview */}
          {(quantityNum > 0 || (amountNum > 0 && calculatedQuantity > 0)) && (
            <div className="p-4 bg-green-50 rounded-xl border border-green-200">
              <p className="text-sm text-green-800 font-medium mb-2">예상 매수</p>
              <div className="flex items-center justify-between">
                <span className="text-green-700">
                  {calculatedQuantity.toLocaleString()}주 x {formatCurrency(currentPrice)}
                </span>
                <span className="text-lg font-bold text-green-800">
                  = {formatCurrency(totalCost)}
                </span>
              </div>
              {inputMode === 'amount' && amountNum > totalCost && (
                <p className="text-xs text-green-600 mt-2">
                  * 잔액 {formatCurrency(amountNum - totalCost)}는 반환됩니다
                </p>
              )}
            </div>
          )}

          {/* Error Message */}
          {error && (
            <div className="p-3 bg-red-50 rounded-lg border border-red-200">
              <p className="text-sm text-red-600 flex items-center gap-2">
                <svg className="w-4 h-4 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                {error}
              </p>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-4 bg-gray-50 border-t border-gray-200 flex items-center gap-3">
          <Button
            variant="secondary"
            size="lg"
            onClick={onClose}
            disabled={isLoading}
            className="flex-1"
          >
            취소
          </Button>
          <Button
            variant="success"
            size="lg"
            onClick={handleConfirm}
            isLoading={isLoading}
            disabled={isLoading || !!error || (!quantity && !amount)}
            className="flex-1"
          >
            매수 확인
          </Button>
        </div>
      </div>
    </div>
  );
}
