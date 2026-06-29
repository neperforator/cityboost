<script setup lang="ts">
defineProps({
  status: { type: String, required: true },
  size: { type: String, default: 'normal' },
})

const labels = { NEW: 'Новая', IN_WORK: 'В работе', DONE: 'Выполнена', CLOSED: 'Закрыта' }
</script>

<template>
  <span
    class="inline-flex items-center rounded-full font-semibold"
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
