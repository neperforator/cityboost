<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { authAPI } from '@/api'
import { useToast } from '@/composables/useToast'
import AuthShell from '@/components/AuthShell.vue'
import { CheckCircleIcon, ExclamationTriangleIcon } from '@heroicons/vue/24/outline'

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
  token.value = (route.query.token as string) || ''
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
    error.value = (err as Error).message
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <AuthShell
    title="Новый пароль"
    subtitle="Придумайте пароль для входа в аккаунт."
  >
    <div v-if="success">
      <div class="flex items-center gap-2 text-sm font-semibold text-emerald-700 dark:text-emerald-400">
        <CheckCircleIcon class="h-5 w-5" />
        Пароль изменён
      </div>
      <p class="mt-3 text-sm text-ink-soft dark:text-ink-dark-soft">Перенаправляем на страницу входа...</p>
    </div>

    <div v-else-if="invalidToken">
      <div class="flex items-center gap-2 text-sm font-semibold text-red-700 dark:text-red-400">
        <ExclamationTriangleIcon class="h-5 w-5" />
        Недействительная ссылка
      </div>
      <p class="mt-3 text-sm text-ink-soft dark:text-ink-dark-soft">{{ error }}</p>
      <router-link to="/forgot-password" class="btn-accent mt-6 w-full">Запросить новый сброс</router-link>
    </div>

    <form v-else @submit.prevent="handleReset" class="space-y-4">
      <div class="form-input-group">
        <label for="reset-password" class="form-label">Новый пароль</label>
        <input
          id="reset-password"
          v-model="password"
          type="password"
          class="form-input"
          placeholder="Минимум 8 символов"
          autocomplete="new-password"
          required
          minlength="8"
        />
      </div>

      <div class="form-input-group">
        <label for="reset-confirm" class="form-label">Подтвердите пароль</label>
        <input
          id="reset-confirm"
          v-model="passwordConfirm"
          type="password"
          class="form-input"
          placeholder="Повторите пароль"
          autocomplete="new-password"
          required
        />
      </div>

      <div v-if="error" class="rounded-sm border-2 border-red-200 bg-red-50 px-4 py-2.5 text-sm text-red-700 dark:border-red-800 dark:bg-red-900/20 dark:text-red-300">
        {{ error }}
      </div>

      <button type="submit" class="btn-accent w-full" :disabled="loading">
        {{ loading ? 'Сброс...' : 'Сбросить пароль' }}
      </button>
    </form>
  </AuthShell>
</template>
