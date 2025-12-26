<template>
  <div class="login-page">
    <!-- 左侧品牌区 -->
    <div class="login-brand">
      <div class="brand-bg"></div>
      <div class="brand-content">
        <div class="brand-logo">
          <svg width="32" height="32" viewBox="0 0 24 24" fill="none">
            <path d="M12 2L2 7L12 12L22 7L12 2Z" fill="currentColor" opacity="0.9"/>
            <path d="M2 17L12 22L22 17" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="M2 12L12 17L22 12" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
        </div>
        <h1 class="brand-title">AnyRouter</h1>
        <p class="brand-subtitle">多账号自动签到管理平台</p>

        <div class="brand-features">
          <div class="feature-item">
            <div class="feature-icon">
              <n-icon :size="18"><CheckmarkCircleOutline /></n-icon>
            </div>
            <div class="feature-text">
              <span class="feature-title">多账号管理</span>
              <span class="feature-desc">统一管理多个账号</span>
            </div>
          </div>
          <div class="feature-item">
            <div class="feature-icon">
              <n-icon :size="18"><CheckmarkCircleOutline /></n-icon>
            </div>
            <div class="feature-text">
              <span class="feature-title">自动签到</span>
              <span class="feature-desc">定时自动执行签到</span>
            </div>
          </div>
          <div class="feature-item">
            <div class="feature-icon">
              <n-icon :size="18"><CheckmarkCircleOutline /></n-icon>
            </div>
            <div class="feature-text">
              <span class="feature-title">消息推送</span>
              <span class="feature-desc">多渠道签到通知</span>
            </div>
          </div>
        </div>
      </div>
      <div class="brand-footer">
        <span>© 2024 AnyRouter. All rights reserved.</span>
      </div>
    </div>

    <!-- 右侧登录区 -->
    <div class="login-form-area">
      <div class="form-container">
        <div class="form-header">
          <h2>欢迎回来</h2>
          <p>请登录您的管理账号</p>
        </div>

        <div class="form-body">
          <div class="form-group">
            <label>用户名</label>
            <div class="input-box">
              <n-icon class="input-prefix" :size="18"><PersonOutline /></n-icon>
              <input
                v-model="form.username"
                type="text"
                placeholder="请输入用户名"
                @keyup.enter="handleLogin"
              />
            </div>
          </div>

          <div class="form-group">
            <label>密码</label>
            <div class="input-box">
              <n-icon class="input-prefix" :size="18"><LockClosedOutline /></n-icon>
              <input
                v-model="form.password"
                :type="showPassword ? 'text' : 'password'"
                placeholder="请输入密码"
                @keyup.enter="handleLogin"
              />
              <n-icon
                class="input-suffix"
                :size="18"
                @click="showPassword = !showPassword"
              >
                <EyeOutline v-if="!showPassword" />
                <EyeOffOutline v-else />
              </n-icon>
            </div>
          </div>

          <button class="btn-submit" :disabled="loading" @click="handleLogin">
            <template v-if="!loading">登 录</template>
            <template v-else>
              <span class="btn-loading"></span>
              登录中...
            </template>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useMessage } from 'naive-ui'
import { PersonOutline, LockClosedOutline, EyeOutline, EyeOffOutline, CheckmarkCircleOutline } from '@vicons/ionicons5'
import { authApi } from '../api'
import { setToken } from '../utils/auth'

const router = useRouter()
const message = useMessage()

const loading = ref(false)
const showPassword = ref(false)
const form = ref({
  username: '',
  password: ''
})

const handleLogin = async () => {
  if (!form.value.username.trim()) {
    message.warning('请输入用户名')
    return
  }
  if (!form.value.password.trim()) {
    message.warning('请输入密码')
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
      message.success('登录成功')
      router.push('/')
    } else {
      message.error(res.message || '登录失败')
    }
  } catch (e: any) {
    message.error(e.message || '登录失败')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  background: var(--bg-color);
}

