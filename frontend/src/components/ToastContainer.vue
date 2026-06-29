<script setup lang="ts">
import { useToast } from '@/composables/useToast'

const { toasts, remove } = useToast()
</script>

<template>
  <div class="fixed top-4 right-4 z-[9999] flex flex-col gap-2 max-w-sm w-full pointer-events-none">
    <TransitionGroup name="toast">
      <div
        v-for="t in toasts"
        :key="t.id"
        class="pointer-events-auto px-4 py-3 rounded-xl shadow-xl text-sm font-medium flex items-center gap-3 animate-slide-in"
        :class="{
          'bg-emerald-500 text-white': t.type === 'success',
          'bg-red-500 text-white': t.type === 'error',
          'bg-indigo-500 text-white': t.type === 'info',
          'bg-amber-500 text-white': t.type === 'warning',
        }"
      >
        <span class="text-lg">{{ t.type === 'success' ? '✅' : t.type === 'error' ? '❌' : t.type === 'warning' ? '⚠️' : 'ℹ️' }}</span>
        <span class="flex-1">{{ t.message }}</span>
        <button @click="remove(t.id)" class="text-white/70 hover:text-white shrink-0">&times;</button>
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
