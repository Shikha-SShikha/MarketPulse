import { apiClient } from './client';
import type { SegmentStatsResponse } from '../types';

/**
 * Get segment statistics for dashboard widgets.
 */
export async function getSegmentStats(days: number = 7): Promise<SegmentStatsResponse> {
  const response = await apiClient.get<SegmentStatsResponse>('/segments/stats', {
    params: { days },
  });
  return response.data;
}
