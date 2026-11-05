<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch } from 'vue'
import { Marker, type MapMouseEvent } from 'maplibre-gl'
import { MagnifyingGlassIcon } from '@heroicons/vue/24/outline'
import { useToast } from '@/composables/useToast'
import { createMap, DEFAULT_CENTER, DEFAULT_ZOOM, isInVitebsk } from '@/lib/map'
import type { Map } from 'maplibre-gl'

const props = defineProps({
  modelValue: { type: Object, default: () => ({ lat: null, lng: null }) },
  height: { type: String, default: '400px' },
})
const emit = defineEmits(['update:modelValue', 'address'])

const mapContainer = ref<HTMLDivElement | null>(null)
const address = ref('')
const geocoding = ref(false)
let map: Map | null = null
let marker: Marker | null = null
let lastValid: { lat: number; lng: number } | null = null

function formatAddress(data: any): string {
  const a = data?.address || {}
  const city = a.city || a.town || a.village || a.municipality || a.hamlet || ''
  const road = a.road || a.pedestrian || a.footway || a.cycleway || a.path || a.square || ''
  const house = a.house_number || ''
  const street = road ? `${road}${house ? `, ${house}` : ''}` : ''
  const parts = [city, street].filter(Boolean)
  return parts.length ? parts.join(', ') : (data?.display_name || '')
}

const nominatimReverse = async (lat: number, lng: number) => {
  geocoding.value = true
  try {
    const res = await fetch(
      `https://nominatim.openstreetmap.org/reverse?lat=${lat}&lon=${lng}&format=json&addressdetails=1&accept-language=ru`,
      { headers: { 'User-Agent': 'CityBoost/2.0' } }
    )
    const data = await res.json()
    const formatted = formatAddress(data)
    if (formatted) {
      address.value = formatted
      emit('address', formatted)
    }
  } catch {
    // silent
  } finally {
    geocoding.value = false
  }
}

function placeMarker(lat: number, lng: number) {
  lastValid = { lat, lng }
  if (marker) {
    marker.setLngLat([lng, lat])
    return
  }
  marker = new Marker({ color: '#0E5A4A', draggable: true })
    .setLngLat([lng, lat])
    .addTo(map!)
  marker.on('dragend', () => {
    const pos = marker!.getLngLat()
    if (!isInVitebsk(pos.lat, pos.lng)) {
      useToast().warning('Метку можно ставить только в границах Витебска')
      if (lastValid) marker!.setLngLat([lastValid.lng, lastValid.lat])
      return
    }
    lastValid = { lat: pos.lat, lng: pos.lng }
    emit('update:modelValue', { lat: pos.lat.toFixed(6), lng: pos.lng.toFixed(6) })
    nominatimReverse(pos.lat, pos.lng)
  })
}

function onMapClick(e: MapMouseEvent) {
  const { lat, lng } = e.lngLat
  if (!isInVitebsk(lat, lng)) {
    useToast().warning('Метку можно ставить только в границах Витебска')
    return
  }
  placeMarker(lat, lng)
  emit('update:modelValue', { lat: lat.toFixed(6), lng: lng.toFixed(6) })
  nominatimReverse(lat, lng)
}

function manualGeocode() {
  if (!address.value.trim()) return
  const toast = useToast()
  geocoding.value = true
  fetch(
    `https://nominatim.openstreetmap.org/search?q=${encodeURIComponent(address.value)}&format=json&addressdetails=1&limit=1&accept-language=ru`,
    { headers: { 'User-Agent': 'CityBoost/2.0' } }
  ).then(r => r.json()).then(data => {
    if (data.length > 0) {
      const { lat, lon } = data[0]
      const latNum = parseFloat(lat), lngNum = parseFloat(lon)
      if (!isInVitebsk(latNum, lngNum)) {
        toast.warning('Выберите адрес в пределах Витебска')
        return
      }
      placeMarker(latNum, lngNum)
      map!.jumpTo({ center: [lngNum, latNum], zoom: 16 })
      const formatted = formatAddress(data[0])
      address.value = formatted
      emit('update:modelValue', { lat: latNum.toFixed(6), lng: lngNum.toFixed(6) })
      emit('address', formatted)
    } else {
      toast.warning('Адрес не найден')
    }
  }).catch(() => {
    toast.error('Ошибка геокодирования')
  }).finally(() => { geocoding.value = false })
}

watch(() => props.modelValue, (val: any) => {
  if (val?.lat && val?.lng && map) {
    const lat = Number(val.lat)
    const lng = Number(val.lng)
    if (!isInVitebsk(lat, lng)) return
    map.jumpTo({ center: [lng, lat], zoom: 16 })
    placeMarker(lat, lng)
  }
})

onMounted(() => {
  map = createMap(mapContainer.value!, {
    center: DEFAULT_CENTER,
    zoom: DEFAULT_ZOOM,
    attributionControl: false,
  })

  map.on('click', onMapClick)

  // If initial position set
  if (props.modelValue?.lat && props.modelValue?.lng) {
    const lat = Number(props.modelValue.lat)
    const lng = Number(props.modelValue.lng)
    if (isInVitebsk(lat, lng)) {
      map.jumpTo({ center: [lng, lat], zoom: 16 })
      placeMarker(lat, lng)
    }
  }
})

onUnmounted(() => {
  if (map) map.remove()
  map = null
  marker = null
})
</script>

<template>
  <div class="space-y-3">
    <!-- Search by address -->
    <div class="flex gap-2">
      <div class="relative flex-1">
        <MagnifyingGlassIcon class="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-ink-soft dark:text-ink-dark-soft" />
        <input
          v-model="address"
          type="text"
          class="form-input pl-9"
          placeholder="Поиск адреса в Витебске..."
          @keyup.enter="manualGeocode"
        />
      </div>
      <button type="button" class="btn-primary btn-sm" :disabled="geocoding || !address.trim()" @click="manualGeocode">
        {{ geocoding ? 'Поиск...' : 'Найти' }}
      </button>
    </div>

    <!-- Map -->
    <div
      ref="mapContainer"
      class="z-0 overflow-hidden rounded-sm border-2 border-line dark:border-line-dark"
      :style="{ height }"
    ></div>
  </div>
</template>
