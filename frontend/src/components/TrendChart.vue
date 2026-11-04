<script setup lang="ts">
import { computed, ref } from 'vue'
import type { AnalyticsDayPoint } from '@/types'

const props = defineProps<{
  points: AnalyticsDayPoint[]
}>()

const W = 900
const H = 340
const PAD = { top: 20, right: 20, bottom: 36, left: 46 }
const INNER_W = W - PAD.left - PAD.right
const INNER_H = H - PAD.top - PAD.bottom
const BASE_Y = PAD.top + INNER_H

type SeriesKey = 'created' | 'resolved' | 'backlog'

interface SeriesConfig {
  key: SeriesKey
  label: string
  colorClass: string
  dotClass: string
  areaId?: string
  dashed?: boolean
}

const series: SeriesConfig[] = [
  {
    key: 'created',
    label: 'Создано',
    colorClass: 'stroke-map-500 dark:stroke-map-300',
    dotClass: 'bg-map-500',
    areaId: 'analytics-created-fill',
  },
  {
    key: 'resolved',
    label: 'Решено',
    colorClass: 'stroke-emerald-500 dark:stroke-emerald-400',
    dotClass: 'bg-emerald-500',
    areaId: 'analytics-resolved-fill',
  },
  {
    key: 'backlog',
    label: 'В очереди',
    colorClass: 'stroke-accent-500 dark:stroke-accent-400',
    dotClass: 'bg-accent-500',
    dashed: true,
  },
]

const visible = ref<Record<SeriesKey, boolean>>({
  created: true,
  resolved: true,
  backlog: true,
})

const hoverIndex = ref<number | null>(null)

const activeSeries = computed(() => series.filter(item => visible.value[item.key]))

const showBars = computed(
  () => props.points.length <= 31 && visible.value.created,
)

const maxValue = computed(() =>
  Math.max(
    1,
    ...props.points.flatMap(point =>
      activeSeries.value.map(item => point[item.key]),
    ),
  ),
)

const niceMax = computed(() => {
  const raw = maxValue.value
  const power = 10 ** Math.floor(Math.log10(raw))
  const normalized = raw / power
  const step = normalized <= 1 ? 1 : normalized <= 2 ? 2 : normalized <= 5 ? 5 : 10
  return step * power
})

const stepX = computed(() =>
  props.points.length > 1 ? INNER_W / (props.points.length - 1) : 0,
)

function xAt(index: number): number {
  return PAD.left + index * stepX.value
}

function yAt(value: number): number {
  return PAD.top + INNER_H - (value / niceMax.value) * INNER_H
}

function smoothPath(key: SeriesKey): string {
  const coords = props.points.map((point, index) => ({
    x: xAt(index),
    y: yAt(point[key]),
  }))
  if (!coords.length) return ''
  if (coords.length === 1) {
    return `M ${coords[0].x.toFixed(1)} ${coords[0].y.toFixed(1)}`
  }

  let path = `M ${coords[0].x.toFixed(1)} ${coords[0].y.toFixed(1)}`
  for (let index = 1; index < coords.length; index += 1) {
    const previous = coords[index - 1]
    const current = coords[index]
    const controlOffset = (current.x - previous.x) / 3
    path +=
      ` C ${(previous.x + controlOffset).toFixed(1)} ${previous.y.toFixed(1)},` +
      ` ${(current.x - controlOffset).toFixed(1)} ${current.y.toFixed(1)},` +
      ` ${current.x.toFixed(1)} ${current.y.toFixed(1)}`
  }
  return path
}

function areaPath(key: SeriesKey): string {
  if (!props.points.length) return ''
  const last = props.points.length - 1
  return `${smoothPath(key)} L ${xAt(last).toFixed(1)} ${BASE_Y} L ${PAD.left} ${BASE_Y} Z`
}

const gridLines = computed(() =>
  [0, 0.25, 0.5, 0.75, 1].map(ratio => ({
    y: PAD.top + INNER_H - ratio * INNER_H,
    value: Math.round(niceMax.value * ratio),
  })),
)

