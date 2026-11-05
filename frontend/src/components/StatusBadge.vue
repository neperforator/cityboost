<script setup lang="ts">
withDefaults(defineProps<{
  status: string
  size?: string
}>(), { size: 'normal' })

const labels: Record<string, string> = { NEW: 'Новая', IN_WORK: 'В работе', DONE: 'Выполнена', CLOSED: 'Отклонена' }
</script>

<template>
  <span
    class="inline-flex items-center font-semibold"
    :class="{
      'badge-new': status === 'NEW',
      'badge-in-work': status === 'IN_WORK',
      'badge-done': status === 'DONE',
      'badge-closed': status === 'CLOSED',
      'px-2 py-0.5 text-xs': size === 'normal',
      'px-3 py-1 text-sm': size === 'lg',
    }"
  >
    <span class="h-1.5 w-1.5 rounded-full bg-current" />
    {{ labels[status] || status }}
  </span>
</template>
