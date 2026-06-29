<script setup lang="ts">
import { ref, watch, nextTick, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { adminAPI } from '@/api'
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
const router = useRouter()
const toast = useToast()
const auth = useAuthStore()
const { getUserName, fetchUsers, loaded } = useUsers()

const ticket = ref(null)
const loading = ref(true)
const error = ref('')
const commentText = ref('')
const commenting = ref(false)
const history = ref([])
let map = null

const statuses = ['NEW', 'IN_WORK', 'DONE', 'CLOSED']

if (!loaded.value) fetchUsers()

async function load() {
  loading.value = true
  error.value = ''
  try {
    const [t, h] = await Promise.all([
      adminAPI.getTicket(route.params.id),
      adminAPI.getHistory(route.params.id),
    ])
    ticket.value = t
    history.value = h
  } catch (err) {
    error.value = err.message
  } finally {
    loading.value = false
  }
}

// Init map when ticket loads with coords
watch(ticket, async (val) => {
  if (!val?.latitude || !val?.longitude) return
  await nextTick()
  const container = document.getElementById('admin-ticket-map')
  if (!container || map) return
  map = L.map(container, { attributionControl: false }).setView([val.latitude, val.longitude], 15)
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
  }).addTo(map)
  L.marker([val.latitude, val.longitude]).addTo(map)
})

async function changeStatus(status) {
  try {
    await adminAPI.changeStatus(ticket.value.id, status)
    toast.success(`Статус изменён на «${status}»`)
    await load()
  } catch (err) { toast.error(err.message) }
}

async function assign() {
  try {
    await adminAPI.assign(ticket.value.id)
    toast.success('Заявка назначена на вас')
    await load()
  } catch (err) { toast.error(err.message) }
}

async function addComment() {
  if (!commentText.value.trim()) return
  commenting.value = true
  try {
    await adminAPI.addComment(ticket.value.id, commentText.value.trim())
    toast.success('Комментарий добавлен')
    commentText.value = ''
    await load()
  } catch (err) { toast.error(err.message) }
  finally { commenting.value = false }
}

function formatDate(d) {
  return new Date(d).toLocaleString('ru-RU', { day: 'numeric', month: 'long', year: 'numeric', hour: '2-digit', minute: '2-digit' })
}

load()
onUnmounted(() => { if (map) map.remove() })
</script>

