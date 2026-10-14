import type { PageQuery } from './common'

export type SearchHitType = 'club' | 'activity'

/** 综合搜索命中条目 */
export interface SearchHit {
  type: SearchHitType
  id: string
  title: string
  subtitle: string
}

/** 搜索查询参数（含高级筛选） */
export interface SearchQuery extends PageQuery {
  keyword: string
  type?: SearchHitType
  category?: string
  startDate?: string
  endDate?: string
  activityType?: string
}

/** 搜索历史记录 */
export interface SearchHistoryItem {
  id: string
  keyword: string
  searchedAt: string
}
