import type { Activity, ActivityRegistration } from '@/types/activity'
import type { KbDocument } from '@/types/ai'
import type { Club, ClubApplication, ClubMember, ClubNotice, RecruitmentPost } from '@/types/club'
import type { NotificationItem } from '@/types/notification'
import type { SearchHistoryItem } from '@/types/search'
import type { UserInfo } from '@/types/user'
import type { Venue, VenueReservation } from '@/types/venue'

import { SEARCH_HISTORY_STORAGE_KEY } from '@/utils/constants'

/** mock 用户 = 登录用户 + 凭据 */
export interface MockUser extends UserInfo {
  token: string
  password: string
}

/** 生成相对当前时间偏移 n 天的 ISO 时间 */
function iso(daysFromNow: number, hour = 9, minute = 0): string {
  const date = new Date()
  date.setDate(date.getDate() + daysFromNow)
  date.setHours(hour, minute, 0, 0)
  return date.toISOString()
}

/** 演示账号：登录页一键填充用 */
export const DEMO_ACCOUNTS = [
  { role: 'student', label: '学生', account: '2024001', password: '123456' },
  { role: 'clubAdmin', label: '社长', account: '2021002', password: '123456' },
  { role: 'admin', label: '管理员', account: 'admin', password: '123456' }
] as const

