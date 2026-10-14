<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'

import {
  clearSearchHistory,
  deleteSearchHistory,
  getSearchHistory,
  search
} from '@/api/search'
import SearchBar from '@/components/SearchBar.vue'
import StateBlock from '@/components/StateBlock.vue'
import type { SearchHistoryItem, SearchHit, SearchHitType } from '@/types/search'
import type { PageResult } from '@/types/common'
import { DEFAULT_PAGE_SIZE } from '@/utils/constants'
import { useUserStore } from '@/stores/user'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const keyword = ref('')
const type = ref<SearchHitType | ''>('')
const dateRange = ref<[string, string] | null>(null)
const page = ref(1)
const pageSize = ref(DEFAULT_PAGE_SIZE)
const result = ref<PageResult<SearchHit> | null>(null)
const loading = ref(false)
const errorMessage = ref('')
const hasSearched = ref(false)

// 搜索历史
const history = ref<SearchHistoryItem[]>([])

const typeFilters: { label: string; value: SearchHitType | '' }[] = [
  { label: '全部', value: '' },
  { label: '社团', value: 'club' },
  { label: '活动', value: 'activity' }
]

async function doSearch(): Promise<void> {
  if (!keyword.value.trim()) {
    // 搜索词为空时不清空已有结果、不隐藏筛选按钮
    return
  }
  hasSearched.value = true
  loading.value = true
  errorMessage.value = ''
  try {
    result.value = await search({
      keyword: keyword.value.trim(),
      type: type.value || undefined,
      startDate: dateRange.value?.[0],
      endDate: dateRange.value?.[1],
      page: page.value,
      pageSize: pageSize.value
    })
    // 搜索成功后刷新历史列表
    if (userStore.isLoggedIn) {
      void loadHistory()
    }
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '搜索失败'
  } finally {
    loading.value = false
  }
}

function handleSearch(value: string): void {
  keyword.value = value
  page.value = 1
  // 同步 URL query，方便分享 / 刷新
  void router.replace({ path: '/search', query: value ? { keyword: value } : {} })
  void doSearch()
}

function handleTypeChange(): void {
  // 切换到非"活动"类型时清除时间筛选
  if (type.value !== 'activity') {
    dateRange.value = null
  }
  page.value = 1
  // 没有关键词时不触发搜索，避免清空已有结果
  if (keyword.value.trim()) {
    void doSearch()
  }
}

function handleDateRangeChange(): void {
  page.value = 1
  void doSearch()
}

function handlePageChange(next: number): void {
  page.value = next
  void doSearch()
}

function gotoDetail(hit: SearchHit): void {
  if (hit.type === 'club') {
    void router.push({ name: 'club-detail', params: { id: hit.id } })
  } else {
    void router.push({ name: 'activity-detail', params: { id: hit.id } })
  }
}

/* ---------------- 搜索历史 ---------------- */

async function loadHistory(): Promise<void> {
  if (!userStore.isLoggedIn) {
    history.value = []
    return
  }
  try {
    history.value = await getSearchHistory()
  } catch {
    // 历史加载失败不影响主流程
  }
}

function searchFromHistory(kw: string): void {
  keyword.value = kw
  page.value = 1
  void router.replace({ path: '/search', query: { keyword: kw } })
  void doSearch()
}

async function deleteHistoryItem(item: SearchHistoryItem): Promise<void> {
  try {
    await deleteSearchHistory(item.id)
    history.value = history.value.filter((h) => h.id !== item.id)
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '删除失败')
  }
}

async function clearAllHistory(): Promise<void> {
  try {
    await ElMessageBox.confirm('确定清空全部搜索历史吗？', '提示', {
      type: 'warning',
      confirmButtonText: '清空',
      cancelButtonText: '取消'
    })
  } catch {
    return // 用户取消
  }
  try {
    await clearSearchHistory()
    history.value = []
    ElMessage.success('已清空搜索历史')
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '清空失败')
  }
}

// 路由参数变化时触发搜索（如从首页搜索跳转过来）
watch(
  () => route.query.keyword,
  (val) => {
    const kw = typeof val === 'string' ? val : ''
    if (kw !== keyword.value) {
      keyword.value = kw
      page.value = 1
      void doSearch()
    }
  },
  { immediate: true }
)

onMounted(loadHistory)
watch(() => userStore.isLoggedIn, loadHistory)
</script>

