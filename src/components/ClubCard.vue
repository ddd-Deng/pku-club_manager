<script setup lang="ts">
import { User } from '@element-plus/icons-vue'
import { useRouter } from 'vue-router'

import type { Club } from '@/types/club'

const props = defineProps<{ club: Club }>()

const router = useRouter()

function goDetail(): void {
  void router.push(`/clubs/${props.club.id}`)
}
</script>

<template>
  <el-card class="club-card" shadow="hover" @click="goDetail">
    <div class="club-card__logo">{{ club.logo }}</div>
    <h3 class="club-card__name">{{ club.name }}</h3>
    <div class="club-card__meta">
      <el-icon><User /></el-icon>
      <span>{{ club.memberCount }} 人</span>
      <el-tag size="small" type="info" effect="plain">{{ club.category }}</el-tag>
    </div>
    <p class="club-card__desc app-ellipsis-2">{{ club.description }}</p>
    <el-button class="club-card__btn" type="primary" round @click.stop="goDetail">
      进入社团主页
    </el-button>
  </el-card>
</template>

<style scoped>
.club-card {
  height: 100%;
  cursor: pointer;
  transition:
    box-shadow 0.2s,
    transform 0.2s;
}

.club-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--app-shadow-card-hover);
}

.club-card__logo {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 64px;
  height: 64px;
  font-size: 32px;
  background: var(--app-color-primary-bg);
  border-radius: 50%;
}

.club-card__name {
  margin: 12px 0 8px;
  font-size: 16px;
  font-weight: 600;
}

.club-card__meta {
  display: flex;
  gap: 6px;
  align-items: center;
  font-size: 13px;
  color: var(--app-color-text-secondary);
}

.club-card__desc {
  min-height: 40px;
  margin: 8px 0 12px;
  font-size: 13px;
  line-height: 20px;
  color: var(--app-color-text-secondary);
}

.club-card__btn {
  width: 100%;
}
</style>
