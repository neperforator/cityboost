<script setup lang="ts">
import { ref, watch, nextTick, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { adminAPI } from '@/api'
import { useAuthStore } from '@/stores/auth'
import { useUsers } from '@/composables/useUsers'
import { useToast } from '@/composables/useToast'
import type { TicketStatus } from '@/types'
import StatusBadge from '@/components/StatusBadge.vue'
import SkeletonDetail from '@/components/SkeletonDetail.vue'
import ImageLightbox from '@/components/ImageLightbox.vue'
import { Marker, type Map } from 'maplibre-gl'
import { createMap } from '@/lib/map'

import { ArrowLeftIcon, MapPinIcon, ChatBubbleLeftRightIcon, PhotoIcon, CalendarDaysIcon, CheckCircleIcon, UserCircleIcon, ShieldCheckIcon, ArrowPathIcon, ClipboardDocumentCheckIcon, ClockIcon, ExclamationTriangleIcon, NoSymbolIcon } from '@heroicons/vue/24/outline'
import { WrenchScrewdriverIcon } from '@heroicons/vue/24/solid'

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
const closeReason = ref('')
const pendingClose = ref(false)
const lightboxRef = ref<InstanceType<typeof ImageLightbox> | null>(null)
let map: Map | null = null

function openLightbox(files: any[], index: number) {
  const images = files.filter((f: any) => f.mime_type?.startsWith('image/')).map((f: any) => `/storage/${f.file_path}`)
  if (images.length > 0) lightboxRef.value?.open(images, index)
}

const statuses = ['NEW', 'IN_WORK', 'DONE', 'CLOSED']

const statusLabels: Record<string, string> = {
  NEW: 'Новая',
  IN_WORK: 'В работе',
  DONE: 'Выполнена',
  CLOSED: 'Отклонена',
}

const statusActions: Record<string, string> = {
  NEW: 'Вернуть в новые',
  IN_WORK: 'Взять в работу',
  DONE: 'Выполнить',
  CLOSED: 'Отклонить',
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
onUnmounted(() => {
  if (map) map.remove()
  map = null
})
watch(ticket, async (val) => {
  if (!val?.latitude || !val?.longitude) return
  await nextTick()
  const container = document.getElementById('admin-ticket-map')
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

async function changeStatus(status: string) {
  if (status === 'CLOSED') {
    if (!pendingClose.value) {
      closeReason.value = ''
      pendingClose.value = true
      return
    }
    if (!closeReason.value.trim()) {
      toast.warning('Укажите причину отклонения заявки')
      return
    }
  }
  const prev = { ...ticket.value }
  ticket.value = { ...ticket.value, status }
  try {
    await adminAPI.changeStatus(
      ticket.value.id,
      status as TicketStatus,
      status === 'CLOSED' ? closeReason.value.trim() : undefined,
    )
    toast.success(`Статус изменён на «${statusLabels[status]}»`)
    pendingClose.value = false
    closeReason.value = ''
    load(true)
  } catch (err) {
    ticket.value = prev
    toast.error((err as Error).message)
  }
}

function cancelClose() {
  pendingClose.value = false
  closeReason.value = ''
}

async function assign() {
  const prev = { ...ticket.value }
  ticket.value = { ...ticket.value, assigned_to: auth.user!.id, status: 'IN_WORK' }
  try {
    await adminAPI.assign(ticket.value.id)
    toast.success('Заявка назначена на вас')
    load(true)
  } catch (err) {
    ticket.value = prev
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
    if (ticket.value.comments) {
      ticket.value = { ...ticket.value, comments: [...ticket.value.comments, comment] }
    }
    toast.success('Сообщение отправлено')
    load(true)
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

const historyActionIcons: Record<string, any> = {
  CREATED: CheckCircleIcon,
  STATUS_CHANGED: ArrowPathIcon,
  ASSIGNED: WrenchScrewdriverIcon,
  COMMENT_ADDED: ChatBubbleLeftRightIcon,
  FILE_ADDED: PhotoIcon,
}

function historyActionLabel(h: any): string {
  switch (h.action) {
    case 'CREATED':
      return 'Заявка создана'
    case 'ASSIGNED':
      return 'Назначена на исполнителя'
    case 'COMMENT_ADDED':
      return 'Добавлено сообщение'
    case 'FILE_ADDED':
      return 'Прикреплён файл'
    default:
      return `Статус: ${statusLabels[h.old_status] || '—'} → ${statusLabels[h.new_status] || h.new_status}`
  }
}
</script>

<template>
  <div class="mx-auto max-w-6xl px-4 py-8 sm:px-8 sm:py-10">
    <router-link to="/admin/tickets" class="inline-flex items-center gap-1.5 text-sm font-medium text-ink-soft transition-colors hover:text-primary-700 dark:text-ink-dark-soft dark:hover:text-primary-300">
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
          <router-link to="/admin/tickets" class="btn-secondary btn-sm mt-4">Назад</router-link>
        </div>
      </div>
    </div>

    <template v-else-if="ticket">
      <header class="mt-6 border-b-2 border-line pb-7 dark:border-line-dark">
        <div class="flex flex-wrap items-start justify-between gap-4">
          <div class="min-w-0 flex-1">
            <p class="page-kicker">Администрирование / заявка</p>
            <h1 class="mt-2 font-display text-2xl font-semibold leading-tight tracking-tight text-ink dark:text-ink-dark sm:text-3xl">
              {{ ticket.title }}
            </h1>
            <div class="mt-3 flex flex-wrap items-center gap-x-5 gap-y-1.5 text-sm text-ink-soft dark:text-ink-dark-soft">
              <span class="inline-flex items-center gap-1.5">
                <CalendarDaysIcon class="h-4 w-4" />
                {{ formatDate(ticket.created_at) }}
              </span>
              <span class="inline-flex items-center gap-1.5">
                <UserCircleIcon class="h-4 w-4" />
                {{ ticket.user_name || getUserDisplay(ticket.user_id) }}
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

      <div class="mt-6 grid gap-5 lg:grid-cols-[1fr_300px]">
        <!-- Main -->
        <div class="space-y-5">
          <section class="panel p-5 sm:p-6">
            <h2 class="text-xs font-semibold text-ink-soft dark:text-ink-dark-soft">Описание</h2>
            <p class="mt-3 whitespace-pre-wrap text-sm leading-7 text-ink dark:text-ink-dark">{{ ticket.description }}</p>

            <div v-if="ticket.status === 'CLOSED'" class="mt-5 border-l-4 border-l-red-500 bg-red-50 p-4 dark:bg-red-900/20">
              <h3 class="flex items-center gap-1.5 text-xs font-semibold text-red-700 dark:text-red-300">
                <NoSymbolIcon class="h-4 w-4" />
                Заявка отклонена
              </h3>
              <p class="mt-1 text-sm leading-6 text-red-900 dark:text-red-200">
                Снята с рассмотрения: спам, дубль или не относится к городу.
              </p>
              <p v-if="ticket.close_reason" class="mt-2 whitespace-pre-wrap text-sm leading-6 text-red-900 dark:text-red-200">
                <span class="font-semibold">Причина:</span> {{ ticket.close_reason }}
              </p>
            </div>
          </section>

          <section v-if="ticket.latitude" class="panel p-4 sm:p-5">
            <h2 class="flex items-center gap-1.5 text-xs font-semibold text-ink-soft dark:text-ink-dark-soft">
              <MapPinIcon class="h-4 w-4" />
              Местоположение
            </h2>
            <div id="admin-ticket-map" class="z-0 mt-3 h-56 overflow-hidden border-2 border-line dark:border-line-dark"></div>
          </section>

          <section v-if="ticket.files?.length" class="panel p-5 sm:p-6">
            <h2 class="flex items-center gap-1.5 text-xs font-semibold text-ink-soft dark:text-ink-dark-soft">
              <PhotoIcon class="h-4 w-4" />
              Файлы ({{ ticket.files.length }})
            </h2>
            <div class="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-3">
              <div
                v-for="(f, fi) in ticket.files"
                :key="f.id"
                @click="f.mime_type?.startsWith('image/') && openLightbox(ticket.files, fi)"
                @keydown.enter.prevent="f.mime_type?.startsWith('image/') && openLightbox(ticket.files, fi)"
                @keydown.space.prevent="f.mime_type?.startsWith('image/') && openLightbox(ticket.files, fi)"
                :role="f.mime_type?.startsWith('image/') ? 'button' : undefined"
                :tabindex="f.mime_type?.startsWith('image/') ? 0 : -1"
                :aria-label="f.mime_type?.startsWith('image/') ? `Открыть фото ${f.file_path.split('/').pop()}` : undefined"
                class="overflow-hidden border-2 border-line bg-surface-muted transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-primary-500 dark:border-line-dark dark:bg-surface-dark-muted"
                :class="{ 'cursor-pointer hover:border-primary-400': f.mime_type?.startsWith('image/'), 'cursor-default': !f.mime_type?.startsWith('image/') }"
              >
                <img v-if="f.mime_type?.startsWith('image/')" :src="`/storage/${f.file_path}`" class="h-28 w-full object-cover" loading="lazy" />
                <div v-else class="flex h-28 items-center justify-center text-ink-soft dark:text-ink-dark-soft">
                  <PhotoIcon class="h-8 w-8" />
                </div>
                <div class="truncate border-t-2 border-line px-2 py-1.5 text-xs text-ink-soft dark:border-line-dark dark:text-ink-dark-soft">{{ f.file_path.split('/').pop() }}</div>
              </div>
            </div>
          </section>

          <section class="panel p-5 sm:p-6">
            <h2 class="flex items-center gap-1.5 text-xs font-semibold text-ink-soft dark:text-ink-dark-soft">
              <ChatBubbleLeftRightIcon class="h-4 w-4" />
              Связь с заявителем ({{ ticket.comments?.length || 0 }})
            </h2>

            <div v-if="ticket.comments?.length" class="mt-4 max-h-96 space-y-3 overflow-y-auto pr-1">
              <div v-for="c in ticket.comments" :key="c.id" class="flex gap-3 border-l-2 border-line bg-surface-muted p-4 dark:border-line-dark dark:bg-surface-dark-muted">
                <div class="flex h-8 w-8 shrink-0 items-center justify-center rounded-sm bg-primary-500 text-xs font-bold text-white">
                  {{ (c.author_name || getUserName(c.author_id))?.slice(0, 1).toUpperCase() }}
                </div>
                <div class="min-w-0 flex-1">
                  <div class="flex flex-wrap items-center gap-2">
                    <span class="text-sm font-semibold text-ink dark:text-ink-dark">{{ c.author_name || getUserName(c.author_id) }}</span>
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
            <div v-else class="py-6 text-center text-sm text-ink-soft dark:text-ink-dark-soft">Сообщений пока нет</div>

            <div v-if="ticket.status !== 'DONE' && ticket.status !== 'CLOSED'" class="mt-5 border-t-2 border-line pt-4 dark:border-line-dark">
              <div class="relative">
                <textarea v-model="commentText" class="form-textarea pb-6 text-sm" rows="2" maxlength="2000" placeholder="Написать сообщение заявителю..."></textarea>
                <span class="absolute bottom-2 right-3 text-xs text-ink-soft dark:text-ink-dark-soft">{{ commentText.length }}/2000</span>
              </div>
              <button @click="addComment" class="btn-primary btn-sm mt-2" :disabled="commenting || !commentText.trim()">
                {{ commenting ? 'Отправка...' : 'Отправить сообщение' }}
              </button>
            </div>
          </section>
        </div>

        <!-- Sidebar -->
        <aside class="space-y-5">
          <section class="panel p-5">
            <h2 class="flex items-center gap-1.5 text-xs font-semibold text-ink-soft dark:text-ink-dark-soft">
              <ArrowPathIcon class="h-4 w-4" />
              Статус
            </h2>
            <div class="mt-3 space-y-2">
              <button
                v-for="s in statuses"
                :key="s"
                @click="changeStatus(s)"
                :disabled="ticket.status === s"
                class="flex w-full items-center gap-2 border-2 px-3 py-2 text-left text-sm font-medium transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-primary-500"
                :class="ticket.status === s
                  ? 'cursor-not-allowed border-primary-500 bg-primary-500 text-white'
                  : s === 'CLOSED'
                    ? 'cursor-pointer border-red-300 text-red-700 hover:border-red-500 dark:border-red-800 dark:text-red-300'
                    : 'cursor-pointer border-line text-ink hover:border-primary-400 dark:border-line-dark dark:text-ink-dark dark:hover:border-primary-500'"
              >
                <CheckCircleIcon v-if="ticket.status === s" class="h-4 w-4" />
                <span v-else class="h-4 w-4" />
                {{ ticket.status === s ? statusLabels[s] : (statusActions[s] || statusLabels[s]) }}
              </button>
            </div>

            <div v-if="pendingClose" class="mt-4 border-t-2 border-line pt-4 dark:border-line-dark">
              <label for="close-reason" class="form-label">Причина отклонения</label>
              <textarea
                id="close-reason"
                v-model="closeReason"
                class="form-textarea text-sm"
                rows="3"
                maxlength="1000"
                placeholder="Спам, дубль, не относится к городу..."
              ></textarea>
              <span class="mt-1 block text-right text-xs text-ink-soft dark:text-ink-dark-soft">{{ closeReason.length }}/1000</span>
              <div class="mt-2 flex gap-2">
                <button @click="changeStatus('CLOSED')" class="btn-danger btn-sm flex-1" :disabled="!closeReason.trim()">Отклонить заявку</button>
                <button @click="cancelClose" class="btn-secondary btn-sm">Отмена</button>
              </div>
            </div>
          </section>

          <section class="panel p-5">
            <h2 class="flex items-center gap-1.5 text-xs font-semibold text-ink-soft dark:text-ink-dark-soft">
              <ClipboardDocumentCheckIcon class="h-4 w-4" />
              Назначение
            </h2>
            <div v-if="ticket.assigned_to" class="mt-2 text-sm text-ink-soft dark:text-ink-dark-soft">
              Исполнитель: <strong class="text-ink dark:text-ink-dark">{{ ticket.assigned_to_name || getUserDisplay(ticket.assigned_to) }}</strong>
            </div>
            <button @click="assign" :disabled="!!ticket.assigned_to" class="btn-primary mt-3 w-full text-sm disabled:opacity-50">
              <WrenchScrewdriverIcon v-if="!ticket.assigned_to" class="h-4 w-4" />
              {{ ticket.assigned_to ? 'Назначена' : 'Назначить на себя' }}
            </button>
          </section>

          <section class="panel p-5">
            <h2 class="flex items-center gap-1.5 text-xs font-semibold text-ink-soft dark:text-ink-dark-soft">
              <UserCircleIcon class="h-4 w-4" />
              Заявитель
            </h2>
            <div class="mt-2 space-y-1 text-sm">
              <p class="text-ink dark:text-ink-dark">{{ ticket.user_name || getUserDisplay(ticket.user_id) }}</p>
              <p class="inline-flex items-center gap-1 text-xs text-ink-soft dark:text-ink-dark-soft">
                <CalendarDaysIcon class="h-3.5 w-3.5" />
                {{ formatDate(ticket.created_at) }}
              </p>
            </div>
          </section>

          <section class="panel p-5">
            <h2 class="flex items-center gap-1.5 text-xs font-semibold text-ink-soft dark:text-ink-dark-soft">
              <ClockIcon class="h-4 w-4" />
              История изменений
            </h2>
            <div v-if="history.length === 0" class="py-4 text-center text-sm text-ink-soft dark:text-ink-dark-soft">История пуста</div>
            <div v-else class="mt-3 max-h-80 space-y-3 overflow-y-auto pr-1">
              <div v-for="h in history" :key="h.id" class="border-l-2 border-primary-300 py-1 pl-3 text-xs dark:border-primary-600">
                <p class="text-ink-soft dark:text-ink-dark-soft">{{ formatDate(h.created_at) }}</p>
                <p class="mt-1 flex items-center gap-1.5 text-ink-soft dark:text-ink-dark-soft">
                  <component :is="historyActionIcons[h.action] || ClockIcon" class="h-4 w-4 shrink-0 text-primary-500" />
                  <span class="font-medium text-ink dark:text-ink-dark">{{ h.changed_by_name || getUserDisplay(h.changed_by) }}</span>
                  <span>—</span>
                  <span class="font-semibold text-ink dark:text-ink-dark">{{ historyActionLabel(h) }}</span>
                </p>
                <p v-if="h.details" class="mt-1 text-ink-soft dark:text-ink-dark-soft">{{ h.details }}</p>
                <p v-if="h.action === 'STATUS_CHANGED'" class="mt-1 flex flex-wrap items-center gap-1.5">
                  <span class="border border-line px-1.5 py-0.5 text-ink-soft dark:border-line-dark dark:text-ink-dark-soft">{{ statusLabels[h.old_status] || h.old_status || '—' }}</span>
                  <span class="font-bold text-primary-500">→</span>
                  <span class="border border-primary-300 px-1.5 py-0.5 font-semibold text-primary-700 dark:border-primary-700 dark:text-primary-300">{{ statusLabels[h.new_status] || h.new_status }}</span>
                </p>
              </div>
            </div>
          </section>
        </aside>
      </div>
    </template>
    <ImageLightbox ref="lightboxRef" />
  </div>
</template>
