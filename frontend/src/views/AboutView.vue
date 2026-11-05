<script setup lang="ts">
import { useAuthStore } from '@/stores/auth'
import { MapPinIcon, PhotoIcon, ArrowPathIcon, ChatBubbleLeftRightIcon, PlusCircleIcon } from '@heroicons/vue/24/outline'

const auth = useAuthStore()

const features = [
  { icon: MapPinIcon, title: 'Карта с координатами', desc: 'Выберите точное место на карте или найдите по адресу' },
  { icon: PhotoIcon, title: 'Загрузка файлов', desc: 'Прикрепите фото проблемы (JPEG/PNG, до 10 МБ)' },
  { icon: ArrowPathIcon, title: 'Отслеживание статуса', desc: 'Следите за выполнением заявки в реальном времени' },
  { icon: ChatBubbleLeftRightIcon, title: 'Связь с администрацией', desc: 'Общайтесь с администрацией по вашей заявке' },
]

const techStack = ['Vue 3', 'Tailwind CSS', 'Leaflet.js', 'FastAPI', 'PostgreSQL', 'Docker', 'OpenStreetMap', 'Heroicons']
</script>

<template>
  <div class="mx-auto max-w-4xl px-4 py-8 sm:px-8 sm:py-10">
    <header class="border-b-2 border-line pb-7 dark:border-line-dark">
      <p class="page-kicker">О сервисе</p>
      <h1 class="mt-2 font-display text-3xl font-semibold tracking-tight text-ink dark:text-ink-dark">Город, который слышит</h1>
      <p class="mt-2 max-w-2xl text-sm leading-6 text-ink-soft dark:text-ink-dark-soft">
        CityBoost — платформа для подачи и обработки городских заявок. Жители сообщают о проблемах, служба отвечает, статус виден на каждом этапе.
      </p>
    </header>

    <div class="mt-6 grid gap-5 lg:grid-cols-[1fr_280px]">
      <div class="space-y-5">
        <!-- Feature rows -->
        <section class="panel">
          <div class="border-b-2 border-line px-5 py-4 dark:border-line-dark">
            <h2 class="text-xs font-semibold text-ink-soft dark:text-ink-dark-soft">Возможности</h2>
          </div>
          <div
            v-for="(f, i) in features"
            :key="f.title"
            class="flex items-start gap-4 border-b-2 border-line px-5 py-4 last:border-b-0 dark:border-line-dark"
          >
            <span class="font-display text-sm font-semibold text-primary-600 dark:text-primary-400">0{{ i + 1 }}</span>
            <div class="flex-1">
              <p class="flex items-center gap-2 text-sm font-semibold text-ink dark:text-ink-dark">
                <component :is="f.icon" class="h-4 w-4 text-ink-soft dark:text-ink-dark-soft" />
                {{ f.title }}
              </p>
              <p class="mt-1 text-sm leading-6 text-ink-soft dark:text-ink-dark-soft">{{ f.desc }}</p>
            </div>
          </div>
        </section>

        <section v-if="auth.isAuthenticated" class="panel border-l-4 border-l-accent-500 p-5 sm:p-6">
          <p class="font-display text-lg font-semibold text-ink dark:text-ink-dark">Готовы сообщить о проблеме?</p>
          <p class="mt-1 text-sm text-ink-soft dark:text-ink-dark-soft">Заявка занимает несколько минут. Фото и точка на карте помогут службе.</p>
          <router-link to="/tickets/create" class="btn-accent mt-4">
            <PlusCircleIcon class="h-5 w-5" />
            Создать заявку
          </router-link>
        </section>
      </div>

      <aside class="space-y-5">
        <section class="bg-primary-900 p-5 text-white">
          <p class="text-xs font-semibold text-primary-200">Версия</p>
          <p class="mt-2 font-display text-4xl font-semibold">2.0 Beta</p>
          <p class="mt-2 text-sm leading-6 text-primary-100">Единый маршрут обращения: от заявки до ответа службы.</p>
        </section>

        <section class="panel p-5">
          <h2 class="text-xs font-semibold text-ink-soft dark:text-ink-dark-soft">Технологии</h2>
          <div class="mt-3 flex flex-wrap gap-1.5">
            <span
              v-for="tech in techStack"
              :key="tech"
              class="border border-line px-2 py-1 text-[11px] font-medium text-ink-soft dark:border-line-dark dark:text-ink-dark-soft"
            >
              {{ tech }}
            </span>
          </div>
        </section>
      </aside>
    </div>
  </div>
</template>
