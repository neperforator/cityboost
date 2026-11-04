<script setup lang="ts">
import { ref, computed } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { authAPI } from '@/api'
import { useToast } from '@/composables/useToast'
import { EnvelopeIcon, CalendarDaysIcon, ShieldCheckIcon, PencilSquareIcon, KeyIcon } from '@heroicons/vue/24/outline'

const auth = useAuthStore()
const toast = useToast()

const name = ref(auth.userName || '')
const savingProfile = ref(false)
const profileError = ref('')

const currentPassword = ref('')
const newPassword = ref('')
const savingPassword = ref(false)
const passwordError = ref('')

const joinDate = computed(() => {
  if (!auth.user?.created_at) return '—'
  return new Date(auth.user.created_at).toLocaleDateString('ru-RU', {
    day: 'numeric', month: 'long', year: 'numeric',
  })
})

async function saveProfile() {
  if (!name.value.trim()) { profileError.value = 'Имя не может быть пустым'; return }
  savingProfile.value = true
  profileError.value = ''
  try {
    const updated = await authAPI.updateProfile({ name: name.value.trim() })
    auth.user = { ...auth.user, ...updated }
    localStorage.setItem('cityboost_user', JSON.stringify(auth.user))
    toast.success('Профиль обновлён')
  } catch (err) {
    profileError.value = (err as Error).message
  } finally {
    savingProfile.value = false
  }
}

async function changePassword() {
  if (!currentPassword.value) { passwordError.value = 'Введите текущий пароль'; return }
  if (!newPassword.value) { passwordError.value = 'Введите новый пароль'; return }
  if (newPassword.value.length < 8) { passwordError.value = 'Новый пароль должен быть минимум 8 символов'; return }

  savingPassword.value = true
  passwordError.value = ''
  try {
    await authAPI.updateProfile({
      current_password: currentPassword.value,
      new_password: newPassword.value,
    })
    toast.success('Пароль изменён')
    currentPassword.value = ''
    newPassword.value = ''
  } catch (err) {
    passwordError.value = (err as Error).message
  } finally {
    savingPassword.value = false
  }
}
</script>

