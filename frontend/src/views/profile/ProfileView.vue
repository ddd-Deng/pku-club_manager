<script setup lang="ts">
import { ElMessage } from 'element-plus'
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'

import {
  changePassword,
  getFootprints,
  getMyApplications,
  getMyRegistrations,
  getProfile,
  updateProfile
} from '@/api/user'
import StateBlock from '@/components/StateBlock.vue'
import { useUserStore } from '@/stores/user'
import type { ClubApplication } from '@/types/club'
import type { ActivityRegistrationRecord, FootprintItem, UserInfo } from '@/types/user'
import { APPLICATION_STATUS_LABELS, ROLE_LABELS } from '@/utils/constants'
import { formatDate, formatDateTime } from '@/utils/format'

/**
 * 个人中心（backlog #13）
 * 左侧为个人资料与账号安全，右侧为「我的入社申请 / 我的活动报名 / 活动足迹」三个分区。
 * 数据全部来自 api/user.ts（接口 3.1–3.6），不直接访问 axios 或 mock。
 * 入社申请分区同时解决"社长审核通过后学生看不到结果"的问题。
 */
const router = useRouter()
const userStore = useUserStore()

const activeTab = ref('applications')
const loading = ref(false)
const errorMessage = ref('')
const profile = ref<UserInfo | null>(null)
const applications = ref<ClubApplication[]>([])
const registrations = ref<ActivityRegistrationRecord[]>([])
const footprints = ref<FootprintItem[]>([])

const roleLabel = computed(() => (profile.value ? ROLE_LABELS[profile.value.role] : ''))
const pendingCount = computed(
  () => applications.value.filter((item) => item.status === 'pending').length
)

/** 四个接口并发拉取，统一三态；失败由 StateBlock 展示并提供重试 */
async function loadAll(): Promise<void> {
  loading.value = true
  errorMessage.value = ''
  try {
    const [profileData, applicationData, registrationData, footprintData] = await Promise.all([
      getProfile(),
      getMyApplications(),
      getMyRegistrations(),
      getFootprints()
    ])
    profile.value = profileData
    applications.value = applicationData
    registrations.value = registrationData
    footprints.value = footprintData
    // 同步顶部导航展示的昵称与头像，避免改完资料后导航仍是旧值
    userStore.userInfo = profileData
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '加载失败'
  } finally {
    loading.value = false
  }
}

onMounted(loadAll)

function applicationTagType(status: ClubApplication['status']): 'success' | 'warning' | 'danger' {
  if (status === 'approved') return 'success'
  if (status === 'rejected') return 'danger'
  return 'warning'
}

function applicationStatusLabel(status: ClubApplication['status']): string {
  return APPLICATION_STATUS_LABELS[status]
}

function goClub(clubId: string): void {
  void router.push(`/clubs/${clubId}`)
}

function goActivity(activityId: string): void {
  void router.push(`/activities/${activityId}`)
}

function goClubPlaza(): void {
  void router.push('/clubs')
}

function goAdmin(): void {
  void router.push('/admin')
}

/* ---------------- 资料编辑 ---------------- */

const editVisible = ref(false)
const saving = ref(false)
const editForm = reactive({ name: '', email: '', avatar: '' })

function openEdit(): void {
  if (!profile.value) return
  editForm.name = profile.value.name
  editForm.email = profile.value.email
  editForm.avatar = profile.value.avatar
  editVisible.value = true
}

/** 只提交被修改且非空的字段：后端 Payload 拒绝 null，空串也会触发 1003 */
async function saveProfile(): Promise<void> {
  const current = profile.value
  if (!current) return
  const name = editForm.name.trim()
  const email = editForm.email.trim()
  const avatar = editForm.avatar.trim()
  if (!name) {
    ElMessage.warning('姓名不能为空')
    return
  }
  if (!email.includes('@')) {
    ElMessage.warning('邮箱格式不正确')
    return
  }
  const payload: { name?: string; email?: string; avatar?: string } = {}
  if (name !== current.name) payload.name = name
  if (email !== current.email) payload.email = email
  if (avatar && avatar !== current.avatar) payload.avatar = avatar
  if (!Object.keys(payload).length) {
    ElMessage.info('没有需要保存的修改')
    return
  }
  saving.value = true
  try {
    const updated = await updateProfile(payload)
    profile.value = updated
    userStore.userInfo = updated
    editVisible.value = false
    ElMessage.success('个人资料已更新')
  } catch {
    // 请求层已统一提示错误
  } finally {
    saving.value = false
  }
}

/* ---------------- 修改密码 ---------------- */

