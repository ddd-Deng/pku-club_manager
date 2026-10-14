import type { Role } from './common'
import type { ClubApplication } from './club'

/** 登录用户信息 */
export interface UserInfo {
  id: string
  name: string
  studentNo: string
  email: string
  role: Role
  /** 头像，emoji 或图片 url */
  avatar: string
  /** 社长所管理的社团 id，student / admin 为空 */
  clubId?: string
  clubName?: string
}

export interface LoginPayload {
  /** 学号 / 邮箱 / 管理员账号 */
  account: string
  password: string
  remember?: boolean
}

export interface LoginResult {
  token: string
  user: UserInfo
}

export interface RegisterPayload {
  name: string
  studentNo: string
  email: string
  password: string
}

export interface UpdateProfilePayload {
  name?: string
  email?: string
  avatar?: string
}

export interface ChangePasswordPayload {
  oldPassword: string
  newPassword: string
}

/** 我的活动报名记录 */
export interface ActivityRegistrationRecord {
  id: string
  activityId: string
  title: string
  clubName: string
  startTime: string
  status: 'registered' | 'cancelled'
  createdAt: string
}

/** 燕园活动足迹档案条目 */
export interface FootprintItem {
  id: string
  activityId: string
  title: string
  clubName: string
  finishedAt: string
}

export type { ClubApplication }
