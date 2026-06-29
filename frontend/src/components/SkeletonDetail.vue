<script setup lang="ts">
</script>

<template>
  <div class="max-w-3xl mx-auto animate-pulse">
    <!-- Back button -->
    <div class="h-4 skeleton w-24 mb-6" />

    <!-- Title area -->
    <div class="card p-6 mb-6 space-y-4">
      <div class="flex justify-between">
        <div class="space-y-3 flex-1">
          <div class="h-7 skeleton w-3/4" />
          <div class="h-4 skeleton w-1/3" />
        </div>
        <div class="h-7 w-24 skeleton rounded-full shrink-0 ml-4" />
      </div>
      <div class="h-4 skeleton w-1/4 mt-4" />
      <div class="space-y-2">
        <div class="h-3 skeleton w-full" />
        <div class="h-3 skeleton w-full" />
        <div class="h-3 skeleton w-2/3" />
      </div>
    </div>

    <!-- Comments skeleton -->
    <div class="card p-6">
      <div class="h-5 skeleton w-32 mb-4" />
      <div v-for="i in 2" :key="i" class="flex gap-3 p-4 bg-gray-50 dark:bg-gray-800/50 rounded-lg mb-3">
        <div class="w-9 h-9 skeleton rounded-full shrink-0" />
        <div class="flex-1 space-y-2">
          <div class="h-3 skeleton w-32" />
          <div class="h-3 skeleton w-full" />
          <div class="h-3 skeleton w-4/5" />
        </div>
      </div>
    </div>
  </div>
</template>
