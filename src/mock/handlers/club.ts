import { CLUB_CATEGORIES } from '@/utils/constants'
import type { ClubApplication, ClubDetail, ReviewApplicationPayload } from '@/types/club'

import { mockDb } from '../db'
import {
  MockError,
  mockRoute,
  paginate,
  readString,
  requireClubOwner,
  requireRole
} from '../registry'

/** 组装社团详情 */
function buildClubDetail(clubId: string): ClubDetail {
  const club = mockDb.clubs.find((item) => item.id === clubId)
  if (!club) {
    throw new MockError(1404, '社团不存在')
  }
  return {
    ...club,
    introduction: club.introduction ?? club.description,
    notices: mockDb.notices
      .filter((item) => item.clubId === clubId)
      .map((item) => ({
        id: item.id,
        title: item.title,
        content: item.content,
        publishedAt: item.publishedAt
      })),
    recentActivities: mockDb.activities
      .filter((item) => item.clubId === clubId && item.status === 'published')
      .slice(0, 3)
  }
}

mockRoute('GET', '/api/clubs', (ctx) => {
  const keyword = readString(ctx.params, 'keyword').toLowerCase()
  const category = readString(ctx.params, 'category')
  const filtered = mockDb.clubs.filter((club) => {
    const hitKeyword =
      !keyword ||
      club.name.toLowerCase().includes(keyword) ||
      club.description.toLowerCase().includes(keyword) ||
      club.tags.some((tag) => tag.toLowerCase().includes(keyword))
    const hitCategory = !category || category === '全部类型' || club.category === category
    return hitKeyword && hitCategory
  })
  return paginate(filtered, ctx.params.page, ctx.params.pageSize)
})

mockRoute('GET', '/api/clubs/categories', () => [...CLUB_CATEGORIES])

mockRoute('GET', '/api/clubs/recommended', () => mockDb.clubs.slice(0, 4))

mockRoute('GET', '/api/clubs/:id', (ctx) => buildClubDetail(ctx.pathParams.id))

mockRoute('PUT', '/api/clubs/:id', (ctx) => {
  const clubId = ctx.pathParams.id
  requireClubOwner(ctx, clubId)
  const club = mockDb.clubs.find((item) => item.id === clubId)
  if (!club) {
    throw new MockError(1404, '社团不存在')
  }
  const name = readString(ctx.data, 'name')
  const description = readString(ctx.data, 'description')
  const introduction = readString(ctx.data, 'introduction')
  const logo = readString(ctx.data, 'logo')
  if (name) club.name = name
  if (description) club.description = description
  if (introduction) club.introduction = introduction
  if (logo) club.logo = logo
  if (Array.isArray(ctx.data.tags)) {
    club.tags = (ctx.data.tags as unknown[]).filter((tag): tag is string => typeof tag === 'string')
  }
  return buildClubDetail(clubId)
})

mockRoute('POST', '/api/clubs/:id/applications', (ctx) => {
  const user = requireRole(ctx, ['student'])
  const clubId = ctx.pathParams.id
  const club = mockDb.clubs.find((item) => item.id === clubId)
  if (!club) {
    throw new MockError(1404, '社团不存在')
  }
  const duplicated = mockDb.applications.some(
    (item) =>
      item.clubId === clubId && item.applicantName === user.name && item.status === 'pending'
  )
  if (duplicated) {
    throw new MockError(1409, '你已提交过该社团的入社申请，请等待审核')
  }
  const application: ClubApplication = {
    id: `ap-${Date.now()}`,
    clubId,
    clubName: club.name,
    applicantName: user.name,
    message: readString(ctx.data, 'message'),
    status: 'pending',
    createdAt: new Date().toISOString()
  }
  mockDb.applications.push(application)
  return application
})

mockRoute('GET', '/api/clubs/:id/applications', (ctx) => {
  const clubId = ctx.pathParams.id
  requireClubOwner(ctx, clubId)
  const status = readString(ctx.params, 'status')
  const list = mockDb.applications.filter(
    (item) => item.clubId === clubId && (!status || item.status === status)
  )
  return paginate(list, ctx.params.page, ctx.params.pageSize)
})

mockRoute('PUT', '/api/clubs/:id/applications/:appId', (ctx) => {
  const clubId = ctx.pathParams.id
  requireClubOwner(ctx, clubId)
  const application = mockDb.applications.find((item) => item.id === ctx.pathParams.appId)
  if (!application) {
    throw new MockError(1404, '申请不存在')
  }
  if (application.status !== 'pending') {
    throw new MockError(1410, '该申请已处理，不能重复审核')
  }
  const action = readString(ctx.data, 'action') as ReviewApplicationPayload['action']
  if (action !== 'approve' && action !== 'reject') {
    throw new MockError(1003, 'action 只能为 approve 或 reject')
  }
  application.status = action === 'approve' ? 'approved' : 'rejected'
  application.reviewedAt = new Date().toISOString()
  return application
})

mockRoute('GET', '/api/clubs/:id/members', (ctx) => {
  const clubId = ctx.pathParams.id
  requireClubOwner(ctx, clubId)
  return mockDb.members.filter((item) => item.clubId === clubId)
})

mockRoute('PUT', '/api/clubs/:id/members/:memberId', (ctx) => {
  const clubId = ctx.pathParams.id
  requireClubOwner(ctx, clubId)
  const index = mockDb.members.findIndex((item) => item.id === ctx.pathParams.memberId)
  if (index === -1) {
    throw new MockError(1404, '成员不存在')
  }
  const action = readString(ctx.data, 'action')
  if (action === 'remove') {
    const [removed] = mockDb.members.splice(index, 1)
    return removed
  }
  const role = readString(ctx.data, 'role')
  if (role === 'member' || role === 'officer') {
    mockDb.members[index].role = role
  }
  return mockDb.members[index]
})

mockRoute('POST', '/api/clubs/:id/recruitments', (ctx) => {
  const clubId = ctx.pathParams.id
  requireClubOwner(ctx, clubId)
  const title = readString(ctx.data, 'title')
  if (!title) {
    throw new MockError(1003, '招新帖标题不能为空')
  }
  const post = {
    id: `rc-${Date.now()}`,
    clubId,
    title,
    content: readString(ctx.data, 'content'),
    deadline: readString(ctx.data, 'deadline'),
    createdAt: new Date().toISOString()
  }
  mockDb.recruitments.push(post)
  return post
})
