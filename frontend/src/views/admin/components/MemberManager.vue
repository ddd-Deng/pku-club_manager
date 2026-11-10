<script setup lang="ts">
import { ElMessage, ElMessageBox } from 'element-plus'
import { onMounted, ref } from 'vue'

import { getClubMembers, updateClubMember } from '@/api/club'
import StateBlock from '@/components/StateBlock.vue'
import type { ClubMember } from '@/types/club'
import { formatDateTime } from '@/utils/format'

/** 后台「成员权限管理」分区：owner 不可变更/移除 */
const props = defineProps<{ clubId: string }>()

const ROLE_LABELS: Record<string, string> = {
  owner: '社长',
  officer: '骨干',
  member: '成员'
}

const loading = ref(false)
const errorMessage = ref('')
const members = ref<ClubMember[]>([])
const submitting = ref(false)

function tagType(role: string): 'primary' | 'warning' | 'info' {
  if (role === 'owner') return 'primary'
  if (role === 'officer') return 'warning'
  return 'info'
}

async function load(): Promise<void> {
  loading.value = true
  errorMessage.value = ''
  try {
    members.value = await getClubMembers(props.clubId)
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '加载失败'
  } finally {
    loading.value = false
  }
}

onMounted(load)

async function changeRole(member: ClubMember, role: 'member' | 'officer' | ''): Promise<void> {
  if (!role) return
  submitting.value = true
  try {
    await updateClubMember(props.clubId, member.id, { role })
    ElMessage.success('成员角色已更新')
    await load()
  } catch {
    // 请求层已统一提示错误
  } finally {
    submitting.value = false
  }
}

async function remove(member: ClubMember): Promise<void> {
  try {
    await ElMessageBox.confirm(`确定将 ${member.name} 移出社团吗？`, '移除成员', {
      confirmButtonText: '移除',
      cancelButtonText: '取消',
      type: 'warning'
    })
  } catch {
    return
  }
  submitting.value = true
  try {
    await updateClubMember(props.clubId, member.id, { action: 'remove' })
    ElMessage.success('成员已移除')
    await load()
  } catch {
    // 请求层已统一提示错误
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <StateBlock :loading="loading" :error="errorMessage" @retry="load">
    <el-table :data="members" empty-text="暂无成员">
      <el-table-column prop="name" label="姓名" width="140" />
      <el-table-column label="角色" width="130">
        <template #default="{ row }">
          <el-tag :type="tagType(row.role)" effect="light">{{ ROLE_LABELS[row.role] }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="加入时间" width="160">
        <template #default="{ row }">{{ formatDateTime(row.joinedAt) }}</template>
      </el-table-column>
      <el-table-column label="操作" min-width="180">
        <template #default="{ row }">
          <template v-if="row.role !== 'owner'">
            <el-select
              :model-value="row.role"
              size="small"
              class="member-manager__role-select"
              :disabled="submitting"
              @change="(value: string) => changeRole(row, value as 'member' | 'officer')"
            >
              <el-option label="成员" value="member" />
              <el-option label="骨干" value="officer" />
            </el-select>
            <el-button
              size="small"
              text
              type="danger"
              :disabled="submitting"
              @click="remove(row)"
            >
              移除
            </el-button>
          </template>
          <span v-else class="member-manager__owner">社长不可变更</span>
        </template>
      </el-table-column>
    </el-table>
  </StateBlock>
</template>

<style scoped>
.member-manager__role-select {
  width: 100px;
  margin-right: 8px;
}

.member-manager__owner {
  font-size: 12px;
  color: var(--app-color-text-placeholder);
}
</style>
