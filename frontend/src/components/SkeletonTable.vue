<script setup lang="ts">
withDefaults(defineProps<{
  rows?: number
  columns?: number
}>(), { rows: 5, columns: 4 })
</script>

<template>
  <div class="overflow-hidden">
    <table class="w-full">
      <thead class="border-b-2 border-line dark:border-line-dark">
        <tr>
          <th v-for="c in columns" :key="c" class="px-4 py-3">
            <div class="skeleton h-3 w-16" />
          </th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="r in rows" :key="r" class="border-b border-line last:border-b-0 dark:border-line-dark">
          <td v-for="c in columns" :key="c" class="px-4 py-4">
            <div class="skeleton h-3" :style="{ width: (40 + (c * r * 13) % 40) + '%' }" />
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>
