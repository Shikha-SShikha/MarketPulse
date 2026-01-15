import { apiClient } from './client';
import type { WeeklyBrief } from '../types';

export async function getCurrentBrief(): Promise<WeeklyBrief | null> {
  try {
    const response = await apiClient.get<WeeklyBrief>('/briefs/current');
    // 204 No Content means no brief available
    if (response.status === 204 || !response.data) {
      return null;
    }
    return response.data;
  } catch (error: any) {
    // If it's a 204, that's not an error - just no brief available
    if (error.response?.status === 204) {
      return null;
    }
    throw error;
  }
}

export async function getBriefById(id: string): Promise<WeeklyBrief> {
  const response = await apiClient.get<WeeklyBrief>(`/briefs/${id}`);
  return response.data;
}

export interface GenerateBriefResponse {
  message: string;
  brief_id: string;
  week_start: string;
  week_end: string;
  themes_created: number;
  signals_processed: number;
}

export async function generateBrief(): Promise<GenerateBriefResponse> {
  const response = await apiClient.post<GenerateBriefResponse>('/admin/generate-brief');
  return response.data;
}

export async function downloadBriefPdf(briefId: string): Promise<void> {
  const response = await apiClient.get(`/briefs/${briefId}/download`, {
    responseType: 'blob',
  });

  // Extract filename from Content-Disposition header or use default
  const contentDisposition = response.headers['content-disposition'];
  let filename = 'STM_Intelligence_Brief.pdf';

  if (contentDisposition) {
    const filenameMatch = contentDisposition.match(/filename="?(.+?)"?$/);
    if (filenameMatch) {
      filename = filenameMatch[1];
    }
  }

  // Create blob and trigger download
  const blob = new Blob([response.data], { type: 'application/pdf' });
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  window.URL.revokeObjectURL(url);
}
