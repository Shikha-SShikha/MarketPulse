import { apiClient } from './client';
import type { Signal, SignalCreate, SignalListResponse, SemanticSearchResponse, SignalSummary } from '../types';

export async function createSignal(data: SignalCreate): Promise<Signal> {
  const response = await apiClient.post<Signal>('/signals', data);
  return response.data;
}

export async function getSignals(params?: {
  limit?: number;
  offset?: number;
  entity?: string;
  topic?: string;
  segment?: string;
  impact_area?: string;
  start_date?: string; // YYYY-MM-DD format
  end_date?: string; // YYYY-MM-DD format
}): Promise<SignalListResponse> {
  const response = await apiClient.get<SignalListResponse>('/signals', { params });
  return response.data;
}

export async function getSignal(id: string): Promise<Signal> {
  const response = await apiClient.get<Signal>(`/signals/${id}`);
  return response.data;
}

export async function deleteSignal(id: string): Promise<void> {
  await apiClient.delete(`/signals/${id}`);
}

// Get unique values for autocomplete
export async function getUniqueEntities(): Promise<string[]> {
  const response = await getSignals({ limit: 100 });
  const entities = new Set(response.signals.map((s) => s.entity));
  return Array.from(entities).sort();
}

export async function getUniqueTopics(): Promise<string[]> {
  const response = await getSignals({ limit: 100 });
  const topics = new Set(response.signals.map((s) => s.topic));
  return Array.from(topics).sort();
}

// Get pending signals for curator review
export async function getPendingSignals(params?: {
  limit?: number;
  offset?: number;
}): Promise<SignalListResponse> {
  const response = await apiClient.get<SignalListResponse>('/admin/signals/pending', { params });
  return response.data;
}

// Update signal status (approve/reject)
export async function updateSignalStatus(
  signalId: string,
  status: 'approved' | 'rejected',
  reviewerName?: string
): Promise<Signal> {
  const response = await apiClient.patch<Signal>(`/admin/signals/${signalId}/status`, {
    status,
    reviewer_name: reviewerName,
  });
  return response.data;
}

// Get AI-generated summary of signals
export async function getSignalsSummary(params?: {
  entity?: string;
  topic?: string;
  segment?: string;
  start_date?: string;
  end_date?: string;
}): Promise<SignalSummary> {
  const response = await apiClient.get<SignalSummary>('/signals/summary', { params });
  return response.data;
}

// Semantic search using natural language queries
export async function semanticSearchSignals(params: {
  q: string;
  limit?: number;
  threshold?: number;
  entity?: string;
  topic?: string;
  days_back?: number;
}): Promise<SemanticSearchResponse> {
  const response = await apiClient.get<SemanticSearchResponse>('/signals/search', { params });
  return response.data;
}
