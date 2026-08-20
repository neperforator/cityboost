<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { TicketIcon } from '@heroicons/vue/24/solid'
import { EnvelopeIcon, ArrowPathIcon } from '@heroicons/vue/24/outline'

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
    await auth.verifyEmail(email.value, code.value)
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
  <div class="min-h-screen flex items-center justify-center bg-gradient-to-br from-primary-50 via-white to-primary-100 dark:from-gray-900 dark:via-gray-800 dark:to-gray-900 px-4">
    <div class="w-full max-w-md">
      <!-- Logo -->
      <div class="text-center mb-8">
        <div class="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-gradient-to-br from-primary-500 to-primary-700 shadow-lg mb-4">
          <TicketIcon class="w-7 h-7 text-white" />
        </div>
        <h1 class="text-3xl font-extrabold text-gray-900 dark:text-white tracking-tight">Подтверждение email</h1>
        <p class="text-gray-500 dark:text-gray-400 mt-1.5">Введите код из письма</p>
      </div>

      <div class="card p-8">
        <!-- Form -->
        <div>
          <div class="bg-primary-50 dark:bg-primary-900/20 rounded-lg p-4 mb-6 flex items-start gap-3">
            <EnvelopeIcon class="w-5 h-5 text-primary-600 dark:text-primary-400 mt-0.5 shrink-0" />
            <p class="text-sm text-gray-600 dark:text-gray-300">
              Код отправлен на <strong class="text-gray-900 dark:text-white">{{ email }}</strong>.
              Проверьте почту (возможно, папку «Спам»).
            </p>
          </div>

          <form @submit.prevent="handleVerify" class="space-y-6">
            <!-- Code input -->
            <div class="form-input-group">
              <label class="form-label text-center block w-full">6-значный код</label>
              <div class="flex justify-center">
                <input
                  :value="code"
                  @input="onCodeInput"
                  type="text"
                  inputmode="numeric"
                  pattern="[0-9]*"
                  maxlength="6"
                  class="form-input text-center text-2xl font-bold tracking-[0.5em] h-14 w-full max-w-[220px]"
                  placeholder="000000"
                  autocomplete="one-time-code"
                  required
                />
              </div>
            </div>

            <div v-if="error" class="bg-red-50 dark:bg-red-900/30 text-red-600 dark:text-red-400 text-sm rounded-lg px-4 py-2.5 text-center">
              {{ error }}
            </div>

            <button type="submit" class="btn-accent w-full text-base py-3" :disabled="loading || code.length !== 6">
              <svg v-if="loading" class="animate-spin h-5 w-5 mx-auto" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" fill="none"/><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/></svg>
              <span v-else>Подтвердить</span>
            </button>
          </form>

          <div class="mt-6 text-center text-sm">
            <button
              @click="handleResend"
              :disabled="resendCooldown > 0 || resending"
              class="inline-flex items-center gap-1.5 text-primary-600 dark:text-primary-400 font-medium hover:underline disabled:text-gray-400 disabled:cursor-not-allowed disabled:no-underline focus:outline-none focus-visible:ring-2 focus-visible:ring-primary-500/40 rounded-lg"
            >
              <ArrowPathIcon class="w-4 h-4" :class="{ 'animate-spin': resending }" />
              <span v-if="resending">Отправка...</span>
              <span v-else-if="resendCooldown > 0">Отправить повторно ({{ resendCooldown }}с)</span>
              <span v-else>Отправить код повторно</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
