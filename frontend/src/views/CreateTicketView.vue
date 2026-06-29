<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ticketAPI } from '@/api'
import { useToast } from '@/composables/useToast'
import MapPicker from '@/components/MapPicker.vue'
import { ArrowLeftIcon, PhotoIcon, XMarkIcon } from '@heroicons/vue/24/outline'
import { PlusCircleIcon } from '@heroicons/vue/24/solid'

const router = useRouter()
const toast = useToast()

const title = ref('')
const description = ref('')
const address = ref('')
const coords = ref({ lat: null, lng: null })
const loading = ref(false)
const error = ref('')

// --- Files ---
const selectedFiles = ref<File[]>([])
const fileError = ref('')
const fileInput = ref<HTMLInputElement | null>(null)
const MAX_FILES = 5
const ALLOWED_TYPES = ['image/jpeg', 'image/png']
const MAX_FILE_SIZE = 10 * 1024 * 1024 // 10 MB

const filePreviews = computed(() =>
  selectedFiles.value.map(f => ({
    name: f.name,
    size: (f.size / 1024 / 1024).toFixed(1) + ' MB',
    url: URL.createObjectURL(f),
  }))
)

function handleFileInput(e: Event) {
  fileError.value = ''
  const input = e.target as HTMLInputElement
  if (!input.files?.length) return

  const newFiles: File[] = []
  for (const file of Array.from(input.files)) {
    if (!ALLOWED_TYPES.includes(file.type)) {
      fileError.value = `Файл "${file.name}" недопустимого типа. Разрешены: JPEG, PNG`
      continue
    }
    if (file.size > MAX_FILE_SIZE) {
      fileError.value = `Файл "${file.name}" слишком большой (макс. 10 МБ)`
      continue
    }
    if (file.size === 0) {
      fileError.value = `Файл "${file.name}" пустой`
      continue
    }
    newFiles.push(file)
  }

  const total = selectedFiles.value.length + newFiles.length
  if (total > MAX_FILES) {
    fileError.value = `Максимум ${MAX_FILES} файлов за раз`
    return
  }

  selectedFiles.value = [...selectedFiles.value, ...newFiles]
  input.value = ''
}

function removeFile(index: number) {
  selectedFiles.value.splice(index, 1)
}

function onAddressUpdate(val: string) {
  address.value = val
}

async function submit() {
  if (!title.value.trim()) { error.value = 'Введите название заявки'; return }
  if (!description.value.trim()) { error.value = 'Введите описание заявки'; return }
  if (selectedFiles.value.length === 0) { error.value = 'Загрузите хотя бы одно фото'; return }

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
      <h1 class="text-2xl font-bold text-gray-900 dark:text-white tracking-tight mb-1">Создать заявку</h1>
      <p class="text-gray-500 dark:text-gray-400 text-sm mb-8">Опишите проблему, загрузите фото и укажите местоположение на карте</p>

      <form @submit.prevent="submit" class="space-y-6">
        <!-- Title -->
        <div class="form-input-group">
          <label class="form-label">Название <span class="text-red-500">*</span></label>
          <input v-model="title" type="text" class="form-input" placeholder="Кратко опишите проблему" required maxlength="255" />
        </div>

        <!-- Description -->
        <div class="form-input-group">
          <label class="form-label">Описание <span class="text-red-500">*</span></label>
          <textarea v-model="description" class="form-textarea" placeholder="Подробно опишите проблему..." required></textarea>
        </div>

        <!-- Photos -->
        <div>
          <label class="form-label">
            Фото <span class="text-red-500">*</span>
            <span class="text-xs text-gray-400 font-normal ml-1">(JPEG/PNG, от 1 до {{ MAX_FILES }} файлов, макс. 10 МБ каждый)</span>
          </label>
          <div
            class="border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-xl p-6 sm:p-8 text-center hover:border-primary-400 dark:hover:border-primary-500 transition-colors cursor-pointer"
            @click="fileInput?.click()"
          >
            <PhotoIcon class="mx-auto w-12 h-12 text-gray-400" />
            <p class="mt-3 text-sm font-medium text-gray-600 dark:text-gray-400">Нажмите, чтобы выбрать фото</p>
            <p class="text-xs text-gray-400 mt-1">или перетащите файлы сюда</p>
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
                <button type="button" class="text-white bg-red-600 rounded-full w-7 h-7 flex items-center justify-center hover:bg-red-700 transition-colors" @click="removeFile(i)">
                  <XMarkIcon class="w-4 h-4" />
                </button>
              </div>
              <div class="px-1.5 py-0.5 text-[10px] text-gray-500 dark:text-gray-400 truncate">{{ preview.name }} ({{ preview.size }})</div>
            </div>
          </div>
          <p v-if="fileError" class="mt-1.5 text-xs text-red-500">{{ fileError }}</p>
        </div>

        <!-- Map -->
        <div>
          <label class="form-label">Местоположение на карте</label>
          <p class="text-xs text-gray-400 mb-2">Кликните на карте, чтобы указать точное местоположение, или введите адрес в поле поиска</p>
          <MapPicker v-model="coords" @address="onAddressUpdate" />
        </div>

        <!-- Manual address -->
        <div class="form-input-group">
          <label class="form-label">Адрес (вручную)</label>
          <input v-model="address" type="text" class="form-input" placeholder="ул. Ленина, 15" maxlength="500" />
        </div>

        <div v-if="error" class="bg-red-50 dark:bg-red-900/30 text-red-600 dark:text-red-400 text-sm rounded-lg px-4 py-2.5">
          {{ error }}
        </div>

        <!-- Buttons -->
        <div class="flex flex-col sm:flex-row gap-3 pt-2">
          <button type="submit" class="btn-primary btn-lg flex-1" :disabled="loading">
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
