<script setup lang="ts">
import { ArrowLeft } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { applyJoinClub, getClubDetail } from '@/api/club'
import StateBlock from '@/components/StateBlock.vue'
import { useUserStore } from '@/stores/user'
import type { Club } from '@/types/club'
import { ROLE_LABELS } from '@/utils/constants'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()
const clubId = computed(() => String(route.params.id))

const loading = ref(false)
const errorMessage = ref('')
const club = ref<Club | null>(null)
const message = ref('')
const submitting = ref(false)

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

onMounted(() => {
  if (!userStore.isLoggedIn) {
    void router.replace({ path: '/login', query: { redirect: route.fullPath } })
    return
  }
  void loadClub()
})

async function submitApplication(): Promise<void> {
  submitting.value = true
  try {
    await applyJoinClub(clubId.value, message.value.trim())
    ElMessage.success('入社申请已提交，等待社长审核')
    void router.push(`/clubs/${clubId.value}`)
  } catch {
    // 请求层已统一提示（1409 重复申请等）
  } finally {
    submitting.value = false
  }
}

function goBack(): void {
  void router.push(`/clubs/${clubId.value}`)
}
</script>

<template>
  <div class="app-container">
    <el-button class="club-apply__back" text @click="goBack">
      <el-icon><ArrowLeft /></el-icon>
      返回社团详情
    </el-button>

    <StateBlock :loading="loading" :error="errorMessage" @retry="loadClub">
      <el-card v-if="club" class="club-apply__card" shadow="never">
        <h2 class="app-section-title">申请加入 {{ club.name }}</h2>
        <el-alert
          class="club-apply__tip"
          type="info"
          :closable="false"
          show-icon
          :title="`当前登录：${userStore.userInfo?.name ?? ''}（${userStore.role ? ROLE_LABELS[userStore.role] : ''}）`"
          description="请填写申请理由，提交后将通知社长审核，可在个人中心查看进度。"
        />
        <el-form label-position="top" @submit.prevent="submitApplication">
          <el-form-item label="申请理由（200 字以内，选填）">
            <el-input
              v-model="message"
              type="textarea"
              :rows="5"
              maxlength="200"
              show-word-limit
              placeholder="例如：热爱摄影，希望加入学习后期与参加外拍活动。"
            />
          </el-form-item>
          <el-button type="primary" round :loading="submitting" @click="submitApplication">
            提交申请
          </el-button>
        </el-form>
      </el-card>
    </StateBlock>
  </div>
</template>

<style scoped>
.club-apply__back {
  margin-bottom: 8px;
  padding-left: 0;
}

.club-apply__card {
  max-width: 640px;
}

.club-apply__tip {
  margin-bottom: 16px;
}
</style>