<template>
  <div class="app-container search-view">
    <h2 class="app-section-title">搜索结果</h2>

    <SearchBar
      v-model="keyword"
      class="search-view__bar"
      placeholder="搜索社团名称或关键词"
      @search="handleSearch"
    />

    <!-- 搜索历史（始终展示） -->
    <div v-if="history.length > 0" class="search-history">
      <div class="search-history__header">
        <span class="search-history__title">搜索历史</span>
        <button class="search-history__clear" type="button" @click="clearAllHistory">
          清空
        </button>
      </div>
      <div class="search-history__tags">
        <span
          v-for="item in history"
          :key="item.id"
          class="search-history__tag"
        >
          <button class="search-history__tag-text" type="button" @click="searchFromHistory(item.keyword)">
            {{ item.keyword }}
          </button>
          <button
            class="search-history__tag-close"
            type="button"
            title="删除"
            @click="deleteHistoryItem(item)"
          >
            ×
          </button>
        </span>
      </div>
    </div>

    <div v-if="hasSearched" class="search-view__filters">
      <button
        v-for="filter in typeFilters"
        :key="filter.value"
        class="search-view__filter"
        :class="{ 'is-active': type === filter.value }"
        type="button"
        @click="
          () => {
            type = filter.value
            handleTypeChange()
          }
        "
      >
        {{ filter.label }}
      </button>

      <!-- 时间筛选：仅在选"活动"时显示 -->
      <el-date-picker
        v-if="type === 'activity'"
        v-model="dateRange"
        class="search-view__date-range"
        type="daterange"
        range-separator="至"
        start-placeholder="开始日期"
        end-placeholder="结束日期"
        value-format="YYYY-MM-DD"
        size="default"
        clearable
        @change="handleDateRangeChange"
      />
    </div>

    <StateBlock
      v-if="hasSearched"
      :loading="loading"
      :error="errorMessage"
      :empty="(result?.list.length ?? 0) === 0 && !loading"
      @retry="doSearch"
    >
      <div class="search-view__list">
        <div
          v-for="hit in result?.list ?? []"
          :key="`${hit.type}-${hit.id}`"
          class="search-hit"
          @click="gotoDetail(hit)"
        >
          <div class="search-hit__icon">
            <span v-if="hit.type === 'club'">社团</span>
            <span v-else>活动</span>
          </div>
          <div class="search-hit__content">
            <h3 class="search-hit__title">{{ hit.title }}</h3>
            <p class="search-hit__subtitle">{{ hit.subtitle }}</p>
          </div>
          <span class="search-hit__arrow">›</span>
        </div>
      </div>

      <el-pagination
        v-if="(result?.total ?? 0) > pageSize"
        class="search-view__pagination"
        :current-page="page"
        :page-size="pageSize"
        :total="result?.total ?? 0"
        layout="total, prev, pager, next"
        background
        @current-change="handlePageChange"
      />
    </StateBlock>
  </div>
</template>

<style scoped>
.search-view__bar {
  margin-bottom: 16px;
}

/* ---------------- 搜索历史 ---------------- */
.search-history {
  margin-bottom: 24px;
}

.search-history__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.search-history__title {
  font-size: 14px;
  color: var(--app-color-text-secondary);
}

.search-history__clear {
  padding: 2px 8px;
  font-size: 13px;
  color: var(--app-color-text-secondary);
  cursor: pointer;
  background: transparent;
  border: none;
  transition: color 0.2s;
}

.search-history__clear:hover {
  color: var(--app-color-danger, #f56c6c);
}

.search-history__tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.search-history__tag {
  display: inline-flex;
  align-items: center;
  overflow: hidden;
  background: var(--app-color-surface);
  border: 1px solid var(--app-color-border);
  border-radius: 999px;
}

.search-history__tag-text {
  padding: 4px 12px;
  font-size: 13px;
  color: var(--app-color-text-secondary);
  cursor: pointer;
  background: transparent;
  border: none;
  transition: color 0.2s;
}

.search-history__tag-text:hover {
  color: var(--app-color-primary);
}

.search-history__tag-close {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 24px;
  font-size: 16px;
  line-height: 1;
  color: var(--app-color-text-secondary);
  cursor: pointer;
  background: transparent;
  border: none;
  border-left: 1px solid var(--app-color-border);
  transition: color 0.2s;
}

.search-history__tag-close:hover {
  color: var(--app-color-danger, #f56c6c);
}

/* ---------------- 筛选栏 ---------------- */
.search-view__filters {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 20px;
}

.search-view__filter {
  padding: 6px 16px;
  font-size: 14px;
  color: var(--app-color-text-secondary);
  cursor: pointer;
  background: var(--app-color-surface);
  border: 1px solid var(--app-color-border);
  border-radius: 999px;
  transition: all 0.2s;
}

.search-view__filter:hover {
  color: var(--app-color-primary);
  border-color: var(--app-color-primary-light);
}

.search-view__filter.is-active {
  font-weight: 600;
  color: #fff;
  background: var(--app-color-primary);
  border-color: var(--app-color-primary);
}

.search-view__date-range {
  margin-left: 8px;
}

.search-view__list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.search-hit {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px;
  background: var(--app-color-surface);
  border: 1px solid var(--app-color-border);
  border-radius: 8px;
  cursor: pointer;
  transition: box-shadow 0.2s, border-color 0.2s;
}

.search-hit:hover {
  border-color: var(--app-color-primary-light);
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
}

.search-hit__icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 48px;
  height: 48px;
  font-size: 13px;
  font-weight: 600;
  color: var(--app-color-primary);
  background: var(--app-color-primary-light);
  border-radius: 50%;
  flex-shrink: 0;
}

.search-hit__content {
  flex: 1;
  min-width: 0;
}

.search-hit__title {
  margin: 0 0 4px;
  font-size: 16px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.search-hit__subtitle {
  margin: 0;
  font-size: 14px;
  color: var(--app-color-text-secondary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.search-hit__arrow {
  font-size: 20px;
  color: var(--app-color-text-secondary);
  flex-shrink: 0;
}

.search-view__pagination {
  justify-content: center;
  margin-top: 24px;
}
</style>
