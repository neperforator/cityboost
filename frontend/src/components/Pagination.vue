<script setup lang="ts">
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
    class="flex flex-wrap items-center justify-center gap-1.5 mt-6 mb-2"
  >
    <!-- Prev -->
    <button
      :disabled="page <= 1"
      class="px-3 py-1.5 rounded-lg text-sm font-medium transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
      :class="page > 1 ? 'hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-700 dark:text-gray-300' : 'text-gray-400'"
      @click="emit('change', page - 1)"
    >
      ←
    </button>

    <!-- Pages -->
    <template v-for="(p, i) in getVisiblePages(page, totalPages)" :key="i">
      <span v-if="p === 'ellipsis'" class="px-1 text-gray-400 text-sm">…</span>
      <button
        v-else
        class="min-w-[36px] h-9 rounded-lg text-sm font-medium transition-all"
        :class="p === page
          ? 'bg-primary-600 text-white shadow-md'
          : 'hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-700 dark:text-gray-300 border border-gray-200 dark:border-gray-700'"
        @click="emit('change', p)"
      >
        {{ p }}
      </button>
    </template>

    <!-- Next -->
    <button
      :disabled="page >= totalPages"
      class="px-3 py-1.5 rounded-lg text-sm font-medium transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
      :class="page < totalPages ? 'hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-700 dark:text-gray-300' : 'text-gray-400'"
      @click="emit('change', page + 1)"
    >
      →
    </button>

    <!-- Total info -->
    <span class="ml-2 text-xs text-gray-400">
      {{ total }} заявок
    </span>
  </div>
</template>
