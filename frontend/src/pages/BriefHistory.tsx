import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Calendar, Clock, FileText, AlertCircle } from 'lucide-react';
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
import { getErrorMessage } from '../utils/errorHandling';

interface BriefSummary {
  id: string;
  week_start: string;
  week_end: string;
  generated_at: string;
  total_signals: number;
  coverage_areas: string[];
  theme_count: number;
}

export default function BriefHistory() {
  const navigate = useNavigate();
  const [briefs, setBriefs] = useState<BriefSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadBriefs();
  }, []);

  async function loadBriefs() {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch('http://localhost:8000/briefs');
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      setBriefs(data);
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
        background: 'var(--cds-background)',
        borderBottom: '1px solid var(--cds-border-subtle)',
        padding: '1.5rem 2rem'
      }}>
        <div style={{ maxWidth: '1000px', margin: '0 auto' }}>
          <h1 style={{
            fontSize: '1.75rem',
            fontWeight: 600,
            marginBottom: '0.25rem',
            color: 'var(--cds-text-primary)'
          }}>
            Brief History
          </h1>
          <p style={{
            fontSize: '0.875rem',
            color: 'var(--cds-text-secondary)'
          }}>
            Browse all weekly intelligence briefs
          </p>
        </div>
      </div>

      <main className="cds--content" style={{ padding: '2rem', maxWidth: '1000px', margin: '0 auto' }}>
        {/* Loading State */}
        {loading && (
          <div className="flex items-center justify-center py-16">
            <Clock className="w-6 h-6 text-gray-400 animate-spin" />
            <span className="ml-3 text-gray-600">Loading briefs...</span>
          </div>
        )}

        {/* Error State */}
        {error && !loading && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
            <div>
              <p className="text-red-800 font-medium">Error loading briefs</p>
              <p className="text-red-600 text-sm mt-1">{error}</p>
              <button
                onClick={loadBriefs}
                className="mt-3 text-sm text-red-700 hover:text-red-800 underline"
              >
                Try again
              </button>
            </div>
          </div>
        )}

        {/* No Briefs State */}
        {!loading && !error && briefs.length === 0 && (
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8 text-center">
            <FileText className="w-12 h-12 text-gray-300 mx-auto mb-4" />
            <h2 className="text-xl font-semibold text-gray-900 mb-2">
              No Briefs Generated Yet
            </h2>
            <p className="text-gray-600 mb-4">
              Generate your first weekly brief to see it here.
            </p>
            <button
              onClick={() => navigate('/')}
              className="inline-block px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
            >
              Go to Dashboard
            </button>
          </div>
        )}

        {/* Briefs List */}
        {!loading && !error && briefs.length > 0 && (
          <div className="space-y-4">
            {briefs.map((brief) => (
              <button
                key={brief.id}
                onClick={() => navigate(`/briefs/${brief.id}`)}
                className="w-full bg-white rounded-lg shadow-sm border border-gray-200 p-6 hover:shadow-md hover:border-gray-300 transition-all text-left"
              >
                <div className="flex items-start justify-between gap-4 mb-3">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 text-gray-900 font-semibold text-lg mb-2">
                      <Calendar className="w-5 h-5 text-gray-400" />
                      {formatDate(brief.week_start)} — {formatDate(brief.week_end)}
                    </div>
                    <div className="flex items-center gap-2 text-gray-500 text-sm">
                      <Clock className="w-4 h-4" />
                      Generated {formatDateTime(brief.generated_at)}
                    </div>
                  </div>
                </div>

                <div className="flex flex-wrap gap-4 text-sm">
                  <div className="flex items-center gap-2">
                    <span className="text-gray-500">Themes:</span>
                    <span className="font-semibold text-gray-900">{brief.theme_count}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-gray-500">Signals:</span>
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
              </button>
            ))}
          </div>
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
