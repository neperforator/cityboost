<script setup lang="ts">
import { ref, computed } from 'vue'
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

// Per-field inline validation errors (server errors stay in `error`)
const errors = ref({ title: '', description: '', photos: '' })

// --- Files ---
const selectedFiles = ref<File[]>([])
const fileInput = ref<HTMLInputElement | null>(null)
const MAX_FILES = 5
const ALLOWED_TYPES = ['image/jpeg', 'image/png']
const MAX_FILE_SIZE = 10 * 1024 * 1024 // 10 MB

// Drag & drop state (depth counter avoids flicker over child elements)
const dragActive = ref(false)
let dragDepth = 0

const filePreviews = computed(() =>
  selectedFiles.value.map(f => ({
    name: f.name,
    size: (f.size / 1024 / 1024).toFixed(1) + ' MB',
    url: URL.createObjectURL(f),
  }))
)

// Shared validation for both the file input and drag & drop
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
  selectedFiles.value.splice(index, 1)
  errors.value.photos = ''
}

function onAddressUpdate(val: string) {
  address.value = val
}

async function submit() {
  // Validate inline — show each problem next to its field
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
  <div class="max-w-4xl mx-auto px-4 sm:px-6 py-8">
    <!-- Back link -->
    <div class="mb-6">
      <router-link to="/dashboard" class="inline-flex items-center gap-1.5 text-sm text-primary-600 dark:text-primary-400 hover:text-primary-700 dark:hover:text-primary-300 font-medium transition-colors">
        <ArrowLeftIcon class="w-4 h-4" />
        Назад к заявкам
      </router-link>
    </div>

    <div class="card p-6 sm:p-8">
      <h1 class="font-display text-2xl font-bold text-gray-900 dark:text-white tracking-tight mb-1">Создать заявку</h1>
      <p class="text-gray-500 dark:text-gray-400 text-sm mb-8">Заполните три шага — остальное мы возьмём на себя</p>

      <form @submit.prevent="submit" novalidate>
        <!-- ═══════ Шаг 1. Информация ═══════ -->
        <section>
          <div class="flex items-center gap-3 mb-5">
            <span class="w-8 h-8 rounded-full bg-primary-600 dark:bg-primary-500 text-white text-sm font-display font-bold flex items-center justify-center shrink-0 shadow-sm">1</span>
            <div>
              <h2 class="font-display text-lg font-semibold text-gray-900 dark:text-white leading-tight">Информация</h2>
              <p class="text-xs text-gray-500 dark:text-gray-400">Что и где случилось</p>
            </div>
          </div>

          <div class="sm:pl-11 space-y-6">
            <!-- Title -->
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
                <ExclamationCircleIcon class="w-4 h-4 shrink-0" />
                {{ errors.title }}
              </p>
            </div>

            <!-- Description -->
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
                <ExclamationCircleIcon class="w-4 h-4 shrink-0" />
                {{ errors.description }}
              </p>
            </div>
          </div>
        </section>

        <div class="border-t border-gray-100 dark:border-gray-700/50 my-8"></div>

        <!-- ═══════ Шаг 2. Фотографии ═══════ -->
        <section>
          <div class="flex items-center gap-3 mb-5">
            <span class="w-8 h-8 rounded-full bg-primary-600 dark:bg-primary-500 text-white text-sm font-display font-bold flex items-center justify-center shrink-0 shadow-sm">2</span>
            <div>
              <h2 class="font-display text-lg font-semibold text-gray-900 dark:text-white leading-tight">Фотографии</h2>
              <p class="text-xs text-gray-500 dark:text-gray-400">Подтвердят проблему — можно до {{ MAX_FILES }}</p>
            </div>
          </div>

          <div class="sm:pl-11">
            <div
              class="border-2 border-dashed rounded-xl p-6 sm:p-8 text-center transition-colors cursor-pointer focus-visible:ring-2 focus-visible:ring-primary-500 focus-visible:ring-offset-2 focus:outline-none"
              :class="dragActive
                ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/20'
                : 'border-gray-300 dark:border-gray-600 hover:border-primary-400 dark:hover:border-primary-500'"
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
              <div class="w-14 h-14 rounded-2xl bg-primary-50 dark:bg-primary-900/30 flex items-center justify-center mx-auto mb-3">
                <PhotoIcon class="w-7 h-7 text-primary-500" />
              </div>
              <p class="text-sm font-medium text-gray-600 dark:text-gray-400">Нажмите, чтобы выбрать фото</p>
              <p class="text-xs text-gray-400 mt-1">или перетащите файлы сюда (JPEG/PNG, макс. 10 МБ каждый)</p>
            </div>
            <input
              ref="fileInput"
              type="file"
              accept="image/jpeg,image/png"
              multiple
              class="hidden"
              @change="handleFileInput"
            />

            <!-- Preview -->
            <div v-if="selectedFiles.length" class="mt-3 grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-3">
              <div v-for="(preview, i) in filePreviews" :key="i" class="relative group rounded-lg overflow-hidden border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/50">
                <img :src="preview.url" class="w-full h-20 object-cover" alt="" />
                <div class="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                  <button
                    type="button"
                    class="text-white bg-red-600 rounded-full w-7 h-7 flex items-center justify-center hover:bg-red-700 transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-red-400/60 focus-visible:ring-offset-2"
                    :aria-label="`Удалить ${preview.name}`"
                    @click="removeFile(i)"
                  >
                    <XMarkIcon class="w-4 h-4" />
                  </button>
                </div>
                <div class="px-1.5 py-0.5 text-[10px] text-gray-500 dark:text-gray-400 truncate">{{ preview.name }} ({{ preview.size }})</div>
              </div>
            </div>
            <p v-if="errors.photos" class="form-error">
              <ExclamationCircleIcon class="w-4 h-4 shrink-0" />
              {{ errors.photos }}
            </p>
          </div>
        </section>

        <div class="border-t border-gray-100 dark:border-gray-700/50 my-8"></div>

        <!-- ═══════ Шаг 3. Местоположение ═══════ -->
        <section>
          <div class="flex items-center gap-3 mb-5">
            <span class="w-8 h-8 rounded-full bg-primary-600 dark:bg-primary-500 text-white text-sm font-display font-bold flex items-center justify-center shrink-0 shadow-sm">3</span>
            <div>
              <h2 class="font-display text-lg font-semibold text-gray-900 dark:text-white leading-tight">Местоположение</h2>
              <p class="text-xs text-gray-500 dark:text-gray-400">Укажите точку на карте или адрес</p>
            </div>
          </div>

          <div class="sm:pl-11 space-y-6">
            <div>
              <label class="form-label">Карта</label>
              <p class="text-xs text-gray-400 mb-2">Кликните на карте, чтобы указать точное местоположение, или найдите адрес в поле поиска</p>
              <MapPicker v-model="coords" @address="onAddressUpdate" />
            </div>

            <!-- Manual address -->
            <div class="form-input-group">
              <label class="form-label">Адрес (вручную)</label>
              <div class="relative">
                <MapPinIcon class="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                <input v-model="address" type="text" class="form-input pl-10" placeholder="ул. Ленина, 15" maxlength="500" />
              </div>
            </div>
          </div>
        </section>

        <div v-if="error" class="mt-8 bg-red-50 dark:bg-red-900/30 text-red-600 dark:text-red-400 text-sm rounded-lg px-4 py-2.5 flex items-start gap-2">
          <ExclamationCircleIcon class="w-4 h-4 mt-0.5 shrink-0" />
          {{ error }}
        </div>

        <!-- Buttons -->
        <div class="flex flex-col sm:flex-row gap-3 pt-8 mt-8 border-t border-gray-100 dark:border-gray-700/50">
          <button type="submit" class="btn-accent btn-lg flex-1" :disabled="loading">
            <svg v-if="loading" class="animate-spin h-5 w-5" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" fill="none"/><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/></svg>
            <PlusCircleIcon v-else class="w-5 h-5" />
            {{ loading ? 'Создание...' : 'Создать заявку' }}
          </button>
          <router-link to="/dashboard" class="btn-secondary btn-lg">Отмена</router-link>
        </div>
      </form>
    </div>
  </div>
</template>
