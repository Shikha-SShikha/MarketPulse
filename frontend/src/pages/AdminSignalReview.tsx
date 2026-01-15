import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { CheckCircle, XCircle, ExternalLink } from 'lucide-react';
import AdminHeader from '../components/AdminHeader';
import { getPendingSignals, updateSignalStatus } from '../api/signals';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../context/ToastContext';
import { getErrorMessage } from '../utils/errorHandling';
import type { Signal } from '../types';

export default function AdminSignalReview() {
  const navigate = useNavigate();
  const { isAuthenticated } = useAuth();
  const { showSuccess, showError } = useToast();

  const [signals, setSignals] = useState<Signal[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [processingId, setProcessingId] = useState<string | null>(null);

  useEffect(() => {
    loadPendingSignals();
  }, []);

  async function loadPendingSignals() {
    setLoading(true);
    setError(null);
    try {
      const response = await getPendingSignals({ limit: 50 });
      setSignals(response.signals);
      setTotal(response.total);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  async function handleApprove(signalId: string) {
    setProcessingId(signalId);
    try {
      await updateSignalStatus(signalId, 'approved');
      setSignals(signals.filter((s) => s.id !== signalId));
      setTotal(total - 1);
      showSuccess('Signal approved successfully');
    } catch (err) {
      showError(getErrorMessage(err));
    } finally {
      setProcessingId(null);
    }
  }

  async function handleReject(signalId: string) {
    if (!confirm('Are you sure you want to reject this signal?')) {
      return;
    }
    setProcessingId(signalId);
    try {
      await updateSignalStatus(signalId, 'rejected');
      setSignals(signals.filter((s) => s.id !== signalId));
      setTotal(total - 1);
      showSuccess('Signal rejected successfully');
    } catch (err) {
      showError(getErrorMessage(err));
    } finally {
      setProcessingId(null);
    }
  }

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  if (!isAuthenticated) {
    navigate('/admin/signals');
    return null;
  }

  return (
    <div className="min-h-screen" style={{ background: 'var(--cds-background)' }}>
      <AdminHeader
        title="Review Automated Signals"
        subtitle={`${total} signal${total !== 1 ? 's' : ''} pending review`}
        showBackButton={true}
        onBack={() => navigate('/admin/signals')}
        onRefresh={loadPendingSignals}
        refreshing={loading}
      />

      <main className="cds--content" style={{ padding: '2rem' }}>
        {loading && (
          <div className="text-center py-12">
            <p className="text-gray-500">Loading pending signals...</p>
          </div>
        )}

        {error && (
          <div className="p-4 bg-red-50 border border-red-200 rounded-lg text-red-800">
            {error}
          </div>
        )}

        {!loading && !error && signals.length === 0 && (
          <div className="text-center py-12 bg-white rounded-lg shadow">
            <CheckCircle className="w-16 h-16 text-green-500 mx-auto mb-4" />
            <p className="text-gray-900 text-lg font-medium mb-2">All caught up!</p>
            <p className="text-gray-500">No pending signals to review</p>
          </div>
        )}

        {!loading && signals.length > 0 && (
          <div className="space-y-4">
            {signals.map((signal) => (
              <div
                key={signal.id}
                className="bg-white rounded-lg shadow-md p-6 border-l-4 border-yellow-400"
              >
                <div className="flex justify-between items-start mb-4">
                  <div className="flex-1">
                    <div className="flex items-start gap-3 mb-2">
                      <h3 className="text-lg font-semibold text-gray-900">{signal.entity}</h3>
                      <span className="px-2 py-1 text-xs font-medium bg-gray-100 text-gray-800 rounded">
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
                    <p className="text-sm text-gray-600 mb-1">
                      <strong>Topic:</strong> {signal.topic}
                    </p>
                    <p className="text-sm text-gray-600 mb-3">
                      <strong>Impact Areas:</strong> {signal.impact_areas.join(', ')}
                    </p>
                    <div className="bg-gray-50 rounded p-3 mb-3">
                      <p className="text-sm text-gray-700 italic">{signal.evidence_snippet}</p>
                    </div>
                    <div className="flex items-center gap-4 text-xs text-gray-500">
                      <span>Collected: {formatDate(signal.created_at)}</span>
                      {signal.entity_tags.length > 0 && (
                        <span>Tags: {signal.entity_tags.join(', ')}</span>
                      )}
                      <a
                        href={signal.source_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="flex items-center gap-1 text-blue-600 hover:text-blue-800"
                      >
                        <ExternalLink className="w-3 h-3" />
                        View source
                      </a>
                    </div>
                  </div>
                </div>

                <div className="flex gap-3 pt-4 border-t border-gray-200">
                  <button
                    onClick={() => handleApprove(signal.id)}
                    disabled={processingId === signal.id}
                    className="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
                  >
                    <CheckCircle className="w-4 h-4" />
                    {processingId === signal.id ? 'Processing...' : 'Approve'}
                  </button>
                  <button
                    onClick={() => handleReject(signal.id)}
                    disabled={processingId === signal.id}
                    className="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
                  >
                    <XCircle className="w-4 h-4" />
                    {processingId === signal.id ? 'Processing...' : 'Reject'}
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}