const passwordVisible = ref(false)
const changingPassword = ref(false)
const passwordForm = reactive({ oldPassword: '', newPassword: '', confirmPassword: '' })

function openPassword(): void {
  passwordForm.oldPassword = ''
  passwordForm.newPassword = ''
  passwordForm.confirmPassword = ''
  passwordVisible.value = true
}

/** 后端改密会吊销该用户全部会话，因此成功后清理本地登录态并回到登录页 */
async function submitPassword(): Promise<void> {
  if (!passwordForm.oldPassword) {
    ElMessage.warning('请输入原密码')
    return
  }
  if (passwordForm.newPassword.length < 6) {
    ElMessage.warning('新密码至少 6 位')
    return
  }
  if (passwordForm.newPassword !== passwordForm.confirmPassword) {
    ElMessage.warning('两次输入的新密码不一致')
    return
  }
  changingPassword.value = true
  try {
    await changePassword({
      oldPassword: passwordForm.oldPassword,
      newPassword: passwordForm.newPassword
    })
    passwordVisible.value = false
    ElMessage.success('密码已修改，请使用新密码重新登录')
    userStore.reset()
    void router.replace('/login')
  } catch {
    // 请求层已统一提示错误（1005 原密码不正确等）
  } finally {
    changingPassword.value = false
  }
}
</script>

