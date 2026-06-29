<script setup lang="ts">
import { ref, watch, nextTick, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { adminAPI } from '@/api'
import { useAuthStore } from '@/stores/auth'
import { useUsers } from '@/composables/useUsers'
import { useToast } from '@/composables/useToast'
import StatusBadge from '@/components/StatusBadge.vue'
import SkeletonDetail from '@/components/SkeletonDetail.vue'
import ImageLightbox from '@/components/ImageLightbox.vue'
import L from 'leaflet'

import { ArrowLeftIcon, MapPinIcon, ChatBubbleLeftRightIcon, PhotoIcon, CalendarDaysIcon, CheckCircleIcon, UserCircleIcon, ShieldCheckIcon, ArrowPathIcon, ClipboardDocumentCheckIcon, ClockIcon } from '@heroicons/vue/24/outline'
import { WrenchScrewdriverIcon } from '@heroicons/vue/24/solid'

// Fix default Leaflet marker icons
delete (L.Icon.Default.prototype as any)._getIconUrl
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
})

const route = useRoute()
const router = useRouter()
const toast = useToast()
const auth = useAuthStore()
const { getUserName, getUserDisplay } = useUsers()

const ticket = ref<any>(null)
const loading = ref(true)
const error = ref('')
const commentText = ref('')
const commenting = ref(false)
const history = ref<any[]>([])
const lightboxRef = ref<InstanceType<typeof ImageLightbox> | null>(null)
let map: L.Map | null = null

function openLightbox(files: any[], index: number) {
  const images = files.filter((f: any) => f.mime_type?.startsWith('image/')).map((f: any) => `/storage/${f.file_path}`)
  if (images.length > 0) lightboxRef.value?.open(images, index)
}

const statuses = ['NEW', 'IN_WORK', 'DONE', 'CLOSED']

const statusLabels: Record<string, string> = {
  NEW: 'Новая',
  IN_WORK: 'В работе',
  DONE: 'Выполнена',
  CLOSED: 'Закрыта',
}

async function load(silent = false) {
  const ticketId = route.params.id as string
  if (!silent) loading.value = true
  error.value = ''
  try {
    const [ticketData, historyData] = await Promise.all([
      adminAPI.getTicket(ticketId),
      adminAPI.getHistory(ticketId),
    ])
    ticket.value = ticketData
    history.value = historyData
  } catch (err) {
    error.value = (err as Error).message
    if ((err as Error).message.includes('404')) error.value = 'Заявка не найдена'
  } finally {
    if (!silent) loading.value = false
  }
}

load()
onUnmounted(() => { if (map) map.remove() })
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

async function changeStatus(status: string) {
  const prev = { ...ticket.value }
  ticket.value = { ...ticket.value, status }
  try {
    await adminAPI.changeStatus(ticket.value.id, status)
    toast.success(`Статус изменён на «${statusLabels[status]}»`)
    load(true)  // silent background refresh, no skeleton
  } catch (err) {
    ticket.value = prev  // revert locally
    toast.error((err as Error).message)
  }
}

async function assign() {
  const prev = { ...ticket.value }
  ticket.value = { ...ticket.value, assigned_to: auth.user!.id, status: 'IN_WORK' }
  try {
    await adminAPI.assign(ticket.value.id)
    toast.success('Заявка назначена на вас')
    load(true)  // silent background refresh, no skeleton
  } catch (err) {
    ticket.value = prev  // revert locally
    toast.error((err as Error).message)
  }
}

async function addComment() {
  if (!commentText.value.trim()) return
  commenting.value = true
  const text = commentText.value.trim()
  commentText.value = ''
  try {
    const comment = await adminAPI.addComment(ticket.value.id, text)
    // Append optimistically without full reload
    if (ticket.value.comments) {
      ticket.value = { ...ticket.value, comments: [...ticket.value.comments, comment] }
    }
    toast.success('Комментарий добавлен')
    load(true)  // silent background refresh, no skeleton
  } catch (err) {
    toast.error((err as Error).message)
    commentText.value = text
    await load()
  } finally {
    commenting.value = false
  }
}

function formatDate(d: string) {
  return new Date(d).toLocaleString('ru-RU', { day: 'numeric', month: 'long', year: 'numeric', hour: '2-digit', minute: '2-digit' })
}

</script>

