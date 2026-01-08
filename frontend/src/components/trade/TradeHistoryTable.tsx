import { Trade } from '../../types';
import { Table } from '../common/Table';
import { Button } from '../common/Button';

interface TradeHistoryTableProps {
  trades: Trade[];
  isLoading?: boolean;
  onDelete?: (tradeId: string) => void;
  isDeleting?: string | null;
}

export function TradeHistoryTable({
  trades,
  isLoading = false,
  onDelete,
  isDeleting,
}: TradeHistoryTableProps) {
  const formatCurrency = (value: number) =>
    new Intl.NumberFormat('ko-KR', {
      style: 'currency',
      currency: 'KRW',
      maximumFractionDigits: 0,
    }).format(value);

  const formatPnL = (value: number | null) => {
    if (value === null) return '-';
    const formatted = formatCurrency(Math.abs(value));
    if (value > 0) return <span className="text-green-600">+{formatted}</span>;
    if (value < 0) return <span className="text-red-600">-{formatted}</span>;
    return formatted;
  };

  const columns = [
    {
      key: 'trade_date',
      header: '거래일',
      render: (trade: Trade) => trade.trade_date,
    },
    {
      key: 'stock_code',
      header: '종목코드',
      render: (trade: Trade) => (
        <span className="font-mono text-sm">{trade.stock_code}</span>
      ),
    },
    {
      key: 'stock_name',
      header: '종목명',
    },
    {
      key: 'action',
      header: '거래유형',
      render: (trade: Trade) => (
        <span
          className={`px-2 py-1 rounded-full text-xs font-medium ${
            trade.action === 'BUY'
              ? 'bg-red-100 text-red-800'
              : 'bg-blue-100 text-blue-800'
          }`}
        >
          {trade.action === 'BUY' ? '매수' : '매도'}
        </span>
      ),
    },
    {
      key: 'quantity',
      header: '수량',
      className: 'text-right',
      render: (trade: Trade) => (
        <span className="font-mono">{trade.quantity.toLocaleString()}</span>
      ),
    },
    {
      key: 'price',
      header: '단가',
      className: 'text-right',
      render: (trade: Trade) => formatCurrency(trade.price),
    },
    {
      key: 'total_amount',
      header: '거래금액',
      className: 'text-right',
      render: (trade: Trade) => formatCurrency(trade.total_amount),
    },
    {
      key: 'realized_pnl',
      header: '실현손익',
      className: 'text-right',
      render: (trade: Trade) => formatPnL(trade.realized_pnl),
    },
    {
      key: 'reason',
      header: '사유',
      render: (trade: Trade) => (
        <span className="text-gray-500 text-sm truncate max-w-[150px] block">
          {trade.reason || '-'}
        </span>
      ),
    },
    ...(onDelete
      ? [
          {
            key: 'actions',
            header: '',
            render: (trade: Trade) => (
              <Button
                variant="danger"
                size="sm"
                onClick={() => onDelete(trade.id)}
                disabled={isDeleting === trade.id}
                isLoading={isDeleting === trade.id}
              >
                삭제
              </Button>
            ),
          },
        ]
      : []),
  ];

  return (
    <Table
      columns={columns}
      data={trades}
      keyExtractor={(trade, _i) => trade.id}
      emptyMessage="거래 이력이 없습니다."
      isLoading={isLoading}
    />
  );
}
