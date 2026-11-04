<script setup lang="ts">
import { useRouter } from 'vue-router'
import { HomeIcon } from '@heroicons/vue/24/outline'
import { ArrowLeftIcon } from '@heroicons/vue/24/solid'

const router = useRouter()
</script>

<template>
  <div class="flex min-h-[60vh] items-center justify-center px-4 py-10">
    <div class="w-full max-w-lg border-2 border-line bg-surface dark:border-line-dark dark:bg-surface-dark">
      <div class="border-b-2 border-line px-6 py-5 dark:border-line-dark">
        <p class="font-display text-5xl font-semibold text-ink-soft dark:text-ink-dark-soft">404</p>
        <h1 class="mt-2 font-display text-2xl font-semibold text-ink dark:text-ink-dark">Страница не найдена</h1>
      </div>
      <div class="p-6">
        <p class="text-sm leading-6 text-ink-soft dark:text-ink-dark-soft">
          Возможно, она была удалена или вы перешли по неверной ссылке.
        </p>
        <div class="mt-6 flex flex-wrap gap-2">
          <button @click="router.push('/dashboard')" class="btn-primary">
            <HomeIcon class="h-5 w-5" />
            На главную
          </button>
          <button @click="router.back()" class="btn-secondary">
            <ArrowLeftIcon class="h-4 w-4" />
            Назад
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
