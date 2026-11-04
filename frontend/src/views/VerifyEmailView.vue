<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import AuthShell from '@/components/AuthShell.vue'
import { ArrowPathIcon } from '@heroicons/vue/24/outline'

const auth = useAuthStore()
const router = useRouter()
const route = useRoute()

const email = ref((route.query.email as string) || auth.userEmail || '')
const code = ref('')
const loading = ref(false)
const resending = ref(false)
const resendCooldown = ref(0)
const error = ref('')
let resendTimer: ReturnType<typeof setInterval> | null = null

onMounted(() => {
  if (!email.value) {
    router.push('/login')
    return
  }
  startResendCooldown()
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

async function handleVerify() {
  if (code.value.length !== 6) {
    error.value = 'Введите полный 6-значный код'
    return
  }
  loading.value = true
  error.value = ''
  try {
    const result = await auth.verifyEmail(email.value, code.value)

    // Администратору после подтверждения email всё равно нужен вход с 2FA.
    if (result.requires_2fa) {
      if (result.challenge_token) {
        sessionStorage.setItem('cityboost_2fa_challenge', result.challenge_token)
        router.push('/login')
      } else {
        router.push('/login?verified=1')
      }
      return
    }

    router.push('/dashboard')
  } catch (err) {
    const msg = (err as Error).message
    if (msg.includes('код') || msg.includes('просроч')) {
      error.value = 'Неверный или просроченный код. Запросите новый.'
    } else {
      error.value = msg
    }
  } finally {
    loading.value = false
  }
}

async function handleResend() {
  if (resendCooldown.value > 0 || resending.value) return
  resending.value = true
  try {
    await auth.resendCode(email.value)
    startResendCooldown()
  } catch {
    // ignore
  } finally {
    resending.value = false
  }
}
</script>

<template>
  <AuthShell
    title="Подтвердите email"
    subtitle="Введите код из письма, чтобы активировать аккаунт."
  >
    <div class="rounded-sm border-2 border-line bg-surface-muted px-4 py-3 text-sm leading-6 text-ink-soft dark:border-line-dark dark:bg-surface-dark-muted dark:text-ink-dark-soft">
      Код отправлен на <strong class="font-medium text-ink dark:text-ink-dark">{{ email }}</strong>.
      Проверьте почту и папку «Спам».
    </div>

    <form @submit.prevent="handleVerify" class="mt-5 space-y-5">
      <div class="form-input-group">
        <label for="verify-code" class="form-label">6-значный код</label>
        <input
          id="verify-code"
          :value="code"
          @input="onCodeInput"
          type="text"
          inputmode="numeric"
          pattern="[0-9]*"
          maxlength="6"
          class="form-input text-center text-xl font-semibold tracking-[0.4em]"
          placeholder="000000"
          autocomplete="one-time-code"
          required
        />
      </div>

      <div v-if="error" class="rounded-sm border-2 border-red-200 bg-red-50 px-4 py-2.5 text-sm text-red-700 dark:border-red-800 dark:bg-red-900/20 dark:text-red-300">
        {{ error }}
      </div>

      <button type="submit" class="btn-accent w-full" :disabled="loading || code.length !== 6">
        {{ loading ? 'Проверка...' : 'Подтвердить' }}
      </button>
    </form>

    <div class="mt-5 text-sm">
      <button
        @click="handleResend"
        :disabled="resendCooldown > 0 || resending"
        class="inline-flex items-center gap-1.5 font-medium text-primary-700 hover:underline disabled:cursor-not-allowed disabled:text-ink-soft disabled:no-underline dark:text-primary-300"
      >
        <ArrowPathIcon class="h-4 w-4" :class="{ 'animate-spin': resending }" />
        <span v-if="resending">Отправка...</span>
        <span v-else-if="resendCooldown > 0">Отправить повторно ({{ resendCooldown }}с)</span>
        <span v-else>Отправить код повторно</span>
      </button>
    </div>
  </AuthShell>
</template>
