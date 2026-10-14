<script setup lang="ts">
withDefaults(
  defineProps<{
    /** 加载中 */
    loading?: boolean
    /** 失败信息，非空展示失败态 */
    error?: string
    /** 空数据 */
    empty?: boolean
  }>(),
  { loading: false, error: '', empty: false }
)

defineEmits<{ retry: [] }>()
</script>

<template>
  <div v-if="loading" class="state-block">
    <el-skeleton :rows="4" animated />
  </div>

  <el-result v-else-if="error" class="state-block" icon="error" title="加载失败" :sub-title="error">
    <template #extra>
      <el-button type="primary" @click="$emit('retry')">重新加载</el-button>
    </template>
  </el-result>

  <el-empty v-else-if="empty" class="state-block" description="暂无数据" />

  <slot v-else />
</template>

<style scoped>
.state-block {
  padding: 24px 0;
}
</style>
