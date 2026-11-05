<script setup lang="ts">
import { ref, watch, nextTick, onUnmounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import { ticketAPI } from '@/api'
import { useAuthStore } from '@/stores/auth'
import { useToast } from '@/composables/useToast'
import StatusBadge from '@/components/StatusBadge.vue'
import SkeletonDetail from '@/components/SkeletonDetail.vue'
import ImageLightbox from '@/components/ImageLightbox.vue'
import { Marker, type Map } from 'maplibre-gl'
import { createMap } from '@/lib/map'

import { ArrowLeftIcon, ArrowUpTrayIcon, MapPinIcon, ChatBubbleLeftRightIcon, PhotoIcon, CalendarDaysIcon, ShieldCheckIcon, ExclamationTriangleIcon, CheckCircleIcon } from '@heroicons/vue/24/outline'

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
let map: Map | null = null

const statusOrder = ['NEW', 'IN_WORK', 'DONE', 'CLOSED']
const statusIndex = computed(() => Math.max(0, statusOrder.indexOf(ticket.value?.status)))

const routeStops = [
  { key: 'NEW', label: 'Зарегистрирована' },
  { key: 'IN_WORK', label: 'В работе' },
  { key: 'DONE', label: 'Выполнена' },
  { key: 'CLOSED', label: 'Закрыта' },
]

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

watch(ticket, async (val) => {
  if (!val?.latitude || !val?.longitude) return
  await nextTick()
  const container = document.getElementById('ticket-map')
  if (!container || map) return
  map = createMap(container, {
    center: [val.longitude, val.latitude],
    zoom: 15,
    attributionControl: false,
  })
  new Marker({ color: '#0E5A4A' })
    .setLngLat([val.longitude, val.latitude])
    .addTo(map)
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
    loadTicket(true)
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
    if (ticket.value.comments) {
      ticket.value = { ...ticket.value, comments: [...ticket.value.comments, comment] }
    }
    toast.success('Комментарий добавлен')
    loadTicket(true)
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
onUnmounted(() => {
  if (map) map.remove()
  map = null
})
</script>

<template>
  <div class="mx-auto max-w-5xl px-4 py-8 sm:px-8 sm:py-10">
    <router-link to="/dashboard" class="inline-flex items-center gap-1.5 text-sm font-medium text-ink-soft transition-colors hover:text-primary-700 dark:text-ink-dark-soft dark:hover:text-primary-300">
      <ArrowLeftIcon class="h-4 w-4" />
      Назад к заявкам
    </router-link>

    <SkeletonDetail v-if="loading" class="mt-6" />

    <div v-else-if="error" class="panel mt-6 border-l-4 border-l-red-500 p-6">
      <div class="flex items-start gap-3">
        <ExclamationTriangleIcon class="mt-0.5 h-5 w-5 shrink-0 text-red-600 dark:text-red-400" />
        <div>
          <p class="font-semibold text-ink dark:text-ink-dark">Не удалось загрузить заявку</p>
          <p class="mt-1 text-sm text-ink-soft dark:text-ink-dark-soft">{{ error }}</p>
          <router-link to="/dashboard" class="btn-secondary btn-sm mt-4">Вернуться к заявкам</router-link>
        </div>
      </div>
    </div>

    <template v-else-if="ticket">
      <header class="mt-6 border-b-2 border-line pb-7 dark:border-line-dark">
        <div class="flex flex-wrap items-start justify-between gap-4">
          <div class="min-w-0 flex-1">
            <p class="page-kicker">Заявка</p>
            <h1 class="mt-2 font-display text-2xl font-semibold leading-tight tracking-tight text-ink dark:text-ink-dark sm:text-3xl">
              {{ ticket.title }}
            </h1>
            <div class="mt-3 flex flex-wrap items-center gap-x-5 gap-y-1.5 text-sm text-ink-soft dark:text-ink-dark-soft">
              <span class="inline-flex items-center gap-1.5">
                <CalendarDaysIcon class="h-4 w-4" />
                {{ formatDate(ticket.created_at) }}
              </span>
              <span v-if="ticket.address" class="inline-flex items-center gap-1.5">
                <MapPinIcon class="h-4 w-4 shrink-0" />
                {{ ticket.address }}
              </span>
            </div>
          </div>
          <StatusBadge :status="ticket.status" size="lg" />
        </div>
      </header>

      <!-- Route progress -->
      <section class="mt-6 border-2 border-line bg-surface p-5 dark:border-line-dark dark:bg-surface-dark">
        <p class="text-xs font-semibold text-ink-soft dark:text-ink-dark-soft">Маршрут заявки</p>
        <div class="mt-5 flex flex-col gap-0 sm:flex-row sm:items-start">
          <div v-for="(stop, i) in routeStops" :key="stop.key" class="relative flex flex-1 gap-3 pb-5 last:pb-0 sm:flex-col sm:gap-2 sm:pb-0">
            <span
              class="absolute left-[5px] top-3 h-full w-0.5 sm:left-3 sm:right-0 sm:top-[5px] sm:h-0.5 sm:w-auto"
              :class="i < routeStops.length - 1 ? (i < statusIndex ? 'bg-primary-500' : 'bg-line dark:bg-line-dark') : 'bg-transparent'"
            />
            <span
              class="relative z-10 flex h-3 w-3 shrink-0 items-center justify-center rounded-full border-2 sm:mt-0"
              :class="i <= statusIndex ? 'border-primary-500 bg-primary-500' : 'border-line bg-surface dark:border-line-dark dark:bg-surface-dark'"
            />
            <div class="sm:pr-3">
              <p class="text-xs font-semibold" :class="i <= statusIndex ? 'text-ink dark:text-ink-dark' : 'text-ink-soft dark:text-ink-dark-soft'">{{ stop.label }}</p>
            </div>
          </div>
        </div>
      </section>

      <!-- Description -->
      <section class="panel mt-5 p-5 sm:p-6">
        <h2 class="text-xs font-semibold text-ink-soft dark:text-ink-dark-soft">Описание</h2>
        <p class="mt-3 whitespace-pre-wrap text-sm leading-7 text-ink dark:text-ink-dark">{{ ticket.description }}</p>

        <div v-if="ticket.status === 'CLOSED' && ticket.close_reason" class="mt-5 border-l-4 border-l-emerald-500 bg-emerald-50 p-4 dark:bg-emerald-900/20">
          <h3 class="flex items-center gap-1.5 text-xs font-semibold text-emerald-700 dark:text-emerald-300">
            <CheckCircleIcon class="h-4 w-4" />
            Причина закрытия
          </h3>
          <p class="mt-1 whitespace-pre-wrap text-sm leading-6 text-emerald-900 dark:text-emerald-200">{{ ticket.close_reason }}</p>
        </div>
      </section>

      <!-- Map -->
      <section v-if="ticket.latitude" class="panel mt-5 p-4 sm:p-5">
        <h2 class="flex items-center gap-1.5 text-xs font-semibold text-ink-soft dark:text-ink-dark-soft">
          <MapPinIcon class="h-4 w-4" />
          Местоположение
        </h2>
        <div id="ticket-map" class="z-0 mt-3 h-64 overflow-hidden border-2 border-line dark:border-line-dark"></div>
      </section>

      <!-- Files -->
      <section class="panel mt-5 p-5 sm:p-6">
        <h2 class="flex items-center gap-1.5 text-xs font-semibold text-ink-soft dark:text-ink-dark-soft">
          <PhotoIcon class="h-4 w-4" />
          Файлы ({{ ticket.files?.length || 0 }})
        </h2>

        <div v-if="ticket.files?.length" class="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-3 md:grid-cols-4">
          <div
            v-for="(f, fi) in ticket.files"
            :key="f.id"
            @click="f.mime_type?.startsWith('image/') && openLightbox(ticket.files, fi)"
            @keydown.enter.prevent="f.mime_type?.startsWith('image/') && openLightbox(ticket.files, fi)"
            @keydown.space.prevent="f.mime_type?.startsWith('image/') && openLightbox(ticket.files, fi)"
            :role="f.mime_type?.startsWith('image/') ? 'button' : undefined"
            :tabindex="f.mime_type?.startsWith('image/') ? 0 : -1"
            :aria-label="f.mime_type?.startsWith('image/') ? `Открыть фото ${f.file_path.split('/').pop()}` : undefined"
            class="group overflow-hidden border-2 border-line bg-surface-muted transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-primary-500 dark:border-line-dark dark:bg-surface-dark-muted"
            :class="{ 'cursor-pointer hover:border-primary-400': f.mime_type?.startsWith('image/'), 'cursor-default': !f.mime_type?.startsWith('image/') }"
          >
            <img v-if="f.mime_type?.startsWith('image/')" :src="`/storage/${f.file_path}`" class="h-32 w-full object-cover" loading="lazy" />
            <div v-else class="flex h-32 items-center justify-center text-ink-soft dark:text-ink-dark-soft">
              <PhotoIcon class="h-8 w-8" />
            </div>
            <div class="truncate border-t-2 border-line px-2 py-1.5 text-xs text-ink-soft dark:border-line-dark dark:text-ink-dark-soft">{{ f.file_path.split('/').pop() }}</div>
          </div>
        </div>

        <p v-else class="mt-3 text-sm text-ink-soft dark:text-ink-dark-soft">Файлов пока нет.</p>

        <div v-if="ticket.status !== 'DONE' && ticket.status !== 'CLOSED'" class="mt-5 border-t-2 border-line pt-4 dark:border-line-dark">
          <h3 class="text-sm font-medium text-ink dark:text-ink-dark">Загрузить файл (JPEG/PNG)</h3>
          <div class="mt-2 flex flex-col items-start gap-2 sm:flex-row sm:items-center">
            <label class="btn-secondary btn-sm inline-flex cursor-pointer items-center gap-1.5">
              <ArrowUpTrayIcon class="h-4 w-4" />
              Выбрать файл
              <input type="file" accept="image/jpeg,image/png" class="hidden" @change="e => uploadFile = (e.target as HTMLInputElement).files![0]" />
            </label>
            <span v-if="uploadFile" class="max-w-[220px] truncate text-sm text-ink-soft dark:text-ink-dark-soft">{{ uploadFile.name }}</span>
            <button @click="doUpload" class="btn-primary btn-sm" :disabled="uploading || !uploadFile">
              {{ uploading ? 'Загрузка...' : 'Загрузить' }}
            </button>
          </div>
        </div>
      </section>

      <!-- Comments -->
      <section class="panel mt-5 p-5 sm:p-6">
        <h2 class="flex items-center gap-1.5 text-xs font-semibold text-ink-soft dark:text-ink-dark-soft">
          <ChatBubbleLeftRightIcon class="h-4 w-4" />
          Комментарии ({{ ticket.comments?.length || 0 }})
        </h2>

        <div v-if="!ticket.comments?.length" class="py-8 text-center text-sm text-ink-soft dark:text-ink-dark-soft">
          Комментариев пока нет
        </div>

        <div v-else class="mt-4 max-h-96 space-y-3 overflow-y-auto pr-1">
          <div v-for="c in ticket.comments" :key="c.id" class="flex gap-3 border-l-2 border-line bg-surface-muted p-4 dark:border-line-dark dark:bg-surface-dark-muted">
            <div class="flex h-8 w-8 shrink-0 items-center justify-center rounded-sm bg-primary-500 text-xs font-bold text-white">
              {{ c.author_name?.slice(0, 1).toUpperCase() }}
            </div>
            <div class="min-w-0 flex-1">
              <div class="flex flex-wrap items-center gap-2">
                <span class="text-sm font-semibold text-ink dark:text-ink-dark">{{ c.author_name }}</span>
                <span v-if="c.author_role === 'admin'" class="inline-flex items-center gap-1 border border-primary-300 px-1.5 py-0.5 text-[10px] font-semibold text-primary-700 dark:border-primary-700 dark:text-primary-300">
                  <ShieldCheckIcon class="h-3 w-3" />
                  Администратор
                </span>
                <span class="text-xs text-ink-soft dark:text-ink-dark-soft">{{ formatDate(c.created_at) }}</span>
              </div>
              <p class="mt-1 whitespace-pre-wrap text-sm leading-6 text-ink dark:text-ink-dark">{{ c.comment_text }}</p>
            </div>
          </div>
        </div>

        <div v-if="ticket.status !== 'DONE' && ticket.status !== 'CLOSED'" class="mt-5 border-t-2 border-line pt-4 dark:border-line-dark">
          <div class="relative">
            <textarea v-model="commentText" class="form-textarea pb-6 text-sm" rows="2" maxlength="2000" placeholder="Добавить комментарий..."></textarea>
            <span class="absolute bottom-2 right-3 text-xs text-ink-soft dark:text-ink-dark-soft">{{ commentText.length }}/2000</span>
          </div>
          <button @click="addComment" class="btn-primary btn-sm mt-2" :disabled="commenting || !commentText.trim()">
            {{ commenting ? 'Отправка...' : 'Отправить комментарий' }}
          </button>
        </div>
      </section>
    </template>
    <ImageLightbox ref="lightboxRef" />
  </div>
</template>
