<script setup lang="ts">
import { ref } from 'vue'
import { authAPI } from '@/api'
import { TicketIcon } from '@heroicons/vue/24/solid'
import { ArrowLeftIcon, EnvelopeIcon, CheckCircleIcon } from '@heroicons/vue/24/outline'

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
  <div class="min-h-screen flex items-center justify-center bg-gradient-to-br from-primary-50 via-white to-primary-100 dark:from-gray-900 dark:via-gray-800 dark:to-gray-900 px-4">
    <div class="w-full max-w-md">
      <!-- Logo -->
      <div class="text-center mb-8">
        <div class="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-gradient-to-br from-primary-500 to-primary-700 shadow-lg mb-4">
          <TicketIcon class="w-7 h-7 text-white" />
        </div>
        <h1 class="text-3xl font-extrabold text-gray-900 dark:text-white tracking-tight">Восстановление пароля</h1>
        <p class="text-gray-500 dark:text-gray-400 mt-1.5">Введите email, и мы пришлём ссылку для сброса</p>
      </div>

      <div class="card p-8">
        <!-- Success state -->
        <div v-if="sent" class="text-center py-4">
          <div class="w-16 h-16 rounded-2xl bg-emerald-50 dark:bg-emerald-900/30 flex items-center justify-center mx-auto mb-4">
            <CheckCircleIcon class="w-8 h-8 text-emerald-500" />
          </div>
          <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-2">Письмо отправлено</h3>
          <p class="text-sm text-gray-500 dark:text-gray-400 mb-6">
            Если email <strong class="text-gray-700 dark:text-gray-300">{{ email }}</strong> зарегистрирован, вы получите письмо со ссылкой для сброса пароля.
          </p>
          <router-link to="/login" class="btn-primary">Вернуться к входу</router-link>
        </div>

        <!-- Form -->
        <form v-else @submit.prevent="handleSubmit" class="space-y-5">
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

          <div v-if="error" class="bg-red-50 dark:bg-red-900/30 text-red-600 dark:text-red-400 text-sm rounded-lg px-4 py-2.5">
            {{ error }}
          </div>

          <button type="submit" class="btn-accent w-full text-base py-3" :disabled="loading">
            <svg v-if="loading" class="animate-spin h-5 w-5 mx-auto" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" fill="none"/><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/></svg>
            {{ loading ? 'Отправка...' : 'Отправить ссылку' }}
          </button>
        </form>

        <div class="mt-6 text-center text-sm">
          <router-link to="/login" class="inline-flex items-center gap-1 text-primary-600 dark:text-primary-400 font-medium hover:underline">
            <ArrowLeftIcon class="w-4 h-4" />
            Вернуться к входу
          </router-link>
        </div>
      </div>
    </div>
  </div>
</template>
