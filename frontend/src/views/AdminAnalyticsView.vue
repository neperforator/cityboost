<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import type { Component } from 'vue'
import { adminAPI } from '@/api'
import type { AdminAnalytics, TicketStatus } from '@/types'
import { useToast } from '@/composables/useToast'
import TrendChart from '@/components/TrendChart.vue'
import {
  ArrowPathIcon,
  ArrowTrendingDownIcon,
  ArrowTrendingUpIcon,
  CheckCircleIcon,
  ClockIcon,
  ExclamationTriangleIcon,
  InboxStackIcon,
  MinusIcon,
  UsersIcon,
} from '@heroicons/vue/24/outline'

interface KpiCard {
  key: string
  label: string
  value: string
  hint: string
  icon: Component
  tone: 'primary' | 'accent' | 'emerald' | 'red' | 'map'
  delta?: number | null
  positiveIsGood?: boolean
}

const periods = [7, 30, 90]
const days = ref(30)
const data = ref<AdminAnalytics | null>(null)
const loading = ref(true)
const refreshing = ref(false)
const error = ref('')
const toast = useToast()
let requestId = 0

const toneClasses: Record<KpiCard['tone'], { icon: string; bar: string }> = {
  primary: { icon: 'text-primary-600 dark:text-primary-300', bar: 'bg-primary-500' },
  accent: { icon: 'text-accent-600 dark:text-accent-300', bar: 'bg-accent-500' },
  emerald: { icon: 'text-emerald-600 dark:text-emerald-400', bar: 'bg-emerald-500' },
  red: { icon: 'text-red-600 dark:text-red-400', bar: 'bg-red-600' },
  map: { icon: 'text-map-600 dark:text-map-300', bar: 'bg-map-500' },
}

const statusTones: Record<TicketStatus, string> = {
  NEW: 'bg-map-500',
  IN_WORK: 'bg-accent-500',
  DONE: 'bg-emerald-500',
  CLOSED: 'bg-ink-soft dark:bg-ink-dark-soft',
}

const statusStrokes: Record<TicketStatus, string> = {
  NEW: 'stroke-map-500',
  IN_WORK: 'stroke-accent-500',
  DONE: 'stroke-emerald-500',
  CLOSED: 'stroke-ink-soft dark:stroke-ink-dark-soft',
}

const summary = computed(() => data.value?.summary ?? null)

const kpis = computed<KpiCard[]>(() => {
  const current = summary.value
  return [
    {
      key: 'created',
      label: 'Создано за период',
      value: formatNumber(current?.created_in_period ?? 0),
      hint: `в прошлом периоде: ${formatNumber(current?.created_prev_period ?? 0)}`,
      icon: InboxStackIcon,
      tone: 'map',
      delta: current?.created_delta_pct,
      positiveIsGood: true,
    },
    {
      key: 'resolved',
      label: 'Решено за период',
      value: formatNumber(current?.resolved_in_period ?? 0),
      hint: `из новых закрыто ${current?.resolution_rate ?? 0}%`,
      icon: CheckCircleIcon,
      tone: 'emerald',
      delta: current?.resolved_delta_pct,
      positiveIsGood: true,
    },
    {
      key: 'open',
      label: 'Открыто сейчас',
      value: formatNumber(current?.open_now ?? 0),
      hint: `просрочено: ${formatNumber(current?.overdue_now ?? 0)}`,
      icon: ClockIcon,
      tone: current?.overdue_now ? 'red' : 'accent',
    },
    {
      key: 'avg',
      label: 'Среднее решение',
      value: formatHours(current?.avg_resolution_hours ?? null),
      hint: `медиана: ${formatHours(current?.median_resolution_hours ?? null)}`,
      icon: ExclamationTriangleIcon,
      tone: 'accent',
      delta: current?.avg_resolution_delta_pct,
      positiveIsGood: false,
    },
  ]
})

const donutCircumference = 2 * Math.PI * 42

