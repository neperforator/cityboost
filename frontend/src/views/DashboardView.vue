<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ticketAPI } from '@/api'
import { useAuthStore } from '@/stores/auth'
import StatusBadge from '@/components/StatusBadge.vue'
import SkeletonCard from '@/components/SkeletonCard.vue'
import Pagination from '@/components/Pagination.vue'
import { PlusIcon } from '@heroicons/vue/24/solid'
import { InboxStackIcon, MapPinIcon, CalendarDaysIcon, ChevronRightIcon, PhotoIcon, ExclamationTriangleIcon } from '@heroicons/vue/24/outline'

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

const stats = ref({
  total: 0,
  new: 0,
  in_work: 0,
  done: 0,
  closed: 0,
})

const filters = computed(() => [
  { key: '', label: 'Всего', value: stats.value.total },
  { key: 'NEW', label: 'Новые', value: stats.value.new },
  { key: 'IN_WORK', label: 'В работе', value: stats.value.in_work },
  { key: 'DONE', label: 'Выполнены', value: stats.value.done },
  { key: 'CLOSED', label: 'Отклонены', value: stats.value.closed },
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
  <div class="mx-auto max-w-5xl px-4 py-8 sm:px-8 sm:py-10">
    <!-- Page header -->
    <header class="flex flex-col gap-5 border-b-2 border-line pb-7 dark:border-line-dark sm:flex-row sm:items-end sm:justify-between">
      <div>
        <p class="page-kicker">Личный кабинет</p>
        <h1 class="mt-2 font-display text-3xl font-semibold leading-tight tracking-tight text-ink dark:text-ink-dark">
          {{ auth.userName }}
        </h1>
        <p class="mt-2 max-w-xl text-sm leading-6 text-ink-soft dark:text-ink-dark-soft">
          Ваши обращения в городскую службу. Каждая заявка проходит маршрут от регистрации до ответа.
        </p>
      </div>
      <button @click="goToCreate" class="btn-accent shrink-0">
        <PlusIcon class="h-5 w-5" />
        Новая заявка
      </button>
    </header>

    <!-- Status filter line -->
    <div class="mt-6 overflow-x-auto scrollbar-none">
      <div class="flex min-w-max items-stretch border-2 border-line dark:border-line-dark">
        <button
          v-for="f in filters"
          :key="f.key"
          @click="setFilter(f.key)"
          class="relative flex items-center gap-2 border-r-2 border-line px-4 py-3 text-sm font-medium transition-colors last:border-r-0 dark:border-line-dark"
          :class="activeFilter === f.key
            ? 'bg-primary-500 text-white'
            : 'bg-surface text-ink-soft hover:bg-surface-muted dark:bg-surface-dark dark:text-ink-dark-soft dark:hover:bg-surface-dark-muted'"
          :disabled="statsLoading"
        >
          {{ f.label }}
          <span
            class="text-xs font-semibold tabular-nums"
            :class="activeFilter === f.key ? 'text-primary-100' : 'text-ink-soft dark:text-ink-dark-soft'"
          >{{ f.value }}</span>
        </button>
      </div>
    </div>

    <Transition name="page" mode="out-in">
      <SkeletonCard v-if="loading" key="loading" :count="5" />

      <div v-else-if="error" key="error" class="panel mt-5 border-l-4 border-l-red-500 p-6">
        <div class="flex items-start gap-3">
          <ExclamationTriangleIcon class="mt-0.5 h-5 w-5 shrink-0 text-red-600 dark:text-red-400" />
          <div>
            <p class="font-semibold text-ink dark:text-ink-dark">Не удалось загрузить заявки</p>
            <p class="mt-1 text-sm text-ink-soft dark:text-ink-dark-soft">{{ error }}</p>
            <button @click="loadTickets" class="btn-secondary btn-sm mt-4">Повторить</button>
          </div>
        </div>
      </div>

      <div v-else-if="tickets.length === 0" key="empty" class="panel mt-5 p-10 text-center">
        <div class="mx-auto flex h-12 w-12 items-center justify-center rounded-sm border-2 border-line dark:border-line-dark">
          <InboxStackIcon class="h-6 w-6 text-ink-soft dark:text-ink-dark-soft" />
        </div>
        <h3 class="mt-4 font-display text-lg font-semibold text-ink dark:text-ink-dark">
          {{ activeFilter === '' ? 'Заявок пока нет' : 'Нет заявок с таким статусом' }}
        </h3>
        <p class="mx-auto mt-1 max-w-sm text-sm text-ink-soft dark:text-ink-dark-soft">
          {{ activeFilter === '' ? 'Создайте первую заявку — служба получит её и начнёт работу.' : 'Выберите другой статус в строке фильтров.' }}
        </p>
        <button v-if="activeFilter === ''" @click="goToCreate" class="btn-accent mt-5">
          <PlusIcon class="h-5 w-5" />
          Создать заявку
        </button>
      </div>

      <div v-else key="list" class="panel mt-5 overflow-hidden">
        <div
          v-for="ticket in tickets"
          :key="ticket.id"
          @click="viewTicket(ticket.id)"
          @keydown.enter="viewTicket(ticket.id)"
          @keydown.space.prevent="viewTicket(ticket.id)"
          role="link"
          tabindex="0"
          class="group relative flex items-start gap-4 border-b-2 border-line p-5 transition-colors last:border-b-0 hover:bg-surface-muted focus:outline-none focus-visible:bg-surface-muted dark:border-line-dark dark:hover:bg-surface-dark-muted dark:focus-visible:bg-surface-dark-muted"
        >
          <span class="mt-1.5 h-2.5 w-2.5 shrink-0 rounded-full border-2" :class="{
            'border-primary-500 bg-primary-500': ticket.status === 'NEW',
            'border-amber-500 bg-amber-400': ticket.status === 'IN_WORK',
            'border-emerald-500 bg-emerald-500': ticket.status === 'DONE',
            'border-ink-soft bg-transparent': ticket.status === 'CLOSED',
          }" />
          <div class="min-w-0 flex-1">
            <h3 class="truncate font-display text-base font-semibold text-ink dark:text-ink-dark">{{ ticket.title }}</h3>
            <div class="mt-2 flex flex-wrap items-center gap-x-4 gap-y-1.5 text-xs text-ink-soft dark:text-ink-dark-soft">
              <span class="inline-flex items-center gap-1.5">
                <CalendarDaysIcon class="h-3.5 w-3.5 shrink-0" />
                {{ formatDate(ticket.created_at) }}
              </span>
              <span v-if="ticket.address" class="inline-flex max-w-xs items-center gap-1.5">
                <MapPinIcon class="h-3.5 w-3.5 shrink-0" />
                <span class="truncate">{{ ticket.address }}</span>
              </span>
              <span v-if="ticket.files && ticket.files.length > 0" class="inline-flex items-center gap-1.5">
                <PhotoIcon class="h-3.5 w-3.5 shrink-0" />
                {{ ticket.files.length }}
              </span>
            </div>
          </div>
          <div class="flex shrink-0 items-center gap-2">
            <StatusBadge :status="ticket.status" />
            <ChevronRightIcon class="h-4 w-4 text-ink-soft transition-transform group-hover:translate-x-0.5 dark:text-ink-dark-soft" />
          </div>
        </div>
      </div>
    </Transition>

    <Pagination
      v-if="!loading && tickets.length > 0 && totalPages > 1"
      :page="page"
      :total-pages="totalPages"
      :total="total"
      @change="onPageChange"
    />
  </div>
</template>
