<script setup lang="ts">
import { useRouter, useRoute } from 'vue-router'
import { HomeIcon } from '@heroicons/vue/24/outline'
import { ArrowLeftOnRectangleIcon } from '@heroicons/vue/24/solid'

const router = useRouter()
const route = useRoute()

const errorMessage = (route.query?.message as string) || 'Произошла непредвиденная ошибка'
</script>

<template>
  <div class="flex min-h-[60vh] items-center justify-center px-4 py-10">
    <div class="w-full max-w-lg border-2 border-line bg-surface dark:border-line-dark dark:bg-surface-dark">
      <div class="border-b-2 border-line bg-red-50 px-6 py-5 dark:border-line-dark dark:bg-red-900/20">
        <p class="font-display text-5xl font-semibold text-red-600 dark:text-red-400">!</p>
        <h1 class="mt-2 font-display text-2xl font-semibold text-ink dark:text-ink-dark">Ошибка</h1>
      </div>
      <div class="p-6">
        <p class="text-sm text-ink-soft dark:text-ink-dark-soft">Что-то пошло не так</p>
        <p class="mt-3 border-l-4 border-l-red-500 bg-surface-muted px-3 py-2 text-sm text-red-700 dark:bg-surface-dark-muted dark:text-red-300">
          {{ errorMessage }}
        </p>
        <div class="mt-6 flex flex-wrap gap-2">
          <button @click="router.push('/dashboard')" class="btn-primary">
            <HomeIcon class="h-5 w-5" />
            На главную
          </button>
          <button @click="router.push('/login')" class="btn-secondary">
            <ArrowLeftOnRectangleIcon class="h-4 w-4" />
            Войти
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
