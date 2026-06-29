<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useToast } from '@/composables/useToast'

const auth = useAuthStore()
const router = useRouter()
const toast = useToast()

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
    toast.success('Аккаунт создан! Добро пожаловать!')
    router.push('/dashboard')
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
        <h1 class="text-3xl font-extrabold text-gray-900 dark:text-white">Создать аккаунт</h1>
        <p class="text-gray-500 dark:text-gray-400 mt-1">Зарегистрируйтесь для работы с заявками</p>
      </div>

      <div class="card p-8">
        <form @submit.prevent="handleRegister" class="space-y-4">
          <div>
            <label class="form-label">Имя</label>
            <input v-model="name" type="text" class="form-input" placeholder="Иван Иванов" required />
          </div>
          <div>
            <label class="form-label">Email</label>
            <input v-model="email" type="email" class="form-input" placeholder="your@email.com" autocomplete="email" required />
          </div>
          <div>
            <label class="form-label">Пароль</label>
            <input v-model="password" type="password" class="form-input" placeholder="Минимум 6 символов" autocomplete="new-password" required minlength="6" />
          </div>
          <div>
            <label class="form-label">Подтвердите пароль</label>
            <input v-model="passwordConfirm" type="password" class="form-input" placeholder="Повторите пароль" autocomplete="new-password" required />
          </div>

          <div v-if="error" class="bg-red-50 dark:bg-red-900/30 text-red-600 dark:text-red-400 text-sm rounded-lg px-4 py-2.5">
            {{ error }}
          </div>

          <button type="submit" class="btn-primary w-full text-base py-3" :disabled="loading">
            <svg v-if="loading" class="animate-spin h-5 w-5" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" fill="none"/><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/></svg>
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
