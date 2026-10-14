import type { Activity, ActivityRegistration } from '@/types/activity'

import { mockDb } from '../db'
import {
  MockError,
  mockRoute,
  paginate,
  readNumber,
  readString,
  requireAuth,
  requireClubOwner,
  requireRole
} from '../registry'

function findActivity(id: string): Activity {
  const activity = mockDb.activities.find((item) => item.id === id)
  if (!activity) {
    throw new MockError(1404, '活动不存在')
  }
  return activity
}

mockRoute('GET', '/api/activities', (ctx) => {
  const keyword = readString(ctx.params, 'keyword').toLowerCase()
  const clubId = readString(ctx.params, 'clubId')
  const category = readString(ctx.params, 'category')
  const startDate = readString(ctx.params, 'startDate')
  const endDate = readString(ctx.params, 'endDate')
  const status = readString(ctx.params, 'status')
  const list = mockDb.activities
    .filter((item) => {
      if (status) {
        if (item.status !== status) return false
      } else if (item.status !== 'published' && item.status !== 'finished') {
        return false
      }
      if (clubId && item.clubId !== clubId) return false
      if (category && category !== '全部类型') {
        const club = mockDb.clubs.find((entry) => entry.id === item.clubId)
        if (!club || club.category !== category) return false
      }
      if (
        keyword &&
        !item.title.toLowerCase().includes(keyword) &&
        !item.description.toLowerCase().includes(keyword)
      ) {
        return false
      }
      const day = item.startTime.slice(0, 10)
      if (startDate && day < startDate) return false
      if (endDate && day > endDate) return false
      return true
    })
    .sort((a, b) => a.startTime.localeCompare(b.startTime))
  return paginate(list, ctx.params.page, ctx.params.pageSize)
})

mockRoute('GET', '/api/activities/upcoming', () => {
  const now = new Date().toISOString()
  return mockDb.activities
    .filter((item) => item.status === 'published' && item.startTime >= now)
    .sort((a, b) => a.startTime.localeCompare(b.startTime))
    .slice(0, 5)
})

mockRoute('GET', '/api/activities/:id', (ctx) => findActivity(ctx.pathParams.id))

mockRoute('POST', '/api/activities', (ctx) => {
  const user = requireRole(ctx, ['clubAdmin', 'admin'])
  const clubId =
    user.role === 'admin' ? readString(ctx.data, 'clubId') || 'c-1' : (user.clubId ?? '')
  const club = mockDb.clubs.find((item) => item.id === clubId)
  const title = readString(ctx.data, 'title')
  if (!title) {
    throw new MockError(1003, '活动标题不能为空')
  }
  const activity: Activity = {
    id: `a-${Date.now()}`,
    clubId,
    clubName: club?.name ?? '-',
    title,
    cover: readString(ctx.data, 'cover') || '🎯',
    description: readString(ctx.data, 'description'),
    location: readString(ctx.data, 'location'),
    startTime: readString(ctx.data, 'startTime'),
    endTime: readString(ctx.data, 'endTime'),
    status: 'draft',
    capacity: readNumber(ctx.data, 'capacity', 50),
    registeredCount: 0,
    type: readString(ctx.data, 'type') || '讲座'
  }
  mockDb.activities.push(activity)
  return activity
})

mockRoute('PUT', '/api/activities/:id', (ctx) => {
  const activity = findActivity(ctx.pathParams.id)
  requireClubOwner(ctx, activity.clubId)
  const title = readString(ctx.data, 'title')
  const description = readString(ctx.data, 'description')
  const location = readString(ctx.data, 'location')
  const startTime = readString(ctx.data, 'startTime')
  const endTime = readString(ctx.data, 'endTime')
  const type = readString(ctx.data, 'type')
  if (title) activity.title = title
  if (description) activity.description = description
  if (location) activity.location = location
  if (startTime) activity.startTime = startTime
  if (endTime) activity.endTime = endTime
  if (type) activity.type = type
  if (ctx.data.capacity !== undefined) {
    activity.capacity = readNumber(ctx.data, 'capacity', activity.capacity)
  }
  return activity
})

mockRoute('POST', '/api/activities/:id/publish', (ctx) => {
  const activity = findActivity(ctx.pathParams.id)
  requireClubOwner(ctx, activity.clubId)
  activity.status = 'published'
  return activity
})

mockRoute('POST', '/api/activities/:id/unpublish', (ctx) => {
  const activity = findActivity(ctx.pathParams.id)
  requireClubOwner(ctx, activity.clubId)
  activity.status = 'unpublished'
  return activity
})

mockRoute('DELETE', '/api/activities/:id', (ctx) => {
  const activity = findActivity(ctx.pathParams.id)
  requireClubOwner(ctx, activity.clubId)
  const index = mockDb.activities.findIndex((item) => item.id === activity.id)
  mockDb.activities.splice(index, 1)
  return null
})

mockRoute('POST', '/api/activities/:id/registrations', (ctx) => {
  const user = requireRole(ctx, ['student'])
  const activity = findActivity(ctx.pathParams.id)
  if (activity.status !== 'published') {
    throw new MockError(1412, '活动未发布，暂不能报名')
  }
  if (activity.registeredCount >= activity.capacity) {
    throw new MockError(1411, '报名人数已满')
  }
  const existed = mockDb.registrations.some(
    (item) =>
      item.activityId === activity.id && item.userId === user.id && item.status === 'registered'
  )
  if (existed) {
    throw new MockError(1409, '你已报名该活动')
  }
  const registration: ActivityRegistration = {
    id: `rg-${Date.now()}`,
    activityId: activity.id,
    userId: user.id,
    userName: user.name,
    status: 'registered',
    createdAt: new Date().toISOString()
  }
  mockDb.registrations.push(registration)
  activity.registeredCount += 1
  return registration
})

mockRoute('DELETE', '/api/activities/:id/registrations', (ctx) => {
  const user = requireAuth(ctx)
  const activity = findActivity(ctx.pathParams.id)
  const registration = mockDb.registrations.find(
    (item) =>
      item.activityId === activity.id && item.userId === user.id && item.status === 'registered'
  )
  if (!registration) {
    throw new MockError(1404, '未找到你的报名记录')
  }
  registration.status = 'cancelled'
  activity.registeredCount = Math.max(0, activity.registeredCount - 1)
  return null
})
