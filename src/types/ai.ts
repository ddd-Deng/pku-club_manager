import type { PageQuery } from './common'

/** 对话消息 */
export interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
}

/** RAG 问答请求 */
export interface AiChatPayload {
  question: string
  clubId?: string
  history?: ChatMessage[]
}

/** 答案引用的知识库文档 */
export interface AiReference {
  docId: string
  title: string
}

export interface AiChatResult {
  answer: string
  references: AiReference[]
}

/** 知识库文档 */
export interface KbDocument {
  id: string
  clubId: string
  clubName: string
  title: string
  /** 文件大小（字节） */
  size: number
  uploadedBy: string
  uploadedAt: string
}

export interface KbDocumentQuery extends PageQuery {
  clubId?: string
}
