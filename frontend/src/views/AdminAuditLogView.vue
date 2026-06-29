<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { adminAPI } from '@/api'
import { useToast } from '@/composables/useToast'
import { useUsers } from '@/composables/useUsers'
import Pagination from '@/components/Pagination.vue'
import SkeletonTable from '@/components/SkeletonTable.vue'

import { ClockIcon, FunnelIcon } from '@heroicons/vue/24/outline'
import { NoSymbolIcon, CheckBadgeIcon, ShieldCheckIcon, ArrowPathIcon, WrenchScrewdriverIcon } from '@heroicons/vue/24/solid'

const toast = useToast()
const { getUserName, getUserDisplay, fetchUsers, loaded } = useUsers()

const logs = ref<any[]>([])
const total = ref(0)
const loading = ref(true)
const page = ref(1)
const pageSize = 30
const actionFilter = ref('')
const totalPages = computed(() => Math.max(1, Math.ceil(total.value / pageSize)))

const actions = [
  { value: '', label: 'Все действия', icon: FunnelIcon },
  { value: 'ban', label: 'Блокировка', icon: NoSymbolIcon },
  { value: 'unban', label: 'Разблокировка', icon: CheckBadgeIcon },
  { value: 'change_role', label: 'Смена роли', icon: ShieldCheckIcon },
  { value: 'change_ticket_status', label: 'Изменение статуса заявки', icon: ArrowPathIcon },
  { value: 'assign_ticket', label: 'Назначение заявки', icon: WrenchScrewdriverIcon },
]

const actionLabels: Record<string, string> = {
  ban: 'Блокировка',
  unban: 'Разблокировка',
  change_role: 'Смена роли',
  change_ticket_status: 'Смена статуса заявки',
  assign_ticket: 'Назначение заявки',
}

async function loadLogs() {
  loading.value = true
  try {
    const params: any = { page: page.value, page_size: pageSize }
    if (actionFilter.value) params.action = actionFilter.value
    const data = await adminAPI.getAuditLogs(params)
    logs.value = data.items
    total.value = data.total
  } catch (err) {
    toast.error((err as Error).message)
  } finally {
    loading.value = false
  }
}

function setFilter(action: string) {
  actionFilter.value = action
  page.value = 1
  loadLogs()
}

function goPage(p: number) {
  page.value = p
  loadLogs()
}

function formatDate(d: string) {
  return new Date(d).toLocaleString('ru-RU', { day: 'numeric', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' })
}

onMounted(async () => {
  if (!loaded.value) await fetchUsers()
  loadLogs()
})
</script>

<template>
  <div class="max-w-6xl mx-auto px-4 sm:px-6 py-8">
    <!-- Page header -->
    <div class="page-header">
      <h1 class="page-title flex items-center gap-2">
        <ClockIcon class="w-7 h-7 text-primary-600 dark:text-primary-400" />
        Аудит-лог
      </h1>
      <p class="page-subtitle">Всего записей: {{ total }}</p>
    </div>

    <!-- Filters -->
    <div class="flex flex-wrap gap-2 mb-6">
      <button
        v-for="a in actions"
        :key="a.value"
        @click="setFilter(a.value)"
        class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium transition-all"
        :class="actionFilter === a.value
          ? 'bg-primary-600 text-white shadow-sm'
          : 'bg-white dark:bg-gray-800 text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700 border border-gray-200 dark:border-gray-700'"
      >
        <component :is="a.icon" class="w-4 h-4" />
        {{ a.label }}
      </button>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="card overflow-hidden">
      <SkeletonTable :rows="8" :columns="5" />
    </div>

    <!-- Empty -->
    <div v-else-if="logs.length === 0" class="card p-12 text-center">
      <div class="w-16 h-16 rounded-2xl bg-gray-100 dark:bg-gray-800 flex items-center justify-center mx-auto mb-4">
        <ClockIcon class="w-8 h-8 text-gray-400" />
      </div>
      <p class="text-gray-500 dark:text-gray-400">Нет записей аудит-лога</p>
    </div>

    <!-- Table -->
    <div v-else class="card overflow-hidden">
      <div class="overflow-x-auto">
        <table class="w-full text-sm">
          <thead>
            <tr class="bg-gray-50 dark:bg-gray-800/50 border-b border-gray-200 dark:border-gray-700">
              <th class="text-left px-4 py-3 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">Дата</th>
              <th class="text-left px-4 py-3 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">Действие</th>
              <th class="text-left px-4 py-3 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">Администратор</th>
              <th class="text-left px-4 py-3 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">Цель</th>
              <th class="text-left px-4 py-3 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">Детали</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-100 dark:divide-gray-700">
            <tr v-for="log in logs" :key="log.id" class="hover:bg-gray-50 dark:hover:bg-gray-800/30 transition-colors">
              <td class="px-4 py-3 text-xs text-gray-500 whitespace-nowrap">{{ formatDate(log.created_at) }}</td>
              <td class="px-4 py-3">
                <span class="font-medium text-gray-900 dark:text-white">{{ actionLabels[log.action] || log.action }}</span>
              </td>
              <td class="px-4 py-3 text-sm text-gray-600 dark:text-gray-400">{{ getUserDisplay(log.admin_id) }}</td>
              <td class="px-4 py-3 text-xs">
                <template v-if="log.target_type === 'user'">
                  <span class="text-gray-700 dark:text-gray-300 font-medium">{{ getUserDisplay(log.target_id) }}</span>
                </template>
                <template v-else-if="log.target_type === 'ticket'">
                  <span class="text-gray-500">Заявка</span>
                </template>
                <span v-else class="text-gray-500">{{ log.target_type }}</span>
              </td>
              <td class="px-4 py-3 text-xs text-gray-500 max-w-xs truncate">{{ log.details || '—' }}</td>
            </tr>
          </tbody>
        </table>
      </div>

      <Pagination
        :page="page"
        :total-pages="totalPages"
        :total="total"
        @change="goPage"
      />
    </div>
  </div>
</template>
