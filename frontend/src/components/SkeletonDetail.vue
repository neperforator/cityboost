<script setup lang="ts">
</script>

<template>
  <div class="max-w-3xl mx-auto animate-pulse">
    <!-- Back button -->
    <div class="h-4 bg-gray-200 dark:bg-gray-700 rounded w-24 mb-6" />

    <!-- Title -->
    <div class="h-8 bg-gray-200 dark:bg-gray-700 rounded w-3/4 mb-4" />
    <div class="h-4 bg-gray-200 dark:bg-gray-700 rounded w-1/3 mb-8" />

    <!-- Status badges row -->
    <div class="flex gap-3 mb-8">
      <div class="h-7 w-24 bg-gray-200 dark:bg-gray-700 rounded-full" />
      <div class="h-7 w-20 bg-gray-200 dark:bg-gray-700 rounded-full" />
    </div>

    <!-- Content card -->
    <div class="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6 space-y-4">
      <div class="h-4 bg-gray-200 dark:bg-gray-700 rounded w-1/4" />
      <div class="h-3 bg-gray-200 dark:bg-gray-700 rounded w-full" />
      <div class="h-3 bg-gray-200 dark:bg-gray-700 rounded w-full" />
      <div class="h-3 bg-gray-200 dark:bg-gray-700 rounded w-2/3" />

      <div class="border-t border-gray-100 dark:border-gray-700 pt-4 mt-4">
        <div class="h-4 bg-gray-200 dark:bg-gray-700 rounded w-1/4 mb-4" />
        <div class="grid grid-cols-2 gap-4">
          <div v-for="i in 4" :key="i">
            <div class="h-3 bg-gray-200 dark:bg-gray-700 rounded w-16 mb-1" />
            <div class="h-4 bg-gray-200 dark:bg-gray-700 rounded w-32" />
          </div>
        </div>
      </div>
    </div>

    <!-- Comments section -->
    <div class="mt-8">
      <div class="h-5 bg-gray-200 dark:bg-gray-700 rounded w-32 mb-4" />
      <div v-for="i in 2" :key="i" class="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-4 mb-3">
        <div class="flex items-center gap-2 mb-2">
          <div class="h-3 bg-gray-200 dark:bg-gray-700 rounded w-20" />
          <div class="h-3 bg-gray-200 dark:bg-gray-700 rounded w-16" />
        </div>
        <div class="h-3 bg-gray-200 dark:bg-gray-700 rounded w-full" />
        <div class="h-3 bg-gray-200 dark:bg-gray-700 rounded w-4/5 mt-1" />
      </div>
    </div>
  </div>
</template>
