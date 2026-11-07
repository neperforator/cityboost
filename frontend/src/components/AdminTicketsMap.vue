<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, shallowRef, watch } from 'vue'
import { useRouter } from 'vue-router'
import { LngLatBounds, Map, Popup, type GeoJSONSource, type MapLayerMouseEvent } from 'maplibre-gl'
import type { FeatureCollection } from 'geojson'
import { adminAPI } from '@/api'
import type { TicketMapPoint, TicketMapResponse, TicketStatus } from '@/types'
import { ExclamationTriangleIcon, MapPinIcon } from '@heroicons/vue/24/outline'
import { createMap, DEFAULT_CENTER, DEFAULT_ZOOM } from '@/lib/map'

const props = withDefaults(defineProps<{
  status?: TicketStatus | ''
  search?: string
  assignee?: 'all' | 'me' | 'unassigned'
  overdue?: boolean
}>(), {
  status: '',
  search: '',
  assignee: 'all',
  overdue: false,
})

const emit = defineEmits<{ reset: [] }>()

const STATUS_META: Record<TicketStatus, { color: string; label: string }> = {
  NEW: { color: '#0E5A4A', label: 'Новая' },
  IN_WORK: { color: '#E4572E', label: 'В работе' },
  DONE: { color: '#059669', label: 'Выполнена' },
  CLOSED: { color: '#6B7280', label: 'Отклонена' },
}

const MAP_LIMIT = 20000
const SOURCE_ID = 'tickets'
const LAYER_ID = 'tickets-points'

const router = useRouter()

const mapEl = ref<HTMLElement | null>(null)
const map = shallowRef<Map | null>(null)

const data = ref<TicketMapResponse | null>(null)
const loading = ref(true)
const refreshing = ref(false)
const error = ref('')

let requestSeq = 0
let styleReady = false
let fitNext = true
let popup: Popup | null = null
let tooltip: Popup | null = null
let resizeObserver: ResizeObserver | undefined

const points = computed(() => data.value?.items ?? [])
const total = computed(() => data.value?.total ?? 0)
const hiddenCount = computed(() => Math.max(0, total.value - points.value.length))
const filtersActive = computed(
  () => Boolean(props.status) || Boolean(props.search) || props.assignee !== 'all' || props.overdue,
)

const dateFormatter = new Intl.DateTimeFormat('ru-RU', {
  day: 'numeric',
  month: 'short',
  year: 'numeric',
})

function formatDate(value: string): string {
  const date = new Date(value)
  return Number.isNaN(date.getTime()) ? value : dateFormatter.format(date)
}

function metaRow(label: string, value: string): HTMLDivElement {
  const row = document.createElement('div')
  row.className = 'ticket-map-popup__row'

  const term = document.createElement('dt')
  term.textContent = label

  const description = document.createElement('dd')
  description.textContent = value

  row.append(term, description)
  return row
}

function buildPopup(point: TicketMapPoint): HTMLElement {
  const meta = STATUS_META[point.status] ?? STATUS_META.NEW
  const root = document.createElement('div')
  root.className = 'ticket-map-popup'

  const statusRow = document.createElement('p')
  statusRow.className = 'ticket-map-popup__status'
  const dot = document.createElement('span')
  dot.className = 'ticket-map-popup__dot'
  dot.style.backgroundColor = meta.color
  const statusText = document.createElement('span')
  statusText.textContent = meta.label
  statusRow.append(dot, statusText)

  const title = document.createElement('p')
  title.className = 'ticket-map-popup__title'
  title.textContent = point.title

  const list = document.createElement('dl')
  list.className = 'ticket-map-popup__meta'
  if (point.address) list.append(metaRow('Адрес', point.address))
  list.append(metaRow('Создана', formatDate(point.created_at)))
  if (point.assigned_to_name) list.append(metaRow('Исполнитель', point.assigned_to_name))

  const link = document.createElement('a')
  link.className = 'btn btn-primary btn-sm ticket-map-popup__link'
  link.href = `#/admin/tickets/${point.id}`
  link.textContent = 'Открыть заявку'
  link.addEventListener('click', (event) => {
    event.preventDefault()
    router.push(`/admin/tickets/${point.id}`)
  })

  root.append(statusRow, title, list, link)
  return root
}

function featureCollection(): FeatureCollection {
  return {
    type: 'FeatureCollection',
    features: points.value.map(point => ({
      type: 'Feature',
      geometry: { type: 'Point', coordinates: [point.longitude, point.latitude] },
      properties: { id: point.id, title: point.title, status: point.status },
    })),
  }
}

