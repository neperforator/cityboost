<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { userAPI } from '@/api'
import { useToast } from '@/composables/useToast'
import { useAuthStore } from '@/stores/auth'
import SkeletonTable from '@/components/SkeletonTable.vue'
import Pagination from '@/components/Pagination.vue'

import { UsersIcon, MagnifyingGlassIcon, ShieldCheckIcon, NoSymbolIcon, CheckBadgeIcon, UserCircleIcon, EnvelopeIcon } from '@heroicons/vue/24/outline'

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

const stats = ref({ total: 0, admins: 0, users: 0, banned: 0 })

const filterRole = ref('')
const filterBanned = ref<boolean | undefined>(undefined)

let searchTimer: ReturnType<typeof setTimeout> | null = null

const totalPages = computed(() => Math.max(1, Math.ceil(total.value / PAGE_SIZE)))

const filters = computed(() => [
  { key: 'all', label: 'Все', count: stats.value.total, role: '', banned: undefined as boolean | undefined },
  { key: 'admins', label: 'Администраторы', count: stats.value.admins, role: 'admin', banned: undefined as boolean | undefined },
  { key: 'users', label: 'Пользователи', count: stats.value.users, role: 'user', banned: undefined as boolean | undefined },
  { key: 'banned', label: 'Заблокированы', count: stats.value.banned, role: '', banned: true },
])

function isActive(key: string) {
  const s = filters.value.find(c => c.key === key)!
  return filterRole.value === s.role && filterBanned.value === s.banned
}

async function loadStats() {
  try {
    stats.value = await userAPI.getStats()
  } catch {
    // fallback
  }
}

async function loadUsers(p?: number) {
  if (p) page.value = p
  loading.value = true
  try {
    const data = await userAPI.list(
      page.value,
      PAGE_SIZE,
      searchQuery.value.trim(),
      filterBanned.value,
      filterRole.value || undefined,
    )
    users.value = data.items
    total.value = data.total
  } catch (err) {
    toast.error((err as Error).message)
  } finally {
    loading.value = false
  }
}

