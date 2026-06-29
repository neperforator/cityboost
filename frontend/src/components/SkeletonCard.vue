<script setup lang="ts">
withDefaults(defineProps<{
  count?: number
}>(), { count: 3 })
</script>

<template>
  <div class="space-y-4">
    <div
      v-for="i in count"
      :key="i"
      class="card p-5 animate-pulse"
    >
      <div class="flex items-start justify-between">
        <div class="flex-1 space-y-3">
          <div class="h-4 skeleton w-3/4" />
          <div class="h-3 skeleton w-1/2" />
        </div>
        <div class="h-6 w-20 skeleton rounded-full ml-4 shrink-0" />
      </div>
      <div class="mt-4 flex items-center gap-4">
        <div class="h-3 skeleton w-24" />
        <div class="h-3 skeleton w-20" />
      </div>
    </div>
  </div>
</template>
