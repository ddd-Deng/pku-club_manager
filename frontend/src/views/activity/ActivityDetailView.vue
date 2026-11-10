<script setup lang="ts">
import { ArrowLeft, Location, Timer } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import {
  cancelRegistration,
  getActivityDetail,
  registerActivity
} from '@/api/activity'
import StateBlock from '@/components/StateBlock.vue'
import { useUserStore } from '@/stores/user'
import type { Activity } from '@/types/activity'
import { ACTIVITY_STATUS_LABELS } from '@/utils/constants'
import { formatDateTime } from '@/utils/format'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()
const activityId = computed(() => String(route.params.id))

const loading = ref(false)
const errorMessage = ref('')
const activity = ref<Activity | null>(null)
const submitting = ref(false)

const registered = computed(() => activity.value?.registered ?? false)

/** 主操作按钮策略：按登录态 + 活动状态机（见设计文档 §5）决定渲染 */
const primaryAction = computed(() => {
  if (!activity.value) return null
  if (!userStore.isLoggedIn) {
    return { label: '登录后报名', kind: 'login' as const }
  }
  if (userStore.role === 'admin') return null
  if (registered.value) {
    return { label: '取消报名', kind: 'cancel' as const }
  }
  if (activity.value.status !== 'published') return null
  if (activity.value.registeredCount >= activity.value.capacity) return null
  return { label: '立即报名', kind: 'register' as const }
})

async function loadActivity(): Promise<void> {
  loading.value = true
  errorMessage.value = ''
  try {
    activity.value = await getActivityDetail(activityId.value)
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '加载失败'
  } finally {
    loading.value = false
  }
}

onMounted(loadActivity)

function goBack(): void {
  if (activity.value) {
    void router.push(`/clubs/${activity.value.clubId}`)
  } else {
    void router.push('/clubs')
  }
}

async function handleRegister(): Promise<void> {
  if (!activity.value) return
  submitting.value = true
  try {
    await registerActivity(activity.value.id)
    ElMessage.success('报名成功')
    await loadActivity()
  } catch {
    // 请求层已统一提示（名额满/未发布/重复报名等）
  } finally {
    submitting.value = false
  }
}

async function handleCancel(): Promise<void> {
  if (!activity.value) return
  try {
    await ElMessageBox.confirm('确定要取消报名该活动吗？', '取消报名', {
      confirmButtonText: '确定',
      cancelButtonText: '再想想',
      type: 'warning'
    })
  } catch {
    return
  }
  submitting.value = true
  try {
    await cancelRegistration(activity.value.id)
    ElMessage.success('已取消报名')
    await loadActivity()
  } catch {
    // 请求层已统一提示错误
  } finally {
    submitting.value = false
  }
}

function handlePrimary(): void {
  if (!primaryAction.value) return
  if (primaryAction.value.kind === 'login') {
    void router.push({ path: '/login', query: { redirect: route.fullPath } })
  } else if (primaryAction.value.kind === 'register') {
    void handleRegister()
  } else {
    void handleCancel()
  }
}
</script>

<template>
  <div class="app-container">
    <el-button class="activity-detail__back" text @click="goBack">
      <el-icon><ArrowLeft /></el-icon>
      返回社团详情
    </el-button>

    <StateBlock :loading="loading" :error="errorMessage" @retry="loadActivity">
      <template v-if="activity">
        <el-card class="activity-detail__card" shadow="never">
          <div class="activity-detail__head">
            <span class="activity-detail__cover">{{ activity.cover }}</span>
            <div class="activity-detail__head-main">
              <h2 class="activity-detail__title">{{ activity.title }}</h2>
              <div class="activity-detail__meta">
                <el-tag effect="plain" type="primary">{{ activity.type }}</el-tag>
                <el-tag
                  :type="activity.status === 'published' ? 'success' : 'info'"
                  effect="light"
                >
                  {{ ACTIVITY_STATUS_LABELS[activity.status] }}
                </el-tag>
                <span class="activity-detail__club" @click="goBack">
                  {{ activity.clubName }}
                </span>
              </div>
              <div class="activity-detail__time">
                <span>
                  <el-icon><Timer /></el-icon>
                  {{ formatDateTime(activity.startTime) }} ~ {{ formatDateTime(activity.endTime) }}
                </span>
                <span>
                  <el-icon><Location /></el-icon>
                  {{ activity.location }}
                </span>
              </div>
            </div>
            <div class="activity-detail__side">
              <div class="activity-detail__count">
                已报名 <strong>{{ activity.registeredCount }}</strong> / {{ activity.capacity }}
              </div>
              <el-progress
                :percentage="
                  Math.min(100, Math.round((activity.registeredCount / activity.capacity) * 100))
                "
                :stroke-width="8"
              />
              <el-button
                v-if="primaryAction"
                class="activity-detail__action"
                :loading="submitting"
                round
                :type="primaryAction.kind === 'cancel' ? 'danger' : 'primary'"
                @click="handlePrimary"
              >
                {{ primaryAction.label }}
              </el-button>
              <el-alert
                v-else-if="
                  activity.status === 'published' &&
                  activity.registeredCount >= activity.capacity
                "
                title="名额已满"
                type="warning"
                :closable="false"
                show-icon
              />
              <el-alert
                v-else-if="
                  userStore.isLoggedIn &&
                  userStore.role !== 'admin' &&
                  !registered &&
                  activity.status !== 'published'
                "
                title="活动暂未开放报名"
                type="info"
                :closable="false"
                show-icon
              />
            </div>
          </div>
          <el-divider />
          <div class="activity-detail__section">
            <h3 class="app-section-title">活动介绍</h3>
            <p class="activity-detail__desc">{{ activity.description }}</p>
          </div>
        </el-card>
      </template>
    </StateBlock>
  </div>
</template>

<style scoped>
.activity-detail__back {
  margin-bottom: 8px;
  padding-left: 0;
}

.activity-detail__head {
  display: flex;
  gap: 20px;
  align-items: flex-start;
}

.activity-detail__cover {
  display: flex;
  flex-shrink: 0;
  align-items: center;
  justify-content: center;
  width: 72px;
  height: 72px;
  font-size: 36px;
  background: var(--app-color-primary-bg);
  border-radius: var(--app-radius-md);
}

.activity-detail__head-main {
  flex: 1;
}

.activity-detail__title {
  margin: 0 0 10px;
  font-size: 20px;
  font-weight: 600;
}

.activity-detail__meta {
  display: flex;
  gap: 10px;
  align-items: center;
}

.activity-detail__club {
  font-size: 13px;
  color: var(--app-color-primary);
  cursor: pointer;
}

.activity-detail__time {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-top: 12px;
  font-size: 13px;
  color: var(--app-color-text-secondary);
}

.activity-detail__time span {
  display: flex;
  gap: 6px;
  align-items: center;
}

.activity-detail__side {
  display: flex;
  flex-direction: column;
  gap: 12px;
  width: 220px;
  flex-shrink: 0;
}

.activity-detail__count {
  font-size: 13px;
  color: var(--app-color-text-secondary);
}

.activity-detail__count strong {
  font-size: 20px;
  color: var(--app-color-primary);
}

.activity-detail__desc {
  margin: 0;
  font-size: 14px;
  line-height: 24px;
  color: var(--app-color-text-secondary);
  white-space: pre-line;
}

@media (max-width: 992px) {
  .activity-detail__head {
    flex-direction: column;
  }

  .activity-detail__side {
    width: 100%;
  }
}
</style>
