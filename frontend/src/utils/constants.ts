import type { ActivityStatus } from '@/types/activity'
import type { ApplicationStatus, ClubRelation } from '@/types/club'
import type { Role } from '@/types/common'

/** localStorage 中 token 的键名 */
export const TOKEN_STORAGE_KEY = 'campus_club_token'

/** localStorage 中搜索历史的键名 */
export const SEARCH_HISTORY_STORAGE_KEY = 'campus_club_search_history'

/** 角色枚举与中文名 */
export const ROLE_LABELS: Record<Role, string> = {
  student: '学生',
  clubAdmin: '社长',
  admin: '系统管理员'
}

/** 社团分类（与 UI 稿筛选项一致） */
export const CLUB_CATEGORIES = ['学术科技', '文化艺术', '体育竞技', '志愿服务'] as const

/** 社团分类联合类型 */
export type ClubCategory = (typeof CLUB_CATEGORIES)[number]

/** 分页默认值 */
export const DEFAULT_PAGE_SIZE = 8

/** 入社申请状态中文名 */
export const APPLICATION_STATUS_LABELS: Record<ApplicationStatus, string> = {
  pending: '待审核',
  approved: '已通过',
  rejected: '已拒绝'
}

/** 我与社团的关系中文名（社团详情 myStatus） */
export const CLUB_RELATION_LABELS: Record<ClubRelation, string> = {
  none: '未申请',
  pending: '申请审核中',
  approved: '已通过',
  rejected: '已拒绝',
  member: '已是成员'
}

/** 活动状态中文名 */
export const ACTIVITY_STATUS_LABELS: Record<ActivityStatus, string> = {
  draft: '草稿',
  published: '已发布',
  unpublished: '已下架',
  finished: '已结束'
}
