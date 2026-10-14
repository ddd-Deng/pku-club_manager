import type { ApiResponse } from '@/types/common'
import { getToken } from '@/utils/storage'

import { findRoute, MockError, ok, type MockContext, type MockRequest } from './registry'

// 注册各模块 mock 路由（副作用导入）
import './handlers/auth'
import './handlers/user'
import './handlers/club'
import './handlers/activity'
import './handlers/misc'

/** 是否启用本地 mock：由环境变量 VITE_USE_MOCK 控制 */
export function isMockEnabled(): boolean {
  return import.meta.env.VITE_USE_MOCK === 'true'
}

const MIN_DELAY = 200
const MAX_DELAY = 500

/** 模拟网络延迟，方便演示加载态 */
function delay(): Promise<void> {
  const ms = MIN_DELAY + Math.random() * (MAX_DELAY - MIN_DELAY)
  return new Promise((resolve) => {
    setTimeout(resolve, ms)
  })
}

/**
 * mock 请求分发：匹配路由 -> 执行 handler -> 包装成与真实后端一致的
 * { code, message, data } 信封返回。
 */
export async function dispatchMock<T>(options: MockRequest): Promise<ApiResponse<T>> {
  await delay()
  const matched = findRoute(options.method, options.url)
  if (!matched) {
    return {
      code: -1,
      message: `[mock] 接口未实现：${options.method.toUpperCase()} ${options.url}（契约见 docs/api.md）`,
      data: null as T
    }
  }
  const token = getToken()
  const ctx: MockContext = {
    method: options.method.toUpperCase(),
    url: options.url,
    params: options.params ?? {},
    data: (options.data ?? {}) as Record<string, unknown>,
    pathParams: matched.pathParams,
    headers: token ? { Authorization: `Bearer ${token}` } : {}
  }
  try {
    const data = await matched.handler(ctx)
    return ok(data as T)
  } catch (error) {
    if (error instanceof MockError) {
      return { code: error.code, message: error.message, data: null as T }
    }
    throw error
  }
}
