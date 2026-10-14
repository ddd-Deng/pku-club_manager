import type { PageResult } from '@/types/common'
import type {
  Club,
  ClubApplication,
  ClubDetail,
  ClubMember,
  ClubQuery,
  RecruitmentPost,
  ReviewApplicationPayload,
  UpdateClubPayload
} from '@/types/club'

import { request } from './request'

/** 社团列表（分页 + 关键词 + 分类筛选） */
export function getClubs(query: ClubQuery = {}): Promise<PageResult<Club>> {
  return request<PageResult<Club>>({
    method: 'GET',
    url: '/api/clubs',
    params: { ...query }
  })
}

/** 社团分类枚举 */
export function getClubCategories(): Promise<string[]> {
  return request<string[]>({ method: 'GET', url: '/api/clubs/categories' })
}

/** 首页社团推荐卡片 */
export function getRecommendedClubs(): Promise<Club[]> {
  return request<Club[]>({ method: 'GET', url: '/api/clubs/recommended' })
}

/** 社团详情 */
export function getClubDetail(id: string): Promise<ClubDetail> {
  return request<ClubDetail>({ method: 'GET', url: `/api/clubs/${id}` })
}

/** 编辑社团资料（社长 / 管理员） */
export function updateClub(id: string, payload: UpdateClubPayload): Promise<ClubDetail> {
  return request<ClubDetail>({ method: 'PUT', url: `/api/clubs/${id}`, data: payload })
}

/** 提交入社申请（学生） */
export function applyJoinClub(clubId: string, message: string): Promise<ClubApplication> {
  return request<ClubApplication>({
    method: 'POST',
    url: `/api/clubs/${clubId}/applications`,
    data: { message }
  })
}

/** 入社申请列表（社长 / 管理员） */
export function getClubApplications(
  clubId: string,
  query: { status?: string; page?: number; pageSize?: number } = {}
): Promise<PageResult<ClubApplication>> {
  return request<PageResult<ClubApplication>>({
    method: 'GET',
    url: `/api/clubs/${clubId}/applications`,
    params: { ...query }
  })
}

/** 审核入社申请（社长 / 管理员） */
export function reviewApplication(
  clubId: string,
  applicationId: string,
  payload: ReviewApplicationPayload
): Promise<ClubApplication> {
  return request<ClubApplication>({
    method: 'PUT',
    url: `/api/clubs/${clubId}/applications/${applicationId}`,
    data: payload
  })
}

/** 社团成员列表（社长 / 管理员） */
export function getClubMembers(clubId: string): Promise<ClubMember[]> {
  return request<ClubMember[]>({ method: 'GET', url: `/api/clubs/${clubId}/members` })
}

/** 修改成员角色或移除成员（社长 / 管理员） */
export function updateClubMember(
  clubId: string,
  memberId: string,
  payload: { role?: 'member' | 'officer'; action?: 'remove' }
): Promise<ClubMember> {
  return request<ClubMember>({
    method: 'PUT',
    url: `/api/clubs/${clubId}/members/${memberId}`,
    data: payload
  })
}

/** 发布招新帖（社长 / 管理员） */
export function publishRecruitment(
  clubId: string,
  payload: { title: string; content: string; deadline: string }
): Promise<RecruitmentPost> {
  return request<RecruitmentPost>({
    method: 'POST',
    url: `/api/clubs/${clubId}/recruitments`,
    data: payload
  })
}

/** 公开招新帖列表 */
export function getRecruitments(clubId: string): Promise<RecruitmentPost[]> {
  return request<RecruitmentPost[]>({ method: 'GET', url: `/api/clubs/${clubId}/recruitments` })
}
