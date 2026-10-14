<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import { changePassword } from '@/api/user'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const userStore = useUserStore()
const formRef = ref<FormInstance>()
const loading = ref(false)
const form = reactive({ oldPassword: '', newPassword: '', confirmPassword: '' })
const rules: FormRules = {
  oldPassword: [{ required: true, message: '请输入原密码', trigger: 'blur' }],
  newPassword: [
    { required: true, min: 6, max: 128, message: '新密码长度为6～128位', trigger: 'blur' }
  ],
  confirmPassword: [
    {
      validator: (_rule, value: string, callback) => {
        if (!value || value !== form.newPassword) callback(new Error('两次新密码必须一致'))
        else callback()
      },
      trigger: 'blur'
    }
  ]
}
async function submit(): Promise<void> {
  if (!(await formRef.value?.validate().catch(() => false))) return
  loading.value = true
  try {
    await changePassword({ oldPassword: form.oldPassword, newPassword: form.newPassword })
    userStore.reset()
    ElMessage.success('密码已修改，请重新登录')
    await router.push('/login')
  } catch {
    /* 请求层统一提示 */
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="app-container password-view">
    <el-card
      ><h2 class="app-section-title">修改本人密码</h2>
      <p>修改成功后，所有设备上的登录会话都会失效。</p>
      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-width="90px"
        @submit.prevent="submit"
      >
        <el-form-item label="原密码" prop="oldPassword"
          ><el-input
            v-model="form.oldPassword"
            type="password"
            show-password
            autocomplete="current-password"
        /></el-form-item>
        <el-form-item label="新密码" prop="newPassword"
          ><el-input
            v-model="form.newPassword"
            type="password"
            show-password
            autocomplete="new-password"
        /></el-form-item>
        <el-form-item label="确认密码" prop="confirmPassword"
          ><el-input
            v-model="form.confirmPassword"
            type="password"
            show-password
            autocomplete="new-password"
        /></el-form-item>
        <el-form-item
          ><el-button type="primary" native-type="submit" :loading="loading"
            >保存新密码</el-button
          ></el-form-item
        >
      </el-form>
    </el-card>
  </div>
</template>

<style scoped>
.password-view {
  max-width: 600px;
}
</style>
