<script setup lang="ts">
import { useRouter } from 'vue-router'
import { HomeIcon } from '@heroicons/vue/24/outline'
import { ArrowLeftIcon } from '@heroicons/vue/24/solid'

const router = useRouter()
</script>

<template>
  <div class="min-h-[60vh] flex items-center justify-center px-4">
    <div class="text-center max-w-md">
      <div class="w-20 h-20 rounded-2xl bg-gray-100 dark:bg-gray-800 flex items-center justify-center mx-auto mb-6">
        <span class="text-4xl font-bold text-gray-300 dark:text-gray-600">404</span>
      </div>
      <h1 class="text-3xl font-bold text-gray-900 dark:text-white mb-2">Страница не найдена</h1>
      <p class="text-gray-500 dark:text-gray-400 mb-8">
        Возможно, она была удалена или вы перешли по неверной ссылке
      </p>
      <div class="flex items-center justify-center gap-3">
        <button @click="router.push('/dashboard')" class="btn-primary">
          <HomeIcon class="w-5 h-5" />
          На главную
        </button>
        <button @click="router.back()" class="btn-secondary">
          <ArrowLeftIcon class="w-4 h-4" />
          Назад
        </button>
      </div>
    </div>
  </div>
</template>
