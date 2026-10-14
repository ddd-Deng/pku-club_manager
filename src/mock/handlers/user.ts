import type { ActivityRegistrationRecord, FootprintItem } from '@/types/user'

import { mockDb } from '../db'
import { MockError, mockRoute, readString, requireAuth } from '../registry'
import { toPublicUser } from './auth'

mockRoute('GET', '/api/user/profile', (ctx) => toPublicUser(requireAuth(ctx)))

mockRoute('PUT', '/api/user/profile', (ctx) => {
  const user = requireAuth(ctx)
  const name = readString(ctx.data, 'name')
  const email = readString(ctx.data, 'email')
  const avatar = readString(ctx.data, 'avatar')
  if (name) user.name = name
  if (email) user.email = email
  if (avatar) user.avatar = avatar
  return toPublicUser(user)
})

mockRoute('PUT', '/api/user/password', (ctx) => {
  const user = requireAuth(ctx)
  const oldPassword = readString(ctx.data, 'oldPassword')
  const newPassword = readString(ctx.data, 'newPassword')
  if (user.password !== oldPassword) {
    throw new MockError(1005, '原密码不正确')
  }
  if (!newPassword) {
    throw new MockError(1003, '新密码不能为空')
  }
  user.password = newPassword
  return null
})

mockRoute('GET', '/api/user/footprints', (ctx) => {
  requireAuth(ctx)
  const footprints: FootprintItem[] = mockDb.activities
    .filter((item) => item.status === 'finished')
    .map((item) => ({
      id: `fp-${item.id}`,
      activityId: item.id,
      title: item.title,
      clubName: item.clubName,
      finishedAt: item.endTime
    }))
  return footprints
})

mockRoute('GET', '/api/user/applications', (ctx) => {
  const user = requireAuth(ctx)
  return mockDb.applications.filter((item) => item.applicantName === user.name)
})

mockRoute('GET', '/api/user/activity-registrations', (ctx) => {
  const user = requireAuth(ctx)
  const records: ActivityRegistrationRecord[] = mockDb.registrations
    .filter((item) => item.userId === user.id)
    .map((item) => {
      const activity = mockDb.activities.find((act) => act.id === item.activityId)
      return {
        id: item.id,
        activityId: item.activityId,
        title: activity?.title ?? '已删除的活动',
        clubName: activity?.clubName ?? '-',
        startTime: activity?.startTime ?? '',
        status: item.status,
        createdAt: item.createdAt
      }
    })
  return records
})
