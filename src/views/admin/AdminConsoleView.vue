<script setup lang="ts">
import { ref } from 'vue'

import PagePlaceholder from '@/components/PagePlaceholder.vue'

const activeTab = ref('profile')

const tabs = [
  {
    name: 'profile',
    label: '社团资料编辑',
    description: '维护社团名称、简介、标签与头像等基础资料。'
  },
  { name: 'activity', label: '活动管理', description: '活动新建 / 草稿 / 发布 / 下架全流程管理。' },
  {
    name: 'recruitment',
    label: '招新审核',
    description: '发布招新帖、处理入社申请（通过 / 拒绝）。'
  },
  { name: 'member', label: '成员权限管理', description: '查看成员列表，设置骨干 / 移除成员。' },
  { name: 'venue', label: '场地物资预约', description: '提交场地与物资预约单，查看审批状态。' },
  { name: 'kb', label: '社团知识库上传', description: '上传社团文档，供 AI 知识库问答检索。' }
]
</script>

<template>
  <el-card class="admin-console">
    <el-tabs v-model="activeTab">
      <el-tab-pane v-for="tab in tabs" :key="tab.name" :label="tab.label" :name="tab.name">
        <PagePlaceholder :title="tab.label" :description="tab.description" />
      </el-tab-pane>
    </el-tabs>
  </el-card>
</template>

<style scoped>
.admin-console {
  min-height: calc(100vh - 160px);
}
</style>
