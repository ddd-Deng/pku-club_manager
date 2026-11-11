<script setup lang="ts">
import { ElMessage, ElMessageBox } from 'element-plus'
import { onMounted, reactive, ref, watch } from 'vue'

import {
  getClubApplications,
  getRecruitments,
  publishRecruitment,
  reviewApplication
} from '@/api/club'
import StateBlock from '@/components/StateBlock.vue'
import type { ClubApplication, RecruitmentPost } from '@/types/club'
import { formatDate, formatDateTime } from '@/utils/format'

/** 后台「招新审核」分区：入社申请审核 + 发布招新帖（顺序图见设计文档 §4.2） */
const props = defineProps<{ clubId: string }>()

const STATUS_LABELS: Record<string, string> = {
  pending: '待审核',
  approved: '已通过',
  rejected: '已拒绝'
}

const loading = ref(false)
const errorMessage = ref('')
const applications = ref<ClubApplication[]>([])
const statusFilter = ref('pending')
const recruitments = ref<RecruitmentPost[]>([])
const reviewing = ref(false)

const dialogVisible = ref(false)
const recruitForm = reactive({ title: '', content: '', deadline: '' })
const publishing = ref(false)

async function loadApplications(): Promise<void> {
  loading.value = true
  errorMessage.value = ''
  try {
    const result = await getClubApplications(props.clubId, {
      status: statusFilter.value || undefined,
      pageSize: 50
    })
    applications.value = result.list
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '加载失败'
  } finally {
    loading.value = false
  }
}

async function loadRecruitments(): Promise<void> {
  try {
    recruitments.value = await getRecruitments(props.clubId)
  } catch {
    // 请求层已统一提示错误
  }
}

onMounted(() => {
  void loadApplications()
  void loadRecruitments()
})
watch(statusFilter, loadApplications)

async function review(application: ClubApplication, action: 'approve' | 'reject'): Promise<void> {
  let comment = ''
  if (action === 'reject') {
    try {
      const { value } = await ElMessageBox.prompt(
        '请输入拒绝原因（可选）',
        `拒绝 ${application.applicantName} 的申请`,
        {
          confirmButtonText: '确认拒绝',
          cancelButtonText: '取消',
          inputPlaceholder: '例如：当前招新名额已满'
        }
      )
      comment = (value ?? '').trim()
    } catch {
      return
    }
  }
  reviewing.value = true
  try {
    await reviewApplication(props.clubId, application.id, { action, comment })
    ElMessage.success(action === 'approve' ? '已通过申请' : '已拒绝申请')
    await loadApplications()
  } catch {
    // 请求层已统一提示错误（1410 已处理等）
  } finally {
    reviewing.value = false
  }
}

async function publish(): Promise<void> {
  publishing.value = true
  try {
    await publishRecruitment(props.clubId, {
      title: recruitForm.title,
      content: recruitForm.content,
      deadline: recruitForm.deadline
    })
    ElMessage.success('招新帖已发布')
    dialogVisible.value = false
    recruitForm.title = ''
    recruitForm.content = ''
    recruitForm.deadline = ''
    await loadRecruitments()
  } catch {
    // 请求层已统一提示错误
  } finally {
    publishing.value = false
  }
}
</script>

<template>
  <div class="application-review">
    <div class="application-review__toolbar">
      <el-radio-group v-model="statusFilter">
        <el-radio-button value="pending">待审核</el-radio-button>
        <el-radio-button value="approved">已通过</el-radio-button>
        <el-radio-button value="rejected">已拒绝</el-radio-button>
      </el-radio-group>
      <el-button type="primary" @click="dialogVisible = true">发布招新帖</el-button>
    </div>

    <StateBlock :loading="loading" :error="errorMessage" @retry="loadApplications">
      <el-table :data="applications" empty-text="暂无申请">
        <el-table-column prop="applicantName" label="申请人" width="110" />
        <el-table-column
          prop="message"
          label="申请理由"
          min-width="220"
          show-overflow-tooltip
        />
        <el-table-column label="提交时间" width="150">
          <template #default="{ row }">{{ formatDateTime(row.createdAt) }}</template>
        </el-table-column>
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag
              :type="
                row.status === 'approved'
                  ? 'success'
                  : row.status === 'rejected'
                    ? 'danger'
                    : 'warning'
              "
              effect="light"
            >
              {{ STATUS_LABELS[row.status] }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <template v-if="row.status === 'pending'">
              <el-button
                size="small"
                text
                type="success"
                :loading="reviewing"
                @click="review(row, 'approve')"
              >
                通过
              </el-button>
              <el-button size="small" text type="danger" @click="review(row, 'reject')">
                拒绝
              </el-button>
            </template>
            <span v-else class="application-review__reviewed">
              {{ row.reviewedAt ? formatDateTime(row.reviewedAt) : '—' }}
            </span>
          </template>
        </el-table-column>
      </el-table>
    </StateBlock>

    <el-card class="application-review__recruitments" shadow="never">
      <h3 class="app-section-title">招新帖（{{ recruitments.length }}）</h3>
      <el-empty v-if="!recruitments.length" description="暂无招新帖" :image-size="80" />
      <div
        v-for="post in recruitments"
        :key="post.id"
        class="application-review__recruitment"
      >
        <div class="application-review__recruitment-head">
          <strong>{{ post.title }}</strong>
          <el-tag effect="plain" type="primary">截止 {{ formatDate(post.deadline) }}</el-tag>
        </div>
        <p>{{ post.content }}</p>
      </div>
    </el-card>

    <el-dialog v-model="dialogVisible" title="发布招新帖" width="520px" destroy-on-close>
      <el-form label-position="top">
        <el-form-item label="标题" required>
          <el-input v-model="recruitForm.title" placeholder="例如：摄影社秋季招新" />
        </el-form-item>
        <el-form-item label="内容" required>
          <el-input
            v-model="recruitForm.content"
            type="textarea"
            :rows="4"
            placeholder="招新要求、面向人群、报名方式……"
          />
        </el-form-item>
        <el-form-item label="报名截止" required>
          <el-date-picker
            v-model="recruitForm.deadline"
            type="date"
            placeholder="截止日期"
            style="width: 100%"
            value-format="YYYY-MM-DD"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="publishing" @click="publish">发布</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.application-review__toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.application-review__reviewed {
  font-size: 12px;
  color: var(--app-color-text-placeholder);
}

.application-review__recruitments {
  margin-top: 20px;
}

.application-review__recruitment {
  padding: 12px 0;
  border-bottom: 1px solid var(--app-color-border);
}

.application-review__recruitment:last-child {
  border-bottom: none;
}

.application-review__recruitment-head {
  display: flex;
  gap: 10px;
  align-items: center;
}

.application-review__recruitment-head .el-tag {
  margin-left: auto;
}

.application-review__recruitment p {
  margin: 8px 0 0;
  font-size: 13px;
  line-height: 20px;
  color: var(--app-color-text-secondary);
}
</style>