function setFilter(role: string, banned?: boolean) {
  filterRole.value = role
  filterBanned.value = banned
  page.value = 1
  loadUsers()
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

onMounted(() => {
  loadStats()
  loadUsers()
})
</script>

<template>
  <div class="mx-auto max-w-6xl px-4 py-8 sm:px-8 sm:py-10">
    <header class="border-b-2 border-line pb-7 dark:border-line-dark">
      <p class="page-kicker">Администрирование</p>
      <div class="mt-2 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h1 class="font-display text-3xl font-semibold tracking-tight text-ink dark:text-ink-dark">Пользователи</h1>
          <p class="mt-2 text-sm text-ink-soft dark:text-ink-dark-soft">Роли, доступ и блокировки аккаунтов.</p>
        </div>
        <div class="relative w-full sm:w-72">
          <MagnifyingGlassIcon class="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-ink-soft dark:text-ink-dark-soft" />
          <input v-model="searchQuery" @input="onSearchInput" type="text" class="form-input pl-9" placeholder="Поиск по имени, email..." />
        </div>
      </div>
    </header>

    <div class="mt-6 overflow-x-auto scrollbar-none">
      <div class="flex min-w-max items-stretch border-2 border-line dark:border-line-dark">
        <button
          v-for="f in filters"
          :key="f.key"
          @click="setFilter(f.role, f.banned)"
          class="flex items-center gap-2 border-r-2 border-line px-4 py-3 text-sm font-medium transition-colors last:border-r-0 dark:border-line-dark"
          :class="isActive(f.key)
            ? 'bg-primary-500 text-white'
            : 'bg-surface text-ink-soft hover:bg-surface-muted dark:bg-surface-dark dark:text-ink-dark-soft dark:hover:bg-surface-dark-muted'"
        >
          {{ f.label }}
          <span class="text-xs font-semibold tabular-nums" :class="isActive(f.key) ? 'text-primary-100' : 'text-ink-soft dark:text-ink-dark-soft'">{{ f.count }}</span>
        </button>
      </div>
    </div>

    <Transition name="page" mode="out-in">
      <div v-if="loading" key="loading" class="panel mt-5 overflow-hidden">
        <SkeletonTable :rows="7" :columns="5" />
      </div>

      <div v-else-if="users.length === 0" key="empty" class="panel mt-5 p-10 text-center">
        <UsersIcon class="mx-auto h-8 w-8 text-ink-soft dark:text-ink-dark-soft" />
        <p class="mt-3 text-sm text-ink-soft dark:text-ink-dark-soft">Пользователи не найдены</p>
      </div>

      <div v-else key="table" class="mt-5">
        <div class="panel overflow-hidden">
          <div class="overflow-x-auto">
            <table class="w-full text-sm">
              <thead>
                <tr class="border-b-2 border-line bg-surface-muted dark:border-line-dark dark:bg-surface-dark-muted">
                  <th class="px-4 py-3 text-left text-[11px] font-semibold uppercase tracking-wider text-ink-soft dark:text-ink-dark-soft">Пользователь</th>
                  <th class="px-4 py-3 text-left text-[11px] font-semibold uppercase tracking-wider text-ink-soft dark:text-ink-dark-soft">Email</th>
                  <th class="px-4 py-3 text-left text-[11px] font-semibold uppercase tracking-wider text-ink-soft dark:text-ink-dark-soft">Роль</th>
                  <th class="px-4 py-3 text-left text-[11px] font-semibold uppercase tracking-wider text-ink-soft dark:text-ink-dark-soft">Регистрация</th>
                  <th class="px-4 py-3 text-right text-[11px] font-semibold uppercase tracking-wider text-ink-soft dark:text-ink-dark-soft">Действия</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="u in users" :key="u.id" class="border-b-2 border-line transition-colors last:border-b-0 hover:bg-surface-muted dark:border-line-dark dark:hover:bg-surface-dark-muted">
                  <td class="px-4 py-3.5">
                    <div class="flex items-center gap-3">
                      <div class="flex h-8 w-8 shrink-0 items-center justify-center rounded-sm bg-primary-500 text-[10px] font-bold text-white">
                        {{ u.name.split(' ').map((w: string) => w[0]).join('').toUpperCase().slice(0, 2) }}
                      </div>
                      <p class="font-medium text-ink dark:text-ink-dark">{{ u.name }}</p>
                    </div>
                  </td>
                  <td class="px-4 py-3.5">
                    <div class="flex items-center gap-1.5 text-ink-soft dark:text-ink-dark-soft">
                      <EnvelopeIcon class="h-3.5 w-3.5 shrink-0" />
                      {{ u.email }}
                    </div>
                  </td>
                  <td class="px-4 py-3.5">
                    <div class="flex flex-wrap items-center gap-1.5">
                      <span v-if="u.role === 'admin'" class="inline-flex items-center gap-1 border border-primary-300 px-2 py-0.5 text-[10px] font-semibold text-primary-700 dark:border-primary-700 dark:text-primary-300">
                        <ShieldCheckIcon class="h-3 w-3" />
                        Администратор
                      </span>
                      <span v-else class="inline-flex items-center gap-1 border border-line px-2 py-0.5 text-[10px] font-semibold text-ink-soft dark:border-line-dark dark:text-ink-dark-soft">
                        <UserCircleIcon class="h-3 w-3" />
                        Пользователь
                      </span>
                      <span v-if="u.is_banned" class="inline-flex items-center gap-1 border border-red-300 px-2 py-0.5 text-[10px] font-semibold text-red-700 dark:border-red-700 dark:text-red-400">
                        <NoSymbolIcon class="h-3 w-3" />
                        Заблокирован
                      </span>
                    </div>
                  </td>
                  <td class="whitespace-nowrap px-4 py-3.5 text-xs text-ink-soft dark:text-ink-dark-soft">{{ formatDate(u.created_at) }}</td>
                  <td class="px-4 py-3.5 text-right">
                    <div class="flex flex-wrap items-center justify-end gap-1.5">
                      <button
                        @click="toggleRole(u)"
                        :disabled="updating === u.id"
                        class="btn-sm whitespace-nowrap text-xs"
                        :class="u.role === 'admin' ? 'btn-secondary' : 'btn-primary'"
                      >
                        <span v-if="updating === u.id" class="mr-1 inline-block h-3 w-3 animate-spin rounded-full border-2 border-current border-t-transparent"></span>
                        {{ u.role === 'admin' ? 'Снять админа' : 'Сделать админом' }}
                      </button>
                      <button
                        v-if="u.id !== auth.user?.id && !u.is_banned"
                        @click="toggleBan(u)"
                        :disabled="banning === u.id"
                        class="btn-danger btn-sm whitespace-nowrap text-xs"
                      >
                        <span v-if="banning === u.id" class="mr-1 inline-block h-3 w-3 animate-spin rounded-full border-2 border-current border-t-transparent"></span>
                        <NoSymbolIcon class="h-3.5 w-3.5" />
                        Заблокировать
                      </button>
                      <button
                        v-else-if="u.id !== auth.user?.id && u.is_banned"
                        @click="toggleBan(u)"
                        :disabled="banning === u.id"
                        class="btn-secondary btn-sm whitespace-nowrap text-xs"
                      >
                        <span v-if="banning === u.id" class="mr-1 inline-block h-3 w-3 animate-spin rounded-full border-2 border-current border-t-transparent"></span>
                        <CheckBadgeIcon class="h-3.5 w-3.5" />
                        Разблокировать
                      </button>
                    </div>
                  </td>
                </tr>
              </tbody>
            </table>
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