const donutSegments = computed(() => {
  let offset = 0
  return (data.value?.by_status ?? []).map((item) => {
    const length = (item.percent / 100) * donutCircumference
    const segment = {
      ...item,
      dash: `${length} ${donutCircumference - length}`,
      offset: -offset,
    }
    offset += length
    return segment
  })
})

const maxResolved = computed(() =>
  Math.max(1, ...(data.value?.by_assignee ?? []).map(item => item.resolved_in_period)),
)

const generatedAt = computed(() => {
  if (!data.value?.generated_at) return ''
  return new Date(data.value.generated_at).toLocaleString('ru-RU', {
    day: 'numeric',
    month: 'long',
    hour: '2-digit',
    minute: '2-digit',
  })
})

function formatNumber(value: number): string {
  return new Intl.NumberFormat('ru-RU').format(value)
}

function formatHours(hours: number | null): string {
  if (hours == null) return '—'
  if (hours < 24) return `${hours.toFixed(1)} ч`
  return `${(hours / 24).toFixed(1)} дн.`
}

function deltaText(delta: number | null | undefined): string {
  if (delta == null) return 'нет базы'
  if (delta === 0) return '0%'
  return `${delta > 0 ? '+' : '−'}${Math.abs(delta).toFixed(1)}%`
}

function deltaClass(delta: number | null | undefined, positiveIsGood = true): string {
  if (delta == null || delta === 0) {
    return 'text-ink-soft dark:text-ink-dark-soft'
  }
  const isGood = positiveIsGood ? delta > 0 : delta < 0
  return isGood
    ? 'text-emerald-600 dark:text-emerald-400'
    : 'text-red-600 dark:text-red-400'
}

function assigneePercent(value: number): number {
  return Math.round((value / maxResolved.value) * 100)
}

async function load() {
  const current = ++requestId
  error.value = ''
  if (data.value) {
    refreshing.value = true
  } else {
    loading.value = true
  }
  try {
    const result = await adminAPI.getAnalytics(days.value)
    if (current !== requestId) return
    data.value = result
  } catch (err) {
    if (current !== requestId) return
    error.value = (err as Error).message
  } finally {
    if (current === requestId) {
      loading.value = false
      refreshing.value = false
    }
  }
}

function setPeriod(value: number) {
  if (days.value === value) return
  days.value = value
  load()
}

async function refresh() {
  await load()
  if (!error.value) toast.success('Аналитика обновлена')
}

onMounted(load)
</script>

