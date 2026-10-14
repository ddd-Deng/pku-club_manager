<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { assignPresident, getAccounts, getAdminClubs } from '@/api/admin'
import StateBlock from '@/components/StateBlock.vue'
import type { AdminAccount, AdminClub } from '@/types/admin'

const clubs = ref<AdminClub[]>([])
const total = ref(0)
const page = ref(1)
const keyword = ref('')
const loading = ref(false)
const errorMessage = ref('')
const selected = ref<AdminClub | null>(null)
const dialogVisible = ref(false)
const candidateId = ref('')
const candidates = ref<AdminAccount[]>([])
const candidateKeyword = ref('')
const candidatePage = ref(1)
const candidateTotal = ref(0)
const candidatesLoading = ref(false)
const candidateError = ref('')
const saving = ref(false)

async function loadData(): Promise<void> {
  loading.value = true
  errorMessage.value = ''
  try {
    const result = await getAdminClubs({
      page: page.value,
      pageSize: 10,
      keyword: keyword.value.trim()
    })
    clubs.value = result.list
    total.value = result.total
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '加载失败'
  } finally {
    loading.value = false
  }
}
function search(): void {
  page.value = 1
  void loadData()
}
async function loadCandidates(): Promise<void> {
  candidatesLoading.value = true
  candidateError.value = ''
  try {
    const result = await getAccounts({
      page: candidatePage.value,
      pageSize: 10,
      keyword: candidateKeyword.value.trim(),
      role: 'student',
      isActive: true
    })
    candidates.value = result.list
    candidateTotal.value = result.total
  } catch (error) {
    candidateError.value = error instanceof Error ? error.message : '候选人加载失败'
  } finally {
    candidatesLoading.value = false
  }
}
function searchCandidates(): void {
  candidatePage.value = 1
  candidateId.value = ''
  void loadCandidates()
}
function changeCandidatePage(): void {
  candidateId.value = ''
  void loadCandidates()
}
function open(club: AdminClub): void {
  selected.value = club
  candidateId.value = ''
  candidateKeyword.value = ''
  candidatePage.value = 1
  candidates.value = []
  dialogVisible.value = true
  void loadCandidates()
}
async function submit(): Promise<void> {
  const club = selected.value
  const candidate = candidates.value.find((user) => user.id === candidateId.value)
  if (!club || !candidate) {
    ElMessage.warning('请选择一位候选学生')
    return
  }
  try {
    await ElMessageBox.confirm(
      `将${club.name}的社长从“${club.president?.name ?? '未任命'}”更换为“${candidate.name}（${candidate.studentNo}）”？旧社长保留为普通成员，新旧社长需要重新登录。`,
      '确认社长任命',
      { type: 'warning' }
    )
  } catch {
    return
  }
  saving.value = true
  try {
    await assignPresident(club.id, {
      userId: candidate.id,
      expectedPresidentId: club.president?.id ?? null
    })
    dialogVisible.value = false
    ElMessage.success('社长任命已完成')
    await loadData()
  } catch {
    dialogVisible.value = false
    await loadData() // Refresh the expected owner after a concurrent handover or candidate change.
  } finally {
    saving.value = false
  }
}
onMounted(loadData)
</script>

<template>
  <el-card class="presidents-view">
    <h2 class="app-section-title">任命／更换社长</h2>
    <p>每人最多管理一个社团。未入社的学生会自动成为成员；旧社长保留为普通成员。</p>
    <div class="presidents-view__search">
      <el-input
        v-model="keyword"
        placeholder="搜索社团名称"
        clearable
        @keyup.enter="search"
      /><el-button type="primary" @click="search">查询</el-button>
    </div>
    <StateBlock
      :loading="loading"
      :error="errorMessage"
      :empty="clubs.length === 0"
      @retry="loadData"
    >
      <el-table :data="clubs" row-key="id">
        <el-table-column prop="name" label="社团" min-width="140" /><el-table-column
          prop="category"
          label="类型"
          min-width="110"
        />
        <el-table-column label="当前社长" min-width="140"
          ><template #default="{ row }">{{
            row.president?.name ?? '未任命'
          }}</template></el-table-column
        >
        <el-table-column label="社长学号" min-width="120"
          ><template #default="{ row }">{{
            row.president?.studentNo ?? '—'
          }}</template></el-table-column
        >
        <el-table-column label="操作" width="130"
          ><template #default="{ row }"
            ><el-button link type="primary" @click="open(row)">{{
              row.president ? '更换社长' : '任命社长'
            }}</el-button></template
          ></el-table-column
        >
      </el-table>
    </StateBlock>
    <el-pagination
      v-if="total > 0"
      v-model:current-page="page"
      :page-size="10"
      :total="total"
      layout="prev, pager, next, total"
      @current-change="loadData"
    />
    <el-dialog
      v-model="dialogVisible"
      :title="`${selected?.name ?? ''}：选择新社长`"
      width="min(620px, 95vw)"
      :close-on-click-modal="!saving"
      :show-close="!saving"
    >
      <p>
        当前社长：{{
          selected?.president?.name ?? '未任命'
        }}。候选人仅包含启用且未担任其他社团社长的学生。
      </p>
      <div class="presidents-view__search">
        <el-input
          v-model="candidateKeyword"
          placeholder="搜索候选人的姓名、学号或邮箱"
          clearable
          @keyup.enter="searchCandidates"
        /><el-button :disabled="saving" @click="searchCandidates">查找</el-button>
      </div>
      <StateBlock
        :loading="candidatesLoading"
        :error="candidateError"
        :empty="candidates.length === 0"
        @retry="loadCandidates"
      >
        <el-radio-group
          v-model="candidateId"
          :disabled="saving"
          class="presidents-view__candidates"
        >
          <el-radio v-for="candidate in candidates" :key="candidate.id" :value="candidate.id"
            >{{ candidate.name }} · {{ candidate.studentNo }} · {{ candidate.email }}</el-radio
          >
        </el-radio-group>
      </StateBlock>
      <el-pagination
        v-if="candidateTotal > 0"
        v-model:current-page="candidatePage"
        :page-size="10"
        :total="candidateTotal"
        layout="prev, pager, next"
        @current-change="changeCandidatePage"
      />
      <template #footer
        ><el-button :disabled="saving" @click="dialogVisible = false">取消</el-button
        ><el-button
          type="primary"
          :disabled="!candidateId || candidatesLoading"
          :loading="saving"
          @click="submit"
          >确认任命</el-button
        ></template
      >
    </el-dialog>
  </el-card>
</template>

<style scoped>
.presidents-view__search {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
}
.presidents-view__search .el-input {
  max-width: 380px;
}
.presidents-view__candidates {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
}
.presidents-view .el-pagination {
  margin-top: 20px;
}
</style>
