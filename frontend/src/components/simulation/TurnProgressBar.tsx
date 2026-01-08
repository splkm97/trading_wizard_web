/**
 * TurnProgressBar - Display game progress with Next Day button
 * 
 * Shows current date, progress bar from start to end date,
 * and a button to advance to the next trading day.
 */

import { Button } from '../common/Button';

interface TurnProgressBarProps {
  currentDate: string;
  startDate: string;
  endDate: string;
  isGameOver: boolean;
  isLoading?: boolean;
  onAdvanceTurn: () => void;
}

export function TurnProgressBar({
  currentDate,
  startDate,
  endDate,
  isGameOver,
  isLoading = false,
  onAdvanceTurn,
}: TurnProgressBarProps) {
  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    return `${date.getFullYear()}.${String(date.getMonth() + 1).padStart(2, '0')}.${String(date.getDate()).padStart(2, '0')}`;
  };

  const progress = (() => {
    const start = new Date(startDate).getTime();
    const end = new Date(endDate).getTime();
    const current = new Date(currentDate).getTime();
    return Math.min(100, Math.max(0, ((current - start) / (end - start)) * 100));
  })();

  return (
    <div className="flex items-center gap-4 flex-1">
      {/* Current Date Display */}
      <div className="flex items-center gap-2">
        <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
        <span className="text-sm font-semibold text-gray-900">
          {formatDate(currentDate)}
        </span>
      </div>

      {/* Progress Bar */}
      <div className="flex-1 max-w-xs">
        <div className="flex items-center justify-between text-xs text-gray-500 mb-1">
          <span>{formatDate(startDate)}</span>
          <span className="font-medium text-gray-700">{progress.toFixed(0)}%</span>
          <span>{formatDate(endDate)}</span>
        </div>
        <div className="h-2 bg-gray-200 rounded-full overflow-hidden shadow-inner">
          <div
            className="h-full bg-gradient-to-r from-primary-500 via-primary-600 to-emerald-500 rounded-full transition-all duration-500 ease-out"
            style={{ width: `${progress}%` }}
          />
        </div>
      </div>

      {/* Next Day Button or Game Over Message */}
      {isGameOver ? (
        <div className="px-4 py-2 bg-gradient-to-r from-amber-100 to-orange-100 border border-amber-300 rounded-lg">
          <span className="text-sm font-semibold text-amber-800">
            게임 종료
          </span>
        </div>
      ) : (
        <Button
          variant="primary"
          size="sm"
          onClick={onAdvanceTurn}
          disabled={isLoading}
          isLoading={isLoading}
          className="whitespace-nowrap shadow-sm hover:shadow-md transition-shadow"
        >
          {isLoading ? '처리중...' : '다음 날 →'}
        </Button>
      )}
    </div>
  );
}