<template>
  <div class="max-w-5xl mx-auto px-4 sm:px-6 py-8">

    <div class="mb-6">
      <router-link to="/admin" class="inline-flex items-center gap-1.5 text-sm text-primary-600 dark:text-primary-400 hover:text-primary-700 dark:hover:text-primary-300 font-medium transition-colors">
        <ArrowLeftIcon class="w-4 h-4" />
        Назад к админ-панели
        <span v-if="ticket" class="text-gray-400 ml-1">/ {{ ticket.title }}</span>
      </router-link>
    </div>

    <!-- Loading -->
    <SkeletonDetail v-if="loading" />

    <!-- Error -->
    <div v-else-if="error" class="card p-8 text-center">
      <div class="w-16 h-16 rounded-2xl bg-gray-100 dark:bg-gray-800 flex items-center justify-center mx-auto mb-4">
        <span class="text-2xl">😕</span>
      </div>
      <p class="text-red-500 mb-4">{{ error }}</p>
      <router-link to="/admin" class="btn-primary">Назад</router-link>
    </div>

    <template v-else-if="ticket">
      <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">

        <!-- Left: main content -->
        <div class="lg:col-span-2 space-y-6">

          <!-- Header card -->
          <div class="card p-6">
            <div class="flex items-start justify-between gap-4 mb-4">
              <div class="flex-1 min-w-0">
                <h1 class="text-2xl font-bold text-gray-900 dark:text-white tracking-tight">{{ ticket.title }}</h1>
                <div class="flex flex-wrap items-center gap-3 mt-2 text-sm text-gray-500 dark:text-gray-400">
                  <span class="inline-flex items-center gap-1"><CalendarDaysIcon class="w-4 h-4" /> {{ formatDate(ticket.created_at) }}</span>
                  <span class="text-gray-300 dark:text-gray-600">·</span>
                  <span class="inline-flex items-center gap-1"><UserCircleIcon class="w-4 h-4" /> {{ ticket.user_name || getUserDisplay(ticket.user_id) }}</span>
                </div>
              </div>
              <StatusBadge :status="ticket.status" size="lg" />
            </div>
            <div v-if="ticket.address" class="flex items-center gap-1.5 mb-4 text-sm text-gray-500">
              <MapPinIcon class="w-4 h-4 shrink-0" />
              {{ ticket.address }}
            </div>
            <div class="divider" />
            <p class="text-gray-700 dark:text-gray-300 whitespace-pre-wrap leading-relaxed">{{ ticket.description }}</p>
          </div>

          <!-- Map -->
          <div v-if="ticket.latitude" class="card p-4">
            <h3 class="font-semibold text-gray-900 dark:text-white mb-2 flex items-center gap-1.5">
              <MapPinIcon class="w-5 h-5 text-gray-400" />
              Местоположение
            </h3>
            <p class="text-xs text-gray-500 mb-2">{{ ticket.latitude }}, {{ ticket.longitude }}</p>
            <div id="admin-ticket-map" class="h-56 rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden z-0"></div>
          </div>

          <!-- Files -->
          <div v-if="ticket.files?.length" class="card p-4">
            <h3 class="font-semibold text-gray-900 dark:text-white mb-3 flex items-center gap-1.5">
              <PhotoIcon class="w-5 h-5 text-gray-400" />
              Файлы ({{ ticket.files.length }})
            </h3>
            <div class="grid grid-cols-2 sm:grid-cols-3 gap-3">
              <div v-for="(f, fi) in ticket.files" :key="f.id"
                @click="f.mime_type?.startsWith('image/') && openLightbox(ticket.files, fi)"
                class="rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden bg-gray-50 dark:bg-gray-800 hover:shadow-md transition-shadow cursor-pointer"
                :class="{ 'cursor-pointer': f.mime_type?.startsWith('image/'), 'cursor-default': !f.mime_type?.startsWith('image/') }">
                <img v-if="f.mime_type?.startsWith('image/')" :src="`/storage/${f.file_path}`" class="w-full h-28 object-cover" loading="lazy" />
                <div v-else class="h-28 flex items-center justify-center text-gray-400">
                  <PhotoIcon class="w-8 h-8" />
                </div>
                <div class="p-2 text-xs truncate border-t border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800">{{ f.file_path.split('/').pop() }}</div>
              </div>
            </div>
          </div>

          <!-- Comments -->
          <div class="card p-6">
            <h3 class="font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-1.5">
              <ChatBubbleLeftRightIcon class="w-5 h-5 text-gray-400" />
              Комментарии ({{ ticket.comments?.length || 0 }})
            </h3>

            <div v-if="ticket.comments?.length" class="space-y-3 mb-6 max-h-96 overflow-y-auto pr-1 -mr-1">
              <div v-for="c in ticket.comments" :key="c.id" class="flex gap-3 p-4 bg-gray-50 dark:bg-gray-800/50 rounded-lg">
                <div class="w-9 h-9 rounded-full bg-primary-100 dark:bg-primary-900/50 flex items-center justify-center shrink-0">
                  <UserCircleIcon class="w-5 h-5 text-primary-600 dark:text-primary-400" />
                </div>
                <div class="flex-1">
                  <div class="flex items-center gap-2 mb-1">
                    <span class="text-sm font-semibold text-gray-900 dark:text-white">{{ c.author_name || getUserName(c.author_id) }}</span>
                    <span v-if="c.author_role === 'admin'" class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-semibold bg-primary-50 text-primary-700 dark:bg-primary-900/40 dark:text-primary-300">
                      <ShieldCheckIcon class="w-3.5 h-3.5" />
                      Администратор
                    </span>
                    <span class="text-xs text-gray-400">{{ formatDate(c.created_at) }}</span>
                  </div>
                  <p class="text-sm text-gray-700 dark:text-gray-300 whitespace-pre-wrap">{{ c.comment_text }}</p>
                </div>
              </div>
            </div>
            <div v-else class="text-sm text-gray-400 py-4 text-center">Комментариев пока нет</div>

            <div class="border-t border-gray-200 dark:border-gray-700 pt-4">
              <div class="relative">
                <textarea v-model="commentText" class="form-textarea text-sm" rows="2" maxlength="2000" placeholder="Добавить комментарий..."></textarea>
                <span class="absolute bottom-2 right-3 text-xs text-gray-400">{{ commentText.length }}/2000</span>
              </div>
              <button @click="addComment" class="btn-primary btn-sm mt-2" :disabled="commenting || !commentText.trim()">
                {{ commenting ? 'Отправка...' : 'Отправить комментарий' }}
              </button>
            </div>
          </div>
        </div>

        <!-- Right: management sidebar -->
        <div class="space-y-6">

          <!-- Status -->
          <div class="card p-5">
            <h3 class="font-semibold text-gray-900 dark:text-white mb-3 flex items-center gap-1.5">
              <ArrowPathIcon class="w-5 h-5 text-gray-400" />
              Статус
            </h3>
            <div class="space-y-2">
              <button
                v-for="s in statuses"
                :key="s"
                @click="changeStatus(s)"
                :disabled="ticket.status === s"
                class="w-full text-left px-3 py-2.5 rounded-lg text-sm font-medium transition-colors flex items-center gap-2"
                :class="ticket.status === s
                  ? 'bg-primary-50 dark:bg-primary-900/30 text-primary-700 dark:text-primary-300 cursor-not-allowed'
                  : 'bg-gray-50 dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 cursor-pointer'"
              >
                <CheckCircleIcon v-if="ticket.status === s" class="w-4 h-4" />
                <span v-else class="w-4 h-4" />
                {{ statusLabels[s] }}
              </button>
            </div>
          </div>

          <!-- Assign -->
          <div class="card p-5">
            <h3 class="font-semibold text-gray-900 dark:text-white mb-3 flex items-center gap-1.5">
              <ClipboardDocumentCheckIcon class="w-5 h-5 text-gray-400" />
              Назначение
            </h3>
            <div v-if="ticket.assigned_to" class="text-sm text-gray-600 dark:text-gray-400 mb-2">
              Исполнитель: <strong class="text-gray-900 dark:text-white">{{ ticket.assigned_to_name || getUserDisplay(ticket.assigned_to) }}</strong>
            </div>
            <button @click="assign" :disabled="!!ticket.assigned_to" class="btn-primary w-full text-sm" :class="{ 'opacity-50 cursor-not-allowed': ticket.assigned_to }">
              <WrenchScrewdriverIcon v-if="!ticket.assigned_to" class="w-4 h-4" />
              {{ ticket.assigned_to ? 'Назначена' : 'Назначить на себя' }}
            </button>
          </div>

          <!-- User info -->
          <div class="card p-5">
            <h3 class="font-semibold text-gray-900 dark:text-white mb-3 flex items-center gap-1.5">
              <UserCircleIcon class="w-5 h-5 text-gray-400" />
              Заявитель
            </h3>
            <div class="text-sm space-y-2">
              <p class="text-gray-700 dark:text-gray-300">{{ ticket.user_name || getUserDisplay(ticket.user_id) }}</p>
              <p class="text-xs text-gray-400 inline-flex items-center gap-1">
                <CalendarDaysIcon class="w-3.5 h-3.5" />
                {{ formatDate(ticket.created_at) }}
              </p>
            </div>
          </div>

          <!-- History -->
          <div class="card p-5">
            <h3 class="font-semibold text-gray-900 dark:text-white mb-3 flex items-center gap-1.5">
              <ClockIcon class="w-5 h-5 text-gray-400" />
              История изменений
            </h3>
            <div v-if="history.length === 0" class="text-sm text-gray-400 text-center py-4">История пуста</div>
            <div v-else class="space-y-3 max-h-80 overflow-y-auto pr-1 -mr-1">
              <div v-for="h in history" :key="h.id" class="text-xs border-l-2 border-primary-300 dark:border-primary-600 pl-3 py-1.5">
                <p class="text-gray-400">{{ formatDate(h.created_at) }}</p>
                <p class="text-gray-600 dark:text-gray-400 mt-0.5">
                  <span class="font-medium text-gray-700 dark:text-gray-300">{{ h.changed_by_name || getUserDisplay(h.changed_by) }}</span>
                </p>
                <p class="mt-1 flex items-center gap-1.5 flex-wrap">
                  <span class="bg-gray-100 dark:bg-gray-700 px-1.5 py-0.5 rounded text-gray-600 dark:text-gray-400">{{ h.old_status || '—' }}</span>
                  <span class="text-primary-500 font-bold">→</span>
                  <span class="bg-primary-50 dark:bg-primary-900/30 text-primary-700 dark:text-primary-300 px-1.5 py-0.5 rounded font-semibold">{{ h.new_status }}</span>
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </template>
    <ImageLightbox ref="lightboxRef" />
  </div>
</template>
