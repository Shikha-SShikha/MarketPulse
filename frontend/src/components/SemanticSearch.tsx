import React, { useState } from 'react';
import { semanticSearchSignals } from '../api/signals';
import type { SemanticSearchResponse, SemanticSearchResult } from '../types';

interface SemanticSearchProps {
  onResultClick?: (signalId: string) => void;
  placeholder?: string;
  limit?: number;
  defaultThreshold?: number;
}

export function SemanticSearch({
  onResultClick,
  placeholder = "Ask a question... (e.g., 'What are competitors doing with AI integrity tools?')",
  limit = 20,
  defaultThreshold = 0.6,
}: SemanticSearchProps) {
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<SemanticSearchResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [threshold, setThreshold] = useState(defaultThreshold);
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [daysBack, setDaysBack] = useState<number | undefined>(undefined);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!query.trim() || query.trim().length < 3) {
      setError('Please enter at least 3 characters');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await semanticSearchSignals({
        q: query.trim(),
        limit,
        threshold,
        days_back: daysBack,
      });

      setResults(response);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to search. Please try again.');
      setResults(null);
    } finally {
      setLoading(false);
    }
  };

  const getSimilarityColor = (score: number): string => {
    if (score >= 0.8) return 'text-green-600 bg-green-50';
    if (score >= 0.7) return 'text-blue-600 bg-blue-50';
    if (score >= 0.6) return 'text-yellow-600 bg-yellow-50';
    return 'text-gray-600 bg-gray-50';
  };

  const getSimilarityLabel = (score: number): string => {
    if (score >= 0.8) return 'Highly Relevant';
    if (score >= 0.7) return 'Very Relevant';
    if (score >= 0.6) return 'Relevant';
    return 'Somewhat Relevant';
  };

  return (
    <div className="space-y-4">
      {/* Search Form */}
      <form onSubmit={handleSearch} className="space-y-3">
        <div className="relative">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder={placeholder}
            style={{ color: 'var(--cds-text-primary)', backgroundColor: 'var(--cds-field)' }}
            className="w-full px-4 py-3 pr-12 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            disabled={loading}
          />
          <button
            type="submit"
            disabled={loading || query.trim().length < 3}
            className="absolute right-2 top-1/2 -translate-y-1/2 p-2 text-blue-600 hover:text-blue-800 disabled:text-gray-400 disabled:cursor-not-allowed"
          >
            {loading ? (
              <svg className="animate-spin h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
            ) : (
              <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
            )}
          </button>
        </div>

        {/* Advanced Options */}
        <div className="flex items-center justify-between">
          <button
            type="button"
            onClick={() => setShowAdvanced(!showAdvanced)}
            className="text-sm text-gray-600 hover:text-gray-800 flex items-center gap-1"
          >
            <svg className={`h-4 w-4 transform transition-transform ${showAdvanced ? 'rotate-90' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
            </svg>
            Advanced Options
          </button>

          {results && (
            <span className="text-sm text-gray-600">
              {results.total} result{results.total !== 1 ? 's' : ''} for "{results.query}"
            </span>
          )}
        </div>

        {showAdvanced && (
          <div className="bg-gray-50 p-4 rounded-lg space-y-3">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Similarity Threshold
                  <span className="ml-2 text-xs text-gray-500">({(threshold * 100).toFixed(0)}%)</span>
                </label>
                <input
                  type="range"
                  min="0.5"
                  max="0.95"
                  step="0.05"
                  value={threshold}
                  onChange={(e) => setThreshold(parseFloat(e.target.value))}
                  className="w-full"
                />
                <div className="flex justify-between text-xs text-gray-500 mt-1">
                  <span>More Results</span>
                  <span>Higher Quality</span>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Time Range
                </label>
                <select
                  value={daysBack || ''}
                  onChange={(e) => setDaysBack(e.target.value ? parseInt(e.target.value) : undefined)}
                  style={{ color: 'var(--cds-text-primary)', backgroundColor: 'var(--cds-field)' }}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">All Time</option>
                  <option value="7">Last 7 Days</option>
                  <option value="30">Last 30 Days</option>
                  <option value="90">Last 90 Days</option>
                  <option value="365">Last Year</option>
                </select>
              </div>
            </div>
          </div>
        )}
      </form>

      {/* Error Message */}
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
          {error}
        </div>
      )}

      {/* Search Results */}
      {results && results.total > 0 && (
        <div className="space-y-3">
          {results.results.map((result: SemanticSearchResult) => (
            <div
              key={result.signal.id}
              onClick={() => onResultClick?.(result.signal.id)}
              className="bg-white border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow cursor-pointer"
            >
              {/* Header with similarity score */}
              <div className="flex items-start justify-between mb-2">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="font-semibold text-gray-900">{result.signal.entity}</span>
                    <span className="text-sm text-gray-500">•</span>
                    <span className="text-sm text-gray-600">{result.signal.topic}</span>
                    <span className="text-sm text-gray-500">•</span>
                    <span className="text-xs text-gray-500">
                      {new Date(result.signal.created_at).toLocaleDateString()}
                    </span>
                  </div>
                </div>

                <div className={`px-3 py-1 rounded-full text-xs font-medium ${getSimilarityColor(result.similarity_score)}`}>
                  {(result.similarity_score * 100).toFixed(0)}% {getSimilarityLabel(result.similarity_score)}
                </div>
              </div>

              {/* Evidence snippet */}
              <p className="text-sm text-gray-700 line-clamp-3 mb-2">
                {result.signal.evidence_snippet}
              </p>

              {/* Footer with metadata */}
              <div className="flex items-center gap-4 text-xs text-gray-500">
                <span className="flex items-center gap-1">
                  <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z" />
                  </svg>
                  {result.signal.event_type}
                </span>
                <span className="flex items-center gap-1">
                  <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                  </svg>
                  {result.signal.impact_areas.join(', ')}
                </span>
                <span className={`px-2 py-0.5 rounded ${
                  result.signal.confidence === 'High' ? 'bg-green-100 text-green-800' :
                  result.signal.confidence === 'Medium' ? 'bg-yellow-100 text-yellow-800' :
                  'bg-gray-100 text-gray-800'
                }`}>
                  {result.signal.confidence}
                </span>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Empty State */}
      {results && results.total === 0 && (
        <div className="bg-gray-50 border border-gray-200 rounded-lg p-8 text-center">
          <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
          <h3 className="mt-2 text-sm font-medium text-gray-900">No results found</h3>
          <p className="mt-1 text-sm text-gray-500">
            Try adjusting your search query or lowering the similarity threshold
          </p>
        </div>
      )}

      {/* Helper Text */}
      {!results && !error && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <p className="text-sm text-blue-800 font-medium mb-2">💡 Semantic Search Tips:</p>
          <ul className="text-sm text-blue-700 space-y-1 list-disc list-inside">
            <li>Ask natural language questions (e.g., "What are competitors doing with AI?")</li>
            <li>Search finds relevant signals even without exact keyword matches</li>
            <li>Higher similarity scores mean more relevant results</li>
            <li>Lower the threshold to see more results</li>
          </ul>
        </div>
      )}
    </div>
  );
}
