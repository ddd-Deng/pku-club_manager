<script setup lang="ts">
import { Bell, Search } from '@element-plus/icons-vue'
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { getUnreadCount } from '@/api/notification'
import { useUserStore } from '@/stores/user'
import { ROLE_LABELS } from '@/utils/constants'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const unreadCount = ref(0)

const navItems = [
  { path: '/', label: '首页' },
  { path: '/clubs', label: '社团广场' },
  { path: '/ai', label: 'AI 问答' },
  { path: '/notifications', label: '消息' }
]

const activePath = computed(() => (route.path.startsWith('/clubs') ? '/clubs' : route.path))
const roleLabel = computed(() => (userStore.role ? ROLE_LABELS[userStore.role] : ''))

async function refreshUnread(): Promise<void> {
  if (!userStore.isLoggedIn) {
    unreadCount.value = 0
    return
  }
  try {
    unreadCount.value = await getUnreadCount()
  } catch {
    unreadCount.value = 0
  }
}

function goSearch(): void {
  void router.push('/search')
}

function goNotifications(): void {
  void router.push('/notifications')
}

function handleCommand(command: string): void {
  if (command === 'logout') {
    void handleLogout()
    return
  }
  void router.push(`/${command}`)
}

async function handleLogout(): Promise<void> {
  await userStore.logout()
  await refreshUnread()
  void router.push('/login')
}

onMounted(refreshUnread)
watch(() => userStore.isLoggedIn, refreshUnread)
</script>

<template>
  <div class="front-layout">
    <header class="front-navbar">
      <div class="front-navbar__inner">
        <router-link class="front-navbar__logo" to="/">
          <span class="front-navbar__logo-icon">🎓</span>
          <span>校园社团系统</span>
        </router-link>

        <nav class="front-navbar__nav">
          <router-link
            v-for="item in navItems"
            :key="item.path"
            :to="item.path"
            class="front-navbar__link"
            :class="{ 'is-active': activePath === item.path }"
          >
            {{ item.label }}
          </router-link>
        </nav>

        <div class="front-navbar__actions">
          <el-tooltip content="搜索社团与活动" placement="bottom">
            <el-button :icon="Search" circle @click="goSearch" />
          </el-tooltip>

          <el-badge :value="unreadCount" :hidden="unreadCount === 0">
            <el-button :icon="Bell" circle @click="goNotifications" />
          </el-badge>

          <el-dropdown v-if="userStore.isLoggedIn" @command="handleCommand">
            <span class="front-navbar__user">
              <span class="front-navbar__avatar">{{ userStore.userInfo?.avatar }}</span>
              <span class="front-navbar__name">{{ userStore.userInfo?.name }}</span>
              <el-tag size="small" type="info" effect="dark">{{ roleLabel }}</el-tag>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="profile">个人中心</el-dropdown-item>
                <el-dropdown-item v-if="userStore.role !== 'student'" command="admin">
                  管理后台
                </el-dropdown-item>
                <el-dropdown-item command="logout" divided>退出登录</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>

          <el-button v-else type="primary" round @click="router.push('/login')">
            登录 / 注册
          </el-button>
        </div>
      </div>
    </header>

    <main class="front-main">
      <router-view />
    </main>

    <footer class="front-footer">校园社团管理系统（基础 V1.0）· 软件工程课程项目</footer>
  </div>
</template>

<style scoped>
.front-layout {
  display: flex;
  flex-direction: column;
  min-height: 100%;
}

.front-navbar {
  position: sticky;
  top: 0;
  z-index: 100;
  height: var(--app-navbar-height);
  background: var(--app-color-primary);
  box-shadow: 0 2px 8px rgba(29, 95, 208, 0.25);
}

.front-navbar__inner {
  display: flex;
  align-items: center;
  gap: 32px;
  max-width: var(--app-container-width);
  height: 100%;
  margin: 0 auto;
  padding: 0 16px;
}

.front-navbar__logo {
  display: flex;
  gap: 8px;
  align-items: center;
  font-size: 18px;
  font-weight: 700;
  color: #fff;
}

.front-navbar__logo-icon {
  font-size: 22px;
}

.front-navbar__nav {
  display: flex;
  flex: 1;
  gap: 4px;
}

.front-navbar__link {
  padding: 0 14px;
  line-height: var(--app-navbar-height);
  color: rgba(255, 255, 255, 0.85);
  border-bottom: 3px solid transparent;
  transition: color 0.2s;
}

.front-navbar__link:hover {
  color: #fff;
}

.front-navbar__link.is-active {
  font-weight: 600;
  color: #fff;
  border-bottom-color: #fff;
}

.front-navbar__actions {
  display: flex;
  gap: 12px;
  align-items: center;
}

.front-navbar__user {
  display: flex;
  gap: 8px;
  align-items: center;
  color: #fff;
  cursor: pointer;
  outline: none;
}

.front-navbar__avatar {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  font-size: 18px;
  background: #fff;
  border-radius: 50%;
}

.front-navbar__name {
  font-size: 14px;
}

.front-main {
  flex: 1;
}

.front-footer {
  padding: 16px;
  font-size: 12px;
  color: var(--app-color-text-secondary);
  text-align: center;
}
</style>
