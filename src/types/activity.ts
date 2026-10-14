import type { PageQuery } from './common'

/** 活动状态：草稿 / 已发布 / 已下架 / 已结束 */
export type ActivityStatus = 'draft' | 'published' | 'unpublished' | 'finished'

export interface Activity {
  id: string
  clubId: string
  clubName: string
  title: string
  /** 封面，emoji 或图片 url */
  cover: string
  description: string
  location: string
  startTime: string
  endTime: string
  status: ActivityStatus
  capacity: number
  registeredCount: number
  /** 活动详情返回，当前登录用户是否已报名 */
  registered?: boolean
  /** 活动类型：讲座 / 比赛 / 演出 / 志愿活动等 */
  type: string
}

/** 活动列表查询参数 */
export interface ActivityQuery extends PageQuery {
  keyword?: string
  clubId?: string
  category?: string
  startDate?: string
  endDate?: string
  status?: ActivityStatus
}

/** 新建 / 编辑活动 */
export interface ActivityPayload {
  title: string
  description: string
  location: string
  startTime: string
  endTime: string
  capacity: number
  type: string
  /** 管理员可指定社团；社长只能使用本社团 */
  clubId?: string
  cover?: string
}

/** 活动报名记录 */
export interface ActivityRegistration {
  id: string
  activityId: string
  userId: string
  userName: string
  status: 'registered' | 'cancelled'
  createdAt: string
}
