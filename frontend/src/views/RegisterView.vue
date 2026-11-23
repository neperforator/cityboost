<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import AuthShell from '@/components/AuthShell.vue'

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
    const user = await auth.register(name.value, email.value, password.value)
    // В DEBUG-режиме с обходом почты аккаунт уже подтверждён — код не нужен.
    if (user.is_verified) {
      router.push('/login?registered=1')
      return
    }
    router.push('/verify-email?email=' + encodeURIComponent(email.value))
  } catch (err) {
    error.value = (err as Error).message
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <AuthShell
    title="Создать аккаунт"
    subtitle="Аккаунт нужен, чтобы отправлять заявки и получать ответы службы."
  >
    <form @submit.prevent="handleRegister" class="space-y-4">
      <div class="form-input-group">
        <label for="register-name" class="form-label">Имя</label>
        <input id="register-name" v-model="name" type="text" class="form-input" placeholder="Иван Иванов" autocomplete="name" required />
      </div>

      <div class="form-input-group">
        <label for="register-email" class="form-label">Email</label>
        <input id="register-email" v-model="email" type="email" class="form-input" placeholder="your@email.com" autocomplete="email" required />
      </div>

      <div class="form-input-group">
        <label for="register-password" class="form-label">Пароль</label>
        <input
          id="register-password"
          v-model="password"
          type="password"
          class="form-input"
          placeholder="Минимум 6 символов"
          autocomplete="new-password"
          required
          minlength="6"
        />
      </div>

      <div class="form-input-group">
        <label for="register-confirm" class="form-label">Подтвердите пароль</label>
        <input
          id="register-confirm"
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
        {{ loading ? 'Регистрация...' : 'Зарегистрироваться' }}
      </button>
    </form>

    <p class="mt-6 text-sm text-ink-soft dark:text-ink-dark-soft">
      Уже есть аккаунт?
      <router-link to="/login" class="font-medium text-primary-700 hover:underline dark:text-primary-300">
        Войти
      </router-link>
    </p>
  </AuthShell>
</template>
