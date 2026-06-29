<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { ticketAPI } from '@/api'
import { useToast } from '@/composables/useToast'
import MapPicker from '@/components/MapPicker.vue'

const router = useRouter()
const toast = useToast()

const title = ref('')
const description = ref('')
const address = ref('')
const coords = ref({ lat: null, lng: null })
const loading = ref(false)
const error = ref('')

function onAddressUpdate(val) {
  address.value = val
}

async function submit() {
  if (!title.value.trim()) { error.value = 'Введите название заявки'; return }
  if (!description.value.trim()) { error.value = 'Введите описание заявки'; return }

  loading.value = true
  error.value = ''
  try {
    const data = {
      title: title.value.trim(),
      description: description.value.trim(),
      address: address.value.trim() || null,
      latitude: coords.value.lat ? parseFloat(coords.value.lat) : null,
      longitude: coords.value.lng ? parseFloat(coords.value.lng) : null,
    }
    const ticket = await ticketAPI.create(data)
    toast.success('Заявка создана!')
    router.push(`/tickets/${ticket.id}`)
  } catch (err) {
    error.value = err.message
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="max-w-4xl mx-auto px-4 sm:px-6 py-8">
    <div class="mb-6">
      <router-link to="/dashboard" class="text-sm text-primary-600 dark:text-primary-400 hover:underline flex items-center gap-1">
        ← Назад к заявкам
      </router-link>
    </div>

    <div class="card p-6 sm:p-8">
      <h1 class="text-2xl font-extrabold text-gray-900 dark:text-white mb-1">Создать заявку</h1>
      <p class="text-gray-500 dark:text-gray-400 text-sm mb-8">Опишите проблему и укажите её местоположение на карте</p>

      <form @submit.prevent="submit" class="space-y-6">
        <!-- Title -->
        <div>
          <label class="form-label">Название *</label>
          <input v-model="title" type="text" class="form-input" placeholder="Кратко опишите проблему" required maxlength="255" />
        </div>

        <!-- Description -->
        <div>
          <label class="form-label">Описание *</label>
          <textarea v-model="description" class="form-textarea" placeholder="Подробно опишите проблему..." required></textarea>
        </div>

        <!-- Map -->
        <div>
          <label class="form-label">📍 Местоположение на карте</label>
          <p class="text-xs text-gray-400 mb-2">Кликните на карте, чтобы указать точное местоположение, или введите адрес в поле поиска</p>
          <MapPicker v-model="coords" @address="onAddressUpdate" />
        </div>

        <!-- Manual address -->
        <div>
          <label class="form-label">Адрес (вручную)</label>
          <input v-model="address" type="text" class="form-input" placeholder="ул. Ленина, 15" maxlength="500" />
        </div>

        <div v-if="error" class="bg-red-50 dark:bg-red-900/30 text-red-600 dark:text-red-400 text-sm rounded-lg px-4 py-2.5">
          {{ error }}
        </div>

        <!-- Buttons -->
        <div class="flex gap-3 pt-2">
          <button type="submit" class="btn-primary btn-lg flex-1" :disabled="loading">
            <svg v-if="loading" class="animate-spin h-5 w-5" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" fill="none"/><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/></svg>
            {{ loading ? 'Создание...' : '📝 Создать заявку' }}
          </button>
          <router-link to="/dashboard" class="btn-secondary btn-lg">Отмена</router-link>
        </div>
      </form>
    </div>
  </div>
</template>
