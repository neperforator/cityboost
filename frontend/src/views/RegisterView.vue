<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { TicketIcon } from '@heroicons/vue/24/solid'
import { UserPlusIcon, UserIcon, EnvelopeIcon, LockClosedIcon } from '@heroicons/vue/24/outline'

const auth = useAuthStore()
const router = useRouter()

const name = ref('')
const email = ref('')
const password = ref('')
const passwordConfirm = ref('')
const loading = ref(false)
const error = ref('')

async function handleRegister() {
  if (!name.value || !email.value || !password.value) { error.value = 'Заполните все поля'; return }
  if (password.value.length < 6) { error.value = 'Пароль минимум 6 символов'; return }
  if (password.value !== passwordConfirm.value) { error.value = 'Пароли не совпадают'; return }
  loading.value = true
  error.value = ''
  try {
    await auth.register(name.value, email.value, password.value)
    router.push('/verify-email?email=' + encodeURIComponent(email.value))
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
        <h1 class="text-3xl font-extrabold text-gray-900 dark:text-white tracking-tight">Создать аккаунт</h1>
        <p class="text-gray-500 dark:text-gray-400 mt-1.5">Зарегистрируйтесь для работы с заявками</p>
      </div>

      <div class="card p-8">
        <form @submit.prevent="handleRegister" class="space-y-4">
          <div class="form-input-group">
            <label class="form-label">Имя</label>
            <div class="relative">
              <UserIcon class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input v-model="name" type="text" class="form-input pl-10" placeholder="Иван Иванов" required />
            </div>
          </div>
          <div class="form-input-group">
            <label class="form-label">Email</label>
            <div class="relative">
              <EnvelopeIcon class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input v-model="email" type="email" class="form-input pl-10" placeholder="your@email.com" autocomplete="email" required />
            </div>
          </div>
          <div class="form-input-group">
            <label class="form-label">Пароль</label>
            <div class="relative">
              <LockClosedIcon class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input v-model="password" type="password" class="form-input pl-10" placeholder="Минимум 6 символов" autocomplete="new-password" required minlength="6" />
            </div>
          </div>
          <div class="form-input-group">
            <label class="form-label">Подтвердите пароль</label>
            <div class="relative">
              <LockClosedIcon class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input v-model="passwordConfirm" type="password" class="form-input pl-10" placeholder="Повторите пароль" autocomplete="new-password" required />
            </div>
          </div>

          <div v-if="error" class="bg-red-50 dark:bg-red-900/30 text-red-600 dark:text-red-400 text-sm rounded-lg px-4 py-2.5">
            {{ error }}
          </div>

          <button type="submit" class="btn-accent w-full text-base py-3" :disabled="loading">
            <svg v-if="loading" class="animate-spin h-5 w-5" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" fill="none"/><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/></svg>
            <UserPlusIcon v-else class="w-5 h-5" />
            {{ loading ? 'Регистрация...' : 'Зарегистрироваться' }}
          </button>
        </form>

        <div class="mt-6 text-center text-sm text-gray-500 dark:text-gray-400">
          Уже есть аккаунт?
          <router-link to="/login" class="text-primary-600 dark:text-primary-400 font-medium hover:underline">Войти</router-link>
        </div>
      </div>
    </div>
  </div>
</template>
