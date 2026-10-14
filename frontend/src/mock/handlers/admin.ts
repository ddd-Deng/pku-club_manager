import type { AdminAccount, AdminClub } from '@/types/admin'
import { mockDb, type MockUser } from '../db'
import { MockError, mockRoute, readString, requireRole, paginate } from '../registry'
import { toPublicUser } from './auth'

function accountData(user: MockUser): AdminAccount {
  return {
    ...toPublicUser(user),
    isActive: user.isActive !== false,
    createdAt: user.createdAt ?? '2026-01-01T00:00:00Z'
  }
}
function target(id: string): MockUser {
  const user = mockDb.users.find((item) => item.id === id)
  if (!user) throw new MockError(1404, '账号不存在')
  if (user.role === 'admin') throw new MockError(403, '此功能不能修改管理员账号')
  return user
}
function clubData(id: string): AdminClub {
  const club = mockDb.clubs.find((item) => item.id === id)
  if (!club) throw new MockError(1404, '社团不存在')
  const president = mockDb.users.find((user) => user.role === 'clubAdmin' && user.clubId === id)
  return {
    id,
    name: club.name,
    category: club.category,
    president: president
      ? { id: president.id, name: president.name, studentNo: president.studentNo }
      : null
  }
}
function adminPage<T>(list: T[], params: Record<string, unknown>) {
  const page = Number(params.page ?? 1)
  const pageSize = Number(params.pageSize ?? 10)
  if (
    !Number.isInteger(page) ||
    page < 1 ||
    !Number.isInteger(pageSize) ||
    pageSize < 1 ||
    pageSize > 100
  )
    throw new MockError(1003, '分页参数无效')
  return paginate(list, page, pageSize)
}

mockRoute('GET', '/api/admin/users', (ctx) => {
  requireRole(ctx, ['admin'])
  const keyword = readString(ctx.params, 'keyword').toLowerCase()
  const role = readString(ctx.params, 'role')
  if (role && !['student', 'clubAdmin'].includes(role)) throw new MockError(1003, '角色筛选无效')
  const active = ctx.params.isActive
  const list = mockDb.users
    .filter(
      (user) =>
        user.role !== 'admin' &&
        (!role || user.role === role) &&
        (active === undefined ||
          (user.isActive !== false) === (active === true || active === 'true')) &&
        (!keyword || `${user.name} ${user.studentNo} ${user.email}`.toLowerCase().includes(keyword))
    )
    .sort(
      (a, b) => (b.createdAt ?? '').localeCompare(a.createdAt ?? '') || a.id.localeCompare(b.id)
    )
  return adminPage(list.map(accountData), ctx.params)
})

mockRoute('PUT', '/api/admin/users/:id', (ctx) => {
  requireRole(ctx, ['admin'])
  const user = target(ctx.pathParams.id)
  const keys = Object.keys(ctx.data)
  if (!keys.length || keys.some((key) => !['name', 'email'].includes(key)))
    throw new MockError(1003, '仅可修改姓名和邮箱')
  const name = readString(ctx.data, 'name')
  const email = readString(ctx.data, 'email').toLowerCase()
  if ('name' in ctx.data && (!name || name.length > 100)) throw new MockError(1003, '姓名无效')
  if ('email' in ctx.data && (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email) || email.length > 254))
    throw new MockError(1003, '邮箱格式无效')
  if (email && mockDb.users.some((item) => item.id !== user.id && item.email === email))
    throw new MockError(1004, '邮箱已被其他账号使用')
  if (name) {
    user.name = name
    for (const member of mockDb.members.filter((item) => item.userId === user.id))
      member.name = name
  }
  if (email) user.email = email
  return accountData(user)
})

mockRoute('PUT', '/api/admin/users/:id/status', (ctx) => {
  requireRole(ctx, ['admin'])
  const user = target(ctx.pathParams.id)
  if (typeof ctx.data.isActive !== 'boolean' || Object.keys(ctx.data).length !== 1)
    throw new MockError(1003, 'isActive 必须为布尔值')
  if (!ctx.data.isActive && user.role === 'clubAdmin')
    throw new MockError(1409, '请先更换该社团社长，再禁用此账号')
  user.isActive = ctx.data.isActive
  if (!user.isActive) user.token = ''
  return accountData(user)
})

mockRoute('GET', '/api/admin/clubs', (ctx) => {
  requireRole(ctx, ['admin'])
  const keyword = readString(ctx.params, 'keyword')
  return adminPage(
    mockDb.clubs
      .filter((club) => !keyword || club.name.includes(keyword))
      .map((club) => clubData(club.id)),
    ctx.params
  )
})

mockRoute('PUT', '/api/admin/clubs/:id/president', (ctx) => {
  requireRole(ctx, ['admin'])
  if (
    Object.keys(ctx.data).some((key) => !['userId', 'expectedPresidentId'].includes(key)) ||
    !('expectedPresidentId' in ctx.data) ||
    !(ctx.data.expectedPresidentId === null || typeof ctx.data.expectedPresidentId === 'string')
  )
    throw new MockError(1003, '任命参数不完整')
  const club = clubData(ctx.pathParams.id)
  const candidate = target(readString(ctx.data, 'userId'))
  if (candidate.isActive === false) throw new MockError(1409, '候选人必须是启用的学生账号')
  if (candidate.role === 'clubAdmin' && candidate.clubId !== club.id)
    throw new MockError(1409, '候选人已管理其他社团，请先完成原社团交接')
  if (club.president?.id === candidate.id) return club
  if ((club.president?.id ?? null) !== ctx.data.expectedPresidentId)
    throw new MockError(1410, '社长已被其他管理员更改，请刷新后重试')
  const former = club.president ? target(club.president.id) : null
  const oldMember = former
    ? mockDb.members.find((member) => member.clubId === club.id && member.userId === former.id)
    : null
  if (former && (!oldMember || oldMember.role !== 'owner'))
    throw new MockError(1409, '原社长成员数据不一致，请联系维护者')
  if (former && oldMember) {
    former.role = 'student'
    former.clubId = null
    former.clubName = null
    former.token = ''
    oldMember.role = 'member'
  }
  candidate.role = 'clubAdmin'
  candidate.clubId = club.id
  candidate.clubName = club.name
  candidate.token = ''
  const member = mockDb.members.find(
    (item) => item.clubId === club.id && item.userId === candidate.id
  )
  if (member) member.role = 'owner'
  else {
    mockDb.members.push({
      id: `m-${crypto.randomUUID()}`,
      userId: candidate.id,
      clubId: club.id,
      name: candidate.name,
      role: 'owner',
      joinedAt: new Date().toISOString()
    })
    const publicClub = mockDb.clubs.find((item) => item.id === club.id)
    if (publicClub) publicClub.memberCount += 1
  }
  for (const application of mockDb.applications.filter(
    (item) => item.clubId === club.id && item.userId === candidate.id && item.status === 'pending'
  )) {
    application.status = 'approved'
    application.reviewedAt = new Date().toISOString()
    mockDb.notifications.push({
      id: `n-${crypto.randomUUID()}`,
      userId: candidate.id,
      type: 'application',
      title: '入社申请审核结果',
      content: `你已被任命为${club.name}社长，入社申请已通过`,
      link: '/profile',
      read: false,
      createdAt: new Date().toISOString()
    })
  }
  return clubData(club.id)
})
