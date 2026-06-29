<script setup lang="ts">
import { ChevronLeftIcon, ChevronRightIcon } from '@heroicons/vue/24/solid'

defineProps<{
  page: number
  totalPages: number
  total: number
}>()

const emit = defineEmits<{
  (e: 'change', page: number): void
}>()

function range(start: number, end: number): number[] {
  return Array.from({ length: end - start + 1 }, (_, i) => start + i)
}

function getVisiblePages(current: number, total: number): (number | 'ellipsis')[] {
  if (total <= 7) return range(1, total)

  const pages: (number | 'ellipsis')[] = []
  pages.push(1)

  if (current > 3) pages.push('ellipsis')

  const start = Math.max(2, current - 1)
  const end = Math.min(total - 1, current + 1)

  for (let i = start; i <= end; i++) {
    pages.push(i)
  }

  if (current < total - 2) pages.push('ellipsis')

  pages.push(total)
  return pages
}
</script>

<template>
  <div
    v-if="totalPages > 1"
    class="flex flex-wrap items-center justify-between gap-3 mt-5 pt-4 border-t border-gray-200 dark:border-gray-700"
  >
    <span class="text-sm text-gray-500 dark:text-gray-400">
      {{ total }} {{ total === 1 ? 'запись' : total % 10 === 1 && total % 100 !== 11 ? 'запись' : total % 10 >= 2 && total % 10 <= 4 && (total % 100 < 10 || total % 100 >= 20) ? 'записи' : 'записей' }}
    </span>

    <div class="flex items-center gap-1">
      <!-- Prev -->
      <button
        :disabled="page <= 1"
        class="inline-flex items-center justify-center w-9 h-9 rounded-lg text-sm transition-all disabled:opacity-30 disabled:cursor-not-allowed hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-600 dark:text-gray-300"
        @click="emit('change', page - 1)"
      >
        <ChevronLeftIcon class="w-4 h-4" />
      </button>

      <!-- Pages -->
      <template v-for="(p, i) in getVisiblePages(page, totalPages)" :key="i">
        <span v-if="p === 'ellipsis'" class="px-1.5 text-gray-400 text-sm select-none">…</span>
        <button
          v-else
          class="min-w-[36px] h-9 rounded-lg text-sm font-medium transition-all"
          :class="p === page
            ? 'bg-primary-600 text-white shadow-sm cursor-default'
            : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700'"
          @click="emit('change', p)"
        >
          {{ p }}
        </button>
      </template>

      <!-- Next -->
      <button
        :disabled="page >= totalPages"
        class="inline-flex items-center justify-center w-9 h-9 rounded-lg text-sm transition-all disabled:opacity-30 disabled:cursor-not-allowed hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-600 dark:text-gray-300"
        @click="emit('change', page + 1)"
      >
        <ChevronRightIcon class="w-4 h-4" />
      </button>
    </div>
  </div>
</template>
