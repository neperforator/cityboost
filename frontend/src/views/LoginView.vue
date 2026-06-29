<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useToast } from '@/composables/useToast'

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
    error.value = err.message
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="min-h-screen flex items-center justify-center bg-gradient-to-br from-indigo-50 via-white to-blue-50 dark:from-gray-900 dark:via-gray-800 dark:to-gray-900 px-4">
    <div class="w-full max-w-md">
      <div class="text-center mb-8">
        <div class="text-5xl mb-3">🏙️</div>
        <h1 class="text-3xl font-extrabold text-gray-900 dark:text-white">CityBoost</h1>
        <p class="text-gray-500 dark:text-gray-400 mt-1">Войдите в систему городских заявок</p>
      </div>

      <div class="card p-8">
        <form @submit.prevent="handleLogin" class="space-y-5">
          <div>
            <label class="form-label">Email</label>
            <input
              v-model="email"
              type="email"
              class="form-input"
              placeholder="your@email.com"
              autocomplete="email"
              required
            />
          </div>
          <div>
            <label class="form-label">Пароль</label>
            <input
              v-model="password"
              type="password"
              class="form-input"
              placeholder="••••••••"
              autocomplete="current-password"
              required
              minlength="6"
            />
          </div>

          <div v-if="error" class="bg-red-50 dark:bg-red-900/30 text-red-600 dark:text-red-400 text-sm rounded-lg px-4 py-2.5">
            {{ error }}
          </div>

          <button type="submit" class="btn-primary w-full text-base py-3" :disabled="loading">
            <svg v-if="loading" class="animate-spin h-5 w-5" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" fill="none"/><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/></svg>
            {{ loading ? 'Вход...' : 'Войти' }}
          </button>
        </form>

        <div class="mt-4 text-center text-sm">
          <router-link to="/forgot-password" class="text-gray-500 dark:text-gray-400 hover:text-primary-600 dark:hover:text-primary-400">Забыли пароль?</router-link>
        </div>
        <div class="mt-4 text-center text-sm text-gray-500 dark:text-gray-400">
          Нет аккаунта?
          <router-link to="/register" class="text-primary-600 dark:text-primary-400 font-medium hover:underline">Зарегистрироваться</router-link>
        </div>
      </div>
    </div>
  </div>
</template>
