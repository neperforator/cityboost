<script setup lang="ts">
import { ref, computed } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { authAPI } from '@/api'
import { useToast } from '@/composables/useToast'

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

// --- Avatar ---
const avatarFile = ref(null)
const uploadingAvatar = ref(false)
const avatarPreview = ref(null)

const initials = computed(() => {
  if (!auth.userName) return '?'
  return auth.userName.split(' ').map(w => w[0]).join('').toUpperCase().slice(0, 2)
})

const avatarUrl = computed(() => {
  if (auth.user?.avatar_path) {
    return `/storage/${auth.user.avatar_path}`
  }
  return null
})

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
    profileError.value = err.message
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
    passwordError.value = err.message
  } finally {
    savingPassword.value = false
  }
}

function onAvatarSelected(e) {
  const file = e.target.files[0]
  if (!file) return
  if (!['image/jpeg', 'image/png'].includes(file.type)) {
    toast.error('Допустимы только JPEG и PNG')
    return
  }
  avatarFile.value = file
  const reader = new FileReader()
  reader.onload = (ev) => { avatarPreview.value = ev.target.result }
  reader.readAsDataURL(file)
}

async function uploadAvatar() {
  if (!avatarFile.value) { toast.warning('Выберите файл'); return }
  uploadingAvatar.value = true
  try {
    const updated = await authAPI.uploadAvatar(avatarFile.value)
    auth.user = { ...auth.user, ...updated }
    localStorage.setItem('cityboost_user', JSON.stringify(auth.user))
    avatarPreview.value = null
    avatarFile.value = null
    toast.success('Аватар обновлён')
  } catch (err) {
    toast.error(err.message)
  } finally {
    uploadingAvatar.value = false
  }
}
</script>

<template>
  <div class="max-w-2xl mx-auto px-4 sm:px-6 py-8">
    <h1 class="text-2xl font-extrabold text-gray-900 dark:text-white mb-6">👤 Профиль</h1>

    <!-- Profile card -->
    <div class="card p-6 sm:p-8 mb-6">
      <div class="flex items-center gap-6 mb-8">
        <!-- Avatar -->
        <div class="relative shrink-0">
          <div v-if="avatarUrl && !avatarPreview"
               class="w-20 h-20 rounded-full overflow-hidden bg-gray-100 dark:bg-gray-800">
            <img :src="avatarUrl" class="w-full h-full object-cover" alt="Аватар" />
          </div>
          <div v-else-if="avatarPreview"
               class="w-20 h-20 rounded-full overflow-hidden bg-gray-100 dark:bg-gray-800 ring-2 ring-primary-400">
            <img :src="avatarPreview" class="w-full h-full object-cover" alt="Новый аватар" />
          </div>
          <div v-else
               class="w-20 h-20 rounded-full bg-primary-100 dark:bg-primary-900/50 flex items-center justify-center text-2xl font-bold text-primary-600 dark:text-primary-400">
            {{ initials }}
          </div>
        </div>

        <div>
          <h2 class="text-xl font-bold text-gray-900 dark:text-white">{{ auth.userName }}</h2>
          <p class="text-gray-500 dark:text-gray-400 text-sm">{{ auth.userEmail }}</p>
          <div class="mt-1 flex items-center gap-2">
            <span v-if="auth.isAdmin" class="badge-admin text-xs">Администратор</span>
            <span v-else class="bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300 text-xs px-2.5 py-0.5 rounded-full">Пользователь</span>
          </div>
        </div>
      </div>

      <!-- Avatar upload -->
      <div class="border-t border-gray-200 dark:border-gray-700 pt-4 mb-6">
        <h3 class="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">🖼️ Аватар</h3>
        <div class="flex items-center gap-2">
          <input type="file" accept="image/jpeg,image/png" @change="onAvatarSelected" class="form-input text-sm py-2 max-w-xs" />
          <button v-if="avatarFile" @click="uploadAvatar" class="btn-primary btn-sm" :disabled="uploadingAvatar">
            {{ uploadingAvatar ? 'Загрузка...' : 'Загрузить' }}
          </button>
        </div>
        <p class="text-xs text-gray-400 mt-1">JPEG/PNG, макс. 1 МБ</p>
      </div>

      <!-- Info grid -->
      <div class="grid grid-cols-2 gap-6 border-t border-gray-200 dark:border-gray-700 pt-6">
        <div>
          <p class="text-xs text-gray-500 dark:text-gray-400 font-medium uppercase tracking-wide">Email</p>
          <p class="text-sm font-mono mt-1 text-gray-900 dark:text-white">{{ auth.userEmail }}</p>
        </div>
        <div>
          <p class="text-xs text-gray-500 dark:text-gray-400 font-medium uppercase tracking-wide">Дата регистрации</p>
          <p class="text-sm font-medium mt-1 text-gray-900 dark:text-white">{{ joinDate }}</p>
        </div>
        <div>
          <p class="text-xs text-gray-500 dark:text-gray-400 font-medium uppercase tracking-wide">Роль</p>
          <p class="text-sm font-medium mt-1">{{ auth.isAdmin ? 'Администратор' : 'Пользователь' }}</p>
        </div>
        <div>
          <p class="text-xs text-gray-500 dark:text-gray-400 font-medium uppercase tracking-wide">ID</p>
          <p class="text-sm font-mono mt-1 text-gray-900 dark:text-white">{{ auth.user?.id?.slice(0, 12) }}...</p>
        </div>
      </div>
    </div>

    <!-- Edit name -->
    <div class="card p-6 mb-6">
      <h3 class="font-semibold text-gray-900 dark:text-white mb-4">✏️ Редактировать профиль</h3>
      <form @submit.prevent="saveProfile" class="space-y-4">
        <div>
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
      <h3 class="font-semibold text-gray-900 dark:text-white mb-4">🔑 Сменить пароль</h3>
      <form @submit.prevent="changePassword" class="space-y-4">
        <div>
          <label class="form-label">Текущий пароль</label>
          <input v-model="currentPassword" type="password" class="form-input" autocomplete="current-password" />
        </div>
        <div>
          <label class="form-label">Новый пароль</label>
          <input v-model="newPassword" type="password" class="form-input" placeholder="Минимум 8 символов" autocomplete="new-password" />
        </div>
        <div>
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
