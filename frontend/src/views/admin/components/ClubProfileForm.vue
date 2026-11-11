<script setup lang="ts">
import { ElMessage } from 'element-plus'
import { onMounted, reactive, ref } from 'vue'

import { getClubDetail, updateClub } from '@/api/club'
import StateBlock from '@/components/StateBlock.vue'
import type { ClubDetail } from '@/types/club'

/** 后台「社团资料编辑」分区：只依赖 clubApi 的 getClubDetail / updateClub */
const props = defineProps<{ clubId: string }>()
const emit = defineEmits<{ (e: 'club-loaded', name: string): void }>()

const loading = ref(false)
const errorMessage = ref('')
const clubDetail = ref<ClubDetail | null>(null)
const saving = ref(false)

const form = reactive({
  name: '',
  description: '',
  introduction: '',
  logo: '',
  tags: [] as string[]
})

const tagInput = ref('')

async function load(): Promise<void> {
  loading.value = true
  errorMessage.value = ''
  try {
    const detail = await getClubDetail(props.clubId)
    clubDetail.value = detail
    form.name = detail.name
    form.description = detail.description
    form.introduction = detail.introduction
    form.logo = detail.logo
    form.tags = [...detail.tags]
    emit('club-loaded', detail.name)
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '加载失败'
  } finally {
    loading.value = false
  }
}

onMounted(load)

function addTag(): void {
  const value = tagInput.value.trim()
  if (!value) return
  if (form.tags.length >= 5) {
    ElMessage.warning('标签最多 5 个')
    return
  }
  if (!form.tags.includes(value)) {
    form.tags.push(value)
  }
  tagInput.value = ''
}

function removeTag(tag: string): void {
  form.tags = form.tags.filter((item) => item !== tag)
}

async function save(): Promise<void> {
  saving.value = true
  try {
    const detail = await updateClub(props.clubId, {
      name: form.name,
      description: form.description,
      introduction: form.introduction,
      logo: form.logo,
      tags: form.tags
    })
    clubDetail.value = detail
    emit('club-loaded', detail.name)
    ElMessage.success('社团资料已保存')
  } catch {
    // 请求层已统一提示错误
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <StateBlock :loading="loading" :error="errorMessage" @retry="load">
    <el-form
      v-if="clubDetail"
      class="club-profile-form"
      label-position="top"
      @submit.prevent="save"
    >
      <el-form-item label="社团名称">
        <el-input v-model="form.name" placeholder="社团名称" />
      </el-form-item>
      <el-form-item label="一句话简介（卡片展示）">
        <el-input v-model="form.description" placeholder="一句话简介" />
      </el-form-item>
      <el-form-item label="详细介绍">
        <el-input
          v-model="form.introduction"
          type="textarea"
          :rows="4"
          placeholder="社团详细介绍"
        />
      </el-form-item>
      <el-form-item label="头像（emoji 或图片链接）">
        <el-input v-model="form.logo" placeholder="例如 📷">
          <template #append>{{ form.logo }}</template>
        </el-input>
      </el-form-item>
      <el-form-item label="标签（最多 5 个）">
        <div class="club-profile-form__tags">
          <el-tag
            v-for="tag in form.tags"
            :key="tag"
            closable
            effect="plain"
            @close="removeTag(tag)"
          >
            {{ tag }}
          </el-tag>
          <el-input
            v-if="form.tags.length < 5"
            v-model="tagInput"
            class="club-profile-form__tag-input"
            placeholder="输入后回车添加"
            @keyup.enter="addTag"
            @blur="addTag"
          />
        </div>
      </el-form-item>
      <el-button type="primary" :loading="saving" @click="save">保存资料</el-button>
    </el-form>
  </StateBlock>
</template>

<style scoped>
.club-profile-form {
  max-width: 640px;
}

.club-profile-form__tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
}

.club-profile-form__tag-input {
  width: 160px;
}
</style>
