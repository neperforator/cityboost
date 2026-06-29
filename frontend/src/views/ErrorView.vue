<script setup lang="ts">
import { useRouter, useRoute } from 'vue-router'

const router = useRouter()
const route = useRoute()

const errorMessage = (route.query?.message as string) || 'Произошла непредвиденная ошибка'
</script>

<template>
  <div class="min-h-[60vh] flex items-center justify-center px-4">
    <div class="text-center max-w-md">
      <div class="text-8xl mb-6">😵</div>
      <h1 class="text-4xl font-extrabold text-gray-900 dark:text-white mb-3">Ошибка</h1>
      <p class="text-lg text-gray-600 dark:text-gray-400 mb-2">Что-то пошло не так</p>
      <p class="text-sm text-red-500 dark:text-red-400 mb-8 bg-red-50 dark:bg-red-900/20 rounded-lg px-4 py-3">
        {{ errorMessage }}
      </p>
      <div class="flex items-center justify-center gap-3">
        <button @click="router.push('/dashboard')" class="btn-primary">
          🏠 На главную
        </button>
        <button @click="router.push('/login')" class="btn-secondary">
          🔑 Войти
        </button>
      </div>
    </div>
  </div>
</template>
