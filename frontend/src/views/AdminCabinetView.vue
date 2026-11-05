<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import type { Component } from 'vue'
import { useRouter } from 'vue-router'
import type { RouteLocationRaw } from 'vue-router'
import { adminAPI } from '@/api'
import type { AdminActionLog, AdminDashboardStats, Ticket, TicketStatus } from '@/types'
import { useAuthStore } from '@/stores/auth'
import { useToast } from '@/composables/useToast'
import StatusBadge from '@/components/StatusBadge.vue'
import SkeletonCard from '@/components/SkeletonCard.vue'
import {
  ArrowPathIcon,
  ArrowRightIcon,
  CheckBadgeIcon,
  CheckCircleIcon,
  ClockIcon,
  ExclamationTriangleIcon,
  InboxStackIcon,
  NoSymbolIcon,
  ShieldCheckIcon,
  WrenchScrewdriverIcon,
} from '@heroicons/vue/24/outline'

type TabKey = 'all' | TicketStatus

interface KpiCard {
  key: string
  label: string
  value: number
  hint: string
  icon: Component
  tone: 'primary' | 'accent' | 'emerald' | 'red'
  to: RouteLocationRaw
}

const MY_TICKETS_LIMIT = 20
const QUEUE_LIMIT = 10

const auth = useAuthStore()
const router = useRouter()
const toast = useToast()

const data = ref<AdminDashboardStats | null>(null)
const myTickets = ref<Ticket[]>([])
const myTicketsLoading = ref(true)
const loading = ref(true)
const error = ref('')
const assigning = ref<string | null>(null)
const activeTab = ref<TabKey>('all')
let myTicketsRequest = 0

const today = new Date().toLocaleDateString('ru-RU', {
  day: 'numeric',
  month: 'long',
  year: 'numeric',
})

const toneClasses: Record<KpiCard['tone'], { icon: string; bar: string }> = {
  primary: { icon: 'text-primary-600 dark:text-primary-300', bar: 'bg-primary-500' },
  accent: { icon: 'text-accent-600 dark:text-accent-300', bar: 'bg-accent-500' },
  emerald: { icon: 'text-emerald-600 dark:text-emerald-400', bar: 'bg-emerald-500' },
  red: { icon: 'text-red-600 dark:text-red-400', bar: 'bg-red-600' },
}

const kpis = computed<KpiCard[]>(() => {
  const assigned = data.value?.assigned
  return [
    {
      key: 'mine',
      label: 'На мне',
      value: assigned?.in_work ?? 0,
      hint: 'заявок в работе',
      icon: WrenchScrewdriverIcon,
      tone: 'primary',
      to: { path: '/admin/tickets', query: { assignee: 'me', status: 'IN_WORK' } },
    },
    {
      key: 'queue',
      label: 'В очереди',
      value: data.value?.queue ?? 0,
      hint: 'новых без исполнителя',
      icon: InboxStackIcon,
      tone: 'accent',
      to: { path: '/admin/tickets', query: { assignee: 'unassigned', status: 'NEW' } },
    },
    {
      key: 'done',
      label: 'Решено мной',
      value: assigned?.done ?? 0,
      hint: 'выполненных заявок',
      icon: CheckCircleIcon,
      tone: 'emerald',
      to: { path: '/admin/tickets', query: { assignee: 'me', status: 'DONE' } },
    },
    {
      key: 'overdue',
      label: 'Просрочено',
      value: data.value?.overdue ?? 0,
      hint: 'в работе дольше 15 дней',
      icon: ExclamationTriangleIcon,
      tone: 'red',
      to: { path: '/admin/tickets', query: { assignee: 'me', status: 'IN_WORK', overdue: '1' } },
    },
  ]
})

const tabs = computed<Array<{ key: TabKey; label: string; count: number }>>(() => {
  const assigned = data.value?.assigned
  return [
    { key: 'all', label: 'Все мои', count: assigned?.total ?? 0 },
    { key: 'IN_WORK', label: 'В работе', count: assigned?.in_work ?? 0 },
    { key: 'DONE', label: 'Выполнены', count: assigned?.done ?? 0 },
    { key: 'CLOSED', label: 'Закрыты', count: assigned?.closed ?? 0 },
  ]
})

