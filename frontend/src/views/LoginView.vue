<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useToast } from '@/composables/useToast'
import { TicketIcon } from '@heroicons/vue/24/solid'
import { ArrowRightIcon, EnvelopeIcon, LockClosedIcon } from '@heroicons/vue/24/outline'

const auth = useAuthStore()
const router = useRouter()
const toast = useToast()

const email = ref('')
const password = ref('')
const loading = ref(false)
const error = ref('')

async function handleLogin() {
  if (!email.value || !password.value) { error.value = 'Заполните все поля'; return }
  loading.value = true
  error.value = ''
  try {
    await auth.login(email.value, password.value)
    toast.success('Добро пожаловать!')
    router.push(auth.isAdmin ? '/admin' : '/dashboard')
  } catch (err) {
    error.value = (err as Error).message
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="min-h-screen flex items-center justify-center bg-gradient-to-br from-primary-50 via-white to-blue-50 dark:from-gray-900 dark:via-gray-800 dark:to-gray-900 px-4">
    <div class="w-full max-w-md">
      <!-- Logo -->
      <div class="text-center mb-8">
        <div class="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-primary-600 dark:bg-primary-500 shadow-lg mb-4">
          <TicketIcon class="w-7 h-7 text-white" />
        </div>
        <h1 class="text-3xl font-extrabold text-gray-900 dark:text-white tracking-tight">CityBoost</h1>
        <p class="text-gray-500 dark:text-gray-400 mt-1.5">Система городских заявок</p>
      </div>

      <div class="card p-8">
        <form @submit.prevent="handleLogin" class="space-y-5">
          <div class="form-input-group">
            <label class="form-label">Email</label>
            <div class="relative">
              <EnvelopeIcon class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                v-model="email"
                type="email"
                class="form-input pl-10"
                placeholder="your@email.com"
                autocomplete="email"
                required
              />
            </div>
          </div>
          <div class="form-input-group">
            <label class="form-label">Пароль</label>
            <div class="relative">
              <LockClosedIcon class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                v-model="password"
                type="password"
                class="form-input pl-10"
                placeholder="••••••••"
                autocomplete="current-password"
                required
                minlength="6"
              />
            </div>
          </div>

          <div v-if="error" class="bg-red-50 dark:bg-red-900/30 text-red-600 dark:text-red-400 text-sm rounded-lg px-4 py-2.5 flex items-center gap-2">
            <span>{{ error }}</span>
          </div>

          <button type="submit" class="btn-primary w-full text-base py-3" :disabled="loading">
            <svg v-if="loading" class="animate-spin h-5 w-5" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" fill="none"/><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/></svg>
            <ArrowRightIcon v-else class="w-5 h-5" />
            {{ loading ? 'Вход...' : 'Войти' }}
          </button>
        </form>

        <div class="mt-5 text-center space-y-2">
          <router-link to="/forgot-password" class="text-sm text-primary-600 dark:text-primary-400 hover:text-primary-700 dark:hover:text-primary-300 font-medium hover:underline underline-offset-2">
            Забыли пароль?
          </router-link>
          <div class="text-sm text-gray-500 dark:text-gray-400">
            Нет аккаунта?
            <router-link to="/register" class="text-primary-600 dark:text-primary-400 font-medium hover:underline">Зарегистрироваться</router-link>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
