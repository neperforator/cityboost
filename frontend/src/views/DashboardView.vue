<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ticketAPI } from '@/api'
import { useAuthStore } from '@/stores/auth'
import StatusBadge from '@/components/StatusBadge.vue'
import SkeletonCard from '@/components/SkeletonCard.vue'
import Pagination from '@/components/Pagination.vue'
import { PlusIcon } from '@heroicons/vue/24/solid'
import { InboxStackIcon, NewspaperIcon, WrenchScrewdriverIcon, CheckBadgeIcon, ArchiveBoxXMarkIcon, MapPinIcon, CalendarDaysIcon } from '@heroicons/vue/24/outline'

const PAGE_SIZE = 10

const auth = useAuthStore()
const router = useRouter()
const tickets = ref<any[]>([])
const total = ref(0)
const page = ref(1)
const loading = ref(true)
const error = ref('')
const activeFilter = ref('ALL')
const statsLoading = ref(true)

const totalPages = computed(() => Math.max(1, Math.ceil(total.value / PAGE_SIZE)))

const filters = [
  { key: 'ALL', label: 'Все', icon: InboxStackIcon },
  { key: 'NEW', label: 'Новые', icon: NewspaperIcon },
  { key: 'IN_WORK', label: 'В работе', icon: WrenchScrewdriverIcon },
  { key: 'DONE', label: 'Выполнены', icon: CheckBadgeIcon },
  { key: 'CLOSED', label: 'Закрыты', icon: ArchiveBoxXMarkIcon },
]

// Global stats from server
const stats = ref({
  total: 0,
  new: 0,
  in_work: 0,
  done: 0,
  closed: 0,
})

async function loadStats() {
  statsLoading.value = true
  try {
    stats.value = await ticketAPI.getStats()
  } catch {
    // fallback
  } finally {
    statsLoading.value = false
  }
}

async function loadTickets() {
  loading.value = true
  error.value = ''
  try {
    const statusParam = activeFilter.value === 'ALL' ? undefined : activeFilter.value
    const data = await ticketAPI.list(page.value, PAGE_SIZE, statusParam)
    tickets.value = data.items
    total.value = data.total
  } catch (err) {
    error.value = (err as Error).message
  } finally {
    loading.value = false
  }
}

function setFilter(key: string) {
  activeFilter.value = key
  page.value = 1
  loadTickets()
}

function onPageChange(newPage: number) {
  page.value = newPage
  loadTickets()
}

function goToCreate() {
  router.push('/tickets/create')
}

function viewTicket(id: string) {
  router.push(`/tickets/${id}`)
}

function statusCount(status: string) {
  if (status === 'ALL') return stats.value.total
  const map: Record<string, keyof typeof stats.value> = {
    'NEW': 'new',
    'IN_WORK': 'in_work',
    'DONE': 'done',
    'CLOSED': 'closed',
  }
  return stats.value[map[status] || 'total']
}

function formatDate(dateStr: string) {
  return new Date(dateStr).toLocaleDateString('ru-RU', { day: 'numeric', month: 'long', year: 'numeric' })
}

onMounted(() => {
  loadStats()
  loadTickets()
})
</script>

<template>
  <div class="max-w-7xl mx-auto px-4 sm:px-6 py-8">
    <!-- Page header -->
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-8">
      <div>
        <h1 class="text-2xl font-bold text-gray-900 dark:text-white tracking-tight">Мои заявки</h1>
        <p class="text-gray-500 dark:text-gray-400 text-sm mt-1">Всего заявок: {{ stats.total }}</p>
      </div>
      <button @click="goToCreate" class="btn-primary">
        <PlusIcon class="w-5 h-5" />
        Новая заявка
      </button>
    </div>

    <!-- Filters with global counts -->
    <div class="flex flex-wrap gap-2 mb-6">
      <button
        v-for="f in filters"
        :key="f.key"
        @click="setFilter(f.key)"
        class="inline-flex items-center gap-1.5 px-4 py-2 rounded-lg text-sm font-medium transition-all"
        :class="activeFilter === f.key
          ? 'bg-primary-600 text-white shadow-sm'
          : 'bg-white dark:bg-gray-800 text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700 border border-gray-200 dark:border-gray-700'"
      >
        <component :is="f.icon" class="w-4 h-4" />
        {{ f.label }}
        <span class="ml-1 opacity-75">({{ statusCount(f.key) }})</span>
      </button>
    </div>

    <!-- Content with transition -->
    <Transition name="page" mode="out-in">
      <!-- Loading -->
      <SkeletonCard v-if="loading" key="loading" :count="5" />

      <!-- Error -->
      <div v-else-if="error" key="error" class="card p-8 text-center">
        <p class="text-red-500 mb-4">{{ error }}</p>
        <button @click="loadTickets" class="btn-secondary">Повторить</button>
      </div>

      <!-- Empty state -->
      <div v-else-if="tickets.length === 0" key="empty" class="card p-12 text-center">
        <div class="w-16 h-16 rounded-2xl bg-gray-100 dark:bg-gray-800 flex items-center justify-center mx-auto mb-4">
          <InboxStackIcon class="w-8 h-8 text-gray-400" />
        </div>
        <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-1">
          {{ activeFilter === 'ALL' ? 'У вас пока нет заявок' : 'Нет заявок с таким статусом' }}
        </h3>
        <p class="text-gray-500 dark:text-gray-400 text-sm mb-6">
          {{ activeFilter === 'ALL' ? 'Создайте первую заявку — мы поможем решить вашу проблему' : 'Попробуйте другой фильтр' }}
        </p>
        <button v-if="activeFilter === 'ALL'" @click="goToCreate" class="btn-primary">
          <PlusIcon class="w-5 h-5" /> Создать заявку
        </button>
      </div>

      <!-- Ticket list -->
      <div v-else key="list" class="space-y-3">
        <div
          v-for="ticket in tickets"
          :key="ticket.id"
          @click="viewTicket(ticket.id)"
          class="card-hover p-5"
        >
          <div class="flex items-start justify-between gap-4">
            <div class="flex-1 min-w-0">
              <h3 class="font-semibold text-gray-900 dark:text-white truncate">{{ ticket.title }}</h3>
              <div class="flex flex-wrap items-center gap-3 mt-2 text-sm text-gray-500 dark:text-gray-400">
                <span class="inline-flex items-center gap-1">
                  <CalendarDaysIcon class="w-4 h-4" />
                  {{ formatDate(ticket.created_at) }}
                </span>
                <span v-if="ticket.address" class="inline-flex items-center gap-1 truncate max-w-xs">
                  <MapPinIcon class="w-4 h-4 shrink-0" />
                  {{ ticket.address }}
                </span>
              </div>
            </div>
            <StatusBadge :status="ticket.status" />
          </div>
        </div>
      </div>
    </Transition>

    <!-- Pagination -->
    <Pagination
      v-if="!loading && tickets.length > 0 && totalPages > 1"
      :page="page"
      :total-pages="totalPages"
      :total="total"
      @change="onPageChange"
    />
  </div>
</template>
