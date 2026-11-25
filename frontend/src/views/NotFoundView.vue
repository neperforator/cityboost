<script setup lang="ts">
import { useRouter } from 'vue-router'
import { HomeIcon } from '@heroicons/vue/24/outline'
import { ArrowLeftIcon } from '@heroicons/vue/24/solid'

const router = useRouter()

const goHome = () => router.push('/')
const goBack = () => {
  if (window.history.length > 1) router.back()
  else goHome()
}
</script>

<template>
  <div class="mx-auto max-w-4xl px-4 py-10 sm:px-8 sm:py-16">
    <div class="panel overflow-hidden sm:grid sm:grid-cols-[minmax(0,1fr)_260px]">
      <div class="px-6 py-8 sm:px-8 sm:py-10">
        <p class="page-kicker">Городская служба заявок</p>
        <h1 class="mt-2 font-display text-2xl font-semibold leading-tight tracking-tight text-ink dark:text-ink-dark sm:text-3xl">
          Страница не найдена
        </h1>
        <p class="mt-3 max-w-md text-sm leading-6 text-ink-soft dark:text-ink-dark-soft">
          Возможно, она была удалена или вы перешли по неверной ссылке.
          Проверьте адрес — или вернитесь на главную.
        </p>

        <div class="mt-8 flex flex-col gap-2 sm:flex-row">
          <button class="btn-accent" @click="goHome">
            <HomeIcon class="h-5 w-5" />
            На главную
          </button>
          <button class="btn-secondary" @click="goBack">
            <ArrowLeftIcon class="h-4 w-4" />
            Вернуться назад
          </button>
        </div>
      </div>

      <aside class="flex items-center justify-between gap-4 bg-primary-900 px-6 py-5 text-white sm:flex-col sm:items-start sm:justify-center sm:px-7 sm:py-8">
        <p class="font-display text-4xl font-bold leading-none tracking-tighter text-white sm:text-6xl">
          404
        </p>
        <div class="text-right sm:mt-5 sm:text-left">
          <p class="font-display text-sm font-semibold text-white">Маршрут не найден</p>
          <p class="mt-1 max-w-[15rem] text-xs leading-5 text-primary-200">
            У этого адреса нет маршрута в CityBoost.
          </p>
        </div>
      </aside>
    </div>
  </div>
</template>