<template>
  <div class="max-w-5xl mx-auto px-4 sm:px-6 py-8">

    <div class="mb-4">
      <router-link to="/admin" class="text-sm text-primary-600 dark:text-primary-400 hover:underline flex items-center gap-1">← Назад к админ-панели</router-link>
      <span v-if="ticket" class="text-sm text-gray-400 ml-2">/ {{ ticket.title }}</span>
    </div>

    <!-- Loading -->
    <SkeletonDetail v-if="loading" />

    <!-- Error -->
    <div v-else-if="error" class="card p-8 text-center">
      <div class="text-5xl mb-3">😕</div>
      <p class="text-red-500 mb-4">{{ error }}</p>
      <router-link to="/admin" class="btn-primary">Назад</router-link>
    </div>

    <template v-else-if="ticket">
      <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">

        <!-- Left: main content -->
        <div class="lg:col-span-2 space-y-6">

          <!-- Header -->
          <div class="card p-6">
            <div class="flex items-start justify-between gap-4 mb-4">
              <div>
                <h1 class="text-2xl font-extrabold text-gray-900 dark:text-white">{{ ticket.title }}</h1>
                <div class="flex items-center gap-2 mt-1 text-sm text-gray-500 dark:text-gray-400">
                  <span>📅 {{ formatDate(ticket.created_at) }}</span>
                  <span>•</span>
                  <span>👤 {{ getUserName(ticket.user_id) }}</span>
                </div>
              </div>
              <StatusBadge :status="ticket.status" size="lg" />
            </div>
            <div v-if="ticket.address" class="mb-3 text-sm text-gray-500">📍 {{ ticket.address }}</div>
            <p class="text-gray-700 dark:text-gray-300 whitespace-pre-wrap leading-relaxed">{{ ticket.description }}</p>
          </div>

          <!-- Map -->
          <div v-if="ticket.latitude" class="card p-4">
            <h3 class="font-semibold text-gray-900 dark:text-white mb-2">🗺️ Местоположение</h3>
            <p class="text-xs text-gray-500 mb-2">{{ ticket.latitude }}, {{ ticket.longitude }}</p>
            <div id="admin-ticket-map" class="h-56 rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden z-0"></div>
          </div>

          <!-- Files -->
          <div v-if="ticket.files?.length" class="card p-4">
            <h3 class="font-semibold text-gray-900 dark:text-white mb-3">📎 Файлы ({{ ticket.files.length }})</h3>
            <div class="grid grid-cols-2 sm:grid-cols-3 gap-3">
              <div v-for="f in ticket.files" :key="f.id" class="rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden bg-gray-50 dark:bg-gray-800 hover:shadow-md transition-shadow">
                <a :href="`/storage/${f.file_path}`" target="_blank">
                  <img v-if="f.mime_type?.startsWith('image/')" :src="`/storage/${f.file_path}`" class="w-full h-28 object-cover" loading="lazy" />
                  <div v-else class="h-28 flex items-center justify-center text-gray-400 text-2xl">📄</div>
                  <div class="p-2 text-xs truncate border-t border-gray-200 dark:border-gray-700">{{ f.file_path.split('/').pop() }}</div>
                </a>
              </div>
            </div>
          </div>

          <!-- Comments -->
          <div class="card p-4">
            <h3 class="font-semibold text-gray-900 dark:text-white mb-4">💬 Комментарии ({{ ticket.comments?.length || 0 }})</h3>

            <div v-if="ticket.comments?.length" class="space-y-3 mb-6">
              <div v-for="c in ticket.comments" :key="c.id" class="flex gap-3 p-4 bg-gray-50 dark:bg-gray-800/50 rounded-lg">
                <div class="w-9 h-9 rounded-full bg-primary-100 dark:bg-primary-900/50 flex items-center justify-center text-sm font-bold text-primary-600 shrink-0">
                  {{ (getUserName(c.author_id))[0] }}
                </div>
                <div class="flex-1">
                  <div class="flex items-center gap-2 mb-1">
                    <span class="text-sm font-semibold text-gray-900 dark:text-white">{{ getUserName(c.author_id) }}</span>
                    <span class="text-xs text-gray-400">{{ formatDate(c.created_at) }}</span>
                  </div>
                  <p class="text-sm text-gray-700 dark:text-gray-300 whitespace-pre-wrap">{{ c.comment_text }}</p>
                </div>
              </div>
            </div>

            <div class="border-t border-gray-200 dark:border-gray-700 pt-4">
              <textarea v-model="commentText" class="form-textarea text-sm" rows="2" placeholder="Добавить комментарий..."></textarea>
              <button @click="addComment" class="btn-primary btn-sm mt-2" :disabled="commenting || !commentText.trim()">{{ commenting ? 'Отправка...' : 'Отправить комментарий' }}</button>
            </div>
          </div>
        </div>

        <!-- Right: management sidebar -->
        <div class="space-y-6">

          <!-- Status -->
          <div class="card p-4">
            <h3 class="font-semibold text-gray-900 dark:text-white mb-3">📌 Статус</h3>
            <div class="space-y-2">
              <button v-for="s in statuses" :key="s" @click="changeStatus(s)" :disabled="ticket.status === s"
                class="w-full text-left px-3 py-2.5 rounded-lg text-sm font-medium transition-colors"
                :class="ticket.status === s
                  ? 'bg-primary-100 dark:bg-primary-900/30 text-primary-700 dark:text-primary-300 cursor-not-allowed'
                  : 'bg-gray-50 dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 cursor-pointer'">
                {{ {NEW:'🆕 Новая',IN_WORK:'🔧 В работе',DONE:'✅ Выполнена',CLOSED:'📁 Закрыта'}[s] }}
                <span v-if="ticket.status === s" class="float-right text-xs">✓</span>
              </button>
            </div>
          </div>

          <!-- Assign -->
          <div class="card p-4">
            <h3 class="font-semibold text-gray-900 dark:text-white mb-3">👤 Назначение</h3>
            <div v-if="ticket.assigned_to" class="text-sm text-gray-600 dark:text-gray-400 mb-2">
              Исполнитель: <strong class="text-gray-900 dark:text-white">{{ getUserName(ticket.assigned_to) }}</strong>
            </div>
            <button @click="assign" :disabled="!!ticket.assigned_to" class="btn-primary w-full text-sm" :class="{ 'opacity-50 cursor-not-allowed': ticket.assigned_to }">
              {{ ticket.assigned_to ? '✅ Назначена' : '📌 Назначить на себя' }}
            </button>
          </div>

          <!-- User info -->
          <div class="card p-4">
            <h3 class="font-semibold text-gray-900 dark:text-white mb-3">👤 Заявитель</h3>
            <div class="text-sm space-y-1">
              <p class="text-gray-700 dark:text-gray-300">{{ getUserName(ticket.user_id) }}</p>
              <p class="text-xs text-gray-400 font-mono">{{ ticket.user_id.slice(0, 8) }}...</p>
              <p class="text-xs text-gray-400">📅 {{ formatDate(ticket.created_at) }}</p>
            </div>
          </div>

          <!-- History -->
          <div class="card p-4">
            <h3 class="font-semibold text-gray-900 dark:text-white mb-3">📋 История изменений</h3>
            <div v-if="history.length === 0" class="text-sm text-gray-400">История пуста</div>
            <div v-else class="space-y-3 max-h-80 overflow-y-auto pr-1">
              <div v-for="h in history" :key="h.id" class="text-xs border-l-2 border-primary-300 dark:border-primary-600 pl-3 py-1.5">
                <p class="text-gray-500">{{ formatDate(h.created_at) }}</p>
                <p class="text-gray-700 dark:text-gray-300 mt-0.5">
                  <span class="text-gray-400 text-xs">{{ getUserName(h.changed_by) }}</span>
                </p>
                <p class="mt-0.5">
                  <span class="bg-gray-100 dark:bg-gray-700 px-1.5 py-0.5 rounded">{{ h.old_status || '—' }}</span>
                  <span class="text-primary-500 font-bold mx-1">→</span>
                  <span class="bg-primary-100 dark:bg-primary-900/30 text-primary-700 dark:text-primary-300 px-1.5 py-0.5 rounded font-semibold">{{ h.new_status }}</span>
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>
