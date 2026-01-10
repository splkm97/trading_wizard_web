import { useState } from 'react';

interface CollapsibleSectionProps {
  title: string;
  summary: string;
  children: React.ReactNode;
  defaultExpanded?: boolean;
}

export function CollapsibleSection({
  title,
  summary,
  children,
  defaultExpanded = false,
}: CollapsibleSectionProps) {
  const [isExpanded, setIsExpanded] = useState(defaultExpanded);

  return (
    <div className="border border-gray-200 rounded-lg overflow-hidden">
      <div className="bg-white p-4">
        <h3 className="text-lg font-semibold text-gray-900 mb-2">{title}</h3>
        <p className="text-gray-600 text-sm">{summary}</p>

        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className="mt-3 text-sm text-primary-600 hover:text-primary-700 font-medium flex items-center gap-1"
        >
          {isExpanded ? '접기' : '더 알아보기'}
          <svg
            className={`w-4 h-4 transition-transform ${isExpanded ? 'rotate-180' : ''}`}
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </button>
      </div>

      {isExpanded && (
        <div className="border-t border-gray-200 bg-gray-50 p-4">
          {children}
        </div>
      )}
    </div>
  );
}