function fitToPoints() {
  const instance = map.value
  if (!instance) return

  if (points.value.length === 0) {
    instance.jumpTo({ center: DEFAULT_CENTER, zoom: DEFAULT_ZOOM })
    return
  }

  const bounds = new LngLatBounds()
  for (const point of points.value) {
    bounds.extend([point.longitude, point.latitude])
  }
  instance.fitBounds(bounds, { padding: 40, maxZoom: 14, duration: 0 })
}

function applyData() {
  const instance = map.value
  if (!instance || !styleReady) return

  const source = instance.getSource(SOURCE_ID) as GeoJSONSource | undefined
  source?.setData(featureCollection())

  if (fitNext) {
    fitNext = false
    fitToPoints()
  }
}

function onLayerMove(event: MapLayerMouseEvent) {
  const instance = map.value
  const feature = event.features?.[0]
  if (!instance || !feature) return

  instance.getCanvas().style.cursor = 'pointer'

  const title = String(feature.properties?.title ?? '')
  if (!tooltip) {
    tooltip = new Popup({
      closeButton: false,
      closeOnClick: false,
      offset: 14,
      className: 'ticket-map-tooltip',
    })
  }
  tooltip.setLngLat(event.lngLat).setText(title).addTo(instance)
}

function onLayerLeave() {
  const instance = map.value
  if (instance) instance.getCanvas().style.cursor = ''
  tooltip?.remove()
}

function onLayerClick(event: MapLayerMouseEvent) {
  const instance = map.value
  const feature = event.features?.[0]
  if (!instance || !feature) return

  const id = String(feature.properties?.id ?? '')
  const point = points.value.find(item => item.id === id)
  if (!point) return

  tooltip?.remove()
  popup?.remove()
  popup = new Popup({ maxWidth: '280px', offset: 12 })
    .setLngLat(event.lngLat)
    .setDOMContent(buildPopup(point))
    .addTo(instance)
}

function bindLayerEvents(instance: Map) {
  instance.on('mousemove', LAYER_ID, onLayerMove)
  instance.on('mouseleave', LAYER_ID, onLayerLeave)
  instance.on('click', LAYER_ID, onLayerClick)
}

function initMap() {
  if (!mapEl.value || map.value) return

  const instance = createMap(mapEl.value, {
    center: DEFAULT_CENTER,
    zoom: DEFAULT_ZOOM,
  })
  map.value = instance

  instance.on('load', () => {
    instance.addSource(SOURCE_ID, {
      type: 'geojson',
      data: featureCollection(),
    })
    instance.addLayer({
      id: LAYER_ID,
      type: 'circle',
      source: SOURCE_ID,
      paint: {
        'circle-radius': ['interpolate', ['linear'], ['zoom'], 8, 5, 12, 7, 16, 10],
        'circle-color': [
          'match',
          ['get', 'status'],
          'NEW', STATUS_META.NEW.color,
          'IN_WORK', STATUS_META.IN_WORK.color,
          'DONE', STATUS_META.DONE.color,
          'CLOSED', STATUS_META.CLOSED.color,
          STATUS_META.NEW.color,
        ],
        'circle-opacity': 0.9,
        'circle-stroke-width': 2,
        'circle-stroke-color': '#FFFFFF',
        'circle-stroke-opacity': 0.9,
      },
    })

    styleReady = true
    bindLayerEvents(instance)
    applyData()
  })

  resizeObserver = new ResizeObserver(() => instance.resize())
  resizeObserver.observe(mapEl.value)
  requestAnimationFrame(() => instance.resize())
}

async function load(fit = false) {
  const seq = ++requestSeq
  if (fit) fitNext = true

  if (data.value) refreshing.value = true
  else loading.value = true
  error.value = ''

  try {
    const result = await adminAPI.getTicketMap({
      status: props.status || undefined,
      q: props.search || undefined,
      assignee: props.assignee,
      overdue: props.overdue || undefined,
      limit: MAP_LIMIT,
    })
    if (seq !== requestSeq) return

    data.value = result
    await nextTick()
    applyData()
  } catch (err) {
    if (seq !== requestSeq) return
    error.value = err instanceof Error ? err.message : 'Не удалось загрузить заявки'
  } finally {
    if (seq === requestSeq) {
      loading.value = false
      refreshing.value = false
    }
  }
}

watch(
  () => [props.status, props.search, props.assignee, props.overdue],
  () => load(true),
)

onMounted(async () => {
  await nextTick()
  initMap()
  await load(true)
})

onBeforeUnmount(() => {
  requestSeq += 1
  resizeObserver?.disconnect()
  resizeObserver = undefined
  tooltip?.remove()
  popup?.remove()
  tooltip = null
  popup = null
  map.value?.remove()
  map.value = null
  styleReady = false
})
</script>

