import { defineStore } from 'pinia'
import { computed, ref } from 'vue'

import * as authApi from '@/api/auth'
import * as userApi from '@/api/user'
import type { LoginPayload, RegisterPayload, UserInfo } from '@/types/user'
import { clearToken, getToken, setToken } from '@/utils/storage'

/** 登录态与用户信息 store */
export const useUserStore = defineStore('user', () => {
  const token = ref(getToken())
  const userInfo = ref<UserInfo | null>(null)

  const isLoggedIn = computed(() => Boolean(token.value))
  const role = computed(() => userInfo.value?.role ?? null)

  function reset(): void {
    token.value = ''
    userInfo.value = null
    clearToken()
  }

  async function login(payload: LoginPayload): Promise<UserInfo> {
    const result = await authApi.login(payload)
    token.value = result.token
    setToken(result.token)
    userInfo.value = result.user
    return result.user
  }

  async function register(payload: RegisterPayload): Promise<UserInfo> {
    const result = await authApi.register(payload)
    token.value = result.token
    setToken(result.token)
    userInfo.value = result.user
    return result.user
  }

  async function logout(): Promise<void> {
    try {
      await authApi.logout()
    } catch {
      // 登出接口失败也要清理本地登录态
    }
    reset()
  }

  /** 拉取当前登录用户资料；token 失效时自动清理登录态 */
  async function fetchProfile(): Promise<void> {
    if (!token.value) {
      return
    }
    try {
      userInfo.value = await userApi.getProfile()
    } catch {
      reset()
    }
  }

  return { token, userInfo, isLoggedIn, role, login, register, logout, reset, fetchProfile }
})
