<script setup lang="ts">
import { nextTick, onUnmounted, ref, watch } from 'vue'
import { XMarkIcon } from '@heroicons/vue/24/outline'

const props = withDefaults(defineProps<{
  open: boolean
  title: string
  confirmLabel?: string
  cancelLabel?: string
  tone?: 'primary' | 'danger'
  busy?: boolean
}>(), {
  confirmLabel: 'Подтвердить',
  cancelLabel: 'Отмена',
  tone: 'primary',
  busy: false,
})

const emit = defineEmits<{ confirm: []; cancel: [] }>()

const confirmButton = ref<HTMLButtonElement | null>(null)
const cancelButton = ref<HTMLButtonElement | null>(null)

function onKeydown(event: KeyboardEvent) {
  if (event.key === 'Escape' && !props.busy) emit('cancel')
}

watch(() => props.open, async (open) => {
  if (open) {
    window.addEventListener('keydown', onKeydown)
    document.body.style.overflow = 'hidden'
    await nextTick()
    // Для опасного действия фокус по умолчанию — на отмене.
    if (props.tone === 'danger') cancelButton.value?.focus()
    else confirmButton.value?.focus()
  } else {
    window.removeEventListener('keydown', onKeydown)
    document.body.style.overflow = ''
  }
})

onUnmounted(() => {
  window.removeEventListener('keydown', onKeydown)
  if (props.open) document.body.style.overflow = ''
})
</script>

<template>
  <Teleport to="body">
    <Transition name="modal">
      <div
        v-if="open"
        class="fixed inset-0 z-[60] flex items-end justify-center bg-ink/50 p-4 sm:items-center dark:bg-black/70"
        @click.self="!busy && emit('cancel')"
      >
        <div
          class="w-full max-w-md border-2 border-line bg-surface shadow-panel dark:border-line-dark dark:bg-surface-dark"
          role="dialog"
          aria-modal="true"
          aria-labelledby="confirm-dialog-title"
        >
          <div class="flex items-start justify-between gap-3 border-b-2 border-line px-5 py-4 dark:border-line-dark">
            <h2 id="confirm-dialog-title" class="font-display text-lg font-semibold text-ink dark:text-ink-dark">
              {{ title }}
            </h2>
            <button
              type="button"
              class="btn-ghost btn-icon btn-sm -mr-1 -mt-1"
              aria-label="Закрыть"
              :disabled="busy"
              @click="emit('cancel')"
            >
              <XMarkIcon class="h-5 w-5" />
            </button>
          </div>

          <div class="px-5 py-4">
            <slot />
          </div>

          <div class="flex flex-col-reverse gap-2 border-t-2 border-line px-5 py-4 sm:flex-row sm:justify-end dark:border-line-dark">
            <button
              ref="cancelButton"
              type="button"
              class="btn-secondary"
              :disabled="busy"
              @click="emit('cancel')"
            >
              {{ cancelLabel }}
            </button>
            <button
              ref="confirmButton"
              type="button"
              class="btn"
              :class="tone === 'danger' ? 'btn-danger' : 'btn-primary'"
              :disabled="busy"
              @click="emit('confirm')"
            >
              <span
                v-if="busy"
                class="h-4 w-4 animate-spin rounded-full border-2 border-white/40 border-t-white"
              />
              {{ busy ? 'Выполняется…' : confirmLabel }}
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.modal-enter-active,
.modal-leave-active {
  transition: opacity 0.18s ease;
}
.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}
.modal-enter-active > div,
.modal-leave-active > div {
  transition: transform 0.2s ease;
}
.modal-enter-from > div,
.modal-leave-to > div {
  transform: translateY(8px) scale(0.98);
}
</style>
