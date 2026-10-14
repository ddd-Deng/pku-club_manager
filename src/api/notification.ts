import type { PageResult } from '@/types/common'
import type { NotificationItem, NotificationQuery } from '@/types/notification'

import { request } from './request'

/** 通知列表（分页 + 类型 / 已读筛选） */
export function getNotifications(
  query: NotificationQuery = {}
): Promise<PageResult<NotificationItem>> {
  return request<PageResult<NotificationItem>>({
    method: 'GET',
    url: '/api/notifications',
    params: { ...query }
  })
}

/** 未读通知数（顶栏角标） */
export function getUnreadCount(): Promise<number> {
  return request<number>({ method: 'GET', url: '/api/notifications/unread-count' })
}

/** 标记单条已读 */
export function markNotificationRead(id: string): Promise<NotificationItem> {
  return request<NotificationItem>({ method: 'PUT', url: `/api/notifications/${id}/read` })
}

/** 全部标记已读 */
export function markAllNotificationsRead(): Promise<{ updated: number }> {
  return request<{ updated: number }>({ method: 'PUT', url: '/api/notifications/read-all' })
}
