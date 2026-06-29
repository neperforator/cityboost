<script setup lang="ts">
defineProps<{
  rows?: number
  columns?: number
}>()
</script>

<template>
  <div class="overflow-hidden rounded-xl border border-gray-200 dark:border-gray-700">
    <table class="w-full">
      <thead class="bg-gray-50 dark:bg-gray-800/50">
        <tr>
          <th
            v-for="c in columns ?? 4"
            :key="c"
            class="px-4 py-3"
          >
            <div class="h-3 bg-gray-200 dark:bg-gray-700 rounded w-16 animate-pulse" />
          </th>
        </tr>
      </thead>
      <tbody>
        <tr
          v-for="r in rows ?? 5"
          :key="r"
          class="border-t border-gray-100 dark:border-gray-700"
        >
          <td
            v-for="c in columns ?? 4"
            :key="c"
            class="px-4 py-4"
          >
            <div
              class="h-3 bg-gray-200 dark:bg-gray-700 rounded animate-pulse"
              :style="{ width: (40 + Math.random() * 40) + '%' }"
            />
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>
