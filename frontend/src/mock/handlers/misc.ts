import type { AiChatResult, KbDocument } from '@/types/ai'
import type { HelloResult } from '@/types/common'
import type { SearchHit } from '@/types/search'
import type { VenueReservation } from '@/types/venue'

import { mockDb } from '../db'
import {
  MockError,
  mockRoute,
  paginate,
  readString,
  requireAuth,
  requireClubOwner,
  requireRole
} from '../registry'
import { SEARCH_HISTORY_STORAGE_KEY } from '@/utils/constants'

/** 将搜索历史同步写入 localStorage */
function saveSearchHistory(): void {
  localStorage.setItem(SEARCH_HISTORY_STORAGE_KEY, JSON.stringify(mockDb.searchHistory))
}

/* ---------------- 连通性测试 ---------------- */

mockRoute('GET', '/api/test/hello', (): HelloResult => {
  return {
    message: 'hello world',
    source: 'mock',
    serverTime: new Date().toISOString()
  }
})

/* ---------------- 消息与通知 ---------------- */

mockRoute('GET', '/api/notifications', (ctx) => {
  requireAuth(ctx)
  const type = readString(ctx.params, 'type')
  const readParam = ctx.params.read
  const list = mockDb.notifications
    .filter((item) => {
      if (type && item.type !== type) return false
      if (typeof readParam === 'string') {
        return item.read === (readParam === 'true')
      }
      return true
    })
    .sort((a, b) => b.createdAt.localeCompare(a.createdAt))
  return paginate(list, ctx.params.page, ctx.params.pageSize)
})

mockRoute('GET', '/api/notifications/unread-count', (ctx) => {
  requireAuth(ctx)
  return mockDb.notifications.filter((item) => !item.read).length
})

mockRoute('PUT', '/api/notifications/:id/read', (ctx) => {
  requireAuth(ctx)
  const notification = mockDb.notifications.find((item) => item.id === ctx.pathParams.id)
  if (!notification) {
    throw new MockError(1404, '通知不存在')
  }
  notification.read = true
  return notification
})

mockRoute('PUT', '/api/notifications/read-all', (ctx) => {
  requireAuth(ctx)
  let updated = 0
  mockDb.notifications.forEach((item) => {
    if (!item.read) {
      item.read = true
      updated += 1
    }
  })
  return { updated }
})

/* ---------------- 场地与物资预约 ---------------- */

mockRoute('GET', '/api/venues', () => mockDb.venues)

mockRoute('POST', '/api/venue-reservations', (ctx) => {
  const user = requireRole(ctx, ['clubAdmin', 'admin'])
  const venue = mockDb.venues.find((item) => item.id === readString(ctx.data, 'venueId'))
  if (!venue) {
    throw new MockError(1404, '场地不存在')
  }
  const date = readString(ctx.data, 'date')
  const timeSlot = readString(ctx.data, 'timeSlot')
  const slot = venue.slots.find((item) => item.date === date && item.timeSlot === timeSlot)
  if (!slot) {
    throw new MockError(1413, '该时段不存在')
  }
  if (!slot.available) {
    throw new MockError(1414, '该时段已被预约')
  }
  slot.available = false
  const reservation: VenueReservation = {
    id: `vr-${Date.now()}`,
    venueId: venue.id,
    venueName: venue.name,
    clubId: user.clubId ?? '-',
    clubName: user.clubName ?? '-',
    date,
    timeSlot,
    purpose: readString(ctx.data, 'purpose'),
    items: Array.isArray(ctx.data.items)
      ? (ctx.data.items as unknown[]).filter((item): item is string => typeof item === 'string')
      : [],
    status: 'pending',
    createdAt: new Date().toISOString()
  }
  mockDb.reservations.push(reservation)
  return reservation
})

mockRoute('GET', '/api/venue-reservations', (ctx) => {
  const user = requireRole(ctx, ['clubAdmin', 'admin'])
  const status = readString(ctx.params, 'status')
  const list = mockDb.reservations.filter((item) => {
    if (user.role === 'clubAdmin' && item.clubId !== user.clubId) return false
    if (status && item.status !== status) return false
    return true
  })
  return paginate(list, ctx.params.page, ctx.params.pageSize)
})

mockRoute('PUT', '/api/venue-reservations/:id', (ctx) => {
  requireRole(ctx, ['admin'])
  const reservation = mockDb.reservations.find((item) => item.id === ctx.pathParams.id)
  if (!reservation) {
    throw new MockError(1404, '预约单不存在')
  }
  if (reservation.status !== 'pending') {
    throw new MockError(1410, '该预约单已审批')
  }
  const action = readString(ctx.data, 'action')
  if (action !== 'approve' && action !== 'reject') {
    throw new MockError(1003, 'action 只能为 approve 或 reject')
  }
  reservation.status = action === 'approve' ? 'approved' : 'rejected'
  return reservation
})

/* ---------------- 知识库与 AI 问答 ---------------- */

