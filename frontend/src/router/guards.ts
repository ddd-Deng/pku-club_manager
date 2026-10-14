import { ElMessage } from 'element-plus'
import type { Router } from 'vue-router'

import { setUnauthorizedHandler } from '@/api/request'
import { useUserStore } from '@/stores/user'

/** 注册全局路由守卫：登录守卫 + 角色守卫 + 标题 */
export function setupRouterGuards(router: Router): void {
  router.beforeEach(async (to) => {
    const userStore = useUserStore()

    // 有 token 但尚未拉取用户信息时先补齐（刷新页面场景）
    if (userStore.isLoggedIn && !userStore.userInfo) {
      await userStore.fetchProfile()
    }

    if (to.meta.publicOnly && userStore.isLoggedIn) {
      return { path: '/' }
    }

    if (to.meta.requiresAuth && !userStore.isLoggedIn) {
      return { path: '/login', query: { redirect: to.fullPath } }
    }

    const roles = to.meta.roles
    if (roles && roles.length > 0 && (!userStore.role || !roles.includes(userStore.role))) {
      ElMessage.warning('当前角色无权访问该页面')
      return { path: '/' }
    }

    return true
  })

  router.afterEach((to) => {
    const appTitle = import.meta.env.VITE_APP_TITLE || '校园社团管理系统'
    document.title = to.meta.title ? `${to.meta.title} - ${appTitle}` : appTitle
  })

  // 请求层 401 时统一清理登录态并跳登录页
  setUnauthorizedHandler(() => {
    const userStore = useUserStore()
    userStore.reset()
    const current = router.currentRoute.value
    if (current.name !== 'login') {
      void router.push({ path: '/login', query: { redirect: current.fullPath } })
    }
  })
}
