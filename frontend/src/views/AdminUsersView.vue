<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue'
import { userAPI } from '@/api'
import { useToast } from '@/composables/useToast'
import { useAuthStore } from '@/stores/auth'
import SkeletonTable from '@/components/SkeletonTable.vue'
import Pagination from '@/components/Pagination.vue'

import { UsersIcon, MagnifyingGlassIcon, ShieldCheckIcon, NoSymbolIcon, CheckBadgeIcon, UserCircleIcon, CalendarDaysIcon, EnvelopeIcon } from '@heroicons/vue/24/outline'

const PAGE_SIZE = 20

const toast = useToast()
const auth = useAuthStore()

const users = ref<any[]>([])
const total = ref(0)
const page = ref(1)
const loading = ref(true)
const searchQuery = ref('')
const updating = ref<string | null>(null)
const banning = ref<string | null>(null)

let searchTimer: ReturnType<typeof setTimeout> | null = null

const totalPages = computed(() => Math.max(1, Math.ceil(total.value / PAGE_SIZE)))

const stats = computed(() => ({
  total: total.value,
  admins: users.value.filter((u: any) => u.role === 'admin').length,
  regular: users.value.filter((u: any) => u.role === 'user').length,
  banned: users.value.filter((u: any) => u.is_banned).length,
}))

async function loadUsers(p?: number) {
  if (p) page.value = p
  loading.value = true
  try {
    const data = await userAPI.list(page.value, PAGE_SIZE, searchQuery.value.trim())
    users.value = data.items
    total.value = data.total
  } catch (err) {
    toast.error((err as Error).message)
  } finally {
    loading.value = false
  }
}

function onSearchInput() {
  if (searchTimer) clearTimeout(searchTimer)
  searchTimer = setTimeout(() => {
    page.value = 1
    loadUsers()
  }, 300)
}

async function toggleRole(user: any) {
  const newRole = user.role === 'admin' ? 'user' : 'admin'
  updating.value = user.id
  try {
    const updated = await userAPI.changeRole(user.id, newRole)
    Object.assign(user, updated)
    toast.success(`Роль пользователя ${user.name} изменена на «${newRole === 'admin' ? 'администратор' : 'пользователь'}»`)
  } catch (err) {
    toast.error((err as Error).message)
  } finally {
    updating.value = null
  }
}

async function toggleBan(user: any) {
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
    toast.error((err as Error).message)
  } finally {
    banning.value = null
  }
}

function formatDate(d: string) {
  return new Date(d).toLocaleDateString('ru-RU', { day: 'numeric', month: 'short', year: 'numeric' })
}

onMounted(() => loadUsers())
</script>

