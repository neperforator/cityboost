<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { userAPI } from '@/api'
import { useToast } from '@/composables/useToast'
import { useAuthStore } from '@/stores/auth'

import SkeletonTable from '@/components/SkeletonTable.vue'

const toast = useToast()
const auth = useAuthStore()

const users = ref([])
const loading = ref(true)
const searchQuery = ref('')
const updating = ref(null)
const banning = ref(null)

const filteredUsers = computed(() => {
  if (!searchQuery.value.trim()) return users.value
  const q = searchQuery.value.toLowerCase()
  return users.value.filter(u =>
    u.name.toLowerCase().includes(q) ||
    u.email.toLowerCase().includes(q) ||
    u.id.toLowerCase().includes(q)
  )
})

const stats = computed(() => ({
  total: users.value.length,
  admins: users.value.filter(u => u.role === 'admin').length,
  users: users.value.filter(u => u.role === 'user').length,
  banned: users.value.filter(u => u.is_banned).length,
}))


async function loadUsers() {
  loading.value = true
  try {
    users.value = await userAPI.list()
  } catch (err) {
    toast.error(err.message)
  } finally {
    loading.value = false
  }
}

async function toggleRole(user) {
  const newRole = user.role === 'admin' ? 'user' : 'admin'
  updating.value = user.id
  try {
    const updated = await userAPI.changeRole(user.id, newRole)
    Object.assign(user, updated)
    toast.success(`Роль пользователя ${user.name} изменена на «${newRole}»`)
  } catch (err) {
    toast.error(err.message)
  } finally {
    updating.value = null
  }
}

async function toggleBan(user) {
  banning.value = user.id
  try {
    if (user.is_banned) {
      const updated = await userAPI.unban(user.id)
      Object.assign(user, updated)
      toast.success(`Пользователь ${user.name} разблокирован`)
    } else {
      const updated = await userAPI.ban(user.id)
      Object.assign(user, updated)
      toast.success(`Пользователь ${user.name} заблокирован`)
    }
  } catch (err) {
    toast.error(err.message)
  } finally {
    banning.value = null
  }
}

function formatDate(d) {
  return new Date(d).toLocaleDateString('ru-RU', { day: 'numeric', month: 'short', year: 'numeric' })
}

onMounted(loadUsers)
</script>

<template>
  <div class="max-w-5xl mx-auto px-4 sm:px-6 py-8">
    <!-- Header -->
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-8">
      <div>
        <h1 class="text-2xl font-extrabold text-gray-900 dark:text-white flex items-center gap-2">👥 Управление пользователями</h1>
        <p class="text-sm text-gray-500 dark:text-gray-400 mt-0.5">Всего: {{ stats.total }} · админов: {{ stats.admins }} · пользователей: {{ stats.users }} · заблокировано: {{ stats.banned }}</p>
      </div>
      <div class="relative">
        <svg class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/></svg>
        <input v-model="searchQuery" type="text" class="form-input pl-9 w-64" placeholder="Поиск по имени, email..." />
      </div>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="card overflow-hidden">
      <SkeletonTable :rows="7" :columns="5" />
    </div>

    <!-- Table -->
    <div v-else class="card overflow-hidden">
      <div class="overflow-x-auto">
        <table class="w-full text-sm">
          <thead>
            <tr class="bg-gray-50 dark:bg-gray-800/50 border-b border-gray-200 dark:border-gray-700">
              <th class="text-left px-4 py-3 font-semibold text-gray-600 dark:text-gray-400">Пользователь</th>
              <th class="text-left px-4 py-3 font-semibold text-gray-600 dark:text-gray-400">Email</th>
              <th class="text-left px-4 py-3 font-semibold text-gray-600 dark:text-gray-400">Роль</th>
              <th class="text-left px-4 py-3 font-semibold text-gray-600 dark:text-gray-400">Дата регистрации</th>
              <th class="text-right px-4 py-3 font-semibold text-gray-600 dark:text-gray-400">Действия</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-100 dark:divide-gray-700">
            <tr v-for="u in filteredUsers" :key="u.id" class="hover:bg-gray-50 dark:hover:bg-gray-800/30 transition-colors">
              <td class="px-4 py-3">
                <div class="flex items-center gap-3">
                  <div class="w-8 h-8 rounded-full bg-primary-100 dark:bg-primary-900/50 flex items-center justify-center text-xs font-bold text-primary-600 dark:text-primary-400 shrink-0">
                    {{ u.name.split(' ').map(w => w[0]).join('').toUpperCase().slice(0, 2) }}
                  </div>
                  <div>
                    <p class="font-medium text-gray-900 dark:text-white">{{ u.name }}</p>
                    <p class="text-xs text-gray-400 font-mono">{{ u.id.slice(0, 8) }}...</p>
                  </div>
                </div>
              </td>
              <td class="px-4 py-3 text-gray-500 dark:text-gray-400">{{ u.email }}</td>
              <td class="px-4 py-3">
                <div class="flex items-center gap-2">
                  <span v-if="u.role === 'admin'" class="badge-admin text-xs">Администратор</span>
                  <span v-else class="bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300 text-xs px-2.5 py-0.5 rounded-full">Пользователь</span>
                  <span v-if="u.is_banned" class="bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-300 text-xs px-2 py-0.5 rounded-full font-semibold">🚫 Заблокирован</span>
                </div>
              </td>
              <td class="px-4 py-3 text-xs text-gray-500">{{ formatDate(u.created_at) }}</td>
              <td class="px-4 py-3 text-right">
                <div class="flex items-center justify-end gap-2">
                  <button
                    @click="toggleRole(u)"
                    :disabled="updating === u.id"
                    class="btn-sm"
                    :class="u.role === 'admin' ? 'btn-secondary' : 'btn-primary'"
                  >
                    <span v-if="updating === u.id" class="animate-spin inline-block w-3 h-3 border-2 border-current border-t-transparent rounded-full mr-1"></span>
                    {{ u.role === 'admin' ? 'Снять админа' : 'Сделать админом' }}
                  </button>
                  <button
                    v-if="u.id !== auth.user?.id && !u.is_banned"
                    @click="toggleBan(u)"
                    :disabled="banning === u.id"
                    class="btn-sm btn-danger"
                  >
                    <span v-if="banning === u.id" class="animate-spin inline-block w-3 h-3 border-2 border-current border-t-transparent rounded-full mr-1"></span>
                    🚫 Заблокировать
                  </button>
                  <button
                    v-else-if="u.id !== auth.user?.id && u.is_banned"
                    @click="toggleBan(u)"
                    :disabled="banning === u.id"
                    class="btn-sm btn-secondary"
                  >
                    <span v-if="banning === u.id" class="animate-spin inline-block w-3 h-3 border-2 border-current border-t-transparent rounded-full mr-1"></span>
                    ✅ Разблокировать
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Empty state -->
      <div v-if="filteredUsers.length === 0 && !loading" class="p-8 text-center text-gray-400">
        Пользователи не найдены
      </div>
    </div>
  </div>
</template>
