<script setup lang="ts">
withDefaults(defineProps<{
  count?: number
}>(), { count: 3 })
</script>

<template>
  <div class="space-y-3">
    <div v-for="i in count" :key="i" class="panel p-5">
      <div class="flex items-start justify-between gap-4">
        <div class="flex-1 space-y-3">
          <div class="skeleton h-4 w-3/4" />
          <div class="skeleton h-3 w-1/2" />
        </div>
        <div class="skeleton h-6 w-20 shrink-0" />
      </div>
      <div class="mt-4 flex items-center gap-4">
        <div class="skeleton h-3 w-24" />
        <div class="skeleton h-3 w-20" />
      </div>
    </div>
  </div>
</template>