const xTicks = computed(() => {
  const count = props.points.length
  if (!count) return []
  const maxTicks = 8
  const step = Math.max(1, Math.ceil((count - 1) / (maxTicks - 1)))
  const indexes: number[] = []
  for (let index = 0; index < count; index += step) indexes.push(index)
  if (indexes[indexes.length - 1] !== count - 1) indexes.push(count - 1)
  return indexes.map(index => ({
    index,
    x: xAt(index),
    label: formatDay(props.points[index].date),
  }))
})

const hoveredPoint = computed(() =>
  hoverIndex.value === null ? null : props.points[hoverIndex.value] ?? null,
)

const tooltipStyle = computed(() => {
  if (hoverIndex.value === null) return {}
  const percent = (xAt(hoverIndex.value) / W) * 100
  return { left: `${Math.min(88, Math.max(12, percent))}%` }
})

function onPointerMove(event: PointerEvent) {
  if (!props.points.length) return
  const target = event.currentTarget as SVGSVGElement
  const rect = target.getBoundingClientRect()
  const x = ((event.clientX - rect.left) / rect.width) * W
  const rawIndex = (x - PAD.left) / (stepX.value || 1)
  hoverIndex.value = Math.min(
    props.points.length - 1,
    Math.max(0, Math.round(rawIndex)),
  )
}

function formatDay(isoDate: string): string {
  const [, month, day] = isoDate.split('-')
  return `${day}.${month}`
}

function formatLong(isoDate: string): string {
  return new Date(`${isoDate}T00:00:00`).toLocaleDateString('ru-RU', {
    day: 'numeric',
    month: 'long',
    year: 'numeric',
  })
}
</script>

