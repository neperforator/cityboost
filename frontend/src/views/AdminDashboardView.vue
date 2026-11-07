<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { adminAPI } from '@/api'
import type { TicketStatus, BulkTicketResult } from '@/types'
import { useToast } from '@/composables/useToast'
import { useUsers } from '@/composables/useUsers'
import StatusBadge from '@/components/StatusBadge.vue'
import SkeletonTable from '@/components/SkeletonTable.vue'
import Pagination from '@/components/Pagination.vue'
import AdminTicketsMap from '@/components/AdminTicketsMap.vue'
import SelectionCheckbox from '@/components/SelectionCheckbox.vue'
import ConfirmDialog from '@/components/ConfirmDialog.vue'
import { InboxStackIcon, MagnifyingGlassIcon, ExclamationTriangleIcon, XMarkIcon, ListBulletIcon, MapIcon, CheckIcon } from '@heroicons/vue/24/outline'

const PAGE_SIZE = 15
const REPORT_PREVIEW = 3
const STATUS_LABELS: Record<TicketStatus, string> = {
  NEW: 'Новая',
  IN_WORK: 'В работе',
  DONE: 'Выполнена',
  CLOSED: 'Отклонена',
}

const route = useRoute()
const router = useRouter()
const toast = useToast()
const { getUserDisplay } = useUsers()

const tickets = ref<any[]>([])
const total = ref(0)
const page = ref(1)
const loading = ref(true)
const statusFilter = ref<TicketStatus | ''>(
  typeof route.query.status === 'string' && ['NEW', 'IN_WORK', 'DONE', 'CLOSED'].includes(route.query.status)
    ? (route.query.status as TicketStatus)
    : '',
)
const assigneeFilter = ref<'all' | 'me' | 'unassigned'>(
  route.query.assignee === 'me' || route.query.assignee === 'unassigned'
    ? route.query.assignee
    : 'all',
)
const overdueFilter = ref(route.query.overdue === '1' || route.query.overdue === 'true')
const viewMode = ref<'list' | 'map'>(route.query.view === 'map' ? 'map' : 'list')
const searchInput = ref('')
const searchQuery = ref('')
const selectedIds = ref<string[]>([])
const bulkStatus = ref<TicketStatus | ''>('')
const bulkCloseReason = ref('')
const bulkLoading = ref(false)
const bulkReport = ref<{ action: string; result: BulkTicketResult } | null>(null)
const reportDrawerOpen = ref(false)
const confirmAction = ref<'assign' | 'status' | null>(null)
let searchTimer: ReturnType<typeof setTimeout> | undefined

const totalPages = computed(() => Math.max(1, Math.ceil(total.value / PAGE_SIZE)))
const allSelected = computed(
  () => tickets.value.length > 0 && tickets.value.every(t => selectedIds.value.includes(t.id)),
)
const someSelected = computed(() => selectedIds.value.length > 0 && !allSelected.value)
const reportIssues = computed(() => {
  if (!bulkReport.value) return []
  const { result } = bulkReport.value
  return [
    ...result.skipped_items.map(item => ({
      key: `skip-${item.ticket_id}`,
      title: item.title || `Заявка ${item.ticket_id.slice(0, 8)}`,
      reason: item.reason,
      kind: 'skip' as const,
    })),
    ...result.errors.map(item => ({
      key: `error-${item.ticket_id}`,
      title: `Заявка ${item.ticket_id.slice(0, 8)}`,
      reason: item.detail,
      kind: 'error' as const,
    })),
  ]
})
const reportPreview = computed(() => reportIssues.value.slice(0, REPORT_PREVIEW))
const confirmTitle = computed(
  () => confirmAction.value === 'assign'
    ? 'Назначить заявки на себя?'
    : 'Изменить статус заявок?',
)
const confirmLabel = computed(
  () => confirmAction.value === 'assign'
    ? 'Назначить'
    : bulkStatus.value === 'CLOSED'
      ? 'Отклонить'
      : 'Применить',
)
const confirmTone = computed<'primary' | 'danger'>(
  () => confirmAction.value === 'status' && bulkStatus.value === 'CLOSED'
    ? 'danger'
    : 'primary',
)
const confirmStatusLabel = computed(
  () => (bulkStatus.value ? STATUS_LABELS[bulkStatus.value] : ''),
)
const confirmHint = computed(() => {
  if (confirmAction.value === 'assign') {
    return 'Заявки будут назначены на вас, «Новые» перейдут в работу. Автор получит письмо, если уведомления включены.'
  }
  if (bulkStatus.value === 'CLOSED') {
    return 'Заявки будут отклонены. Автор получит письмо с причиной отклонения.'
  }
  if (bulkStatus.value === 'DONE') {
    return 'Заявки будут отмечены выполненными. Автор получит письмо.'
  }
  return 'Автор получит письмо об изменении статуса, если уведомления включены.'
})

