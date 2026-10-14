<script setup lang="ts">
import { Search } from '@element-plus/icons-vue'

const model = defineModel<string>({ default: '' })

withDefaults(
  defineProps<{
    placeholder?: string
  }>(),
  { placeholder: '搜索社团名称或关键词' }
)

const emit = defineEmits<{ search: [keyword: string] }>()

function handleSearch(): void {
  emit('search', model.value.trim())
}

function handleClear(): void {
  model.value = ''
  emit('search', '')
}
</script>

<template>
  <el-input
    v-model="model"
    class="search-bar"
    :placeholder="placeholder"
    size="large"
    clearable
    :prefix-icon="Search"
    @keyup.enter="handleSearch"
    @clear="handleClear"
  >
    <template #append>
      <el-button :icon="Search" @click="handleSearch" />
    </template>
  </el-input>
</template>

<style scoped>
.search-bar {
  width: 100%;
}
</style>
