<script setup lang="ts">
defineProps<{
  count?: number
}>()
</script>

<template>
  <div class="space-y-4">
    <div
      v-for="i in count ?? 3"
      :key="i"
      class="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-5 animate-pulse"
    >
      <div class="flex items-start justify-between">
        <div class="flex-1 space-y-3">
          <div class="h-4 bg-gray-200 dark:bg-gray-700 rounded w-3/4" />
          <div class="h-3 bg-gray-200 dark:bg-gray-700 rounded w-1/2" />
          <div class="h-3 bg-gray-200 dark:bg-gray-700 rounded w-full" />
        </div>
        <div class="h-6 w-20 bg-gray-200 dark:bg-gray-700 rounded-full ml-4" />
      </div>
      <div class="mt-4 flex items-center gap-4">
        <div class="h-3 bg-gray-200 dark:bg-gray-700 rounded w-24" />
        <div class="h-3 bg-gray-200 dark:bg-gray-700 rounded w-20" />
      </div>
    </div>
  </div>
</template>