mockRoute('POST', '/api/kb/documents', (ctx) => {
  const user = requireRole(ctx, ['clubAdmin', 'admin'])
  const title = readString(ctx.data, 'title')
  if (!title) {
    throw new MockError(1003, '文档名称不能为空')
  }
  const document: KbDocument = {
    id: `kb-${Date.now()}`,
    clubId: user.clubId ?? '-',
    clubName: user.clubName ?? '-',
    title,
    size: Number(ctx.data.size) || 0,
    uploadedBy: user.name,
    uploadedAt: new Date().toISOString()
  }
  mockDb.kbDocuments.push(document)
  return document
})

mockRoute('GET', '/api/kb/documents', (ctx) => {
  requireAuth(ctx)
  const clubId = readString(ctx.params, 'clubId')
  const list = mockDb.kbDocuments.filter((item) => !clubId || item.clubId === clubId)
  return paginate(list, ctx.params.page, ctx.params.pageSize)
})

mockRoute('DELETE', '/api/kb/documents/:id', (ctx) => {
  const index = mockDb.kbDocuments.findIndex((item) => item.id === ctx.pathParams.id)
  if (index === -1) {
    throw new MockError(1404, '文档不存在')
  }
  requireClubOwner(ctx, mockDb.kbDocuments[index].clubId)
  mockDb.kbDocuments.splice(index, 1)
  return null
})

mockRoute('POST', '/api/ai/chat', (ctx): AiChatResult => {
  requireAuth(ctx)
  const question = readString(ctx.data, 'question')
  if (!question) {
    throw new MockError(1003, '问题不能为空')
  }
  const references = mockDb.kbDocuments.slice(0, 2).map((item) => ({
    docId: item.id,
    title: item.title
  }))
  return {
    answer: `【mock 回答】根据社团知识库检索结果，与"${question}"相关的信息如下：社团章程规定例会每周举行一次，器材借用需提前一天在管理后台提交预约。（正式环境由后端 RAG 服务返回真实答案）`,
    references
  }
})

mockRoute('GET', '/api/ai/documents/search', (ctx) => {
  requireAuth(ctx)
  const keyword = readString(ctx.params, 'keyword').toLowerCase()
  return mockDb.kbDocuments.filter((item) => !keyword || item.title.toLowerCase().includes(keyword))
})

/* ---------------- 搜索与历史 ---------------- */

mockRoute('GET', '/api/search', (ctx) => {
  const keyword = readString(ctx.params, 'keyword').toLowerCase()
  if (!keyword) {
    throw new MockError(1003, '请输入搜索关键词')
  }
  const type = readString(ctx.params, 'type')
  const category = readString(ctx.params, 'category')
  const activityType = readString(ctx.params, 'activityType')
  const startDate = readString(ctx.params, 'startDate')
  const endDate = readString(ctx.params, 'endDate')

  const hits: SearchHit[] = []
  if (type !== 'activity') {
    mockDb.clubs
      .filter((club) => {
        const hitKeyword =
          club.name.toLowerCase().includes(keyword) ||
          club.description.toLowerCase().includes(keyword) ||
          club.tags.some((tag) => tag.toLowerCase().includes(keyword))
        const hitCategory = !category || category === '全部类型' || club.category === category
        return hitKeyword && hitCategory
      })
      .forEach((club) => {
        hits.push({ type: 'club', id: club.id, title: club.name, subtitle: club.description })
      })
  }
  if (type !== 'club') {
    mockDb.activities
      .filter((activity) => {
        if (activity.status !== 'published' && activity.status !== 'finished') return false
        const hitKeyword =
          activity.title.toLowerCase().includes(keyword) ||
          activity.description.toLowerCase().includes(keyword)
        const hitType = !activityType || activity.type === activityType
        const day = activity.startTime.slice(0, 10)
        const hitDate = (!startDate || day >= startDate) && (!endDate || day <= endDate)
        return hitKeyword && hitType && hitDate
      })
      .forEach((activity) => {
        hits.push({
          type: 'activity',
          id: activity.id,
          title: activity.title,
          subtitle: `${activity.clubName} · ${activity.type}`
        })
      })
  }

  // 记录搜索历史（去重，保留最近一次时间）
  const rawKeyword = readString(ctx.params, 'keyword')
  const existed = mockDb.searchHistory.find((item) => item.keyword === rawKeyword)
  if (existed) {
    existed.searchedAt = new Date().toISOString()
  } else {
    mockDb.searchHistory.unshift({
      id: `sh-${Date.now()}`,
      keyword: rawKeyword,
      searchedAt: new Date().toISOString()
    })
  }
  saveSearchHistory()
  return paginate(hits, ctx.params.page, ctx.params.pageSize)
})

mockRoute('GET', '/api/search/history', (ctx) => {
  requireAuth(ctx)
  return [...mockDb.searchHistory].sort((a, b) => b.searchedAt.localeCompare(a.searchedAt))
})

mockRoute('DELETE', '/api/search/history/:id', (ctx) => {
  requireAuth(ctx)
  const index = mockDb.searchHistory.findIndex((item) => item.id === ctx.pathParams.id)
  if (index === -1) {
    throw new MockError(1404, '历史记录不存在')
  }
  mockDb.searchHistory.splice(index, 1)
  saveSearchHistory()
  return null
})

mockRoute('DELETE', '/api/search/history', (ctx) => {
  requireAuth(ctx)
  mockDb.searchHistory = []
  saveSearchHistory()
  return null
})