<template>
  <div class="mx-auto max-w-4xl px-4 py-8 sm:px-8 sm:py-10">
    <header class="border-b-2 border-line pb-7 dark:border-line-dark">
      <p class="page-kicker">Аккаунт</p>
      <h1 class="mt-2 font-display text-3xl font-semibold tracking-tight text-ink dark:text-ink-dark">Профиль</h1>
      <p class="mt-2 text-sm text-ink-soft dark:text-ink-dark-soft">Личные данные и доступ к аккаунту.</p>
    </header>

    <!-- Identity -->
    <section class="panel mt-6 p-5 sm:p-6">
      <div class="flex flex-col gap-5 sm:flex-row sm:items-start">
        <div class="flex h-16 w-16 shrink-0 items-center justify-center rounded-sm bg-primary-500 font-display text-2xl font-semibold text-white">
          {{ auth.userName?.charAt(0).toUpperCase() || '?' }}
        </div>
        <div class="min-w-0 flex-1">
          <h2 class="font-display text-xl font-semibold text-ink dark:text-ink-dark">{{ auth.userName }}</h2>
          <p class="text-sm text-ink-soft dark:text-ink-dark-soft">{{ auth.userEmail }}</p>
          <span v-if="auth.isAdmin" class="mt-2 inline-flex items-center gap-1 border border-primary-300 px-2 py-0.5 text-[10px] font-semibold text-primary-700 dark:border-primary-700 dark:text-primary-300">
            <ShieldCheckIcon class="h-3 w-3" />
            Администратор
          </span>
          <span v-else class="mt-2 inline-flex items-center border border-line px-2 py-0.5 text-[10px] font-semibold text-ink-soft dark:border-line-dark dark:text-ink-dark-soft">
            Пользователь
          </span>
        </div>
      </div>

      <div class="mt-6 grid grid-cols-1 gap-4 border-t-2 border-line pt-5 dark:border-line-dark sm:grid-cols-3">
        <div class="flex items-start gap-2.5">
          <EnvelopeIcon class="mt-0.5 h-4 w-4 shrink-0 text-ink-soft dark:text-ink-dark-soft" />
          <div>
            <p class="text-[11px] font-semibold uppercase tracking-wider text-ink-soft dark:text-ink-dark-soft">Email</p>
            <p class="mt-0.5 text-sm text-ink dark:text-ink-dark">{{ auth.userEmail }}</p>
          </div>
        </div>
        <div class="flex items-start gap-2.5">
          <CalendarDaysIcon class="mt-0.5 h-4 w-4 shrink-0 text-ink-soft dark:text-ink-dark-soft" />
          <div>
            <p class="text-[11px] font-semibold uppercase tracking-wider text-ink-soft dark:text-ink-dark-soft">Регистрация</p>
            <p class="mt-0.5 text-sm text-ink dark:text-ink-dark">{{ joinDate }}</p>
          </div>
        </div>
        <div class="flex items-start gap-2.5">
          <ShieldCheckIcon class="mt-0.5 h-4 w-4 shrink-0 text-ink-soft dark:text-ink-dark-soft" />
          <div>
            <p class="text-[11px] font-semibold uppercase tracking-wider text-ink-soft dark:text-ink-dark-soft">Роль</p>
            <p class="mt-0.5 text-sm text-ink dark:text-ink-dark">{{ auth.isAdmin ? 'Администратор' : 'Пользователь' }}</p>
          </div>
        </div>
      </div>
    </section>

    <div class="mt-5 grid gap-5 lg:grid-cols-2">
      <!-- Edit name -->
      <section class="panel p-5 sm:p-6">
        <h2 class="flex items-center gap-1.5 text-xs font-semibold text-ink-soft dark:text-ink-dark-soft">
          <PencilSquareIcon class="h-4 w-4" />
          Редактировать профиль
        </h2>
        <form @submit.prevent="saveProfile" class="mt-4 space-y-4">
          <div class="form-input-group">
            <label class="form-label">Имя</label>
            <input v-model="name" type="text" class="form-input" required maxlength="150" />
          </div>
          <div v-if="profileError" class="border-l-4 border-l-red-500 bg-red-50 px-3 py-2 text-sm text-red-700 dark:bg-red-900/20 dark:text-red-300">
            {{ profileError }}
          </div>
          <button type="submit" class="btn-primary" :disabled="savingProfile">
            {{ savingProfile ? 'Сохранение...' : 'Сохранить' }}
          </button>
        </form>
      </section>

      <!-- Change password -->
      <section class="panel p-5 sm:p-6">
        <h2 class="flex items-center gap-1.5 text-xs font-semibold text-ink-soft dark:text-ink-dark-soft">
          <KeyIcon class="h-4 w-4" />
          Сменить пароль
        </h2>
        <form @submit.prevent="changePassword" class="mt-4 space-y-4">
          <div class="form-input-group">
            <label class="form-label">Текущий пароль</label>
            <input v-model="currentPassword" type="password" class="form-input" autocomplete="current-password" />
          </div>
          <div class="form-input-group">
            <label class="form-label">Новый пароль</label>
            <input v-model="newPassword" type="password" class="form-input" placeholder="Минимум 8 символов" autocomplete="new-password" />
          </div>
          <div v-if="passwordError" class="border-l-4 border-l-red-500 bg-red-50 px-3 py-2 text-sm text-red-700 dark:bg-red-900/20 dark:text-red-300">
            {{ passwordError }}
          </div>
          <button type="submit" class="btn-primary" :disabled="savingPassword">
            {{ savingPassword ? 'Смена...' : 'Сменить пароль' }}
          </button>
        </form>
      </section>
    </div>
  </div>
</template>
