<script setup lang="ts">
import { ref, watch, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { ticketAPI } from '@/api'
import { useToast } from '@/composables/useToast'
import MapPicker from '@/components/MapPicker.vue'
import { ArrowLeftIcon, PhotoIcon, XMarkIcon, ExclamationCircleIcon, MapPinIcon } from '@heroicons/vue/24/outline'
import { PlusCircleIcon } from '@heroicons/vue/24/solid'

const router = useRouter()
const toast = useToast()

const title = ref('')
const description = ref('')
const address = ref('')
const coords = ref({ lat: null, lng: null })
const loading = ref(false)
const error = ref('')

const errors = ref({ title: '', description: '', photos: '' })

const selectedFiles = ref<File[]>([])
const fileInput = ref<HTMLInputElement | null>(null)
const MAX_FILES = 5
const ALLOWED_TYPES = ['image/jpeg', 'image/png']
const MAX_FILE_SIZE = 10 * 1024 * 1024

const dragActive = ref(false)
let dragDepth = 0

const filePreviews = ref<Array<{ name: string; size: string; url: string }>>([])
// Один object URL на файл: переиспользуем и освобождаем при удалении/уходе.
const previewUrls = new Map<File, string>()

function syncPreviews() {
  const files = selectedFiles.value

  for (const [file, url] of previewUrls) {
    if (!files.includes(file)) {
      URL.revokeObjectURL(url)
      previewUrls.delete(file)
    }
  }

  filePreviews.value = files.map((file) => {
    let url = previewUrls.get(file)
    if (!url) {
      url = URL.createObjectURL(file)
      previewUrls.set(file, url)
    }
    return {
      name: file.name,
      size: (file.size / 1024 / 1024).toFixed(1) + ' MB',
      url,
    }
  })
}

function releasePreviews() {
  for (const url of previewUrls.values()) URL.revokeObjectURL(url)
  previewUrls.clear()
  filePreviews.value = []
}

watch(selectedFiles, syncPreviews, { immediate: true })

onUnmounted(releasePreviews)

function processFiles(files: FileList | File[]) {
  errors.value.photos = ''
  const incoming = Array.from(files)
  const accepted: File[] = []
  let fileMsg = ''

  for (const file of incoming) {
    if (!ALLOWED_TYPES.includes(file.type)) {
      fileMsg = `Файл "${file.name}" недопустимого типа. Разрешены: JPEG, PNG`
      continue
    }
    if (file.size > MAX_FILE_SIZE) {
      fileMsg = `Файл "${file.name}" слишком большой (макс. 10 МБ)`
      continue
    }
    if (file.size === 0) {
      fileMsg = `Файл "${file.name}" пустой`
      continue
    }
    accepted.push(file)
  }
  if (fileMsg) errors.value.photos = fileMsg

  const total = selectedFiles.value.length + accepted.length
  if (total > MAX_FILES) {
    errors.value.photos = `Максимум ${MAX_FILES} файлов за раз`
    return
  }

  if (accepted.length) selectedFiles.value = [...selectedFiles.value, ...accepted]
}

function handleFileInput(e: Event) {
  const input = e.target as HTMLInputElement
  if (!input.files?.length) return
  processFiles(input.files)
  input.value = ''
}

function handleDrop(e: DragEvent) {
  dragDepth = 0
  dragActive.value = false
  if (!e.dataTransfer?.files?.length) return
  processFiles(e.dataTransfer.files)
}

function onDragEnter() {
  dragDepth++
  dragActive.value = true
}

function onDragLeave() {
  dragDepth = Math.max(0, dragDepth - 1)
  if (dragDepth === 0) dragActive.value = false
}

function removeFile(index: number) {
  selectedFiles.value = selectedFiles.value.filter((_, i) => i !== index)
  errors.value.photos = ''
}

function onAddressUpdate(val: string) {
  address.value = val
}

async function submit() {
  errors.value = { title: '', description: '', photos: '' }
  let hasErrors = false
  if (!title.value.trim()) { errors.value.title = 'Введите название заявки'; hasErrors = true }
  if (!description.value.trim()) { errors.value.description = 'Введите описание заявки'; hasErrors = true }
  if (selectedFiles.value.length === 0) { errors.value.photos = 'Загрузите хотя бы одно фото'; hasErrors = true }
  if (hasErrors) return

  loading.value = true
  error.value = ''
  try {
    const fd = new FormData()
    fd.append('title', title.value.trim())
    fd.append('description', description.value.trim())
    if (address.value.trim()) fd.append('address', address.value.trim())
    if (coords.value.lat) fd.append('latitude', String(coords.value.lat))
    if (coords.value.lng) fd.append('longitude', String(coords.value.lng))
    for (const file of selectedFiles.value) {
      fd.append('files', file)
    }
    const ticket = await ticketAPI.create(fd)
    releasePreviews()
    toast.success('Заявка создана!')
    router.push(`/tickets/${ticket.id}`)
  } catch (err) {
    error.value = (err as Error).message
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="mx-auto max-w-6xl px-4 py-8 sm:px-8 sm:py-10">
    <router-link to="/dashboard" class="inline-flex items-center gap-1.5 text-sm font-medium text-ink-soft transition-colors hover:text-primary-700 dark:text-ink-dark-soft dark:hover:text-primary-300">
      <ArrowLeftIcon class="h-4 w-4" />
      Назад к заявкам
    </router-link>

    <header class="mt-5 border-b-2 border-line pb-7 dark:border-line-dark">
      <p class="page-kicker">Новое обращение</p>
      <h1 class="mt-2 font-display text-3xl font-semibold tracking-tight text-ink dark:text-ink-dark">Создать заявку</h1>
      <p class="mt-2 max-w-2xl text-sm leading-6 text-ink-soft dark:text-ink-dark-soft">
        Три шага: опишите проблему, приложите фото и отметьте место. Чем точнее данные, тем быстрее служба начнёт работу.
      </p>
    </header>

    <div class="mt-8 grid gap-6 lg:grid-cols-[220px_1fr]">
      <!-- Step rail -->
      <aside class="hidden lg:block">
        <div class="sticky top-8">
          <div class="relative pl-6">
            <span class="absolute bottom-4 left-[9px] top-4 w-0.5 bg-line dark:bg-line-dark" />
            <div class="relative pb-8 last:pb-0">
              <span class="absolute -left-6 flex h-5 w-5 items-center justify-center rounded-sm border-2 border-primary-500 bg-primary-500 text-[10px] font-bold text-white">1</span>
              <p class="text-sm font-semibold text-ink dark:text-ink-dark">Информация</p>
              <p class="mt-0.5 text-xs text-ink-soft dark:text-ink-dark-soft">Что случилось</p>
            </div>
            <div class="relative pb-8 last:pb-0">
              <span class="absolute -left-6 flex h-5 w-5 items-center justify-center rounded-sm border-2 border-line bg-surface text-[10px] font-bold text-ink-soft dark:border-line-dark dark:bg-surface-dark dark:text-ink-dark-soft">2</span>
              <p class="text-sm font-semibold text-ink dark:text-ink-dark">Фотографии</p>
              <p class="mt-0.5 text-xs text-ink-soft dark:text-ink-dark-soft">Подтверждение</p>
            </div>
            <div class="relative last:pb-0">
              <span class="absolute -left-6 flex h-5 w-5 items-center justify-center rounded-sm border-2 border-line bg-surface text-[10px] font-bold text-ink-soft dark:border-line-dark dark:bg-surface-dark dark:text-ink-dark-soft">3</span>
              <p class="text-sm font-semibold text-ink dark:text-ink-dark">Место</p>
              <p class="mt-0.5 text-xs text-ink-soft dark:text-ink-dark-soft">Карта или адрес</p>
            </div>
          </div>

          <div class="mt-8 border-l-4 border-l-accent-500 bg-surface-muted p-4 text-xs leading-5 text-ink-soft dark:bg-surface-dark-muted dark:text-ink-dark-soft">
            Заявка без фото не принимается: снимок помогает службе оценить проблему до выезда.
          </div>
        </div>
      </aside>

      <form @submit.prevent="submit" novalidate class="space-y-5">
        <!-- Step 1 -->
        <section class="panel p-5 sm:p-7">
          <div class="flex items-start gap-3">
            <span class="flex h-8 w-8 shrink-0 items-center justify-center rounded-sm bg-primary-500 font-display text-sm font-bold text-white">01</span>
            <div>
              <h2 class="font-display text-lg font-semibold text-ink dark:text-ink-dark">Информация</h2>
              <p class="text-xs text-ink-soft dark:text-ink-dark-soft">Кратко и по существу</p>
            </div>
          </div>

          <div class="mt-6 space-y-5 sm:pl-11">
            <div class="form-input-group">
              <label class="form-label">Название <span class="text-red-500">*</span></label>
              <input
                v-model="title"
                type="text"
                class="form-input"
                :class="{ 'form-input-error': errors.title }"
                placeholder="Кратко опишите проблему"
                required
                maxlength="255"
                @input="errors.title = ''"
              />
              <p v-if="errors.title" class="form-error">
                <ExclamationCircleIcon class="h-4 w-4 shrink-0" />
                {{ errors.title }}
              </p>
            </div>

            <div class="form-input-group">
              <label class="form-label">Описание <span class="text-red-500">*</span></label>
              <textarea
                v-model="description"
                class="form-textarea"
                :class="{ 'form-input-error': errors.description }"
                placeholder="Подробно опишите проблему..."
                required
                @input="errors.description = ''"
              ></textarea>
              <p v-if="errors.description" class="form-error">
                <ExclamationCircleIcon class="h-4 w-4 shrink-0" />
                {{ errors.description }}
              </p>
            </div>
          </div>
        </section>

        <!-- Step 2 -->
        <section class="panel p-5 sm:p-7">
          <div class="flex items-start gap-3">
            <span class="flex h-8 w-8 shrink-0 items-center justify-center rounded-sm border-2 border-line font-display text-sm font-bold text-ink-soft dark:border-line-dark dark:text-ink-dark-soft">02</span>
            <div>
              <h2 class="font-display text-lg font-semibold text-ink dark:text-ink-dark">Фотографии</h2>
              <p class="text-xs text-ink-soft dark:text-ink-dark-soft">До {{ MAX_FILES }} файлов, JPEG или PNG</p>
            </div>
          </div>

          <div class="mt-6 sm:pl-11">
            <div
              class="flex cursor-pointer flex-col items-center border-2 border-dashed px-6 py-8 text-center transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-primary-500"
              :class="dragActive
                ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/20'
                : 'border-line hover:border-primary-400 dark:border-line-dark dark:hover:border-primary-500'"
              role="button"
              tabindex="0"
              @click="fileInput?.click()"
              @keydown.enter.prevent="fileInput?.click()"
              @keydown.space.prevent="fileInput?.click()"
              @dragenter.prevent="onDragEnter"
              @dragover.prevent="dragActive = true"
              @dragleave.prevent="onDragLeave"
              @drop.prevent="handleDrop"
            >
              <PhotoIcon class="h-7 w-7 text-primary-600 dark:text-primary-400" />
              <p class="mt-3 text-sm font-medium text-ink dark:text-ink-dark">Нажмите, чтобы выбрать фото</p>
              <p class="mt-1 text-xs text-ink-soft dark:text-ink-dark-soft">или перетащите файлы сюда (макс. 10 МБ каждый)</p>
            </div>
            <input ref="fileInput" type="file" accept="image/jpeg,image/png" multiple class="hidden" @change="handleFileInput" />

            <div v-if="selectedFiles.length" class="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-3 md:grid-cols-5">
              <div v-for="(preview, i) in filePreviews" :key="i" class="group relative overflow-hidden border-2 border-line bg-surface-muted dark:border-line-dark dark:bg-surface-dark-muted">
                <img :src="preview.url" class="h-20 w-full object-cover" alt="" />
                <button
                  type="button"
                  class="absolute right-1 top-1 flex h-6 w-6 items-center justify-center rounded-sm bg-ink/80 text-white transition-colors hover:bg-red-600 focus:outline-none focus-visible:ring-2 focus-visible:ring-white/70"
                  :aria-label="`Удалить ${preview.name}`"
                  @click="removeFile(i)"
                >
                  <XMarkIcon class="h-3.5 w-3.5" />
                </button>
                <div class="truncate px-1.5 py-1 text-[10px] text-ink-soft dark:text-ink-dark-soft">{{ preview.name }} ({{ preview.size }})</div>
              </div>
            </div>
            <p v-if="errors.photos" class="form-error mt-3">
              <ExclamationCircleIcon class="h-4 w-4 shrink-0" />
              {{ errors.photos }}
            </p>
          </div>
        </section>

        <!-- Step 3 -->
        <section class="panel p-5 sm:p-7">
          <div class="flex items-start gap-3">
            <span class="flex h-8 w-8 shrink-0 items-center justify-center rounded-sm border-2 border-line font-display text-sm font-bold text-ink-soft dark:border-line-dark dark:text-ink-dark-soft">03</span>
            <div>
              <h2 class="font-display text-lg font-semibold text-ink dark:text-ink-dark">Местоположение</h2>
              <p class="text-xs text-ink-soft dark:text-ink-dark-soft">Точка на карте или адрес</p>
            </div>
          </div>

          <div class="mt-6 space-y-5 sm:pl-11">
            <div>
              <label class="form-label">Карта</label>
              <p class="mb-2 text-xs text-ink-soft dark:text-ink-dark-soft">Кликните на карте, чтобы указать точное место, или найдите адрес в поле поиска</p>
              <MapPicker v-model="coords" @address="onAddressUpdate" />
            </div>

            <div class="form-input-group">
              <label class="form-label">Адрес (вручную)</label>
              <div class="relative">
                <MapPinIcon class="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-ink-soft dark:text-ink-dark-soft" />
                <input v-model="address" type="text" class="form-input pl-9" placeholder="ул. Ленина, 15" maxlength="500" />
              </div>
            </div>
          </div>
        </section>

        <div v-if="error" class="flex items-start gap-2 border-l-4 border-l-red-500 bg-red-50 px-4 py-3 text-sm text-red-700 dark:bg-red-900/20 dark:text-red-300">
          <ExclamationCircleIcon class="mt-0.5 h-4 w-4 shrink-0" />
          {{ error }}
        </div>

        <div class="flex flex-col gap-3 border-t-2 border-line pt-5 dark:border-line-dark sm:flex-row">
          <button type="submit" class="btn-accent btn-lg flex-1" :disabled="loading">
            <svg v-if="loading" class="h-5 w-5 animate-spin" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" fill="none"/><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/></svg>
            <PlusCircleIcon v-else class="h-5 w-5" />
            {{ loading ? 'Создание...' : 'Создать заявку' }}
          </button>
          <router-link to="/dashboard" class="btn-secondary btn-lg text-center">Отмена</router-link>
        </div>
      </form>
    </div>
  </div>
</template>
