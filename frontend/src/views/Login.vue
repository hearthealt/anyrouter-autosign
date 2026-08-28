<template>
  <div class="login-page material-grid">
    <SignalField class="login-field" :density="28" :intensity="0.48" />
    <div class="login-aura login-aura--one" aria-hidden="true" />
    <div class="login-aura login-aura--two" aria-hidden="true" />
    <div class="login-noise" aria-hidden="true" />

    <main class="login-layout">
      <section class="login-intro" aria-labelledby="login-intro-title">
        <div class="login-intro__topline">
          <span class="mono">ANYROUTER / AUTH NODE</span>
          <span class="login-intro__live"><i aria-hidden="true" /> LINK READY</span>
        </div>

        <div class="login-intro__copy">
          <div class="login-kicker"><span class="login-kicker__line" /> ACCESS / 01</div>
          <h1 id="login-intro-title">让自动化<br /><em>持续在场。</em></h1>
          <p>
            一个为多账号签到而生的实时控制面。把状态、额度与每一次任务回执，收进同一块清晰的仪表面。
          </p>
        </div>

        <div class="login-readouts" aria-label="系统状态">
          <div class="login-readout">
            <Activity :size="15" :stroke-width="1.7" />
            <span><small>RUNTIME</small><strong>REALTIME</strong></span>
          </div>
          <div class="login-readout">
            <ShieldCheck :size="15" :stroke-width="1.7" />
            <span><small>ACCESS</small><strong>ENCRYPTED</strong></span>
          </div>
          <div class="login-readout login-readout--index">
            <span class="mono">NODE</span><strong class="mono">AR-01</strong>
          </div>
        </div>

        <div class="login-intro__footer">
          <span class="mono">SIGNAL / 2026</span>
          <span class="login-intro__footer-line" aria-hidden="true" />
          <span class="mono">KEEP IT RUNNING</span>
        </div>
      </section>

      <section class="login-card material-noise" aria-labelledby="login-title">
        <div class="login-card__brand">
          <div class="brand-mark" aria-hidden="true"><Layers3 :size="19" :stroke-width="1.8" /></div>
          <div>
            <span class="brand-eyebrow mono">AUTOMATION / 01</span>
            <span class="brand-text">AnyRouter</span>
          </div>
        </div>

        <div class="login-header">
          <div class="login-header__code mono">CONTROL PLANE <span>///</span> SIGN IN</div>
          <h2 id="login-title">登录控制台</h2>
          <p>输入管理账号，进入你的自动化工作区。</p>
        </div>

        <form class="login-form" @submit.prevent="handleLogin">
          <div class="field">
            <label for="login-username">用户名</label>
            <UiInput
              id="login-username"
              v-model:value="form.username"
              placeholder="请输入用户名"
              size="medium"
              autofocus
              autocomplete="username"
              @update:value="loginError = ''"
            >
              <template #prefix><User :size="15" :stroke-width="1.8" /></template>
            </UiInput>
          </div>

          <div class="field">
            <label for="login-password">密码</label>
            <UiInput
              id="login-password"
              v-model:value="form.password"
              type="password"
              show-password-on="click"
              placeholder="请输入密码"
              size="medium"
              autocomplete="current-password"
              @update:value="loginError = ''"
            >
              <template #prefix><Lock :size="15" :stroke-width="1.8" /></template>
            </UiInput>
          </div>

          <div v-if="loginError" class="login-error" role="alert">
            <AlertCircle :size="15" :stroke-width="2" />
            <span>{{ loginError }}</span>
          </div>

          <UiButton type="primary" :loading="loading" block size="large" native-type="submit" class="login-submit">
            <template #icon><ArrowUpRight :size="16" :stroke-width="2" /></template>
            进入工作区
          </UiButton>
        </form>

        <div class="login-card__footer">
          <span>安全连接已建立</span>
          <span class="login-card__footer-status"><i aria-hidden="true" /> SECURE SESSION</span>
        </div>
      </section>
    </main>

    <div class="login-corner login-corner--left mono">01 / AUTH</div>
    <div class="login-corner login-corner--right mono">v2.0 / ONLINE</div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { Activity, AlertCircle, ArrowUpRight, Layers3, Lock, ShieldCheck, User } from 'lucide-vue-next'
import { UiButton, UiInput } from '../ui'
import SignalField from '../components/layout/SignalField.vue'
import { authApi } from '../api'
import { setToken } from '../utils/auth'
import { apiError } from '../utils/apiError'

const router = useRouter()

