<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import { editAccount, getAccounts, setAccountStatus } from '@/api/admin'
import StateBlock from '@/components/StateBlock.vue'
import type { AdminAccount } from '@/types/admin'

const loading = ref(false)
const errorMessage = ref('')
const accounts = ref<AdminAccount[]>([])
const total = ref(0)
const page = ref(1)
const keyword = ref('')
const role = ref<'' | 'student' | 'clubAdmin'>('')
const active = ref<'' | 'active' | 'disabled'>('')
const editing = ref<AdminAccount | null>(null)
const dialogVisible = ref(false)
const saving = ref(false)
const busyId = ref('')
const formRef = ref<FormInstance>()
const form = reactive({ name: '', email: '' })
const rules: FormRules = {
  name: [
    {
      required: true,
      whitespace: true,
      max: 100,
      message: '请输入姓名（最多100字）',
      trigger: 'blur'
    }
  ],
  email: [{ required: true, type: 'email', max: 254, message: '请输入有效邮箱', trigger: 'blur' }]
}

async function loadData(): Promise<void> {
  loading.value = true
  errorMessage.value = ''
  try {
    const result = await getAccounts({
      page: page.value,
      pageSize: 10,
      keyword: keyword.value.trim(),
      role: role.value || undefined,
      isActive: active.value ? active.value === 'active' : undefined
    })
    accounts.value = result.list
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
function edit(user: AdminAccount): void {
  editing.value = user
  form.name = user.name
  form.email = user.email
  dialogVisible.value = true
}
async function save(): Promise<void> {
  if (!editing.value || !(await formRef.value?.validate().catch(() => false))) return
  saving.value = true
  try {
    await editAccount(editing.value.id, { name: form.name.trim(), email: form.email.trim() })
    dialogVisible.value = false
    ElMessage.success('账号资料已更新')
    await loadData()
  } catch {
    /* 请求层统一提示 */
  } finally {
    saving.value = false
  }
}
async function toggle(user: AdminAccount): Promise<void> {
  if (user.isActive && user.role === 'clubAdmin') {
    ElMessage.warning('请先完成社长交接，再禁用账号')
    return
  }
  try {
    await ElMessageBox.confirm(
      `${user.isActive ? '禁用' : '启用'} ${user.name}（${user.studentNo}）？${user.isActive ? '该账号将退出所有登录会话，历史记录保留。' : '启用后需要重新登录。'}`,
      '确认账号状态',
      { type: 'warning' }
    )
  } catch {
    return
  }
  busyId.value = user.id
  try {
    await setAccountStatus(user.id, !user.isActive)
    ElMessage.success('账号状态已更新')
    await loadData()
  } catch {
    /* 请求层统一提示 */
  } finally {
    busyId.value = ''
  }
}
onMounted(loadData)
</script>

<template>
  <el-card class="accounts-view">
    <h2 class="app-section-title">学生账号管理</h2>
    <p>管理学生与社长账号；学号和学籍白名单不在此修改。</p>
    <div class="accounts-view__filters">
      <el-input
        v-model="keyword"
        placeholder="搜索姓名、学号或邮箱"
        clearable
        @keyup.enter="search"
      />
      <el-select v-model="role" placeholder="全部角色" @change="search">
        <el-option label="全部角色" value="" /><el-option
          label="普通学生"
          value="student"
        /><el-option label="社长" value="clubAdmin" />
      </el-select>
      <el-select v-model="active" placeholder="全部状态" @change="search">
        <el-option label="全部状态" value="" /><el-option label="启用" value="active" /><el-option
          label="禁用"
          value="disabled"
        />
      </el-select>
      <el-button type="primary" @click="search">查询</el-button>
    </div>
    <StateBlock
      :loading="loading"
      :error="errorMessage"
      :empty="accounts.length === 0"
      @retry="loadData"
    >
      <el-table :data="accounts" row-key="id">
        <el-table-column prop="name" label="姓名" min-width="90" />
        <el-table-column prop="studentNo" label="学号" min-width="110" />
        <el-table-column prop="email" label="邮箱" min-width="200" />
        <el-table-column label="角色" width="100"
          ><template #default="{ row }">{{
            row.role === 'clubAdmin' ? '社长' : '学生'
          }}</template></el-table-column
        >
        <el-table-column label="管理社团" min-width="120"
          ><template #default="{ row }">{{ row.clubName || '—' }}</template></el-table-column
        >
        <el-table-column label="状态" width="80"
          ><template #default="{ row }"
            ><el-tag :type="row.isActive ? 'success' : 'danger'">{{
              row.isActive ? '启用' : '禁用'
            }}</el-tag></template
          ></el-table-column
        >
        <el-table-column label="操作" width="155"
          ><template #default="{ row }">
            <el-button link type="primary" @click="edit(row)">编辑</el-button>
            <el-button
              link
              :type="row.isActive ? 'danger' : 'success'"
              :loading="busyId === row.id"
              :disabled="busyId !== ''"
              @click="toggle(row)"
              >{{ row.isActive ? '禁用' : '启用' }}</el-button
            >
          </template></el-table-column
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
      title="编辑账号资料"
      width="min(500px, 95vw)"
      :close-on-click-modal="!saving"
      :show-close="!saving"
    >
      <el-form ref="formRef" :model="form" :rules="rules" label-width="70px">
        <el-form-item label="姓名" prop="name"
          ><el-input v-model="form.name" maxlength="100"
        /></el-form-item>
        <el-form-item label="邮箱" prop="email"
          ><el-input v-model="form.email" maxlength="254"
        /></el-form-item>
      </el-form>
      <template #footer
        ><el-button :disabled="saving" @click="dialogVisible = false">取消</el-button
        ><el-button type="primary" :loading="saving" @click="save">保存</el-button></template
      >
    </el-dialog>
  </el-card>
</template>

<style scoped>
.accounts-view__filters {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-bottom: 20px;
}
.accounts-view__filters .el-input {
  width: 260px;
}
.accounts-view__filters .el-select {
  width: 140px;
}
.accounts-view .el-pagination {
  margin-top: 20px;
}
</style>
