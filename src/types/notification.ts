import type { PageQuery } from './common'

/** 通知类型：入社申请审核 / 活动上新 / 场地预约审批 */
export type NotificationType = 'application' | 'activity' | 'venue'

export interface NotificationItem {
  id: string
  type: NotificationType
  title: string
  content: string
  read: boolean
  createdAt: string
  /** 点击跳转的前端路由 */
  link?: string
}

export interface NotificationQuery extends PageQuery {
  type?: NotificationType
  read?: boolean
}
