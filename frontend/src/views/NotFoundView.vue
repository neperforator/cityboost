<script setup lang="ts">
import { useRouter } from 'vue-router'

const router = useRouter()
</script>

<template>
  <div class="min-h-[60vh] flex items-center justify-center px-4">
    <div class="text-center max-w-md">
      <div class="text-8xl mb-6">🤷</div>
      <h1 class="text-4xl font-extrabold text-gray-900 dark:text-white mb-3">404</h1>
      <p class="text-xl text-gray-600 dark:text-gray-400 mb-2">Страница не найдена</p>
      <p class="text-sm text-gray-500 dark:text-gray-500 mb-8">
        Возможно, она была удалена или вы перешли по неверной ссылке
      </p>
      <div class="flex items-center justify-center gap-3">
        <button @click="router.push('/dashboard')" class="btn-primary">
          🏠 На главную
        </button>
        <button @click="router.back()" class="btn-secondary">
          ← Назад
        </button>
      </div>
    </div>
  </div>
</template>
