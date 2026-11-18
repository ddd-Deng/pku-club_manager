<script setup lang="ts">
import { ElMessage } from 'element-plus'
import { computed, onMounted, reactive, ref, watch } from 'vue'

import { createReservation, getReservations, getVenues } from '@/api/venue'
import StateBlock from '@/components/StateBlock.vue'
import type { ReservationStatus, Venue, VenueReservation } from '@/types/venue'
import { formatDateTime } from '@/utils/format'

/**
 * 后台「场地物资预约」分区（backlog #14）
 * 社长为本社团提交场地 + 物资预约单，并查看审批结果；审批由系统管理员完成。
 * 时段可用性来自接口 6.1，提交与列表使用接口 6.2 / 6.3。
 */
const STATUS_LABELS: Record<ReservationStatus, string> = {
  pending: '待审批',
  approved: '已通过',
  rejected: '已拒绝'
}

const loading = ref(false)
const errorMessage = ref('')
const venues = ref<Venue[]>([])
const reservations = ref<VenueReservation[]>([])
const total = ref(0)
const submitting = ref(false)

const form = reactive({
  venueId: '',
  date: '',
  timeSlot: '',
  purpose: '',
  items: [] as string[]
})

const currentVenue = computed(() => venues.value.find((item) => item.id === form.venueId) ?? null)

/** 可选日期来自该场地的时段表，天然限制在可预约窗口内 */
const dateOptions = computed(() => {
  const dates = new Set((currentVenue.value?.slots ?? []).map((slot) => slot.date))
  return [...dates].sort()
})

const slotOptions = computed(() =>
  (currentVenue.value?.slots ?? []).filter((slot) => slot.date === form.date)
)

// 换场地或换日期后原时段不再适用，清空以避免提交无效组合
watch(
  () => [form.venueId, form.date],
  () => {
    form.timeSlot = ''
  }
)

async function load(): Promise<void> {
  loading.value = true
  errorMessage.value = ''
  try {
    const [venueData, reservationData] = await Promise.all([
      getVenues(),
      getReservations({ page: 1, pageSize: 20 })
    ])
    venues.value = venueData
    reservations.value = reservationData.list
    total.value = reservationData.total
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '加载失败'
  } finally {
    loading.value = false
  }
}

onMounted(load)

function statusTagType(status: ReservationStatus): 'success' | 'warning' | 'danger' {
  if (status === 'approved') return 'success'
  if (status === 'rejected') return 'danger'
  return 'warning'
}

async function submit(): Promise<void> {
  if (!form.venueId || !form.date || !form.timeSlot) {
    ElMessage.warning('请先选择场地、日期与时段')
    return
  }
  if (!form.purpose.trim()) {
    ElMessage.warning('请填写用途说明')
    return
  }
  submitting.value = true
  try {
    await createReservation({
      venueId: form.venueId,
      date: form.date,
      timeSlot: form.timeSlot,
      purpose: form.purpose.trim(),
      items: form.items
    })
    ElMessage.success('预约单已提交，等待系统管理员审批')
    form.purpose = ''
    form.items = []
    await load()
  } catch {
    // 请求层已统一提示错误（1413 时段不存在 / 1414 时段已被占用等）
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <StateBlock :loading="loading" :error="errorMessage" @retry="load">
    <el-alert
      class="venue-panel__tip"
      type="info"
      :closable="false"
      show-icon
      title="以本社团名义提交场地与物资预约，审批结果会通过站内通知反馈，也可在下方列表查看。"
    />

    <el-form class="venue-panel__form" label-position="top" @submit.prevent="submit">
      <div class="venue-panel__row">
        <el-form-item label="场地">
          <el-select v-model="form.venueId" placeholder="请选择场地" class="venue-panel__control">
            <el-option
              v-for="venue in venues"
              :key="venue.id"
              :label="`${venue.name}（${venue.location}）`"
              :value="venue.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="日期">
          <el-select
            v-model="form.date"
            placeholder="请选择日期"
            :disabled="!form.venueId"
            class="venue-panel__control"
          >
            <el-option v-for="day in dateOptions" :key="day" :label="day" :value="day" />
          </el-select>
        </el-form-item>
        <el-form-item label="时段">
          <el-select
            v-model="form.timeSlot"
            placeholder="请选择时段"
            :disabled="!form.date"
            class="venue-panel__control"
          >
            <el-option
              v-for="slot in slotOptions"
              :key="slot.timeSlot"
              :label="slot.available ? slot.timeSlot : `${slot.timeSlot}（已被占用）`"
              :value="slot.timeSlot"
              :disabled="!slot.available"
            />
          </el-select>
        </el-form-item>
      </div>

      <el-form-item label="用途说明">
        <el-input
          v-model="form.purpose"
          maxlength="200"
          show-word-limit
          placeholder="例如：摄影社例会与评片会"
        />
      </el-form-item>
      <el-form-item label="随场地预约的物资（选填，输入后回车）">
        <el-select
          v-model="form.items"
          multiple
          filterable
          allow-create
          default-first-option
          :reserve-keyword="false"
          placeholder="例如：投影仪、白板"
          class="venue-panel__control"
        >
          <el-option label="投影仪" value="投影仪" />
          <el-option label="白板" value="白板" />
          <el-option label="音响" value="音响" />
          <el-option label="桌椅" value="桌椅" />
        </el-select>
      </el-form-item>
      <el-button type="primary" :loading="submitting" @click="submit">提交预约单</el-button>
    </el-form>

    <el-divider />

    <div class="venue-panel__list-head">
      <h3 class="app-section-title">本社团预约单（{{ total }}）</h3>
      <el-button text type="primary" @click="load">刷新</el-button>
    </div>
    <el-table :data="reservations" empty-text="还没有提交过预约单">
      <el-table-column prop="venueName" label="场地" min-width="160" />
      <el-table-column prop="date" label="日期" width="120" />
      <el-table-column prop="timeSlot" label="时段" width="120" />
      <el-table-column prop="purpose" label="用途" min-width="160" show-overflow-tooltip />
      <el-table-column label="物资" min-width="140">
        <template #default="{ row }">
          <el-tag v-for="item in row.items" :key="item" size="small" effect="plain" class="venue-panel__item">
            {{ item }}
          </el-tag>
          <span v-if="!row.items?.length">—</span>
        </template>
      </el-table-column>
      <el-table-column label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="statusTagType(row.status)" effect="light">
            {{ STATUS_LABELS[row.status as ReservationStatus] }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="审批意见" min-width="140">
        <template #default="{ row }">{{ row.comment || '—' }}</template>
      </el-table-column>
      <el-table-column label="提交时间" width="160">
        <template #default="{ row }">{{ formatDateTime(row.createdAt) }}</template>
      </el-table-column>
    </el-table>
  </StateBlock>
</template>

<style scoped>
.venue-panel__tip {
  margin-bottom: 16px;
}

.venue-panel__form {
  max-width: 860px;
}

.venue-panel__row {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
}

.venue-panel__control {
  width: 100%;
}

.venue-panel__list-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.venue-panel__item {
  margin-right: 4px;
}

@media (max-width: 992px) {
  .venue-panel__row {
    grid-template-columns: 1fr;
  }
}
</style>
