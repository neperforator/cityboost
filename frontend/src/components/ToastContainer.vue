<script setup lang="ts">
import { useToast } from '@/composables/useToast'
import { XMarkIcon } from '@heroicons/vue/24/solid'
import { CheckCircleIcon, ExclamationTriangleIcon, InformationCircleIcon, XCircleIcon } from '@heroicons/vue/24/outline'

const { toasts, remove } = useToast()

const iconMap: Record<string, any> = {
  success: CheckCircleIcon,
  error: XCircleIcon,
  warning: ExclamationTriangleIcon,
  info: InformationCircleIcon,
}

const accentMap: Record<string, string> = {
  success: 'border-l-emerald-400',
  error: 'border-l-red-400',
  warning: 'border-l-amber-400',
  info: 'border-l-map-400',
}
</script>

<template>
  <div role="status" aria-live="polite" class="pointer-events-none fixed right-4 top-4 z-[9999] flex w-full max-w-sm flex-col gap-2">
    <TransitionGroup name="toast">
      <div
        v-for="t in toasts"
        :key="t.id"
        class="pointer-events-auto flex items-center gap-3 rounded-sm border-l-4 bg-ink px-4 py-3 text-sm font-medium text-white dark:bg-surface-dark"
        :class="accentMap[t.type]"
      >
        <component :is="iconMap[t.type]" class="h-5 w-5 shrink-0" />
        <span class="flex-1">{{ t.message }}</span>
        <button
          @click="remove(t.id)"
          :aria-label="`Закрыть уведомление: ${t.message}`"
          class="shrink-0 rounded-sm text-white/60 hover:text-white focus:outline-none focus-visible:ring-2 focus-visible:ring-white/50"
        >
          <XMarkIcon class="h-4 w-4" />
        </button>
      </div>
    </TransitionGroup>
  </div>
</template>

<style scoped>
.toast-enter-active { animation: slideIn 0.2s ease; }
.toast-leave-active { animation: slideOut 0.2s ease; }
@keyframes slideIn { from { transform: translateX(100%); opacity: 0; } to { transform: translateX(0); opacity: 1; } }
@keyframes slideOut { from { transform: translateX(0); opacity: 1; } to { transform: translateX(100%); opacity: 0; } }
</style>
