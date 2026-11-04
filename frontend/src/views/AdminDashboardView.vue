<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { adminAPI } from '@/api'
import type { TicketStatus } from '@/types'
import { useToast } from '@/composables/useToast'
import { useUsers } from '@/composables/useUsers'
import StatusBadge from '@/components/StatusBadge.vue'
import SkeletonTable from '@/components/SkeletonTable.vue'
import Pagination from '@/components/Pagination.vue'
import { InboxStackIcon, MagnifyingGlassIcon, ExclamationTriangleIcon, XMarkIcon } from '@heroicons/vue/24/outline'

const PAGE_SIZE = 15

const route = useRoute()
const router = useRouter()
const toast = useToast()
const { getUserDisplay } = useUsers()

const tickets = ref<any[]>([])
const total = ref(0)
const page = ref(1)
const loading = ref(true)
const statusFilter = ref(
  typeof route.query.status === 'string' && ['NEW', 'IN_WORK', 'DONE', 'CLOSED'].includes(route.query.status)
    ? route.query.status
    : '',
)
const assigneeFilter = ref<'all' | 'me' | 'unassigned'>(
  route.query.assignee === 'me' || route.query.assignee === 'unassigned'
    ? route.query.assignee
    : 'all',
)
const overdueFilter = ref(route.query.overdue === '1' || route.query.overdue === 'true')
const searchInput = ref('')
const searchQuery = ref('')
let searchTimer: ReturnType<typeof setTimeout> | undefined

const totalPages = computed(() => Math.max(1, Math.ceil(total.value / PAGE_SIZE)))

const stats = ref({
  total: 0,
  new: 0,
  in_work: 0,
  done: 0,
  closed: 0,
})

const filters = computed(() => [
  { key: '', label: 'Всего', count: stats.value.total },
  { key: 'NEW', label: 'Новые', count: stats.value.new },
  { key: 'IN_WORK', label: 'В работе', count: stats.value.in_work },
  { key: 'DONE', label: 'Выполнены', count: stats.value.done },
])

async function loadStats() {
  try {
    stats.value = await adminAPI.getStats()
  } catch {
    // fallback
  }
}

async function loadTickets() {
  loading.value = true
  try {
    const data = await adminAPI.listTickets({
      page: page.value,
      page_size: PAGE_SIZE,
      status: (statusFilter.value || undefined) as TicketStatus | undefined,
      q: searchQuery.value || undefined,
      assignee: assigneeFilter.value,
      overdue: overdueFilter.value || undefined,
    })
    tickets.value = data.items
    total.value = data.total
  } catch (err) {
    toast.error((err as Error).message)
  } finally {
    loading.value = false
  }
}

function onPageChange(newPage: number) {
  page.value = newPage
  loadTickets()
}

function setFilter(status: string) {
  statusFilter.value = status
  overdueFilter.value = false
  page.value = 1
  syncQuery()
  loadTickets()
}

function setAssignee(value: 'all' | 'me' | 'unassigned') {
  assigneeFilter.value = value
  page.value = 1
  syncQuery()
  loadTickets()
}

function clearOverdue() {
  overdueFilter.value = false
  page.value = 1
  syncQuery()
  loadTickets()
}

function resetFilters() {
  statusFilter.value = ''
  assigneeFilter.value = 'all'
  overdueFilter.value = false
  page.value = 1
  syncQuery()
  loadTickets()
}

function syncQuery() {
  const query: Record<string, string> = {}
  if (statusFilter.value) query.status = statusFilter.value
  if (assigneeFilter.value !== 'all') query.assignee = assigneeFilter.value
  if (overdueFilter.value) query.overdue = '1'
  router.replace({ query })
}

function clearSearch() {
  if (searchTimer) clearTimeout(searchTimer)
  searchInput.value = ''
  searchQuery.value = ''
  page.value = 1
  loadTickets()
}

watch(searchInput, (value) => {
  if (searchTimer) clearTimeout(searchTimer)
  const next = value.trim()
  if (next === searchQuery.value) return
  searchTimer = setTimeout(() => {
    searchQuery.value = next
    page.value = 1
    loadTickets()
  }, 350)
})

onUnmounted(() => {
  if (searchTimer) clearTimeout(searchTimer)
})

function viewTicket(id: string) {
  router.push(`/admin/tickets/${id}`)
}