const queuePreview = computed(() => (data.value?.queue_tickets ?? []).slice(0, QUEUE_LIMIT))

const mineLink = computed(() => ({
  path: '/admin/tickets',
  query: {
    assignee: 'me',
    ...(activeTab.value !== 'all' ? { status: activeTab.value } : {}),
  },
}))

const actionLabels: Record<string, string> = {
  ban: 'Блокировка',
  unban: 'Разблокировка',
  change_role: 'Смена роли',
  change_ticket_status: 'Смена статуса заявки',
  assign_ticket: 'Назначение заявки',
}

const actionIcons: Record<string, Component> = {
  ban: NoSymbolIcon,
  unban: CheckBadgeIcon,
  change_role: ShieldCheckIcon,
  change_ticket_status: ArrowPathIcon,
  assign_ticket: WrenchScrewdriverIcon,
}

function actionIcon(action: string): Component {
  return actionIcons[action] || ClockIcon
}

async function loadDashboard(silent = false) {
  if (!silent) loading.value = true
  error.value = ''
  try {
    data.value = await adminAPI.getDashboard()
  } catch (err) {
    if (!silent) error.value = (err as Error).message
    else toast.error((err as Error).message)
  } finally {
    loading.value = false
  }
}

async function loadMyTickets() {
  const requestId = ++myTicketsRequest
  myTicketsLoading.value = true
  try {
    const response = await adminAPI.listTickets({
      assignee: 'me',
      page: 1,
      page_size: MY_TICKETS_LIMIT,
      status: activeTab.value === 'all' ? undefined : activeTab.value,
    })
    if (requestId !== myTicketsRequest) return
    myTickets.value = response.items
  } catch (err) {
    if (requestId === myTicketsRequest) toast.error((err as Error).message)
  } finally {
    if (requestId === myTicketsRequest) myTicketsLoading.value = false
  }
}

function selectTab(tab: TabKey) {
  if (activeTab.value === tab) return
  activeTab.value = tab
  loadMyTickets()
}

async function assignToMe(ticket: Ticket) {
  if (assigning.value) return
  assigning.value = ticket.id
  try {
    await adminAPI.assign(ticket.id)
    toast.success(`Заявка «${ticket.title}» назначена на вас`)
    await Promise.all([loadDashboard(true), loadMyTickets()])
  } catch (err) {
    toast.error((err as Error).message)
  } finally {
    assigning.value = null
  }
}

function goTicket(id: string) {
  router.push(`/admin/tickets/${id}`)
}

function formatDate(dateStr: string) {
  return new Date(dateStr).toLocaleDateString('ru-RU', {
    day: 'numeric',
    month: 'short',
    hour: '2-digit',
    minute: '2-digit',
  })
}

function waitingLabel(dateStr: string) {
  const days = Math.floor((Date.now() - new Date(dateStr).getTime()) / 86_400_000)
  if (days <= 0) return 'сегодня'
  if (days === 1) return '1 день'
  if (days < 5) return `${days} дня`
  return `${days} дней`
}

function timeAgo(dateStr: string) {
  const diff = Date.now() - new Date(dateStr).getTime()
  const minutes = Math.floor(diff / 60_000)
  if (minutes < 1) return 'только что'
  if (minutes < 60) return `${minutes} мин назад`
  const hours = Math.floor(minutes / 60)
  if (hours < 24) return `${hours} ч назад`
  const days = Math.floor(hours / 24)
  if (days === 1) return 'вчера'
  if (days < 7) return `${days} дн. назад`
  return new Date(dateStr).toLocaleDateString('ru-RU', { day: 'numeric', month: 'short' })
}

function truncate(value: string, limit: number) {
  return value.length > limit ? `${value.slice(0, limit)}…` : value
}

function targetLabel(log: AdminActionLog) {
  if (log.target_type === 'ticket') {
    return log.target_name ? `Заявка «${truncate(log.target_name, 48)}»` : 'Заявка'
  }
  if (log.target_type === 'user') {
    return log.target_name || 'Пользователь'
  }
  return log.target_type
}

onMounted(() => {
  loadDashboard()
  loadMyTickets()
})
</script>

