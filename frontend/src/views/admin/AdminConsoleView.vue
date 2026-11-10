<script setup lang="ts">
import { computed, ref } from 'vue'

import { useUserStore } from '@/stores/user'

import ActivityManager from './components/ActivityManager.vue'
import ApplicationReviewPanel from './components/ApplicationReviewPanel.vue'
import ClubProfileForm from './components/ClubProfileForm.vue'
import MemberManager from './components/MemberManager.vue'

/**
 * 管理后台容器（OOD：单一职责）
 * 只负责：标签切换 + 确定"当前管理的社团" + 分发到四个业务子组件。
 * 各分区的数据加载与业务逻辑都在子组件内完成（见 docs/phase2-design.md §3 类图）。
 */
const userStore = useUserStore()
const isAdmin = computed(() => userStore.role === 'admin')
/** 社长固定管理所属社团；管理员演示默认操作摄影社 */
const managedClubId = computed(() =>
  isAdmin.value ? 'c-1' : (userStore.userInfo?.clubId ?? 'c-1')
)

const activeTab = ref('profile')
const clubName = ref('')
</script>

<template>
  <el-card class="admin-console" shadow="never">
    <div class="admin-console__head">
      <h2 class="admin-console__title">社团管理后台</h2>
      <el-tag v-if="clubName" type="primary" effect="plain">当前管理：{{ clubName }}</el-tag>
    </div>

    <el-tabs v-model="activeTab">
      <el-tab-pane label="社团资料编辑" name="profile">
        <ClubProfileForm :club-id="managedClubId" @club-loaded="clubName = $event" />
      </el-tab-pane>
      <el-tab-pane label="活动管理" name="activity">
        <ActivityManager :club-id="managedClubId" />
      </el-tab-pane>
      <el-tab-pane label="招新审核" name="recruitment">
        <ApplicationReviewPanel :club-id="managedClubId" />
      </el-tab-pane>
      <el-tab-pane label="成员权限管理" name="member">
        <MemberManager :club-id="managedClubId" />
      </el-tab-pane>
      <el-tab-pane label="场地物资预约" name="venue" disabled>
        <p class="admin-console__placeholder">本阶段范围外，保留占位（见 backlog ID 14）。</p>
      </el-tab-pane>
      <el-tab-pane label="社团知识库上传" name="kb" disabled>
        <p class="admin-console__placeholder">本阶段范围外，保留占位（见 backlog ID 15）。</p>
      </el-tab-pane>
    </el-tabs>
  </el-card>
</template>

<style scoped>
.admin-console {
  min-height: calc(100vh - 160px);
}

.admin-console__head {
  display: flex;
  gap: 12px;
  align-items: center;
  margin-bottom: 8px;
}

.admin-console__title {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
}

.admin-console__placeholder {
  margin: 24px 0;
  text-align: center;
  color: var(--app-color-text-placeholder);
}
</style>
