<script setup lang="ts">
import { TicketIcon } from '@heroicons/vue/24/solid'
</script>

<template>
  <footer class="bg-white dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700/60 text-sm py-6 mt-auto">
    <div class="max-w-7xl mx-auto px-4 sm:px-6">
      <div class="flex flex-col sm:flex-row items-center justify-between gap-3">
        <div class="flex items-center gap-2 text-gray-500 dark:text-gray-400">
          <div class="w-6 h-6 rounded-md bg-gradient-to-br from-primary-500 to-primary-700 flex items-center justify-center shadow-sm">
            <TicketIcon class="w-3.5 h-3.5 text-white" />
          </div>
          <span class="font-medium">CityBoost</span>
          <span class="text-gray-300 dark:text-gray-600">·</span>
          <span class="text-gray-400 dark:text-gray-500">Система городских заявок</span>
        </div>
        <p class="text-gray-400 dark:text-gray-500 text-xs">© {{ new Date().getFullYear() }} CityBoost.</p>
      </div>
    </div>
  </footer>
</template>