export const mockDb = {
  users: [
    {
      id: 'u-student',
      name: '林晓',
      studentNo: '2024001',
      email: 'linxiao@campus.edu.cn',
      role: 'student',
      avatar: '🧑‍',
      token: 'mock-token-student',
      password: '123456'
    },
    {
      id: 'u-club',
      name: '陈光影',
      studentNo: '2021002',
      email: 'chensy@campus.edu.cn',
      role: 'clubAdmin',
      avatar: '📷',
      clubId: 'c-1',
      clubName: '摄影社',
      token: 'mock-token-club',
      password: '123456'
    },
    {
      id: 'u-admin',
      name: '系统管理员',
      studentNo: 'admin',
      email: 'admin@campus.edu.cn',
      role: 'admin',
      avatar: '🛡️',
      token: 'mock-token-admin',
      password: '123456'
    }
  ] as MockUser[],

  clubs: [
    {
      id: 'c-1',
      name: '摄影社',
      category: '文化艺术',
      logo: '📷',
      description: '用镜头记录校园瞬间，定期组织摄影培训与作品展览。',
      memberCount: 128,
      foundedAt: '2015-09-01',
      tags: ['摄影', '校园纪实', '户外活动']
    },
    {
      id: 'c-2',
      name: '街舞社',
      category: '文化艺术',
      logo: '🕺',
      description: '汇聚全校街舞爱好者，涵盖 Breaking、Hip-hop、Jazz 等舞种。',
      memberCount: 96,
      foundedAt: '2016-03-01',
      tags: ['街舞', '演出']
    },
    {
      id: 'c-3',
      name: '辩论社',
      category: '学术科技',
      logo: '🎙️',
      description: '以辩会友，锻炼思辨表达，常年征战校际辩论联赛。',
      memberCount: 84,
      foundedAt: '2012-10-01',
      tags: ['辩论', '思辨']
    },
    {
      id: 'c-4',
      name: '爱心社',
      category: '志愿服务',
      logo: '❤️',
      description: '组织敬老院关怀、支教助学等公益活动，传递校园温度。',
      memberCount: 152,
      foundedAt: '2010-05-01',
      tags: ['公益', '志愿']
    },
    {
      id: 'c-5',
      name: '无人机社',
      category: '学术科技',
      logo: '🛸',
      description: '研究无人机飞行与航拍技术，承接校园航拍项目。',
      memberCount: 66,
      foundedAt: '2019-09-01',
      tags: ['无人机', '航拍']
    },
    {
      id: 'c-6',
      name: '文学社',
      category: '文化艺术',
      logo: '📚',
      description: '创办校园刊物，举办读书会与征文比赛，滋养校园文学生态。',
      memberCount: 73,
      foundedAt: '2008-04-01',
      tags: ['文学', '刊物']
    },
    {
      id: 'c-7',
      name: '篮球社',
      category: '体育竞技',
      logo: '🏀',
      description: '组织院系联赛与日常训练，欢迎各水平同学加入。',
      memberCount: 110,
      foundedAt: '2011-09-01',
      tags: ['篮球', '联赛']
    },
    {
      id: 'c-8',
      name: '青年志愿者协会',
      category: '志愿服务',
      logo: '🤝',
      description: '统筹全校志愿服务项目，累计服务时长超两万小时。',
      memberCount: 208,
      foundedAt: '2009-03-01',
      tags: ['志愿', '社区服务']
    }
  ] as Club[],

  notices: [
    {
      id: 'n-1',
      clubId: 'c-1',
      title: '秋季招新截止提醒',
      content: '本学期招新将于两周后截止，请有意向的同学尽快提交入社申请。',
      publishedAt: iso(-2)
    },
    {
      id: 'n-2',
      clubId: 'c-1',
      title: '每周三晚例会',
      content: '每周三 19:00 在大学生活动中心 305 举行例会与评片会。',
      publishedAt: iso(-6)
    },
    {
      id: 'n-3',
      clubId: 'c-3',
      title: '新生辩论赛报名开启',
      content: '以四人队伍为单位报名，赛程与赛制详见活动页。',
      publishedAt: iso(-1)
    }
  ] as (ClubNotice & { clubId: string })[],

  activities: [
    {
      id: 'a-1',
      clubId: 'c-1',
      clubName: '摄影社',
      title: '秋日校园摄影大赛',
      cover: '🍂',
      description: '以"秋日校园"为主题征集摄影作品，设最佳构图、最佳人气奖。',
      location: '大学生活动中心展厅',
      startTime: iso(7, 14),
      endTime: iso(7, 17),
      status: 'published',
      capacity: 80,
      registeredCount: 46,
      type: '比赛'
    },
    {
      id: 'a-2',
      clubId: 'c-1',
      clubName: '摄影社',
      title: '新生人像拍摄活动',
      cover: '📸',
      description: '为新生免费拍摄校园写真，含后期修图教学环节。',
      location: '樱花大道',
      startTime: iso(3, 9),
      endTime: iso(3, 12),
      status: 'published',
      capacity: 40,
      registeredCount: 38,
      type: '实践'
    },
    {
      id: 'a-3',
      clubId: 'c-2',
      clubName: '街舞社',
      title: '校园街舞之夜',
      cover: '🎤',
      description: '年度公演，联合校内五大舞团同台演出。',
      location: '体育馆主馆',
      startTime: iso(10, 19),
      endTime: iso(10, 21),
      status: 'published',
      capacity: 500,
      registeredCount: 322,
      type: '演出'
    },
    {
      id: 'a-4',
      clubId: 'c-3',
      clubName: '辩论社',
      title: '新生辩论赛初赛',
      cover: '🗣️',
      description: '八强争夺战第一轮，辩题现场公布。',
      location: '文科楼 208',
      startTime: iso(5, 18),
      endTime: iso(5, 21),
      status: 'published',
      capacity: 60,
      registeredCount: 52,
      type: '比赛'
    },
    {
      id: 'a-5',
      clubId: 'c-4',
      clubName: '爱心社',
      title: '敬老院志愿服务',
      cover: '🧓',
      description: '前往校外敬老院开展陪伴与文艺表演服务。',
      location: '校外集合统一乘车',
      startTime: iso(12, 8),
      endTime: iso(12, 16),
      status: 'published',
      capacity: 30,
      registeredCount: 21,
      type: '志愿活动'
    },
    {
      id: 'a-6',
      clubId: 'c-5',
      clubName: '无人机社',
      title: '无人机航拍公开课',
      cover: '🛸',
      description: '零基础航拍入门，含真机演示与飞行安全规范讲解。',
      location: '工程训练中心',
      startTime: iso(15, 14),
      endTime: iso(15, 16),
      status: 'published',
      capacity: 50,
      registeredCount: 12,
      type: '讲座'
    },
    {
      id: 'a-7',
      clubId: 'c-6',
      clubName: '文学社',
      title: '秋季读书分享会',
      cover: '📖',
      description: '共读《乡土中国》，分享读书笔记与感悟。',
      location: '图书馆报告厅',
      startTime: iso(-10, 19),
      endTime: iso(-10, 21),
      status: 'finished',
      capacity: 45,
      registeredCount: 45,
      type: '讲座'
    },
    {
      id: 'a-8',
      clubId: 'c-7',
      clubName: '篮球社',
      title: '3v3 篮球争霸赛',
      cover: '🏀',
      description: '院系组队报名，冠军队伍代表学校参加市高校联赛。',
      location: '东区篮球场',
      startTime: iso(20, 13),
      endTime: iso(20, 18),
      status: 'published',
      capacity: 64,
      registeredCount: 40,
      type: '比赛'
    },
    {
      id: 'a-9',
      clubId: 'c-1',
      clubName: '摄影社',
      title: '社团招新宣讲会（草稿）',
      cover: '📝',
      description: '面向新生的社团宣讲与器材展示，时间待定。',
      location: '待定',
      startTime: iso(25, 19),
      endTime: iso(25, 20),
      status: 'draft',
      capacity: 100,
      registeredCount: 0,
      type: '讲座'
    }
  ] as Activity[],

  members: [
    { id: 'm-1', clubId: 'c-1', name: '陈光影', role: 'owner', joinedAt: iso(-400) },
    { id: 'm-2', clubId: 'c-1', name: '赵一帆', role: 'officer', joinedAt: iso(-300) },
    { id: 'm-3', clubId: 'c-1', name: '孙悦', role: 'member', joinedAt: iso(-120) },
    { id: 'm-4', clubId: 'c-1', name: '周子航', role: 'member', joinedAt: iso(-60) }
  ] as (ClubMember & { clubId: string })[],

  applications: [
    {
      id: 'ap-1',
      clubId: 'c-1',
      clubName: '摄影社',
      applicantName: '王小明',
      message: '热爱风光摄影，有自己的相机，希望加入学习后期。',
      status: 'pending',
      createdAt: iso(-1)
    },
    {
      id: 'ap-2',
      clubId: 'c-1',
      clubName: '摄影社',
      applicantName: '李婷婷',
      message: '喜欢人像摄影，参加过中学摄影兴趣小组。',
      status: 'pending',
      createdAt: iso(-3)
    },
    {
      id: 'ap-3',
      clubId: 'c-3',
      clubName: '辩论社',
      applicantName: '林晓',
      message: '想锻炼表达能力，希望加入辩论社。',
      status: 'pending',
      createdAt: iso(-2)
    }
  ] as ClubApplication[],

  registrations: [
    {
      id: 'rg-1',
      activityId: 'a-1',
      userId: 'u-student',
      userName: '林晓',
      status: 'registered',
      createdAt: iso(-1)
    }
  ] as ActivityRegistration[],

  notifications: [
    {
      id: 'nt-1',
      type: 'application',
      title: '入社申请待审核',
      content: '王小明 提交了摄影社入社申请，请及时处理。',
      read: false,
      createdAt: iso(-1),
      link: '/admin'
    },
    {
      id: 'nt-2',
      type: 'activity',
      title: '活动上新提醒',
      content: '你关注的摄影社发布了新活动「秋日校园摄影大赛」。',
      read: false,
      createdAt: iso(-2),
      link: '/activities/a-1'
    },
    {
      id: 'nt-3',
      type: 'venue',
      title: '场地预约审批反馈',
      content: '你提交的「大学生活动中心 305」预约已通过审批。',
      read: true,
      createdAt: iso(-4),
      link: '/admin'
    },
    {
      id: 'nt-4',
      type: 'application',
      title: '入社申请审核通知',
      content: '你提交的辩论社入社申请正在审核中。',
      read: true,
      createdAt: iso(-2),
      link: '/profile'
    }
  ] as NotificationItem[],

  venues: [
    {
      id: 'v-1',
      name: '大学生活动中心 305',
      location: '大学生活动中心三楼',
      slots: [
        { date: iso(1).slice(0, 10), timeSlot: '14:00-16:00', available: true },
        { date: iso(1).slice(0, 10), timeSlot: '19:00-21:00', available: false },
        { date: iso(2).slice(0, 10), timeSlot: '14:00-16:00', available: true }
      ]
    },
    {
      id: 'v-2',
      name: '体育馆副馆',
      location: '东区体育馆',
      slots: [
        { date: iso(1).slice(0, 10), timeSlot: '08:00-11:00', available: true },
        { date: iso(3).slice(0, 10), timeSlot: '19:00-21:00', available: true }
      ]
    }
  ] as Venue[],

  reservations: [
    {
      id: 'vr-1',
      venueId: 'v-1',
      venueName: '大学生活动中心 305',
      clubId: 'c-1',
      clubName: '摄影社',
      date: iso(4).slice(0, 10),
      timeSlot: '19:00-21:00',
      purpose: '摄影社例会与评片会',
      items: ['投影仪', '白板'],
      status: 'pending',
      createdAt: iso(-1)
    }
  ] as VenueReservation[],

  kbDocuments: [
    {
      id: 'kb-1',
      clubId: 'c-1',
      clubName: '摄影社',
      title: '摄影社章程.pdf',
      size: 245760,
      uploadedBy: '陈光影',
      uploadedAt: iso(-30)
    },
    {
      id: 'kb-2',
      clubId: 'c-1',
      clubName: '摄影社',
      title: '器材借用管理办法.docx',
      size: 88120,
      uploadedBy: '陈光影',
      uploadedAt: iso(-12)
    }
  ] as KbDocument[],

  recruitments: [
    {
      id: 'rc-1',
      clubId: 'c-1',
      title: '摄影社秋季招新帖',
      content: '招收热爱摄影的新成员，不限器材基础，提供培训。',
      deadline: iso(14).slice(0, 10),
      createdAt: iso(-5)
    }
  ] as RecruitmentPost[],

  searchHistory: loadSearchHistory()
}

/** 从 localStorage 加载搜索历史，没有则使用默认值 */
function loadSearchHistory(): SearchHistoryItem[] {
  const stored = localStorage.getItem(SEARCH_HISTORY_STORAGE_KEY)
  if (stored) {
    try {
      const parsed = JSON.parse(stored) as SearchHistoryItem[]
      if (Array.isArray(parsed)) {
        return parsed
      }
    } catch {
      // JSON 解析失败，回退到默认值
    }
  }
  return [
    { id: 'sh-1', keyword: '摄影', searchedAt: iso(-1) },
    { id: 'sh-2', keyword: '辩论赛', searchedAt: iso(-3) }
  ]
}
