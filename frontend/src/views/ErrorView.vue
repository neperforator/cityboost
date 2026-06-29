<script setup lang="ts">
import { useRouter, useRoute } from 'vue-router'
import { HomeIcon } from '@heroicons/vue/24/outline'
import { ArrowLeftOnRectangleIcon } from '@heroicons/vue/24/solid'

const router = useRouter()
const route = useRoute()

const errorMessage = (route.query?.message as string) || 'Произошла непредвиденная ошибка'
</script>

<template>
  <div class="min-h-[60vh] flex items-center justify-center px-4">
    <div class="text-center max-w-md">
      <div class="w-20 h-20 rounded-2xl bg-red-50 dark:bg-red-900/30 flex items-center justify-center mx-auto mb-6">
        <span class="text-4xl">!</span>
      </div>
      <h1 class="text-3xl font-bold text-gray-900 dark:text-white mb-2">Ошибка</h1>
      <p class="text-gray-500 dark:text-gray-400 mb-2">Что-то пошло не так</p>
      <p class="text-sm text-red-600 dark:text-red-400 mb-8 bg-red-50 dark:bg-red-900/20 rounded-lg px-4 py-3">
        {{ errorMessage }}
      </p>
      <div class="flex items-center justify-center gap-3">
        <button @click="router.push('/dashboard')" class="btn-primary">
          <HomeIcon class="w-5 h-5" />
          На главную
        </button>
        <button @click="router.push('/login')" class="btn-secondary">
          <ArrowLeftOnRectangleIcon class="w-4 h-4" />
          Войти
        </button>
      </div>
    </div>
  </div>
</template>
