import { apiClient } from './client';
import type { Notification } from '../types';

export async function getNotifications(unreadOnly: boolean = true, limit: number = 20): Promise<Notification[]> {
  const response = await apiClient.get<Notification[]>('/notifications', {
    params: { unread_only: unreadOnly, limit },
  });
  return response.data;
}

export async function markNotificationRead(id: string): Promise<void> {
  await apiClient.patch(`/notifications/${id}/read`);
}
