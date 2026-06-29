<script setup lang="ts">
import { ref, watch, nextTick, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import { ticketAPI } from '@/api'
import { useAuthStore } from '@/stores/auth'
import { useUsers } from '@/composables/useUsers'
import { useToast } from '@/composables/useToast'
import StatusBadge from '@/components/StatusBadge.vue'
import SkeletonDetail from '@/components/SkeletonDetail.vue'
import L from 'leaflet'

// Fix default Leaflet marker icons
delete L.Icon.Default.prototype._getIconUrl
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
})

const route = useRoute()
const auth = useAuthStore()
const toast = useToast()
const { getUserName, fetchUsers, loaded } = useUsers()

const ticket = ref(null)
const loading = ref(true)
const error = ref('')
const uploadFile = ref(null)
const uploading = ref(false)
let map = null

// Load users if admin
if (auth.isAdmin && !loaded.value) fetchUsers()

async function loadTicket() {
  loading.value = true
  error.value = ''
  try {
    ticket.value = await ticketAPI.get(route.params.id)
  } catch (err) {
    error.value = err.message
    if (err.message.includes('404')) error.value = 'Заявка не найдена'
  } finally {
    loading.value = false
  }
}

// Init map when ticket loads with coordinates
watch(ticket, async (val) => {
  if (!val?.latitude || !val?.longitude) return
  await nextTick()
  const container = document.getElementById('ticket-map')
  if (!container || map) return
  map = L.map(container, { attributionControl: false }).setView([val.latitude, val.longitude], 15)
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
  }).addTo(map)
  L.marker([val.latitude, val.longitude]).addTo(map)
})

async function doUpload() {
  if (!uploadFile.value) { toast.warning('Выберите файл'); return }
  const file = uploadFile.value
  if (!['image/jpeg', 'image/png'].includes(file.type)) { toast.error('Допустимы только JPEG и PNG'); return }
  uploading.value = true
  try {
    await ticketAPI.uploadFile(ticket.value.id, file)
    toast.success('Файл загружен!')
    uploadFile.value = null
    await loadTicket()
  } catch (err) {
    toast.error(err.message)
  } finally {
    uploading.value = false
  }
}

function formatDate(dateStr) {
  return new Date(dateStr).toLocaleString('ru-RU', {
    day: 'numeric', month: 'long', year: 'numeric', hour: '2-digit', minute: '2-digit'
  })
}

loadTicket()
onUnmounted(() => { if (map) map.remove() })
</script>

<template>
  <div class="max-w-4xl mx-auto px-4 sm:px-6 py-8">

    <div class="mb-4">
      <router-link to="/dashboard" class="text-sm text-primary-600 dark:text-primary-400 hover:underline flex items-center gap-1">← Назад к заявкам</router-link>
    </div>

    <!-- Loading -->
    <SkeletonDetail v-if="loading" />

    <!-- Error -->
    <div v-else-if="error" class="card p-8 text-center">
      <div class="text-5xl mb-3">😕</div>
      <p class="text-red-500 mb-4">{{ error }}</p>
      <router-link to="/dashboard" class="btn-primary">Вернуться к заявкам</router-link>
    </div>

    <template v-else-if="ticket">
      <!-- Header -->
      <div class="card p-6 mb-6">
        <div class="flex items-start justify-between gap-4 mb-4">
          <div>
            <h1 class="text-2xl font-extrabold text-gray-900 dark:text-white">{{ ticket.title }}</h1>
            <p class="text-xs text-gray-400 mt-1">Создана: {{ formatDate(ticket.created_at) }}</p>
          </div>
          <StatusBadge :status="ticket.status" size="lg" />
        </div>

        <div v-if="ticket.address" class="mb-4 text-sm text-gray-500 dark:text-gray-400">📍 {{ ticket.address }}</div>

        <h3 class="text-sm font-semibold text-gray-500 dark:text-gray-400 mb-2 uppercase tracking-wide">Описание</h3>
        <p class="text-gray-700 dark:text-gray-300 whitespace-pre-wrap leading-relaxed">{{ ticket.description }}</p>
      </div>

      <!-- Map -->
      <div v-if="ticket.latitude" class="card p-4 mb-6">
        <h3 class="font-semibold text-gray-900 dark:text-white mb-2">🗺️ Местоположение</h3>
        <p class="text-xs text-gray-500 dark:text-gray-400 mb-2">{{ ticket.latitude }}, {{ ticket.longitude }}</p>
        <div id="ticket-map" class="h-64 rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden z-0"></div>
      </div>

      <!-- Files -->
      <div class="card p-6 mb-6">
        <h3 class="font-semibold text-gray-900 dark:text-white mb-4">📎 Файлы ({{ ticket.files?.length || 0 }})</h3>

        <div v-if="ticket.files?.length" class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3 mb-6">
          <div v-for="f in ticket.files" :key="f.id" class="group relative rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden bg-gray-50 dark:bg-gray-800/50 hover:shadow-md transition-shadow">
            <a :href="`/storage/${f.file_path}`" target="_blank" class="block">
              <img v-if="f.mime_type?.startsWith('image/')" :src="`/storage/${f.file_path}`" class="w-full h-32 object-cover" loading="lazy" />
              <div v-else class="h-32 flex items-center justify-center text-3xl text-gray-400">📄</div>
              <div class="p-2 text-xs truncate border-t border-gray-200 dark:border-gray-700">{{ f.file_path.split('/').pop() }}</div>
            </a>
          </div>
        </div>

        <div class="border-t border-gray-200 dark:border-gray-700 pt-4">
          <h4 class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">📤 Загрузить файл (JPEG/PNG)</h4>
          <div class="flex gap-2">
            <input type="file" accept="image/jpeg,image/png" @change="e => uploadFile = e.target.files[0]" class="form-input text-sm py-2" />
            <button @click="doUpload" class="btn-primary btn-sm" :disabled="uploading || !uploadFile">{{ uploading ? 'Загрузка...' : 'Загрузить' }}</button>
          </div>
        </div>
      </div>

      <!-- Comments -->
      <div class="card p-6">
        <h3 class="font-semibold text-gray-900 dark:text-white mb-4">💬 Комментарии ({{ ticket.comments?.length || 0 }})</h3>

        <div v-if="!ticket.comments?.length" class="text-sm text-gray-400 dark:text-gray-500 py-4 text-center">Комментариев пока нет</div>

        <div v-else class="space-y-3">
          <div v-for="c in ticket.comments" :key="c.id" class="flex gap-3 p-4 bg-gray-50 dark:bg-gray-800/50 rounded-lg">
            <div class="w-9 h-9 rounded-full bg-primary-100 dark:bg-primary-900/50 flex items-center justify-center text-sm font-bold text-primary-600 dark:text-primary-400 shrink-0">
              {{ (getUserName(c.author_id))[0] }}
            </div>
            <div class="flex-1 min-w-0">
              <div class="flex items-center gap-2 mb-1">
                <span class="text-sm font-semibold text-gray-900 dark:text-white">{{ getUserName(c.author_id) }}</span>
                <span class="text-xs text-gray-400">{{ formatDate(c.created_at) }}</span>
              </div>
              <p class="text-sm text-gray-700 dark:text-gray-300 whitespace-pre-wrap leading-relaxed">{{ c.comment_text }}</p>
            </div>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>
