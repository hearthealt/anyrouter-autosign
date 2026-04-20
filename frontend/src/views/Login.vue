<template>
  <div class="login-page">
    <div class="login-card">
      <div class="login-brand">
        <div class="brand-mark">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
            <path d="M12 2L2 7L12 12L22 7L12 2Z" fill="currentColor"/>
            <path d="M2 17L12 22L22 17" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="M2 12L12 17L22 12" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
        </div>
        <span class="brand-text">AnyRouter</span>
      </div>

      <div class="login-header">
        <h1>登录控制台</h1>
        <p>输入管理账号进入工作区</p>
      </div>

      <div class="login-form">
        <div class="field">
          <label>用户名</label>
          <n-input
            v-model:value="form.username"
            placeholder="请输入用户名"
            size="medium"
            autofocus
            @keyup.enter="handleLogin"
          >
            <template #prefix>
              <n-icon :size="14"><PersonOutline /></n-icon>
            </template>
          </n-input>
        </div>

        <div class="field">
          <label>密码</label>
          <n-input
            v-model:value="form.password"
            type="password"
            show-password-on="click"
            placeholder="请输入密码"
            size="medium"
            @keyup.enter="handleLogin"
          >
            <template #prefix>
              <n-icon :size="14"><LockClosedOutline /></n-icon>
            </template>
          </n-input>
        </div>

        <n-button
          type="primary"
          :loading="loading"
          block
          size="medium"
          @click="handleLogin"
        >
          登录
        </n-button>
      </div>

      <div class="login-footer">
        <span>AnyRouter · 多账号签到管理</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { PersonOutline, LockClosedOutline } from '@vicons/ionicons5'
import { authApi } from '../api'
import { setToken } from '../utils/auth'

const router = useRouter()

const loading = ref(false)
const form = ref({
  username: '',
  password: ''
})

const handleLogin = async () => {
  if (!form.value.username.trim()) {
    window.$notify('请输入用户名', 'warning')
    return
  }
  if (!form.value.password.trim()) {
    window.$notify('请输入密码', 'warning')
    return
  }

  loading.value = true
  try {
    const res: any = await authApi.login({
      username: form.value.username,
      password: form.value.password
    })

    if (res.success && res.data?.access_token) {
      setToken(res.data.access_token)
      window.$notify('登录成功', 'success')
      router.push('/')
    } else {
      window.$notify(res.message || '登录失败', 'error')
    }
  } catch (e: any) {
    window.$notify(e.message || '登录失败', 'error')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  display: grid;
  place-items: center;
  padding: var(--spacing-6);
  background: var(--bg-color);
}

.login-card {
  width: min(100%, 380px);
  padding: var(--spacing-8);
  background: var(--bg-card);
  border: 1px solid var(--border-color-light);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-lg);
  display: flex;
  flex-direction: column;
  gap: var(--spacing-5);
}

.login-brand {
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
}

.brand-mark {
  display: grid;
  place-items: center;
  width: 28px;
  height: 28px;
  border-radius: var(--radius-sm);
  background: var(--primary-color);
  color: var(--text-inverse);
}

.brand-text {
  font-family: var(--font-display);
  font-size: var(--text-md);
  font-weight: var(--font-semibold);
  letter-spacing: -0.01em;
  color: var(--text-primary);
}

.login-header h1 {
  margin: 0;
  font-size: var(--text-xl);
  font-weight: var(--font-semibold);
  letter-spacing: -0.01em;
  color: var(--text-primary);
}

.login-header p {
  margin: 4px 0 0;
  font-size: var(--text-sm);
  color: var(--text-tertiary);
}

.login-form {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-3);
}

.field {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.field label {
  font-size: var(--text-xs);
  font-weight: var(--font-medium);
  color: var(--text-secondary);
}

.login-footer {
  padding-top: var(--spacing-4);
  border-top: 1px solid var(--border-color-light);
  text-align: center;
  color: var(--text-quaternary);
  font-size: var(--text-xs);
}

@media (max-width: 480px) {
  .login-card {
    padding: var(--spacing-5);
  }
}
</style>
