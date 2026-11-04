<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import AuthShell from '@/components/AuthShell.vue'

const auth = useAuthStore()
const route = useRoute()
const router = useRouter()

const email = ref('')
const password = ref('')
const loading = ref(false)
const error = ref('')
const info = ref('')

const step = ref<'credentials' | '2fa'>('credentials')
const challengeToken = ref('')
const code = ref('')
const resending = ref(false)
const resendCooldown = ref(0)
let resendTimer: ReturnType<typeof setInterval> | null = null

const title = computed(() =>
  step.value === '2fa' ? 'Подтверждение входа' : 'Вход в CityBoost',
)
const subtitle = computed(() =>
  step.value === '2fa'
    ? 'Код отправлен на почту администратора. Он действует 10 минут.'
    : 'Отправляйте заявки в городскую службу и следите за их решением.',
)

onMounted(() => {
  if (route.query.verified) {
    info.value = 'Email подтверждён. Войдите — для администратора потребуется код из письма.'
  }

  // Переход со страницы подтверждения email: сразу показываем ввод кода.
  const pendingChallenge = sessionStorage.getItem('cityboost_2fa_challenge')
  if (pendingChallenge) {
    sessionStorage.removeItem('cityboost_2fa_challenge')
    challengeToken.value = pendingChallenge
    step.value = '2fa'
    startResendCooldown()
  }
})

onUnmounted(() => {
  if (resendTimer) clearInterval(resendTimer)
})

function startResendCooldown() {
  resendCooldown.value = 60
  if (resendTimer) clearInterval(resendTimer)
  resendTimer = setInterval(() => {
    resendCooldown.value--
    if (resendCooldown.value <= 0) {
      if (resendTimer) clearInterval(resendTimer)
      resendTimer = null
    }
  }, 1000)
}

function onCodeInput(e: Event) {
  const input = e.target as HTMLInputElement
  code.value = input.value.replace(/\D/g, '').slice(0, 6)
}

async function handleLogin() {
  if (!email.value || !password.value) { error.value = 'Заполните все поля'; return }
  loading.value = true
  error.value = ''
  info.value = ''
  try {
    const result = await auth.login(email.value, password.value)

    if (result.requires2FA) {
      if (!result.challengeToken) {
        throw new Error('Не удалось начать подтверждение входа')
      }
      challengeToken.value = result.challengeToken
      code.value = ''
      step.value = '2fa'
      startResendCooldown()
      return
    }

    router.push(auth.isAdmin ? '/admin' : '/dashboard')
  } catch (err) {
    const msg = (err as Error).message
    if (msg.includes('Подтвердите email')) {
      auth.resendCode(email.value).catch(() => {})
      router.push('/verify-email?email=' + encodeURIComponent(email.value))
      return
    }
    error.value = msg
  } finally {
    loading.value = false
  }
}

async function handleVerify2FA() {
  if (code.value.length !== 6) {
    error.value = 'Введите полный 6-значный код'
    return
  }
  loading.value = true
  error.value = ''
  info.value = ''
  try {
    await auth.verifyAdmin2FA(challengeToken.value, code.value)
    router.push('/admin')
  } catch (err) {
    const msg = (err as Error).message
    if (msg.includes('Сессия подтверждения истекла')) {
      backToCredentials()
      error.value = 'Сессия подтверждения истекла. Войдите заново.'
      return
    }
    error.value = msg
  } finally {
    loading.value = false
  }
}

async function handleResend2FA() {
  if (resendCooldown.value > 0 || resending.value) return
  resending.value = true
  error.value = ''
  info.value = ''
  try {
    await auth.resendAdmin2FA(challengeToken.value)
    info.value = 'Новый код отправлен на почту.'
    startResendCooldown()
  } catch (err) {
    error.value = (err as Error).message
  } finally {
    resending.value = false
  }
}

function backToCredentials() {
  step.value = 'credentials'
  challengeToken.value = ''
  code.value = ''
  error.value = ''
  info.value = ''
}
</script>

