<script setup lang="ts">
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { isMockEnabled } from '@/mock'
import { DEMO_ACCOUNTS } from '@/mock/db'
import { useUserStore } from '@/stores/user'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const loginFormRef = ref<FormInstance>()
const registerFormRef = ref<FormInstance>()
const registerSectionRef = ref<HTMLElement>()
const loginLoading = ref(false)
const registerLoading = ref(false)

const loginForm = reactive({ account: '', password: '', remember: true })
const registerForm = reactive({ name: '', studentNo: '', email: '', password: '' })

const loginRules: FormRules = {
  account: [{ required: true, message: '请输入学号 / 邮箱', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }]
}

const registerRules: FormRules = {
  name: [{ required: true, message: '请输入姓名', trigger: 'blur' }],
  studentNo: [{ required: true, message: '请输入学号', trigger: 'blur' }],
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '邮箱格式不正确', trigger: 'blur' }
  ],
  password: [{ required: true, min: 6, message: '密码至少 6 位', trigger: 'blur' }]
}

function redirectAfterLogin(): void {
  const redirect = route.query.redirect
  void router.push(typeof redirect === 'string' && redirect ? redirect : '/')
}

async function handleLogin(): Promise<void> {
  const form = loginFormRef.value
  if (!form) {
    return
  }
  const valid = await form.validate().catch(() => false)
  if (!valid) {
    return
  }
  loginLoading.value = true
  try {
    const user = await userStore.login({
      account: loginForm.account,
      password: loginForm.password,
      remember: loginForm.remember
    })
    ElMessage.success(`欢迎回来，${user.name}`)
    redirectAfterLogin()
  } catch {
    // 错误提示由请求层统一处理
  } finally {
    loginLoading.value = false
  }
}

async function handleRegister(): Promise<void> {
  const form = registerFormRef.value
  if (!form) {
    return
  }
  const valid = await form.validate().catch(() => false)
  if (!valid) {
    return
  }
  registerLoading.value = true
  try {
    const user = await userStore.register({ ...registerForm })
    ElMessage.success(`注册成功，欢迎你，${user.name}`)
    redirectAfterLogin()
  } catch {
    // 错误提示由请求层统一处理
  } finally {
    registerLoading.value = false
  }
}

function fillDemo(account: string, password: string): void {
  loginForm.account = account
  loginForm.password = password
}

function handleForgot(): void {
  ElMessage.info('密码找回将在后续迭代开放；演示阶段可直接使用下方演示账号')
}

function scrollToRegister(): void {
  registerSectionRef.value?.scrollIntoView({ behavior: 'smooth', block: 'center' })
}
</script>

<template>
  <div class="login-view">
    <div class="login-view__inner">
      <section class="login-view__slogan">
        <h1>一个账号，<br />访问全校社团与活动</h1>
        <p>统一身份登录 · 学生身份校验 · 社团 / 活动 / 通知一站管理</p>
      </section>

      <section class="login-view__forms">
        <el-card class="login-view__card">
          <h2 class="login-view__card-title">统一账号登录</h2>
          <el-form
            ref="loginFormRef"
            :model="loginForm"
            :rules="loginRules"
            label-position="top"
            @submit.prevent="handleLogin"
          >
            <el-form-item prop="account">
              <el-input v-model="loginForm.account" placeholder="学号 / 邮箱" size="large" />
            </el-form-item>
            <el-form-item prop="password">
              <el-input
                v-model="loginForm.password"
                placeholder="密码"
                type="password"
                size="large"
                show-password
                @keyup.enter="handleLogin"
              />
            </el-form-item>
            <el-form-item>
              <el-checkbox v-model="loginForm.remember">记住登录状态</el-checkbox>
            </el-form-item>
            <el-button type="primary" size="large" :loading="loginLoading" @click="handleLogin">
              登录
            </el-button>
            <div class="login-view__links">
              <el-link type="primary" underline="never" @click="handleForgot">忘记密码</el-link>
              <el-link type="primary" underline="never" @click="scrollToRegister">
                注册新账号
              </el-link>
            </div>
          </el-form>

          <div v-if="isMockEnabled()" class="login-view__demo">
            <span class="login-view__demo-label">演示账号一键填充：</span>
            <el-button
              v-for="account in DEMO_ACCOUNTS"
              :key="account.role"
              size="small"
              round
              @click="fillDemo(account.account, account.password)"
            >
              {{ account.label }} {{ account.account }}
            </el-button>
          </div>
        </el-card>

        <div ref="registerSectionRef">
          <el-card class="login-view__card">
            <h2 class="login-view__card-title">注册账号</h2>
            <el-form
              ref="registerFormRef"
              :model="registerForm"
              :rules="registerRules"
              label-position="top"
              @submit.prevent="handleRegister"
            >
              <div class="login-view__grid">
                <el-form-item label="姓名" prop="name">
                  <el-input v-model="registerForm.name" placeholder="姓名" />
                </el-form-item>
                <el-form-item label="学号" prop="studentNo">
                  <el-input v-model="registerForm.studentNo" placeholder="学号" />
                </el-form-item>
                <el-form-item label="邮箱" prop="email">
                  <el-input v-model="registerForm.email" placeholder="邮箱" />
                </el-form-item>
                <el-form-item label="设置密码" prop="password">
                  <el-input
                    v-model="registerForm.password"
                    placeholder="设置密码"
                    type="password"
                    show-password
                  />
                </el-form-item>
              </div>
              <el-button
                type="primary"
                size="large"
                :loading="registerLoading"
                @click="handleRegister"
              >
                立即注册
              </el-button>
            </el-form>
          </el-card>
        </div>
      </section>
    </div>
  </div>
</template>

<style scoped>
.login-view {
  min-height: calc(100vh - var(--app-navbar-height));
  padding: 48px 16px;
  background: linear-gradient(180deg, #dceafe 0%, var(--app-color-bg) 60%);
}

.login-view__inner {
  display: flex;
  gap: 48px;
  align-items: flex-start;
  justify-content: center;
  max-width: 1080px;
  margin: 0 auto;
}

.login-view__slogan {
  flex: 1;
  padding-top: 48px;
}

.login-view__slogan h1 {
  margin: 0 0 16px;
  font-size: 36px;
  line-height: 1.3;
  color: var(--app-color-primary-dark);
}

.login-view__slogan p {
  font-size: 15px;
  color: var(--app-color-text-secondary);
}

.login-view__forms {
  display: flex;
  flex-direction: column;
  gap: 20px;
  width: 420px;
}

.login-view__card-title {
  margin: 0 0 16px;
  font-size: 18px;
}

.login-view__card .el-button--primary {
  width: 100%;
}

.login-view__links {
  display: flex;
  justify-content: flex-end;
  gap: 16px;
  margin-top: 12px;
}

.login-view__grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0 16px;
}

.login-view__demo {
  padding-top: 12px;
  margin-top: 4px;
  border-top: 1px dashed var(--app-color-border);
}

.login-view__demo-label {
  margin-right: 8px;
  font-size: 12px;
  color: var(--app-color-text-secondary);
}

@media (max-width: 992px) {
  .login-view__slogan {
    display: none;
  }
}
</style>
