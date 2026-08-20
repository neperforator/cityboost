<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ticketAPI } from '@/api'
import { useAuthStore } from '@/stores/auth'
import StatusBadge from '@/components/StatusBadge.vue'
import SkeletonCard from '@/components/SkeletonCard.vue'
import Pagination from '@/components/Pagination.vue'
import { PlusIcon } from '@heroicons/vue/24/solid'
import { InboxStackIcon, NewspaperIcon, WrenchScrewdriverIcon, CheckBadgeIcon, ArchiveBoxXMarkIcon, MapPinIcon, CalendarDaysIcon, ChevronRightIcon, PhotoIcon, ExclamationTriangleIcon } from '@heroicons/vue/24/outline'

const PAGE_SIZE = 10

const auth = useAuthStore()
const router = useRouter()
const tickets = ref<any[]>([])
const total = ref(0)
const page = ref(1)
const loading = ref(true)
const error = ref('')
const activeFilter = ref('')
const statsLoading = ref(true)

const totalPages = computed(() => Math.max(1, Math.ceil(total.value / PAGE_SIZE)))

// Global stats from server
const stats = ref({
  total: 0,
  new: 0,
  in_work: 0,
  done: 0,
  closed: 0,
})

const statCards = computed(() => [
  { key: '', label: 'Всего заявок', value: stats.value.total, icon: InboxStackIcon, bg: 'bg-primary-50 dark:bg-primary-900/30', color: 'text-primary-600 dark:text-primary-400', ring: 'ring-primary-500' },
  { key: 'NEW', label: 'Новые', value: stats.value.new, icon: NewspaperIcon, bg: 'bg-blue-50 dark:bg-blue-900/30', color: 'text-blue-600 dark:text-blue-400', ring: 'ring-blue-500' },
  { key: 'IN_WORK', label: 'В работе', value: stats.value.in_work, icon: WrenchScrewdriverIcon, bg: 'bg-amber-50 dark:bg-amber-900/30', color: 'text-amber-600 dark:text-amber-400', ring: 'ring-amber-500' },
  { key: 'DONE', label: 'Выполнены', value: stats.value.done, icon: CheckBadgeIcon, bg: 'bg-emerald-50 dark:bg-emerald-900/30', color: 'text-emerald-600 dark:text-emerald-400', ring: 'ring-emerald-500' },
  { key: 'CLOSED', label: 'Закрыты', value: stats.value.closed, icon: ArchiveBoxXMarkIcon, bg: 'bg-gray-100 dark:bg-gray-800/60', color: 'text-gray-500 dark:text-gray-400', ring: 'ring-gray-500' },
])

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
    const statusParam = activeFilter.value || undefined
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
    <!-- Hero -->
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-8">
      <div>
        <h1 class="font-display text-2xl sm:text-3xl font-bold text-gray-900 dark:text-white tracking-tight">
          Добро пожаловать, <span class="text-primary-600 dark:text-primary-400">{{ auth.userName }}</span>
        </h1>
        <p class="mt-1.5 text-sm text-gray-500 dark:text-gray-400">
          Следите за статусами заявок — мы держим вас в курсе каждого шага
        </p>
      </div>
      <button @click="goToCreate" class="btn-accent shrink-0">
        <PlusIcon class="w-5 h-5" />
        Новая заявка
      </button>
    </div>

    <!-- Stat cards (click to filter) -->
    <div class="grid grid-cols-2 sm:grid-cols-3 xl:grid-cols-5 gap-3 sm:gap-4 mb-8">
      <button
        v-for="s in statCards"
        :key="s.key"
        @click="setFilter(s.key)"
        class="stat-card min-w-0 text-left cursor-pointer hover:shadow-md transition-shadow focus:outline-none focus-visible:ring-2 focus-visible:ring-primary-500/40 focus-visible:ring-offset-2"
        :class="[
          activeFilter === s.key ? `ring-2 ${s.ring}` : '',
          { 'opacity-70': statsLoading },
        ]"
      >
        <div class="stat-icon shrink-0" :class="s.bg">
          <component :is="s.icon" class="w-6 h-6" :class="s.color" />
        </div>
        <div class="min-w-0">
          <p class="stat-value leading-none">{{ s.value }}</p>
          <p class="stat-label mt-1.5 truncate">{{ s.label }}</p>
        </div>
      </button>
    </div>

    <!-- Content with transition -->
    <Transition name="page" mode="out-in">
      <!-- Loading -->
      <SkeletonCard v-if="loading" key="loading" :count="5" />

      <!-- Error -->
      <div v-else-if="error" key="error" class="card p-12 text-center">
        <div class="w-16 h-16 rounded-2xl bg-red-50 dark:bg-red-900/20 flex items-center justify-center mx-auto mb-4">
          <ExclamationTriangleIcon class="w-8 h-8 text-red-500" />
        </div>
        <p class="text-gray-700 dark:text-gray-200 font-medium mb-1">Не удалось загрузить заявки</p>
        <p class="text-sm text-gray-500 dark:text-gray-400 mb-6">{{ error }}</p>
        <button @click="loadTickets" class="btn-secondary">Повторить</button>
      </div>

      <!-- Empty state -->
      <div v-else-if="tickets.length === 0" key="empty" class="card p-12 text-center">
        <div class="w-16 h-16 rounded-2xl bg-primary-50 dark:bg-primary-900/30 flex items-center justify-center mx-auto mb-4">
          <InboxStackIcon class="w-8 h-8 text-primary-500" />
        </div>
        <h3 class="font-display text-lg font-semibold text-gray-900 dark:text-white mb-1">
          {{ activeFilter === '' ? 'У вас пока нет заявок' : 'Нет заявок с таким статусом' }}
        </h3>
        <p class="text-gray-500 dark:text-gray-400 text-sm mb-6">
          {{ activeFilter === '' ? 'Создайте первую заявку — мы поможем решить вашу проблему' : 'Попробуйте другой фильтр' }}
        </p>
        <button v-if="activeFilter === ''" @click="goToCreate" class="btn-accent">
          <PlusIcon class="w-5 h-5" /> Создать заявку
        </button>
      </div>

      <!-- Ticket list -->
      <div v-else key="list" class="space-y-3">
        <div
          v-for="ticket in tickets"
          :key="ticket.id"
          @click="viewTicket(ticket.id)"
          @keydown.enter="viewTicket(ticket.id)"
          @keydown.space.prevent="viewTicket(ticket.id)"
          role="link"
          tabindex="0"
          class="card-hover p-5 focus:outline-none focus-visible:ring-2 focus-visible:ring-primary-500/40"
        >
          <div class="flex items-start justify-between gap-4">
            <div class="flex-1 min-w-0">
              <h3 class="font-display font-semibold text-gray-900 dark:text-white truncate">{{ ticket.title }}</h3>
              <div class="flex flex-wrap items-center gap-x-4 gap-y-1.5 mt-2 text-sm text-gray-500 dark:text-gray-400">
                <span class="inline-flex items-center gap-1.5">
                  <CalendarDaysIcon class="w-4 h-4 shrink-0" />
                  {{ formatDate(ticket.created_at) }}
                </span>
                <span v-if="ticket.address" class="inline-flex items-center gap-1.5 truncate max-w-xs">
                  <MapPinIcon class="w-4 h-4 shrink-0" />
                  <span class="truncate">{{ ticket.address }}</span>
                </span>
                <span v-if="ticket.files && ticket.files.length > 0" class="inline-flex items-center gap-1.5">
                  <PhotoIcon class="w-4 h-4 shrink-0" />
                  {{ ticket.files.length }}
                </span>
              </div>
            </div>
            <div class="flex items-center gap-2 shrink-0">
              <StatusBadge :status="ticket.status" />
              <ChevronRightIcon class="w-4 h-4 text-gray-300 dark:text-gray-600" />
            </div>
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
