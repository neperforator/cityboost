<script setup lang="ts">
import { ref } from 'vue'
import { authAPI } from '@/api'

const email = ref('')
const loading = ref(false)
const sent = ref(false)
const error = ref('')

async function handleSubmit() {
  if (!email.value.trim()) { error.value = 'Введите email'; return }
  loading.value = true
  error.value = ''
  try {
    const resp = await authAPI.forgotPassword(email.value.trim())
    sent.value = true
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
        <div class="text-5xl mb-3">🔐</div>
        <h1 class="text-3xl font-extrabold text-gray-900 dark:text-white">Восстановление пароля</h1>
        <p class="text-gray-500 dark:text-gray-400 mt-1">Введите email, и мы пришлём ссылку для сброса</p>
      </div>

      <div class="card p-8">
        <!-- Success state -->
        <div v-if="sent" class="text-center py-4">
          <div class="text-5xl mb-4">📧</div>
          <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-2">Письмо отправлено</h3>
          <p class="text-sm text-gray-500 dark:text-gray-400 mb-6">
            Если email <strong>{{ email }}</strong> зарегистрирован, вы получите письмо со ссылкой для сброса пароля.
          </p>
          <router-link to="/login" class="btn-primary">Вернуться к входу</router-link>
        </div>

        <!-- Form -->
        <form v-else @submit.prevent="handleSubmit" class="space-y-5">
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

          <div v-if="error" class="bg-red-50 dark:bg-red-900/30 text-red-600 dark:text-red-400 text-sm rounded-lg px-4 py-2.5">
            {{ error }}
          </div>

          <button type="submit" class="btn-primary w-full text-base py-3" :disabled="loading">
            <svg v-if="loading" class="animate-spin h-5 w-5 mx-auto" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" fill="none"/><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/></svg>
            {{ loading ? 'Отправка...' : 'Отправить ссылку' }}
          </button>
        </form>

        <div class="mt-6 text-center text-sm text-gray-500 dark:text-gray-400">
          <router-link to="/login" class="text-primary-600 dark:text-primary-400 font-medium hover:underline">← Вернуться к входу</router-link>
        </div>
      </div>
    </div>
  </div>
</template>