<template>
  <div class="mx-auto max-w-6xl px-4 py-8 sm:px-8 sm:py-10">
    <header class="border-b-2 border-line pb-7 dark:border-line-dark">
      <p class="page-kicker">Администрирование</p>
      <div class="mt-2 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h1 class="font-display text-3xl font-semibold tracking-tight text-ink dark:text-ink-dark">
            Кабинет администратора
          </h1>
          <p class="mt-2 text-sm text-ink-soft dark:text-ink-dark-soft">
            {{ auth.userName }} · {{ today }}
          </p>
        </div>
        <div class="flex flex-wrap items-center gap-2">
          <router-link to="/admin/tickets" class="btn-secondary btn-sm">Все заявки</router-link>
          <router-link
            :to="{ path: '/admin/tickets', query: { assignee: 'unassigned', status: 'NEW' } }"
            class="btn-secondary btn-sm"
          >
            Очередь
          </router-link>
        </div>
      </div>
    </header>

    <Transition name="page" mode="out-in">
      <div v-if="loading" key="loading" class="mt-6 space-y-5">
        <div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <div v-for="i in 4" :key="i" class="panel p-5">
            <div class="skeleton h-3 w-20" />
            <div class="skeleton mt-3 h-8 w-16" />
            <div class="skeleton mt-2 h-3 w-28" />
          </div>
        </div>
        <SkeletonCard :count="3" />
      </div>

      <div v-else-if="error" key="error" class="panel mt-6 border-l-4 border-l-red-500 p-6">
        <div class="flex items-start gap-3">
          <ExclamationTriangleIcon class="mt-0.5 h-5 w-5 shrink-0 text-red-600 dark:text-red-400" />
          <div>
            <p class="font-semibold text-ink dark:text-ink-dark">Не удалось загрузить кабинет</p>
            <p class="mt-1 text-sm text-ink-soft dark:text-ink-dark-soft">{{ error }}</p>
            <button @click="loadDashboard()" class="btn-secondary btn-sm mt-4">Повторить</button>
          </div>
        </div>
      </div>

      <div v-else-if="data" key="content" class="mt-6">
        <!-- KPI -->
        <div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <router-link
            v-for="kpi in kpis"
            :key="kpi.key"
            :to="kpi.to"
            class="panel group relative overflow-hidden p-5 transition-colors hover:bg-surface-muted focus:outline-none focus-visible:ring-2 focus-visible:ring-primary-500 dark:hover:bg-surface-dark-muted"
          >
            <span class="absolute inset-x-0 top-0 h-1" :class="toneClasses[kpi.tone].bar" />
            <div class="flex items-start justify-between gap-3">
              <div class="min-w-0">
                <p class="text-[11px] font-semibold uppercase tracking-wider text-ink-soft dark:text-ink-dark-soft">
                  {{ kpi.label }}
                </p>
                <p class="mt-2 font-display text-3xl font-semibold tabular-nums leading-none text-ink dark:text-ink-dark">
                  {{ kpi.value }}
                </p>
                <p class="mt-2 text-xs text-ink-soft dark:text-ink-dark-soft">{{ kpi.hint }}</p>
              </div>
              <span class="flex h-10 w-10 shrink-0 items-center justify-center border-2 border-line dark:border-line-dark">
                <component :is="kpi.icon" class="h-5 w-5" :class="toneClasses[kpi.tone].icon" />
              </span>
            </div>
            <span class="mt-4 inline-flex items-center gap-1 text-xs font-medium text-primary-700 transition-transform group-hover:translate-x-0.5 dark:text-primary-300">
              Открыть
              <ArrowRightIcon class="h-3 w-3" />
            </span>
          </router-link>
        </div>

        <div class="mt-5 grid gap-5 lg:h-[38rem] lg:grid-cols-3">
          <!-- Мои заявки -->
          <section class="panel flex flex-col overflow-hidden lg:col-span-2">
            <header class="panel-header">
              <div>
                <h2 class="font-display text-lg font-semibold text-ink dark:text-ink-dark">Мои заявки</h2>
                <p class="mt-0.5 text-xs text-ink-soft dark:text-ink-dark-soft">
                  Последние {{ MY_TICKETS_LIMIT }} обращений, назначенные на вас
                </p>
              </div>
              <router-link
                :to="{ path: '/admin/tickets', query: { assignee: 'me' } }"
                class="text-xs font-medium text-primary-700 hover:underline dark:text-primary-300"
              >
                Все мои
              </router-link>
            </header>

            <div class="flex flex-wrap border-b-2 border-line dark:border-line-dark">
              <button
                v-for="tab in tabs"
                :key="tab.key"
                @click="selectTab(tab.key)"
                class="flex items-center gap-1.5 border-r-2 border-line px-3 py-2.5 text-xs font-medium transition-colors last:border-r-0 dark:border-line-dark"
                :class="activeTab === tab.key
                  ? 'bg-primary-500 text-white'
                  : 'bg-surface text-ink-soft hover:bg-surface-muted dark:bg-surface-dark dark:text-ink-dark-soft dark:hover:bg-surface-dark-muted'"
              >
                {{ tab.label }}
                <span
                  class="font-semibold tabular-nums"
                  :class="activeTab === tab.key ? 'text-primary-100' : 'text-ink-soft dark:text-ink-dark-soft'"
                >{{ tab.count }}</span>
              </button>
            </div>

            <div v-if="myTicketsLoading" class="min-h-0 flex-1 space-y-3 overflow-hidden p-4">
              <div v-for="i in 4" :key="i" class="skeleton h-10 w-full" />
            </div>

            <div v-else-if="myTickets.length === 0" class="flex min-h-0 flex-1 flex-col items-center justify-center px-6 py-10 text-center">
              <InboxStackIcon class="h-7 w-7 text-ink-soft dark:text-ink-dark-soft" />
              <p class="mt-2 text-sm text-ink-soft dark:text-ink-dark-soft">
                {{ activeTab === 'all' ? 'На вас пока не назначено ни одной заявки' : 'В этом статусе заявок нет' }}
              </p>
            </div>

            <div v-else class="min-h-0 max-h-[26rem] flex-1 overflow-y-auto lg:max-h-none">
              <button
                v-for="ticket in myTickets"
                :key="ticket.id"
                @click="goTicket(ticket.id)"
                class="flex w-full items-start gap-3 border-b-2 border-line p-4 text-left transition-colors last:border-b-0 hover:bg-surface-muted focus:outline-none focus-visible:bg-surface-muted dark:border-line-dark dark:hover:bg-surface-dark-muted dark:focus-visible:bg-surface-dark-muted"
              >
                <div class="min-w-0 flex-1">
                  <p class="truncate font-medium text-ink dark:text-ink-dark">{{ ticket.title }}</p>
                  <p class="mt-1 truncate text-xs text-ink-soft dark:text-ink-dark-soft">
                    {{ ticket.user_name || 'Заявитель' }} · {{ formatDate(ticket.created_at) }}
                  </p>
                </div>
                <StatusBadge :status="ticket.status" />
              </button>
            </div>

            <router-link
              :to="mineLink"
              class="panel-footer flex items-center justify-between text-sm font-medium text-primary-700 transition-colors hover:bg-surface-muted dark:text-primary-300 dark:hover:bg-surface-dark-muted"
            >
              Открыть все мои заявки
              <ArrowRightIcon class="h-4 w-4" />
            </router-link>
          </section>

          <!-- Очередь -->
          <section class="panel flex flex-col overflow-hidden">
            <header class="panel-header">
              <div>
                <h2 class="font-display text-lg font-semibold text-ink dark:text-ink-dark">Очередь</h2>
                <p class="mt-0.5 text-xs text-ink-soft dark:text-ink-dark-soft">
                  {{ QUEUE_LIMIT }} самых старых новых заявок
                </p>
              </div>
              <span class="flex h-8 min-w-8 items-center justify-center border-2 border-line px-2 font-display text-sm font-semibold tabular-nums text-ink dark:border-line-dark dark:text-ink-dark">
                {{ data.queue }}
              </span>
            </header>

            <div v-if="queuePreview.length === 0" class="flex min-h-0 flex-1 flex-col items-center justify-center px-6 py-10 text-center">
              <CheckCircleIcon class="h-7 w-7 text-emerald-600 dark:text-emerald-400" />
              <p class="mt-2 text-sm text-ink-soft dark:text-ink-dark-soft">
                Очередь пуста — все новые заявки распределены
              </p>
            </div>

            <div v-else class="min-h-0 max-h-[26rem] flex-1 overflow-y-auto lg:max-h-none">
              <div
                v-for="ticket in queuePreview"
                :key="ticket.id"
                class="border-b-2 border-line p-4 last:border-b-0 dark:border-line-dark"
              >
                <button @click="goTicket(ticket.id)" class="block w-full text-left">
                  <p class="truncate font-medium text-ink dark:text-ink-dark">{{ ticket.title }}</p>
                  <p class="mt-1 text-xs text-ink-soft dark:text-ink-dark-soft">
                    {{ formatDate(ticket.created_at) }} · ждёт {{ waitingLabel(ticket.created_at) }}
                  </p>
                </button>
                <button
                  @click="assignToMe(ticket)"
                  :disabled="assigning !== null"
                  class="btn-secondary btn-sm mt-3 w-full"
                >
                  <ArrowPathIcon v-if="assigning === ticket.id" class="h-3.5 w-3.5 animate-spin" />
                  <WrenchScrewdriverIcon v-else class="h-3.5 w-3.5" />
                  {{ assigning === ticket.id ? 'Назначаем…' : 'Назначить на себя' }}
                </button>
              </div>
            </div>

            <router-link
              :to="{ path: '/admin/tickets', query: { assignee: 'unassigned', status: 'NEW' } }"
              class="panel-footer flex items-center justify-between text-sm font-medium text-primary-700 transition-colors hover:bg-surface-muted dark:text-primary-300 dark:hover:bg-surface-dark-muted"
            >
              Вся очередь
              <ArrowRightIcon class="h-4 w-4" />
            </router-link>
          </section>
        </div>

        <!-- Активность -->
        <section class="panel mt-5 overflow-hidden">
          <header class="panel-header">
            <div>
              <h2 class="font-display text-lg font-semibold text-ink dark:text-ink-dark">Моя активность</h2>
              <p class="mt-0.5 text-xs text-ink-soft dark:text-ink-dark-soft">Последние действия в системе</p>
            </div>
            <router-link
              to="/admin/audit?mine=1"
              class="text-xs font-medium text-primary-700 hover:underline dark:text-primary-300"
            >
              Весь лог
            </router-link>
          </header>

          <div v-if="data.recent_activity.length === 0" class="flex flex-col items-center px-6 py-10 text-center">
            <ClockIcon class="h-7 w-7 text-ink-soft dark:text-ink-dark-soft" />
            <p class="mt-2 text-sm text-ink-soft dark:text-ink-dark-soft">Вы пока не совершали действий</p>
          </div>

          <div v-else>
            <div
              v-for="log in data.recent_activity"
              :key="log.id"
              class="flex items-start gap-3 border-b-2 border-line p-4 last:border-b-0 dark:border-line-dark"
            >
              <span class="flex h-8 w-8 shrink-0 items-center justify-center border-2 border-line text-ink-soft dark:border-line-dark dark:text-ink-dark-soft">
                <component :is="actionIcon(log.action)" class="h-4 w-4" />
              </span>
              <div class="min-w-0 flex-1">
                <p class="text-sm font-medium text-ink dark:text-ink-dark">
                  {{ actionLabels[log.action] || log.action }}
                </p>
                <p class="mt-0.5 truncate text-xs text-ink-soft dark:text-ink-dark-soft">
                  {{ log.details || targetLabel(log) }}
                </p>
              </div>
              <div class="shrink-0 text-right">
                <p class="text-xs text-ink-soft dark:text-ink-dark-soft">{{ timeAgo(log.created_at) }}</p>
                <router-link
                  v-if="log.target_type === 'ticket' && log.target_id"
                  :to="`/admin/tickets/${log.target_id}`"
                  class="mt-0.5 inline-block text-[11px] font-medium text-primary-700 hover:underline dark:text-primary-300"
                >
                  Открыть
                </router-link>
              </div>
            </div>
          </div>
        </section>
      </div>
    </Transition>
  </div>
</template>