<template>
  <AuthShell :title="title" :subtitle="subtitle">
    <div
      v-if="info"
      class="mb-5 rounded-sm border-2 border-primary-200 bg-primary-50 px-4 py-2.5 text-sm text-primary-800 dark:border-primary-800 dark:bg-primary-900/20 dark:text-primary-200"
    >
      {{ info }}
    </div>

    <form v-if="step === 'credentials'" @submit.prevent="handleLogin" class="space-y-5">
      <div class="form-input-group">
        <label for="login-email" class="form-label">Email</label>
        <input
          id="login-email"
          v-model="email"
          type="email"
          class="form-input"
          placeholder="your@email.com"
          autocomplete="email"
          required
        />
      </div>

      <div class="form-input-group">
        <label for="login-password" class="form-label">Пароль</label>
        <input
          id="login-password"
          v-model="password"
          type="password"
          class="form-input"
          placeholder="Пароль"
          autocomplete="current-password"
          required
          minlength="6"
        />
      </div>

      <div v-if="error" class="rounded-sm border-2 border-red-200 bg-red-50 px-4 py-2.5 text-sm text-red-700 dark:border-red-800 dark:bg-red-900/20 dark:text-red-300">
        {{ error }}
      </div>

      <button type="submit" class="btn-accent w-full" :disabled="loading">
        {{ loading ? 'Вход...' : 'Войти' }}
      </button>
    </form>

    <form v-else @submit.prevent="handleVerify2FA" class="space-y-5">
      <div class="rounded-sm border-2 border-line bg-surface-muted px-4 py-3 text-sm leading-6 text-ink-soft dark:border-line-dark dark:bg-surface-dark-muted dark:text-ink-dark-soft">
        Код отправлен на <strong class="font-medium text-ink dark:text-ink-dark">{{ email }}</strong>.
        Проверьте почту и папку «Спам».
      </div>

      <div class="form-input-group">
        <label for="login-2fa-code" class="form-label">6-значный код</label>
        <input
          id="login-2fa-code"
          :value="code"
          @input="onCodeInput"
          type="text"
          inputmode="numeric"
          pattern="[0-9]*"
          maxlength="6"
          class="form-input text-center text-xl font-semibold tracking-[0.4em]"
          placeholder="000000"
          autocomplete="one-time-code"
          autofocus
          required
        />
      </div>

      <div v-if="error" class="rounded-sm border-2 border-red-200 bg-red-50 px-4 py-2.5 text-sm text-red-700 dark:border-red-800 dark:bg-red-900/20 dark:text-red-300">
        {{ error }}
      </div>

      <button type="submit" class="btn-accent w-full" :disabled="loading || code.length !== 6">
        {{ loading ? 'Проверка...' : 'Подтвердить вход' }}
      </button>

      <div class="flex flex-wrap items-center justify-between gap-3 text-sm">
        <button
          type="button"
          @click="handleResend2FA"
          :disabled="resendCooldown > 0 || resending"
          class="font-medium text-primary-700 hover:underline disabled:cursor-not-allowed disabled:text-ink-soft disabled:no-underline dark:text-primary-300"
        >
          <span v-if="resending">Отправка...</span>
          <span v-else-if="resendCooldown > 0">Отправить повторно ({{ resendCooldown }}с)</span>
          <span v-else>Отправить код повторно</span>
        </button>

        <button
          type="button"
          @click="backToCredentials"
          class="font-medium text-ink-soft hover:underline dark:text-ink-dark-soft"
        >
          Назад
        </button>
      </div>
    </form>

    <div v-if="step === 'credentials'" class="mt-6 space-y-2 text-sm">
      <router-link to="/forgot-password" class="block font-medium text-primary-700 hover:underline dark:text-primary-300">
        Забыли пароль?
      </router-link>
      <p class="text-ink-soft dark:text-ink-dark-soft">
        Нет аккаунта?
        <router-link to="/register" class="font-medium text-primary-700 hover:underline dark:text-primary-300">
          Зарегистрироваться
        </router-link>
      </p>
    </div>
  </AuthShell>
</template>
