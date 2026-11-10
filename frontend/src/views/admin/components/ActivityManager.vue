<script setup lang="ts">
import { ElMessage, ElMessageBox } from 'element-plus'
import { onMounted, reactive, ref, watch } from 'vue'

import {
  createActivity,
  deleteActivity,
  getActivities,
  publishActivity,
  unpublishActivity,
  updateActivity
} from '@/api/activity'
import StateBlock from '@/components/StateBlock.vue'
import type { Activity, ActivityPayload, ActivityStatus } from '@/types/activity'
import { ACTIVITY_STATUS_LABELS } from '@/utils/constants'
import { formatDateTime } from '@/utils/format'

/** 后台「活动管理」分区：活动状态机见设计文档 §5，按钮按状态渲染（策略） */
const props = defineProps<{ clubId: string }>()

const ACTIVITY_TYPES = ['讲座', '比赛', '演出', '实践', '志愿活动']

const loading = ref(false)
const errorMessage = ref('')
const activities = ref<Activity[]>([])
const statusFilter = ref<ActivityStatus | ''>('')
const submitting = ref(false)

const dialogVisible = ref(false)
const editingId = ref<string | null>(null)
const form = reactive<ActivityPayload>({
  title: '',
  description: '',
  location: '',
  startTime: '',
  endTime: '',
  capacity: 50,
  type: '讲座',
  cover: ''
})

function statusLabel(status: ActivityStatus): string {
  return ACTIVITY_STATUS_LABELS[status]
}

function tagType(status: ActivityStatus): 'success' | 'warning' | 'info' {
  if (status === 'published') return 'success'
  if (status === 'draft') return 'warning'
  return 'info'
}

async function load(): Promise<void> {
  loading.value = true
  errorMessage.value = ''
  try {
    const result = await getActivities({
      clubId: props.clubId,
      status: statusFilter.value || undefined,
      pageSize: 50
    })
    activities.value = result.list
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '加载失败'
  } finally {
    loading.value = false
  }
}

onMounted(load)
watch(statusFilter, load)

function resetForm(): void {
  editingId.value = null
  form.title = ''
  form.description = ''
  form.location = ''
  form.startTime = ''
  form.endTime = ''
  form.capacity = 50
  form.type = '讲座'
  form.cover = ''
  form.clubId = undefined
}

function openCreate(): void {
  resetForm()
  dialogVisible.value = true
}

function openEdit(activity: Activity): void {
  editingId.value = activity.id
  form.title = activity.title
  form.description = activity.description
  form.location = activity.location
  form.startTime = activity.startTime.slice(0, 16)
  form.endTime = activity.endTime.slice(0, 16)
  form.capacity = activity.capacity
  form.type = activity.type
  form.cover = activity.cover
  form.clubId = activity.clubId
  dialogVisible.value = true
}

async function submit(): Promise<void> {
  submitting.value = true
  try {
    const payload: Partial<ActivityPayload> = {
      ...form,
      startTime: new Date(form.startTime).toISOString(),
      endTime: new Date(form.endTime).toISOString()
    }
    if (editingId.value) {
      await updateActivity(editingId.value, payload)
      ElMessage.success('活动已保存')
    } else {
      await createActivity(payload as ActivityPayload)
      ElMessage.success('活动已创建（草稿），发布后对外展示')
    }
    dialogVisible.value = false
    await load()
  } catch {
    // 请求层已统一提示错误
  } finally {
    submitting.value = false
  }
}

async function changeStatus(activity: Activity, action: 'publish' | 'unpublish'): Promise<void> {
  submitting.value = true
  try {
    if (action === 'publish') {
      await publishActivity(activity.id)
      ElMessage.success('活动已发布')
    } else {
      await unpublishActivity(activity.id)
      ElMessage.success('活动已下架')
    }
    await load()
  } catch {
    // 请求层已统一提示错误
  } finally {
    submitting.value = false
  }
}

