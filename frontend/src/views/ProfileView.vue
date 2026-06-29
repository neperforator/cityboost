<script setup lang="ts">
import { ref, computed } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { authAPI } from '@/api'
import { useToast } from '@/composables/useToast'
import { UserCircleIcon, EnvelopeIcon, CalendarDaysIcon, ShieldCheckIcon, PencilSquareIcon, KeyIcon } from '@heroicons/vue/24/outline'

const auth = useAuthStore()
const toast = useToast()

// --- Profile form ---
const name = ref(auth.userName || '')
const savingProfile = ref(false)
const profileError = ref('')

// --- Password form ---
const currentPassword = ref('')
const newPassword = ref('')
const newPasswordConfirm = ref('')
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
  if (newPassword.value !== newPasswordConfirm.value) { passwordError.value = 'Пароли не совпадают'; return }

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
    newPasswordConfirm.value = ''
  } catch (err) {
    passwordError.value = (err as Error).message
  } finally {
    savingPassword.value = false
  }
}
</script>

<template>
  <div class="max-w-2xl mx-auto px-4 sm:px-6 py-8">
    <!-- Page header -->
    <div class="page-header">
      <h1 class="page-title flex items-center gap-2">
        <UserCircleIcon class="w-7 h-7 text-primary-600 dark:text-primary-400" />
        Профиль
      </h1>
      <p class="page-subtitle">Управление личными данными и настройками</p>
    </div>

    <!-- Profile card -->
    <div class="card p-6 sm:p-8 mb-6">
      <div class="flex flex-col sm:flex-row items-center sm:items-start gap-6 mb-8">
        <div class="w-20 h-20 rounded-full bg-primary-100 dark:bg-primary-900/50 flex items-center justify-center text-2xl font-bold text-primary-600 dark:text-primary-400 shrink-0">
          {{ auth.userName?.charAt(0).toUpperCase() || '?' }}
        </div>

        <div class="text-center sm:text-left">
          <h2 class="text-xl font-bold text-gray-900 dark:text-white">{{ auth.userName }}</h2>
          <p class="text-gray-500 dark:text-gray-400 text-sm">{{ auth.userEmail }}</p>
          <div class="mt-2">
            <span v-if="auth.isAdmin" class="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-primary-50 text-primary-700 dark:bg-primary-900/40 dark:text-primary-300">
              <ShieldCheckIcon class="w-3.5 h-3.5" />
              Администратор
            </span>
            <span v-else class="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-gray-100 text-gray-600 dark:bg-gray-700/50 dark:text-gray-400">
              Пользователь
            </span>
          </div>
        </div>
      </div>

      <!-- Info grid -->
      <div class="grid grid-cols-1 sm:grid-cols-2 gap-6 border-t border-gray-200 dark:border-gray-700 pt-6">
        <div class="flex items-start gap-3">
          <EnvelopeIcon class="w-4 h-4 text-gray-400 mt-0.5 shrink-0" />
          <div>
            <p class="text-xs text-gray-500 dark:text-gray-400 font-medium uppercase tracking-wide">Email</p>
            <p class="text-sm mt-0.5 text-gray-900 dark:text-white">{{ auth.userEmail }}</p>
          </div>
        </div>
        <div class="flex items-start gap-3">
          <CalendarDaysIcon class="w-4 h-4 text-gray-400 mt-0.5 shrink-0" />
          <div>
            <p class="text-xs text-gray-500 dark:text-gray-400 font-medium uppercase tracking-wide">Дата регистрации</p>
            <p class="text-sm mt-0.5 text-gray-900 dark:text-white">{{ joinDate }}</p>
          </div>
        </div>
        <div class="flex items-start gap-3">
          <ShieldCheckIcon class="w-4 h-4 text-gray-400 mt-0.5 shrink-0" />
          <div>
            <p class="text-xs text-gray-500 dark:text-gray-400 font-medium uppercase tracking-wide">Роль</p>
            <p class="text-sm mt-0.5">{{ auth.isAdmin ? 'Администратор' : 'Пользователь' }}</p>
          </div>
        </div>
      </div>
    </div>

    <!-- Edit name -->
    <div class="card p-6 mb-6">
      <h3 class="font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-1.5">
        <PencilSquareIcon class="w-5 h-5 text-gray-400" />
        Редактировать профиль
      </h3>
      <form @submit.prevent="saveProfile" class="space-y-4">
        <div class="form-input-group">
          <label class="form-label">Имя</label>
          <input v-model="name" type="text" class="form-input" required maxlength="150" />
        </div>
        <div v-if="profileError" class="bg-red-50 dark:bg-red-900/30 text-red-600 dark:text-red-400 text-sm rounded-lg px-4 py-2.5">
          {{ profileError }}
        </div>
        <button type="submit" class="btn-primary" :disabled="savingProfile">
          {{ savingProfile ? 'Сохранение...' : 'Сохранить' }}
        </button>
      </form>
    </div>

    <!-- Change password -->
    <div class="card p-6">
      <h3 class="font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-1.5">
        <KeyIcon class="w-5 h-5 text-gray-400" />
        Сменить пароль
      </h3>
      <form @submit.prevent="changePassword" class="space-y-4">
        <div class="form-input-group">
          <label class="form-label">Текущий пароль</label>
          <input v-model="currentPassword" type="password" class="form-input" autocomplete="current-password" />
        </div>
        <div class="form-input-group">
          <label class="form-label">Новый пароль</label>
          <input v-model="newPassword" type="password" class="form-input" placeholder="Минимум 8 символов" autocomplete="new-password" />
        </div>
        <div class="form-input-group">
          <label class="form-label">Подтвердите новый пароль</label>
          <input v-model="newPasswordConfirm" type="password" class="form-input" autocomplete="new-password" />
        </div>
        <div v-if="passwordError" class="bg-red-50 dark:bg-red-900/30 text-red-600 dark:text-red-400 text-sm rounded-lg px-4 py-2.5">
          {{ passwordError }}
        </div>
        <button type="submit" class="btn-primary" :disabled="savingPassword">
          {{ savingPassword ? 'Смена...' : 'Сменить пароль' }}
        </button>
      </form>
    </div>
  </div>
</template>
