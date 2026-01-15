import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Trash2, ExternalLink } from 'lucide-react';
import { DatePicker, DatePickerInput, Dropdown, Toggle } from '@carbon/react';
import AdminHeader from '../components/AdminHeader';
import { getSignals, deleteSignal, getUniqueEntities, getUniqueTopics, getSignalsSummary } from '../api/signals';
import { generateBrief } from '../api/briefs';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../context/ToastContext';
import { getErrorMessage } from '../utils/errorHandling';
import type { Signal, SignalSummary } from '../types';

export default function AdminSignalList() {
  const navigate = useNavigate();
  const { isAuthenticated, logout } = useAuth();
  const { showSuccess, showError } = useToast();

  const [signals, setSignals] = useState<Signal[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [generating, setGenerating] = useState(false);

  // View state
  const [showSummary, setShowSummary] = useState(false);
  const [summary, setSummary] = useState<SignalSummary | null>(null);
  const [summaryLoading, setSummaryLoading] = useState(false);

  // Filter states
  const [entityFilter, setEntityFilter] = useState<string | undefined>(undefined);
  const [topicFilter, setTopicFilter] = useState<string | undefined>(undefined);
  const [segmentFilter, setSegmentFilter] = useState<string | undefined>(undefined);
  const [startDate, setStartDate] = useState<string | undefined>(undefined);
  const [endDate, setEndDate] = useState<string | undefined>(undefined);

  // Autocomplete options
  const [entityOptions, setEntityOptions] = useState<Array<{ id: string; label: string }>>([{ id: 'all', label: 'All Entities' }]);
  const [topicOptions, setTopicOptions] = useState<Array<{ id: string; label: string }>>([{ id: 'all', label: 'All Topics' }]);

  const segmentOptions = [
    { id: 'all', label: 'All Segments' },
    { id: 'customer', label: 'Customer' },
    { id: 'competitor', label: 'Competitor' },
    { id: 'industry', label: 'Industry' },
    { id: 'influencer', label: 'Influencer' },
  ];

  useEffect(() => {
    loadFilterOptions();
  }, []);

  useEffect(() => {
    // Check if any filters are applied
    const hasFilters = entityFilter || topicFilter || segmentFilter || startDate || endDate;

    // If no filters and summary view is on, switch back to table view
    if (!hasFilters && showSummary) {
      setShowSummary(false);
    }

    if (showSummary && hasFilters) {
      loadSummary();
    } else {
      loadSignals();
    }
  }, [entityFilter, topicFilter, segmentFilter, startDate, endDate, showSummary]);

  async function loadFilterOptions() {
    try {
      const [entities, topics] = await Promise.all([
        getUniqueEntities(),
        getUniqueTopics(),
      ]);

      setEntityOptions([
        { id: 'all', label: 'All Entities' },
        ...entities.map(e => ({ id: e, label: e }))
      ]);

      setTopicOptions([
        { id: 'all', label: 'All Topics' },
        ...topics.map(t => ({ id: t, label: t }))
      ]);
    } catch (err) {
      console.error('Failed to load filter options:', err);
    }
  }

  async function loadSignals() {
    setLoading(true);
    setError(null);
    try {
      const params: any = { limit: 50 };

      if (entityFilter && entityFilter !== 'all') params.entity = entityFilter;
      if (topicFilter && topicFilter !== 'all') params.topic = topicFilter;
      if (segmentFilter && segmentFilter !== 'all') params.segment = segmentFilter;
      if (startDate) params.start_date = startDate;
      if (endDate) params.end_date = endDate;

      const response = await getSignals(params);
      setSignals(response.signals);
      setTotal(response.total);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  async function loadSummary() {
    setSummaryLoading(true);
    setError(null);
    try {
      const params: any = {};

      if (entityFilter && entityFilter !== 'all') params.entity = entityFilter;
      if (topicFilter && topicFilter !== 'all') params.topic = topicFilter;
      if (segmentFilter && segmentFilter !== 'all') params.segment = segmentFilter;
      if (startDate) params.start_date = startDate;
      if (endDate) params.end_date = endDate;

      const response = await getSignalsSummary(params);
      setSummary(response);
      setTotal(response.total_signals);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setSummaryLoading(false);
    }
  }

  async function handleDelete(id: string) {
    if (!confirm('Are you sure you want to delete this signal?')) {
      return;
    }
    try {
      await deleteSignal(id);
      setSignals(signals.filter((s) => s.id !== id));
      setTotal(total - 1);
      showSuccess('Signal deleted successfully');
    } catch (err) {
      showError(getErrorMessage(err));
    }
  }

  async function handleGenerateBrief() {
    setGenerating(true);
    try {
      const result = await generateBrief();
      showSuccess(`Brief generated: ${result.themes_created} themes from ${result.signals_processed} signals`);
    } catch (err) {
      showError(getErrorMessage(err));
    } finally {
      setGenerating(false);
    }
  }

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    });
  };

  if (!isAuthenticated) {
    navigate('/admin/signals/new');
    return null;
  }

  return (
    <div className="min-h-screen" style={{ background: 'var(--cds-background)' }}>
      <AdminHeader
        title="Signal Management"
        subtitle={`${total} signal${total !== 1 ? 's' : ''} in the database`}
        onGenerateBrief={handleGenerateBrief}
        generating={generating}
      />

      <main className="cds--content" style={{ padding: '0.5rem 1rem' }}>
        {/* Filters Section */}
        <div style={{
          background: 'var(--cds-layer-01)',
          padding: '0.75rem 1rem',
          marginBottom: '1rem',
          borderRadius: '4px',
          border: '1px solid var(--cds-border-subtle)'
        }}>
          <div style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            marginBottom: '0.5rem'
          }}>
            <h3 style={{
              fontSize: '0.875rem',
              fontWeight: 600,
              color: 'var(--cds-text-primary)',
              margin: 0
            }}>
              Filter Signals
            </h3>
            <button
              onClick={() => {
                setEntityFilter(undefined);
                setTopicFilter(undefined);
                setSegmentFilter(undefined);
                setStartDate(undefined);
                setEndDate(undefined);
                setShowSummary(false);  // Reset to table view when clearing filters
              }}
              style={{
                padding: '0.25rem 0.75rem',
                background: 'transparent',
                color: 'var(--cds-link-primary)',
                border: '1px solid var(--cds-border-subtle)',
                borderRadius: '4px',
                cursor: 'pointer',
                fontSize: '0.75rem'
              }}
            >
              Clear All
            </button>
          </div>

          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(5, 1fr)',
            gap: '0.75rem',
            alignItems: 'end'
          }}>
            <Dropdown
              id="entity-filter"
              titleText="Entity"
              label="All Entities"
              items={entityOptions}
              itemToString={(item) => item ? item.label : ''}
              onChange={({ selectedItem }) => setEntityFilter(selectedItem?.id)}
              size="sm"
            />

            <Dropdown
              id="topic-filter"
              titleText="Topic"
              label="All Topics"
              items={topicOptions}
              itemToString={(item) => item ? item.label : ''}
              onChange={({ selectedItem }) => setTopicFilter(selectedItem?.id)}
              size="sm"
            />

            <Dropdown
              id="segment-filter"
              titleText="Segment"
              label="All Segments"
              items={segmentOptions}
              itemToString={(item) => item ? item.label : ''}
              onChange={({ selectedItem }) => setSegmentFilter(selectedItem?.id)}
              size="sm"
            />

            <DatePicker
              datePickerType="single"
              onChange={(dates) => {
                const date = dates[0];
                if (date) {
                  const formattedDate = date.toISOString().split('T')[0];
                  setStartDate(formattedDate);
                } else {
                  setStartDate(undefined);
                }
              }}
              dateFormat="Y-m-d"
            >
              <DatePickerInput
                id="start-date-filter"
                placeholder="yyyy-mm-dd"
                labelText="Start Date"
                size="sm"
              />
            </DatePicker>

            <DatePicker
              datePickerType="single"
              onChange={(dates) => {
                const date = dates[0];
                if (date) {
                  const formattedDate = date.toISOString().split('T')[0];
                  setEndDate(formattedDate);
                } else {
                  setEndDate(undefined);
                }
              }}
              dateFormat="Y-m-d"
            >
              <DatePickerInput
                id="end-date-filter"
                placeholder="yyyy-mm-dd"
                labelText="End Date"
                size="sm"
              />
            </DatePicker>
          </div>
        </div>

        {/* View Toggle - Only show when filters are applied */}
        {(entityFilter || topicFilter || segmentFilter || startDate || endDate) && (
          <div style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            marginBottom: '1rem',
            padding: '0.75rem 1rem',
            background: 'var(--cds-layer-01)',
            borderRadius: '4px',
            border: '1px solid var(--cds-border-subtle)'
          }}>
            <div style={{
              fontSize: '0.875rem',
              color: 'var(--cds-text-secondary)'
            }}>
              Viewing {total} filtered signal{total !== 1 ? 's' : ''}
            </div>
            <Toggle
              id="view-toggle"
              labelText="AI Summary View"
              labelA="Table"
              labelB="Summary"
              toggled={showSummary}
              onToggle={(checked) => setShowSummary(checked)}
              size="sm"
            />
          </div>
        )}

        {/* Message when no filters applied and trying to view summary */}
        {!entityFilter && !topicFilter && !segmentFilter && !startDate && !endDate && showSummary && (
          <div style={{
            padding: '1rem',
            background: 'var(--cds-notification-background-info)',
            border: '1px solid var(--cds-notification-border-info)',
            borderRadius: '4px',
            marginBottom: '1rem',
            color: 'var(--cds-text-primary)'
          }}>
            <strong>Apply filters to generate summary:</strong> Please select at least one filter (Entity, Topic, Segment, or Date Range) to generate an AI-powered summary. Summaries work best with focused datasets.
          </div>
        )}

        {(loading || summaryLoading) && (
          <div className="text-center py-12">
            <p className="text-gray-500">Loading signals...</p>
          </div>
        )}

        {error && (
          <div className="p-4 bg-red-50 border border-red-200 rounded-lg text-red-800">
            {error}
          </div>
        )}

        {!loading && !error && signals.length === 0 && (
          <div className="text-center py-12 bg-white rounded-lg shadow">
            <p className="text-gray-500 mb-4">No signals yet</p>
            <button
              onClick={() => navigate('/admin/signals/new')}
              className="text-blue-600 hover:underline"
            >
              Add your first signal
            </button>
          </div>
        )}

        {/* Summary View */}
        {!summaryLoading && showSummary && summary && (
          <div style={{
            background: 'var(--cds-layer-01)',
            padding: '1.5rem',
            borderRadius: '4px',
            border: '1px solid var(--cds-border-subtle)'
          }}>
            <h2 style={{
              fontSize: '1.25rem',
              fontWeight: 600,
              marginBottom: '1rem',
              color: 'var(--cds-text-primary)'
            }}>
              Executive Summary
            </h2>

            {/* Metadata */}
            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
              gap: '1rem',
              marginBottom: '1.5rem',
              padding: '1rem',
              background: 'var(--cds-layer-02)',
              borderRadius: '4px'
            }}>
              <div>
                <div style={{ fontSize: '0.75rem', color: 'var(--cds-text-secondary)' }}>Signals Analyzed</div>
                <div style={{ fontSize: '1.25rem', fontWeight: 600, color: 'var(--cds-text-primary)' }}>{summary.total_signals}</div>
              </div>
              <div>
                <div style={{ fontSize: '0.75rem', color: 'var(--cds-text-secondary)' }}>Date Range</div>
                <div style={{ fontSize: '0.875rem', fontWeight: 500, color: 'var(--cds-text-primary)' }}>{summary.date_range}</div>
              </div>
              <div>
                <div style={{ fontSize: '0.75rem', color: 'var(--cds-text-secondary)' }}>Segments</div>
                <div style={{ fontSize: '0.875rem', fontWeight: 500, color: 'var(--cds-text-primary)' }}>{summary.segments_covered.join(', ') || 'Various'}</div>
              </div>
              <div>
                <div style={{ fontSize: '0.75rem', color: 'var(--cds-text-secondary)' }}>Impact Areas</div>
                <div style={{ fontSize: '0.875rem', fontWeight: 500, color: 'var(--cds-text-primary)' }}>{summary.impact_areas.join(', ')}</div>
              </div>
            </div>

            {/* Overall Summary */}
            <div style={{
              padding: '1rem',
              background: 'var(--cds-layer-02)',
              borderRadius: '4px',
              marginBottom: '1.5rem',
              borderLeft: '4px solid var(--cds-interactive)'
            }}>
              <p style={{ fontSize: '0.9375rem', lineHeight: '1.6', color: 'var(--cds-text-primary)' }}>
                {summary.summary}
              </p>
            </div>

            {/* Key Insights */}
            <h3 style={{
              fontSize: '1rem',
              fontWeight: 600,
              marginBottom: '1rem',
              color: 'var(--cds-text-primary)'
            }}>
              Key Insights
            </h3>

            {summary.key_insights.map((insight, index) => (
              <div
                key={index}
                style={{
                  padding: '1rem',
                  background: 'var(--cds-layer-02)',
                  borderRadius: '4px',
                  marginBottom: '1rem',
                  border: '1px solid var(--cds-border-subtle)'
                }}
              >
                <p style={{
                  fontSize: '0.9375rem',
                  fontWeight: 500,
                  marginBottom: '0.75rem',
                  color: 'var(--cds-text-primary)'
                }}>
                  {insight.insight}
                </p>

                <div style={{
                  display: 'flex',
                  gap: '1rem',
                  marginTop: '0.5rem',
                  fontSize: '0.8125rem',
                  color: 'var(--cds-text-secondary)'
                }}>
                  <div>
                    <strong>Entities:</strong> {insight.entities.join(', ')}
                  </div>
                  <div>
                    <strong>Sources:</strong> {insight.signal_ids.length} signal{insight.signal_ids.length !== 1 ? 's' : ''}
                  </div>
                </div>

                {/* Traceability - Signal IDs */}
                <details style={{ marginTop: '0.75rem' }}>
                  <summary style={{
                    cursor: 'pointer',
                    fontSize: '0.8125rem',
                    color: 'var(--cds-link-primary)',
                    fontWeight: 500
                  }}>
                    View source signals ({insight.signal_ids.length})
                  </summary>
                  <div style={{
                    marginTop: '0.5rem',
                    padding: '0.5rem',
                    background: 'var(--cds-layer-01)',
                    borderRadius: '4px',
                    fontSize: '0.75rem',
                    fontFamily: 'monospace',
                    maxHeight: '150px',
                    overflowY: 'auto'
                  }}>
                    {insight.signal_ids.map(id => (
                      <div key={id} style={{ padding: '0.25rem 0' }}>
                        {id}
                      </div>
                    ))}
                  </div>
                </details>
              </div>
            ))}
          </div>
        )}

        {/* Table View */}
        {!loading && !showSummary && signals.length > 0 && (
          <div className="bg-white rounded-lg shadow overflow-hidden">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Entity
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Topic
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Type
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Confidence
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Date
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {signals.map((signal) => (
                  <tr key={signal.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm font-medium text-gray-900">
                        {signal.entity}
                      </div>
                      <div className="text-sm text-gray-500">
                        {signal.impact_areas.join(', ')}
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <div className="text-sm text-gray-900">{signal.topic}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="px-2 py-1 text-xs font-medium bg-gray-100 text-gray-800 rounded">
                        {signal.event_type}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
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
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {formatDate(signal.created_at)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      <div className="flex items-center gap-3">
                        <a
                          href={signal.source_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-blue-600 hover:text-blue-800"
                          title="View source"
                        >
                          <ExternalLink className="w-4 h-4" />
                        </a>
                        <button
                          onClick={() => handleDelete(signal.id)}
                          className="text-red-600 hover:text-red-800"
                          title="Delete signal"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </main>
    </div>
  );
}
