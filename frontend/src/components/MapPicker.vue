<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch } from 'vue'
import L from 'leaflet'

// Fix default Leaflet marker icons (broken after npm build)
delete L.Icon.Default.prototype._getIconUrl
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
})

import { useToast } from '@/composables/useToast'

const props = defineProps({
  modelValue: { type: Object, default: () => ({ lat: null, lng: null }) },
  height: { type: String, default: '400px' },
})
const emit = defineEmits(['update:modelValue'])

const mapContainer = ref(null)
const address = ref('')
const geocoding = ref(false)
let map = null
let marker = null

const nominatimReverse = async (lat, lng) => {
  geocoding.value = true
  try {
    const res = await fetch(
      `https://nominatim.openstreetmap.org/reverse?lat=${lat}&lon=${lng}&format=json&accept-language=ru`,
      { headers: { 'User-Agent': 'CityBoost/2.0' } }
    )
    const data = await res.json()
    if (data.display_name) {
      address.value = data.display_name
      emit('address', data.display_name)
    }
  } catch {
    // silent
  } finally {
    geocoding.value = false
  }
}

function onMapClick(e) {
  const { lat, lng } = e.latlng
  if (marker) marker.setLatLng([lat, lng])
  else marker = L.marker([lat, lng], { draggable: true }).addTo(map)
  marker.on('dragend', () => {
    const pos = marker.getLatLng()
    emit('update:modelValue', { lat: pos.lat.toFixed(6), lng: pos.lng.toFixed(6) })
    nominatimReverse(pos.lat, pos.lng)
  })
  emit('update:modelValue', { lat: lat.toFixed(6), lng: lng.toFixed(6) })
  nominatimReverse(lat, lng)
}

function manualGeocode() {
  if (!address.value.trim()) return
  const toast = useToast()
  geocoding.value = true
  fetch(
    `https://nominatim.openstreetmap.org/search?q=${encodeURIComponent(address.value)}&format=json&limit=1&accept-language=ru`,
    { headers: { 'User-Agent': 'CityBoost/2.0' } }
  ).then(r => r.json()).then(data => {
    if (data.length > 0) {
      const { lat, lon, display_name } = data[0]
      const latNum = parseFloat(lat), lngNum = parseFloat(lon)
      if (marker) marker.setLatLng([latNum, lngNum])
      else marker = L.marker([latNum, lngNum], { draggable: true }).addTo(map)
      map.setView([latNum, lngNum], 16)
      address.value = display_name
      emit('update:modelValue', { lat: latNum.toFixed(6), lng: lngNum.toFixed(6) })
      emit('address', display_name)
    } else {
      toast.warning('Адрес не найден')
    }
  }).catch(() => {
    const toast = useToast()
    toast.error('Ошибка геокодирования')
  }).finally(() => { geocoding.value = false })
}

watch(() => props.modelValue, (val) => {
  if (val.lat && val.lng && map) {
    map.setView([val.lat, val.lng], 16)
    if (marker) marker.setLatLng([val.lat, val.lng])
    else marker = L.marker([val.lat, val.lng], { draggable: true }).addTo(map)
  }
})

onMounted(() => {
  map = L.map(mapContainer.value, { attributionControl: false }).setView([55.7558, 37.6173], 12)

  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
  }).addTo(map)

  map.on('click', onMapClick)

  // If initial position set
  if (props.modelValue.lat && props.modelValue.lng) {
    map.setView([props.modelValue.lat, props.modelValue.lng], 16)
    marker = L.marker([props.modelValue.lat, props.modelValue.lng], { draggable: true }).addTo(map)
  }
})

onUnmounted(() => {
  if (map) map.remove()
})
</script>

<template>
  <div class="space-y-3">
    <!-- Search by address -->
    <div class="flex gap-2">
      <input
        v-model="address"
        type="text"
        class="form-input flex-1"
        placeholder="Введите адрес для поиска на карте..."
        @keyup.enter="manualGeocode"
      />
      <button type="button" class="btn-primary btn-sm" :disabled="geocoding || !address.trim()" @click="manualGeocode">
        {{ geocoding ? 'Поиск...' : '🔍 Найти' }}
      </button>
    </div>

    <!-- Map -->
    <div
      ref="mapContainer"
      class="rounded-xl border-2 border-gray-200 dark:border-gray-700 overflow-hidden z-0"
      :style="{ height }"
    ></div>

    <!-- Coordinates display -->
    <div v-if="modelValue.lat" class="flex gap-4 text-sm text-gray-500 dark:text-gray-400 bg-gray-50 dark:bg-gray-800/50 rounded-lg px-3 py-2">
      <span>📍 Широта: <strong>{{ modelValue.lat }}</strong></span>
      <span>📍 Долгота: <strong>{{ modelValue.lng }}</strong></span>
    </div>
  </div>
</template>
