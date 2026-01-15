import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Calendar, Clock, FileText, AlertCircle, RefreshCw, Download } from 'lucide-react';
import {
  Header,
  HeaderContainer,
  HeaderName,
  HeaderGlobalBar,
  HeaderGlobalAction,
  SkipToContent,
  Button,
} from '@carbon/react';
import { Renew, Login, Search } from '@carbon/icons-react';
import { getCurrentBrief, generateBrief, downloadBriefPdf } from '../api/briefs';
import ThemeCard from '../components/ThemeCard';
import NotificationBell from '../components/NotificationBell';
import SegmentStatsWidget from '../components/SegmentStatsWidget';
import { SearchModal } from '../components/SearchModal';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../context/ToastContext';
import { getErrorMessage } from '../utils/errorHandling';
import type { WeeklyBrief } from '../types';

export default function Dashboard() {
  const [brief, setBrief] = useState<WeeklyBrief | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [generating, setGenerating] = useState(false);
  const [downloading, setDownloading] = useState(false);
  const [searchModalOpen, setSearchModalOpen] = useState(false);
  const { isAuthenticated } = useAuth();
  const { showSuccess, showError } = useToast();

  useEffect(() => {
    loadBrief();
  }, []);

  // Global Cmd/Ctrl+K keyboard shortcut for search
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        setSearchModalOpen(true);
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  async function loadBrief() {
    setLoading(true);
    setError(null);
    try {
      const data = await getCurrentBrief();
      setBrief(data);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  async function handleGenerateBrief() {
    setGenerating(true);
    try {
      const result = await generateBrief();
      showSuccess(`Brief generated: ${result.themes_created} themes from ${result.signals_processed} signals`);
      // Reload the brief
      await loadBrief();
    } catch (err) {
      showError(getErrorMessage(err));
    } finally {
      setGenerating(false);
    }
  }

  async function handleDownloadPdf() {
    if (!brief) return;

    setDownloading(true);
    try {
      await downloadBriefPdf(brief.id);
      showSuccess('PDF downloaded successfully');
    } catch (err) {
      showError(getErrorMessage(err));
    } finally {
      setDownloading(false);
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
                aria-label="Search Intelligence (Ctrl+K)"
                tooltipAlignment="end"
                onClick={() => setSearchModalOpen(true)}
              >
                <Search size={20} />
              </HeaderGlobalAction>
              {isAuthenticated && (
                <HeaderGlobalAction
                  aria-label="Generate Weekly Brief"
                  tooltipAlignment="end"
                  onClick={handleGenerateBrief}
                  isActive={generating}
                >
                  <Renew size={20} />
                </HeaderGlobalAction>
              )}
              <HeaderGlobalAction
                aria-label="Admin Panel"
                tooltipAlignment="end"
                onClick={() => window.location.href = '/admin/signals'}
              >
                <Login size={20} />
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
            Weekly Intelligence Brief
          </h1>
          <p style={{
            fontSize: '0.875rem',
            color: 'var(--cds-text-secondary)'
          }}>
            Market and Competitive Intel
          </p>
        </div>
      </div>

      <main className="cds--content" style={{ padding: '1rem', maxWidth: '1200px', margin: '0 auto' }}>
        {/* Segment Stats Widget */}
        <div className="mb-8">
          <SegmentStatsWidget />
        </div>

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
                onClick={loadBrief}
                className="mt-3 text-sm text-red-700 hover:text-red-800 underline"
              >
                Try again
              </button>
            </div>
          </div>
        )}

        {/* No Brief State */}
        {!loading && !error && !brief && (
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8 text-center">
            <FileText className="w-12 h-12 text-gray-300 mx-auto mb-4" />
            <h2 className="text-xl font-semibold text-gray-900 mb-2">
              No Brief Available Yet
            </h2>
            <p className="text-gray-600 mb-4">
              The weekly brief hasn't been generated yet. Check back later or ask your curator to generate one.
            </p>
            <Link
              to="/admin/signals/new"
              className="inline-block px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
            >
              Add Signals
            </Link>
          </div>
        )}

        {/* Brief Content */}
        {!loading && !error && brief && (
          <>
            {/* Brief Metadata */}
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 sm:p-6 mb-6">
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
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
                <Button
                  kind="tertiary"
                  size="md"
                  renderIcon={Download}
                  onClick={handleDownloadPdf}
                  disabled={downloading}
                >
                  {downloading ? 'Downloading...' : 'Download PDF'}
                </Button>
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

      {/* Search Modal */}
      <SearchModal
        isOpen={searchModalOpen}
        onClose={() => setSearchModalOpen(false)}
      />
    </div>
  );
}
