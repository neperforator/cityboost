<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import AuthShell from '@/components/AuthShell.vue'

const auth = useAuthStore()
const router = useRouter()

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
    router.push(auth.isAdmin ? '/admin' : '/dashboard')
  } catch (err) {
    const msg = (err as Error).message
    if (msg.includes('Подтвердите email')) {
      auth.resendCode(email.value).catch(() => {})
      router.push('/verify-email?email=' + encodeURIComponent(email.value))
      return
    }
    error.value = msg
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <AuthShell
    title="Вход в CityBoost"
    subtitle="Отправляйте заявки в городскую службу и следите за их решением."
  >
    <form @submit.prevent="handleLogin" class="space-y-5">
      <div class="form-input-group">
        <label for="login-email" class="form-label">Email</label>
        <input
          id="login-email"
          v-model="email"
          type="email"
          class="form-input"
          placeholder="your@email.com"
          autocomplete="email"
          required
        />
      </div>

      <div class="form-input-group">
        <label for="login-password" class="form-label">Пароль</label>
        <input
          id="login-password"
          v-model="password"
          type="password"
          class="form-input"
          placeholder="Пароль"
          autocomplete="current-password"
          required
          minlength="6"
        />
      </div>

      <div v-if="error" class="rounded-sm border-2 border-red-200 bg-red-50 px-4 py-2.5 text-sm text-red-700 dark:border-red-800 dark:bg-red-900/20 dark:text-red-300">
        {{ error }}
      </div>

      <button type="submit" class="btn-accent w-full" :disabled="loading">
        {{ loading ? 'Вход...' : 'Войти' }}
      </button>
    </form>

    <div class="mt-6 space-y-2 text-sm">
      <router-link to="/forgot-password" class="block font-medium text-primary-700 hover:underline dark:text-primary-300">
        Забыли пароль?
      </router-link>
      <p class="text-ink-soft dark:text-ink-dark-soft">
        Нет аккаунта?
        <router-link to="/register" class="font-medium text-primary-700 hover:underline dark:text-primary-300">
          Зарегистрироваться
        </router-link>
      </p>
    </div>
  </AuthShell>
</template>
