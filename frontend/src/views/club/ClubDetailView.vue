<script setup lang="ts">
import { ArrowLeft, Document, User } from '@element-plus/icons-vue'
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { getClubDetail } from '@/api/club'
import ActivityCard from '@/components/ActivityCard.vue'
import StateBlock from '@/components/StateBlock.vue'
import type { ClubDetail } from '@/types/club'
import { formatDate } from '@/utils/format'

const route = useRoute()
const router = useRouter()
const clubId = computed(() => String(route.params.id))

const loading = ref(false)
const errorMessage = ref('')
const club = ref<ClubDetail | null>(null)

/** 数据加载：统一三态，失败交给 StateBlock 展示并提供重试 */
async function loadClub(): Promise<void> {
  loading.value = true
  errorMessage.value = ''
  try {
    club.value = await getClubDetail(clubId.value)
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '加载失败'
  } finally {
    loading.value = false
  }
}

onMounted(loadClub)

function goBack(): void {
  void router.push('/clubs')
}

function goApply(): void {
  void router.push(`/clubs/${clubId.value}/apply`)
}
</script>

<template>
  <div class="app-container">
    <el-button class="club-detail__back" text @click="goBack">
      <el-icon><ArrowLeft /></el-icon>
      返回社团广场
    </el-button>

    <StateBlock :loading="loading" :error="errorMessage" @retry="loadClub">
      <template v-if="club">
        <el-card class="club-detail__head" shadow="never">
          <div class="club-detail__head-main">
            <span class="club-detail__logo">{{ club.logo }}</span>
            <div class="club-detail__title">
              <h2 class="club-detail__name">{{ club.name }}</h2>
              <div class="club-detail__meta">
                <el-tag effect="plain" type="primary">{{ club.category }}</el-tag>
                <span><el-icon><User /></el-icon>成员 {{ club.memberCount }} 人</span>
                <span>成立于 {{ formatDate(club.foundedAt) }}</span>
              </div>
              <el-tag
                v-for="tag in club.tags"
                :key="tag"
                class="club-detail__tag"
                effect="plain"
                round
                type="info"
              >
                {{ tag }}
              </el-tag>
            </div>
            <el-button class="club-detail__apply" round type="primary" @click="goApply">
              申请加入
            </el-button>
          </div>
          <p class="club-detail__desc">{{ club.description }}</p>
          <div class="club-detail__intro">{{ club.introduction }}</div>
        </el-card>

        <div class="club-detail__grid">
          <div class="club-detail__column">
            <el-card v-if="club.notices.length" shadow="never">
              <h3 class="app-section-title">社团公告</h3>
              <div v-for="notice in club.notices" :key="notice.id" class="club-detail__notice">
                <div class="club-detail__notice-head">
                  <el-icon><Document /></el-icon>
                  <strong>{{ notice.title }}</strong>
                  <span>{{ formatDate(notice.publishedAt) }}</span>
                </div>
                <p>{{ notice.content }}</p>
              </div>
            </el-card>

            <el-card shadow="never">
              <h3 class="app-section-title">近期活动</h3>
              <el-empty
                v-if="!club.recentActivities.length"
                description="暂无活动"
                :image-size="80"
              />
              <div
                v-for="activity in club.recentActivities"
                :key="activity.id"
                class="club-detail__activity"
              >
                <ActivityCard :activity="activity" />
              </div>
            </el-card>
          </div>

          <el-card shadow="never" class="club-detail__apply-card">
            <h3 class="app-section-title">加入社团</h3>
            <p class="club-detail__apply-tip">
              对{{ club.name }}感兴趣？登录学生账号提交入社申请，等待社长审核。
            </p>
            <el-button round type="primary" @click="goApply">提交入社申请</el-button>
          </el-card>
        </div>
      </template>
    </StateBlock>
  </div>
</template>

<style scoped>
.club-detail__back {
  margin-bottom: 8px;
  padding-left: 0;
}

.club-detail__head {
  margin-bottom: 16px;
}

.club-detail__head-main {
  display: flex;
  gap: 20px;
  align-items: flex-start;
}

.club-detail__logo {
  display: flex;
  flex-shrink: 0;
  align-items: center;
  justify-content: center;
  width: 72px;
  height: 72px;
  font-size: 36px;
  background: var(--app-color-primary-bg);
  border-radius: 50%;
}

.club-detail__title {
  flex: 1;
}

.club-detail__name {
  margin: 0 0 8px;
  font-size: 20px;
  font-weight: 600;
}

.club-detail__meta {
  display: flex;
  gap: 14px;
  align-items: center;
  font-size: 13px;
  color: var(--app-color-text-secondary);
}

.club-detail__meta span {
  display: flex;
  gap: 4px;
  align-items: center;
}

.club-detail__tag {
  margin: 10px 8px 0 0;
}

.club-detail__apply {
  flex-shrink: 0;
}

.club-detail__desc {
  margin: 16px 0 8px;
  color: var(--app-color-text-secondary);
}

.club-detail__intro {
  font-size: 13px;
  line-height: 22px;
  color: var(--app-color-text-secondary);
  white-space: pre-line;
}

.club-detail__grid {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 16px;
  align-items: start;
}

.club-detail__column {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.club-detail__notice {
  padding: 12px 0;
  border-bottom: 1px solid var(--app-color-border);
}

.club-detail__notice:last-child {
  border-bottom: none;
}

.club-detail__notice-head {
  display: flex;
  gap: 6px;
  align-items: center;
  font-size: 14px;
}

.club-detail__notice-head span {
  margin-left: auto;
  font-size: 12px;
  color: var(--app-color-text-placeholder);
}

.club-detail__notice p {
  margin: 8px 0 0;
  font-size: 13px;
  line-height: 20px;
  color: var(--app-color-text-secondary);
}

.club-detail__activity + .club-detail__activity {
  margin-top: 12px;
}

.club-detail__apply-card {
  position: sticky;
  top: 80px;
}

.club-detail__apply-tip {
  font-size: 13px;
  line-height: 20px;
  color: var(--app-color-text-secondary);
}

@media (max-width: 992px) {
  .club-detail__grid {
    grid-template-columns: 1fr;
  }
}
</style>
