<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'

import { getUpcomingActivities } from '@/api/activity'
import { getRecommendedClubs } from '@/api/club'
import ActivityCard from '@/components/ActivityCard.vue'
import ClubCard from '@/components/ClubCard.vue'
import SearchBar from '@/components/SearchBar.vue'
import StateBlock from '@/components/StateBlock.vue'
import type { Activity } from '@/types/activity'
import type { Club } from '@/types/club'

const router = useRouter()

const keyword = ref('')
const clubs = ref<Club[]>([])
const activities = ref<Activity[]>([])
const loading = ref(true)
const errorMessage = ref('')

async function loadData(): Promise<void> {
  loading.value = true
  errorMessage.value = ''
  try {
    const [clubList, activityList] = await Promise.all([
      getRecommendedClubs(),
      getUpcomingActivities()
    ])
    clubs.value = clubList
    activities.value = activityList
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '加载失败'
  } finally {
    loading.value = false
  }
}

function handleSearch(value: string): void {
  void router.push({ path: '/search', query: value ? { keyword: value } : {} })
}

onMounted(loadData)
</script>

<template>
  <div class="home-view">
    <section class="home-hero">
      <div class="home-hero__inner">
        <h1 class="home-hero__title">一个账号，访问全校社团与活动</h1>
        <p class="home-hero__subtitle">发现兴趣社团 · 报名校园活动 · 管理社团事务</p>
        <SearchBar
          v-model="keyword"
          class="home-hero__search"
          placeholder="搜索社团名称或关键词"
          @search="handleSearch"
        />
      </div>
    </section>

    <div class="app-container">
      <StateBlock
        :loading="loading"
        :error="errorMessage"
        :empty="clubs.length === 0 && activities.length === 0"
        @retry="loadData"
      >
        <section class="home-section">
          <h2 class="app-section-title">社团推荐</h2>
          <div class="home-section__clubs">
            <ClubCard v-for="club in clubs" :key="club.id" :club="club" />
          </div>
        </section>

        <section class="home-section">
          <h2 class="app-section-title">近期活动</h2>
          <div class="home-section__activities">
            <ActivityCard v-for="activity in activities" :key="activity.id" :activity="activity" />
          </div>
        </section>
      </StateBlock>
    </div>
  </div>
</template>

<style scoped>
.home-hero {
  padding: 56px 16px;
  background: linear-gradient(
    135deg,
    var(--app-color-primary) 0%,
    var(--app-color-primary-light) 100%
  );
}

.home-hero__inner {
  max-width: var(--app-container-width);
  margin: 0 auto;
}

.home-hero__title {
  margin: 0 0 12px;
  font-size: 32px;
  color: #fff;
}

.home-hero__subtitle {
  margin: 0 0 24px;
  font-size: 15px;
  color: rgba(255, 255, 255, 0.85);
}

.home-hero__search {
  max-width: 560px;
}

.home-section {
  margin-bottom: 32px;
}

.home-section__clubs {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}

.home-section__activities {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
}

@media (max-width: 992px) {
  .home-section__clubs {
    grid-template-columns: repeat(2, 1fr);
  }

  .home-section__activities {
    grid-template-columns: 1fr;
  }
}
</style>
