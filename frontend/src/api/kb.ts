import type { KbDocument, KbDocumentQuery } from '@/types/ai'
import type { PageResult } from '@/types/common'

import { request } from './request'

/** 上传知识库文档（社长 / 管理员；真实模式为 multipart/form-data） */
export function uploadDocument(payload: {
  title: string
  size: number
  clubId?: string
}): Promise<KbDocument> {
  return request<KbDocument>({ method: 'POST', url: '/api/kb/documents', data: payload })
}

/** 知识库文档列表 */
export function getDocuments(query: KbDocumentQuery = {}): Promise<PageResult<KbDocument>> {
  return request<PageResult<KbDocument>>({
    method: 'GET',
    url: '/api/kb/documents',
    params: { ...query }
  })
}

/** 删除知识库文档（社长 / 管理员） */
export function deleteDocument(id: string): Promise<null> {
  return request<null>({ method: 'DELETE', url: `/api/kb/documents/${id}` })
}
