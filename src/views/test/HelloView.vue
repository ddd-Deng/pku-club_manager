<script setup lang="ts">
import { onMounted, ref } from 'vue'

import { getHello } from '@/api/test'
import StateBlock from '@/components/StateBlock.vue'
import { isMockEnabled } from '@/mock'
import type { HelloResult } from '@/types/common'

const result = ref<HelloResult | null>(null)
const loading = ref(true)
const errorMessage = ref('')

async function load(): Promise<void> {
  loading.value = true
  errorMessage.value = ''
  try {
    result.value = await getHello()
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '请求失败'
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>

<template>
  <div class="app-container hello-view">
    <el-card>
      <h1 class="hello-view__title">hello world</h1>
      <p class="hello-view__tip">
        下方展示 GET /api/test/hello 的返回结果（当前数据模式：{{
          isMockEnabled() ? '本地 mock' : '真实后端'
        }}）
      </p>

      <StateBlock :loading="loading" :error="errorMessage" :empty="!result" @retry="load">
        <el-descriptions :column="1" border>
          <el-descriptions-item label="message">{{ result?.message }}</el-descriptions-item>
          <el-descriptions-item label="source">{{ result?.source }}</el-descriptions-item>
          <el-descriptions-item label="serverTime">{{ result?.serverTime }}</el-descriptions-item>
        </el-descriptions>
        <pre class="hello-view__raw">{{ JSON.stringify(result, null, 2) }}</pre>
      </StateBlock>
    </el-card>
  </div>
</template>

<style scoped>
.hello-view__title {
  margin: 0 0 8px;
  font-size: 28px;
}

.hello-view__tip {
  margin: 0 0 16px;
  color: var(--app-color-text-secondary);
}

.hello-view__raw {
  padding: 12px;
  margin-top: 16px;
  overflow: auto;
  font-size: 12px;
  background: var(--app-color-bg);
  border-radius: var(--app-radius-sm);
}
</style>
