import type { AiChatPayload, AiChatResult, KbDocument } from '@/types/ai'

import { request } from './request'

/** RAG 问答 */
export function chat(payload: AiChatPayload): Promise<AiChatResult> {
  return request<AiChatResult>({ method: 'POST', url: '/api/ai/chat', data: payload })
}

/** 社团文档检索 */
export function searchDocuments(keyword: string): Promise<KbDocument[]> {
  return request<KbDocument[]>({
    method: 'GET',
    url: '/api/ai/documents/search',
    params: { keyword }
  })
}
