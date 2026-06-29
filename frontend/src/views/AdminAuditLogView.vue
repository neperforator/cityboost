<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { adminAPI } from '@/api'
import { useToast } from '@/composables/useToast'
import Pagination from '@/components/Pagination.vue'
import SkeletonTable from '@/components/SkeletonTable.vue'

const toast = useToast()

const logs = ref([])
const total = ref(0)
const loading = ref(true)
const page = ref(1)
const pageSize = 30
const actionFilter = ref('')
const totalPages = computed(() => Math.max(1, Math.ceil(total.value / pageSize)))

const actions = [
  { value: '', label: 'Все действия' },
  { value: 'ban', label: '🚫 Блокировка' },
  { value: 'unban', label: '✅ Разблокировка' },
  { value: 'change_role', label: '👤 Смена роли' },
  { value: 'change_ticket_status', label: '📌 Изменение статуса заявки' },
  { value: 'assign_ticket', label: '📋 Назначение заявки' },
]

async function loadLogs() {
  loading.value = true
  try {
    const params = { page: page.value, page_size: pageSize }
    if (actionFilter.value) params.action = actionFilter.value
    const data = await adminAPI.getAuditLogs(params)
    logs.value = data.items
    total.value = data.total
  } catch (err) {
    toast.error(err.message)
  } finally {
    loading.value = false
  }
}

function setFilter(action) {
  actionFilter.value = action
  page.value = 1
  loadLogs()
}

function prevPage() {
  if (page.value > 1) { page.value--; loadLogs() }
}

function nextPage() {
  if (page.value < totalPages.value) { page.value++; loadLogs() }
}

function goPage(p) {
  page.value = p
  loadLogs()
}

function actionLabel(action) {
  const labels = {
    ban: '🚫 Блокировка',
    unban: '✅ Разблокировка',
    change_role: '👤 Смена роли',
    change_ticket_status: '📌 Смена статуса заявки',
    assign_ticket: '📋 Назначение заявки',
  }
  return labels[action] || action
}

function formatDate(d) {
  return new Date(d).toLocaleString('ru-RU', { day: 'numeric', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' })
}

onMounted(loadLogs)
</script>

<template>
  <div class="max-w-6xl mx-auto px-4 sm:px-6 py-8">
    <!-- Header -->
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-8">
      <div>
        <h1 class="text-2xl font-extrabold text-gray-900 dark:text-white flex items-center gap-2">📋 Аудит-лог</h1>
        <p class="text-sm text-gray-500 dark:text-gray-400 mt-0.5">Всего записей: {{ total }}</p>
      </div>
    </div>

    <!-- Filters -->
    <div class="flex flex-wrap gap-2 mb-6">
      <button
        v-for="a in actions"
        :key="a.value"
        @click="setFilter(a.value)"
        class="px-3 py-1.5 rounded-lg text-sm font-medium transition-all"
        :class="actionFilter === a.value
          ? 'bg-primary-600 text-white shadow-md'
          : 'bg-white dark:bg-gray-800 text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700 border border-gray-200 dark:border-gray-700'"
      >
        {{ a.label }}
      </button>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="card overflow-hidden">
      <SkeletonTable :rows="8" :columns="5" />
    </div>

    <!-- Empty -->
    <div v-else-if="logs.length === 0" class="card p-12 text-center">
      <div class="text-5xl mb-4">📭</div>
      <p class="text-gray-500 dark:text-gray-400">Нет записей аудит-лога</p>
    </div>

    <!-- Table -->
    <div v-else class="card overflow-hidden">
      <div class="overflow-x-auto">
        <table class="w-full text-sm">
          <thead>
            <tr class="bg-gray-50 dark:bg-gray-800/50 border-b border-gray-200 dark:border-gray-700">
              <th class="text-left px-4 py-3 font-semibold text-gray-600 dark:text-gray-400">Дата</th>
              <th class="text-left px-4 py-3 font-semibold text-gray-600 dark:text-gray-400">Действие</th>
              <th class="text-left px-4 py-3 font-semibold text-gray-600 dark:text-gray-400">Администратор</th>
              <th class="text-left px-4 py-3 font-semibold text-gray-600 dark:text-gray-400">Цель</th>
              <th class="text-left px-4 py-3 font-semibold text-gray-600 dark:text-gray-400">Детали</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-100 dark:divide-gray-700">
            <tr v-for="log in logs" :key="log.id" class="hover:bg-gray-50 dark:hover:bg-gray-800/30 transition-colors">
              <td class="px-4 py-3 text-xs text-gray-500 whitespace-nowrap">{{ formatDate(log.created_at) }}</td>
              <td class="px-4 py-3">
                <span class="font-medium text-gray-900 dark:text-white">{{ actionLabel(log.action) }}</span>
              </td>
              <td class="px-4 py-3 font-mono text-xs text-gray-500">{{ log.admin_id.slice(0, 8) }}...</td>
              <td class="px-4 py-3 text-xs">
                <span class="text-gray-500 font-mono">{{ log.target_type }}:</span>
                <span class="font-mono text-gray-400 ml-1">{{ log.target_id?.slice(0, 8) }}...</span>
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
