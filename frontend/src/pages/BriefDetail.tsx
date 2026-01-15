import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Calendar, Clock, AlertCircle, RefreshCw } from 'lucide-react';
import {
  Header,
  HeaderContainer,
  HeaderName,
  HeaderGlobalBar,
  HeaderGlobalAction,
  SkipToContent,
} from '@carbon/react';
import { Home } from '@carbon/icons-react';
import ThemeCard from '../components/ThemeCard';
import NotificationBell from '../components/NotificationBell';
import { getErrorMessage } from '../utils/errorHandling';
import type { WeeklyBrief } from '../types';

export default function BriefDetail() {
  const { briefId } = useParams<{ briefId: string }>();
  const navigate = useNavigate();
  const [brief, setBrief] = useState<WeeklyBrief | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (briefId) {
      loadBrief(briefId);
    }
  }, [briefId]);

  async function loadBrief(id: string) {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`http://localhost:8000/briefs/${id}`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      setBrief(data);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString('en-US', {
      month: 'long',
      day: 'numeric',
      year: 'numeric',
    });
  };

  const formatDateTime = (dateStr: string) => {
    return new Date(dateStr).toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: 'numeric',
      minute: '2-digit',
    });
  };

  return (
    <div className="min-h-screen" style={{ background: 'var(--cds-background)' }}>
      <HeaderContainer
        render={() => (
          <Header aria-label="MarketPulse">
            <SkipToContent />
            <HeaderName href="#" prefix="">
              MarketPulse
            </HeaderName>
            <HeaderGlobalBar>
              <div style={{ display: 'flex', alignItems: 'center', paddingRight: '1rem' }}>
                <NotificationBell />
              </div>
              <HeaderGlobalAction
                aria-label="Back to History"
                tooltipAlignment="end"
                onClick={() => navigate('/briefs/history')}
              >
                <Home size={20} />
              </HeaderGlobalAction>
            </HeaderGlobalBar>
          </Header>
        )}
      />

      {/* Page Header */}
      <div className="cds--content" style={{
        background: 'var(--cds-background)',
        borderBottom: '1px solid var(--cds-border-subtle)',
        padding: '1rem'
      }}>
        <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
          <h1 style={{
            fontSize: '1.75rem',
            fontWeight: 600,
            marginBottom: '0.25rem',
            color: 'var(--cds-text-primary)'
          }}>
            Weekly Brief
          </h1>
          <p style={{
            fontSize: '0.875rem',
            color: 'var(--cds-text-secondary)'
          }}>
            Intelligence summary
          </p>
        </div>
      </div>

      <main className="cds--content" style={{ padding: '1rem', maxWidth: '1200px', margin: '0 auto' }}>
        {/* Loading State */}
        {loading && (
          <div className="flex items-center justify-center py-16">
            <RefreshCw className="w-6 h-6 text-gray-400 animate-spin" />
            <span className="ml-3 text-gray-600">Loading brief...</span>
          </div>
        )}

        {/* Error State */}
        {error && !loading && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
            <div>
              <p className="text-red-800 font-medium">Error loading brief</p>
              <p className="text-red-600 text-sm mt-1">{error}</p>
              <button
                onClick={() => briefId && loadBrief(briefId)}
                className="mt-3 text-sm text-red-700 hover:text-red-800 underline"
              >
                Try again
              </button>
            </div>
          </div>
        )}

        {/* Brief Content */}
        {!loading && !error && brief && (
          <>
            {/* Brief Metadata */}
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 sm:p-6 mb-6">
              <div className="flex flex-col sm:flex-row sm:items-center gap-4 sm:gap-8">
                <div className="flex items-center gap-2 text-gray-600">
                  <Calendar className="w-5 h-5 text-gray-400" />
                  <span className="font-medium">
                    {formatDate(brief.week_start)} — {formatDate(brief.week_end)}
                  </span>
                </div>
                <div className="flex items-center gap-2 text-gray-500 text-sm">
                  <Clock className="w-4 h-4" />
                  <span>Generated {formatDateTime(brief.generated_at)}</span>
                </div>
              </div>

              {/* Summary Stats */}
              <div className="mt-4 pt-4 border-t border-gray-100 flex flex-wrap gap-4 sm:gap-8 text-sm">
                <div>
                  <span className="text-gray-500">Themes:</span>{' '}
                  <span className="font-semibold text-gray-900">{brief.themes.length}</span>
                </div>
                <div>
                  <span className="text-gray-500">Signals:</span>{' '}
                  <span className="font-semibold text-gray-900">{brief.total_signals}</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-gray-500">Coverage:</span>
                  <div className="flex gap-1">
                    {brief.coverage_areas.map((area) => (
                      <span
                        key={area}
                        className="px-2 py-0.5 text-xs font-medium bg-gray-100 text-gray-700 rounded"
                      >
                        {area}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            </div>

            {/* Themes */}
            <div className="space-y-4">
              <h2 className="text-lg font-semibold text-gray-900">
                This Week's Themes
              </h2>
              {brief.themes.map((theme, index) => (
                <ThemeCard key={theme.id} theme={theme} rank={index + 1} />
              ))}
            </div>
          </>
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-gray-200 mt-12">
        <div className="max-w-4xl mx-auto px-4 py-6 text-center text-sm text-gray-500">
          MarketPulse
        </div>
      </footer>
    </div>
  );
}
