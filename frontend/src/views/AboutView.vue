<script setup lang="ts">
import { useAuthStore } from '@/stores/auth'
import { TicketIcon } from '@heroicons/vue/24/solid'
import { MapPinIcon, PhotoIcon, ArrowPathIcon, ChatBubbleLeftRightIcon, PlusCircleIcon } from '@heroicons/vue/24/outline'

const auth = useAuthStore()

const features = [
  { icon: MapPinIcon, title: 'Карта с координатами', desc: 'Выберите точное место на карте или найдите по адресу' },
  { icon: PhotoIcon, title: 'Загрузка файлов', desc: 'Прикрепите фото проблемы (JPEG/PNG, до 10 МБ)' },
  { icon: ArrowPathIcon, title: 'Отслеживание статуса', desc: 'Следите за выполнением заявки в реальном времени' },
  { icon: ChatBubbleLeftRightIcon, title: 'Комментарии', desc: 'Общайтесь с администрацией по вашей заявке' },
]

const techStack = ['Vue 3', 'Tailwind CSS', 'Leaflet.js', 'FastAPI', 'PostgreSQL', 'Docker', 'OpenStreetMap', 'Heroicons']
</script>

<template>
  <div class="max-w-3xl mx-auto px-4 sm:px-6 py-8">
    <div class="page-header">
      <h1 class="page-title">О проекте</h1>
      <p class="page-subtitle">CityBoost — система городских заявок</p>
    </div>

    <div class="space-y-6">
      <!-- Main info -->
      <div class="card p-6 sm:p-8">
        <div class="flex items-center gap-4 mb-5">
          <div class="w-12 h-12 rounded-2xl bg-primary-100 dark:bg-primary-900/40 flex items-center justify-center">
            <TicketIcon class="w-6 h-6 text-primary-600 dark:text-primary-400" />
          </div>
          <div>
            <h2 class="text-xl font-bold text-gray-900 dark:text-white">CityBoost</h2>
            <p class="text-sm text-gray-500 dark:text-gray-400">Система городских заявок v2.0</p>
          </div>
        </div>
        <p class="text-gray-700 dark:text-gray-300 leading-relaxed">
          CityBoost — это современная платформа для подачи и обработки городских заявок.
          Жители могут сообщать о проблемах в городе (ямы на дорогах, сломанные фонари, мусор и т.д.),
          указывать точное местоположение на карте и отслеживать статус выполнения.
        </p>
      </div>

      <!-- Features -->
      <div class="card p-6 sm:p-8">
        <h3 class="font-semibold text-gray-900 dark:text-white mb-5">Возможности</h3>
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-5">
          <div v-for="f in features" :key="f.title" class="flex items-start gap-3">
            <div class="w-9 h-9 rounded-xl bg-primary-50 dark:bg-primary-900/30 flex items-center justify-center shrink-0 mt-0.5">
              <component :is="f.icon" class="w-5 h-5 text-primary-600 dark:text-primary-400" />
            </div>
            <div>
              <p class="text-sm font-medium text-gray-900 dark:text-white">{{ f.title }}</p>
              <p class="text-xs text-gray-500 dark:text-gray-400 mt-0.5">{{ f.desc }}</p>
            </div>
          </div>
        </div>
      </div>

      <!-- CTA -->
      <div v-if="auth.isAuthenticated" class="card p-6 text-center">
        <p class="text-gray-500 dark:text-gray-400 mb-4">Готовы сообщить о проблеме?</p>
        <router-link to="/tickets/create" class="btn-accent">
          <PlusCircleIcon class="w-5 h-5" />
          Создать заявку
        </router-link>
      </div>

      <!-- Tech stack -->
      <div class="card p-6 sm:p-8">
        <h3 class="font-semibold text-gray-900 dark:text-white mb-4">Технологии</h3>
        <div class="flex flex-wrap gap-2">
          <span
            v-for="tech in techStack"
            :key="tech"
            class="px-3 py-1.5 bg-gray-100 dark:bg-gray-700 rounded-lg text-xs font-medium text-gray-600 dark:text-gray-300"
          >
            {{ tech }}
          </span>
        </div>
      </div>
    </div>
  </div>
</template>
