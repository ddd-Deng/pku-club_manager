import type { LoginPayload, LoginResult, RegisterPayload } from '@/types/user'

import { request } from './request'

/** 统一账号登录 */
export function login(payload: LoginPayload): Promise<LoginResult> {
  return request<LoginResult>({ method: 'POST', url: '/api/auth/login', data: payload })
}

/** 注册学生账号（注册成功即登录） */
export function register(payload: RegisterPayload): Promise<LoginResult> {
  return request<LoginResult>({ method: 'POST', url: '/api/auth/register', data: payload })
}

/** 登出 */
export function logout(): Promise<null> {
  return request<null>({ method: 'POST', url: '/api/auth/logout' })
}

/** 密码找回：校验学籍信息 */
export function forgotPassword(payload: { studentNo: string; email: string }): Promise<null> {
  return request<null>({ method: 'POST', url: '/api/auth/password/forgot', data: payload })
}

/** 学生身份校验 */
export function verifyStudent(payload: {
  studentNo: string
  email: string
}): Promise<{ verified: boolean; name: string }> {
  return request<{ verified: boolean; name: string }>({
    method: 'POST',
    url: '/api/auth/student-verify',
    data: payload
  })
}
