import type { ClubApplication } from '@/types/club'
import type {
  ActivityRegistrationRecord,
  ChangePasswordPayload,
  FootprintItem,
  UpdateProfilePayload,
  UserInfo
} from '@/types/user'

import { request } from './request'

/** 获取当前登录用户资料 */
export function getProfile(): Promise<UserInfo> {
  return request<UserInfo>({ method: 'GET', url: '/api/user/profile' })
}

/** 修改个人资料 */
export function updateProfile(payload: UpdateProfilePayload): Promise<UserInfo> {
  return request<UserInfo>({ method: 'PUT', url: '/api/user/profile', data: payload })
}

/** 修改密码 */
export function changePassword(payload: ChangePasswordPayload): Promise<null> {
  return request<null>({ method: 'PUT', url: '/api/user/password', data: payload })
}

/** 燕园活动足迹档案 */
export function getFootprints(): Promise<FootprintItem[]> {
  return request<FootprintItem[]>({ method: 'GET', url: '/api/user/footprints' })
}

/** 我的入社申请记录 */
export function getMyApplications(): Promise<ClubApplication[]> {
  return request<ClubApplication[]>({ method: 'GET', url: '/api/user/applications' })
}

/** 我的活动报名记录 */
export function getMyRegistrations(): Promise<ActivityRegistrationRecord[]> {
  return request<ActivityRegistrationRecord[]>({
    method: 'GET',
    url: '/api/user/activity-registrations'
  })
}
