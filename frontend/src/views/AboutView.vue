<script setup lang="ts">
import { useAuthStore } from '@/stores/auth'
const auth = useAuthStore()
</script>

<template>
  <div class="max-w-3xl mx-auto px-4 sm:px-6 py-8">
    <h1 class="text-2xl font-extrabold text-gray-900 dark:text-white mb-6">ℹ️ О проекте</h1>

    <div class="space-y-6">
      <div class="card p-6">
        <div class="flex items-center gap-3 mb-4">
          <span class="text-3xl">🏙️</span>
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

      <div class="card p-6">
        <h3 class="font-semibold text-gray-900 dark:text-white mb-3">🛠️ Возможности</h3>
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div class="flex items-start gap-3">
            <span class="text-lg mt-0.5">📍</span>
            <div>
              <p class="text-sm font-medium text-gray-900 dark:text-white">Карта с координатами</p>
              <p class="text-xs text-gray-500">Выберите точное место на карте или найдите по адресу</p>
            </div>
          </div>
          <div class="flex items-start gap-3">
            <span class="text-lg mt-0.5">📎</span>
            <div>
              <p class="text-sm font-medium text-gray-900 dark:text-white">Загрузка файлов</p>
              <p class="text-xs text-gray-500">Прикрепите фото проблемы (JPEG/PNG, до 5 МБ)</p>
            </div>
          </div>
          <div class="flex items-start gap-3">
            <span class="text-lg mt-0.5">🔄</span>
            <div>
              <p class="text-sm font-medium text-gray-900 dark:text-white">Отслеживание статуса</p>
              <p class="text-xs text-gray-500">Следите за выполнением заявки в реальном времени</p>
            </div>
          </div>
          <div class="flex items-start gap-3">
            <span class="text-lg mt-0.5">💬</span>
            <div>
              <p class="text-sm font-medium text-gray-900 dark:text-white">Комментарии</p>
              <p class="text-xs text-gray-500">Общайтесь с администрацией по вашей заявке</p>
            </div>
          </div>
        </div>
      </div>

      <div v-if="auth.isAuthenticated" class="card p-6 text-center">
        <p class="text-gray-500 dark:text-gray-400 mb-4">Готовы сообщить о проблеме?</p>
        <router-link to="/tickets/create" class="btn-primary">📝 Создать заявку</router-link>
      </div>

      <div class="card p-6">
        <h3 class="font-semibold text-gray-900 dark:text-white mb-3">📊 Технологии</h3>
        <div class="flex flex-wrap gap-2">
          <span class="px-3 py-1.5 bg-gray-100 dark:bg-gray-700 rounded-lg text-xs font-medium">Vue 3</span>
          <span class="px-3 py-1.5 bg-gray-100 dark:bg-gray-700 rounded-lg text-xs font-medium">Tailwind CSS</span>
          <span class="px-3 py-1.5 bg-gray-100 dark:bg-gray-700 rounded-lg text-xs font-medium">Leaflet.js</span>
          <span class="px-3 py-1.5 bg-gray-100 dark:bg-gray-700 rounded-lg text-xs font-medium">FastAPI</span>
          <span class="px-3 py-1.5 bg-gray-100 dark:bg-gray-700 rounded-lg text-xs font-medium">PostgreSQL</span>
          <span class="px-3 py-1.5 bg-gray-100 dark:bg-gray-700 rounded-lg text-xs font-medium">Docker</span>
          <span class="px-3 py-1.5 bg-gray-100 dark:bg-gray-700 rounded-lg text-xs font-medium">OpenStreetMap</span>
        </div>
      </div>
    </div>
  </div>
</template>
