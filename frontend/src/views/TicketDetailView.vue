<script setup lang="ts">
import { ref, watch, nextTick, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import { ticketAPI } from '@/api'
import { useAuthStore } from '@/stores/auth'
import { useToast } from '@/composables/useToast'
import StatusBadge from '@/components/StatusBadge.vue'
import SkeletonDetail from '@/components/SkeletonDetail.vue'
import ImageLightbox from '@/components/ImageLightbox.vue'
import L from 'leaflet'

import { ArrowLeftIcon, ArrowUpTrayIcon, MapPinIcon, ChatBubbleLeftRightIcon, PhotoIcon, CalendarDaysIcon, UserCircleIcon } from '@heroicons/vue/24/outline'

// Fix default Leaflet marker icons
delete (L.Icon.Default.prototype as any)._getIconUrl
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
})

const route = useRoute()
const toast = useToast()
const auth = useAuthStore()

const ticket = ref<any>(null)
const loading = ref(true)
const error = ref('')
const uploadFile = ref<File | null>(null)
const uploading = ref(false)
const commentText = ref('')
const commenting = ref(false)
const lightboxRef = ref<InstanceType<typeof ImageLightbox> | null>(null)
let map: L.Map | null = null

function openLightbox(files: any[], index: number) {
  const images = files.filter((f: any) => f.mime_type?.startsWith('image/')).map((f: any) => `/storage/${f.file_path}`)
  if (images.length > 0) lightboxRef.value?.open(images, index)
}

async function loadTicket(silent = false) {
  if (!silent) loading.value = true
  error.value = ''
  try {
    ticket.value = await ticketAPI.get(route.params.id as string)
  } catch (err) {
    error.value = (err as Error).message
    if ((err as Error).message.includes('404')) error.value = 'Заявка не найдена'
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
    loadTicket(true)  // silent refresh, no skeleton
  } catch (err) {
    toast.error((err as Error).message)
    await loadTicket()
  } finally {
    uploading.value = false
  }
}

async function addComment() {
  if (!commentText.value.trim()) return
  commenting.value = true
  const text = commentText.value.trim()
  commentText.value = ''
  try {
    const comment = await ticketAPI.addComment(ticket.value.id, text)
    // Append optimistically without full reload
    if (ticket.value.comments) {
      ticket.value = { ...ticket.value, comments: [...ticket.value.comments, comment] }
    }
    toast.success('Комментарий добавлен')
    loadTicket(true)  // silent background refresh
  } catch (err) {
    toast.error((err as Error).message)
    commentText.value = text
    await loadTicket()
  } finally {
    commenting.value = false
  }
}

function formatDate(dateStr: string) {
  return new Date(dateStr).toLocaleString('ru-RU', {
    day: 'numeric', month: 'long', year: 'numeric', hour: '2-digit', minute: '2-digit'
  })
}

loadTicket()
onUnmounted(() => { if (map) map.remove() })
</script>