const stats = ref({
  total: 0,
  new: 0,
  in_work: 0,
  done: 0,
  closed: 0,
})

const filters = computed<{ key: TicketStatus | ''; label: string; count: number }[]>(() => [
  { key: '', label: 'Всего', count: stats.value.total },
  { key: 'NEW', label: 'Новые', count: stats.value.new },
  { key: 'IN_WORK', label: 'В работе', count: stats.value.in_work },
  { key: 'DONE', label: 'Выполнены', count: stats.value.done },
  { key: 'CLOSED', label: 'Отклонены', count: stats.value.closed },
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
  clearSelection()
  bulkReport.value = null
  reportDrawerOpen.value = false
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

function clearSelection() {
  selectedIds.value = []
  bulkStatus.value = ''
  bulkCloseReason.value = ''
}

function toggleSelect(id: string) {
  selectedIds.value = selectedIds.value.includes(id)
    ? selectedIds.value.filter(item => item !== id)
    : [...selectedIds.value, id]
}

function toggleSelectAll() {
  selectedIds.value = allSelected.value ? [] : tickets.value.map(ticket => ticket.id)
}

function showBulkReport(action: string, result: BulkTicketResult) {
  bulkReport.value = { action, result }
  if (result.failed > 0) {
    toast.warning(
      `${action}: обновлено ${result.updated}, пропущено ${result.skipped}, ошибок ${result.failed}`,
    )
    return
  }
  if (result.updated === 0) {
    toast.info(`${action}: ничего не изменено`)
    return
  }
  toast.success(
    `${action}: обновлено ${result.updated}` +
    (result.skipped ? `, пропущено ${result.skipped}` : ''),
  )
}

function openReportDrawer() {
  reportDrawerOpen.value = true
}

function closeReportDrawer() {
  reportDrawerOpen.value = false
}

function onDrawerKeydown(event: KeyboardEvent) {
  if (event.key === 'Escape') closeReportDrawer()
}

watch(reportDrawerOpen, (open) => {
  if (open) {
    window.addEventListener('keydown', onDrawerKeydown)
    document.body.style.overflow = 'hidden'
  } else {
    window.removeEventListener('keydown', onDrawerKeydown)
    document.body.style.overflow = ''
  }
})

function requestBulkAssign() {
  if (!selectedIds.value.length) return
  confirmAction.value = 'assign'
}

function requestBulkStatus() {
  if (!selectedIds.value.length || !bulkStatus.value) return
  if (bulkStatus.value === 'CLOSED' && !bulkCloseReason.value.trim()) {
    toast.warning('Укажите причину отклонения')
    return
  }
  confirmAction.value = 'status'
}

async function runConfirmedBulk() {
  const action = confirmAction.value
  if (!action) return
  confirmAction.value = null
  await (action === 'assign' ? applyBulkAssign() : applyBulkStatus())
}

async function applyBulkAssign() {
  if (!selectedIds.value.length) return
  bulkLoading.value = true
  try {
    const result = await adminAPI.bulkAssign(selectedIds.value)
    await Promise.all([loadStats(), loadTickets()])
    showBulkReport('Назначение на себя', result)
  } catch (err) {
    toast.error((err as Error).message)
  } finally {
    bulkLoading.value = false
  }
}

async function applyBulkStatus() {
  if (!selectedIds.value.length || !bulkStatus.value) return
  if (bulkStatus.value === 'CLOSED' && !bulkCloseReason.value.trim()) {
    toast.warning('Укажите причину отклонения')
    return
  }
  const action = `Смена статуса на «${STATUS_LABELS[bulkStatus.value]}»`
  bulkLoading.value = true
  try {
    const result = await adminAPI.bulkChangeStatus(
      selectedIds.value,
      bulkStatus.value,
      bulkStatus.value === 'CLOSED' ? bulkCloseReason.value.trim() : undefined,
    )
    await Promise.all([loadStats(), loadTickets()])
    showBulkReport(action, result)
  } catch (err) {
    toast.error((err as Error).message)
  } finally {
    bulkLoading.value = false
  }
}

function refreshActiveView() {
  if (viewMode.value === 'list') loadTickets()
}

function setFilter(status: TicketStatus | '') {
  statusFilter.value = status
  overdueFilter.value = false
  page.value = 1
  syncQuery()
  refreshActiveView()
}

function setAssignee(value: 'all' | 'me' | 'unassigned') {
  assigneeFilter.value = value
  page.value = 1
  syncQuery()
  refreshActiveView()
}

function clearOverdue() {
  overdueFilter.value = false
  page.value = 1
  syncQuery()
  refreshActiveView()
}

function resetFilters() {
  if (searchTimer) clearTimeout(searchTimer)
  searchInput.value = ''
  searchQuery.value = ''
  statusFilter.value = ''
  assigneeFilter.value = 'all'
  overdueFilter.value = false
  page.value = 1
  syncQuery()
  refreshActiveView()
}

function setViewMode(mode: 'list' | 'map') {
  if (viewMode.value === mode) return
  viewMode.value = mode
  syncQuery()
  if (mode === 'list') loadTickets()
}

function syncQuery() {
  const query: Record<string, string> = {}
  if (statusFilter.value) query.status = statusFilter.value
  if (assigneeFilter.value !== 'all') query.assignee = assigneeFilter.value
  if (overdueFilter.value) query.overdue = '1'
  if (viewMode.value === 'map') query.view = 'map'
  router.replace({ query })
}

function clearSearch() {
  if (searchTimer) clearTimeout(searchTimer)
  searchInput.value = ''
  searchQuery.value = ''
  page.value = 1
  refreshActiveView()
}

watch(searchInput, (value) => {
  if (searchTimer) clearTimeout(searchTimer)
  const next = value.trim()
  if (next === searchQuery.value) return
  searchTimer = setTimeout(() => {
    searchQuery.value = next
    page.value = 1
    refreshActiveView()
  }, 350)
})

onUnmounted(() => {
  if (searchTimer) clearTimeout(searchTimer)
  window.removeEventListener('keydown', onDrawerKeydown)
  if (reportDrawerOpen.value) document.body.style.overflow = ''
})

function viewTicket(id: string) {
  router.push(`/admin/tickets/${id}`)
}

function formatDate(d: string) {
  return new Date(d).toLocaleDateString('ru-RU', { day: 'numeric', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' })
}

onMounted(() => {
  loadStats()
  if (viewMode.value === 'list') loadTickets()
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
        <div class="flex w-full flex-col gap-2 sm:w-auto">
          <div class="inline-flex self-start border-2 border-line dark:border-line-dark sm:self-end">
            <button
              type="button"
              class="flex items-center gap-1.5 px-3 py-2 text-xs font-semibold transition-colors"
              :class="viewMode === 'list'
                ? 'bg-primary-500 text-white'
                : 'bg-surface text-ink-soft hover:bg-surface-muted dark:bg-surface-dark dark:text-ink-dark-soft dark:hover:bg-surface-dark-muted'"
              :aria-pressed="viewMode === 'list'"
              @click="setViewMode('list')"
            >
              <ListBulletIcon class="h-4 w-4" />
              Список
            </button>
            <button
              type="button"
              class="flex items-center gap-1.5 border-l-2 border-line px-3 py-2 text-xs font-semibold transition-colors dark:border-line-dark"
              :class="viewMode === 'map'
                ? 'bg-primary-500 text-white'
                : 'bg-surface text-ink-soft hover:bg-surface-muted dark:bg-surface-dark dark:text-ink-dark-soft dark:hover:bg-surface-dark-muted'"
              :aria-pressed="viewMode === 'map'"
              @click="setViewMode('map')"
            >
              <MapIcon class="h-4 w-4" />
              Карта
            </button>
          </div>
          <div class="flex flex-col gap-2 sm:flex-row sm:items-center">
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

    <Transition v-if="viewMode === 'list'" name="page" mode="out-in">
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
        <div v-if="selectedIds.length" class="mb-4 border-2 border-primary-500 bg-surface shadow-panel dark:border-primary-400 dark:bg-surface-dark">
          <div class="flex flex-col gap-3 px-4 py-3 lg:flex-row lg:items-center lg:justify-between lg:gap-6">
            <div class="flex items-center gap-3">
              <span class="inline-flex h-8 min-w-8 items-center justify-center bg-primary-500 px-2 font-display text-sm font-semibold tabular-nums text-white dark:bg-primary-400 dark:text-primary-900">
                {{ selectedIds.length }}
              </span>
              <div class="leading-tight">
                <p class="text-sm font-semibold text-ink dark:text-ink-dark">
                  {{ selectedIds.length === 1 ? 'Выбрана заявка' : 'Выбрано заявок' }}
                </p>
                <button
                  type="button"
                  class="text-xs font-medium text-primary-700 underline underline-offset-2 transition-colors hover:text-primary-900 dark:text-primary-300 dark:hover:text-primary-100"
                  @click="clearSelection"
                >
                  Снять выделение
                </button>
              </div>
            </div>

            <div class="flex flex-wrap items-center gap-x-4 gap-y-2">
              <button
                type="button"
                class="btn-secondary btn-sm"
                :disabled="bulkLoading"
                @click="requestBulkAssign"
              >
                Назначить на себя
              </button>

              <span class="hidden h-6 w-px bg-line sm:inline-block dark:bg-line-dark" aria-hidden="true"></span>

              <div class="flex flex-wrap items-center gap-2">
                <select
                  v-model="bulkStatus"
                  class="form-input-sm w-40"
                  aria-label="Новый статус выбранных заявок"
                  :disabled="bulkLoading"
                >
                  <option value="">Изменить статус…</option>
                  <option value="NEW">Новая</option>
                  <option value="IN_WORK">В работе</option>
                  <option value="DONE">Выполнена</option>
                  <option value="CLOSED">Отклонена</option>
                </select>
                <button
                  type="button"
                  class="btn-primary btn-sm"
                  :disabled="bulkLoading || !bulkStatus"
                  @click="requestBulkStatus"
                >
                  Применить
                </button>
              </div>
            </div>
          </div>
          <div v-if="bulkStatus === 'CLOSED'" class="border-t-2 border-line bg-accent-50 px-4 py-3 dark:border-line-dark dark:bg-accent-900/20">
            <label class="form-label" for="bulk-close-reason">Причина отклонения</label>
            <textarea
              id="bulk-close-reason"
              v-model="bulkCloseReason"
              class="form-input resize-y"
              rows="2"
              placeholder="Например: дубль заявки. Причина попадёт в письмо автору и в историю."
              :disabled="bulkLoading"
            ></textarea>
          </div>
        </div>

        <div v-if="bulkReport" class="mb-4 border-2 border-line bg-surface dark:border-line-dark dark:bg-surface-dark" role="status" aria-live="polite">
          <div class="flex items-start justify-between gap-3 border-b-2 border-line px-4 py-3 dark:border-line-dark">
            <div class="flex items-start gap-3">
              <span
                class="mt-0.5 inline-flex h-6 w-6 shrink-0 items-center justify-center rounded-full"
                :class="bulkReport.result.failed > 0 || bulkReport.result.skipped > 0
                  ? 'bg-accent-100 text-accent-700 dark:bg-accent-900/50 dark:text-accent-200'
                  : 'bg-primary-100 text-primary-700 dark:bg-primary-900/50 dark:text-primary-200'"
              >
                <ExclamationTriangleIcon
                  v-if="bulkReport.result.failed > 0 || bulkReport.result.skipped > 0"
                  class="h-3.5 w-3.5"
                />
                <CheckIcon v-else class="h-3.5 w-3.5" />
              </span>
              <div>
                <p class="text-sm font-semibold text-ink dark:text-ink-dark">{{ bulkReport.action }}</p>
                <p class="mt-0.5 text-xs text-ink-soft dark:text-ink-dark-soft">
                  Обновлено <span class="font-semibold tabular-nums text-ink dark:text-ink-dark">{{ bulkReport.result.updated }}</span>
                  · пропущено <span class="font-semibold tabular-nums text-ink dark:text-ink-dark">{{ bulkReport.result.skipped }}</span>
                  · ошибок <span class="font-semibold tabular-nums text-ink dark:text-ink-dark">{{ bulkReport.result.failed }}</span>
                </p>
              </div>
            </div>
            <button
              type="button"
              class="btn-ghost btn-icon btn-sm -mr-1 -mt-1"
              aria-label="Скрыть отчёт"
              @click="bulkReport = null"
            >
              <XMarkIcon class="h-4 w-4" />
            </button>
          </div>

          <template v-if="reportIssues.length">
            <ul class="divide-y-2 divide-line dark:divide-line-dark">
              <li
                v-for="issue in reportPreview"
                :key="issue.key"
                class="flex flex-col gap-1 px-4 py-2.5 sm:flex-row sm:items-baseline sm:justify-between sm:gap-4"
              >
                <span class="flex min-w-0 items-center gap-2">
                  <span
                    class="h-1.5 w-1.5 shrink-0 rounded-full"
                    :class="issue.kind === 'error' ? 'bg-red-600 dark:bg-red-400' : 'bg-accent-500'"
                  />
                  <span class="truncate text-sm font-medium text-ink dark:text-ink-dark">{{ issue.title }}</span>
                </span>
                <span
                  class="pl-3.5 text-xs sm:shrink-0 sm:pl-0 sm:text-right"
                  :class="issue.kind === 'error' ? 'text-red-700 dark:text-red-400' : 'text-ink-soft dark:text-ink-dark-soft'"
                >{{ issue.reason }}</span>
              </li>
            </ul>
            <div v-if="reportIssues.length > REPORT_PREVIEW" class="flex items-center justify-between gap-3 border-t-2 border-line px-4 py-2.5 dark:border-line-dark">
              <p class="text-xs text-ink-soft dark:text-ink-dark-soft">
                Показаны первые {{ REPORT_PREVIEW }} из {{ reportIssues.length }}
              </p>
              <button type="button" class="btn-secondary btn-sm" @click="openReportDrawer">
                Показать все
              </button>
            </div>
          </template>
        </div>
        <div class="panel overflow-hidden">
          <div class="overflow-x-auto">
            <table class="w-full text-sm">
              <thead>
                <tr class="border-b-2 border-line bg-surface-muted dark:border-line-dark dark:bg-surface-dark-muted">
                  <th class="w-12 px-3 py-3">
                    <SelectionCheckbox
                      :checked="allSelected"
                      :indeterminate="someSelected"
                      label="Выбрать все заявки на странице"
                      @toggle="toggleSelectAll"
                    />
                  </th>
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
                  :class="selectedIds.includes(t.id) && 'bg-primary-50 dark:bg-primary-900/20'"
                  @click="viewTicket(t.id)"
                  @keydown.enter.self="viewTicket(t.id)"
                  @keydown.space.prevent.self="viewTicket(t.id)"
                  tabindex="0"
                >
                  <td class="px-3 py-3.5" @click.stop>
                    <SelectionCheckbox
                      :checked="selectedIds.includes(t.id)"
                      :label="`Выбрать заявку «${t.title}»`"
                      @toggle="toggleSelect(t.id)"
                    />
                  </td>
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

    <AdminTicketsMap
      v-else
      class="mt-5"
      :status="statusFilter"
      :search="searchQuery"
      :assignee="assigneeFilter"
      :overdue="overdueFilter"
      @reset="resetFilters"
    />
  </div>

  <ConfirmDialog
    :open="confirmAction !== null"
    :title="confirmTitle"
    :confirm-label="confirmLabel"
    :tone="confirmTone"
    :busy="bulkLoading"
    @confirm="runConfirmedBulk"
    @cancel="confirmAction = null"
  >
    <div class="space-y-3 text-sm">
      <div class="flex items-baseline justify-between gap-4">
        <span class="text-ink-soft dark:text-ink-dark-soft">Заявок</span>
        <span class="font-semibold tabular-nums text-ink dark:text-ink-dark">{{ selectedIds.length }}</span>
      </div>
      <div v-if="confirmAction === 'status'" class="flex items-baseline justify-between gap-4">
        <span class="text-ink-soft dark:text-ink-dark-soft">Новый статус</span>
        <span class="font-semibold text-ink dark:text-ink-dark">{{ confirmStatusLabel }}</span>
      </div>
      <div v-else class="flex items-baseline justify-between gap-4">
        <span class="text-ink-soft dark:text-ink-dark-soft">Исполнитель</span>
        <span class="font-semibold text-ink dark:text-ink-dark">Вы</span>
      </div>
      <div
        v-if="confirmAction === 'status' && bulkStatus === 'CLOSED'"
        class="border-2 border-line bg-surface-muted px-3 py-2 dark:border-line-dark dark:bg-surface-dark-muted"
      >
        <p class="text-[11px] font-semibold uppercase tracking-wider text-ink-soft dark:text-ink-dark-soft">
          Причина отклонения
        </p>
        <p class="mt-1 text-sm text-ink dark:text-ink-dark">{{ bulkCloseReason.trim() }}</p>
      </div>
      <p class="text-xs leading-relaxed text-ink-soft dark:text-ink-dark-soft">{{ confirmHint }}</p>
      <p class="text-xs leading-relaxed text-ink-soft dark:text-ink-dark-soft">
        Заявки, которые нельзя изменить, будут пропущены — причины покажем после операции.
      </p>
    </div>
  </ConfirmDialog>

  <Teleport to="body">
    <Transition name="drawer">
      <div
        v-if="reportDrawerOpen && bulkReport"
        class="fixed inset-0 z-50"
        role="dialog"
        aria-modal="true"
        aria-labelledby="bulk-report-title"
      >
        <div class="absolute inset-0 bg-ink/50 dark:bg-black/70" @click="closeReportDrawer" />
        <div class="drawer-panel absolute right-0 top-0 flex h-full w-full max-w-lg flex-col border-l-2 border-line bg-surface shadow-2xl dark:border-line-dark dark:bg-surface-dark">
          <div class="flex items-start justify-between gap-3 border-b-2 border-line px-5 py-4 dark:border-line-dark">
            <div class="min-w-0">
              <p class="page-kicker">Результат операции</p>
              <h2 id="bulk-report-title" class="mt-1 font-display text-lg font-semibold text-ink dark:text-ink-dark">
                {{ bulkReport.action }}
              </h2>
              <p class="mt-1 text-xs text-ink-soft dark:text-ink-dark-soft">
                Обновлено {{ bulkReport.result.updated }} · пропущено {{ bulkReport.result.skipped }} · ошибок {{ bulkReport.result.failed }}
              </p>
            </div>
            <button
              type="button"
              class="btn-ghost btn-icon btn-sm -mr-1 -mt-1"
              aria-label="Закрыть панель"
              @click="closeReportDrawer"
            >
              <XMarkIcon class="h-5 w-5" />
            </button>
          </div>

          <ul class="flex-1 divide-y-2 divide-line overflow-y-auto dark:divide-line-dark">
            <li v-for="issue in reportIssues" :key="issue.key" class="px-5 py-3.5">
              <div class="flex items-start justify-between gap-3">
                <p class="min-w-0 text-sm font-medium text-ink dark:text-ink-dark">{{ issue.title }}</p>
                <span
                  class="shrink-0 border-2 px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wide"
                  :class="issue.kind === 'error'
                    ? 'border-red-200 bg-red-50 text-red-700 dark:border-red-900 dark:bg-red-900/30 dark:text-red-300'
                    : 'border-accent-200 bg-accent-50 text-accent-700 dark:border-accent-800 dark:bg-accent-900/30 dark:text-accent-200'"
                >{{ issue.kind === 'error' ? 'Ошибка' : 'Пропуск' }}</span>
              </div>
              <p class="mt-1 text-xs text-ink-soft dark:text-ink-dark-soft">{{ issue.reason }}</p>
            </li>
          </ul>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.drawer-enter-active,
.drawer-leave-active {
  transition: opacity 0.2s ease;
}
.drawer-enter-from,
.drawer-leave-to {
  opacity: 0;
}
.drawer-enter-active .drawer-panel,
.drawer-leave-active .drawer-panel {
  transition: transform 0.25s cubic-bezier(0.2, 0.8, 0.2, 1);
}
.drawer-enter-from .drawer-panel,
.drawer-leave-to .drawer-panel {
  transform: translateX(100%);
}
</style>
