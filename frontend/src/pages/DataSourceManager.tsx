import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Plus, Trash2, Edit2, CheckCircle, XCircle } from 'lucide-react';
import { Play } from '@carbon/icons-react';
import AdminHeader from '../components/AdminHeader';
import { getDataSources, createDataSource, updateDataSource, deleteDataSource, triggerCollection } from '../api/datasources';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../context/ToastContext';
import { getErrorMessage } from '../utils/errorHandling';
import type { DataSource, DataSourceCreate, SourceType, Confidence, ImpactArea } from '../types';

export default function DataSourceManager() {
  const navigate = useNavigate();
  const { isAuthenticated } = useAuth();
  const { showSuccess, showError } = useToast();

  const [sources, setSources] = useState<DataSource[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showAddForm, setShowAddForm] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [collecting, setCollecting] = useState(false);

  // Form state
  const [formData, setFormData] = useState<DataSourceCreate>({
    name: '',
    source_type: 'rss' as SourceType,
    url: '',
    enabled: true,
    default_confidence: 'Medium' as Confidence,
    default_impact_areas: [],
  });

  useEffect(() => {
    loadDataSources();
  }, []);

  async function loadDataSources() {
    setLoading(true);
    setError(null);
    try {
      const data = await getDataSources();
      setSources(data);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    try {
      if (editingId) {
        await updateDataSource(editingId, formData);
        showSuccess('Data source updated successfully');
      } else {
        await createDataSource(formData);
        showSuccess('Data source created successfully');
      }
      resetForm();
      loadDataSources();
    } catch (err) {
      showError(getErrorMessage(err));
    }
  }

  async function handleDelete(id: string) {
    if (!confirm('Are you sure you want to delete this data source? All associated signals will remain.')) {
      return;
    }
    try {
      await deleteDataSource(id);
      setSources(sources.filter((s) => s.id !== id));
      showSuccess('Data source deleted successfully');
    } catch (err) {
      showError(getErrorMessage(err));
    }
  }

  async function handleToggleEnabled(source: DataSource) {
    try {
      await updateDataSource(source.id, { enabled: !source.enabled });
      loadDataSources();
      showSuccess(`Data source ${source.enabled ? 'disabled' : 'enabled'}`);
    } catch (err) {
      showError(getErrorMessage(err));
    }
  }

  async function handleTriggerCollection() {
    setCollecting(true);
    try {
      const result = await triggerCollection();
      showSuccess(
        `Collected ${result.signals_collected} signals from ${result.sources_processed} sources. ${result.signals_pending_review} pending review.`
      );
      if (result.errors.length > 0) {
        showError(`Errors: ${result.errors.join(', ')}`);
      }
    } catch (err) {
      showError(getErrorMessage(err));
    } finally {
      setCollecting(false);
    }
  }

  function handleEdit(source: DataSource) {
    setEditingId(source.id);
    setFormData({
      name: source.name,
      source_type: source.source_type as SourceType,
      url: source.url || '',
      enabled: source.enabled,
      default_confidence: source.default_confidence as Confidence,
      default_impact_areas: source.default_impact_areas as ImpactArea[],
    });
    setShowAddForm(true);
  }

  function resetForm() {
    setFormData({
      name: '',
      source_type: 'rss' as SourceType,
      url: '',
      enabled: true,
      default_confidence: 'Medium' as Confidence,
      default_impact_areas: [],
    });
    setShowAddForm(false);
    setEditingId(null);
  }

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return 'Never';
    return new Date(dateStr).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
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
        title="Data Source Management"
        subtitle={`${sources.length} data source${sources.length !== 1 ? 's' : ''} configured`}
        showBackButton={true}
        onBack={() => navigate('/admin/signals')}
      />

      <main className="cds--content" style={{ padding: '2rem' }}>
        <div className="max-w-7xl mx-auto">
          <div className="flex gap-3 mb-6">
            <button
              onClick={handleTriggerCollection}
              className="flex items-center gap-2 px-4 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700 disabled:bg-gray-400"
              disabled={collecting}
            >
              <Play size={16} />
              {collecting ? 'Collecting...' : 'Collect Now'}
            </button>
            <button
              onClick={() => setShowAddForm(true)}
              className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
            >
              <Plus className="w-4 h-4" />
              Add Source
            </button>
          </div>
        {showAddForm && (
          <div className="mb-6 bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold mb-4">
              {editingId ? 'Edit Data Source' : 'Add New Data Source'}
            </h2>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Name *
                  </label>
                  <input
                    type="text"
                    required
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="e.g., Nature News RSS"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Type *
                  </label>
                  <select
                    required
                    value={formData.source_type}
                    onChange={(e) => setFormData({ ...formData, source_type: e.target.value as SourceType })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="rss">RSS Feed</option>
                    <option value="linkedin">LinkedIn (Coming Soon)</option>
                    <option value="web">Web Scraper (Coming Soon)</option>
                    <option value="email">Email (Coming Soon)</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  URL {formData.source_type === 'rss' && '*'}
                </label>
                <input
                  type="url"
                  required={formData.source_type === 'rss'}
                  value={formData.url}
                  onChange={(e) => setFormData({ ...formData, url: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="https://example.com/feed.rss"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Default Confidence
                  </label>
                  <select
                    value={formData.default_confidence}
                    onChange={(e) => setFormData({ ...formData, default_confidence: e.target.value as Confidence })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="Low">Low</option>
                    <option value="Medium">Medium</option>
                    <option value="High">High</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Enabled
                  </label>
                  <select
                    value={formData.enabled ? 'true' : 'false'}
                    onChange={(e) => setFormData({ ...formData, enabled: e.target.value === 'true' })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="true">Yes</option>
                    <option value="false">No</option>
                  </select>
                </div>
              </div>

              <div className="flex gap-3">
                <button
                  type="submit"
                  className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
                >
                  {editingId ? 'Update Source' : 'Add Source'}
                </button>
                <button
                  type="button"
                  onClick={resetForm}
                  className="px-4 py-2 border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50"
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        )}

        {loading && (
          <div className="text-center py-12">
            <p className="text-gray-500">Loading data sources...</p>
          </div>
        )}

        {error && (
          <div className="p-4 bg-red-50 border border-red-200 rounded-lg text-red-800">
            {error}
          </div>
        )}

        {!loading && sources.length === 0 && (
          <div className="text-center py-12 bg-white rounded-lg shadow">
            <p className="text-gray-500 mb-4">No data sources configured</p>
            <button
              onClick={() => setShowAddForm(true)}
              className="text-blue-600 hover:underline"
            >
              Add your first data source
            </button>
          </div>
        )}

        {!loading && sources.length > 0 && (
          <div className="bg-white rounded-lg shadow overflow-hidden">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Name
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Type
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Last Success
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Errors
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {sources.map((source) => (
                  <tr key={source.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4">
                      <div className="text-sm font-medium text-gray-900">{source.name}</div>
                      {source.url && (
                        <div className="text-xs text-gray-500 truncate max-w-xs">{source.url}</div>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="px-2 py-1 text-xs font-medium bg-gray-100 text-gray-800 rounded">
                        {source.source_type}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      {source.enabled ? (
                        <span className="flex items-center gap-1 text-green-700">
                          <CheckCircle className="w-4 h-4" />
                          <span className="text-sm">Enabled</span>
                        </span>
                      ) : (
                        <span className="flex items-center gap-1 text-red-700">
                          <XCircle className="w-4 h-4" />
                          <span className="text-sm">Disabled</span>
                        </span>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {formatDate(source.last_success_at)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      {source.error_count > 0 ? (
                        <span className="text-sm text-red-600" title={source.last_error || undefined}>
                          {source.error_count} error{source.error_count !== 1 ? 's' : ''}
                        </span>
                      ) : (
                        <span className="text-sm text-gray-500">None</span>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      <div className="flex items-center gap-3">
                        <button
                          onClick={() => handleToggleEnabled(source)}
                          className="text-blue-600 hover:text-blue-800"
                          title={source.enabled ? 'Disable' : 'Enable'}
                        >
                          {source.enabled ? 'Disable' : 'Enable'}
                        </button>
                        <button
                          onClick={() => handleEdit(source)}
                          className="text-gray-600 hover:text-gray-800"
                          title="Edit source"
                        >
                          <Edit2 className="w-4 h-4" />
                        </button>
                        <button
                          onClick={() => handleDelete(source.id)}
                          className="text-red-600 hover:text-red-800"
                          title="Delete source"
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
        </div>
      </main>
    </div>
  );
}
