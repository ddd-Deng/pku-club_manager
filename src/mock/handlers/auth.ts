import type { LoginResult, UserInfo } from '@/types/user'

import { mockDb, type MockUser } from '../db'
import { MockError, mockRoute, readString } from '../registry'

/** 去掉凭据字段，返回可对外暴露的用户信息 */
export function toPublicUser(user: MockUser): UserInfo {
  return {
    id: user.id,
    name: user.name,
    studentNo: user.studentNo,
    email: user.email,
    role: user.role,
    avatar: user.avatar,
    clubId: user.clubId,
    clubName: user.clubName
  }
}

mockRoute('POST', '/api/auth/login', (ctx) => {
  const account = readString(ctx.data, 'account')
  const password = readString(ctx.data, 'password')
  if (!account || !password) {
    throw new MockError(1003, '请输入账号和密码')
  }
  const user = mockDb.users.find((item) => item.studentNo === account || item.email === account)
  if (!user || user.password !== password) {
    throw new MockError(1001, '账号或密码错误')
  }
  const result: LoginResult = { token: user.token, user: toPublicUser(user) }
  return result
})

mockRoute('POST', '/api/auth/register', (ctx) => {
  const name = readString(ctx.data, 'name')
  const studentNo = readString(ctx.data, 'studentNo')
  const email = readString(ctx.data, 'email')
  const password = readString(ctx.data, 'password')
  if (!name || !studentNo || !email || !password) {
    throw new MockError(1003, '注册信息不完整')
  }
  if (mockDb.users.some((item) => item.studentNo === studentNo)) {
    throw new MockError(1004, '该学号已注册')
  }
  const user: MockUser = {
    id: `u-${Date.now()}`,
    name,
    studentNo,
    email,
    role: 'student',
    avatar: '🧑‍🎓',
    token: `mock-token-${studentNo}`,
    password
  }
  mockDb.users.push(user)
  const result: LoginResult = { token: user.token, user: toPublicUser(user) }
  return result
})

mockRoute('POST', '/api/auth/logout', () => {
  // mock 不做服务端 session 管理，登出由前端清理 token
  return null
})

mockRoute('POST', '/api/auth/password/forgot', (ctx) => {
  const studentNo = readString(ctx.data, 'studentNo')
  const email = readString(ctx.data, 'email')
  const user = mockDb.users.find((item) => item.studentNo === studentNo && item.email === email)
  if (!user) {
    throw new MockError(1002, '学籍信息不匹配，无法找回密码')
  }
  return null
})

mockRoute('POST', '/api/auth/student-verify', (ctx) => {
  const studentNo = readString(ctx.data, 'studentNo')
  const email = readString(ctx.data, 'email')
  const user = mockDb.users.find((item) => item.studentNo === studentNo && item.email === email)
  return { verified: Boolean(user), name: user?.name ?? '' }
})
