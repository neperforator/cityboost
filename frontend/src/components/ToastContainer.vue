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

const bgMap: Record<string, string> = {
  success: 'bg-emerald-600',
  error: 'bg-red-600',
  warning: 'bg-amber-500',
  info: 'bg-primary-600',
}
</script>

<template>
  <div role="status" aria-live="polite" class="fixed top-4 right-4 z-[9999] flex flex-col gap-2 max-w-sm w-full pointer-events-none">
    <TransitionGroup name="toast">
      <div
        v-for="t in toasts"
        :key="t.id"
        class="pointer-events-auto px-4 py-3 rounded-xl shadow-modal text-sm font-medium flex items-center gap-3"
        :class="bgMap[t.type]"
      >
        <component :is="iconMap[t.type]" class="w-5 h-5 text-white shrink-0" />
        <span class="flex-1 text-white">{{ t.message }}</span>
        <button @click="remove(t.id)" :aria-label="`Закрыть уведомление: ${t.message}`" class="text-white/70 hover:text-white shrink-0 focus:outline-none focus-visible:ring-2 focus-visible:ring-white/50 rounded">
          <XMarkIcon class="w-4 h-4" />
        </button>
      </div>
    </TransitionGroup>
  </div>
</template>

<style scoped>
.toast-enter-active { animation: slideIn 0.3s ease; }
.toast-leave-active { animation: slideOut 0.3s ease; }
@keyframes slideIn { from { transform: translateX(100%); opacity: 0; } to { transform: translateX(0); opacity: 1; } }
@keyframes slideOut { from { transform: translateX(0); opacity: 1; } to { transform: translateX(100%); opacity: 0; } }
</style>
