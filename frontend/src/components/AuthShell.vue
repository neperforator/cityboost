<script setup lang="ts">
defineProps<{
  title: string
  subtitle?: string
}>()

const stops = [
  { label: 'Заявка', text: 'Опишите проблему' },
  { label: 'Фото', text: 'Приложите доказательства' },
  { label: 'Карта', text: 'Укажите точный адрес' },
  { label: 'Ответ', text: 'Следите за статусом' },
]
</script>

<template>
  <div class="min-h-screen bg-canvas dark:bg-canvas-dark lg:grid lg:grid-cols-[1fr_420px]">
    <main class="flex min-h-screen flex-col px-5 py-6 sm:px-10 lg:px-16">
      <router-link to="/" class="inline-flex items-center gap-2 text-sm font-semibold text-ink dark:text-ink-dark">
        <span class="flex h-7 w-7 items-center justify-center rounded-sm bg-primary-500 text-[10px] font-bold text-white">CB</span>
        CityBoost
      </router-link>

      <div class="flex flex-1 items-center">
        <div class="w-full max-w-md py-10">
          <p class="page-kicker">Городская служба заявок</p>
          <h1 class="mt-2 font-display text-3xl font-semibold leading-tight tracking-tight text-ink dark:text-ink-dark">
            {{ title }}
          </h1>
          <p v-if="subtitle" class="mt-3 text-sm leading-6 text-ink-soft dark:text-ink-dark-soft">
            {{ subtitle }}
          </p>
          <div class="mt-8">
            <slot />
          </div>
        </div>
      </div>

      <p class="text-xs text-ink-soft dark:text-ink-dark-soft">© {{ new Date().getFullYear() }} CityBoost</p>
    </main>

    <aside class="hidden flex-col justify-between bg-primary-900 p-10 text-white lg:flex">
      <p class="text-xs font-semibold text-primary-200">Как проходит заявка</p>

      <div class="my-10">
        <div class="relative pl-8">
          <span class="absolute bottom-3 left-[7px] top-3 w-0.5 bg-primary-600" />
          <div v-for="(stop, i) in stops" :key="stop.label" class="relative pb-8 last:pb-0">
            <span
              class="absolute -left-8 top-0.5 flex h-4 w-4 items-center justify-center rounded-full border-2"
              :class="i === 0 ? 'border-accent-500 bg-accent-500' : 'border-primary-200 bg-primary-900'"
            />
            <p class="font-display text-sm font-semibold text-white">{{ stop.label }}</p>
            <p class="mt-0.5 text-sm text-primary-200">{{ stop.text }}</p>
          </div>
        </div>
      </div>

      <p class="max-w-xs text-sm leading-6 text-primary-100">
        Одна заявка — один маршрут. Вы всегда видите, на каком этапе находится обращение.
      </p>
    </aside>
  </div>
</template>