const loading = ref(false)
const loginError = ref('')
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
  loginError.value = ''
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
      const message = res.message || '登录失败'
      loginError.value = message
      window.$notify(message, 'error')
    }
  } catch (e: unknown) {
    const message = apiError(e, '用户名或密码错误')
    loginError.value = message
    window.$notify(message, 'error')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-page {
  position: relative;
  display: grid;
  min-height: 100vh;
  min-height: 100dvh;
  height: 100dvh;
  overflow: hidden;
  place-items: center;
  padding: clamp(22px, 5vw, 72px);
  background-color: var(--surface-page);
  color: var(--ink-max);
  isolation: isolate;
}

.login-page::before {
  position: absolute;
  inset: 0;
  z-index: -1;
  content: '';
  background: radial-gradient(circle at 72% 43%, color-mix(in srgb, var(--signal) 10%, transparent), transparent 30%), linear-gradient(135deg, transparent 0 47%, color-mix(in srgb, var(--line) 42%, transparent) 47.1%, transparent 47.25%);
  pointer-events: none;
}

.login-field {
  position: fixed;
  inset: 0;
  z-index: -2;
  opacity: 0.68;
}

.login-aura {
  position: fixed;
  z-index: -1;
  width: min(44vw, 620px);
  aspect-ratio: 1;
  border: 1px solid color-mix(in srgb, var(--signal) 13%, transparent);
  border-radius: 50%;
  pointer-events: none;
}

.login-aura::before,
.login-aura::after {
  position: absolute;
  inset: 14%;
  border: inherit;
  border-radius: inherit;
  content: '';
}

.login-aura::after { inset: 30%; border-color: color-mix(in srgb, var(--signal) 22%, transparent); }
.login-aura--one { top: -26%; right: -12%; transform: rotate(22deg); }
.login-aura--two { bottom: -44%; left: -14%; transform: rotate(-18deg) scale(0.72); opacity: 0.55; }

.login-noise { position: fixed; inset: 0; z-index: -1; opacity: 0.22; pointer-events: none; }
.login-layout {
  display: grid;
  grid-template-columns: minmax(300px, 0.92fr) minmax(360px, 440px);
  align-items: center;
  width: min(100%, 1120px);
  gap: clamp(52px, 10vw, 160px);
}

.login-intro { display: flex; min-height: min(640px, 72vh); flex-direction: column; justify-content: space-between; padding: 12px 0; }
.login-intro__topline,
.login-intro__footer { display: flex; align-items: center; gap: 12px; color: var(--ink-faint); font-size: 9px; letter-spacing: 0.13em; }
.login-intro__topline { justify-content: space-between; }
.login-intro__live { display: inline-flex; align-items: center; gap: 6px; color: var(--ok); }
.login-intro__live i,
.login-card__footer-status i { width: 5px; height: 5px; border-radius: 50%; background: currentColor; box-shadow: 0 0 12px currentColor; }
.login-intro__copy { max-width: 600px; padding: 10vh 0 8vh; }
.login-kicker { display: flex; align-items: center; gap: 9px; margin-bottom: 20px; color: var(--signal-deep); font-family: var(--font-mono); font-size: 10px; font-weight: var(--weight-semibold); letter-spacing: 0.16em; }
.login-kicker__line { width: 32px; height: 1px; background: var(--signal-deep); }
.login-intro h1 { margin: 0; font-size: clamp(4.5rem, 8.7vw, 9.2rem); font-weight: var(--weight-semibold); letter-spacing: -0.1em; line-height: 0.82; }
.login-intro h1 em { color: var(--signal-deep); font-style: normal; }
.login-intro__copy p { max-width: 400px; margin: 34px 0 0; color: var(--ink-muted); font-size: clamp(13px, 1.3vw, 16px); line-height: 1.8; }
.login-readouts { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); max-width: 560px; border-block: 1px solid var(--line-faint); }
.login-readout { display: flex; align-items: center; gap: 9px; min-width: 0; padding: 13px 15px 13px 0; color: var(--signal-deep); }
.login-readout + .login-readout { padding-left: 15px; border-left: 1px solid var(--line-faint); }
.login-readout span:not(.mono) { display: grid; gap: 2px; min-width: 0; }
.login-readout small { color: var(--ink-faint); font-size: 8px; letter-spacing: 0.1em; }
.login-readout strong { overflow: hidden; color: var(--ink-strong); font-size: 10px; letter-spacing: 0.08em; text-overflow: ellipsis; }
.login-readout--index { display: grid; justify-items: end; align-content: center; text-align: right; color: var(--ink-faint); }
.login-readout--index strong { color: var(--ink-max); }
.login-intro__footer-line { flex: 1; height: 1px; background: var(--line-faint); }

