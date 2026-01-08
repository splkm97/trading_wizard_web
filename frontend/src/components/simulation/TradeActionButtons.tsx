/**
 * Trade Action Buttons - Buy/Skip for non-owned, Sell/Hold for owned stocks
 */

import { Button } from '../common/Button';

interface TradeActionButtonsProps {
  isOwned: boolean;
  isLoading: boolean;
  onBuy: () => void;
  onSkip: () => void;
  onSell: () => void;
  onHold: () => void;
}

export function TradeActionButtons({
  isOwned,
  isLoading,
  onBuy,
  onSkip,
  onSell,
  onHold,
}: TradeActionButtonsProps) {
  if (isOwned) {
    return (
      <div className="flex items-center gap-3">
        <Button
          variant="danger"
          size="lg"
          onClick={onSell}
          isLoading={isLoading}
          disabled={isLoading}
          className="flex-1 group relative overflow-hidden"
        >
          <span className="relative z-10 flex items-center justify-center gap-2">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
            </svg>
            매도 (Sell)
          </span>
        </Button>
        <Button
          variant="secondary"
          size="lg"
          onClick={onHold}
          disabled={isLoading}
          className="flex-1 group"
        >
          <span className="flex items-center justify-center gap-2">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            홀딩 (Hold)
          </span>
        </Button>
      </div>
    );
  }

  return (
    <div className="flex items-center gap-3">
      <Button
        variant="success"
        size="lg"
        onClick={onBuy}
        isLoading={isLoading}
        disabled={isLoading}
        className="flex-1 group relative overflow-hidden"
      >
        <span className="relative z-10 flex items-center justify-center gap-2">
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" transform="scale(1,-1) translate(0,-24)" />
          </svg>
          매수 (Buy)
        </span>
      </Button>
      <Button
        variant="secondary"
        size="lg"
        onClick={onSkip}
        disabled={isLoading}
        className="flex-1 group"
      >
        <span className="flex items-center justify-center gap-2">
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
          </svg>
          관망 (Skip)
        </span>
      </Button>
    </div>
  );
}
