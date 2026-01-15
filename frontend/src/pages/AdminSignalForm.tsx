import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '@carbon/react';
import AdminHeader from '../components/AdminHeader';
import {
  TextInput,
  TextArea,
  Select,
  RadioGroup,
  CheckboxGroup,
  AutocompleteInput,
} from '../components/FormFields';
import { createSignal, getUniqueEntities, getUniqueTopics } from '../api/signals';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../context/ToastContext';
import { getErrorMessage, isAuthError } from '../utils/errorHandling';
import type { SignalCreate, EventType, Confidence, ImpactArea } from '../types';

const EVENT_TYPES: { value: EventType; label: string }[] = [
  { value: 'announcement', label: 'Announcement' },
  { value: 'hire', label: 'Hire' },
  { value: 'policy', label: 'Policy' },
  { value: 'partnership', label: 'Partnership' },
  { value: 'm&a', label: 'M&A' },
  { value: 'retraction', label: 'Retraction' },
  { value: 'launch', label: 'Launch' },
  { value: 'other', label: 'Other' },
];

const CONFIDENCE_OPTIONS: { value: Confidence; label: string }[] = [
  { value: 'Low', label: 'Low' },
  { value: 'Medium', label: 'Medium' },
  { value: 'High', label: 'High' },
];

const IMPACT_AREA_OPTIONS: { value: ImpactArea; label: string }[] = [
  { value: 'Ops', label: 'Ops' },
  { value: 'Tech', label: 'Tech' },
  { value: 'Integrity', label: 'Integrity' },
  { value: 'Procurement', label: 'Procurement' },
];

interface FormData {
  entity: string;
  event_type: string;
  topic: string;
  source_url: string;
  evidence_snippet: string;
  confidence: string;
  impact_areas: string[];
  entity_tags: string;
  notes: string;
}

interface FormErrors {
  entity?: string;
  event_type?: string;
  topic?: string;
  source_url?: string;
  evidence_snippet?: string;
  confidence?: string;
  impact_areas?: string;
}

const initialFormData: FormData = {
  entity: '',
  event_type: '',
  topic: '',
  source_url: '',
  evidence_snippet: '',
  confidence: '',
  impact_areas: [],
  entity_tags: '',
  notes: '',
};

