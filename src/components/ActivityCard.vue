<script setup lang="ts">
import { Location, Timer } from '@element-plus/icons-vue'
import { useRouter } from 'vue-router'

import type { Activity } from '@/types/activity'
import { ACTIVITY_STATUS_LABELS } from '@/utils/constants'
import { formatDateTime } from '@/utils/format'

const props = defineProps<{ activity: Activity }>()

const router = useRouter()

function goDetail(): void {
  void router.push(`/activities/${props.activity.id}`)
}
</script>

<template>
  <el-card class="activity-card" shadow="hover" @click="goDetail">
    <div class="activity-card__head">
      <span class="activity-card__cover">{{ activity.cover }}</span>
      <div class="activity-card__head-main">
        <h4 class="activity-card__title app-ellipsis-2">{{ activity.title }}</h4>
        <span class="activity-card__club">{{ activity.clubName }} · {{ activity.type }}</span>
      </div>
      <el-tag :type="activity.status === 'published' ? 'primary' : 'info'" effect="light">
        {{ ACTIVITY_STATUS_LABELS[activity.status] }}
      </el-tag>
    </div>
    <div class="activity-card__meta">
      <span
        ><el-icon><Timer /></el-icon>{{ formatDateTime(activity.startTime) }}</span
      >
      <span
        ><el-icon><Location /></el-icon>{{ activity.location }}</span
      >
    </div>
    <div class="activity-card__foot">
      <el-progress
        :percentage="
          Math.min(100, Math.round((activity.registeredCount / activity.capacity) * 100))
        "
        :stroke-width="6"
        :show-text="false"
      />
      <span class="activity-card__count">
        已报名 {{ activity.registeredCount }} / {{ activity.capacity }}
      </span>
    </div>
  </el-card>
</template>

<style scoped>
.activity-card {
  height: 100%;
  cursor: pointer;
  transition: box-shadow 0.2s;
}

.activity-card:hover {
  box-shadow: var(--app-shadow-card-hover);
}

.activity-card__head {
  display: flex;
  gap: 10px;
  align-items: flex-start;
}

.activity-card__cover {
  display: flex;
  flex-shrink: 0;
  align-items: center;
  justify-content: center;
  width: 44px;
  height: 44px;
  font-size: 22px;
  background: var(--app-color-primary-bg);
  border-radius: var(--app-radius-sm);
}

.activity-card__head-main {
  flex: 1;
}

.activity-card__title {
  margin: 0 0 4px;
  font-size: 15px;
  font-weight: 600;
}

.activity-card__club {
  font-size: 12px;
  color: var(--app-color-text-secondary);
}

.activity-card__meta {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin: 12px 0;
  font-size: 13px;
  color: var(--app-color-text-secondary);
}

.activity-card__meta span {
  display: flex;
  gap: 4px;
  align-items: center;
}

.activity-card__foot {
  display: flex;
  gap: 10px;
  align-items: center;
}

.activity-card__foot .el-progress {
  flex: 1;
}

.activity-card__count {
  flex-shrink: 0;
  font-size: 12px;
  color: var(--app-color-text-secondary);
}
</style>
