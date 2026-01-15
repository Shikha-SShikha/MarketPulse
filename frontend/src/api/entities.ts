import { apiClient } from './client';
import type { Entity, EntityCreate, EntityUpdate, EntityListResponse } from '../types';

/**
 * Get list of entities with optional filtering.
 */
export async function getEntities(params?: {
  segment?: string;
  limit?: number;
  offset?: number;
}): Promise<EntityListResponse> {
  const response = await apiClient.get<EntityListResponse>('/admin/entities', { params });
  return response.data;
}

/**
 * Get a single entity by ID.
 */
export async function getEntity(id: string): Promise<Entity> {
  const response = await apiClient.get<Entity>(`/admin/entities/${id}`);
  return response.data;
}

/**
 * Create a new entity.
 */
export async function createEntity(data: EntityCreate): Promise<Entity> {
  const response = await apiClient.post<Entity>('/admin/entities', data);
  return response.data;
}

/**
 * Update an existing entity.
 */
export async function updateEntity(id: string, data: EntityUpdate): Promise<Entity> {
  const response = await apiClient.patch<Entity>(`/admin/entities/${id}`, data);
  return response.data;
}

/**
 * Delete an entity.
 */
export async function deleteEntity(id: string): Promise<void> {
  await apiClient.delete(`/admin/entities/${id}`);
}