async function remove(activity: Activity): Promise<void> {
  try {
    await ElMessageBox.confirm(
      `确定删除活动「${activity.title}」吗？仅草稿可删除。`,
      '删除活动',
      { confirmButtonText: '删除', cancelButtonText: '取消', type: 'warning' }
    )
  } catch {
    return
  }
  submitting.value = true
  try {
    await deleteActivity(activity.id)
    ElMessage.success('活动已删除')
    await load()
  } catch {
    // 请求层已统一提示错误
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <div class="activity-manager">
    <div class="activity-manager__toolbar">
      <el-radio-group v-model="statusFilter">
        <el-radio-button value="">全部</el-radio-button>
        <el-radio-button value="draft">草稿</el-radio-button>
        <el-radio-button value="published">已发布</el-radio-button>
        <el-radio-button value="unpublished">已下架</el-radio-button>
        <el-radio-button value="finished">已结束</el-radio-button>
      </el-radio-group>
      <el-button type="primary" @click="openCreate">新建活动</el-button>
    </div>

    <StateBlock :loading="loading" :error="errorMessage" @retry="load">
      <el-table :data="activities" empty-text="暂无活动">
        <el-table-column prop="title" label="活动" min-width="180">
          <template #default="{ row }">
            <span class="activity-manager__cell-title">{{ row.cover }} {{ row.title }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="type" label="类型" width="90" />
        <el-table-column label="时间" min-width="200">
          <template #default="{ row }">
            {{ formatDateTime(row.startTime) }} ~ {{ formatDateTime(row.endTime) }}
          </template>
        </el-table-column>
        <el-table-column prop="location" label="地点" min-width="140" show-overflow-tooltip />
        <el-table-column label="报名" width="110">
          <template #default="{ row }">{{ row.registeredCount }} / {{ row.capacity }}</template>
        </el-table-column>
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="tagType(row.status)" effect="light">
              {{ statusLabel(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="220" fixed="right">
          <template #default="{ row }">
            <el-button size="small" text type="primary" @click="openEdit(row)">编辑</el-button>
            <el-button
              v-if="row.status === 'draft'"
              size="small"
              text
              type="success"
              :loading="submitting"
              @click="changeStatus(row, 'publish')"
            >
              发布
            </el-button>
            <el-button
              v-if="row.status === 'published'"
              size="small"
              text
              type="warning"
              :loading="submitting"
              @click="changeStatus(row, 'unpublish')"
            >
              下架
            </el-button>
            <el-button
              v-if="row.status === 'draft'"
              size="small"
              text
              type="danger"
              @click="remove(row)"
            >
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </StateBlock>

    <el-dialog
      v-model="dialogVisible"
      :title="editingId ? '编辑活动' : '新建活动'"
      width="560px"
      destroy-on-close
    >
      <el-form label-position="top">
        <el-form-item label="活动标题" required>
          <el-input v-model="form.title" placeholder="活动标题" />
        </el-form-item>
        <el-form-item label="活动描述" required>
          <el-input
            v-model="form.description"
            type="textarea"
            :rows="3"
            placeholder="活动描述"
          />
        </el-form-item>
        <el-form-item label="活动地点" required>
          <el-input v-model="form.location" placeholder="活动地点" />
        </el-form-item>
        <div class="activity-manager__form-row">
          <el-form-item label="开始时间" required>
            <el-date-picker
              v-model="form.startTime"
              type="datetime"
              placeholder="开始时间"
              style="width: 100%"
              value-format="YYYY-MM-DDTHH:mm"
            />
          </el-form-item>
          <el-form-item label="结束时间" required>
            <el-date-picker
              v-model="form.endTime"
              type="datetime"
              placeholder="结束时间"
              style="width: 100%"
              value-format="YYYY-MM-DDTHH:mm"
            />
          </el-form-item>
        </div>
        <div class="activity-manager__form-row">
          <el-form-item label="活动类型" required>
            <el-select v-model="form.type" style="width: 100%">
              <el-option v-for="item in ACTIVITY_TYPES" :key="item" :label="item" :value="item" />
            </el-select>
          </el-form-item>
          <el-form-item label="名额上限" required>
            <el-input-number
              v-model="form.capacity"
              :min="1"
              :max="1000"
              style="width: 100%"
            />
          </el-form-item>
        </div>
        <el-form-item label="封面（emoji 或图片链接）">
          <el-input v-model="form.cover" placeholder="例如 🍂">
            <template #append>{{ form.cover }}</template>
          </el-input>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="submit">
          {{ editingId ? '保存' : '创建' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.activity-manager__toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.activity-manager__cell-title {
  font-weight: 500;
}

.activity-manager__form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}
</style>
