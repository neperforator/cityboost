<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { authAPI } from '@/api'
import { useToast } from '@/composables/useToast'

const router = useRouter()
const route = useRoute()
const toast = useToast()

const token = ref('')
const password = ref('')
const passwordConfirm = ref('')
const loading = ref(false)
const error = ref('')
const success = ref(false)
const invalidToken = ref(false)

onMounted(() => {
  token.value = route.query.token || ''
  if (!token.value) {
    invalidToken.value = true
    error.value = 'Отсутствует токен сброса пароля'
  }
})

async function handleReset() {
  if (!password.value) { error.value = 'Введите новый пароль'; return }
  if (password.value.length < 8) { error.value = 'Пароль должен быть минимум 8 символов'; return }
  if (password.value !== passwordConfirm.value) { error.value = 'Пароли не совпадают'; return }

  loading.value = true
  error.value = ''
  try {
    await authAPI.resetPassword(token.value, password.value)
    success.value = true
    toast.success('Пароль изменён! Войдите с новым паролем.')
    setTimeout(() => router.push('/login'), 1500)
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
        <div class="text-5xl mb-3">🔑</div>
        <h1 class="text-3xl font-extrabold text-gray-900 dark:text-white">Новый пароль</h1>
        <p class="text-gray-500 dark:text-gray-400 mt-1">Придумайте новый пароль для входа</p>
      </div>

      <div class="card p-8">
        <!-- Success -->
        <div v-if="success" class="text-center py-4">
          <div class="text-5xl mb-4">✅</div>
          <h3 class="text-lg font-semibold text-gray-900 dark:text-white">Пароль изменён!</h3>
          <p class="text-sm text-gray-500 mt-2">Перенаправляем на страницу входа...</p>
        </div>

        <!-- Invalid token -->
        <div v-else-if="invalidToken" class="text-center py-4">
          <div class="text-5xl mb-4">❌</div>
          <h3 class="text-lg font-semibold text-gray-900 dark:text-white">Недействительная ссылка</h3>
          <p class="text-sm text-gray-500 dark:text-gray-400 mb-6">{{ error }}</p>
          <router-link to="/forgot-password" class="btn-primary">Запросить новый сброс</router-link>
        </div>

        <!-- Form -->
        <form v-else @submit.prevent="handleReset" class="space-y-5">
          <div>
            <label class="form-label">Новый пароль</label>
            <input
              v-model="password"
              type="password"
              class="form-input"
              placeholder="Минимум 8 символов"
              autocomplete="new-password"
              required
              minlength="8"
            />
          </div>
          <div>
            <label class="form-label">Подтвердите пароль</label>
            <input
              v-model="passwordConfirm"
              type="password"
              class="form-input"
              placeholder="Повторите пароль"
              autocomplete="new-password"
              required
            />
          </div>

          <div v-if="error" class="bg-red-50 dark:bg-red-900/30 text-red-600 dark:text-red-400 text-sm rounded-lg px-4 py-2.5">
            {{ error }}
          </div>

          <button type="submit" class="btn-primary w-full text-base py-3" :disabled="loading">
            <svg v-if="loading" class="animate-spin h-5 w-5 mx-auto" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" fill="none"/><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/></svg>
            {{ loading ? 'Сброс...' : 'Сбросить пароль' }}
          </button>
        </form>
      </div>
    </div>
  </div>
</template>