export default function AdminSignalForm() {
  const navigate = useNavigate();
  const { isAuthenticated, setToken } = useAuth();
  const { showSuccess, showError } = useToast();

  const [formData, setFormData] = useState<FormData>(initialFormData);
  const [errors, setErrors] = useState<FormErrors>({});
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Autocomplete suggestions
  const [entitySuggestions, setEntitySuggestions] = useState<string[]>([]);
  const [topicSuggestions, setTopicSuggestions] = useState<string[]>([]);

  // Token input for non-authenticated users
  const [tokenInput, setTokenInput] = useState('');

  // Load suggestions on mount
  useEffect(() => {
    async function loadSuggestions() {
      try {
        const [entities, topics] = await Promise.all([
          getUniqueEntities(),
          getUniqueTopics(),
        ]);
        setEntitySuggestions(entities);
        setTopicSuggestions(topics);
      } catch {
        // Ignore errors - suggestions are optional
      }
    }
    loadSuggestions();
  }, []);

  const validateUrl = (url: string): boolean => {
    if (!url) return false;
    try {
      new URL(url);
      return true;
    } catch {
      return false;
    }
  };

  const validateForm = (): boolean => {
    const newErrors: FormErrors = {};

    if (!formData.entity.trim()) {
      newErrors.entity = 'Entity is required';
    }

    if (!formData.event_type) {
      newErrors.event_type = 'Event type is required';
    }

    if (!formData.topic.trim()) {
      newErrors.topic = 'Topic is required';
    }

    if (!formData.source_url.trim()) {
      newErrors.source_url = 'Source URL is required';
    } else if (!validateUrl(formData.source_url)) {
      newErrors.source_url = 'Please enter a valid URL (e.g., https://example.com)';
    }

    if (!formData.evidence_snippet.trim()) {
      newErrors.evidence_snippet = 'Evidence snippet is required';
    } else if (formData.evidence_snippet.length < 50) {
      newErrors.evidence_snippet = `Evidence snippet must be at least 50 characters (currently ${formData.evidence_snippet.length})`;
    } else if (formData.evidence_snippet.length > 500) {
      newErrors.evidence_snippet = `Evidence snippet must be less than 500 characters (currently ${formData.evidence_snippet.length})`;
    }

    if (!formData.confidence) {
      newErrors.confidence = 'Confidence level is required';
    }

    if (formData.impact_areas.length === 0) {
      newErrors.impact_areas = 'At least one impact area is required';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleUrlBlur = () => {
    if (formData.source_url && !validateUrl(formData.source_url)) {
      setErrors((prev) => ({
        ...prev,
        source_url: 'Please enter a valid URL (e.g., https://example.com)',
      }));
    } else {
      setErrors((prev) => {
        const { source_url, ...rest } = prev;
        return rest;
      });
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validateForm()) {
      return;
    }

    setIsSubmitting(true);

    try {
      const signalData: SignalCreate = {
        entity: formData.entity.trim(),
        event_type: formData.event_type as EventType,
        topic: formData.topic.trim(),
        source_url: formData.source_url.trim(),
        evidence_snippet: formData.evidence_snippet.trim(),
        confidence: formData.confidence as Confidence,
        impact_areas: formData.impact_areas as ImpactArea[],
        entity_tags: formData.entity_tags
          ? formData.entity_tags.split(',').map((t) => t.trim()).filter(Boolean)
          : [],
        notes: formData.notes.trim() || undefined,
      };

      await createSignal(signalData);

      showSuccess('Signal saved successfully!');
      setFormData(initialFormData);

      // Refresh suggestions
      const [entities, topics] = await Promise.all([
        getUniqueEntities(),
        getUniqueTopics(),
      ]);
      setEntitySuggestions(entities);
      setTopicSuggestions(topics);
    } catch (error) {
      if (isAuthError(error)) {
        showError('Authentication failed. Please check your curator token.');
      } else {
        showError(getErrorMessage(error));
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleCancel = () => {
    setFormData(initialFormData);
    setErrors({});
    navigate('/admin/signals');
  };

  const handleTokenSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (tokenInput.trim()) {
      setToken(tokenInput.trim());
    }
  };

  // Show token input if not authenticated
  if (!isAuthenticated) {
    return (
      <div className="min-h-screen" style={{ background: 'var(--cds-background)' }}>
        <AdminHeader
          title="Curator Login"
          subtitle="Enter your credentials to access the signal entry form"
        />
        <main className="cds--content" style={{ padding: '2rem', maxWidth: '600px', margin: '0 auto' }}>
          <div className="bg-white rounded-lg shadow p-6">
            <p className="text-gray-600 mb-4">
              Enter your curator token to access the signal entry form.
            </p>
            <form onSubmit={handleTokenSubmit} className="space-y-4">
              <TextInput
                label="Curator Token"
                name="token"
                value={tokenInput}
                onChange={setTokenInput}
                placeholder="Enter your curator token"
                required
              />
              <Button type="submit" size="md">
                Login
              </Button>
            </form>
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className="min-h-screen" style={{ background: 'var(--cds-background)' }}>
      <AdminHeader
        title="Add New Signal"
        subtitle="Enter market intelligence from public sources"
        showBackButton={true}
        onBack={() => navigate('/admin/signals')}
      />

      <main className="cds--content" style={{ padding: '2rem', maxWidth: '800px', margin: '0 auto' }}>
        <form onSubmit={handleSubmit} className="bg-white rounded-lg shadow p-6 space-y-6">
          {/* Entity */}
          <AutocompleteInput
            label="Entity"
            name="entity"
            value={formData.entity}
            onChange={(value) => setFormData({ ...formData, entity: value })}
            suggestions={entitySuggestions}
            placeholder="e.g., Springer Nature, Elsevier, PLOS"
            error={errors.entity}
            required
          />

          {/* Event Type */}
          <Select
            label="Event Type"
            name="event_type"
            value={formData.event_type}
            onChange={(value) => setFormData({ ...formData, event_type: value })}
            options={EVENT_TYPES}
            error={errors.event_type}
            required
          />

          {/* Topic */}
          <AutocompleteInput
            label="Topic"
            name="topic"
            value={formData.topic}
            onChange={(value) => setFormData({ ...formData, topic: value })}
            suggestions={topicSuggestions}
            placeholder="e.g., Open Access Mandate, In-House Development"
            error={errors.topic}
            required
          />

          {/* Source URL */}
          <TextInput
            label="Source URL"
            name="source_url"
            value={formData.source_url}
            onChange={(value) => setFormData({ ...formData, source_url: value })}
            onBlur={handleUrlBlur}
            placeholder="https://example.com/news/article"
            error={errors.source_url}
            required
          />

          {/* Evidence Snippet */}
          <TextArea
            label="Evidence Snippet"
            name="evidence_snippet"
            value={formData.evidence_snippet}
            onChange={(value) => setFormData({ ...formData, evidence_snippet: value })}
            placeholder="Copy the key quote or summary from the source (50-500 characters)"
            error={errors.evidence_snippet}
            required
            minLength={50}
            maxLength={500}
            showCounter
            rows={4}
          />

          {/* Confidence */}
          <RadioGroup
            label="Confidence Level"
            name="confidence"
            value={formData.confidence}
            onChange={(value) => setFormData({ ...formData, confidence: value })}
            options={CONFIDENCE_OPTIONS}
            error={errors.confidence}
            required
          />

          {/* Impact Areas */}
          <CheckboxGroup
            label="Impact Areas"
            name="impact_areas"
            values={formData.impact_areas}
            onChange={(values) => setFormData({ ...formData, impact_areas: values })}
            options={IMPACT_AREA_OPTIONS}
            error={errors.impact_areas}
            required
          />

          {/* Entity Tags (optional) */}
          <TextInput
            label="Entity Tags (optional)"
            name="entity_tags"
            value={formData.entity_tags}
            onChange={(value) => setFormData({ ...formData, entity_tags: value })}
            placeholder="Comma-separated tags, e.g., publisher, competitor, funder"
          />

          {/* Notes (optional) */}
          <TextArea
            label="Notes (optional)"
            name="notes"
            value={formData.notes}
            onChange={(value) => setFormData({ ...formData, notes: value })}
            placeholder="Any additional context or observations"
            rows={3}
          />

          {/* Form Actions */}
          <div className="flex gap-4 pt-4 border-t">
            <button
              type="submit"
              disabled={isSubmitting}
              className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isSubmitting ? 'Saving...' : 'Save Signal'}
            </button>
            <button
              type="button"
              onClick={handleCancel}
              className="px-6 py-2 border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-gray-500"
            >
              Cancel
            </button>
          </div>
        </form>
      </main>
    </div>
  );
}