<template>
  <div class="panel relative overflow-hidden">
    <div ref="mapEl" class="relative z-0 h-[68vh] min-h-[420px] max-h-[760px] w-full" />

    <div
      v-if="refreshing"
      class="absolute inset-x-0 top-0 z-[600] h-0.5 overflow-hidden bg-line dark:bg-line-dark"
      role="status"
      aria-label="Обновление данных карты"
    >
      <div class="progress-slide h-full w-1/3 bg-primary-500 dark:bg-primary-300" />
    </div>

    <div
      class="pointer-events-none absolute bottom-6 left-3 z-[500] rounded-sm border-2 border-line bg-surface/95 px-3 py-2.5 shadow-panel backdrop-blur dark:border-line-dark dark:bg-surface-dark/95"
    >
      <p class="text-[10px] font-semibold uppercase tracking-wider text-ink-soft dark:text-ink-dark-soft">
        Статус
      </p>
      <ul class="mt-1.5 space-y-1">
        <li
          v-for="(meta, key) in STATUS_META"
          :key="key"
          class="flex items-center gap-2 text-xs text-ink dark:text-ink-dark"
        >
          <span
            class="h-2.5 w-2.5 rounded-full border border-white/80"
            :style="{ backgroundColor: meta.color }"
          />
          {{ meta.label }}
        </li>
      </ul>
    </div>

    <div
      class="pointer-events-none absolute right-3 top-3 z-[500] rounded-sm border-2 border-line bg-surface/95 px-3 py-1.5 text-xs font-semibold text-ink shadow-panel backdrop-blur dark:border-line-dark dark:bg-surface-dark/95 dark:text-ink-dark"
    >
      {{ points.length }}
      <span class="font-normal text-ink-soft dark:text-ink-dark-soft">на карте</span>
    </div>

    <div
      v-if="error && data"
      class="absolute left-1/2 top-3 z-[600] max-w-[calc(100%-10rem)] -translate-x-1/2 rounded-sm border-2 border-red-300 bg-surface/95 px-3 py-1.5 text-xs font-medium text-red-700 shadow-panel backdrop-blur dark:border-red-800 dark:bg-surface-dark/95 dark:text-red-300"
    >
      {{ error }} Показаны последние загруженные заявки.
    </div>

    <div
      v-if="loading && !data"
      class="absolute inset-0 z-[600] flex items-center justify-center bg-surface/70 backdrop-blur-sm dark:bg-surface-dark/70"
    >
      <div class="flex flex-col items-center gap-3">
        <span class="h-8 w-8 animate-spin rounded-full border-2 border-line border-t-primary-500 dark:border-line-dark dark:border-t-primary-300" />
        <p class="text-xs font-semibold uppercase tracking-wider text-ink-soft dark:text-ink-dark-soft">
          Загружаем заявки
        </p>
      </div>
    </div>

    <div
      v-else-if="error && !data"
      class="absolute inset-0 z-[600] flex items-center justify-center bg-surface/90 p-6 dark:bg-surface-dark/90"
    >
      <div class="max-w-sm text-center">
        <ExclamationTriangleIcon class="mx-auto h-8 w-8 text-red-600 dark:text-red-400" />
        <p class="mt-3 font-semibold text-ink dark:text-ink-dark">
          Не удалось загрузить карту
        </p>
        <p class="mt-1 text-sm text-ink-soft dark:text-ink-dark-soft">{{ error }}</p>
        <button class="btn-secondary btn-sm mt-4" @click="load(true)">Повторить</button>
      </div>
    </div>

    <div
      v-else-if="data && points.length === 0"
      class="pointer-events-none absolute inset-0 z-[600] flex items-center justify-center p-6"
    >
      <div class="panel pointer-events-auto max-w-sm bg-surface/95 p-6 text-center shadow-panel dark:bg-surface-dark/95">
        <MapPinIcon class="mx-auto h-8 w-8 text-ink-soft dark:text-ink-dark-soft" />
        <p class="mt-3 font-semibold text-ink dark:text-ink-dark">
          Заявок с координатами нет
        </p>
        <p class="mt-1 text-sm text-ink-soft dark:text-ink-dark-soft">
          {{ filtersActive
            ? 'Попробуйте изменить фильтры или сбросить их.'
            : 'Как только пользователи оставят заявки с адресом на карте, они появятся здесь.' }}
        </p>
        <button
          v-if="filtersActive"
          class="btn-secondary btn-sm mt-4"
          @click="emit('reset')"
        >
          Сбросить фильтры
        </button>
      </div>
    </div>

    <p
      v-if="hiddenCount > 0"
      class="border-t-2 border-line px-4 py-2 text-xs text-ink-soft dark:border-line-dark dark:text-ink-dark-soft"
    >
      На карте показаны последние {{ points.length }} из {{ total }} заявок.
      Уточните фильтры, чтобы увидеть остальные.
    </p>
  </div>
</template>
