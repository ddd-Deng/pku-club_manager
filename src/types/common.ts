/** 统一响应结构：真实后端与本地 mock 返回完全一致 */
export interface ApiResponse<T = unknown> {
  /** 0 表示成功；非 0 为业务错误码，401 表示未登录或登录失效 */
  code: number
  message: string
  data: T
}

/** 列表查询通用分页参数 */
export interface PageQuery {
  page?: number
  pageSize?: number
}

/** 列表统一分页结构 */
export interface PageResult<T> {
  list: T[]
  total: number
  page: number
  pageSize: number
}

/** 系统角色：学生 / 社长 / 管理员 */
export type Role = 'student' | 'clubAdmin' | 'admin'

/** GET /api/test/hello 返回结构 */
export interface HelloResult {
  message: string
  /** 数据来源：mock 或真实后端 */
  source: 'mock' | 'server'
  serverTime: string
}