<template>
  <div class="mx-auto max-w-6xl px-4 py-8 sm:px-8 sm:py-10">
    <header class="border-b-2 border-line pb-7 dark:border-line-dark">
      <p class="page-kicker">Администрирование</p>
      <div class="mt-2 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h1 class="font-display text-3xl font-semibold tracking-tight text-ink dark:text-ink-dark">
            Аналитика заявок
          </h1>
          <p class="mt-2 text-sm text-ink-soft dark:text-ink-dark-soft">
            Поток обращений, очередь и эффективность исполнителей
            <span v-if="generatedAt"> · обновлено {{ generatedAt }}</span>
          </p>
        </div>
        <div class="flex flex-wrap items-center gap-2">
          <div class="flex border-2 border-line dark:border-line-dark">
            <button
              v-for="period in periods"
              :key="period"
              type="button"
              class="px-3 py-1.5 text-xs font-semibold transition-colors"
              :class="days === period
                ? 'bg-primary-500 text-white'
                : 'bg-surface text-ink-soft hover:bg-surface-muted dark:bg-surface-dark dark:text-ink-dark-soft dark:hover:bg-surface-dark-muted'"
              @click="setPeriod(period)"
            >
              {{ period }} дней
            </button>
          </div>
          <button
            class="btn-secondary btn-sm"
            :disabled="loading || refreshing"
            @click="refresh"
          >
            <ArrowPathIcon
              class="h-4 w-4"
              :class="{ 'animate-spin': loading || refreshing }"
            />
            {{ refreshing ? 'Обновляем…' : 'Обновить' }}
          </button>
        </div>
      </div>
    </header>

    <div
      v-if="refreshing"
      class="mt-4 h-0.5 w-full overflow-hidden bg-line dark:bg-line-dark"
      role="status"
      aria-label="Обновление данных"
    >
      <div class="progress-slide h-full w-1/3 bg-primary-500 dark:bg-primary-300" />
    </div>

    <Transition name="page" mode="out-in">
      <div v-if="loading && !data" key="loading" class="mt-6 space-y-5">
        <div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <div v-for="i in 4" :key="i" class="panel p-5">
            <div class="skeleton h-3 w-24" />
            <div class="skeleton mt-3 h-8 w-16" />
            <div class="skeleton mt-2 h-3 w-28" />
          </div>
        </div>
        <div class="panel p-5">
          <div class="skeleton h-4 w-40" />
          <div class="skeleton mt-5 h-64 w-full" />
        </div>
      </div>

      <div v-else-if="error && !data" key="error" class="panel mt-6 border-l-4 border-l-red-500 p-6">
        <div class="flex items-start gap-3">
          <ExclamationTriangleIcon class="mt-0.5 h-5 w-5 shrink-0 text-red-600 dark:text-red-400" />
          <div>
            <p class="font-semibold text-ink dark:text-ink-dark">Не удалось загрузить аналитику</p>
            <p class="mt-1 text-sm text-ink-soft dark:text-ink-dark-soft">{{ error }}</p>
            <button class="btn-secondary btn-sm mt-4" @click="load">Повторить</button>
          </div>
        </div>
      </div>

      <div v-else-if="data" key="content" class="mt-6 space-y-5">
        <div
          v-if="error"
          class="panel flex items-start gap-3 border-l-4 border-l-red-500 p-4"
        >
          <ExclamationTriangleIcon class="mt-0.5 h-4 w-4 shrink-0 text-red-600 dark:text-red-400" />
          <div class="min-w-0">
            <p class="text-sm font-semibold text-ink dark:text-ink-dark">
              Не удалось обновить данные
            </p>
            <p class="mt-0.5 text-xs text-ink-soft dark:text-ink-dark-soft">
              {{ error }} Показаны последние загруженные значения.
            </p>
          </div>
        </div>

        <!-- KPI -->
        <div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <div
            v-for="kpi in kpis"
            :key="kpi.key"
            class="panel relative overflow-hidden p-5"
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
                <p
                  v-if="kpi.delta !== undefined"
                  class="mt-2 inline-flex items-center gap-1 text-xs font-semibold"
                  :class="deltaClass(kpi.delta, kpi.positiveIsGood)"
                >
                  <ArrowTrendingUpIcon v-if="kpi.delta != null && kpi.delta > 0" class="h-3.5 w-3.5" />
                  <ArrowTrendingDownIcon v-else-if="kpi.delta != null && kpi.delta < 0" class="h-3.5 w-3.5" />
                  <MinusIcon v-else class="h-3.5 w-3.5" />
                  {{ deltaText(kpi.delta) }}
                  <span class="font-normal text-ink-soft dark:text-ink-dark-soft">к прошлому</span>
                </p>
              </div>
              <span class="flex h-10 w-10 shrink-0 items-center justify-center border-2 border-line dark:border-line-dark">
                <component :is="kpi.icon" class="h-5 w-5" :class="toneClasses[kpi.tone].icon" />
              </span>
            </div>
          </div>
        </div>

        <!-- Динамика и поток -->
        <section class="panel p-5 sm:p-6">
          <header class="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
            <div>
              <h2 class="font-display text-lg font-semibold text-ink dark:text-ink-dark">Поток заявок</h2>
              <p class="mt-0.5 text-xs text-ink-soft dark:text-ink-dark-soft">
                Создано и решено за последние {{ data.period_days }} дней, накопительная очередь на конец дня
              </p>
            </div>
            <div class="text-right">
              <p class="text-[11px] font-semibold uppercase tracking-wider text-ink-soft dark:text-ink-dark-soft">
                Доля закрытых из новых
              </p>
              <p class="font-display text-2xl font-semibold tabular-nums text-emerald-600 dark:text-emerald-400">
                {{ data.summary.resolution_rate }}%
              </p>
            </div>
          </header>

          <div class="mt-5 grid grid-cols-2 gap-2 border-y-2 border-line py-3 dark:border-line-dark sm:grid-cols-4">
            <div class="px-2">
              <p class="text-[10px] font-semibold uppercase tracking-wider text-ink-soft dark:text-ink-dark-soft">Было в очереди</p>
              <p class="mt-1 font-display text-xl font-semibold tabular-nums text-ink dark:text-ink-dark">{{ formatNumber(data.summary.backlog_start) }}</p>
            </div>
            <div class="border-l-2 border-line px-2 dark:border-line-dark">
              <p class="text-[10px] font-semibold uppercase tracking-wider text-ink-soft dark:text-ink-dark-soft">Создано</p>
              <p class="mt-1 font-display text-xl font-semibold tabular-nums text-map-600 dark:text-map-300">{{ formatNumber(data.summary.created_in_period) }}</p>
            </div>
            <div class="border-l-2 border-line px-2 dark:border-line-dark">
              <p class="text-[10px] font-semibold uppercase tracking-wider text-ink-soft dark:text-ink-dark-soft">Решено</p>
              <p class="mt-1 font-display text-xl font-semibold tabular-nums text-emerald-600 dark:text-emerald-400">{{ formatNumber(data.summary.resolved_in_period) }}</p>
            </div>
            <div class="border-l-2 border-line px-2 dark:border-line-dark">
              <p class="text-[10px] font-semibold uppercase tracking-wider text-ink-soft dark:text-ink-dark-soft">Осталось в очереди</p>
              <p class="mt-1 font-display text-xl font-semibold tabular-nums text-accent-600 dark:text-accent-300">{{ formatNumber(data.summary.backlog_end) }}</p>
            </div>
          </div>

          <div class="mt-5">
            <TrendChart :points="data.by_day" />
          </div>
        </section>

        <div class="grid items-start gap-5 lg:grid-cols-2">
          <!-- Статусы -->
          <section class="panel p-5 sm:p-6">
            <header>
              <h2 class="font-display text-lg font-semibold text-ink dark:text-ink-dark">Судьба новых заявок</h2>
              <p class="mt-0.5 text-xs text-ink-soft dark:text-ink-dark-soft">
                Текущий статус заявок, созданных за период
              </p>
            </header>

            <div v-if="!data.summary.created_in_period" class="mt-6 border-2 border-dashed border-line p-6 text-center text-sm text-ink-soft dark:border-line-dark dark:text-ink-dark-soft">
              За период не было новых заявок
            </div>

            <div v-else class="mt-5 flex flex-col items-center gap-6 sm:flex-row">
              <div class="relative h-36 w-36 shrink-0">
                <svg viewBox="0 0 100 100" class="h-full w-full -rotate-90">
                  <circle cx="50" cy="50" r="42" fill="none" stroke-width="12" class="stroke-surface-muted dark:stroke-surface-dark-muted" />
                  <circle
                    v-for="segment in donutSegments"
                    :key="segment.status"
                    cx="50"
                    cy="50"
                    r="42"
                    fill="none"
                    stroke-width="12"
                    :stroke-dasharray="segment.dash"
                    :stroke-dashoffset="segment.offset"
                    :class="statusStrokes[segment.status]"
                  />
                </svg>
                <div class="absolute inset-0 flex flex-col items-center justify-center">
                  <span class="font-display text-2xl font-semibold tabular-nums text-ink dark:text-ink-dark">{{ formatNumber(data.summary.created_in_period) }}</span>
                  <span class="text-[10px] uppercase tracking-wider text-ink-soft dark:text-ink-dark-soft">заявок</span>
                </div>
              </div>

              <div class="w-full space-y-3">
                <div v-for="item in data.by_status" :key="item.status">
                  <div class="flex items-center justify-between gap-3 text-sm">
                    <span class="inline-flex items-center gap-2 font-medium text-ink dark:text-ink-dark">
                      <span class="h-2.5 w-2.5 rounded-full" :class="statusTones[item.status]" />
                      {{ item.label }}
                    </span>
                    <span class="tabular-nums text-ink-soft dark:text-ink-dark-soft">
                      {{ formatNumber(item.count) }} · {{ item.percent }}%
                    </span>
                  </div>
                  <div class="mt-1.5 h-1.5 w-full overflow-hidden bg-surface-muted dark:bg-surface-dark-muted">
                    <div
                      class="h-full transition-all duration-300"
                      :class="statusTones[item.status]"
                      :style="{ width: `${item.percent}%` }"
                    />
                  </div>
                </div>
              </div>
            </div>
          </section>

          <!-- Исполнители -->
          <section class="panel p-5 sm:p-6">
            <header class="flex items-start justify-between gap-3">
              <div>
                <h2 class="font-display text-lg font-semibold text-ink dark:text-ink-dark">Эффективность исполнителей</h2>
                <p class="mt-0.5 text-xs text-ink-soft dark:text-ink-dark-soft">
                  Решено за период, нагрузка и просрочка
                  <template v-if="data.assignees_total > data.by_assignee.length">
                    · топ-{{ data.by_assignee.length }} из {{ formatNumber(data.assignees_total) }}
                  </template>
                  <template v-else-if="data.assignees_total">
                    · всего {{ formatNumber(data.assignees_total) }}
                  </template>
                </p>
              </div>
              <UsersIcon class="h-5 w-5 shrink-0 text-ink-soft dark:text-ink-dark-soft" />
            </header>

            <div v-if="!data.by_assignee.length" class="mt-6 border-2 border-dashed border-line p-6 text-center text-sm text-ink-soft dark:border-line-dark dark:text-ink-dark-soft">
              Пока нет назначенных заявок
            </div>

            <div v-else class="mt-4 max-h-96 divide-y-2 divide-line overflow-y-auto overscroll-contain pr-1 dark:divide-line-dark">
              <div v-for="assignee in data.by_assignee" :key="assignee.admin_id" class="py-3">
                <div class="flex items-start justify-between gap-3">
                  <div class="min-w-0">
                    <p class="truncate text-sm font-semibold text-ink dark:text-ink-dark">{{ assignee.name }}</p>
                    <p class="mt-0.5 text-[11px] text-ink-soft dark:text-ink-dark-soft">
                      Новые: {{ formatNumber(assignee.created_in_period) }} ·
                      Открыто: {{ formatNumber(assignee.open_now) }} ·
                      <span :class="assignee.overdue ? 'font-semibold text-red-600 dark:text-red-400' : ''">
                        Просрочено: {{ formatNumber(assignee.overdue) }}
                      </span>
                    </p>
                  </div>
                  <div class="shrink-0 text-right">
                    <p class="text-sm font-semibold tabular-nums text-emerald-600 dark:text-emerald-400">
                      {{ formatNumber(assignee.resolved_in_period) }} решено
                    </p>
                    <p class="mt-0.5 text-[11px] text-ink-soft dark:text-ink-dark-soft">
                      ср. {{ formatHours(assignee.avg_resolution_hours) }}
                    </p>
                  </div>
                </div>
                <div class="mt-2 h-1.5 w-full overflow-hidden bg-surface-muted dark:bg-surface-dark-muted">
                  <div
                    class="h-full bg-emerald-500 transition-all duration-300"
                    :style="{ width: `${assigneePercent(assignee.resolved_in_period)}%` }"
                  />
                </div>
              </div>
            </div>
          </section>
        </div>
      </div>
    </Transition>
  </div>
</template>
