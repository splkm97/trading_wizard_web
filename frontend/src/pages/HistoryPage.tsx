import { useState, useEffect, useCallback } from 'react';
import { Card } from '../components/common/Card';
import { Button } from '../components/common/Button';
import { TradeHistoryTable } from '../components/trade/TradeHistoryTable';
import { TradeFilter, TradeFilters } from '../components/trade/TradeFilter';
import { Trade } from '../types';
import { api } from '../services/api';

interface TradeListResponse {
  trades: Trade[];
  total: number;
  page: number;
  page_size: number;
}

export function HistoryPage() {
  const [trades, setTrades] = useState<Trade[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filters, setFilters] = useState<TradeFilters>({});
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [total, setTotal] = useState(0);
  const [isDeleting, setIsDeleting] = useState<string | null>(null);
  const [isExporting, setIsExporting] = useState(false);

  const PAGE_SIZE = 20;

  const fetchTrades = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams();
      if (filters.stockCode) params.set('stock_code', filters.stockCode);
      if (filters.action) params.set('action', filters.action);
      if (filters.startDate) params.set('start_date', filters.startDate);
      if (filters.endDate) params.set('end_date', filters.endDate);
      params.set('page', String(page));
      params.set('page_size', String(PAGE_SIZE));

      const response = await api.get<TradeListResponse>(
        `/trades?${params.toString()}`
      );
      setTrades(response.trades);
      setTotal(response.total);
      setTotalPages(Math.ceil(response.total / PAGE_SIZE));
    } catch (err) {
      setError('거래 이력을 불러오는데 실패했습니다.');
      console.error('Failed to fetch trades:', err);
    } finally {
      setIsLoading(false);
    }
  }, [filters, page]);

  useEffect(() => {
    fetchTrades();
  }, [fetchTrades]);

  const handleFilterChange = (newFilters: TradeFilters) => {
    setFilters(newFilters);
    setPage(1); // Reset to first page on filter change
  };

  const handleDelete = async (tradeId: string) => {
    if (!confirm('이 거래를 삭제하시겠습니까? 포트폴리오가 롤백됩니다.')) {
      return;
    }

    setIsDeleting(tradeId);
    try {
      await api.delete(`/trades/${tradeId}`);
      fetchTrades();
    } catch (err) {
      setError('거래 삭제에 실패했습니다.');
      console.error('Failed to delete trade:', err);
    } finally {
      setIsDeleting(null);
    }
  };

  const handleExport = async () => {
    setIsExporting(true);
    try {
      const params = new URLSearchParams();
      if (filters.stockCode) params.set('stock_code', filters.stockCode);
      if (filters.action) params.set('action', filters.action);
      if (filters.startDate) params.set('start_date', filters.startDate);
      if (filters.endDate) params.set('end_date', filters.endDate);

      const token = api.getToken();
      const response = await fetch(
        `${import.meta.env.VITE_API_URL || '/api'}/trades/export?${params.toString()}`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      if (!response.ok) {
        throw new Error('Export failed');
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download =
        response.headers
          .get('Content-Disposition')
          ?.split('filename=')[1] || 'trades.csv';
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err) {
      setError('CSV 내보내기에 실패했습니다.');
      console.error('Failed to export trades:', err);
    } finally {
      setIsExporting(false);
    }
  };

  return (
    <div className="container mx-auto px-4 py-6">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">거래 이력</h1>

      <TradeFilter
        filters={filters}
        onFilterChange={handleFilterChange}
        onExport={handleExport}
        isExporting={isExporting}
      />

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-4">
          {error}
        </div>
      )}

      <Card>
        <div className="p-4 border-b border-gray-200 flex justify-between items-center">
          <span className="text-sm text-gray-600">
            총 {total.toLocaleString()}건
          </span>
        </div>

        <TradeHistoryTable
          trades={trades}
          isLoading={isLoading}
          onDelete={handleDelete}
          isDeleting={isDeleting}
        />

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="p-4 border-t border-gray-200 flex justify-center items-center gap-2">
            <Button
              variant="secondary"
              size="sm"
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page === 1 || isLoading}
            >
              이전
            </Button>
            <span className="text-sm text-gray-600 px-4">
              {page} / {totalPages}
            </span>
            <Button
              variant="secondary"
              size="sm"
              onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
              disabled={page === totalPages || isLoading}
            >
              다음
            </Button>
          </div>
        )}
      </Card>
    </div>
  );
}
