import assert from 'node:assert/strict'
import { webcrypto } from 'node:crypto'
import { createRequire } from 'node:module'
import { fileURLToPath } from 'node:url'
import vm from 'node:vm'
import test from 'node:test'

// Use Vite's installed esbuild; no additional test dependency or browser state.
const require = createRequire(import.meta.url)
const { build } = require('esbuild')
const directory = fileURLToPath(new URL('../', import.meta.url))
const compiled = await build({
  stdin: {
    contents: `export { mockDb } from './src/mock/db';
    export { findRoute } from './src/mock/registry';
    import './src/mock/handlers/auth'; import './src/mock/handlers/user';
    import './src/mock/handlers/club'; import './src/mock/handlers/admin';
    import './src/mock/handlers/misc';`,
    resolveDir: directory,
    loader: 'ts'
  },
  bundle: true,
  write: false,
  platform: 'node',
  format: 'cjs',
  alias: { '@': `${directory}src` }
})

function setup() {
  const module = { exports: {} }
  vm.runInNewContext(compiled.outputFiles[0].text, {
    module,
    exports: module.exports,
    crypto: webcrypto,
    localStorage: { getItem: () => null, setItem: () => {}, removeItem: () => {} }
  })
  const { mockDb, findRoute } = module.exports
  function call(method, url, token = '', data = {}, params = {}) {
    const matched = findRoute(method, url)
    assert.ok(matched, url)
    return matched.handler({
      method,
      url,
      params,
      data,
      pathParams: matched.pathParams,
      headers: token ? { Authorization: `Bearer ${token}` } : {}
    })
  }
  function login(account) {
    return call('POST', '/api/auth/login', '', { account, password: '123456' }).token
  }
  return { mockDb, call, login }
}

test('admin-only account APIs reject empty tokens and protect administrator accounts', () => {
  const { call, login, mockDb } = setup()
  assert.throws(() => call('GET', '/api/admin/users'), /请先登录/)
  const student = login('2024001')
  assert.throws(() => call('GET', '/api/admin/users', student), /无权限/)
  const admin = login('admin')
  const result = call('GET', '/api/admin/users', admin)
  assert.equal(result.total, 2)
  assert.equal(result.pageSize, 10)
  assert.ok(result.list.every((item) => !('password' in item) && !('token' in item)))
  assert.throws(
    () => call('PUT', '/api/admin/users/u-admin/status', admin, { isActive: false }),
    /管理员账号/
  )
  assert.throws(
    () => call('PUT', '/api/admin/users/u-student', admin, { email: 'admin@campus.edu.cn' }),
    /已被/
  )
  mockDb.users[0].token = ''
  assert.equal(call('GET', '/api/clubs/c-1').myStatus, null)
  assert.throws(() => call('GET', '/api/user/profile'), /请先登录/)
})

test('disable and enable do not revive old tokens, and a president must hand over first', () => {
  const { call, login } = setup()
  const admin = login('admin'),
    old = login('2024001')
  assert.throws(
    () => call('PUT', '/api/admin/users/u-club/status', admin, { isActive: false }),
    /先更换/
  )
  call('PUT', '/api/admin/users/u-student/status', admin, { isActive: false })
  assert.throws(() => call('GET', '/api/user/profile', old), /失效/)
  assert.throws(() => login('2024001'), /停用/)
  call('PUT', '/api/admin/users/u-student/status', admin, { isActive: true })
  assert.throws(() => call('GET', '/api/user/profile', old), /失效/)
  assert.notEqual(login('2024001'), old)
})

test('handover uses account IDs, preserves former membership and processes pending applications', () => {
  const { call, login, mockDb } = setup()
  const admin = login('admin'),
    oldOwner = login('2021002'),
    student = login('2024001')
  const application = call('POST', '/api/clubs/c-1/applications', student, { message: '测试' })
  call('PUT', '/api/admin/users/u-student', admin, { name: '改名学生' })
  call('PUT', '/api/admin/clubs/c-1/president', admin, {
    userId: 'u-student',
    expectedPresidentId: 'u-club'
  })
  assert.equal(application.status, 'approved')
  assert.equal(mockDb.users.find((u) => u.id === 'u-club').role, 'student')
  assert.equal(mockDb.members.find((m) => m.userId === 'u-club').role, 'member')
  assert.equal(mockDb.members.find((m) => m.userId === 'u-student').role, 'owner')
  assert.throws(() => call('GET', '/api/user/profile', oldOwner), /失效/)
  const fresh = login('2024001')
  const memberCount = mockDb.members.length
  call('PUT', '/api/admin/clubs/c-1/president', admin, {
    userId: 'u-student',
    expectedPresidentId: 'u-club'
  })
  assert.equal(mockDb.members.length, memberCount)
  assert.equal(call('GET', '/api/user/profile', fresh).role, 'clubAdmin')
  assert.throws(
    () =>
      call('PUT', '/api/admin/clubs/c-2/president', admin, {
        userId: 'u-student',
        expectedPresidentId: null
      }),
    /其他社团/
  )
  const newOwnerMember = mockDb.members.find((m) => m.userId === 'u-student')
  assert.throws(
    () => call('PUT', `/api/clubs/c-1/members/${newOwnerMember.id}`, admin, { action: 'remove' }),
    /所有者/
  )
  assert.equal(call('GET', '/api/notifications', fresh).total, 3)
})

test('first appointment promotes existing members, detects stale owners and self password changes revoke sessions', () => {
  const { call, login, mockDb } = setup()
  const admin = login('admin'),
    student = login('2024001')
  mockDb.members.push({
    id: 'existing',
    clubId: 'c-2',
    userId: 'u-student',
    name: '林晓',
    role: 'officer',
    joinedAt: new Date().toISOString()
  })
  assert.throws(
    () =>
      call('PUT', '/api/admin/clubs/c-2/president', admin, {
        userId: 'u-student',
        expectedPresidentId: 'stale'
      }),
    /刷新/
  )
  call('PUT', '/api/admin/clubs/c-2/president', admin, {
    userId: 'u-student',
    expectedPresidentId: null
  })
  assert.equal(
    mockDb.members.filter((m) => m.clubId === 'c-2' && m.userId === 'u-student').length,
    1
  )
  const fresh = login('2024001')
  assert.notEqual(fresh, student)
  call('PUT', '/api/user/password', fresh, { oldPassword: '123456', newPassword: 'self-password' })
  assert.throws(() => call('GET', '/api/user/profile', fresh), /失效/)
  assert.throws(() => login('2024001'), /账号或密码/)
  assert.ok(
    call('POST', '/api/auth/login', '', { account: '2024001', password: 'self-password' }).token
  )
})
