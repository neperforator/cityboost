<script setup lang="ts">
withDefaults(defineProps<{
  rows?: number
  columns?: number
}>(), { rows: 5, columns: 4 })
</script>

<template>
  <div class="overflow-hidden rounded-xl border border-gray-200 dark:border-gray-700 animate-pulse">
    <table class="w-full">
      <thead class="bg-gray-50 dark:bg-gray-800/50">
        <tr>
          <th v-for="c in columns" :key="c" class="px-4 py-3">
            <div class="h-3 skeleton w-16" />
          </th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="r in rows" :key="r" class="border-t border-gray-100 dark:border-gray-700">
          <td v-for="c in columns" :key="c" class="px-4 py-4">
            <div class="h-3 skeleton" :style="{ width: (40 + (c * r * 13) % 40) + '%' }" />
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>