<template>
  <div class="max-w-5xl mx-auto px-4 sm:px-6 py-8">
    <!-- Page header -->
    <div class="flex flex-col sm:flex-row sm:items-start justify-between gap-4 mb-8">
      <div>
        <h1 class="page-title flex items-center gap-2">
          <UsersIcon class="w-7 h-7 text-primary-600 dark:text-primary-400" />
          Управление пользователями
        </h1>
        <div class="flex flex-wrap gap-2 mt-3">
          <span class="badge-new text-xs">Всего: {{ stats.total }}</span>
          <span class="badge text-xs bg-primary-50 text-primary-700 dark:bg-primary-900/40 dark:text-primary-300">Админов: {{ stats.admins }}</span>
          <span class="badge text-xs bg-blue-50 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400">Пользователей: {{ stats.regular }}</span>
          <span v-if="stats.banned > 0" class="badge text-xs bg-red-50 text-red-700 dark:bg-red-900/30 dark:text-red-400">Заблокировано: {{ stats.banned }}</span>
        </div>
      </div>
      <div class="relative w-full sm:w-72">
        <MagnifyingGlassIcon class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
        <input v-model="searchQuery" @input="onSearchInput" type="text" class="form-input pl-9" placeholder="Поиск по имени, email..." />
      </div>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="card overflow-hidden">
      <SkeletonTable :rows="7" :columns="5" />
    </div>

    <!-- Table with transition -->
    <Transition name="page" mode="out-in">
      <div v-if="!loading" key="table">
      <div class="card overflow-hidden">
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
              <tr v-for="u in users" :key="u.id" class="hover:bg-gray-50 dark:hover:bg-gray-800/30 transition-colors">
                <td class="px-4 py-3">
                  <div class="flex items-center gap-3">
                    <div class="w-9 h-9 rounded-full bg-primary-100 dark:bg-primary-900/50 flex items-center justify-center text-xs font-bold text-primary-600 dark:text-primary-400 shrink-0">
                      {{ u.name.split(' ').map((w: string) => w[0]).join('').toUpperCase().slice(0, 2) }}
                    </div>
                    <div>
                      <p class="font-medium text-gray-900 dark:text-white">{{ u.name }}</p>
                    </div>
                  </div>
                </td>
                <td class="px-4 py-3">
                  <div class="flex items-center gap-1.5 text-gray-500 dark:text-gray-400">
                    <EnvelopeIcon class="w-3.5 h-3.5 shrink-0" />
                    {{ u.email }}
                  </div>
                </td>
                <td class="px-4 py-3">
                  <div class="flex flex-wrap items-center gap-1.5">
                    <span v-if="u.role === 'admin'" class="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-primary-50 text-primary-700 dark:bg-primary-900/40 dark:text-primary-300">
                      <ShieldCheckIcon class="w-3.5 h-3.5" />
                      Администратор
                    </span>
                    <span v-else class="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-gray-100 text-gray-600 dark:bg-gray-700/50 dark:text-gray-400">
                      <UserCircleIcon class="w-3.5 h-3.5" />
                      Пользователь
                    </span>
                    <span v-if="u.is_banned" class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-semibold bg-red-50 text-red-700 dark:bg-red-900/30 dark:text-red-400">
                      <NoSymbolIcon class="w-3.5 h-3.5" />
                      Заблокирован
                    </span>
                  </div>
                </td>
                <td class="px-4 py-3 text-xs text-gray-500">{{ formatDate(u.created_at) }}</td>
                <td class="px-4 py-3 text-right">
                  <div class="flex flex-wrap items-center justify-end gap-1.5">
                    <button
                      @click="toggleRole(u)"
                      :disabled="updating === u.id"
                      class="btn-sm text-xs whitespace-nowrap"
                      :class="u.role === 'admin' ? 'btn-secondary' : 'btn-primary'"
                    >
                      <span v-if="updating === u.id" class="animate-spin inline-block w-3 h-3 border-2 border-current border-t-transparent rounded-full mr-1"></span>
                      {{ u.role === 'admin' ? 'Снять админа' : 'Сделать админом' }}
                    </button>
                    <button
                      v-if="u.id !== auth.user?.id && !u.is_banned"
                      @click="toggleBan(u)"
                      :disabled="banning === u.id"
                      class="btn-sm text-xs whitespace-nowrap btn-danger"
                    >
                      <span v-if="banning === u.id" class="animate-spin inline-block w-3 h-3 border-2 border-current border-t-transparent rounded-full mr-1"></span>
                      <NoSymbolIcon class="w-3.5 h-3.5" />
                      Заблокировать
                    </button>
                    <button
                      v-else-if="u.id !== auth.user?.id && u.is_banned"
                      @click="toggleBan(u)"
                      :disabled="banning === u.id"
                      class="btn-sm text-xs whitespace-nowrap btn-secondary"
                    >
                      <span v-if="banning === u.id" class="animate-spin inline-block w-3 h-3 border-2 border-current border-t-transparent rounded-full mr-1"></span>
                      <CheckBadgeIcon class="w-3.5 h-3.5" />
                      Разблокировать
                    </button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- Empty state -->
        <div v-if="users.length === 0 && !loading" class="p-8 text-center text-gray-400">
          Пользователи не найдены
        </div>
      </div>

      <Pagination
        v-if="totalPages > 1"
        :page="page"
        :total-pages="totalPages"
        :total="total"
        @change="loadUsers"
      />
    </div>
    </Transition>
  </div>
</template>
