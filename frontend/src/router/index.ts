import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'

import type { Role } from '@/types/common'

import AdminLayout from '@/layouts/AdminLayout.vue'
import FrontLayout from '@/layouts/FrontLayout.vue'

declare module 'vue-router' {
  interface RouteMeta {
    /** 页面标题，用于 document.title */
    title?: string
    /** 需要登录 */
    requiresAuth?: boolean
    /** 仅未登录可访问（登录页） */
    publicOnly?: boolean
    /** 允许访问的角色 */
    roles?: Role[]
  }
}

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    component: FrontLayout,
    children: [
      {
        path: '',
        name: 'home',
        component: () => import('@/views/home/HomeView.vue'),
        meta: { title: '系统首页' }
      },
      {
        path: 'login',
        name: 'login',
        component: () => import('@/views/auth/LoginView.vue'),
        meta: { title: '登录与注册', publicOnly: true }
      },
      {
        path: 'clubs',
        name: 'club-plaza',
        component: () => import('@/views/club/ClubPlazaView.vue'),
        meta: { title: '社团广场' }
      },
      {
        path: 'clubs/:id',
        name: 'club-detail',
        component: () => import('@/views/club/ClubDetailView.vue'),
        meta: { title: '社团详情' }
      },
      {
        path: 'activities/:id',
        name: 'activity-detail',
        component: () => import('@/views/activity/ActivityDetailView.vue'),
        meta: { title: '活动详情' }
      },
      {
        path: 'profile',
        name: 'profile',
        component: () => import('@/views/profile/ProfileView.vue'),
        meta: { title: '个人中心', requiresAuth: true }
      },
      {
        path: 'notifications',
        name: 'notification',
        component: () => import('@/views/notification/NotificationView.vue'),
        meta: { title: '消息与通知', requiresAuth: true }
      },
      {
        path: 'ai',
        name: 'ai-qa',
        component: () => import('@/views/ai/AiQaView.vue'),
        meta: { title: 'AI 知识库问答', requiresAuth: true }
      },
      {
        path: 'search',
        name: 'search',
        component: () => import('@/views/search/SearchResultView.vue'),
        meta: { title: '搜索结果' }
      },
      {
        path: 'test/hello',
        name: 'test-hello',
        component: () => import('@/views/test/HelloView.vue'),
        meta: { title: '接口连通性测试' }
      }
    ]
  },
  {
    path: '/admin',
    component: AdminLayout,
    meta: { requiresAuth: true, roles: ['clubAdmin', 'admin'] },
    children: [
      {
        path: '',
        name: 'admin',
        component: () => import('@/views/admin/AdminConsoleView.vue'),
        meta: { title: '社团管理后台', requiresAuth: true, roles: ['clubAdmin', 'admin'] }
      }
    ]
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'not-found',
    component: () => import('@/views/error/NotFoundView.vue'),
    meta: { title: '页面不存在' }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior: () => ({ top: 0 })
})

export default router
