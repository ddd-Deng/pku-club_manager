import type { PageResult } from '@/types/common'
import type { SearchHistoryItem, SearchHit, SearchQuery } from '@/types/search'

import { request } from './request'

/** 综合搜索（社团 + 活动，含高级筛选） */
export function search(query: SearchQuery): Promise<PageResult<SearchHit>> {
  return request<PageResult<SearchHit>>({
    method: 'GET',
    url: '/api/search',
    params: { ...query }
  })
}

/** 搜索历史记录 */
export function getSearchHistory(): Promise<SearchHistoryItem[]> {
  return request<SearchHistoryItem[]>({ method: 'GET', url: '/api/search/history' })
}

/** 删除单条搜索历史 */
export function deleteSearchHistory(id: string): Promise<null> {
  return request<null>({ method: 'DELETE', url: `/api/search/history/${id}` })
}

/** 清空搜索历史 */
export function clearSearchHistory(): Promise<null> {
  return request<null>({ method: 'DELETE', url: '/api/search/history' })
}
