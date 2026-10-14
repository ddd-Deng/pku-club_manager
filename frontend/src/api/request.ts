import axios, { type AxiosError, type Method } from 'axios'
import { ElMessage } from 'element-plus'

import { dispatchMock, isMockEnabled } from '@/mock'
import type { ApiResponse } from '@/types/common'
import { clearToken, getToken } from '@/utils/storage'

/** 请求配置：页面 / api 模块统一使用，mock 与真实模式共用 */
export interface RequestOptions {
  method: Method
  /** 以 /api 开头的接口路径，例如 /api/clubs */
  url: string
  params?: Record<string, unknown>
  data?: unknown
  /** 为 true 时业务失败不自动弹提示，由页面自行展示失败态 */
  silent?: boolean
}

/** 业务 / 网络错误统一类型 */
export class ApiError extends Error {
  code: number

  constructor(code: number, message: string) {
    super(message)
    this.name = 'ApiError'
    this.code = code
  }
}

const service = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL,
  timeout: 10000
})

// 请求拦截：统一注入 token
service.interceptors.request.use((config) => {
  const token = getToken()
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// 401 时的跳转回调，由 router 层注册，避免 api 层反向依赖 router
let unauthorizedHandler: () => void = () => undefined

export function setUnauthorizedHandler(handler: () => void): void {
  unauthorizedHandler = handler
}

// 响应拦截：HTTP 层 401 清理登录态
service.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    if (error.response?.status === 401) {
      clearToken()
      unauthorizedHandler()
    }
    return Promise.reject(error)
  }
)

/** 校验统一响应结构 { code, message, data }，非 0 抛 ApiError */
function unwrap<T>(body: ApiResponse<T>): T {
  if (body.code === 401) {
    clearToken()
    unauthorizedHandler()
  }
  if (body.code !== 0) {
    throw new ApiError(body.code, body.message || '请求失败')
  }
  return body.data
}

async function requestReal<T>(options: RequestOptions): Promise<ApiResponse<T>> {
  const response = await service.request<ApiResponse<T>>({
    method: options.method,
    url: options.url,
    params: options.params,
    data: options.data
  })
  return response.data
}

/**
 * 统一请求入口：VITE_USE_MOCK=true 走本地 mock，否则走 axios 真实请求。
 * 两种模式返回的信封结构完全一致，页面代码零改动。
 */
export async function request<T>(options: RequestOptions): Promise<T> {
  try {
    const body = isMockEnabled() ? await dispatchMock<T>(options) : await requestReal<T>(options)
    return unwrap<T>(body)
  } catch (error) {
    const apiError = normalizeError(error)
    if (!options.silent) {
      ElMessage.error(apiError.message)
    }
    throw apiError
  }
}

function normalizeError(error: unknown): ApiError {
  if (error instanceof ApiError) {
    return error
  }
  if (axios.isAxiosError(error)) {
    const status = error.response?.status
    const serverMessage = (error.response?.data as ApiResponse | undefined)?.message
    if (status === 401) {
      return new ApiError(401, serverMessage ?? '登录已失效，请重新登录')
    }
    if (serverMessage) {
      return new ApiError(status ?? -1, serverMessage)
    }
    if (error.code === 'ECONNABORTED') {
      return new ApiError(-1, '请求超时，请稍后重试')
    }
    return new ApiError(-1, '网络异常，请检查后端服务是否启动')
  }
  if (error instanceof Error) {
    return new ApiError(-1, error.message)
  }
  return new ApiError(-1, '未知错误')
}