<template>
  <div>
    <div class="flex flex-wrap items-center justify-between gap-3">
      <div class="flex flex-wrap gap-2">
        <button
          v-for="item in series"
          :key="item.key"
          type="button"
          class="inline-flex items-center gap-2 border-2 px-2.5 py-1.5 text-xs font-medium transition-colors"
          :class="visible[item.key]
            ? 'border-line bg-surface text-ink dark:border-line-dark dark:bg-surface-dark dark:text-ink-dark'
            : 'border-transparent bg-transparent text-ink-soft/60 line-through dark:text-ink-dark-soft/60'"
          :aria-pressed="visible[item.key]"
          @click="visible[item.key] = !visible[item.key]"
        >
          <span
            class="h-2.5 w-2.5 rounded-full transition-opacity"
            :class="[item.dotClass, visible[item.key] ? '' : 'opacity-30']"
          />
          {{ item.label }}
        </button>
      </div>
      <p class="text-[11px] text-ink-soft dark:text-ink-dark-soft">
        Наведите на график для деталей
      </p>
    </div>

    <div
      v-if="!points.length"
      class="mt-4 flex h-56 items-center justify-center border-2 border-dashed border-line text-sm text-ink-soft dark:border-line-dark dark:text-ink-dark-soft"
    >
      Нет данных за выбранный период
    </div>

    <div v-else class="relative mt-4">
      <svg
        :viewBox="`0 0 ${W} ${H}`"
        class="h-auto w-full touch-none select-none"
        role="img"
        aria-label="График созданных, решённых заявок и накопительной очереди по дням"
        @pointermove="onPointerMove"
        @pointerleave="hoverIndex = null"
      >
        <defs>
          <linearGradient id="analytics-created-fill" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stop-color="currentColor" class="text-map-500" stop-opacity="0.3" />
            <stop offset="100%" stop-color="currentColor" class="text-map-500" stop-opacity="0" />
          </linearGradient>
          <linearGradient id="analytics-resolved-fill" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stop-color="currentColor" class="text-emerald-500" stop-opacity="0.22" />
            <stop offset="100%" stop-color="currentColor" class="text-emerald-500" stop-opacity="0" />
          </linearGradient>
        </defs>

        <!-- Сетка -->
        <g>
          <line
            v-for="line in gridLines"
            :key="line.y"
            :x1="PAD.left"
            :x2="W - PAD.right"
            :y1="line.y"
            :y2="line.y"
            class="stroke-ink/10 dark:stroke-white/10"
            stroke-width="1"
            :stroke-dasharray="line.value === 0 ? undefined : '3 5'"
          />
          <text
            v-for="line in gridLines"
            :key="`label-${line.y}`"
            :x="PAD.left - 10"
            :y="line.y + 4"
            text-anchor="end"
            class="fill-ink-soft text-[10px] dark:fill-ink-dark-soft"
          >
            {{ line.value }}
          </text>
        </g>

        <!-- Столбцы созданных заявок (на коротких периодах) -->
        <g v-if="showBars">
          <rect
            v-for="(point, index) in points"
            :key="`bar-${point.date}`"
            :x="xAt(index) - Math.max(2, stepX * 0.22)"
            :y="yAt(point.created)"
            :width="Math.max(4, stepX * 0.44)"
            :height="BASE_Y - yAt(point.created)"
            rx="2"
            class="fill-map-500/15 dark:fill-map-300/15"
          />
        </g>

        <!-- Области -->
        <path
          v-if="visible.created"
          :d="areaPath('created')"
          fill="url(#analytics-created-fill)"
        />
        <path
          v-if="visible.resolved"
          :d="areaPath('resolved')"
          fill="url(#analytics-resolved-fill)"
        />

        <!-- Линии -->
        <path
          v-for="item in activeSeries"
          :key="item.key"
          :d="smoothPath(item.key)"
          fill="none"
          :class="item.colorClass"
          stroke-width="2.75"
          stroke-linecap="round"
          stroke-linejoin="round"
          :stroke-dasharray="item.dashed ? '7 6' : undefined"
        />

        <!-- Подсказка при наведении -->
        <g v-if="hoveredPoint && hoverIndex !== null">
          <line
            :x1="xAt(hoverIndex)"
            :x2="xAt(hoverIndex)"
            :y1="PAD.top"
            :y2="BASE_Y"
            class="stroke-ink/25 dark:stroke-white/25"
            stroke-width="1"
            stroke-dasharray="4 4"
          />
          <circle
            v-for="item in activeSeries"
            :key="`hover-${item.key}`"
            :cx="xAt(hoverIndex)"
            :cy="yAt(hoveredPoint[item.key])"
            r="5"
            class="fill-surface stroke-2 dark:fill-surface-dark"
            :class="item.colorClass"
          />
        </g>

        <!-- Подписи по оси X -->
        <text
          v-for="tick in xTicks"
          :key="`tick-${tick.index}`"
          :x="tick.x"
          :y="H - 12"
          text-anchor="middle"
          class="fill-ink-soft text-[10px] dark:fill-ink-dark-soft"
        >
          {{ tick.label }}
        </text>
      </svg>

      <div
        v-if="hoveredPoint"
        class="pointer-events-none absolute top-1 z-10 w-44 -translate-x-1/2 border-2 border-line bg-surface p-3 text-xs shadow-lg dark:border-line-dark dark:bg-surface-dark"
        :style="tooltipStyle"
      >
        <p class="font-semibold text-ink dark:text-ink-dark">
          {{ formatLong(hoveredPoint.date) }}
        </p>
        <div class="mt-2 space-y-1.5">
          <div
            v-for="item in series"
            :key="`tooltip-${item.key}`"
            class="flex items-center justify-between gap-3"
          >
            <span class="inline-flex items-center gap-1.5 text-ink-soft dark:text-ink-dark-soft">
              <span class="h-2 w-2 rounded-full" :class="item.dotClass" />
              {{ item.label }}
            </span>
            <span class="font-semibold tabular-nums text-ink dark:text-ink-dark">
              {{ hoveredPoint[item.key] }}
            </span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
