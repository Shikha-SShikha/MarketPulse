import { useState } from 'react';
import { ChevronDown, ChevronUp } from 'lucide-react';
import SignalEvidence from './SignalEvidence';
import type { Theme } from '../types';

interface ThemeCardProps {
  theme: Theme;
  rank: number;
}

export default function ThemeCard({ theme, rank }: ThemeCardProps) {
  const [expanded, setExpanded] = useState(false);
  const [showFullSoWhat, setShowFullSoWhat] = useState(false);
  const [showNextSteps, setShowNextSteps] = useState(false);

  const confidenceColor = {
    High: 'bg-green-100 text-green-800 border-green-200',
    Medium: 'bg-yellow-100 text-yellow-800 border-yellow-200',
    Low: 'bg-red-100 text-red-800 border-red-200',
  }[theme.aggregate_confidence] || 'bg-gray-100 text-gray-800 border-gray-200';

  // Split So What into sentences for bullet points
  const soWhatSentences = theme.so_what
    .split(/(?<=[.!?])\s+/)
    .filter(s => s.trim().length > 0);

  // Determine if we should show "Read more" button
  const hasMultipleSentences = soWhatSentences.length > 2;
  const shouldShowReadMore = hasMultipleSentences;

  const impactAreaColors: Record<string, string> = {
    Ops: 'bg-blue-100 text-blue-800',
    Tech: 'bg-purple-100 text-purple-800',
    Integrity: 'bg-orange-100 text-orange-800',
    Procurement: 'bg-teal-100 text-teal-800',
  };

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
      {/* Theme Header */}
      <div className="p-4 sm:p-6">
        <div className="flex items-start gap-3 mb-3">
          <span className="flex-shrink-0 w-8 h-8 flex items-center justify-center bg-gray-900 text-white text-sm font-bold rounded-full">
            {rank}
          </span>
          <div className="flex-1 min-w-0">
            <h3 className="text-lg font-semibold text-gray-900 leading-tight">
              {theme.title}
            </h3>
            <div className="flex flex-wrap gap-2 mt-2">
              {theme.impact_areas.map((area) => (
                <span
                  key={area}
                  className={`px-2 py-0.5 text-xs font-medium rounded ${
                    impactAreaColors[area] || 'bg-gray-100 text-gray-800'
                  }`}
                >
                  {area}
                </span>
              ))}
              <span className={`px-2 py-0.5 text-xs font-medium rounded border ${confidenceColor}`}>
                {theme.aggregate_confidence} Confidence
              </span>
            </div>
          </div>
        </div>

        {/* So What - Bullet format with read more */}
        <div className="mb-4">
          <h4 className="text-sm font-medium text-gray-500 uppercase tracking-wide mb-2">
            Why It Matters
          </h4>
          <ul className="space-y-1.5">
            {(showFullSoWhat ? soWhatSentences : soWhatSentences.slice(0, 2)).map((sentence, idx) => (
              <li key={idx} className="flex items-start gap-2 text-gray-700 leading-relaxed">
                <span className="text-blue-500 mt-1 flex-shrink-0">•</span>
                <span>{sentence}</span>
              </li>
            ))}
          </ul>
          {shouldShowReadMore && (
            <button
              onClick={() => setShowFullSoWhat(!showFullSoWhat)}
              className="text-blue-600 hover:text-blue-800 text-sm font-medium mt-2"
            >
              {showFullSoWhat ? 'Show less' : 'Read more'}
            </button>
          )}
        </div>

        {/* Next Steps - Hidden by default */}
        <div className="mb-4">
          <button
            onClick={() => setShowNextSteps(!showNextSteps)}
            className="flex items-center gap-2 text-sm font-medium text-gray-500 uppercase tracking-wide mb-2 hover:text-gray-700 transition-colors"
          >
            <span>Next Steps</span>
            <span className="text-xs">({theme.now_what.length})</span>
            {showNextSteps ? (
              <ChevronUp className="w-4 h-4" />
            ) : (
              <ChevronDown className="w-4 h-4" />
            )}
          </button>
          {showNextSteps && (
            <ul className="space-y-1.5">
              {theme.now_what.map((action, idx) => (
                <li key={idx} className="flex items-start gap-2 text-gray-700">
                  <span className="text-blue-500 mt-1 flex-shrink-0">•</span>
                  <span>{action}</span>
                </li>
              ))}
            </ul>
          )}
        </div>

        {/* Key Players */}
        {theme.key_players.length > 0 && (
          <div className="text-sm text-gray-500">
            <span className="font-medium">Key Players:</span>{' '}
            {theme.key_players.join(', ')}
          </div>
        )}
      </div>

      {/* Evidence Toggle */}
      <div className="border-t border-gray-100">
        <button
          onClick={() => setExpanded(!expanded)}
          className="w-full px-4 sm:px-6 py-3 flex items-center justify-between text-sm font-medium text-gray-600 hover:bg-gray-50 transition-colors"
        >
          <span>
            {theme.signals.length} Supporting Signal{theme.signals.length !== 1 ? 's' : ''}
          </span>
          {expanded ? (
            <ChevronUp className="w-4 h-4" />
          ) : (
            <ChevronDown className="w-4 h-4" />
          )}
        </button>

        {/* Expanded Evidence */}
        {expanded && (
          <div className="px-4 sm:px-6 pb-4 space-y-3 bg-gray-50">
            {theme.signals.map((signal) => (
              <SignalEvidence key={signal.id} signal={signal} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
