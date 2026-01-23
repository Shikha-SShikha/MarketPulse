import { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { ExternalLink, AlertCircle, RefreshCw } from 'lucide-react';
import {
  Header,
  HeaderContainer,
  HeaderName,
  HeaderGlobalBar,
  HeaderGlobalAction,
  SkipToContent,
} from '@carbon/react';
import { Home } from '@carbon/icons-react';
import NotificationBell from '../components/NotificationBell';
import { getSignals } from '../api/signals';
import { getErrorMessage } from '../utils/errorHandling';
import type { Signal } from '../types';

const SEGMENT_CONFIG = {
  customer: {
    label: 'Customers',
    icon: '👥',
    color: 'blue',
    bgColor: 'bg-blue-50',
    borderColor: 'border-blue-500',
    textColor: 'text-blue-700',
    badgeBg: 'bg-blue-100',
    badgeText: 'text-blue-800',
  },
  competitor: {
    label: 'Competitors',
    icon: '⚔️',
    color: 'red',
    bgColor: 'bg-red-50',
    borderColor: 'border-red-500',
    textColor: 'text-red-700',
    badgeBg: 'bg-red-100',
    badgeText: 'text-red-800',
  },
  industry: {
    label: 'Industry',
    icon: '🏛️',
    color: 'green',
    bgColor: 'bg-green-50',
    borderColor: 'border-green-500',
    textColor: 'text-green-700',
    badgeBg: 'bg-green-100',
    badgeText: 'text-green-800',
  },
  influencer: {
    label: 'Influencers',
    icon: '⭐',
    color: 'purple',
    bgColor: 'bg-purple-50',
    borderColor: 'border-purple-500',
    textColor: 'text-purple-700',
    badgeBg: 'bg-purple-100',
    badgeText: 'text-purple-800',
  },
};

export default function SegmentSignals() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const segment = searchParams.get('segment') || '';

  const [signals, setSignals] = useState<Signal[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const config = SEGMENT_CONFIG[segment as keyof typeof SEGMENT_CONFIG];

  useEffect(() => {
    if (segment) {
      loadSignals();
    }
  }, [segment]);

  async function loadSignals() {
    setLoading(true);
    setError(null);
    try {
      const response = await getSignals({ segment, limit: 100 });
      setSignals(response.signals);
      setTotal(response.total);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    });
  };

  if (!segment || !config) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <AlertCircle className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-gray-900 mb-2">Invalid Segment</h2>
          <p className="text-gray-600 mb-4">The requested segment could not be found.</p>
          <button
            onClick={() => navigate('/')}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
          >
            Back to Dashboard
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen" style={{ background: 'var(--cds-background)' }}>
      <HeaderContainer
        render={() => (
          <Header aria-label="MarketPulse">
            <SkipToContent />
            <HeaderName href="#" prefix="" onClick={(e) => {
              e.preventDefault();
              navigate('/');
            }}>
              MarketPulse
            </HeaderName>
            <HeaderGlobalBar>
              <div style={{ display: 'flex', alignItems: 'center', paddingRight: '1rem' }}>
                <NotificationBell />
              </div>
              <HeaderGlobalAction
                aria-label="Back to Dashboard"
                tooltipAlignment="end"
                onClick={() => navigate('/')}
              >
                <Home size={20} />
              </HeaderGlobalAction>
            </HeaderGlobalBar>
          </Header>
        )}
      />

      {/* Page Header */}
      <div className="cds--content" style={{
        background: `var(--cds-layer-01)`,
        borderBottom: `4px solid var(--cds-${config.color})`,
        padding: '1.5rem 2rem'
      }}>
        <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
          <div className="flex items-center gap-3 mb-2">
            <span style={{ fontSize: '2rem' }}>{config.icon}</span>
            <h1 style={{
              fontSize: '1.75rem',
              fontWeight: 600,
              color: 'var(--cds-text-primary)'
            }}>
              {config.label}
            </h1>
          </div>
          <p style={{
            fontSize: '0.875rem',
            color: 'var(--cds-text-secondary)'
          }}>
            {total} signal{total !== 1 ? 's' : ''} from {config.label.toLowerCase()} entities
          </p>
        </div>
      </div>

      <main className="cds--content" style={{ padding: '2rem', maxWidth: '1200px', margin: '0 auto' }}>
        {/* Loading State */}
        {loading && (
          <div className="flex items-center justify-center py-16">
            <RefreshCw className="w-6 h-6 text-gray-400 animate-spin" />
            <span className="ml-3 text-gray-600">Loading signals...</span>
          </div>
        )}

        {/* Error State */}
        {error && !loading && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
            <div>
              <p className="text-red-800 font-medium">Error loading signals</p>
              <p className="text-red-600 text-sm mt-1">{error}</p>
              <button
                onClick={loadSignals}
                className="mt-3 text-sm text-red-700 hover:text-red-800 underline"
              >
                Try again
              </button>
            </div>
          </div>
        )}

        {/* Empty State */}
        {!loading && !error && signals.length === 0 && (
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-12 text-center">
            <div className="text-6xl mb-4">{config.icon}</div>
            <h2 className="text-xl font-semibold text-gray-900 mb-2">
              No {config.label} Signals Yet
            </h2>
            <p className="text-gray-600 mb-6">
              There are no signals from {config.label.toLowerCase()} entities in the database yet.
            </p>
            <button
              onClick={() => navigate('/')}
              className="px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700"
            >
              Back to Dashboard
            </button>
          </div>
        )}

        {/* Signals List */}
        {!loading && signals.length > 0 && (
          <div className="space-y-4">
            {signals.map((signal) => (
              <div
                key={signal.id}
                className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow"
              >
                <div className="flex items-start justify-between mb-3">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2 flex-wrap">
                      {/* Show entity badges from actual entities data if available */}
                      {signal.entities && signal.entities.length > 0 ? (
                        signal.entities.map((entity) => {
                          const entityConfig = SEGMENT_CONFIG[entity.segment as keyof typeof SEGMENT_CONFIG];
                          return (
                            <span
                              key={entity.id}
                              className={`px-3 py-1 text-sm font-medium rounded-full ${
                                entityConfig ? `${entityConfig.badgeBg} ${entityConfig.badgeText}` : 'bg-gray-100 text-gray-800'
                              }`}
                            >
                              {entityConfig?.icon} {entity.name}
                            </span>
                          );
                        })
                      ) : (
                        /* Fallback: show filter segment if entities not loaded */
                        <span className={`px-3 py-1 text-sm font-medium rounded-full ${config.badgeBg} ${config.badgeText}`}>
                          {config.icon} {signal.entity}
                        </span>
                      )}
                      <span className="px-2 py-1 text-xs font-medium bg-gray-100 text-gray-700 rounded">
                        {signal.event_type}
                      </span>
                      <span
                        className={`px-2 py-1 text-xs font-medium rounded ${
                          signal.confidence === 'High'
                            ? 'bg-green-100 text-green-800'
                            : signal.confidence === 'Medium'
                            ? 'bg-yellow-100 text-yellow-800'
                            : 'bg-red-100 text-red-800'
                        }`}
                      >
                        {signal.confidence}
                      </span>
                    </div>
                    <h3 className="text-lg font-semibold text-gray-900 mb-1">
                      {signal.topic}
                    </h3>
                    <p className="text-gray-600 text-sm mb-3">{signal.evidence_snippet}</p>
                    <div className="flex items-center gap-4 text-sm text-gray-500">
                      <span>{formatDate(signal.created_at)}</span>
                      {signal.impact_areas.length > 0 && (
                        <div className="flex gap-1">
                          {signal.impact_areas.map((area) => (
                            <span
                              key={area}
                              className="px-2 py-0.5 text-xs bg-gray-100 text-gray-700 rounded"
                            >
                              {area}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                  <a
                    href={signal.source_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="ml-4 text-blue-600 hover:text-blue-800 flex-shrink-0"
                    title="View source"
                  >
                    <ExternalLink className="w-5 h-5" />
                  </a>
                </div>
              </div>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}
