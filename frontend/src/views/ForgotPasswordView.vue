<script setup lang="ts">
import { ref } from 'vue'
import { authAPI } from '@/api'
import AuthShell from '@/components/AuthShell.vue'
import { ArrowLeftIcon, CheckCircleIcon } from '@heroicons/vue/24/outline'

const email = ref('')
const loading = ref(false)
const sent = ref(false)
const error = ref('')

async function handleSubmit() {
  if (!email.value.trim()) { error.value = 'Введите email'; return }
  loading.value = true
  error.value = ''
  try {
    await authAPI.forgotPassword(email.value.trim())
    sent.value = true
  } catch (err) {
    error.value = (err as Error).message
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <AuthShell
    title="Восстановление пароля"
    subtitle="Укажите email, на который зарегистрирован аккаунт. Мы отправим ссылку для сброса."
  >
    <div v-if="sent">
      <div class="flex items-center gap-2 text-sm font-semibold text-emerald-700 dark:text-emerald-400">
        <CheckCircleIcon class="h-5 w-5" />
        Письмо отправлено
      </div>
      <p class="mt-3 text-sm leading-6 text-ink-soft dark:text-ink-dark-soft">
        Если <strong class="font-medium text-ink dark:text-ink-dark">{{ email }}</strong> зарегистрирован,
        вы получите письмо со ссылкой для сброса пароля.
      </p>
      <router-link to="/login" class="btn-secondary mt-6 w-full">Вернуться к входу</router-link>
    </div>

    <form v-else @submit.prevent="handleSubmit" class="space-y-5">
      <div class="form-input-group">
        <label for="forgot-email" class="form-label">Email</label>
        <input id="forgot-email" v-model="email" type="email" class="form-input" placeholder="your@email.com" autocomplete="email" required />
      </div>

      <div v-if="error" class="rounded-sm border-2 border-red-200 bg-red-50 px-4 py-2.5 text-sm text-red-700 dark:border-red-800 dark:bg-red-900/20 dark:text-red-300">
        {{ error }}
      </div>

      <button type="submit" class="btn-accent w-full" :disabled="loading">
        {{ loading ? 'Отправка...' : 'Отправить ссылку' }}
      </button>
    </form>

    <div v-if="!sent" class="mt-6 text-sm">
      <router-link to="/login" class="inline-flex items-center gap-1 font-medium text-primary-700 hover:underline dark:text-primary-300">
        <ArrowLeftIcon class="h-4 w-4" />
        Вернуться к входу
      </router-link>
    </div>
  </AuthShell>
</template>
