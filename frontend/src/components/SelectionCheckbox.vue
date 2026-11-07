<script setup lang="ts">
import { CheckIcon, MinusIcon } from '@heroicons/vue/24/outline'

withDefaults(defineProps<{
  checked: boolean
  indeterminate?: boolean
  label: string
}>(), { indeterminate: false })

const emit = defineEmits<{ toggle: [] }>()
</script>

<template>
  <button
    type="button"
    role="checkbox"
    :aria-checked="indeterminate ? 'mixed' : checked"
    :aria-label="label"
    :title="label"
    class="inline-flex h-5 w-5 shrink-0 items-center justify-center border-2 transition-colors duration-150 focus:outline-none focus-visible:ring-2 focus-visible:ring-primary-500 focus-visible:ring-offset-2 focus-visible:ring-offset-surface dark:focus-visible:ring-offset-surface-dark"
    :class="checked || indeterminate
      ? 'border-primary-600 bg-primary-500 text-white hover:border-primary-700 hover:bg-primary-600 dark:border-primary-300 dark:bg-primary-400 dark:text-primary-900 dark:hover:border-primary-200 dark:hover:bg-primary-300'
      : 'border-line bg-surface text-transparent hover:border-primary-400 hover:bg-primary-50 dark:border-line-dark dark:bg-surface-dark dark:hover:border-primary-400 dark:hover:bg-primary-900/30'"
    @click.stop="emit('toggle')"
  >
    <MinusIcon v-if="indeterminate" class="h-3.5 w-3.5" />
    <CheckIcon v-else class="h-3.5 w-3.5" :class="{ 'opacity-0': !checked }" />
  </button>
</template>
