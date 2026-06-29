<script setup lang="ts">
withDefaults(defineProps<{
  status: string
  size?: string
}>(), { size: 'normal' })

const labels: Record<string, string> = { NEW: 'Новая', IN_WORK: 'В работе', DONE: 'Выполнена', CLOSED: 'Закрыта' }
</script>

<template>
  <span
    class="inline-flex items-center rounded-full font-semibold transition-all duration-300 ease-in-out"
    :class="{
      'badge-new': status === 'NEW',
      'badge-in-work': status === 'IN_WORK',
      'badge-done': status === 'DONE',
      'badge-closed': status === 'CLOSED',
      'px-2.5 py-0.5 text-xs': size === 'normal',
      'px-3 py-1 text-sm': size === 'lg',
    }"
  >
    {{ labels[status] || status }}
  </span>
</template>
