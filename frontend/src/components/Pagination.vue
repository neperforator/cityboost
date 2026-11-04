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
  for (let i = start; i <= end; i++) pages.push(i)

  if (current < total - 2) pages.push('ellipsis')
  pages.push(total)
  return pages
}
</script>

<template>
  <div
    v-if="totalPages > 1"
    class="mt-5 flex flex-wrap items-center justify-between gap-3 border-t-2 border-line pt-4 dark:border-line-dark"
  >
    <span class="text-sm text-ink-soft dark:text-ink-dark-soft">
      {{ total }} {{ total === 1 ? 'запись' : total % 10 === 1 && total % 100 !== 11 ? 'запись' : total % 10 >= 2 && total % 10 <= 4 && (total % 100 < 10 || total % 100 >= 20) ? 'записи' : 'записей' }}
    </span>

    <div class="flex items-center gap-1">
      <button
        :disabled="page <= 1"
        class="inline-flex h-9 w-9 items-center justify-center rounded-sm border-2 border-line text-sm text-ink-soft transition-colors hover:border-primary-400 hover:text-primary-700 disabled:pointer-events-none disabled:opacity-30 dark:border-line-dark dark:text-ink-dark-soft dark:hover:border-primary-400 dark:hover:text-primary-200"
        aria-label="Предыдущая страница"
        @click="emit('change', page - 1)"
      >
        <ChevronLeftIcon class="h-4 w-4" />
      </button>

      <template v-for="(p, i) in getVisiblePages(page, totalPages)" :key="i">
        <span v-if="p === 'ellipsis'" class="select-none px-1.5 text-sm text-ink-soft dark:text-ink-dark-soft">…</span>
        <button
          v-else
          class="h-9 min-w-[36px] rounded-sm border-2 text-sm font-semibold transition-colors"
          :class="p === page
            ? 'border-primary-500 bg-primary-500 text-white'
            : 'border-line text-ink-soft hover:border-primary-400 hover:text-primary-700 dark:border-line-dark dark:text-ink-dark-soft dark:hover:border-primary-400 dark:hover:text-primary-200'"
          @click="emit('change', p)"
        >
          {{ p }}
        </button>
      </template>

      <button
        :disabled="page >= totalPages"
        class="inline-flex h-9 w-9 items-center justify-center rounded-sm border-2 border-line text-sm text-ink-soft transition-colors hover:border-primary-400 hover:text-primary-700 disabled:pointer-events-none disabled:opacity-30 dark:border-line-dark dark:text-ink-dark-soft dark:hover:border-primary-400 dark:hover:text-primary-200"
        aria-label="Следующая страница"
        @click="emit('change', page + 1)"
      >
        <ChevronRightIcon class="h-4 w-4" />
      </button>
    </div>
  </div>
</template>
