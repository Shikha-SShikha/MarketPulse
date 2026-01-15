import { ExternalLink } from 'lucide-react';
import type { Signal } from '../types';

interface SignalEvidenceProps {
  signal: Signal;
}

export default function SignalEvidence({ signal }: SignalEvidenceProps) {
  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    });
  };

  // Strip XML/HTML tags and extract headline (first sentence or first 100 chars)
  const getHeadline = (text: string): string => {
    // Remove XML/HTML tags
    const stripped = text.replace(/<[^>]*>/g, '');

    // Get first sentence (up to first period, exclamation, or question mark)
    const firstSentence = stripped.match(/^[^.!?]+[.!?]/);
    if (firstSentence) {
      return firstSentence[0].trim();
    }

    // Otherwise take first 100 characters
    return stripped.length > 100 ? stripped.substring(0, 100) + '...' : stripped;
  };

  const confidenceColor = {
    High: 'bg-green-100 text-green-800',
    Medium: 'bg-yellow-100 text-yellow-800',
    Low: 'bg-red-100 text-red-800',
  }[signal.confidence] || 'bg-gray-100 text-gray-800';

  const eventTypeLabel = signal.event_type.charAt(0).toUpperCase() + signal.event_type.slice(1);

  return (
    <div className="border-l-2 border-gray-200 pl-4 py-2 hover:border-blue-400 transition-colors">
      <div className="flex flex-wrap items-center gap-2 mb-1">
        <span className="font-medium text-gray-900">{signal.entity}</span>
        <span className="px-2 py-0.5 text-xs font-medium bg-gray-100 text-gray-700 rounded">
          {eventTypeLabel}
        </span>
        <span className={`px-2 py-0.5 text-xs font-medium rounded ${confidenceColor}`}>
          {signal.confidence}
        </span>
        <a
          href={signal.source_url}
          target="_blank"
          rel="noopener noreferrer"
          className="flex items-center gap-1 text-blue-600 hover:text-blue-800 hover:underline text-xs ml-auto"
        >
          <ExternalLink className="w-3 h-3" />
          Source
        </a>
      </div>

      <p className="text-gray-700 text-sm leading-relaxed">
        {getHeadline(signal.evidence_snippet)}
      </p>
    </div>
  );
}
