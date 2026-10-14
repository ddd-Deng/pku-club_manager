<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'

import { getClubs } from '@/api/club'
import CategoryFilter from '@/components/CategoryFilter.vue'
import ClubCard from '@/components/ClubCard.vue'
import SearchBar from '@/components/SearchBar.vue'
import StateBlock from '@/components/StateBlock.vue'
import type { Club } from '@/types/club'
import type { PageResult } from '@/types/common'
import { CLUB_CATEGORIES, DEFAULT_PAGE_SIZE } from '@/utils/constants'

const keyword = ref('')
const category = ref('全部类型')
const page = ref(1)
const pageSize = ref(DEFAULT_PAGE_SIZE)
const result = ref<PageResult<Club> | null>(null)
const loading = ref(false)
const errorMessage = ref('')

const categories = [...CLUB_CATEGORIES]

async function loadClubs(): Promise<void> {
  loading.value = true
  errorMessage.value = ''
  try {
    result.value = await getClubs({
      keyword: keyword.value || undefined,
      category: category.value,
      page: page.value,
      pageSize: pageSize.value
    })
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '加载失败'
  } finally {
    loading.value = false
  }
}

function handleSearch(value: string): void {
  keyword.value = value
  page.value = 1
  void loadClubs()
}

function handlePageChange(next: number): void {
  page.value = next
  void loadClubs()
}

watch(category, () => {
  page.value = 1
  void loadClubs()
})

onMounted(loadClubs)
</script>

<template>
  <div class="app-container plaza-view">
    <div class="plaza-view__header">
      <h2 class="app-section-title">社团广场</h2>
      <CategoryFilter v-model="category" :categories="categories" />
    </div>

    <SearchBar
      v-model="keyword"
      class="plaza-view__search"
      placeholder="搜索社团名称或关键词"
      @search="handleSearch"
    />

    <StateBlock
      :loading="loading"
      :error="errorMessage"
      :empty="(result?.list.length ?? 0) === 0"
      @retry="loadClubs"
    >
      <div class="plaza-view__grid">
        <ClubCard v-for="club in result?.list ?? []" :key="club.id" :club="club" />
      </div>

      <el-pagination
        v-if="(result?.total ?? 0) > pageSize"
        class="plaza-view__pagination"
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
.plaza-view__header {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}

.plaza-view__header .app-section-title {
  margin-bottom: 0;
}

.plaza-view__search {
  margin-bottom: 20px;
}

.plaza-view__grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}

.plaza-view__pagination {
  justify-content: center;
  margin-top: 24px;
}

@media (max-width: 992px) {
  .plaza-view__grid {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>
