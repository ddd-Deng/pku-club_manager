import type {
  Activity,
  ActivityPayload,
  ActivityQuery,
  ActivityRegistration
} from '@/types/activity'
import type { PageResult } from '@/types/common'

import { request } from './request'

/** 活动列表（分页 + 筛选） */
export function getActivities(query: ActivityQuery = {}): Promise<PageResult<Activity>> {
  return request<PageResult<Activity>>({
    method: 'GET',
    url: '/api/activities',
    params: { ...query }
  })
}

/** 近期活动 / 首页活动预告 */
export function getUpcomingActivities(): Promise<Activity[]> {
  return request<Activity[]>({ method: 'GET', url: '/api/activities/upcoming' })
}

/** 活动详情 */
export function getActivityDetail(id: string): Promise<Activity> {
  return request<Activity>({ method: 'GET', url: `/api/activities/${id}` })
}

/** 新建活动（默认存草稿，社长 / 管理员） */
export function createActivity(payload: ActivityPayload): Promise<Activity> {
  return request<Activity>({ method: 'POST', url: '/api/activities', data: payload })
}

/** 编辑活动（社长 / 管理员） */
export function updateActivity(id: string, payload: Partial<ActivityPayload>): Promise<Activity> {
  return request<Activity>({ method: 'PUT', url: `/api/activities/${id}`, data: payload })
}

/** 发布活动（草稿 -> 已发布） */
export function publishActivity(id: string): Promise<Activity> {
  return request<Activity>({ method: 'POST', url: `/api/activities/${id}/publish` })
}

/** 下架活动 */
export function unpublishActivity(id: string): Promise<Activity> {
  return request<Activity>({ method: 'POST', url: `/api/activities/${id}/unpublish` })
}

/** 删除活动 */
export function deleteActivity(id: string): Promise<null> {
  return request<null>({ method: 'DELETE', url: `/api/activities/${id}` })
}

/** 活动报名（学生） */
export function registerActivity(id: string): Promise<ActivityRegistration> {
  return request<ActivityRegistration>({
    method: 'POST',
    url: `/api/activities/${id}/registrations`
  })
}

/** 取消报名（学生） */
export function cancelRegistration(id: string): Promise<null> {
  return request<null>({ method: 'DELETE', url: `/api/activities/${id}/registrations` })
}