function formatDate(d: string) {
  return new Date(d).toLocaleDateString('ru-RU', { day: 'numeric', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' })
}

onMounted(() => {
  loadStats()
  loadTickets()
})
</script>

<template>
  <div class="mx-auto max-w-6xl px-4 py-8 sm:px-8 sm:py-10">
    <header class="border-b-2 border-line pb-7 dark:border-line-dark">
      <p class="page-kicker">Администрирование</p>
      <div class="mt-2 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h1 class="font-display text-3xl font-semibold tracking-tight text-ink dark:text-ink-dark">Все заявки</h1>
          <p class="mt-2 text-sm text-ink-soft dark:text-ink-dark-soft">Очередь обращений и распределение работы службы.</p>
        </div>
        <div class="flex w-full flex-col gap-2 sm:w-auto sm:flex-row sm:items-center">
          <div class="relative w-full sm:w-72">
            <MagnifyingGlassIcon class="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-ink-soft dark:text-ink-dark-soft" />
            <input
              v-model="searchInput"
              type="text"
              class="form-input pl-9"
              placeholder="Поиск: заявитель, название, адрес..."
              aria-label="Поиск заявок"
              @keydown.esc="clearSearch"
            />
          </div>
          <select
            :value="assigneeFilter"
            class="form-input sm:w-48"
            aria-label="Фильтр по исполнителю"
            @change="setAssignee(($event.target as HTMLSelectElement).value as 'all' | 'me' | 'unassigned')"
          >
            <option value="all">Все исполнители</option>
            <option value="me">На мне</option>
            <option value="unassigned">Без исполнителя</option>
          </select>
        </div>
      </div>
    </header>

    <div class="mt-6 overflow-x-auto scrollbar-none">
      <div class="flex min-w-max items-stretch border-2 border-line dark:border-line-dark">
        <button
          v-for="f in filters"
          :key="f.key"
          @click="setFilter(f.key)"
          class="flex items-center gap-2 border-r-2 border-line px-4 py-3 text-sm font-medium transition-colors last:border-r-0 dark:border-line-dark"
          :class="statusFilter === f.key
            ? 'bg-primary-500 text-white'
            : 'bg-surface text-ink-soft hover:bg-surface-muted dark:bg-surface-dark dark:text-ink-dark-soft dark:hover:bg-surface-dark-muted'"
        >
          {{ f.label }}
          <span class="text-xs font-semibold tabular-nums" :class="statusFilter === f.key ? 'text-primary-100' : 'text-ink-soft dark:text-ink-dark-soft'">{{ f.count }}</span>
        </button>
        <button
          v-if="overdueFilter"
          @click="clearOverdue"
          class="flex items-center gap-1.5 bg-red-600 px-3 py-2.5 text-sm font-medium text-white transition-colors hover:bg-red-700"
          aria-label="Сбросить фильтр просроченных заявок"
        >
          <ExclamationTriangleIcon class="h-3.5 w-3.5" />
          Просроченные
          <XMarkIcon class="h-3.5 w-3.5" />
        </button>
      </div>
    </div>

    <Transition name="page" mode="out-in">
      <div v-if="loading" key="loading" class="panel mt-5 overflow-hidden">
        <SkeletonTable :rows="6" :columns="5" />
      </div>

      <div v-else-if="tickets.length === 0" key="empty" class="panel mt-5 p-10 text-center">
        <InboxStackIcon class="mx-auto h-8 w-8 text-ink-soft dark:text-ink-dark-soft" />
        <p class="mt-3 text-sm text-ink-soft dark:text-ink-dark-soft">
          {{ searchQuery
            ? `Ничего не найдено по запросу «${searchQuery}»`
            : overdueFilter
              ? 'Просроченных заявок нет'
              : 'Нет заявок с выбранным статусом' }}
        </p>
        <button v-if="searchQuery" @click="clearSearch" class="btn-secondary btn-sm mt-4">Сбросить поиск</button>
        <button v-else @click="resetFilters" class="btn-secondary btn-sm mt-4">Сбросить фильтры</button>
      </div>

      <div v-else key="table" class="mt-5">
        <div class="panel overflow-hidden">
          <div class="overflow-x-auto">
            <table class="w-full text-sm">
              <thead>
                <tr class="border-b-2 border-line bg-surface-muted dark:border-line-dark dark:bg-surface-dark-muted">
                  <th class="px-4 py-3 text-left text-[11px] font-semibold uppercase tracking-wider text-ink-soft dark:text-ink-dark-soft">Заявка</th>
                  <th class="px-4 py-3 text-left text-[11px] font-semibold uppercase tracking-wider text-ink-soft dark:text-ink-dark-soft">Заявитель</th>
                  <th class="px-4 py-3 text-left text-[11px] font-semibold uppercase tracking-wider text-ink-soft dark:text-ink-dark-soft">Статус</th>
                  <th class="px-4 py-3 text-left text-[11px] font-semibold uppercase tracking-wider text-ink-soft dark:text-ink-dark-soft">Создана</th>
                  <th class="px-4 py-3 text-right text-[11px] font-semibold uppercase tracking-wider text-ink-soft dark:text-ink-dark-soft">Действие</th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="t in tickets"
                  :key="t.id"
                  class="cursor-pointer border-b-2 border-line transition-colors last:border-b-0 hover:bg-surface-muted focus:outline-none focus-visible:bg-surface-muted dark:border-line-dark dark:hover:bg-surface-dark-muted dark:focus-visible:bg-surface-dark-muted"
                  @click="viewTicket(t.id)"
                  @keydown.enter="viewTicket(t.id)"
                  @keydown.space.prevent="viewTicket(t.id)"
                  tabindex="0"
                >
                  <td class="max-w-xs truncate px-4 py-3.5 font-medium text-ink dark:text-ink-dark">{{ t.title }}</td>
                  <td class="px-4 py-3.5 text-ink-soft dark:text-ink-dark-soft">{{ t.user_name || getUserDisplay(t.user_id) }}</td>
                  <td class="px-4 py-3.5"><StatusBadge :status="t.status" /></td>
                  <td class="whitespace-nowrap px-4 py-3.5 text-xs text-ink-soft dark:text-ink-dark-soft">{{ formatDate(t.created_at) }}</td>
                  <td class="px-4 py-3.5 text-right">
                    <button @click.stop="viewTicket(t.id)" class="btn-ghost btn-sm">Открыть</button>
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
          @change="onPageChange"
        />
      </div>
    </Transition>
  </div>
</template>
