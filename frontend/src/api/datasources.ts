import { apiClient } from './client';
import type { DataSource, DataSourceCreate, DataSourceUpdate, CollectSignalsResponse } from '../types';

export async function getDataSources(): Promise<DataSource[]> {
  const response = await apiClient.get<DataSource[]>('/admin/data-sources');
  return response.data;
}

export async function createDataSource(data: DataSourceCreate): Promise<DataSource> {
  const response = await apiClient.post<DataSource>('/admin/data-sources', data);
  return response.data;
}

export async function updateDataSource(id: string, data: DataSourceUpdate): Promise<DataSource> {
  const response = await apiClient.patch<DataSource>(`/admin/data-sources/${id}`, data);
  return response.data;
}

export async function deleteDataSource(id: string): Promise<void> {
  await apiClient.delete(`/admin/data-sources/${id}`);
}

export async function triggerCollection(): Promise<CollectSignalsResponse> {
  const response = await apiClient.post<CollectSignalsResponse>('/admin/collect-signals');
  return response.data;
}