<template>
  <div class="max-w-4xl mx-auto px-4 sm:px-6 py-8">

    <div class="mb-6">
      <router-link to="/dashboard" class="inline-flex items-center gap-1.5 text-sm text-primary-600 dark:text-primary-400 hover:text-primary-700 dark:hover:text-primary-300 font-medium transition-colors">
        <ArrowLeftIcon class="w-4 h-4" />
        Назад к заявкам
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
      <router-link to="/dashboard" class="btn-primary">Вернуться к заявкам</router-link>
    </div>

    <template v-else-if="ticket">
      <!-- Header card -->
      <div class="card p-6 mb-6">
        <div class="flex items-start justify-between gap-4 mb-4">
          <div class="flex-1 min-w-0">
            <h1 class="text-2xl font-bold text-gray-900 dark:text-white tracking-tight">{{ ticket.title }}</h1>
            <div class="flex items-center gap-2 mt-2 text-sm text-gray-500 dark:text-gray-400">
              <CalendarDaysIcon class="w-4 h-4" />
              <span>{{ formatDate(ticket.created_at) }}</span>
            </div>
          </div>
          <StatusBadge :status="ticket.status" size="lg" />
        </div>

        <div v-if="ticket.address" class="flex items-center gap-1.5 mb-4 text-sm text-gray-500 dark:text-gray-400">
          <MapPinIcon class="w-4 h-4 shrink-0" />
          {{ ticket.address }}
        </div>

        <div class="divider" />

        <h3 class="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-2">Описание</h3>
        <p class="text-gray-700 dark:text-gray-300 whitespace-pre-wrap leading-relaxed">{{ ticket.description }}</p>
      </div>

      <!-- Map -->
      <div v-if="ticket.latitude" class="card p-4 mb-6">
        <h3 class="font-semibold text-gray-900 dark:text-white mb-2 flex items-center gap-1.5">
          <MapPinIcon class="w-5 h-5 text-gray-400" />
          Местоположение
        </h3>
        <p class="text-xs text-gray-500 dark:text-gray-400 mb-2">{{ ticket.latitude }}, {{ ticket.longitude }}</p>
        <div id="ticket-map" class="h-64 rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden z-0"></div>
      </div>

      <!-- Files -->
      <div class="card p-6 mb-6">
        <h3 class="font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-1.5">
          <PhotoIcon class="w-5 h-5 text-gray-400" />
          Файлы ({{ ticket.files?.length || 0 }})
        </h3>

        <div v-if="ticket.files?.length" class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3 mb-6">
          <div v-for="(f, fi) in ticket.files" :key="f.id"
            @click="f.mime_type?.startsWith('image/') && openLightbox(ticket.files, fi)"
            class="group relative rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden bg-gray-50 dark:bg-gray-800/50 hover:shadow-md transition-shadow"
            :class="{ 'cursor-pointer': f.mime_type?.startsWith('image/'), 'cursor-default': !f.mime_type?.startsWith('image/') }">
            <img v-if="f.mime_type?.startsWith('image/')" :src="`/storage/${f.file_path}`" class="w-full h-32 object-cover" loading="lazy" />
            <div v-else class="h-32 flex items-center justify-center text-gray-400">
              <PhotoIcon class="w-8 h-8" />
            </div>
            <div class="p-2 text-xs truncate border-t border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800">{{ f.file_path.split('/').pop() }}</div>
          </div>
        </div>

        <div class="border-t border-gray-200 dark:border-gray-700 pt-4">
          <h4 class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Загрузить файл (JPEG/PNG)</h4>
          <div class="flex flex-col sm:flex-row gap-2 items-start sm:items-center">
            <label class="btn-secondary btn-sm cursor-pointer inline-flex items-center gap-1.5">
              <ArrowUpTrayIcon class="w-4 h-4" />
              Выбрать файл
              <input type="file" accept="image/jpeg,image/png" class="hidden" @change="e => uploadFile = (e.target as HTMLInputElement).files![0]" />
            </label>
            <span v-if="uploadFile" class="text-sm text-gray-500 truncate max-w-[200px]">{{ uploadFile.name }}</span>
            <button @click="doUpload" class="btn-primary btn-sm" :disabled="uploading || !uploadFile">
              {{ uploading ? 'Загрузка...' : 'Загрузить' }}
            </button>
          </div>
        </div>
      </div>

      <!-- Comments -->
      <div class="card p-6">
        <h3 class="font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-1.5">
          <ChatBubbleLeftRightIcon class="w-5 h-5 text-gray-400" />
          Комментарии ({{ ticket.comments?.length || 0 }})
        </h3>

        <div v-if="!ticket.comments?.length" class="text-sm text-gray-400 dark:text-gray-500 py-8 text-center">
          <ChatBubbleLeftRightIcon class="w-8 h-8 mx-auto mb-2 text-gray-300 dark:text-gray-600" />
          Комментариев пока нет
        </div>

        <div v-else class="space-y-3 mb-6">
          <div v-for="c in ticket.comments" :key="c.id" class="flex gap-3 p-4 bg-gray-50 dark:bg-gray-800/50 rounded-lg">
            <div class="w-9 h-9 rounded-full bg-primary-100 dark:bg-primary-900/50 flex items-center justify-center shrink-0">
              <UserCircleIcon class="w-5 h-5 text-primary-600 dark:text-primary-400" />
            </div>
            <div class="flex-1 min-w-0">
              <div class="flex items-center gap-2 mb-1">
                <span class="text-sm font-semibold text-gray-900 dark:text-white">{{ c.author_name }}</span>
                <span v-if="c.author_role === 'admin'" class="inline-flex items-center px-1.5 py-0.5 rounded text-xs font-bold bg-primary-100 text-primary-700 dark:bg-primary-900/50 dark:text-primary-300">Admin</span>
                <span class="text-xs text-gray-400">{{ formatDate(c.created_at) }}</span>
              </div>
              <p class="text-sm text-gray-700 dark:text-gray-300 whitespace-pre-wrap leading-relaxed">{{ c.comment_text }}</p>
            </div>
          </div>
        </div>

        <!-- Comment form -->
        <div class="border-t border-gray-200 dark:border-gray-700 pt-4">
          <textarea v-model="commentText" class="form-textarea text-sm" rows="2" placeholder="Добавить комментарий..."></textarea>
          <button @click="addComment" class="btn-primary btn-sm mt-2" :disabled="commenting || !commentText.trim()">
            {{ commenting ? 'Отправка...' : 'Отправить комментарий' }}
          </button>
        </div>
      </div>
    </template>
    <ImageLightbox ref="lightboxRef" />
  </div>
</template>
