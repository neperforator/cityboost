<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { adminAPI } from '@/api'
import { useAuthStore } from '@/stores/auth'
import { useToast } from '@/composables/useToast'
import StatusBadge from '@/components/StatusBadge.vue'
import SkeletonTable from '@/components/SkeletonTable.vue'
import Pagination from '@/components/Pagination.vue'

const PAGE_SIZE = 15

const router = useRouter()
const auth = useAuthStore()
const toast = useToast()

const tickets = ref([])
const total = ref(0)
const page = ref(1)
const loading = ref(true)
const statusFilter = ref('')

const totalPages = computed(() => Math.max(1, Math.ceil(total.value / PAGE_SIZE)))

const stats = computed(() => {
  const all = tickets.value
  return {
    total: total.value,
    new: all.filter(t => t.status === 'NEW').length,
    inWork: all.filter(t => t.status === 'IN_WORK').length,
    done: all.filter(t => t.status === 'DONE').length,
    closed: all.filter(t => t.status === 'CLOSED').length,
  }
})

async function loadTickets() {
  loading.value = true
  try {
    const data = await adminAPI.listTickets({
      page: page.value,
      page_size: PAGE_SIZE,
      status: statusFilter.value || undefined,
    })
    tickets.value = data.items
    total.value = data.total
  } catch (err) {
    toast.error(err.message)
  } finally {
    loading.value = false
  }
}

function onPageChange(newPage: number) {
  page.value = newPage
  loadTickets()
}

function setFilter(status) {
  statusFilter.value = status
  loadTickets()
}

function viewTicket(id) {
  router.push(`/admin/tickets/${id}`)
}

function formatDate(d) {
  return new Date(d).toLocaleDateString('ru-RU', { day: 'numeric', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' })
}

onMounted(loadTickets)
</script>

<template>
  <div class="max-w-7xl mx-auto px-4 sm:px-6 py-8">
    <!-- Header -->
    <div class="mb-8">
      <h1 class="text-2xl font-extrabold text-gray-900 dark:text-white flex items-center gap-2">
        ⚙️ Админ-панель
        <span class="text-sm font-normal text-gray-500 dark:text-gray-400">— управление заявками</span>
      </h1>
    </div>

    <!-- Stats -->
    <div class="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-6">
      <button @click="setFilter('')" class="card p-4 text-left hover:shadow-md transition-shadow cursor-pointer" :class="statusFilter === '' ? 'ring-2 ring-primary-500' : ''">
        <p class="text-2xl font-bold text-gray-900 dark:text-white">{{ stats.total }}</p>
        <p class="text-sm text-gray-500 dark:text-gray-400">Всего</p>
      </button>
      <button @click="setFilter('NEW')" class="card p-4 text-left hover:shadow-md transition-shadow cursor-pointer" :class="statusFilter === 'NEW' ? 'ring-2 ring-blue-500' : ''">
        <p class="text-2xl font-bold text-blue-600 dark:text-blue-400">{{ stats.new }}</p>
        <p class="text-sm text-gray-500 dark:text-gray-400">🆕 Новые</p>
      </button>
      <button @click="setFilter('IN_WORK')" class="card p-4 text-left hover:shadow-md transition-shadow cursor-pointer" :class="statusFilter === 'IN_WORK' ? 'ring-2 ring-amber-500' : ''">
        <p class="text-2xl font-bold text-amber-600 dark:text-amber-400">{{ stats.inWork }}</p>
        <p class="text-sm text-gray-500 dark:text-gray-400">🔧 В работе</p>
      </button>
      <button @click="setFilter('DONE')" class="card p-4 text-left hover:shadow-md transition-shadow cursor-pointer" :class="statusFilter === 'DONE' ? 'ring-2 ring-emerald-500' : ''">
        <p class="text-2xl font-bold text-emerald-600 dark:text-emerald-400">{{ stats.done }}</p>
        <p class="text-sm text-gray-500 dark:text-gray-400">✅ Выполнены</p>
      </button>
    </div>

    <!-- Filters bar -->
    <div class="card p-4 mb-6">
      <div class="flex flex-wrap items-center gap-3">
        <div class="flex gap-1">
          <button @click="setFilter('')" class="btn-sm" :class="statusFilter === '' ? 'btn-primary' : 'btn-ghost'">Все</button>
          <button @click="setFilter('NEW')" class="btn-sm" :class="statusFilter === 'NEW' ? 'btn-primary' : 'btn-ghost'">Новые</button>
          <button @click="setFilter('IN_WORK')" class="btn-sm" :class="statusFilter === 'IN_WORK' ? 'btn-primary' : 'btn-ghost'">В работе</button>
          <button @click="setFilter('DONE')" class="btn-sm" :class="statusFilter === 'DONE' ? 'btn-primary' : 'btn-ghost'">Выполнены</button>
          <button @click="setFilter('CLOSED')" class="btn-sm" :class="statusFilter === 'CLOSED' ? 'btn-primary' : 'btn-ghost'">Закрыты</button>
        </div>
        <div class="flex-1"></div>
        <span class="text-sm text-gray-400">Всего: {{ total }}</span>
      </div>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="card overflow-hidden">
      <SkeletonTable :rows="6" :columns="6" />
    </div>

    <!-- Empty -->
    <div v-else-if="tickets.length === 0" class="card p-12 text-center">
      <div class="text-5xl mb-4">📭</div>
      <p class="text-gray-500 dark:text-gray-400 mb-4">Нет заявок с выбранным статусом</p>
      <button @click="setFilter('')" class="btn-secondary">Показать все</button>
    </div>

    <!-- Table -->
    <div v-else>
      <div class="card overflow-hidden">
        <div class="overflow-x-auto">
          <table class="w-full text-sm">
          <thead>
            <tr class="bg-gray-50 dark:bg-gray-800/50 border-b border-gray-200 dark:border-gray-700">
              <th class="text-left px-4 py-3 font-semibold text-gray-600 dark:text-gray-400">ID</th>
              <th class="text-left px-4 py-3 font-semibold text-gray-600 dark:text-gray-400">Заголовок</th>
              <th class="text-left px-4 py-3 font-semibold text-gray-600 dark:text-gray-400">Пользователь</th>
              <th class="text-left px-4 py-3 font-semibold text-gray-600 dark:text-gray-400">Статус</th>
              <th class="text-left px-4 py-3 font-semibold text-gray-600 dark:text-gray-400">Дата</th>
              <th class="text-right px-4 py-3 font-semibold text-gray-600 dark:text-gray-400">Действия</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-100 dark:divide-gray-700">
            <tr v-for="t in tickets" :key="t.id" class="hover:bg-gray-50 dark:hover:bg-gray-800/30 transition-colors">
              <td class="px-4 py-3 font-mono text-xs text-gray-500">{{ t.id.slice(0, 8) }}...</td>
              <td class="px-4 py-3 font-medium text-gray-900 dark:text-white max-w-xs truncate">{{ t.title }}</td>
              <td class="px-4 py-3 font-mono text-xs text-gray-500">{{ t.user_id.slice(0, 8) }}...</td>
              <td class="px-4 py-3"><StatusBadge :status="t.status" /></td>
              <td class="px-4 py-3 text-gray-500 text-xs whitespace-nowrap">{{ formatDate(t.created_at) }}</td>
              <td class="px-4 py-3 text-right">
                <button @click="viewTicket(t.id)" class="btn-primary btn-sm">Детали</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
    <Pagination
      :page="page"
      :total-pages="totalPages"
      :total="total"
      @change="onPageChange"
    />
  </div>
</template>
