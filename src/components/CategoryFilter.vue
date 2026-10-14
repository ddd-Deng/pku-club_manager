<script setup lang="ts">
const ALL = '全部类型'

const model = defineModel<string>({ default: ALL })

defineProps<{ categories: string[] }>()

function select(category: string): void {
  model.value = category
}
</script>

<template>
  <div class="category-filter">
    <button
      class="category-filter__item"
      :class="{ 'is-active': model === ALL }"
      type="button"
      @click="select(ALL)"
    >
      全部类型
    </button>
    <button
      v-for="category in categories"
      :key="category"
      class="category-filter__item"
      :class="{ 'is-active': model === category }"
      type="button"
      @click="select(category)"
    >
      {{ category }}
    </button>
  </div>
</template>

<style scoped>
.category-filter {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.category-filter__item {
  padding: 6px 16px;
  font-size: 14px;
  color: var(--app-color-text-secondary);
  cursor: pointer;
  background: var(--app-color-surface);
  border: 1px solid var(--app-color-border);
  border-radius: 999px;
  transition: all 0.2s;
}

.category-filter__item:hover {
  color: var(--app-color-primary);
  border-color: var(--app-color-primary-light);
}

.category-filter__item.is-active {
  font-weight: 600;
  color: #fff;
  background: var(--app-color-primary);
  border-color: var(--app-color-primary);
}
</style>
