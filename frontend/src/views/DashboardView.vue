<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ticketAPI } from '@/api'
import { useAuthStore } from '@/stores/auth'
import StatusBadge from '@/components/StatusBadge.vue'
import SkeletonCard from '@/components/SkeletonCard.vue'
import Pagination from '@/components/Pagination.vue'

const PAGE_SIZE = 10

const auth = useAuthStore()
const router = useRouter()
const tickets = ref([])
const total = ref(0)
const page = ref(1)
const loading = ref(true)
const error = ref('')
const activeFilter = ref('ALL')

const totalPages = computed(() => Math.max(1, Math.ceil(total.value / PAGE_SIZE)))

const filters = [
  { key: 'ALL', label: 'Все', icon: '📋' },
  { key: 'NEW', label: 'Новые', icon: '🆕' },
  { key: 'IN_WORK', label: 'В работе', icon: '🔧' },
  { key: 'DONE', label: 'Выполнены', icon: '✅' },
  { key: 'CLOSED', label: 'Закрыты', icon: '📁' },
]

const filteredTickets = computed(() => {
  if (activeFilter.value === 'ALL') return tickets.value
  return tickets.value.filter(t => t.status === activeFilter.value)
})

async function loadTickets() {
  loading.value = true
  error.value = ''
  try {
    const data = await ticketAPI.list(page.value, PAGE_SIZE)
    tickets.value = data.items
    total.value = data.total
  } catch (err) {
    error.value = err.message
  } finally {
    loading.value = false
  }
}

function onPageChange(newPage: number) {
  page.value = newPage
  loadTickets()
}

function goToCreate() {
  router.push('/tickets/create')
}

function viewTicket(id) {
  router.push(`/tickets/${id}`)
}

function statusCount(status) {
  if (status === 'ALL') return total.value
  return tickets.value.filter(t => t.status === status).length
}

onMounted(loadTickets)
</script>

<template>
  <div class="max-w-7xl mx-auto px-4 sm:px-6 py-8">
    <!-- Header -->
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-8">
      <div>
        <h1 class="text-2xl font-extrabold text-gray-900 dark:text-white">Мои заявки</h1>
        <p class="text-gray-500 dark:text-gray-400 text-sm mt-0.5">Всего заявок: {{ total }}</p>
      </div>
      <button @click="goToCreate" class="btn-primary">
        <span class="text-lg">+</span>
        Новая заявка
      </button>
    </div>

    <!-- Filters -->
    <div class="flex flex-wrap gap-2 mb-6">
      <button
        v-for="f in filters"
        :key="f.key"
        @click="activeFilter = f.key"
        class="px-4 py-2 rounded-lg text-sm font-medium transition-all"
        :class="activeFilter === f.key
          ? 'bg-primary-600 text-white shadow-md'
          : 'bg-white dark:bg-gray-800 text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700 border border-gray-200 dark:border-gray-700'"
      >
        {{ f.icon }} {{ f.label }}
        <span class="ml-1.5 opacity-75">({{ statusCount(f.key) }})</span>
      </button>
    </div>

    <!-- Loading -->
    <SkeletonCard v-if="loading" count="5" />

    <!-- Error -->
    <div v-else-if="error" class="card p-8 text-center">
      <p class="text-red-500 mb-4">{{ error }}</p>
      <button @click="loadTickets" class="btn-secondary">Повторить</button>
    </div>

    <!-- Empty state -->
    <div v-else-if="filteredTickets.length === 0" class="card p-12 text-center">
      <div class="text-5xl mb-4">{{ activeFilter === 'ALL' ? '📋' : '📭' }}</div>
      <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-1">
        {{ activeFilter === 'ALL' ? 'У вас пока нет заявок' : 'Нет заявок с таким статусом' }}
      </h3>
      <p class="text-gray-500 dark:text-gray-400 text-sm mb-6">
        {{ activeFilter === 'ALL' ? 'Создайте первую заявку — мы поможем решить вашу проблему' : 'Попробуйте другой фильтр' }}
      </p>
      <button v-if="activeFilter === 'ALL'" @click="goToCreate" class="btn-primary">Создать заявку</button>
    </div>

    <!-- Ticket list -->
    <div v-else class="space-y-3">
      <div
        v-for="ticket in filteredTickets"
        :key="ticket.id"
        @click="viewTicket(ticket.id)"
        class="card-hover p-5"
      >
        <div class="flex items-start justify-between gap-4">
          <div class="flex-1 min-w-0">
            <h3 class="font-semibold text-gray-900 dark:text-white truncate">{{ ticket.title }}</h3>
            <div class="flex flex-wrap items-center gap-3 mt-1.5 text-sm text-gray-500 dark:text-gray-400">
              <span>📅 {{ new Date(ticket.created_at).toLocaleDateString('ru-RU', { day: 'numeric', month: 'long', year: 'numeric' }) }}</span>
              <span v-if="ticket.address" class="truncate max-w-xs">📍 {{ ticket.address }}</span>
              <span v-if="ticket.latitude">🗺️ {{ ticket.latitude }}, {{ ticket.longitude }}</span>
            </div>
          </div>
          <StatusBadge :status="ticket.status" />
        </div>
      </div>
    </div>

    <!-- Pagination -->
    <Pagination
      v-if="!loading && filteredTickets.length > 0"
      :page="page"
      :total-pages="totalPages"
      :total="total"
      @change="onPageChange"
    />
  </div>
</template>
