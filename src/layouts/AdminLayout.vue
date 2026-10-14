<script setup lang="ts">
import { Bell, ChatDotRound, OfficeBuilding, Setting } from '@element-plus/icons-vue'
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { useUserStore } from '@/stores/user'
import { ROLE_LABELS } from '@/utils/constants'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const roleLabel = computed(() => (userStore.role ? ROLE_LABELS[userStore.role] : ''))
const clubDetailPath = computed(() => {
  const clubId = userStore.userInfo?.clubId
  return clubId ? `/clubs/${clubId}` : '/clubs'
})

function backToFront(): void {
  void router.push('/')
}

async function handleLogout(): Promise<void> {
  await userStore.logout()
  void router.push('/login')
}
</script>

<template>
  <el-container class="admin-layout">
    <el-aside class="admin-aside" width="220px">
      <div class="admin-aside__logo">
        <span class="admin-aside__logo-icon">🎓</span>
        <span>社团管理后台</span>
      </div>
      <el-menu :default-active="route.path" router class="admin-aside__menu">
        <el-menu-item index="/admin">
          <el-icon><Setting /></el-icon>
          <span>管理后台</span>
        </el-menu-item>
        <el-menu-item :index="clubDetailPath">
          <el-icon><OfficeBuilding /></el-icon>
          <span>社团详情页</span>
        </el-menu-item>
        <el-menu-item index="/notifications">
          <el-icon><Bell /></el-icon>
          <span>消息通知</span>
        </el-menu-item>
        <el-menu-item index="/ai">
          <el-icon><ChatDotRound /></el-icon>
          <span>AI 问答</span>
        </el-menu-item>
      </el-menu>
    </el-aside>

    <el-container>
      <el-header class="admin-header">
        <div class="admin-header__title">
          <span>社团管理后台</span>
          <el-tag type="primary" effect="plain">{{ roleLabel }}</el-tag>
          <el-tag v-if="userStore.userInfo?.clubName" effect="plain">
            {{ userStore.userInfo.clubName }}
          </el-tag>
        </div>
        <div class="admin-header__actions">
          <el-button text @click="backToFront">返回前台</el-button>
          <el-button text type="danger" @click="handleLogout">退出登录</el-button>
        </div>
      </el-header>
      <el-main class="admin-main">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<style scoped>
.admin-layout {
  height: 100%;
}

.admin-aside {
  background: var(--app-color-surface);
  border-right: 1px solid var(--app-color-border);
}

.admin-aside__logo {
  display: flex;
  gap: 8px;
  align-items: center;
  height: var(--app-navbar-height);
  padding: 0 20px;
  font-size: 16px;
  font-weight: 700;
  color: #fff;
  background: var(--app-color-primary);
}

.admin-aside__logo-icon {
  font-size: 20px;
}

.admin-aside__menu {
  border-right: none;
}

.admin-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: var(--app-color-surface);
  border-bottom: 1px solid var(--app-color-border);
}

.admin-header__title {
  display: flex;
  gap: 12px;
  align-items: center;
  font-size: 16px;
  font-weight: 600;
}

.admin-header__actions {
  display: flex;
  gap: 4px;
}

.admin-main {
  background: var(--app-color-bg);
}
</style>
