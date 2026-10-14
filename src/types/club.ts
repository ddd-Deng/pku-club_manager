import type { PageQuery } from './common'
import type { Activity } from './activity'

/** 社团卡片信息 */
export interface Club {
  id: string
  name: string
  category: string
  /** 头像，emoji 或图片 url */
  logo: string
  description: string
  memberCount: number
  foundedAt: string
  tags: string[]
  /** 社团简介（详情页展示，可选） */
  introduction?: string
}

/** 社团公告 */
export interface ClubNotice {
  id: string
  title: string
  content: string
  publishedAt: string
}

/** 社团详情 = 卡片信息 + 简介 / 公告 / 近期活动 */
export interface ClubDetail extends Club {
  introduction: string
  notices: ClubNotice[]
  recentActivities: Activity[]
}

/** 社团列表查询参数 */
export interface ClubQuery extends PageQuery {
  keyword?: string
  category?: string
}

export type ApplicationStatus = 'pending' | 'approved' | 'rejected'

/** 入社申请 */
export interface ClubApplication {
  id: string
  clubId: string
  clubName: string
  applicantName: string
  message: string
  status: ApplicationStatus
  createdAt: string
  reviewedAt?: string
}

/** 审核入社申请 */
export interface ReviewApplicationPayload {
  action: 'approve' | 'reject'
  comment?: string
}

/** 社团成员（成员权限管理用） */
export interface ClubMember {
  id: string
  name: string
  role: 'member' | 'officer' | 'owner'
  joinedAt: string
}

/** 编辑社团资料 */
export interface UpdateClubPayload {
  name?: string
  description?: string
  introduction?: string
  logo?: string
  tags?: string[]
}

/** 招新帖 */
export interface RecruitmentPost {
  id: string
  clubId: string
  title: string
  content: string
  deadline: string
  createdAt: string
}