.login-card { position: relative; display: flex; flex-direction: column; gap: 32px; padding: clamp(24px, 4vw, 44px); border: 1px solid var(--line); border-radius: 25px; background: color-mix(in srgb, var(--surface-raised) 82%, transparent); box-shadow: var(--lift-4), 0 0 80px -42px var(--signal-glow); backdrop-filter: blur(24px); }
.login-card::before { position: absolute; inset: 0 0 auto; height: 2px; border-radius: 25px 25px 0 0; background: linear-gradient(90deg, var(--signal-deep), transparent 72%); content: ''; }
.login-card__brand { display: flex; align-items: center; gap: 11px; }
.brand-mark { display: grid; width: 34px; height: 34px; place-items: center; border: 1px solid var(--signal-deep); border-radius: 11px; background: var(--signal); color: var(--signal-ink); box-shadow: 0 0 24px -9px var(--signal-glow); }
.login-card__brand > div:last-child { display: grid; gap: 1px; }
.brand-eyebrow { color: var(--ink-faint); font-size: 8px; letter-spacing: 0.14em; }
.brand-text { color: var(--ink-max); font-family: var(--font-display); font-size: 17px; font-weight: var(--weight-semibold); letter-spacing: -0.04em; }
.login-header { display: grid; gap: 9px; }
.login-header__code { color: var(--signal-deep); font-size: 8px; letter-spacing: 0.14em; }
.login-header__code span { color: var(--ink-faint); }
.login-header h2 { margin: 0; font-size: clamp(2rem, 4vw, 3rem); font-weight: var(--weight-semibold); letter-spacing: -0.08em; line-height: 0.95; }
.login-header p { margin: 0; color: var(--ink-muted); font-size: var(--fn-sm); line-height: 1.7; }
.login-form { display: grid; gap: 17px; min-width: 0; }
.login-error { display: flex; align-items: flex-start; gap: 8px; padding: 10px 12px; border: 1px solid color-mix(in srgb, var(--bad) 35%, var(--line)); border-radius: var(--r-sm); background: color-mix(in srgb, var(--bad) 8%, transparent); color: var(--bad); font-size: var(--fn-xs); line-height: 1.5; }
.login-error svg { flex: 0 0 auto; margin-top: 1px; }
.field { display: grid; gap: 7px; }
.field label { color: var(--ink-strong); font-size: var(--fn-xs); font-weight: var(--weight-medium); }
.login-submit { margin-top: 7px; min-height: 48px; border-radius: 14px; }
.login-card__footer { display: flex; align-items: center; justify-content: space-between; gap: 12px; padding-top: 16px; border-top: 1px solid var(--line-faint); color: var(--ink-faint); font-size: 10px; }
.login-card__footer-status { display: inline-flex; align-items: center; gap: 6px; color: var(--ok); font-family: var(--font-mono); font-size: 8px; letter-spacing: 0.08em; }
.login-corner { position: fixed; bottom: 20px; z-index: 1; color: var(--ink-faint); font-size: 8px; letter-spacing: 0.12em; }
.login-corner--left { left: 24px; }
.login-corner--right { right: 24px; }

@media (max-width: 860px) {
  .login-page { height: auto; min-height: 100dvh; overflow-y: auto; padding: 20px; }
  .login-layout { grid-template-columns: minmax(0, 1fr); gap: 34px; width: min(100%, 500px); }
  .login-intro { min-height: auto; gap: 26px; }
  .login-intro__copy { padding: 2vh 0 0; }
  .login-intro h1 { font-size: clamp(3.8rem, 15vw, 6rem); }
  .login-intro__copy p { margin-top: 22px; }
  .login-intro__footer { display: none; }
  .login-card { gap: 24px; }
}

@media (max-width: 480px) {
  .login-page { align-items: start; height: auto; min-height: 100dvh; padding: 24px 16px 54px; }
  .login-intro__topline { font-size: 8px; }
  .login-intro__topline > span:first-child { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .login-intro__copy { padding-top: 6vh; }
  .login-intro h1 { font-size: clamp(3.3rem, 17vw, 5rem); }
  .login-readouts { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .login-readout--index { display: none; }
  .login-readout:nth-child(2) { border-left: 1px solid var(--line-faint); }
  .login-card { padding: 24px 20px; border-radius: 20px; }
  .login-corner { bottom: 12px; font-size: 7px; }
  .login-corner--left { left: 16px; }
  .login-corner--right { right: 16px; }
}
</style>
