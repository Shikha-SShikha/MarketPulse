import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Plus, Edit2, Trash2, X, AlertCircle, RefreshCw } from 'lucide-react';
import AdminHeader from '../components/AdminHeader';
import { getEntities, createEntity, updateEntity, deleteEntity } from '../api/entities';
import { useToast } from '../context/ToastContext';
import { getErrorMessage } from '../utils/errorHandling';
import type { Entity, EntityCreate, EntityUpdate, EntitySegment } from '../types';

const SEGMENTS = [
  { value: 'customer', label: 'Customer', icon: '👥', color: 'blue' },
  { value: 'competitor', label: 'Competitor', icon: '⚔️', color: 'red' },
  { value: 'industry', label: 'Industry', icon: '🏛️', color: 'green' },
  { value: 'influencer', label: 'Influencer', icon: '⭐', color: 'purple' },
];

export default function EntityManager() {
  const navigate = useNavigate();
  const { showSuccess, showError } = useToast();

  const [entities, setEntities] = useState<Entity[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedSegment, setSelectedSegment] = useState<string | null>(null);

  // Modal state
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingEntity, setEditingEntity] = useState<Entity | null>(null);
  const [formData, setFormData] = useState<EntityCreate>({
    name: '',
    segment: 'customer',
    aliases: [],
    entity_metadata: undefined,
    notes: '',
  });
  const [aliasInput, setAliasInput] = useState('');

  useEffect(() => {
    loadEntities();
  }, [selectedSegment]);

  async function loadEntities() {
    setLoading(true);
    setError(null);
    try {
      const params = selectedSegment ? { segment: selectedSegment } : undefined;
      const response = await getEntities(params);
      setEntities(response.entities);
      setTotal(response.total);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  function openCreateModal() {
    setEditingEntity(null);
    setFormData({
      name: '',
      segment: 'customer',
      aliases: [],
      entity_metadata: undefined,
      notes: '',
    });
    setAliasInput('');
    setIsModalOpen(true);
  }

  function openEditModal(entity: Entity) {
    setEditingEntity(entity);
    setFormData({
      name: entity.name,
      segment: entity.segment as EntitySegment,
      aliases: entity.aliases,
      entity_metadata: entity.entity_metadata ?? undefined,
      notes: entity.notes || '',
    });
    setAliasInput('');
    setIsModalOpen(true);
  }

  function closeModal() {
    setIsModalOpen(false);
    setEditingEntity(null);
  }

  function addAlias() {
    if (aliasInput.trim() && !formData.aliases?.includes(aliasInput.trim())) {
      setFormData({
        ...formData,
        aliases: [...(formData.aliases || []), aliasInput.trim()],
      });
      setAliasInput('');
    }
  }

  function removeAlias(alias: string) {
    setFormData({
      ...formData,
      aliases: formData.aliases?.filter((a) => a !== alias) || [],
    });
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();

    try {
      if (editingEntity) {
        const updated = await updateEntity(editingEntity.id, formData as EntityUpdate);
        setEntities(entities.map((e) => (e.id === updated.id ? updated : e)));
        showSuccess('Entity updated successfully');
      } else {
        const created = await createEntity(formData);
        setEntities([created, ...entities]);
        setTotal(total + 1);
        showSuccess('Entity created successfully');
      }
      closeModal();
    } catch (err) {
      showError(getErrorMessage(err));
    }
  }

  async function handleDelete(entity: Entity) {
    if (!confirm(`Are you sure you want to delete "${entity.name}"? This will remove all signal associations.`)) {
      return;
    }

    try {
      await deleteEntity(entity.id);
      setEntities(entities.filter((e) => e.id !== entity.id));
      setTotal(total - 1);
      showSuccess('Entity deleted successfully');
    } catch (err) {
      showError(getErrorMessage(err));
    }
  }

  const getSegmentBadgeColor = (segment: string) => {
    const config = SEGMENTS.find((s) => s.value === segment);
    if (!config) return 'bg-gray-100 text-gray-800';

    const colorMap: Record<string, string> = {
      blue: 'bg-blue-100 text-blue-800',
      red: 'bg-red-100 text-red-800',
      green: 'bg-green-100 text-green-800',
      purple: 'bg-purple-100 text-purple-800',
    };

    return colorMap[config.color] || 'bg-gray-100 text-gray-800';
  };

  return (
    <div className="min-h-screen" style={{ background: 'var(--cds-background)' }}>
      <AdminHeader
        title="Entity Management"
        subtitle={`${total} ${selectedSegment || 'total'} ${total !== 1 ? 'entities' : 'entity'}`}
        showBackButton={true}
        onBack={() => navigate('/admin/signals')}
        onRefresh={loadEntities}
        refreshing={loading}
      />

      <main className="cds--content" style={{ padding: '0.5rem 1rem' }}>
        <div className="max-w-7xl mx-auto">
          <div className="mb-4 flex justify-end">
            <button
              onClick={openCreateModal}
              className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
            >
              <Plus className="w-4 h-4" />
              Add Entity
            </button>
          </div>
        {/* Segment Filter */}
        <div className="mb-4 flex gap-2 flex-wrap">
          <button
            onClick={() => setSelectedSegment(null)}
            className={`px-4 py-2 rounded-md font-medium transition-colors ${
              selectedSegment === null
                ? 'bg-gray-900 text-white'
                : 'bg-white text-gray-700 border border-gray-300 hover:bg-gray-50'
            }`}
          >
            All
          </button>
          {SEGMENTS.map((segment) => (
            <button
              key={segment.value}
              onClick={() => setSelectedSegment(segment.value)}
              className={`px-4 py-2 rounded-md font-medium transition-colors flex items-center gap-2 ${
                selectedSegment === segment.value
                  ? 'bg-gray-900 text-white'
                  : 'bg-white text-gray-700 border border-gray-300 hover:bg-gray-50'
              }`}
            >
              <span>{segment.icon}</span>
              {segment.label}s
            </button>
          ))}
        </div>

        {/* Loading State */}
        {loading && (
          <div className="flex items-center justify-center py-16">
            <RefreshCw className="w-6 h-6 text-gray-400 animate-spin" />
            <span className="ml-3 text-gray-600">Loading entities...</span>
          </div>
        )}

        {/* Error State */}
        {error && !loading && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
            <div>
              <p className="text-red-800 font-medium">Error loading entities</p>
              <p className="text-red-600 text-sm mt-1">{error}</p>
              <button
                onClick={loadEntities}
                className="mt-3 text-sm text-red-700 hover:text-red-800 underline"
              >
                Try again
              </button>
            </div>
          </div>
        )}

        {/* Empty State */}
        {!loading && !error && entities.length === 0 && (
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-12 text-center">
            <h2 className="text-xl font-semibold text-gray-900 mb-2">No Entities Found</h2>
            <p className="text-gray-600 mb-6">
              {selectedSegment
                ? `No ${selectedSegment} entities exist yet.`
                : 'Get started by adding your first entity.'}
            </p>
            <button
              onClick={openCreateModal}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
            >
              Add Entity
            </button>
          </div>
        )}

        {/* Entity Table */}
        {!loading && entities.length > 0 && (
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Name
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Segment
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Aliases
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {entities.map((entity) => (
                  <tr key={entity.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4">
                      <div className="text-sm font-medium text-gray-900">{entity.name}</div>
                      {entity.notes && (
                        <div className="text-xs text-gray-500 mt-1">{entity.notes}</div>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`px-3 py-1 text-xs font-medium rounded-full ${getSegmentBadgeColor(entity.segment)}`}>
                        {SEGMENTS.find((s) => s.value === entity.segment)?.icon}{' '}
                        {entity.segment}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      {entity.aliases.length > 0 ? (
                        <div className="flex flex-wrap gap-1">
                          {entity.aliases.map((alias) => (
                            <span
                              key={alias}
                              className="px-2 py-0.5 text-xs bg-gray-100 text-gray-700 rounded"
                            >
                              {alias}
                            </span>
                          ))}
                        </div>
                      ) : (
                        <span className="text-sm text-gray-400">No aliases</span>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center gap-3">
                        <button
                          onClick={() => openEditModal(entity)}
                          className="text-blue-600 hover:text-blue-800"
                          title="Edit entity"
                        >
                          <Edit2 className="w-4 h-4" />
                        </button>
                        <button
                          onClick={() => handleDelete(entity)}
                          className="text-red-600 hover:text-red-800"
                          title="Delete entity"
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

      {/* Create/Edit Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between p-6 border-b border-gray-200">
              <h2 className="text-xl font-semibold text-gray-900">
                {editingEntity ? 'Edit Entity' : 'Create Entity'}
              </h2>
              <button
                onClick={closeModal}
                className="text-gray-400 hover:text-gray-600"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleSubmit} className="p-6 space-y-4">
              {/* Name */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Name *
                </label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  required
                />
              </div>

              {/* Segment */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Segment *
                </label>
                <select
                  value={formData.segment}
                  onChange={(e) => setFormData({ ...formData, segment: e.target.value as EntitySegment })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  required
                >
                  {SEGMENTS.map((segment) => (
                    <option key={segment.value} value={segment.value}>
                      {segment.icon} {segment.label}
                    </option>
                  ))}
                </select>
              </div>

              {/* Aliases */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Aliases
                </label>
                <div className="flex gap-2 mb-2">
                  <input
                    type="text"
                    value={aliasInput}
                    onChange={(e) => setAliasInput(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), addAlias())}
                    className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="Add alias and press Enter"
                  />
                  <button
                    type="button"
                    onClick={addAlias}
                    className="px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700"
                  >
                    Add
                  </button>
                </div>
                {formData.aliases && formData.aliases.length > 0 && (
                  <div className="flex flex-wrap gap-2">
                    {formData.aliases.map((alias) => (
                      <span
                        key={alias}
                        className="px-3 py-1 text-sm bg-gray-100 text-gray-700 rounded-full flex items-center gap-2"
                      >
                        {alias}
                        <button
                          type="button"
                          onClick={() => removeAlias(alias)}
                          className="text-gray-500 hover:text-gray-700"
                        >
                          <X className="w-3 h-3" />
                        </button>
                      </span>
                    ))}
                  </div>
                )}
              </div>

              {/* Notes */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Notes
                </label>
                <textarea
                  value={formData.notes}
                  onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  rows={3}
                  placeholder="Optional notes about this entity..."
                />
              </div>

              {/* Actions */}
              <div className="flex justify-end gap-3 pt-4 border-t border-gray-200">
                <button
                  type="button"
                  onClick={closeModal}
                  className="px-4 py-2 border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
                >
                  {editingEntity ? 'Update' : 'Create'} Entity
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
