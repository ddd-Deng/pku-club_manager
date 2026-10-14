import type { HelloResult } from '@/types/common'

import { request } from './request'

/** 连通性测试：GET /api/test/hello */
export function getHello(): Promise<HelloResult> {
  return request<HelloResult>({ method: 'GET', url: '/api/test/hello' })
}
