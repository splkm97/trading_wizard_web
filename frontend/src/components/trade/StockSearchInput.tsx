import { useState, useEffect, useRef } from 'react';
import { api } from '../../services/api';
import { Input } from '../common';

interface Stock {
  code: string;
  name: string;
}

interface StockSearchInputProps {
  value: string;
  onChange: (code: string, name: string) => void;
  error?: string;
}

export default function StockSearchInput({
  value,
  onChange,
  error,
}: StockSearchInputProps) {
  const [query, setQuery] = useState(value);
  const [results, setResults] = useState<Stock[]>([]);
  const [isOpen, setIsOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [selectedName, setSelectedName] = useState('');
  const wrapperRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Close dropdown when clicking outside
    function handleClickOutside(event: MouseEvent) {
      if (wrapperRef.current && !wrapperRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    }

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  useEffect(() => {
    const searchStocks = async () => {
      if (query.length < 1) {
        setResults([]);
        return;
      }

      setIsLoading(true);
      try {
        const response = await api.get<{ results: Stock[] }>(
          `/stocks/search?q=${encodeURIComponent(query)}&limit=10`
        );
        setResults(response.results);
        setIsOpen(true);
      } catch (err) {
        console.error('Stock search failed:', err);
        setResults([]);
      } finally {
        setIsLoading(false);
      }
    };

    const debounce = setTimeout(searchStocks, 300);
    return () => clearTimeout(debounce);
  }, [query]);

  const handleSelect = (stock: Stock) => {
    setQuery(stock.code);
    setSelectedName(stock.name);
    onChange(stock.code, stock.name);
    setIsOpen(false);
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = e.target.value;
    setQuery(val);
    setSelectedName('');
    if (val.length === 6 && /^[0-9]{6}$/.test(val)) {
      // If user types a valid 6-digit code, auto-lookup
      const stock = results.find((s) => s.code === val);
      if (stock) {
        onChange(stock.code, stock.name);
      }
    }
  };

  return (
    <div ref={wrapperRef} className="relative">
      <Input
        label="종목코드"
        value={query}
        onChange={handleInputChange}
        onFocus={() => query.length > 0 && results.length > 0 && setIsOpen(true)}
        placeholder="종목코드 또는 이름 검색"
        error={error}
        maxLength={6}
      />

      {selectedName && (
        <div className="text-sm text-gray-600 mt-1">{selectedName}</div>
      )}

      {isOpen && results.length > 0 && (
        <div className="absolute z-10 w-full mt-1 bg-white border border-gray-300 rounded-lg shadow-lg max-h-60 overflow-auto">
          {isLoading && (
            <div className="px-4 py-2 text-gray-500">검색 중...</div>
          )}
          {results.map((stock) => (
            <button
              key={stock.code}
              type="button"
              className="w-full px-4 py-2 text-left hover:bg-gray-100 focus:bg-gray-100 focus:outline-none"
              onClick={() => handleSelect(stock)}
            >
              <span className="font-mono text-sm">{stock.code}</span>
              <span className="ml-2 text-gray-700">{stock.name}</span>
            </button>
          ))}
        </div>
      )}

      {isOpen && query.length > 0 && results.length === 0 && !isLoading && (
        <div className="absolute z-10 w-full mt-1 bg-white border border-gray-300 rounded-lg shadow-lg px-4 py-2 text-gray-500">
          검색 결과가 없습니다
        </div>
      )}
    </div>
  );
}
