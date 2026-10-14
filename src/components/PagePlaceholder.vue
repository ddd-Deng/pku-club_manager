<script setup lang="ts">
withDefaults(
  defineProps<{
    title: string
    description?: string
  }>(),
  { description: '该页面为第一阶段占位实现，将在后续迭代中按 docs/api.md 契约完成。' }
)
</script>

<template>
  <el-card class="page-placeholder">
    <el-result icon="info" :title="title" :sub-title="description">
      <template #extra>
        <el-tag type="info" effect="plain">当前路由：{{ $route.path }}</el-tag>
      </template>
    </el-result>
  </el-card>
</template>

<style scoped>
.page-placeholder {
  max-width: 720px;
  margin: 0 auto;
}
</style>
