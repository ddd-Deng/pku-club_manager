import type { ApiResponse, PageResult, Role } from '@/types/common'

import { mockDb, type MockUser } from './db'

/** mock 层接收的请求描述（由 api/request.ts 传入） */
export interface MockRequest {
  method: string
  url: string
  params?: Record<string, unknown>
  data?: unknown
}

/** handler 上下文 */
export interface MockContext {
  method: string
  url: string
  params: Record<string, unknown>
  data: Record<string, unknown>
  pathParams: Record<string, string>
  headers: Record<string, string>
}

/** mock 业务错误：code 语义与真实后端保持一致 */
export class MockError extends Error {
  code: number

  constructor(code: number, message: string) {
    super(message)
    this.name = 'MockError'
    this.code = code
  }
}

export type MockHandler = (ctx: MockContext) => unknown | Promise<unknown>

interface MockRoute {
  method: string
  segments: string[]
  handler: MockHandler
}

const routes: MockRoute[] = []

/** 注册 mock 路由，path 支持 :param 占位，需带 /api 前缀 */
export function mockRoute(method: string, path: string, handler: MockHandler): void {
  routes.push({
    method: method.toUpperCase(),
    segments: path.split('/').filter(Boolean),
    handler
  })
}

/** 按 method + path 匹配路由 */
export function findRoute(
  method: string,
  url: string
): { handler: MockHandler; pathParams: Record<string, string> } | null {
  const target = method.toUpperCase()
  const parts = url.split('?')[0].split('/').filter(Boolean)
  for (const route of routes) {
    if (route.method !== target || route.segments.length !== parts.length) {
      continue
    }
    const pathParams: Record<string, string> = {}
    let matched = true
    for (let i = 0; i < route.segments.length; i += 1) {
      const segment = route.segments[i]
      if (segment.startsWith(':')) {
        pathParams[segment.slice(1)] = decodeURIComponent(parts[i])
      } else if (segment !== parts[i]) {
        matched = false
        break
      }
    }
    if (matched) {
      return { handler: route.handler, pathParams }
    }
  }
  return null
}

/** 校验 mock 登录态，返回当前用户 */
export function requireAuth(ctx: MockContext): MockUser {
  const authorization = ctx.headers.Authorization ?? ctx.headers.authorization ?? ''
  const token = authorization.replace(/^Bearer\s+/i, '')
  const user = mockDb.users.find((item) => item.token === token)
  if (!user) {
    throw new MockError(401, '登录已失效，请重新登录')
  }
  return user
}

/** 校验角色 */
export function requireRole(ctx: MockContext, roles: Role[]): MockUser {
  const user = requireAuth(ctx)
  if (!roles.includes(user.role)) {
    throw new MockError(403, '无权限访问该接口')
  }
  return user
}

/** 校验社团管理权限：admin 全权，clubAdmin 仅限本社团 */
export function requireClubOwner(ctx: MockContext, clubId: string): MockUser {
  const user = requireRole(ctx, ['clubAdmin', 'admin'])
  if (user.role === 'clubAdmin' && user.clubId !== clubId) {
    throw new MockError(403, '只能管理自己所属的社团')
  }
  return user
}

/** 统一分页切片，结构与真实后端一致 */
export function paginate<T>(list: T[], page?: unknown, pageSize?: unknown): PageResult<T> {
  const safePage = Math.max(1, Number(page) || 1)
  const safeSize = Math.max(1, Number(pageSize) || 8)
  const start = (safePage - 1) * safeSize
  return {
    list: list.slice(start, start + safeSize),
    total: list.length,
    page: safePage,
    pageSize: safeSize
  }
}

/** 读取字符串参数 */
export function readString(source: Record<string, unknown> | undefined, key: string): string {
  const value = source?.[key]
  return typeof value === 'string' ? value.trim() : ''
}

/** 读取数字参数 */
export function readNumber(
  source: Record<string, unknown> | undefined,
  key: string,
  fallback: number
): number {
  const value = Number(source?.[key])
  return Number.isFinite(value) && value > 0 ? value : fallback
}

/** 组装成功响应信封 */
export function ok<T>(data: T): ApiResponse<T> {
  return { code: 0, message: 'ok', data }
}