<template>
  <div class="app-container">
    <h2 class="profile__title">个人中心</h2>

    <StateBlock :loading="loading" :error="errorMessage" @retry="loadAll">
      <div v-if="profile" class="profile__layout">
        <el-card class="profile__side" shadow="never">
          <div class="profile__identity">
            <span class="profile__avatar">{{ profile.avatar }}</span>
            <div>
              <div class="profile__name">{{ profile.name }}</div>
              <el-tag size="small" effect="dark" type="info">{{ roleLabel }}</el-tag>
            </div>
          </div>

          <el-descriptions :column="1" border size="small" class="profile__descriptions">
            <el-descriptions-item label="学号 / 账号">
              {{ profile.studentNo }}
            </el-descriptions-item>
            <el-descriptions-item label="邮箱">{{ profile.email }}</el-descriptions-item>
            <el-descriptions-item label="所属社团">
              {{ profile.clubName || '暂无' }}
            </el-descriptions-item>
          </el-descriptions>

          <div class="profile__actions">
            <el-button type="primary" plain @click="openEdit">编辑资料</el-button>
            <el-button plain @click="openPassword">修改密码</el-button>
          </div>
          <el-button
            v-if="profile.role === 'clubAdmin'"
            class="profile__admin-entry"
            text
            type="primary"
            @click="goAdmin"
          >
            进入社团管理后台 →
          </el-button>
        </el-card>

        <el-card class="profile__main" shadow="never">
          <el-tabs v-model="activeTab">
            <el-tab-pane name="applications">
              <template #label>
                我的入社申请
                <el-badge
                  v-if="pendingCount"
                  class="profile__badge"
                  :value="pendingCount"
                  type="warning"
                />
              </template>
              <el-table :data="applications" empty-text="还没有提交过入社申请">
                <el-table-column label="社团" min-width="140">
                  <template #default="{ row }">
                    <el-link type="primary" underline="never" @click="goClub(row.clubId)">
                      {{ row.clubName }}
                    </el-link>
                  </template>
                </el-table-column>
                <el-table-column prop="message" label="申请理由" min-width="200" show-overflow-tooltip>
                  <template #default="{ row }">{{ row.message || '（未填写）' }}</template>
                </el-table-column>
                <el-table-column label="状态" width="110">
                  <template #default="{ row }">
                    <el-tag :type="applicationTagType(row.status)" effect="light">
                      {{ applicationStatusLabel(row.status) }}
                    </el-tag>
                  </template>
                </el-table-column>
                <el-table-column label="提交时间" width="160">
                  <template #default="{ row }">{{ formatDateTime(row.createdAt) }}</template>
                </el-table-column>
                <el-table-column label="审核时间" width="160">
                  <template #default="{ row }">
                    {{ row.reviewedAt ? formatDateTime(row.reviewedAt) : '待审核' }}
                  </template>
                </el-table-column>
              </el-table>
              <div class="profile__pane-foot">
                <el-button text type="primary" @click="goClubPlaza">去社团广场看看 →</el-button>
              </div>
            </el-tab-pane>

            <el-tab-pane :label="`我的活动报名（${registrations.length}）`" name="registrations">
              <el-table :data="registrations" empty-text="还没有报名过活动">
                <el-table-column label="活动" min-width="200">
                  <template #default="{ row }">
                    <el-link type="primary" underline="never" @click="goActivity(row.activityId)">
                      {{ row.title }}
                    </el-link>
                  </template>
                </el-table-column>
                <el-table-column prop="clubName" label="主办社团" min-width="120" />
                <el-table-column label="开始时间" width="160">
                  <template #default="{ row }">{{ formatDateTime(row.startTime) }}</template>
                </el-table-column>
                <el-table-column label="报名状态" width="110">
                  <template #default="{ row }">
                    <el-tag :type="row.status === 'registered' ? 'success' : 'info'" effect="light">
                      {{ row.status === 'registered' ? '已报名' : '已取消' }}
                    </el-tag>
                  </template>
                </el-table-column>
                <el-table-column label="报名时间" width="160">
                  <template #default="{ row }">{{ formatDateTime(row.createdAt) }}</template>
                </el-table-column>
              </el-table>
            </el-tab-pane>

            <el-tab-pane :label="`活动足迹（${footprints.length}）`" name="footprints">
              <el-empty
                v-if="!footprints.length"
                description="参加并结束的活动会归档到这里"
                :image-size="80"
              />
              <el-timeline v-else class="profile__timeline">
                <el-timeline-item
                  v-for="item in footprints"
                  :key="item.id"
                  :timestamp="formatDate(item.finishedAt)"
                  placement="top"
                  type="primary"
                >
                  <div class="profile__footprint">
                    <el-link type="primary" underline="never" @click="goActivity(item.activityId)">
                      {{ item.title }}
                    </el-link>
                    <span class="profile__footprint-club">{{ item.clubName }}</span>
                  </div>
                </el-timeline-item>
              </el-timeline>
            </el-tab-pane>
          </el-tabs>
        </el-card>
      </div>
    </StateBlock>

    <el-dialog v-model="editVisible" title="编辑个人资料" width="420px">
      <el-form label-position="top" @submit.prevent="saveProfile">
        <el-form-item label="姓名">
          <el-input v-model="editForm.name" maxlength="100" placeholder="真实姓名" />
        </el-form-item>
        <el-form-item label="邮箱">
          <el-input v-model="editForm.email" maxlength="254" placeholder="name@campus.edu.cn" />
        </el-form-item>
        <el-form-item label="头像（emoji 或图片链接）">
          <el-input v-model="editForm.avatar" maxlength="2048" placeholder="例如 🧑‍🎓">
            <template #append>{{ editForm.avatar }}</template>
          </el-input>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="saveProfile">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="passwordVisible" title="修改密码" width="420px">
      <el-alert
        class="profile__password-tip"
        type="info"
        :closable="false"
        show-icon
        title="修改成功后当前登录会失效，需要用新密码重新登录。"
      />
      <el-form label-position="top" @submit.prevent="submitPassword">
        <el-form-item label="原密码">
          <el-input v-model="passwordForm.oldPassword" type="password" show-password />
        </el-form-item>
        <el-form-item label="新密码（至少 6 位）">
          <el-input v-model="passwordForm.newPassword" type="password" show-password />
        </el-form-item>
        <el-form-item label="确认新密码">
          <el-input v-model="passwordForm.confirmPassword" type="password" show-password />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="passwordVisible = false">取消</el-button>
        <el-button type="primary" :loading="changingPassword" @click="submitPassword">
          确认修改
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.profile__title {
  margin: 0 0 16px;
  font-size: 20px;
  font-weight: 600;
}

.profile__layout {
  display: grid;
  grid-template-columns: 320px 1fr;
  gap: 16px;
  align-items: start;
}

.profile__identity {
  display: flex;
  gap: 12px;
  align-items: center;
  margin-bottom: 16px;
}

.profile__avatar {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 56px;
  height: 56px;
  font-size: 28px;
  background: var(--app-color-primary-bg);
  border-radius: 50%;
}

.profile__name {
  margin-bottom: 6px;
  font-size: 16px;
  font-weight: 600;
}

.profile__descriptions {
  margin-bottom: 16px;
}

.profile__actions {
  display: flex;
  gap: 8px;
}

.profile__admin-entry {
  margin-top: 8px;
  padding-left: 0;
}

.profile__badge {
  margin-left: 6px;
}

.profile__pane-foot {
  margin-top: 8px;
}

.profile__timeline {
  padding-left: 4px;
}

.profile__footprint {
  display: flex;
  gap: 10px;
  align-items: center;
}

.profile__footprint-club {
  font-size: 12px;
  color: var(--app-color-text-secondary);
}

.profile__password-tip {
  margin-bottom: 12px;
}

@media (max-width: 992px) {
  .profile__layout {
    grid-template-columns: 1fr;
  }
}
</style>