/* 左侧品牌区 */
.login-brand {
  width: 45%;
  min-width: 400px;
  background: linear-gradient(135deg, #00b38a 0%, #009e7a 100%);
  display: flex;
  flex-direction: column;
  justify-content: center;
  padding: 60px;
  position: relative;
  overflow: hidden;
}

.brand-bg {
  position: absolute;
  inset: 0;
  background:
    radial-gradient(circle at 20% 80%, rgba(255,255,255,0.1) 0%, transparent 50%),
    radial-gradient(circle at 80% 20%, rgba(255,255,255,0.08) 0%, transparent 40%);
}

.brand-content {
  position: relative;
  z-index: 1;
}

.brand-logo {
  width: 64px;
  height: 64px;
  background: rgba(255,255,255,0.2);
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  margin-bottom: 24px;
  backdrop-filter: blur(10px);
}

.brand-title {
  font-size: 36px;
  font-weight: 700;
  color: white;
  margin: 0 0 8px;
  letter-spacing: -0.5px;
}

.brand-subtitle {
  font-size: 16px;
  color: rgba(255,255,255,0.8);
  margin: 0 0 48px;
}

.brand-features {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.feature-item {
  display: flex;
  align-items: flex-start;
  gap: 14px;
}

.feature-icon {
  width: 36px;
  height: 36px;
  background: rgba(255,255,255,0.15);
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  flex-shrink: 0;
}

.feature-text {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.feature-title {
  font-size: 15px;
  font-weight: 600;
  color: white;
}

.feature-desc {
  font-size: 13px;
  color: rgba(255,255,255,0.7);
}

.brand-footer {
  position: absolute;
  bottom: 32px;
  left: 60px;
  right: 60px;
}

.brand-footer span {
  font-size: 12px;
  color: rgba(255,255,255,0.5);
}

/* 右侧登录区 */
.login-form-area {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px;
}

.form-container {
  width: 100%;
  max-width: 380px;
}

.form-header {
  margin-bottom: 36px;
}

.form-header h2 {
  font-size: 28px;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0 0 8px;
}

.form-header p {
  font-size: 15px;
  color: var(--text-tertiary);
  margin: 0;
}

.form-body {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.form-group label {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-secondary);
}

.input-box {
  position: relative;
  display: flex;
  align-items: center;
}

.input-prefix {
  position: absolute;
  left: 14px;
  color: var(--text-tertiary);
  pointer-events: none;
  transition: color 0.2s;
}

.input-suffix {
  position: absolute;
  right: 14px;
  color: var(--text-tertiary);
  cursor: pointer;
  transition: color 0.2s;
}

.input-suffix:hover {
  color: var(--text-secondary);
}

.input-box input {
  width: 100%;
  height: 50px;
  padding: 0 44px;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  color: var(--text-primary);
  font-size: 15px;
  outline: none;
  transition: all 0.2s;
}

.input-box input::placeholder {
  color: var(--text-placeholder);
}

.input-box input:focus {
  border-color: #00b38a;
  box-shadow: 0 0 0 3px rgba(0, 179, 138, 0.1);
}

.input-box:focus-within .input-prefix {
  color: #00b38a;
}

.btn-submit {
  height: 50px;
  margin-top: 8px;
  background: linear-gradient(135deg, #00b38a 0%, #00c99b 100%);
  border: none;
  border-radius: 12px;
  color: white;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  transition: all 0.2s;
}

.btn-submit:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 8px 20px rgba(0, 179, 138, 0.35);
}

.btn-submit:active:not(:disabled) {
  transform: translateY(0);
}

.btn-submit:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.btn-loading {
  width: 18px;
  height: 18px;
  border: 2px solid rgba(255,255,255,0.3);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* 响应式 */
@media (max-width: 900px) {
  .login-brand {
    display: none;
  }

  .login-form-area {
    padding: 24px;
  }

  .form-header h2 {
    font-size: 24px;
  }
}
</style>
